from __future__ import annotations

"""
Codigo 02: diagnostico de multicolinealidad y redundancia.

Objetivo:
- Medir correlacion entre predictores.
- Identificar pares altamente correlacionados.
- Proponer variables a eliminar por redundancia.
- Calcular VIF si statsmodels esta instalado.

Interpretacion:
- Correlaciones altas entre rezagos, medias moviles y sumas moviles son esperadas.
- La reduccion debe conservar interpretabilidad financiera y poder predictivo.
"""

import numpy as np
import pandas as pd

from config_metodologia import (
    HIGH_CORRELATION_THRESHOLD,
    TARGET_COLUMNS,
    classify_feature,
    ensure_output_dir,
    load_model_dataset,
    numeric_predictors,
)


def high_correlation_pairs(corr: pd.DataFrame, threshold: float) -> pd.DataFrame:
    mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
    pairs = corr.where(mask).stack().reset_index()
    pairs.columns = ["variable_1", "variable_2", "correlacion_abs"]
    return pairs[pairs["correlacion_abs"] >= threshold].sort_values("correlacion_abs", ascending=False)


def greedy_correlation_filter(
    x: pd.DataFrame,
    y: pd.Series,
    threshold: float = HIGH_CORRELATION_THRESHOLD,
) -> tuple[list[str], list[dict]]:
    """
    Conserva, entre variables muy correlacionadas, la que tenga mayor relacion
    absoluta con el objetivo analizado.
    """
    corr_x = x.corr().abs()
    corr_y = x.corrwith(y).abs().fillna(0)
    remaining = set(x.columns)
    decisions = []

    pairs = high_correlation_pairs(corr_x, threshold)
    for _, row in pairs.iterrows():
        a = row["variable_1"]
        b = row["variable_2"]
        if a not in remaining or b not in remaining:
            continue
        drop = a if corr_y[a] < corr_y[b] else b
        keep = b if drop == a else a
        remaining.remove(drop)
        decisions.append(
            {
                "variable_conservada": keep,
                "variable_eliminada": drop,
                "correlacion_abs": row["correlacion_abs"],
                "corr_objetivo_conservada": corr_y[keep],
                "corr_objetivo_eliminada": corr_y[drop],
            }
        )
    return sorted(remaining), decisions


def calculate_vif_if_available(x: pd.DataFrame) -> pd.DataFrame:
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
    except ImportError:
        return pd.DataFrame(
            {
                "nota": [
                    "Para calcular VIF instala statsmodels: pip install statsmodels",
                ]
            }
        )

    sample = x.replace([np.inf, -np.inf], np.nan).fillna(0)
    variances = sample.var()
    sample = sample.loc[:, variances > 0]

    # El VIF es costoso con muchas variables. Se limita a las 80 de mayor varianza.
    top_columns = variances.sort_values(ascending=False).head(80).index.tolist()
    sample = sample[top_columns]

    rows = []
    values = sample.to_numpy(dtype=float)
    for idx, column in enumerate(sample.columns):
        rows.append({"variable": column, "vif": float(variance_inflation_factor(values, idx))})
    return pd.DataFrame(rows).sort_values("vif", ascending=False)


def main() -> None:
    out_dir = ensure_output_dir()
    df = load_model_dataset()
    predictors = numeric_predictors(df)
    x = df[predictors].copy()

    corr = x.corr().abs()
    pairs = high_correlation_pairs(corr, HIGH_CORRELATION_THRESHOLD)

    with pd.ExcelWriter(out_dir / "02_diagnostico_multicolinealidad.xlsx", engine="openpyxl") as writer:
        pairs.to_excel(writer, sheet_name="pares_correlacion_alta", index=False)

        for target in TARGET_COLUMNS:
            kept, decisions = greedy_correlation_filter(x, df[target], HIGH_CORRELATION_THRESHOLD)
            pd.DataFrame(decisions).to_excel(writer, sheet_name=f"filtro_{target[:20]}", index=False)
            pd.DataFrame(
                {
                    "variable": kept,
                    "dimension": [classify_feature(column) for column in kept],
                }
            ).to_excel(writer, sheet_name=f"conservadas_{target[:18]}", index=False)

        calculate_vif_if_available(x).to_excel(writer, sheet_name="vif_opcional", index=False)

    print(f"Archivo generado: {out_dir / '02_diagnostico_multicolinealidad.xlsx'}")


if __name__ == "__main__":
    main()
