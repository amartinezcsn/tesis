"""Technical fixtures, never business observations or evidence for H1."""
import sys,unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hibrido.config import Config
from hibrido.gaps import build_gap_panel,validate_panel,training_targets,history
from hibrido.features import row_features,samples,partitions
from hibrido.data import load_exogenous
from hibrido.models import components,baselines,ml_fit
from hibrido.composition import predict_shares
from hibrido.experiment import run_experiment,select_models
from hibrido.reporting import quality_controls,export_results
from hibrido.evaluation import total_metrics

def panel():
    dates=pd.date_range('2021-05-03',periods=110,freq='W-MON')
    y=200+np.arange(110)*.7+20*np.sin(np.arange(110)/4)
    p=pd.DataFrame({'harina':y*.6,'azucar':y*.4,'total':y},index=dates)
    p.index.name='semana_inicio';p.iloc[[8,9,16,30,41,56,72,88,96,102,108,109]]=np.nan
    return p

class GapTemporalTests(unittest.TestCase):
    def setUp(self):
        self.p=panel();self.c=Config(use_arima=False,use_rf=False,tuning_origins=4,holdout_weeks=16,min_training_observations=12)
        self.ex=load_exogenous(None)
    def test_calendar_not_compressed(self):
        with self.assertRaisesRegex(ValueError,'comprimir'):validate_panel(self.p.dropna())
    def test_partial_missing_panel_rejected(self):
        self.p.iloc[8,0]=1
        with self.assertRaisesRegex(ValueError,'completamente'):validate_panel(self.p)
    def test_last_observation_and_age(self):
        f=row_features(self.p,10,1,self.c,self.ex)
        self.assertEqual(f.ultimo_observado.iloc[0],self.p.total.iloc[7]);self.assertEqual(f.edad_ultimo_semanas.iloc[0],3)
        self.assertEqual(f.n_disponibles_4.iloc[0],2)
    def test_all_missing_summary_remains_missing(self):
        self.p.iloc[6:10]=np.nan
        f=row_features(self.p,10,1,self.c,self.ex)
        self.assertTrue(pd.isna(f.media_disponible_4.iloc[0]));self.assertEqual(f.n_disponibles_4.iloc[0],0)
    def test_future_does_not_change_features(self):
        a=row_features(self.p,80,4,self.c,self.ex);self.p.iloc[80:]=1e8
        pd.testing.assert_frame_equal(a,row_features(self.p,80,4,self.c,self.ex))
    def test_labels_observed_available_and_calendar_aligned(self):
        for h in range(1,5):
            x,y,_=samples(self.p,80,h,self.c,self.ex)
            targets=training_targets(self.p,80,h,self.c)
            np.testing.assert_equal(y,self.p.total.iloc[targets]);self.assertTrue(np.isfinite(y).all())
            self.assertLess(max(targets),80)
            expected=row_features(self.p,targets[-1]-h+1,h,self.c,self.ex)
            pd.testing.assert_frame_equal(x.iloc[[-1]].reset_index(drop=True),expected)
    def test_expanding_history_retains_gaps(self):
        h=history(self.p,80,self.c);self.assertEqual(len(h),80);self.assertTrue(h.total.isna().any())
    def test_tuning_purged_final_missing_not_dropped(self):
        cutoff,tuning,evaluation,f=partitions(self.p,self.c)
        self.assertLess(max(tuning)+3,cutoff);self.assertEqual(len(evaluation),16)
        self.assertTrue((f.ultima_etiqueta_entrenamiento<f.origen).all())
        self.assertTrue((f.motivo=='semana_incierta').any());self.assertTrue((f.motivo=='fuera_del_periodo').any())
    def test_insufficient_labels_block(self):
        with self.assertRaises(ValueError):samples(self.p,10,1,self.c,self.ex)
    def test_no_imputed_targets(self):
        x,y,_=samples(self.p,60,1,self.c,self.ex);y=y.copy();y[0]=np.nan
        with self.assertRaisesRegex(ValueError,'Objetivos'):ml_fit(x,y,'hgb',self.c)
    def test_calendar_composition_weights(self):
        h=pd.DataFrame({'a':[10,np.nan,np.nan,0],'b':[0,np.nan,np.nan,10],'total':[10,np.nan,np.nan,10]},index=pd.date_range('2022-01-03',periods=4,freq='W-MON'))
        p=predict_shares(h,['a','b'],.5,calendar=True)
        self.assertAlmostEqual(p.a,1/9);self.assertAlmostEqual(p.b,8/9)
    def test_baseline_last_observed_not_last_week(self):
        y=self.p.total.iloc[:10];b=baselines(y,1,gaps=True)
        self.assertEqual(b['ultimo_valor'],y.iloc[7])
    def test_state_space_and_native_ml_accept_gaps(self):
        pred,_,errors,_=components(self.p,70,1,self.c,self.ex,())
        self.assertFalse(errors);self.assertTrue(all(np.isfinite(v) for v in pred.values()))
    def test_fitted_predictions_ignore_future(self):
        a=components(self.p,70,2,self.c,self.ex,())[0];self.p.iloc[70:]=1e8
        b=components(self.p,70,2,self.c,self.ex,())[0];self.assertEqual(a,b)

class GapIngestionTests(unittest.TestCase):
    def setUp(self):
        self.d=pd.date_range('2022-01-03',periods=4,freq='W-MON')
        self.p=pd.DataFrame({'semana_inicio':[self.d[0],self.d[2]],'descripcion_normalizada':['HARINA','HARINA'],'importe_nominal':[10.,20.],'es_sintetico':False})
        self.cov=pd.DataFrame({'semana_inicio':self.d,'estado':['registrada','desconocida','registrada','cero_confirmado'],'evidencia':['revisado','','revisado','confirmado'],'fecha_revision':['2026-09-14','','2026-09-14','2026-09-14']})
        self.cat=pd.DataFrame({'descripcion_normalizada':['HARINA'],'insumo_id':['harina'],'aprobado':[True],'decision':['incluir'],'evidencia':['ingrediente']})
    def build(self):return build_gap_panel(self.p,self.cov,self.cat,self.d[0],self.d[-1])
    def test_unknown_and_true_zero_differ(self):
        p,c=self.build();self.assertTrue(p.iloc[1].isna().all());self.assertEqual(p.total.iloc[3],0);self.assertEqual(len(p),4)
    def test_zero_targets_rejected_when_policy_disallows_them(self):
        with self.assertRaisesRegex(ValueError,'Ceros semanales no válidos'):
            build_gap_panel(self.p,self.cov,self.cat,self.d[0],self.d[-1],zero_targets_valid=False)
        self.cov.loc[3,'estado']='incierta'
        p,_=build_gap_panel(self.p,self.cov,self.cat,self.d[0],self.d[-1],zero_targets_valid=False)
        self.assertTrue(p.iloc[3].isna().all())
    def test_missing_coverage_defaults_unknown(self):
        self.cov=self.cov.iloc[[0,2,3]];p,c=self.build();self.assertTrue(p.iloc[1].isna().all())
    def test_synthesis_rejected(self):
        self.p.loc[0,'es_sintetico']=True
        with self.assertRaisesRegex(ValueError,'sintéticos'):self.build()
    def test_fuel_excluded_even_if_catalog_includes(self):
        self.p['CLASIFICACION']='COMBUSTIBLE'
        with self.assertRaisesRegex(ValueError,'excluidos'):self.build()
    def test_zero_items_need_adjudication(self):
        self.p.loc[0,'importe_nominal']=0
        with self.assertRaisesRegex(ValueError,'cero por artículo'):self.build()
    def test_unknown_catalog_blocks(self):
        self.cat.loc[0,'decision']='revisar'
        with self.assertRaisesRegex(ValueError,'Catálogo pendiente'):self.build()
    def test_provisional_catalog_evidence_blocks(self):
        self.cat.loc[0,'evidencia']='Pendiente de homologación por descripción.'
        with self.assertRaisesRegex(ValueError,'evidencia concreta'):self.build()
    def test_provisional_catalog_evidence_blocks(self):
        self.cat.loc[0,'evidencia']='Pendiente de homologación por descripción.'
        with self.assertRaisesRegex(ValueError,'evidencia concreta'):self.build()
    def test_week_without_included_rows_cannot_be_observed(self):
        self.cov.loc[1,['estado','evidencia','fecha_revision']]=['registrada','revisado','2026-09-14']
        with self.assertRaisesRegex(ValueError,'sin compras'):self.build()
    def test_uncertain_week_with_rows_is_masked(self):
        self.cov.loc[0,'estado']='incierta';p,_=self.build();self.assertTrue(p.iloc[0].isna().all())

class GapIntegrationTests(unittest.TestCase):
    def test_exogenous_schema_is_frozen_before_tuning_not_at_panel_start(self):
        p=panel().ffill()
        cfg=Config(use_arima=False,use_rf=False,tuning_origins=3,holdout_weeks=12,min_training_observations=12,weights=(.5,),alphas=(.1,))
        _,tuning,_,_=partitions(p,cfg)
        published=p.index[tuning[0]-1]
        ex=pd.DataFrame([dict(variable='inpc',fecha_referencia=published,available_at=published,
            valor=1.,fuente='fixture',version='1',tipo='observada')])
        selected=select_models(p,cfg,ex)
        self.assertIn('inpc',selected[3])

    def test_pipeline_roundtrip_and_missing_evaluation(self):
        p=panel();before=p.copy();cfg=Config(use_arima=False,use_rf=False,tuning_origins=3,holdout_weeks=12,min_training_observations=12,weights=(.5,),alphas=(.1,))
        with tempfile.TemporaryDirectory() as temp:
            r=run_experiment(p,cfg,load_exogenous(None),temp,demo=True)
            pd.testing.assert_frame_equal(p,before)
            self.assertTrue(all(c['aprobado'] for c in quality_controls(p,r)))
            self.assertTrue(r['predicciones'].real.isna().any())
            main=r['metricas'].query("horizonte==1 and comparacion=='principal_fechas_comunes'")
            self.assertEqual(main.n.nunique(),1)
            self.assertFalse(r['hypothesis']['respaldo_confirmatorio'])
            self.assertEqual(r['hypothesis']['importe']['n'],int(main.n.iloc[0]))
            export_results(temp,r,cfg,demo=True)
            payload=json.loads((Path(temp)/'dss_hibrido.json').read_text(encoding='utf-8'))
            self.assertIn('cobertura_evaluacion',payload)
            self.assertEqual(payload['politica_faltantes'],'calendar_gaps')

if __name__=='__main__':unittest.main()
