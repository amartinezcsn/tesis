from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(r"C:/Users/ramartinez/Documents/Codex/2026-06-26/ana/outputs")
INPUT_FILE = BASE_DIR / "dataset_maestro_diario.xlsx"
OUTPUT_FILE = BASE_DIR / "dataset_modelado_diario.xlsx"


def rolling_features(frame: pd.DataFrame, col: str, windows: list[int]) -> pd.DataFrame:
    shifted = frame[col].shift(1)
    out = {}
    for w in windows:
        out[f"{col}_roll{w}_mean"] = shifted.rolling(w).mean()
        out[f"{col}_roll{w}_std"] = shifted.rolling(w).std()
        out[f"{col}_roll{w}_sum"] = shifted.rolling(w).sum()
    return pd.DataFrame(out, index=frame.index)


def lag_features(frame: pd.DataFrame, col: str, lags: list[int]) -> pd.DataFrame:
    return pd.DataFrame({f"{col}_lag{lag}": frame[col].shift(lag) for lag in lags}, index=frame.index)


def streak_since_nonzero(series: pd.Series) -> pd.Series:
    values = series.to_numpy()
    idx = np.arange(len(values))
    last = np.full(len(values), -1, dtype=int)
    current = -1
    for i, v in enumerate(values):
        last[i] = current
        if pd.notna(v) and v > 0:
            current = i
    out = idx - last
    return pd.Series(out, index=series.index, dtype=float)


def days_to_next_flag(flag: pd.Series) -> pd.Series:
    values = flag.to_numpy(dtype=int)
    n = len(values)
    next_idx = np.full(n, n, dtype=int)
    current = n
    for i in range(n - 1, -1, -1):
        next_idx[i] = current
        if values[i] == 1:
            current = i
    out = next_idx - np.arange(n)
    return pd.Series(out, index=flag.index, dtype=float)


def days_since_last_flag(flag: pd.Series) -> pd.Series:
    values = flag.to_numpy(dtype=int)
    last_idx = np.full(len(values), -1, dtype=int)
    current = -1
    for i, v in enumerate(values):
        last_idx[i] = current
        if v == 1:
            current = i
    out = np.arange(len(values)) - last_idx
    return pd.Series(out, index=flag.index, dtype=float)


def cyclical_encoding(series: pd.Series, period: float, prefix: str) -> pd.DataFrame:
    angle = 2 * math.pi * series.astype(float) / period
    return pd.DataFrame(
        {
            f"{prefix}_sin": np.sin(angle),
            f"{prefix}_cos": np.cos(angle),
        },
        index=series.index,
    )


def build_dictionary(columns: list[str]) -> pd.DataFrame:
    rows = []
    for col in columns:
        if col == "fecha":
            rows.append((col, "Identificador temporal diario", "Fecha de observación"))
        elif col.startswith("target_"):
            if "ventas" in col:
                rows.append((col, "Objetivo de demanda", "Valor observado de ventas ajustado por inflación"))
            elif "compras" in col:
                rows.append((col, "Objetivo de compras", "Valor observado de compras ajustado por inflación"))
            else:
                rows.append((col, "Objetivo", "Variable objetivo"))
        elif col.startswith("clima_"):
            rows.append((col, "Clima codificado", "Variable dummy del clima"))
        elif col in {
            "anio",
            "mes",
            "trimestre",
            "dia_mes",
            "dia_semana",
            "dia_anio",
            "semana_anio",
            "es_fin_de_semana",
            "es_inicio_mes",
            "es_fin_mes",
            "dias_mes",
            "dias_hasta_fin_mes",
            "dias_desde_inicio_mes",
            "es_festivo_mexicano",
            "es_fecha_pago",
            "nacimientos_indice",
            "temperatura_promedio_mensual_hidalgo",
            "inpc_valor_mensual",
            "dias_desde_festivo",
            "dias_hasta_festivo",
            "dias_desde_pago",
            "dias_hasta_pago",
            "festivos_7d",
            "festivos_30d",
            "pagos_7d",
            "pagos_30d",
            "dias_desde_ultima_venta",
            "dias_desde_ultima_compra",
            "ventas_vs_compras_ratio_7d",
            "ventas_minus_compras_7d",
        }:
            rows.append((col, "Calendario / exógena", "Variable de calendario o externa"))
        elif re.search(r"_lag\d+$", col):
            rows.append((col, "Rezago", "Valor histórico rezagado"))
        elif re.search(r"_roll\d+_(mean|std|sum)$", col):
            rows.append((col, "Ventana móvil", "Estadístico calculado sobre valores históricos"))
        else:
            rows.append((col, "Variable derivada", "Variable construida para modelado"))
    return pd.DataFrame(rows, columns=["variable", "grupo", "descripcion"])


def main() -> None:
    raw = pd.read_excel(INPUT_FILE, sheet_name="maestro")
    raw["fecha"] = pd.to_datetime(raw["fecha"])
    raw = raw.sort_values("fecha").reset_index(drop=True)

    work = pd.DataFrame({"fecha": raw["fecha"]})
    date_index = work["fecha"]

    # Calendar and seasonal features.
    work["anio"] = date_index.dt.year.astype(int)
    work["mes"] = date_index.dt.month.astype(int)
    work["trimestre"] = date_index.dt.quarter.astype(int)
    work["dia_mes"] = date_index.dt.day.astype(int)
    work["dia_semana"] = date_index.dt.dayofweek.astype(int)
    work["dia_anio"] = date_index.dt.dayofyear.astype(int)
    work["semana_anio"] = date_index.dt.isocalendar().week.astype(int)
    work["es_fin_de_semana"] = (work["dia_semana"] >= 5).astype(int)
    work["es_inicio_mes"] = (work["dia_mes"] <= 3).astype(int)
    work["es_fin_mes"] = (date_index.dt.is_month_end).astype(int)
    work["dias_mes"] = date_index.dt.days_in_month.astype(int)
    work["dias_hasta_fin_mes"] = work["dias_mes"] - work["dia_mes"]
    work["dias_desde_inicio_mes"] = work["dia_mes"] - 1
    work = pd.concat([work, cyclical_encoding(work["mes"], 12, "mes")], axis=1)
    work = pd.concat([work, cyclical_encoding(work["dia_semana"], 7, "dia_semana")], axis=1)
    work = pd.concat([work, cyclical_encoding(work["dia_anio"], 365.25, "dia_anio")], axis=1)

    # Exogenous and event features.
    exog_cols = [
        "es_festivo_mexicano",
        "es_fecha_pago",
        "nacimientos_indice",
        "temperatura_promedio_mensual_hidalgo",
        "inpc_valor_mensual",
        "clima_DESPEJADO",
        "clima_LLUVIOSO",
        "clima_SIN_DATO",
        "clima_SOLEADO",
    ]
    work = pd.concat([work, raw[exog_cols].reset_index(drop=True)], axis=1)
    work["dias_desde_festivo"] = days_since_last_flag(work["es_festivo_mexicano"])
    work["dias_hasta_festivo"] = days_to_next_flag(work["es_festivo_mexicano"])
    work["dias_desde_pago"] = days_since_last_flag(work["es_fecha_pago"])
    work["dias_hasta_pago"] = days_to_next_flag(work["es_fecha_pago"])
    work["festivos_7d"] = work["es_festivo_mexicano"].shift(1).rolling(7).sum()
    work["festivos_30d"] = work["es_festivo_mexicano"].shift(1).rolling(30).sum()
    work["pagos_7d"] = work["es_fecha_pago"].shift(1).rolling(7).sum()
    work["pagos_30d"] = work["es_fecha_pago"].shift(1).rolling(30).sum()

    # Historical series used only as lagged predictors.
    aggregate_series = [
        "ventas_importe_real_2026_05",
        "ventas_ganancia_real_2026_05",
        "ventas_registros",
        "ventas_cantidad_total",
        "compras_total_real_2026_05",
        "compras_registros",
        "compras_cantidad_total",
    ]
    lag_set = [1, 2, 3, 7, 14, 28]
    roll_set = [7, 14, 28]
    for col in aggregate_series:
        work = pd.concat([work, lag_features(raw, col, lag_set)], axis=1)
        work = pd.concat([work, rolling_features(raw, col, roll_set)], axis=1)

    # Sales composition and purchase composition, also lagged.
    sales_parts = ["ventas_pastel", "ventas_galletas", "ventas_otros", "ventas_cupcakes"]
    purchase_parts = [
        c
        for c in raw.columns
        if c.startswith("compras_") and c.endswith("_real_2026_05") and c != "compras_total_real_2026_05"
    ]
    for col in sales_parts + purchase_parts:
        work = pd.concat([work, lag_features(raw, col, [1, 7])], axis=1)
        work[f"{col}_roll7_mean"] = raw[col].shift(1).rolling(7).mean()

    # Additional stability features.
    work["ventas_vs_compras_ratio_7d"] = (
        work["ventas_importe_real_2026_05_roll7_mean"] / work["compras_total_real_2026_05_roll7_mean"].replace(0, np.nan)
    )
    work["ventas_minus_compras_7d"] = (
        work["ventas_importe_real_2026_05_roll7_mean"] - work["compras_total_real_2026_05_roll7_mean"]
    )
    work["dias_desde_ultima_venta"] = streak_since_nonzero(raw["ventas_importe_real_2026_05"])
    work["dias_desde_ultima_compra"] = streak_since_nonzero(raw["compras_total_real_2026_05"])

    # Targets for supervised learning.
    work["target_ventas_importe_real_2026_05"] = raw["ventas_importe_real_2026_05"]
    work["target_compras_total_real_2026_05"] = raw["compras_total_real_2026_05"]
    work["target_ventas_registros"] = raw["ventas_registros"]
    work["target_compras_registros"] = raw["compras_registros"]

    # Remove rows without sufficient history for the rolling/lag features.
    min_history = 28
    model = work.iloc[min_history:].reset_index(drop=True)

    # Ensure a clean modelling table without missing values.
    model = model.replace([np.inf, -np.inf], np.nan)
    null_cols = [c for c in model.columns if model[c].isna().any()]
    if null_cols:
        for c in null_cols:
            if c in {
                "ventas_vs_compras_ratio_7d",
            }:
                model[c] = model[c].fillna(0)
        model = model.fillna(0)

    # Keep an explicit ordering: date, features, targets.
    target_cols = [
        "target_ventas_importe_real_2026_05",
        "target_compras_total_real_2026_05",
        "target_ventas_registros",
        "target_compras_registros",
    ]
    feature_cols = [c for c in model.columns if c not in target_cols and c != "fecha"]
    ordered_cols = ["fecha"] + feature_cols + target_cols
    model = model.loc[:, ordered_cols]

    dictionary = build_dictionary(model.columns.tolist())
    summary = pd.DataFrame(
        {
            "métrica": [
                "filas",
                "columnas",
                "fecha_inicio",
                "fecha_fin",
                "min_history_eliminado",
            ],
            "valor": [
                len(model),
                len(model.columns),
                str(model["fecha"].min().date()),
                str(model["fecha"].max().date()),
                str(min_history),
            ],
        }
    )

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        model.to_excel(writer, sheet_name="modelo", index=False)
        dictionary.to_excel(writer, sheet_name="diccionario", index=False)
        summary.to_excel(writer, sheet_name="resumen", index=False)

    md = [
        "# Ingeniería de Características",
        "",
        "## Salida generada",
        f"- Archivo: `dataset_modelado_diario.xlsx`",
        f"- Filas: {len(model)}",
        f"- Columnas: {len(model.columns)}",
        f"- Rango: {model['fecha'].min().date()} a {model['fecha'].max().date()}",
        "",
        "## Objetivos",
        "- `target_ventas_importe_real_2026_05`",
        "- `target_compras_total_real_2026_05`",
        "",
        "## Estrategia",
        "- Variables de calendario y estacionalidad",
        "- Codificación cíclica",
        "- Proximidad a festivos y fechas de pago",
        "- Rezagos de 1, 2, 3, 7, 14 y 28 días",
        "- Ventanas móviles de 7, 14 y 28 días",
        "- Rezagos de composición de ventas y compras",
        "- Variables de estabilidad y tendencia",
        "",
        "## Nota",
        "La tabla resultante elimina los primeros 28 días para asegurar que los rezagos y ventanas móviles estén completos.",
    ]
    (BASE_DIR / "feature_engineering_resumen.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
