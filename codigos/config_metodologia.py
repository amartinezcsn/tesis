from __future__ import annotations

"""
Configuracion comun para los codigos de analisis dimensional y modelado.

Tema de tesis:
DE LA INTUICION A LA INTELIGENCIA ARTIFICIAL: TRANSFORMACION PREDICTIVA DE
LA PLANEACION FINANCIERA EN UNA MICROEMPRESA MEDIANTE INTELIGENCIA DE
NEGOCIOS CON MODELOS DE APRENDIZAJE AUTOMATICO.

La metodologia mantiene particion temporal para evitar fuga de informacion:
las fechas antiguas entrenan y las fechas recientes validan/prueban.
"""

from pathlib import Path
import re

import pandas as pd


DATASET_PATH = Path(r"C:/Python/tesis/input/dataset_modelado_diario.xlsx")
SHEET_NAME = "modelo"

BASE_OUTPUT_DIR = Path(r"C:/Python/tesis/output/analisis_dimensional")

DATE_COLUMN = "fecha"
TARGET_COLUMNS = [
    "target_ventas_importe_real_2026_05",
    "target_compras_total_real_2026_05",
    "target_ventas_registros",
    "target_compras_registros",
]

# Ultimos dias reservados para prueba final. Ajustable segun la tesis.
TEST_DAYS = 90

# Reglas base para reduccion. Son umbrales iniciales, no verdades absolutas.
LOW_VARIANCE_THRESHOLD = 1e-8
HIGH_CORRELATION_THRESHOLD = 0.92
MIN_ABS_TARGET_CORRELATION = 0.03
TOP_FEATURES_PER_TARGET = 40


def ensure_output_dir() -> Path:
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return BASE_OUTPUT_DIR


def load_model_dataset(path: Path = DATASET_PATH, sheet_name: str = SHEET_NAME) -> pd.DataFrame:
    """Carga el dataset diario de modelado y ordena cronologicamente."""
    df = pd.read_excel(path, sheet_name=sheet_name)
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    return df.sort_values(DATE_COLUMN).reset_index(drop=True)


def get_predictor_columns(df: pd.DataFrame) -> list[str]:
    """Devuelve variables explicativas, excluyendo fecha y objetivos."""
    excluded = set(TARGET_COLUMNS + [DATE_COLUMN])
    return [column for column in df.columns if column not in excluded]


def temporal_split(df: pd.DataFrame, test_days: int = TEST_DAYS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Divide en entrenamiento y prueba respetando el orden temporal."""
    if len(df) <= test_days:
        raise ValueError("El dataset tiene menos filas que el horizonte de prueba definido.")
    train = df.iloc[:-test_days].copy()
    test = df.iloc[-test_days:].copy()
    return train, test


def classify_feature(column: str) -> str:
    """Clasifica cada variable en una dimension interpretable para la tesis."""
    if column == DATE_COLUMN:
        return "identificador temporal"
    if column in TARGET_COLUMNS:
        return "objetivo"
    if column.startswith("target_"):
        return "objetivo no configurado"
    if column.startswith("clima_"):
        return "clima"
    if column in {
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
        "mes_sin",
        "mes_cos",
        "dia_semana_sin",
        "dia_semana_cos",
        "dia_anio_sin",
        "dia_anio_cos",
    }:
        return "calendario y estacionalidad"
    if column in {
        "es_festivo_mexicano",
        "es_fecha_pago",
        "dias_desde_festivo",
        "dias_hasta_festivo",
        "dias_desde_pago",
        "dias_hasta_pago",
        "festivos_7d",
        "festivos_30d",
        "pagos_7d",
        "pagos_30d",
    }:
        return "eventos comerciales"
    if column in {
        "nacimientos_indice",
        "temperatura_promedio_mensual_hidalgo",
        "inpc_valor_mensual",
    }:
        return "variables exogenas"
    if re.search(r"_lag\d+$", column):
        return "rezagos historicos"
    if re.search(r"_roll\d+_(mean|std|sum)$", column):
        return "ventanas moviles"
    if column.startswith("ventas_"):
        return "composicion de ventas"
    if column.startswith("compras_"):
        return "composicion de compras"
    if column in {
        "ventas_vs_compras_ratio_7d",
        "ventas_minus_compras_7d",
        "dias_desde_ultima_venta",
        "dias_desde_ultima_compra",
    }:
        return "estabilidad y tendencia"
    return "otras variables derivadas"


def numeric_predictors(df: pd.DataFrame) -> list[str]:
    """Devuelve predictores numericos utiles para correlacion, PCA y modelos."""
    predictors = get_predictor_columns(df)
    return [column for column in predictors if pd.api.types.is_numeric_dtype(df[column])]
