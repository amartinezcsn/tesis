"""Pruebas ligeras de reglas temporales del pipeline semanal."""

import importlib
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
aggregate = importlib.import_module("02_agregar_semanal")
features = importlib.import_module("03_features_semanales")
models = importlib.import_module("06_modelos_rolling_window")
from config_semanal import DATE_COLUMN, TARGET_COLUMN, WINDOW_WEEKS


class WeeklyPipelineTests(unittest.TestCase):
    def test_aggregation_keeps_only_complete_weeks(self):
        dates = pd.date_range("2024-01-01", periods=15, freq="D")
        daily = pd.DataFrame(
            {
                "fecha": dates,
                "compras_total_real_2026_05": 1.0,
                "ventas_importe_real_2026_05": 2.0,
                "ventas_registros": 1.0,
                "ventas_cantidad_total": 1.0,
                "es_festivo_mexicano": 0,
                "es_fecha_pago": 0,
                "nacimientos_indice": 1.0,
                "inpc_valor_mensual": 100.0,
                "temperatura_promedio_mensual_hidalgo": 20.0,
            }
        )
        weekly = aggregate.aggregate_daily_to_weekly(daily)
        self.assertEqual(len(weekly), 2)
        self.assertTrue((weekly["compras_importe_semanal"] == 7.0).all())

    def test_weekly_lag_never_uses_current_target(self):
        weeks = pd.date_range("2023-01-02", periods=60, freq="W-MON")
        weekly = pd.DataFrame(
            {
                DATE_COLUMN: weeks,
                "compras_importe_semanal": np.arange(60, dtype=float),
                "ventas_importe_real_2026_05": np.arange(60, dtype=float),
                "ventas_registros": 1.0,
                "ventas_cantidad_total": 2.0,
                "eventos_festivos_semana": 0,
                "eventos_pago_semana": 0,
                "es_san_valentin": 0,
                "es_dia_nino": 0,
                "es_dia_madre": 0,
                "nacimientos_indice_semanal": 1.0,
                "semana_anio": 1,
                "mes": 1,
                "inpc_observado_semana": 100.0,
                "temperatura_observada_semana": 20.0,
            }
        )
        model = features.build_weekly_features(weekly)
        self.assertEqual(model.iloc[0][TARGET_COLUMN], 52.0)
        self.assertEqual(model.iloc[0]["hist_compras_importe_semanal_lag_1s"], 51.0)

    def test_rolling_window_has_fixed_length(self):
        origins = models.iter_rolling_windows(80)
        self.assertEqual(origins[0], WINDOW_WEEKS)
        self.assertEqual(origins[-1], 79)

    def test_complementary_horizon_has_four_steps_without_overrun(self):
        origins = models.iter_rolling_windows(80, horizon=4)
        self.assertEqual(origins[0], WINDOW_WEEKS)
        self.assertEqual(origins[-1], 76)

    def test_seasonal_baseline_uses_all_available_positions_for_h4(self):
        train = pd.DataFrame({TARGET_COLUMN: np.arange(52, dtype=float)})
        forecasts = models.empirical_forecasts(train, steps=4)
        np.testing.assert_array_equal(
            forecasts["empirico_estacional_52s"], np.array([0.0, 1.0, 2.0, 3.0])
        )

    def test_recursive_future_features_use_predictions_for_target_history(self):
        history = [10.0, 20.0, 30.0, 40.0]
        origin = pd.Series(
            {
                "hist_compras_importe_semanal_lag_1s": 40.0,
                "hist_ventas_importe_real_2026_05_lag_1s": 99.0,
                "exog_inpc_publicado": 100.0,
            }
        )
        row = pd.Series(
            {
                "hist_compras_importe_semanal_lag_1s": 999.0,
                "hist_ventas_importe_real_2026_05_lag_1s": 888.0,
                "exog_inpc_publicado": 111.0,
                "exog_es_dia_madre": 1.0,
            }
        )
        future = models._recursive_feature_row(
            row,
            origin,
            list(row.index),
            history + [55.0],
        )
        self.assertEqual(future["hist_compras_importe_semanal_lag_1s"], 55.0)
        self.assertEqual(future["hist_ventas_importe_real_2026_05_lag_1s"], 99.0)
        self.assertEqual(future["exog_inpc_publicado"], 100.0)
        self.assertEqual(future["exog_es_dia_madre"], 1.0)


if __name__ == "__main__":
    unittest.main()
