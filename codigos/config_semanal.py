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


# Resolver el proyecto desde el propio archivo evita que la metodología
# dependa de una ruta absoluta específica del equipo del investigador.
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
# La tesis define un horizonte principal de una semana y un análisis
# complementario de cuatro semanas para consolidar el presupuesto mensual.
PRIMARY_HORIZON_WEEKS = 1
COMPLEMENTARY_HORIZON_WEEKS = 4
FORECAST_HORIZONS = (PRIMARY_HORIZON_WEEKS, COMPLEMENTARY_HORIZON_WEEKS)
STEP_WEEKS = 1
# Se reservan 16 orígenes finales para la evaluación fuera de muestra. Para
# H=1 equivalen a 16 semanas; para H=4 se reportan 16 orígenes consecutivos.
FINAL_EVALUATION_ORIGINS = 16
TUNING_WINDOWS = 8
SIGNIFICANCE_ALPHA = 0.05
H1_MIN_RMSE_REDUCTION = 0.20
SARIMA_SEASONAL_PERIOD_WEEKS = 4

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

# Fuentes exógenas que deben estar disponibles antes de emitir un pronóstico.
# Las dos últimas se incorporan con rezago porque el archivo semanal contiene
# valores observados, no pronósticos futuros.
KNOWN_EXOGENOUS = (
    "es_festivo_mexicano",
    "es_fecha_pago",
    "nacimientos_indice",
    "inpc_valor_mensual",
)
TEMPERATURE_COLUMN = "temperatura_promedio_mensual_hidalgo"

WEEKLY_CALENDAR_EXOGENOUS = (
    "eventos_festivos_semana",
    "eventos_pago_semana",
    "es_san_valentin",
    "es_dia_nino",
    "es_dia_madre",
    "nacimientos_indice_semanal",
)
WEEKLY_DELAYED_EXOGENOUS = (
    "exog_inpc_publicado",
    "exog_temperatura_lag_1s",
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
