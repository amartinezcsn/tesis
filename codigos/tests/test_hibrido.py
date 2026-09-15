"""Regresión Rev44. Todos los datos fabricados son fixtures, nunca evidencia real."""
import sys
import json
import tempfile
import unittest
import importlib
from pathlib import Path
from dataclasses import replace
import numpy as np
import pandas as pd
import joblib

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hibrido.config import Config,load_config
from hibrido.data import load_purchases,build_panel,load_exogenous,load_sales
from hibrido.features import row_features,samples,partitions
from hibrido.composition import select_categories,predict_shares,allocate,shares
from hibrido.evaluation import paired_interval,composition_metrics
from hibrido.experiment import run_experiment,forecast_bundle,select_models
from hibrido.models import components,baselines


def panel(n=110):
    index=pd.date_range('2022-01-03',periods=n,freq='W-MON')
    a=100+np.arange(n)+10*np.sin(np.arange(n)/3)
    result=pd.DataFrame({'harina':a*.6,'azucar':a*.4,'total':a},index=index)
    result.index.name='semana_inicio'
    return result


class TemporalTests(unittest.TestCase):
    def setUp(self):
        self.panel=panel();self.cfg=Config(use_arima=False,use_rf=False);self.exog=load_exogenous(None)

    def test_lags_reference_origin_not_target(self):
        a=row_features(self.panel,70,4,self.cfg,self.exog)
        self.assertEqual(a.lag_1.iloc[0],self.panel.total.iloc[69])

    def test_future_target_mutation_does_not_change_features(self):
        a=row_features(self.panel,70,4,self.cfg,self.exog)
        changed=self.panel.copy();changed.iloc[70:]=1e9
        pd.testing.assert_frame_equal(a,row_features(changed,70,4,self.cfg,self.exog))

    def test_training_labels_precede_origin_all_horizons(self):
        for h in range(1,5):
            x,y,test=samples(self.panel,70,h,self.cfg,self.exog)
            self.assertEqual(len(x),52)
            np.testing.assert_allclose(y,self.panel.total.iloc[18:70])
            self.assertAlmostEqual(x.lag_1.iloc[-1],self.panel.total.iloc[69-h])

    def test_purge_tuning_labels_before_first_test_origin(self):
        cutoff,tuning,evaluation,folds=partitions(self.panel,self.cfg)
        self.assertLess(max(tuning)+3,min(evaluation))
        self.assertEqual(cutoff,94)
        self.assertEqual(len(evaluation),13)
        self.assertTrue((folds.ultima_etiqueta_entrenamiento<folds.origen).all())

    def test_short_history_is_blocked(self):
        with self.assertRaisesRegex(ValueError,'Historia insuficiente'):partitions(panel(60),self.cfg)

    def test_observed_exogenous_not_taken_from_target_week(self):
        origin=self.panel.index[70]
        ex=pd.DataFrame({'variable':['temp','temp'],'fecha_referencia':[origin-pd.Timedelta(days=1),origin+pd.Timedelta(weeks=2)],
            'available_at':[origin,origin+pd.Timedelta(weeks=3)],'valor':[20.,99.],'tipo':['observada','observada']})
        f=row_features(self.panel,70,4,self.cfg,ex,['temp'])
        self.assertEqual(f.exog_temp.iloc[0],20.)

    def test_forecast_vintage_must_be_available_at_origin(self):
        origin=self.panel.index[70];target=origin+pd.Timedelta(weeks=3)
        ex=pd.DataFrame({'variable':['temp','temp'],'fecha_referencia':[target,target],
            'available_at':[origin,origin+pd.Timedelta(days=1)],'valor':[21.,99.],'tipo':['pronostico','pronostico']})
        self.assertEqual(row_features(self.panel,70,4,self.cfg,ex,['temp']).exog_temp.iloc[0],21.)

    def test_unavailable_exogenous_is_missing_not_zero(self):
        row=row_features(self.panel,70,1,self.cfg,self.exog,['unknown'])
        self.assertTrue(np.isnan(row.exog_unknown.iloc[0]))

    def test_future_mutation_does_not_change_prediction(self):
        choice={'stat':'ets','ml':'ridge_1','peso':.5}
        a,_,errors,_=components(self.panel,70,4,self.cfg,self.exog,[],selection=choice)
        self.assertFalse(errors)
        changed=self.panel.copy();changed.iloc[70:]=1e7
        b,_,errors,_=components(changed,70,4,self.cfg,self.exog,[],selection=choice)
        self.assertFalse(errors);self.assertEqual(a,b)

    def test_baseline_zero_is_preserved(self):
        self.assertEqual(baselines(pd.Series([20.,30.,0.]),4)['ultimo_valor'],0)

    def test_unavailable_seasonal_is_not_other_model(self):
        self.assertTrue(np.isnan(baselines(pd.Series([20.,30.,0.]),4)['estacional_52s']))

    def test_synthetic_covariates_not_necessary(self):
        x,y,t=samples(self.panel,70,4,self.cfg,self.exog)
        self.assertTrue(np.isfinite(x.to_numpy()).all())


class DataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)
        self.raw=pd.DataFrame({'fecha':['2024-01-01','2024-01-08'],'descripcion':['Harina','Harina'],'importe_nominal':[10,0]})
        self.coverage=pd.DataFrame({'semana_inicio':['2024-01-01','2024-01-08'],'estado':['observada','cero_confirmado'],'evidencia':['registro revisado']*2,'fecha_revision':['2026-09-12']*2})
        self.cat=pd.DataFrame({'descripcion_normalizada':['HARINA'],'insumo_id':['harina'],'aprobado':[True]})
    def tearDown(self):self.temp.cleanup()
    def purchases(self):
        p=self.path/'source.csv';self.raw.to_csv(p,index=False);return load_purchases(p)
    def test_reconcile_nominal_totals(self):
        valid,reject=self.purchases();p,_=build_panel(valid,self.coverage,self.cat,'2024-01-01','2024-01-08')
        self.assertTrue(reject.empty);self.assertEqual(p.total.sum(),10)
    def test_unknown_week_blocks_training(self):
        valid,_=self.purchases();self.coverage.loc[1,'estado']='desconocida'
        with self.assertRaisesRegex(ValueError,'Cobertura pendiente'):build_panel(valid,self.coverage,self.cat,'2024-01-01','2024-01-08')
    def test_missing_week_not_compressed(self):
        valid,_=self.purchases()
        with self.assertRaises(ValueError):build_panel(valid,self.coverage.iloc[:1],self.cat,'2024-01-01','2024-01-08')
    def test_false_zero_is_rejected(self):
        valid,_=self.purchases();self.coverage.loc[0,'estado']='cero_confirmado'
        with self.assertRaisesRegex(ValueError,'contradice'):build_panel(valid,self.coverage,self.cat,'2024-01-01','2024-01-08')
    def test_no_coverage_evidence_is_rejected(self):
        valid,_=self.purchases();self.coverage['evidencia']=''
        with self.assertRaisesRegex(ValueError,'evidencia'):build_panel(valid,self.coverage,self.cat,'2024-01-01','2024-01-08')
    def test_catalog_requires_approval(self):
        valid,_=self.purchases();self.cat['aprobado']=False
        with self.assertRaisesRegex(ValueError,'aprobación'):build_panel(valid,self.coverage,self.cat,'2024-01-01','2024-01-08')
    def test_reserved_category_is_rejected(self):
        valid,_=self.purchases();self.cat['insumo_id']='total'
        with self.assertRaisesRegex(ValueError,'reservados'):build_panel(valid,self.coverage,self.cat,'2024-01-01','2024-01-08')
    def test_duplicate_rows_are_not_silently_deleted(self):
        self.raw=pd.concat([self.raw,self.raw.iloc[:1]],ignore_index=True)
        valid,reject=self.purchases();self.assertEqual(len(reject),2);self.assertEqual(len(valid),1)
    def test_explicitly_approved_duplicate_rows_are_preserved(self):
        self.raw=pd.concat([self.raw,self.raw.iloc[:1]],ignore_index=True)
        p=self.path/'source.csv';self.raw.to_csv(p,index=False)
        valid,reject=load_purchases(p,approved_duplicate_rows=[2,4])
        self.assertTrue(reject.empty);self.assertEqual(len(valid),3)
    def test_negative_rows_are_quarantined(self):
        self.raw.loc[0,'importe_nominal']=-1
        valid,reject=self.purchases();self.assertEqual(len(reject),1)
    def test_synthetic_rows_rejected_real_mode(self):
        self.raw['es_sintetico']=2
        with self.assertRaisesRegex(ValueError,'sintéticos'):self.purchases()
    def test_approved_synthetic_rows_only_before_holdout(self):
        self.raw['es_sintetico']=[True,False]
        self.raw['metodo_sintesis']=['mediana causal','']
        p=self.path/'source.csv';self.raw.to_csv(p,index=False)
        valid,reject=load_purchases(p,synthetic_training_approved=True,synthetic_before='2024-01-08')
        self.assertTrue(reject.empty);self.assertTrue(valid.es_sintetico.iloc[0])
    def test_synthetic_rows_rejected_inside_holdout(self):
        self.raw['es_sintetico']=[False,True]
        self.raw['metodo_sintesis']=['','mediana causal']
        p=self.path/'source.csv';self.raw.to_csv(p,index=False)
        with self.assertRaisesRegex(ValueError,'holdout'):
            load_purchases(p,synthetic_training_approved=True,synthetic_before='2024-01-08')
    def test_invalid_dates_are_quarantined(self):
        self.raw.loc[0,'fecha']='incorrecta'
        valid,reject=self.purchases();self.assertEqual(reject.motivo.iloc[0],'fecha_invalida')
    def test_iso_date_is_not_swapped_by_mexican_date_parser(self):
        self.raw.loc[0,'fecha']='2021-01-04'
        valid,_=self.purchases();self.assertEqual(valid.fecha.iloc[0],pd.Timestamp('2021-01-04'))
    def test_future_observation_cannot_be_known_early(self):
        p=self.path/'exog.csv'
        pd.DataFrame([dict(variable='x',fecha_referencia='2024-03-01',available_at='2024-01-01',valor=4,fuente='x',version='1',tipo='observada')]).to_csv(p,index=False)
        with self.assertRaisesRegex(ValueError,'observación'):load_exogenous(p)
    def test_config_unknown_key_is_error(self):
        p=self.path/'c.json';p.write_text('{"weights_typo":1}')
        with self.assertRaisesRegex(ValueError,'desconocidas'):load_config(p)
    def test_hybrid_weight_endpoints_invalid(self):
        with self.assertRaises(ValueError):Config(weights=(0,1)).validate()
    def test_boolean_approval_string_is_not_approval(self):
        with self.assertRaisesRegex(ValueError,'booleano'):Config(source_approved='false').validate()


class CompositionTests(unittest.TestCase):
    def test_select_categories_does_not_need_test(self):
        p=panel();self.assertEqual(select_categories(p.iloc[:50],.5),['harina'])
    def test_residual_reconciles(self):
        p=panel();s=shares(p,['harina']);np.testing.assert_allclose(s.sum(axis=1),1)
        np.testing.assert_allclose(s.otros,.4)
    def test_new_test_insumo_goes_to_residual(self):
        p=panel(1);p['nuevo']=50;p.total+=50
        s=shares(p,['harina']);self.assertGreater(s.otros.iloc[0],.4)
    def test_zero_total_shares_undefined(self):
        p=panel(1)*0;self.assertTrue(shares(p,['harina']).isna().all().all())
    def test_all_zero_history_blocks_composition(self):
        with self.assertRaises(ValueError):predict_shares(panel(10)*0,['harina'],.3)
    def test_both_shares_methods_nonnegative_and_normalized(self):
        for alpha in [None,.1,.6]:
            p=predict_shares(panel(10),['harina'],alpha);self.assertTrue((p>=0).all());self.assertAlmostEqual(p.sum(),1)
    def test_allocation_exact_cents(self):
        p=pd.Series([1/3]*3,index=['a','b','otros']);a=allocate(10.,p)
        self.assertEqual(round(a.sum(),2),10.);self.assertEqual(a.a,3.34)
    def test_zero_forecast_allocates_zero(self):
        a=allocate(0.,pd.Series([.3,.7]));self.assertTrue(a.eq(0).all())
    def test_invalid_share_is_rejected(self):
        with self.assertRaises(ValueError):allocate(10.,pd.Series([.2,.2]))
    def test_composition_metric_counts_undefined(self):
        f=pd.DataFrame({'horizonte':[1,1],'modelo':['m','m'],'insumo_id':['a','a'],'real':[.4,np.nan],'prediccion':[.5,.8]})
        m=composition_metrics(f);self.assertAlmostEqual(m.iloc[0].mae_pp,10);self.assertEqual(m.iloc[0].excluidas,1)
    def test_bootstrap_insufficient_is_not_significant(self):
        r=paired_interval([100]*4,Config());self.assertEqual(r['estado'],'muestra_insuficiente');self.assertIsNone(r['limite_inferior'])
    def test_bootstrap_preserves_calendar_with_missing(self):
        d=np.ones(20);d[3:7]=np.nan;r=paired_interval(d,Config());self.assertEqual(r['n'],16);self.assertAlmostEqual(r['media'],1)


class IntegrationTests(unittest.TestCase):
    def test_full_experiment_reload_and_future_no_labels(self):
        p=panel(75)
        cfg=Config(window=24,holdout_weeks=8,tuning_origins=2,use_arima=False,use_rf=False,bootstrap_samples=100)
        ex=load_exogenous(None)
        with tempfile.TemporaryDirectory() as temp:
            result=run_experiment(p,cfg,ex,temp,demo=True)
            model=joblib.load(Path(temp)/'modelos.joblib')
            future=forecast_bundle(model)
            self.assertNotIn('real',future.columns);self.assertEqual(set(future.horizonte),{1,2,3,4})
            self.assertFalse(result['hypothesis']['respaldo_confirmatorio'])
            self.assertEqual(result['hypothesis']['alcance'],'demostracion_sintetica')
            self.assertTrue((future.importe>=0).all())
    def test_test_mutation_does_not_change_selected_configuration(self):
        p=panel(75);cfg=Config(window=24,holdout_weeks=8,tuning_origins=2,use_arima=False,use_rf=False,bootstrap_samples=100)
        a=select_models(p,cfg,load_exogenous(None))
        p.iloc[-8:]*=20
        b=select_models(p,cfg,load_exogenous(None))
        self.assertEqual(a[0],b[0]);self.assertEqual(a[1:4],b[1:4])


if __name__=='__main__':unittest.main()
