"""Pruebas del tablero autocontenido generado por el pipeline híbrido."""
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hibrido.config import Config
from hibrido.reporting import export_results


class DashboardReportingTests(unittest.TestCase):
    def test_interactive_dashboard_is_traceable_and_budget_only(self):
        future = pd.DataFrame([
            dict(origen='2025-08-04', fecha_objetivo='2025-08-04', horizonte=1,
                 insumo_id='HARINA', participacion=.6, importe=60., total=100.,
                 unidad='MXN nominales', demostracion=False),
            dict(origen='2025-08-04', fecha_objetivo='2025-08-04', horizonte=1,
                 insumo_id='RESTO_ELEGIBLE', participacion=.4, importe=40., total=100.,
                 unidad='MXN nominales', demostracion=False),
        ])
        # El tablero acepta los cuatro horizontes; para esta prueba se replica
        # el fixture sin atribuirle valor científico.
        future = pd.concat([
            future.assign(
                horizonte=h,
                fecha_objetivo=str(pd.Timestamp('2025-08-04') + pd.Timedelta(weeks=h - 1)),
            ) for h in range(1, 5)
        ], ignore_index=True)
        four_week = pd.DataFrame([
            dict(insumo_id='HARINA', importe_4_semanas=240.,
                 participacion_4_semanas=.6, total_4_semanas=400.,
                 unidad='MXN nominales', periodo='próximas 4 semanas (28 días)'),
            dict(insumo_id='RESTO_ELEGIBLE', importe_4_semanas=160.,
                 participacion_4_semanas=.4, total_4_semanas=400.,
                 unidad='MXN nominales', periodo='próximas 4 semanas (28 días)'),
        ])
        metrics = pd.DataFrame([
            dict(horizonte=1, modelo='hibrido', n=6, rmse=10., mae=8., mase=.9),
        ])
        composition = pd.DataFrame([
            dict(horizonte=1, modelo='participacion_ewm', insumo_id='HARINA',
                 n=6, mae_pp=5.),
        ])
        partitions = pd.DataFrame([
            dict(etapa='evaluacion', horizonte=1, origen='2025-07-28',
                 objetivo_observado=True),
        ])
        results = {
            'pronostico_futuro': future,
            'pronostico_4_semanas': four_week,
            'selection': {'1': {'stat': 'ss_ar1', 'ml': 'ridge', 'peso': .5}},
            'hypothesis': {
                'alcance': 'fixture',
                'evidencia_favorable_ambos_componentes': False,
                'respaldo_confirmatorio': False,
            },
            'metricas': metrics,
            'metricas_composicion': composition,
            'predicciones': pd.DataFrame(),
            'particiones': partitions,
            'advertencia': 'Fixture de prueba; no es evidencia.',
            'politica_faltantes': 'calendar_gaps',
        }
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'run_fixture'
            output.mkdir()
            export_results(output, results, Config(), demo=False)
            dashboard = (output / 'tablero.html').read_text(encoding='utf-8')
            self.assertIn('id="horizon"', dashboard)
            self.assertIn('id="downloadCsv"', dashboard)
            self.assertIn('Distribución presupuestaria', dashboard)
            self.assertIn('Trazabilidad de la emisión', dashboard)
            self.assertIn('calcula cantidades físicas', dashboard)
            self.assertIn('28 días; no equivale necesariamente a un mes calendario', dashboard)
            self.assertIn('"run_id":"run_fixture"', dashboard)
            self.assertIn('connect-src \'none\'', dashboard)
            self.assertNotIn('src="http', dashboard)


if __name__ == '__main__':
    unittest.main()
