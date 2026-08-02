from __future__ import annotations

"""
Pipeline de ingeniería de características para el conjunto de datos diario de modelado.

Este script lee el conjunto de datos maestro diario ya unificado y lo transforma en
un panel listo para modelar con:
- variables de calendario y estacionalidad,
- codificaciones cíclicas,
- características de proximidad a eventos,
- predictores rezagados,
- estadísticas de ventanas móviles,
- objetivos de demanda y compras.

El diseño evita filtraciones al desplazar todas las agregaciones históricas un día
hacia atrás antes de calcular los resúmenes móviles.
"""

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# Rutas y configuración global
# -----------------------------------------------------------------------------
BASE_DIR = Path(r"C:/Python/tesis/input")
INPUT_FILE = BASE_DIR / "dataset_maestro_diario.xlsx"
OUTPUT_FILE = BASE_DIR / "dataset_modelado_diario.xlsx"
SUMMARY_FILE = BASE_DIR / "feature_engineering_resumen.md"

# Historial requerido para soportar la ventana móvil y el rezago más grandes.
MIN_HISTORY = 28


# -----------------------------------------------------------------------------
# Constructores pequeños y reutilizables de características
# -----------------------------------------------------------------------------
def add_lag_features(frame: pd.DataFrame, column: str, lags: list[int]) -> pd.DataFrame:
    """Devuelve un DataFrame con versiones rezagadas de una variable."""
    return pd.DataFrame(
        {f"{column}_lag{lag}": frame[column].shift(lag) for lag in lags},
        index=frame.index,
    )


def add_rolling_features(frame: pd.DataFrame, column: str, windows: list[int]) -> pd.DataFrame:
    """
    Devuelve estadísticas móviles para una variable.

    La serie fuente se desplaza un día hacia atrás antes de aplicar la ventana
    móvil para que el modelo solo vea valores disponibles estrictamente antes de
    la fecha de predicción.
    """
    source = frame[column].shift(1)
    features = {}
    for window in windows:
        features[f"{column}_roll{window}_mean"] = source.rolling(window).mean()
        features[f"{column}_roll{window}_std"] = source.rolling(window).std()
        features[f"{column}_roll{window}_sum"] = source.rolling(window).sum()
    return pd.DataFrame(features, index=frame.index)


def streak_since_nonzero(series: pd.Series) -> pd.Series:
    """
    Cuenta cuántos días han pasado desde la última observación distinta de cero.

    Útil como proxy de inactividad o de recencia de compras/ventas.
    """
    values = series.to_numpy()
    index = np.arange(len(values))
    last_seen = np.full(len(values), -1, dtype=int)
    current = -1

    for i, value in enumerate(values):
        last_seen[i] = current
        if pd.notna(value) and value > 0:
            current = i

    return pd.Series(index - last_seen, index=series.index, dtype=float)


def days_since_last_flag(flag: pd.Series) -> pd.Series:
    """Días desde el último 1 en una bandera binaria."""
    values = flag.to_numpy(dtype=int)
    last_seen = np.full(len(values), -1, dtype=int)
    current = -1
    for i, value in enumerate(values):
        last_seen[i] = current
        if value == 1:
            current = i
    return pd.Series(np.arange(len(values)) - last_seen, index=flag.index, dtype=float)


def days_to_next_flag(flag: pd.Series) -> pd.Series:
    """Días hasta el próximo 1 en una bandera binaria."""
    values = flag.to_numpy(dtype=int)
    n = len(values)
    next_seen = np.full(n, n, dtype=int)
    current = n
    for i in range(n - 1, -1, -1):
        next_seen[i] = current
        if values[i] == 1:
            current = i
    return pd.Series(next_seen - np.arange(n), index=flag.index, dtype=float)


def cyclical_encoding(series: pd.Series, period: float, prefix: str) -> pd.DataFrame:
    """
    Codifica variables periódicas mediante transformaciones seno/coseno.

    Esta representación es más adecuada que los enteros crudos para redes
    neuronales y muchos algoritmos de ML porque preserva la circularidad.
    """
    angle = 2 * math.pi * series.astype(float) / period
    return pd.DataFrame(
        {
            f"{prefix}_sin": np.sin(angle),
            f"{prefix}_cos": np.cos(angle),
        },
        index=series.index,
    )


def build_dictionary(columns: list[str]) -> pd.DataFrame:
    """
    Construye un diccionario compacto de datos para el conjunto de datos ingenierizado.

    El diccionario es intencionalmente simple para que pueda pegarse en la
    metodología o en las secciones de anexos de la tesis.
    """
    calendar_cols = {
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
    }

    rows = []
    for column in columns:
        if column == "fecha":
            rows.append((column, "Identificador temporal diario", "Fecha de observación"))
        elif column.startswith("target_"):
            if "ventas" in column:
                rows.append((column, "Objetivo de demanda", "Variable objetivo de ventas ajustada por inflación"))
            elif "compras" in column:
                rows.append((column, "Objetivo de compras", "Variable objetivo de compras ajustada por inflación"))
            else:
                rows.append((column, "Objetivo", "Variable objetivo"))
        elif column.startswith("clima_"):
            rows.append((column, "Clima codificado", "Variable dummy del clima"))
        elif column in calendar_cols:
            rows.append((column, "Calendario / exógena", "Variable de calendario o externa"))
        elif re.search(r"_lag\d+$", column):
            rows.append((column, "Rezago", "Valor histórico rezagado"))
        elif re.search(r"_roll\d+_(mean|std|sum)$", column):
            rows.append((column, "Ventana móvil", "Estadístico calculado sobre historial"))
        else:
            rows.append((column, "Variable derivada", "Variable construida para modelado"))

    return pd.DataFrame(rows, columns=["variable", "grupo", "descripcion"])


# -----------------------------------------------------------------------------
# Pipeline principal de ingeniería de características
# -----------------------------------------------------------------------------
def main() -> None:
    # Lee el conjunto de datos maestro diario y lo ordena cronológicamente.
    master = pd.read_excel(INPUT_FILE, sheet_name="maestro")
    master["fecha"] = pd.to_datetime(master["fecha"])
    master = master.sort_values("fecha").reset_index(drop=True)

    features = pd.DataFrame({"fecha": master["fecha"]})
    date_index = features["fecha"]

    # -------------------------------------------------------------------------
    # 1) Características de calendario y estacionalidad
    # -------------------------------------------------------------------------
    features["anio"] = date_index.dt.year.astype(int)
    features["mes"] = date_index.dt.month.astype(int)
    features["trimestre"] = date_index.dt.quarter.astype(int)
    features["dia_mes"] = date_index.dt.day.astype(int)
    features["dia_semana"] = date_index.dt.dayofweek.astype(int)
    features["dia_anio"] = date_index.dt.dayofyear.astype(int)
    features["semana_anio"] = date_index.dt.isocalendar().week.astype(int)
    features["es_fin_de_semana"] = (features["dia_semana"] >= 5).astype(int)
    features["es_inicio_mes"] = (features["dia_mes"] <= 3).astype(int)
    features["es_fin_mes"] = date_index.dt.is_month_end.astype(int)
    features["dias_mes"] = date_index.dt.days_in_month.astype(int)
    features["dias_hasta_fin_mes"] = features["dias_mes"] - features["dia_mes"]
    features["dias_desde_inicio_mes"] = features["dia_mes"] - 1

    features = pd.concat([features, cyclical_encoding(features["mes"], 12, "mes")], axis=1)
    features = pd.concat([features, cyclical_encoding(features["dia_semana"], 7, "dia_semana")], axis=1)
    features = pd.concat([features, cyclical_encoding(features["dia_anio"], 365.25, "dia_anio")], axis=1)

    # -------------------------------------------------------------------------
    # 2) Variables exógenas y características de proximidad a eventos
    # -------------------------------------------------------------------------
    exogenous_columns = [
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
    features = pd.concat([features, master[exogenous_columns].reset_index(drop=True)], axis=1)

    features["dias_desde_festivo"] = days_since_last_flag(features["es_festivo_mexicano"])
    features["dias_hasta_festivo"] = days_to_next_flag(features["es_festivo_mexicano"])
    features["dias_desde_pago"] = days_since_last_flag(features["es_fecha_pago"])
    features["dias_hasta_pago"] = days_to_next_flag(features["es_fecha_pago"])
    features["festivos_7d"] = features["es_festivo_mexicano"].shift(1).rolling(7).sum()
    features["festivos_30d"] = features["es_festivo_mexicano"].shift(1).rolling(30).sum()
    features["pagos_7d"] = features["es_fecha_pago"].shift(1).rolling(7).sum()
    features["pagos_30d"] = features["es_fecha_pago"].shift(1).rolling(30).sum()

    # -------------------------------------------------------------------------
    # 3) Predictores rezagados y móviles para la serie principal
    # -------------------------------------------------------------------------
    target_series = [
        "ventas_importe_real_2026_05",
        "ventas_ganancia_real_2026_05",
        "ventas_registros",
        "ventas_cantidad_total",
        "compras_total_real_2026_05",
        "compras_registros",
        "compras_cantidad_total",
    ]
    lag_windows = [1, 2, 3, 7, 14, 28]
    rolling_windows = [7, 14, 28]

    for column in target_series:
        features = pd.concat([features, add_lag_features(master, column, lag_windows)], axis=1)
        features = pd.concat([features, add_rolling_features(master, column, rolling_windows)], axis=1)

    # -------------------------------------------------------------------------
    # 4) Composición y comportamiento por categorías
    # -------------------------------------------------------------------------
    sales_components = ["ventas_pastel", "ventas_galletas", "ventas_otros", "ventas_cupcakes"]
    purchase_components = [
        column
        for column in master.columns
        if column.startswith("compras_") and column.endswith("_real_2026_05") and column != "compras_total_real_2026_05"
    ]

    for column in sales_components + purchase_components:
        features = pd.concat([features, add_lag_features(master, column, [1, 7])], axis=1)
        features[f"{column}_roll7_mean"] = master[column].shift(1).rolling(7).mean()

    # -------------------------------------------------------------------------
    # 5) Indicadores de estabilidad y tendencia
    # -------------------------------------------------------------------------
    features["ventas_vs_compras_ratio_7d"] = (
        features["ventas_importe_real_2026_05_roll7_mean"]
        / features["compras_total_real_2026_05_roll7_mean"].replace(0, np.nan)
    )
    features["ventas_minus_compras_7d"] = (
        features["ventas_importe_real_2026_05_roll7_mean"] - features["compras_total_real_2026_05_roll7_mean"]
    )
    features["dias_desde_ultima_venta"] = streak_since_nonzero(master["ventas_importe_real_2026_05"])
    features["dias_desde_ultima_compra"] = streak_since_nonzero(master["compras_total_real_2026_05"])

    # -------------------------------------------------------------------------
    # 6) Objetivos de aprendizaje supervisado
    # -------------------------------------------------------------------------
    features["target_ventas_importe_real_2026_05"] = master["ventas_importe_real_2026_05"]
    features["target_compras_total_real_2026_05"] = master["compras_total_real_2026_05"]
    features["target_ventas_registros"] = master["ventas_registros"]
    features["target_compras_registros"] = master["compras_registros"]

    # Elimina las primeras filas que no tienen suficiente historial para los rezagos.
    model = features.iloc[MIN_HISTORY:].reset_index(drop=True)

    # Maneja las pocas divisiones entre cero que pueden aparecer en las características de razón.
    model = model.replace([np.inf, -np.inf], np.nan)
    model["ventas_vs_compras_ratio_7d"] = model["ventas_vs_compras_ratio_7d"].fillna(0)
    model = model.fillna(0)

    # Organiza las columnas para mayor legibilidad: fecha, predictores y objetivos.
    target_columns = [
        "target_ventas_importe_real_2026_05",
        "target_compras_total_real_2026_05",
        "target_ventas_registros",
        "target_compras_registros",
    ]
    predictor_columns = [column for column in model.columns if column not in target_columns and column != "fecha"]
    model = model.loc[:, ["fecha"] + predictor_columns + target_columns]

    # Construye el diccionario de datos y un resumen breve de ejecución.
    dictionary = build_dictionary(model.columns.tolist())
    summary = pd.DataFrame(
        {
            "métrica": ["filas", "columnas", "fecha_inicio", "fecha_fin", "historial_eliminado"],
            "valor": [
                len(model),
                len(model.columns),
                str(model["fecha"].min().date()),
                str(model["fecha"].max().date()),
                str(MIN_HISTORY),
            ],
        }
    )

    # Exporta todo a un único libro de Excel.
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        model.to_excel(writer, sheet_name="modelo", index=False)
        dictionary.to_excel(writer, sheet_name="diccionario", index=False)
        summary.to_excel(writer, sheet_name="resumen", index=False)

    # También escribe una breve nota en Markdown para la documentación de la tesis.
    md = [
        "# Ingeniería de Características",
        "",
        "## Salida generada",
        "- Archivo: `dataset_modelado_diario.xlsx`",
        f"- Filas: {len(model)}",
        f"- Columnas: {len(model.columns)}",
        f"- Rango: {model['fecha'].min().date()} a {model['fecha'].max().date()}",
        "",
        "## Objetivos",
        "- `target_ventas_importe_real_2026_05`",
        "- `target_compras_total_real_2026_05`",
        "",
        "## Estrategia de modelado",
        "- Variables de calendario y estacionalidad",
        "- Codificación cíclica de mes, día de semana y día del año",
        "- Proximidad a festivos y fechas de pago",
        "- Rezagos de 1, 2, 3, 7, 14 y 28 días",
        "- Ventanas móviles de 7, 14 y 28 días",
        "- Rezagos por categorías de ventas y compras",
        "- Variables de estabilidad y tendencia",
        "",
        "## Nota metodológica",
        f"- Se eliminaron los primeros {MIN_HISTORY} días para garantizar que los rezagos y ventanas móviles estuvieran completos.",
    ]
    SUMMARY_FILE.write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
