"""Construye predictores semanales sin información futura.

Propósito
---------
Crear dos conjuntos de predictores para contrastar H2:
``hist_`` contiene sólo información histórica y ``exog_`` añade calendario,
eventos e indicadores externos disponibles antes de la semana pronosticada.
"""

import math

import numpy as np
import pandas as pd

from config_semanal import (
    ALLOWED_EXOGENOUS_FEATURES,
    DATE_COLUMN,
    EXOGENOUS_REGISTRY,
    exogenous_feature_name,
    LAG_WEEKS,
    PURCHASE_COLUMN,
    ROLLING_WINDOWS,
    SALES_COLUMNS,
    TARGET_COLUMN,
    WEEKLY_MASTER_PATH,
    WEEKLY_MODEL_PATH,
)


def add_lags(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Genera rezagos que sólo usan semanas anteriores."""
    return pd.DataFrame(
        {f"hist_{column}_lag_{lag}s": frame[column].shift(lag) for lag in LAG_WEEKS},
        index=frame.index,
    )


def add_rolling_statistics(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Genera medias y desviaciones móviles desplazadas una semana."""
    source = frame[column].shift(1)
    features: dict[str, pd.Series] = {}
    for window in ROLLING_WINDOWS:
        features[f"hist_{column}_media_{window}s"] = source.rolling(window).mean()
        features[f"hist_{column}_desv_{window}s"] = source.rolling(window).std()
    return pd.DataFrame(features, index=frame.index)


def cyclical_encoding(series: pd.Series, period: int, prefix: str) -> pd.DataFrame:
    """Codifica ciclos sin imponer una distancia lineal entre extremos."""
    angle = 2 * math.pi * series.astype(float) / period
    return pd.DataFrame(
        {f"exog_{prefix}_sin": np.sin(angle), f"exog_{prefix}_cos": np.cos(angle)},
        index=series.index,
    )


def build_weekly_features(weekly: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el dataset semanal listo para modelado.

    ``exog_inpc_publicado`` y ``exog_temperatura_lag_1s`` se retrasan una
    semana. Así no se usa el valor observado durante la semana que se desea
    pronosticar.
    """
    frame = weekly.sort_values(DATE_COLUMN).reset_index(drop=True).copy()
    model = pd.DataFrame({DATE_COLUMN: frame[DATE_COLUMN]})
    model[TARGET_COLUMN] = frame["compras_importe_semanal"].astype(float)

    source_columns = ["compras_importe_semanal", *[c for c in SALES_COLUMNS if c in frame]]
    for column in source_columns:
        model = pd.concat([model, add_lags(frame, column)], axis=1)
        model = pd.concat([model, add_rolling_statistics(frame, column)], axis=1)

    # Calendario y eventos son conocidos al inicio de la semana.
    for source, metadata in EXOGENOUS_REGISTRY.items():
        if metadata["rezago_semanas"] == 0 and source in frame:
            model[exogenous_feature_name(source)] = frame[source].astype(float)
    model = pd.concat([model, cyclical_encoding(frame["semana_anio"], 52, "semana_anio")], axis=1)
    model = pd.concat([model, cyclical_encoding(frame["mes"], 12, "mes")], axis=1)

    # Los indicadores publicados u observados sólo se usan a partir del último
    # valor disponible; el registro central define el rezago de cada fuente.
    for source in ("nacimientos_indice_semanal", "inpc_observado_semana", "temperatura_observada_semana"):
        if source in frame:
            lag = EXOGENOUS_REGISTRY[source]["rezago_semanas"]
            model[exogenous_feature_name(source)] = frame[source].shift(lag)

    # Se requieren 52 semanas completas por el mayor rezago.
    model = model.iloc[max(LAG_WEEKS):].reset_index(drop=True)
    validate_registered_exogenous(model)
    return model.replace([np.inf, -np.inf], np.nan)


def validate_registered_exogenous(model: pd.DataFrame) -> None:
    """Bloquea predictores exógenos sin fuente, disponibilidad o rezago definido."""
    actual = {column for column in model.columns if column.startswith("exog_")}
    unregistered = sorted(actual - ALLOWED_EXOGENOUS_FEATURES)
    if unregistered:
        raise ValueError(
            "Se detectaron variables exógenas no registradas: " + ", ".join(unregistered)
            + ". Regístralas primero en EXOGENOUS_REGISTRY."
        )


def build_dictionary(model: pd.DataFrame) -> pd.DataFrame:
    """Documenta cada variable y su disponibilidad temporal."""
    rows = []
    for column in model.columns:
        if column == DATE_COLUMN:
            group, available = "identificador temporal", "inicio de semana"
        elif column == TARGET_COLUMN:
            group, available = "objetivo", "observado después de cerrar la semana"
        elif column.startswith("hist_"):
            group, available = "histórica", "antes del pronóstico"
        elif column.startswith("exog_"):
            group, available = "exógena", "conocida o publicada antes del pronóstico"
        else:
            group, available = "otra", "revisar"
        source = "derivada del calendario o registro de disponibilidad"
        lag = 0
        for registry_name, metadata in EXOGENOUS_REGISTRY.items():
            if column == exogenous_feature_name(registry_name):
                source, lag = metadata["fuente"], metadata["rezago_semanas"]
                break
        if "nacimientos_indice" in column:
            source, lag = EXOGENOUS_REGISTRY["nacimientos_indice_semanal"]["fuente"], EXOGENOUS_REGISTRY["nacimientos_indice_semanal"]["rezago_semanas"]
        elif "inpc" in column:
            source, lag = EXOGENOUS_REGISTRY["inpc_observado_semana"]["fuente"], EXOGENOUS_REGISTRY["inpc_observado_semana"]["rezago_semanas"]
        elif "temperatura" in column:
            source, lag = EXOGENOUS_REGISTRY["temperatura_observada_semana"]["fuente"], EXOGENOUS_REGISTRY["temperatura_observada_semana"]["rezago_semanas"]
        rows.append({"variable": column, "grupo": group, "disponibilidad": available, "fuente": source, "rezago_semanas": lag})
    return pd.DataFrame(rows)


def main() -> None:
    """Genera el libro semanal de modelado y su diccionario de variables."""
    weekly = pd.read_excel(WEEKLY_MASTER_PATH, sheet_name="semanal")
    weekly[DATE_COLUMN] = pd.to_datetime(weekly[DATE_COLUMN])
    model = build_weekly_features(weekly)
    dictionary = build_dictionary(model)
    summary = pd.DataFrame(
        {
            "metrica": ["semanas_modelado", "predictores_historicos", "predictores_exogenos", "inicio", "fin"],
            "valor": [
                len(model),
                sum(column.startswith("hist_") for column in model.columns),
                sum(column.startswith("exog_") for column in model.columns),
                str(model[DATE_COLUMN].min().date()),
                str(model[DATE_COLUMN].max().date()),
            ],
        }
    )
    with pd.ExcelWriter(WEEKLY_MODEL_PATH, engine="openpyxl") as writer:
        model.to_excel(writer, sheet_name="modelo_semanal", index=False)
        dictionary.to_excel(writer, sheet_name="diccionario", index=False)
        summary.to_excel(writer, sheet_name="resumen", index=False)
    print(f"Archivo generado: {WEEKLY_MODEL_PATH}")


if __name__ == "__main__":
    main()
