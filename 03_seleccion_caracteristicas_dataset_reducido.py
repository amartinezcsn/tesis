from __future__ import annotations

"""
Codigo 03: seleccion de caracteristicas y construccion de dataset reducido.

Objetivo:
- Evaluar importancia de variables por objetivo.
- Combinar evidencia estadistica simple y, si esta disponible, aprendizaje automatico.
- Generar un dataset reducido para comparar contra el dataset completo.

Metodos incluidos:
- Correlacion absoluta con cada objetivo.
- Informacion mutua, bosque aleatorio y LassoCV si scikit-learn esta instalado.

Este dataset reducido puede emplearse despues en ARIMA/SARIMA con variables
exogenas, regresion multivariable, arboles, RNN y LSTM.
"""

import numpy as np
import pandas as pd

from config_metodologia import (
    DATE_COLUMN,
    MIN_ABS_TARGET_CORRELATION,
    TARGET_COLUMNS,
    TOP_FEATURES_PER_TARGET,
    classify_feature,
    ensure_output_dir,
    load_model_dataset,
    numeric_predictors,
    temporal_split,
)


def correlation_scores(train: pd.DataFrame, predictors: list[str], target: str) -> pd.DataFrame:
    scores = train[predictors].corrwith(train[target]).abs().fillna(0)
    return pd.DataFrame(
        {
            "variable": scores.index,
            "target": target,
            "metodo": "correlacion_abs",
            "score": scores.values,
        }
    )


def sklearn_scores_if_available(train: pd.DataFrame, predictors: list[str], target: str) -> pd.DataFrame:
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.feature_selection import mutual_info_regression
        from sklearn.linear_model import LassoCV
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return pd.DataFrame(
            {
                "variable": [],
                "target": [],
                "metodo": [],
                "score": [],
            }
        )

    x = train[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
    y = train[target].fillna(0)
    rows = []

    mi = mutual_info_regression(x, y, random_state=42)
    rows.extend(
        {"variable": column, "target": target, "metodo": "informacion_mutua", "score": float(score)}
        for column, score in zip(predictors, mi)
    )

    forest = RandomForestRegressor(n_estimators=400, random_state=42, min_samples_leaf=5, n_jobs=-1)
    forest.fit(x, y)
    rows.extend(
        {"variable": column, "target": target, "metodo": "random_forest", "score": float(score)}
        for column, score in zip(predictors, forest.feature_importances_)
    )

    lasso = make_pipeline(StandardScaler(), LassoCV(cv=5, random_state=42, max_iter=20000))
    lasso.fit(x, y)
    coefs = np.abs(lasso.named_steps["lassocv"].coef_)
    rows.extend(
        {"variable": column, "target": target, "metodo": "lasso_abs_coef", "score": float(score)}
        for column, score in zip(predictors, coefs)
    )

    return pd.DataFrame(rows)


def normalize_scores(scores: pd.DataFrame) -> pd.DataFrame:
    normalized = scores.copy()
    normalized["score_norm"] = normalized.groupby(["target", "metodo"])["score"].transform(
        lambda s: 0 if s.max() == s.min() else (s - s.min()) / (s.max() - s.min())
    )
    return normalized


def select_features(scores: pd.DataFrame) -> pd.DataFrame:
    ranking = (
        scores.groupby(["target", "variable"], as_index=False)
        .agg(score_compuesto=("score_norm", "mean"))
        .sort_values(["target", "score_compuesto"], ascending=[True, False])
    )
    ranking["dimension"] = ranking["variable"].map(classify_feature)
    ranking["rank_target"] = ranking.groupby("target")["score_compuesto"].rank(ascending=False, method="first")
    ranking["seleccionada"] = (
        (ranking["rank_target"] <= TOP_FEATURES_PER_TARGET)
        | (ranking["score_compuesto"] >= MIN_ABS_TARGET_CORRELATION)
    )
    return ranking


def main() -> None:
    out_dir = ensure_output_dir()
    df = load_model_dataset()
    train, _ = temporal_split(df)
    predictors = numeric_predictors(df)

    all_scores = []
    for target in TARGET_COLUMNS:
        all_scores.append(correlation_scores(train, predictors, target))
        all_scores.append(sklearn_scores_if_available(train, predictors, target))

    scores = normalize_scores(pd.concat(all_scores, ignore_index=True))
    ranking = select_features(scores)
    selected = sorted(ranking.loc[ranking["seleccionada"], "variable"].unique().tolist())

    reduced_columns = [DATE_COLUMN] + selected + TARGET_COLUMNS
    reduced = df.loc[:, reduced_columns].copy()

    output_xlsx = out_dir / "03_dataset_reducido_por_seleccion.xlsx"
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        reduced.to_excel(writer, sheet_name="dataset_reducido", index=False)
        ranking.to_excel(writer, sheet_name="ranking_variables", index=False)
        scores.to_excel(writer, sheet_name="scores_metodos", index=False)
        pd.DataFrame(
            {
                "metrica": ["variables_originales", "variables_reducidas", "objetivos"],
                "valor": [len(predictors), len(selected), len(TARGET_COLUMNS)],
            }
        ).to_excel(writer, sheet_name="resumen", index=False)

    print(f"Archivo generado: {output_xlsx}")
    print(f"Variables predictoras seleccionadas: {len(selected)} de {len(predictors)}")


if __name__ == "__main__":
    main()
