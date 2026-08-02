from __future__ import annotations

"""
Codigo 01: perfil del dataset y analisis de dimensiones propuestas.

Objetivo:
- Describir el dataset de modelado.
- Agrupar variables por dimension metodologica.
- Generar estadisticas descriptivas por variable.
- Detectar nulos, variables constantes y variables con muchos ceros.

Este script es el primer insumo para decidir si la dimensionalidad debe reducirse.
"""

import numpy as np
import pandas as pd

from config_metodologia import (
    DATE_COLUMN,
    TARGET_COLUMNS,
    classify_feature,
    ensure_output_dir,
    get_predictor_columns,
    load_model_dataset,
)


def build_variable_profile(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in df.columns:
        serie = df[column]
        is_numeric = pd.api.types.is_numeric_dtype(serie)
        rows.append(
            {
                "variable": column,
                "dimension": classify_feature(column),
                "tipo_dato": str(serie.dtype),
                "nulos": int(serie.isna().sum()),
                "porcentaje_nulos": float(serie.isna().mean()),
                "valores_unicos": int(serie.nunique(dropna=False)),
                "porcentaje_ceros": float((serie.fillna(0) == 0).mean()) if is_numeric else np.nan,
                "media": float(serie.mean()) if is_numeric else np.nan,
                "desviacion": float(serie.std()) if is_numeric else np.nan,
                "minimo": float(serie.min()) if is_numeric else np.nan,
                "p25": float(serie.quantile(0.25)) if is_numeric else np.nan,
                "mediana": float(serie.quantile(0.50)) if is_numeric else np.nan,
                "p75": float(serie.quantile(0.75)) if is_numeric else np.nan,
                "maximo": float(serie.max()) if is_numeric else np.nan,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    out_dir = ensure_output_dir()
    df = load_model_dataset()

    predictors = get_predictor_columns(df)
    profile = build_variable_profile(df)

    dimension_summary = (
        profile.groupby("dimension", as_index=False)
        .agg(
            variables=("variable", "count"),
            nulos_totales=("nulos", "sum"),
            nulos_promedio=("porcentaje_nulos", "mean"),
            ceros_promedio=("porcentaje_ceros", "mean"),
            variables_constantes=("valores_unicos", lambda x: int((x <= 1).sum())),
        )
        .sort_values("variables", ascending=False)
    )

    target_summary = df[TARGET_COLUMNS].describe().T.reset_index().rename(columns={"index": "objetivo"})

    general_summary = pd.DataFrame(
        {
            "metrica": [
                "filas",
                "columnas",
                "predictores",
                "objetivos",
                "fecha_inicio",
                "fecha_fin",
            ],
            "valor": [
                len(df),
                len(df.columns),
                len(predictors),
                len(TARGET_COLUMNS),
                str(df[DATE_COLUMN].min().date()),
                str(df[DATE_COLUMN].max().date()),
            ],
        }
    )

    output_xlsx = out_dir / "01_perfil_dataset_y_dimensiones.xlsx"
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        general_summary.to_excel(writer, sheet_name="resumen_general", index=False)
        dimension_summary.to_excel(writer, sheet_name="resumen_dimensiones", index=False)
        profile.to_excel(writer, sheet_name="perfil_variables", index=False)
        target_summary.to_excel(writer, sheet_name="objetivos", index=False)

    print(f"Archivo generado: {output_xlsx}")


if __name__ == "__main__":
    main()
