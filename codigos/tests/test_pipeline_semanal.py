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
time_series = importlib.import_module("04_analisis_series_temporales_semanal")
from config_semanal import DATE_COLUMN, PRIMARY_BASELINE, TARGET_COLUMN, WINDOW_WEEKS, primary_coverage_block


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
                "nacimientos_indice_semanal": np.arange(60, dtype=float),
                "semana_anio": 1,
                "mes": 1,
                "inpc_observado_semana": 100.0,
                "temperatura_observada_semana": 20.0,
            }
        )
        model = features.build_weekly_features(weekly)
        self.assertEqual(model.iloc[0][TARGET_COLUMN], 52.0)
        self.assertEqual(model.iloc[0]["hist_compras_importe_semanal_lag_1s"], 51.0)
        self.assertEqual(model.iloc[0]["exog_nacimientos_indice_publicado_lag_1s"], 51.0)

    def test_unregistered_exogenous_feature_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no registradas"):
            features.validate_registered_exogenous(pd.DataFrame({"exog_variable_no_registrada": [1.0]}))

    def test_rolling_window_has_fixed_length(self):
        origins = models.iter_rolling_windows(80)
        self.assertEqual(origins[0], WINDOW_WEEKS)
        self.assertEqual(origins[-1], 79)

    def test_direct_h4_uses_only_history_available_at_origin(self):
        frame = pd.DataFrame(
            {
                DATE_COLUMN: pd.date_range("2023-01-02", periods=70, freq="W-MON"),
                TARGET_COLUMN: np.arange(70, dtype=float),
                "hist_signal": np.arange(70, dtype=float) * 10,
                "exog_calendar": np.arange(70, dtype=float) * 100,
            }
        )
        train, test = models.direct_ml_samples(frame, origin=60, horizon=4)
        self.assertEqual(len(train), WINDOW_WEEKS)
        self.assertEqual(float(train[TARGET_COLUMN].iloc[-1]), 59.0)
        self.assertEqual(float(train["hist_signal"].iloc[-1]), 560.0)
        self.assertEqual(float(test["hist_signal"].iloc[0]), 600.0)
        self.assertEqual(float(test["exog_calendar"].iloc[0]), 6300.0)

    def test_monthly_consolidation_sums_four_direct_horizons(self):
        origin = pd.Timestamp("2025-01-06")
        predictions = pd.DataFrame(
            {
                "semana_origen": [origin] * 4,
                "horizonte_semanas": [1, 2, 3, 4],
                "modelo": ["modelo"] * 4,
                "feature_set": ["historico"] * 4,
                "hiperparametros": ["{}"] * 4,
                "real": [10.0, 20.0, 30.0, 40.0],
                "prediccion": [12.0, 18.0, 33.0, 39.0],
            }
        )
        monthly = models.monthly_consolidation(predictions)
        self.assertEqual(len(monthly), 1)
        self.assertEqual(float(monthly.loc[0, "importe_real_4_semanas"]), 100.0)
        self.assertEqual(float(monthly.loc[0, "importe_pronosticado_4_semanas"]), 102.0)

    def test_primary_baseline_is_last_observed_week(self):
        self.assertEqual(PRIMARY_BASELINE, "empirico_ultimo_valor")
        train = pd.DataFrame({TARGET_COLUMN: [0.0, 120.0, 80.0]})
        forecast = models.empirical_forecasts(train, 1)[PRIMARY_BASELINE]
        self.assertEqual(float(forecast[0]), 80.0)

    def test_holm_adjustment_is_monotonic_in_ranked_pvalues(self):
        adjusted = models.holm_adjust(pd.Series([0.01, 0.03, 0.04]))
        np.testing.assert_allclose(adjusted.to_numpy(), np.array([0.03, 0.06, 0.06]))

    def test_diebold_mariano_favors_lower_candidate_loss(self):
        weeks = pd.date_range("2024-01-01", periods=4, freq="W-MON")
        baseline = pd.DataFrame({"semana_prueba": weeks, "error_cuadrado": [4.0, 9.0, 16.0, 25.0]})
        candidate = pd.DataFrame({"semana_prueba": weeks, "error_cuadrado": [1.0, 1.0, 1.0, 1.0]})
        result = models.diebold_mariano_test(baseline, candidate, "prueba")
        self.assertGreater(result["diferencia_media_error_cuadrado"], 0)
        self.assertIn("estadistico_dm", result)

    def test_intermittent_models_return_nonnegative_forecasts(self):
        train = pd.DataFrame(
            {
                TARGET_COLUMN: [0.0, 40.0, 0.0, 80.0, 0.0, 30.0] * 5,
                "hist_signal": np.arange(30, dtype=float),
            }
        )
        test = pd.DataFrame({TARGET_COLUMN: [0.0, 0.0], "hist_signal": [30.0, 31.0]})
        self.assertTrue(np.all(models.forecast_statistical("tsb", train, 2) >= 0))
        for name in ("ridge_log1p", "hurdle_hist_gradient"):
            forecast = models.forecast_ml(name, models.ML_GRIDS[name][0], train, test, ["hist_signal"])
            self.assertEqual(len(forecast), 2)
            self.assertTrue(np.all(np.isfinite(forecast)))
            self.assertTrue(np.all(forecast >= 0))
            if name == "ridge_log1p":
                self.assertTrue(np.all(forecast <= train[TARGET_COLUMN].max()))

    def test_synthetic_targets_are_rejected_from_model_evaluation(self):
        frame = pd.DataFrame(
            {
                DATE_COLUMN: pd.date_range("2024-01-01", periods=2, freq="W-MON"),
                TARGET_COLUMN: [100.0, 120.0],
                "es_sintetico": [0, 1],
            }
        )
        with self.assertRaisesRegex(ValueError, "sintéticas"):
            models.reject_synthetic_targets(frame)

    def test_temporal_analysis_trims_only_unobserved_tail(self):
        frame = pd.DataFrame(
            {
                DATE_COLUMN: pd.date_range("2024-01-01", periods=8, freq="W-MON"),
                time_series.SERIES_COLUMN: [0.0, 10.0, 0.0, 20.0, 0.0, 0.0, 0.0, 0.0],
            }
        )
        observed, tail = time_series.trim_unobserved_tail(frame)
        self.assertEqual(len(observed), 4)
        self.assertEqual(tail, 4)
        self.assertEqual(float(observed.iloc[2][time_series.SERIES_COLUMN]), 0.0)

    def test_intermittency_classification_is_reproducible(self):
        values = np.array([10.0, 0.0, 12.0, 0.0, 11.0, 0.0, 10.0, 0.0])
        result = time_series.classify_intermittency(values)
        self.assertAlmostEqual(float(result["adi"]), 2.0)
        self.assertEqual(result["clasificacion"], "intermitente")

    def test_autocorrelation_table_respects_sample_limit(self):
        values = np.sin(np.arange(40) * 2 * np.pi / 4) + np.arange(40) * 0.01
        result = time_series.autocorrelation_table(values, max_lag=12)
        self.assertEqual(int(result["rezago"].max()), 12)
        self.assertTrue(result["acf"].notna().all())

    def test_primary_coverage_excludes_internal_gap_with_sales(self):
        frame = pd.DataFrame(
            {
                DATE_COLUMN: pd.date_range("2022-01-03", periods=50, freq="W-MON"),
                "compras": [10.0] * 20 + [0.0] * 16 + [20.0] * 14,
                "ventas": [5.0] * 50,
            }
        )
        block, gaps = primary_coverage_block(frame, "compras", activity_column="ventas")
        self.assertEqual(len(block), 20)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps.iloc[0]["motivo"], "brecha interna con actividad comercial")


if __name__ == "__main__":
    unittest.main()
