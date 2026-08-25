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


PROJECT_DIR = Path(r"C:/Python/tesis")
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
HORIZON_WEEKS = 1
STEP_WEEKS = 1
FINAL_EVALUATION_WEEKS = 16
TUNING_WINDOWS = 8

LAG_WEEKS = (1, 2, 4, 8, 52)
ROLLING_WINDOWS = (4, 8, 12)
MAX_FEATURES = 15
RANDOM_STATE = 42

PRIMARY_BASELINE = "empirico_promedio_4s"
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
