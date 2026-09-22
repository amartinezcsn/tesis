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
from hibrido.data import load_purchases,load_exogenous,load_sales
from hibrido.composition import select_categories,predict_shares,allocate,shares
from hibrido.evaluation import paired_interval,composition_metrics,total_metrics
from hibrido.experiment import run_experiment,forecast_bundle,select_models
from hibrido.models import stat_fit, ml_fit


def panel(n=110):
    index=pd.date_range('2022-01-03',periods=n,freq='W-MON')
    a=100+np.arange(n)+10*np.sin(np.arange(n)/3)
    result=pd.DataFrame({'harina':a*.6,'azucar':a*.4,'total':a},index=index)
    result.index.name='semana_inicio'
    return result


class DataTests(unittest.TestCase):
    def test_cli_has_fixed_output_directory(self):
        from hibrido import cli
        self.assertEqual(cli.OUTPUT_DIR,Path('C:/Python/tesis/output'))
        with self.assertRaises(SystemExit):
            cli.main(['audit','--output','otro_directorio'])

    def test_main_entry_uses_hybrid_when_called_as_function(self):
        from unittest.mock import patch
        entry = importlib.import_module('00_pipeline_hibrido')
        with patch('hibrido.cli.main', return_value=0) as hybrid_main:
            self.assertEqual(entry.main(['audit']), 0)
            hybrid_main.assert_called_once_with(['audit'])

    def test_unknown_component_names_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'estadístico no soportado'):
            stat_fit([1., 2., 3.], 'otro')
        with self.assertRaisesRegex(ValueError, 'ML no soportado'):
            ml_fit(pd.DataFrame({'x': [1., 2.]}), np.array([1., 2.]), 'otro', Config())

    def test_normalizer_preserves_legacy_contract(self):
        active = importlib.import_module('01_normalizacion').clean_upper
        for raw, expected in [('  Café  molido ', 'CAFE MOLIDO'), ('Azúcar\trefinada', 'AZUCAR REFINADA'), ('', pd.NA), (None, pd.NA)]:
            value = active(raw)
            if pd.isna(expected):
                self.assertTrue(pd.isna(value))
            else:
                self.assertEqual(value, expected)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)
        self.raw=pd.DataFrame({'fecha':['2024-01-01','2024-01-08'],'descripcion':['Harina','Harina'],'importe_nominal':[10,0]})
    def tearDown(self):self.temp.cleanup()
    def purchases(self):
        p=self.path/'source.csv';self.raw.to_csv(p,index=False);return load_purchases(p)
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
        self.raw['es_sintetico']=True
        with self.assertRaisesRegex(ValueError,'sintéticos'):self.purchases()
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
    def test_text_false_sales_is_not_synthetic(self):
        p=self.path/'sales.csv'
        pd.DataFrame({'semana_inicio':['2024-01-01'],'importe_nominal':[10],
            'available_at':['2024-01-08'],'es_sintetico':['False']}).to_csv(p,index=False)
        result=load_sales(p,pd.DatetimeIndex(['2024-01-01']))
        self.assertEqual(result.importe_nominal.iloc[0],10)


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
    def test_supplementary_metric_uses_own_available_dates(self):
        rows=[]
        for origin in pd.date_range('2024-01-01',periods=3,freq='W-MON'):
            for model in ('hibrido','ss_ar1','hgb','ultimo_valor','promedio_4s'):
                prediction=np.nan if model=='hibrido' and origin.day==8 else 9.
                rows.append(dict(origen=origin,horizonte=1,modelo=model,real=10.,prediccion=prediction,escala_mase=1.))
        metrics=total_metrics(pd.DataFrame(rows),common=True).set_index('modelo')
        self.assertEqual(metrics.loc['hibrido','n'],2)
        self.assertEqual(metrics.loc['promedio_4s','n'],3)


class IntegrationTests(unittest.TestCase):
    def test_full_experiment_reload_and_future_no_labels(self):
        p=panel(75)
        cfg=Config(holdout_weeks=8,tuning_origins=2,use_arima=False,use_rf=False,bootstrap_samples=100)
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
        p=panel(75);cfg=Config(holdout_weeks=8,tuning_origins=2,use_arima=False,use_rf=False,bootstrap_samples=100)
        a=select_models(p,cfg,load_exogenous(None))
        p.iloc[-8:]*=20
        b=select_models(p,cfg,load_exogenous(None))
        self.assertEqual(a[0],b[0]);self.assertEqual(a[1:4],b[1:4])


if __name__=='__main__':unittest.main()
