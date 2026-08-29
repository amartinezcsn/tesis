"""Configuración única del pipeline semanal de presupuesto de abastecimiento.

Propósito
---------
Centralizar los parámetros metodológicos para que todos los módulos usen la
misma definición de semana, horizonte y disponibilidad de información.

Regla temporal
-------------
Una predicción emitida al inicio de una semana sólo puede usar el historial
cerrado y variables externas que ya sean conocidas o publicadas en ese momento.
"""

from pathlib import Path


# Se calcula desde este archivo para que el proyecto se pueda mover, clonar o
# ejecutar en otro equipo sin editar rutas absolutas.
PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_DIR / "input"
OUTPUT_DIR = PROJECT_DIR / "output" / "semanal"
DAILY_MASTER_PATH = INPUT_DIR / "dataset_maestro_diario.xlsx"
WEEKLY_MASTER_PATH = INPUT_DIR / "dataset_maestro_semanal.xlsx"
WEEKLY_MODEL_PATH = INPUT_DIR / "dataset_modelado_semanal.xlsx"

DATE_COLUMN = "semana_inicio"
TARGET_COLUMN = "target_compras_importe_semanal"

# La semana inicia en lunes y termina en domingo. Esta regla se usa en todos los
# agregados, pronósticos y reportes.
WEEK_FREQUENCY = "W-SUN"

WINDOW_WEEKS = 52
# El horizonte inmediato es el contraste principal de las hipótesis. El
# horizonte de cuatro semanas se estima de forma directa y se emplea también
# para consolidar el presupuesto mensual a partir de h=1, h=2, h=3 y h=4.
HORIZON_WEEKS = 1
SECONDARY_HORIZON_WEEKS = 4
MONTHLY_CONSOLIDATION_HORIZONS = (1, 2, 3, 4)
STEP_WEEKS = 1
FINAL_EVALUATION_WEEKS = 16
TUNING_WINDOWS = 8
SIGNIFICANCE_LEVEL = 0.05

LAG_WEEKS = (1, 2, 4, 8, 52)
ROLLING_WINDOWS = (4, 8, 12)
MAX_FEATURES = 15
RANDOM_STATE = 42
EXPERIMENT_SEED = RANDOM_STATE

# Referencia primaria de H1: persistencia del último importe semanal observado.
# Conserva los ceros observados; las ausencias de cobertura y filas sintéticas
# se excluyen antes de la evaluación por las salvaguardas del pipeline.
PRIMARY_BASELINE = "empirico_ultimo_valor"
BASELINE_NAMES = (
    "empirico_ultimo_valor",
    "empirico_promedio_4s",
    "empirico_estacional_52s",
)

# Variables que se agregan y se consideran disponibles antes de pronosticar.
# El INPC se desplaza una semana para representar el último valor publicado.
KNOWN_EXOGENOUS = (
    "es_festivo_mexicano",
    "es_fecha_pago",
    "nacimientos_indice",
    "inpc_valor_mensual",
)
TEMPERATURE_COLUMN = "temperatura_promedio_mensual_hidalgo"

# Registro auditable de procedencia y disponibilidad. Un valor con ``rezago=1``
# se desplaza una semana antes de convertirse en predictor; así se representa
# el último dato publicado y no una medición conocida al cierre de la semana.
EXOGENOUS_REGISTRY = {
    "eventos_festivos_semana": {
        "fuente": "calendario de festividades", "disponibilidad": "conocida antes del inicio de la semana", "rezago_semanas": 0,
    },
    "eventos_pago_semana": {
        "fuente": "calendario de pagos", "disponibilidad": "conocida antes del inicio de la semana", "rezago_semanas": 0,
    },
    "es_san_valentin": {
        "fuente": "calendario comercial", "disponibilidad": "conocida antes del inicio de la semana", "rezago_semanas": 0,
    },
    "es_dia_nino": {
        "fuente": "calendario comercial", "disponibilidad": "conocida antes del inicio de la semana", "rezago_semanas": 0,
    },
    "es_dia_madre": {
        "fuente": "calendario comercial", "disponibilidad": "conocida antes del inicio de la semana", "rezago_semanas": 0,
    },
    "nacimientos_indice_semanal": {
        "fuente": "índice demográfico histórico", "disponibilidad": "último valor publicado", "rezago_semanas": 1,
    },
    "inpc_observado_semana": {
        "fuente": "INPC publicado", "disponibilidad": "último valor publicado", "rezago_semanas": 1,
    },
    "temperatura_observada_semana": {
        "fuente": "temperatura histórica regional", "disponibilidad": "último valor observado", "rezago_semanas": 1,
    },
}

DERIVED_EXOGENOUS_FEATURES = (
    "exog_semana_anio_sin",
    "exog_semana_anio_cos",
    "exog_mes_sin",
    "exog_mes_cos",
)


def exogenous_feature_name(source: str) -> str:
    """Devuelve el nombre permitido del predictor derivado de una fuente."""
    metadata = EXOGENOUS_REGISTRY[source]
    lag = metadata["rezago_semanas"]
    if lag == 0:
        return f"exog_{source}"
    base = (
        source.replace("_observado_semana", "")
        .replace("_observada_semana", "")
        .replace("_semanal", "")
    )
    return f"exog_{base}_publicado_lag_{lag}s"


ALLOWED_EXOGENOUS_FEATURES = frozenset(
    [exogenous_feature_name(source) for source in EXOGENOUS_REGISTRY] + list(DERIVED_EXOGENOUS_FEATURES)
)

# Se conservan las ventas como predictores históricos. Las compras no se usan
# por categoría para evitar una matriz demasiado ancha frente a pocas semanas.
SALES_COLUMNS = (
    "ventas_importe_real_2026_05",
    "ventas_registros",
    "ventas_cantidad_total",
)
PURCHASE_COLUMN = "compras_total_real_2026_05"


def ensure_output_dir() -> Path:
    """Crea y devuelve la carpeta exclusiva de resultados semanales."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR
