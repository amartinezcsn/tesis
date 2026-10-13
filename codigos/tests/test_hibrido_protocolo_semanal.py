"""Regresiones del protocolo real para la sensibilidad rolling semanal."""
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codigos"))

from hibrido.config import load_config
from hibrido.data import load_purchases, read_table
from hibrido.features import partitions
from hibrido.gaps import build_gap_panel


class WeeklyRollingProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.step3 = load_config(ROOT / "codigos" / "02_config_hibrido.json")
        cls.step1 = load_config(
            ROOT / "codigos" / "02_config_hibrido_sensibilidad_step1.json"
        )
        cls.step1_no_imputation = load_config(
            ROOT
            / "codigos"
            / "02_config_hibrido_sensibilidad_step1_sin_imputacion.json"
        )
        cls.ablations = {
            name: load_config(ROOT / "codigos" / filename)
            for name, filename in {
                "compras": "02_config_ablacion_compras_step1.json",
                "compras_ventas": "02_config_ablacion_compras_ventas_step1.json",
                "compras_calendario": "02_config_ablacion_compras_calendario_step1.json",
                "compras_ventas_calendario": "02_config_hibrido_sensibilidad_step1_sin_imputacion.json",
            }.items()
        }
        purchases, rejected = load_purchases(
            ROOT / cls.step1.source,
            cls.step1.source_sheet,
            approved_duplicate_rows=cls.step1.approved_duplicate_rows,
        )
        if not rejected.empty:
            raise AssertionError("La fuente canónica volvió a producir pendientes.")
        cls.panel, _ = build_gap_panel(
            purchases,
            read_table(ROOT / cls.step1.coverage, cls.step1.coverage_sheet),
            read_table(ROOT / cls.step1.catalog, cls.step1.catalog_sheet),
            cls.step1.start,
            cls.step1.end,
            cls.step1.zero_targets_valid,
            cls.step1.excluded_budget_categories,
        )

    def test_step1_changes_only_rolling_stride(self):
        old = self.step3.dictionary()
        new = self.step1.dictionary()
        for key in ("horizons", "weights", "alphas", "excluded_budget_categories"):
            old[key] = tuple(old[key])
            new[key] = tuple(new[key])
        differences = {key for key in old if old[key] != new[key]}
        self.assertEqual(differences, {"rolling_step_weeks"})
        self.assertEqual(old["rolling_step_weeks"], 3)
        self.assertEqual(new["rolling_step_weeks"], 1)

    def test_no_imputation_variant_changes_only_reporting_parameters(self):
        with_imputation = self.step1.dictionary()
        without_imputation = self.step1_no_imputation.dictionary()
        differences = {
            key for key in with_imputation
            if with_imputation[key] != without_imputation[key]
        }
        self.assertEqual(differences, {"imputation_start", "imputation_end"})
        self.assertIsNone(without_imputation["imputation_start"])
        self.assertIsNone(without_imputation["imputation_end"])

    def test_real_calendar_and_weekly_evaluation_counts(self):
        self.assertEqual(len(self.panel), 493)
        self.assertTrue((self.panel.index.dayofweek == 0).all())
        self.assertTrue((self.panel.index.to_series().diff().dropna() == pd.Timedelta(weeks=1)).all())
        self.assertEqual(int(self.panel.total.notna().sum()), 416)
        self.assertEqual(self.panel.total.last_valid_index(), pd.Timestamp("2025-07-28"))

        cutoff, tuning, evaluation, folds = partitions(self.panel, self.step1)
        evaluation_folds = folds.loc[folds.etapa == "evaluacion"]
        self.assertEqual(len(tuning), 5)
        self.assertEqual(len(evaluation), 17)
        self.assertEqual(len(evaluation_folds), 68)
        self.assertTrue(evaluation_folds.objetivo_observado.all())
        self.assertEqual(self.panel.index[cutoff], pd.Timestamp("2025-03-17"))

    def test_partitions_are_purged_and_never_train_on_origin_or_target(self):
        cutoff, tuning, evaluation, folds = partitions(self.panel, self.step1)
        max_horizon = max(self.step1.horizons)
        self.assertLess(max(tuning) + max_horizon - 1, cutoff)
        self.assertGreaterEqual(min(evaluation), cutoff)
        self.assertTrue((folds.ultima_etiqueta_entrenamiento < folds.origen).all())
        expected_target = folds.origen + pd.to_timedelta(folds.horizonte - 1, unit="W")
        pd.testing.assert_series_equal(
            folds.fecha_objetivo.reset_index(drop=True),
            expected_target.reset_index(drop=True),
            check_names=False,
        )
        expected_start = folds.origen - pd.Timedelta(weeks=52)
        pd.testing.assert_series_equal(
            folds.entrenamiento_inicio.reset_index(drop=True),
            expected_start.reset_index(drop=True),
            check_names=False,
        )

    def test_ablation_configs_change_only_optional_predictor_sources(self):
        reference = self.ablations["compras_ventas_calendario"].dictionary()
        _, ref_tuning, ref_evaluation, ref_folds = partitions(
            self.panel, self.ablations["compras_ventas_calendario"]
        )
        for name, cfg in self.ablations.items():
            candidate = cfg.dictionary()
            differences = {
                key for key in reference if reference[key] != candidate[key]
            }
            self.assertLessEqual(differences, {"sales", "exogenous"}, name)
            _, tuning, evaluation, folds = partitions(self.panel, cfg)
            self.assertEqual(tuning, ref_tuning, name)
            self.assertEqual(evaluation, ref_evaluation, name)
            pd.testing.assert_frame_equal(folds, ref_folds)


if __name__ == "__main__":
    unittest.main()
