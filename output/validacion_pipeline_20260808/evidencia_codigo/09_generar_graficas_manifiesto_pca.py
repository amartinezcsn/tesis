from __future__ import annotations

"""
CÓDIGO 09 — GRÁFICAS ACADÉMICAS DE LIMPIEZA, EDA E INTEGRACIÓN
================================================================

Genera evidencia visual y un manifiesto explicativo a partir de los archivos
producidos por ``01_clean_eda.py``:

- inpc_limpio.xlsx
- temperatura_hidalgo_limpia.xlsx
- dataset_tizayuca_limpio.xlsx
- compras_limpias.xlsx
- ventas_limpias.xlsx
- dataset_maestro_diario.xlsx

Salidas:
- Figuras PNG numeradas y listas para incorporarse a la tesis.
- MANIFIESTO_METODOLOGIA_PCA.md con interpretación académica.
- MANIFIESTO_METODOLOGIA_PCA.json para trazabilidad.
- INDICE_GRAFICAS_METODOLOGIA_PCA.csv.
- RESUMEN_ESTADISTICO_CLEAN_EDA.xlsx.

Ejemplo:
    python 09_generar_graficas_manifiesto_clean_eda.py \
        --input-dir "C:/Python/tesis/input"

Dependencias:
    pip install pandas numpy matplotlib openpyxl
"""

import argparse
import json
import logging
import math
import textwrap
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class GraphicRecord:
    orden: int
    etapa: str
    titulo: str
    archivo: str
    fuente: str
    hoja: str
    variables_utilizadas: str
    objetivo: str
    interpretacion: str
    criterio_lectura: str
    ecuacion_o_fundamento: str
    uso_tesis: str
    limitaciones: str
    estado: str = "generada"


@dataclass
class Context:
    input_dir: Path
    graphics_dir: Path
    dpi: int
    top_n: int
    analysis_dir: Path | None = None


FILES = {
    "inpc": ("inpc_limpio.xlsx", "limpio"),
    "inpc_meta": ("inpc_limpio.xlsx", "meta"),
    "temperatura": ("temperatura_hidalgo_limpia.xlsx", "limpio"),
    "tizayuca": ("dataset_tizayuca_limpio.xlsx", "limpio"),
    "compras_detalle": ("compras_limpias.xlsx", "detalle"),
    "compras_diario": ("compras_limpias.xlsx", "pivot_diario"),
    "ventas_detalle": ("ventas_limpias.xlsx", "detalle"),
    "ventas_diario": ("ventas_limpias.xlsx", "diario_completo"),
    "maestro": ("dataset_maestro_diario.xlsx", "maestro"),
}


LABELS = {
    "ventas_importe_real_2026_05": "Ventas reales",
    "ventas_importe_nominal": "Ventas nominales",
    "ventas_ganancia_real_2026_05": "Ganancia real",
    "compras_total_real_2026_05": "Compras reales",
    "ventas_registros": "Registros de venta",
    "compras_registros": "Registros de compra",
    "es_festivo_mexicano": "Días festivos",
    "es_fecha_pago": "Fechas de pago",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera gráficas académicas de limpieza, ingeniería de características, perfil dimensional, multicolinealidad, selección de características y PCA.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-dir", type=Path, default=Path(r"C:/Python/tesis/input"))
    parser.add_argument("--graphics-dir", type=Path, default=None)
    parser.add_argument(
        "--analysis-dir", type=Path, default=None,
        help="Carpeta que contiene los Excel de perfil, multicolinealidad, selección y PCA. Si se omite, se busca también en input-dir."
    )
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--continuar-con-faltantes", action="store_true")
    return parser.parse_args()


def configure_logging(graphics_dir: Path) -> None:
    graphics_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(graphics_dir / "generacion_metodologia_pca.log", mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def load(ctx: Context, key: str) -> pd.DataFrame:
    filename, sheet = FILES[key]
    path = ctx.input_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    with pd.ExcelFile(path) as xls:
        if sheet not in xls.sheet_names:
            raise ValueError(f"{filename} no contiene la hoja '{sheet}'. Hojas: {xls.sheet_names}")
    return pd.read_excel(path, sheet_name=sheet)


def to_date(df: pd.DataFrame, column: str = "fecha") -> pd.DataFrame:
    result = df.copy()
    result[column] = pd.to_datetime(result[column], errors="coerce")
    return result.dropna(subset=[column]).sort_values(column)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def wrap(values, width: int = 34) -> list[str]:
    return ["\n".join(textwrap.wrap(str(v), width=width)) for v in values]


def human(column: str) -> str:
    return LABELS.get(column, column.replace("_real_2026_05", "").replace("_", " ").title())


def save(fig: plt.Figure, ctx: Context, filename: str) -> None:
    fig.savefig(ctx.graphics_dir / filename, dpi=ctx.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def style_time_axis(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.grid(alpha=0.22)


def monthly_sum(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    work = to_date(df)
    valid = [c for c in columns if c in work.columns]
    for c in valid:
        work[c] = numeric(work[c]).fillna(0)
    return work.set_index("fecha")[valid].resample("MS").sum().reset_index()


def monthly_mean(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    work = to_date(df)
    valid = [c for c in columns if c in work.columns]
    for c in valid:
        work[c] = numeric(work[c])
    return work.set_index("fecha")[valid].resample("MS").mean().reset_index()


def rec(order: int, title: str, file: str, source: str, sheet: str, variables: str,
        objective: str, interpretation: str, reading: str, equation: str,
        use: str, limitations: str, stage: str = "Limpieza y EDA") -> GraphicRecord:
    return GraphicRecord(order, stage, title, file, source, sheet, variables, objective,
                         interpretation, reading, equation, use, limitations)


# -----------------------------------------------------------------------------
# 1. Cobertura y trazabilidad
# -----------------------------------------------------------------------------
def graph_source_coverage(ctx: Context) -> GraphicRecord:
    sources = []
    for key, label in [
        ("inpc", "INPC"), ("temperatura", "Temperatura"), ("tizayuca", "Variables exógenas"),
        ("compras_detalle", "Compras"), ("ventas_detalle", "Ventas"), ("maestro", "Dataset maestro")
    ]:
        df = to_date(load(ctx, key))
        sources.append({"fuente": label, "inicio": df.fecha.min(), "fin": df.fecha.max(), "registros": len(df)})
    cov = pd.DataFrame(sources).sort_values("inicio")
    fig, ax = plt.subplots(figsize=(12, 6.8))
    y = np.arange(len(cov))
    starts = mdates.date2num(cov["inicio"])
    widths = mdates.date2num(cov["fin"]) - starts
    ax.barh(y, widths, left=starts)
    ax.set_yticks(y, cov["fuente"])
    ax.invert_yaxis()
    ax.xaxis_date()
    style_time_axis(ax)
    ax.set_title("Cobertura temporal y trazabilidad de las fuentes integradas")
    ax.set_xlabel("Periodo disponible")
    for i, row in cov.reset_index(drop=True).iterrows():
        ax.text(mdates.date2num(row.fin), i, f"  n={row.registros:,}", va="center", fontsize=9)
    fig.tight_layout()
    filename = "01_cobertura_temporal_fuentes.png"
    save(fig, ctx, filename)
    return rec(1, "Cobertura temporal de las fuentes", filename,
               "Seis archivos generados por 01_clean_eda.py", "Varias",
               "fecha y número de registros",
               "Demostrar que las fuentes poseen cobertura temporal compatible antes de la integración.",
               "Las barras muestran que las series convergen en el intervalo analítico; el número al final indica registros disponibles.",
               "La intersección temporal define el dominio válido del dataset maestro.",
               r"D = \bigcap_{j=1}^{m}[t_{inicio,j},t_{fin,j}]",
               "Sección 4.2, construcción del dataset maestro y trazabilidad de fuentes.",
               "La cantidad de registros no implica igual granularidad: INPC y temperatura pueden ser mensuales, mientras ventas y compras son transaccionales.")


# -----------------------------------------------------------------------------
# 2-3. INPC y deflactación
# -----------------------------------------------------------------------------
def graph_inpc_series(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "inpc"))
    df["inpc_valor"] = numeric(df["inpc_valor"])
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.plot(df.fecha, df.inpc_valor, marker="o", markersize=3)
    style_time_axis(ax)
    ax.set_title("Evolución mensual del INPC utilizado para homogeneizar valores monetarios")
    ax.set_ylabel("Índice Nacional de Precios al Consumidor")
    ax.set_xlabel("Mes")
    fig.tight_layout()
    filename = "02_evolucion_inpc.png"
    save(fig, ctx, filename)
    return rec(2, "Evolución del INPC", filename, "inpc_limpio.xlsx", "limpio",
               "fecha, inpc_valor", "Documentar la variable macroeconómica empleada para eliminar el efecto de inflación.",
               "Una trayectoria ascendente implica que una unidad monetaria histórica no es directamente comparable con una unidad del periodo base.",
               "El índice se usa como denominador del factor de actualización.",
               r"F_t=\frac{INPC_{base}}{INPC_t}",
               "Sección de depuración monetaria y Tabla de inflación histórica.",
               "El INPC mensual homogeneiza poder adquisitivo, pero no modela cambios específicos de precios de insumos de repostería.")


def graph_inflation_factor(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "inpc"))
    df["factor_ajuste_a_2026_05"] = numeric(df["factor_ajuste_a_2026_05"])
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.plot(df.fecha, df.factor_ajuste_a_2026_05, marker="o", markersize=3)
    ax.axhline(1.0, linestyle="--", linewidth=1.2, label="Mes base: factor = 1")
    style_time_axis(ax)
    ax.set_title("Factor de actualización monetaria a pesos de mayo de 2026")
    ax.set_ylabel("Factor de ajuste")
    ax.set_xlabel("Mes")
    ax.legend()
    fig.tight_layout()
    filename = "03_factor_ajuste_inflacion.png"
    save(fig, ctx, filename)
    oldest = df.iloc[0]
    return rec(3, "Factor de ajuste inflacionario", filename, "inpc_limpio.xlsx", "limpio",
               "fecha, factor_ajuste_a_2026_05", "Mostrar la magnitud de la corrección aplicada a cada importe nominal.",
               f"El primer factor observado es {oldest.factor_ajuste_a_2026_05:.3f}; valores mayores que uno elevan importes históricos para expresarlos en moneda constante.",
               "La línea horizontal representa el periodo base, donde nominal y real coinciden.",
               r"Valor^{real}_t=Valor^{nominal}_t\times F_t",
               "Justificación de la deflactación de ventas, compras, ganancias, descuentos y envíos.",
               "El factor depende de la fecha y calidad de la serie INPC; los meses faltantes deben revisarse antes de llenar con 1.0.")


# -----------------------------------------------------------------------------
# 4-6. Contexto exógeno
# -----------------------------------------------------------------------------
def graph_temperature(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "temperatura"))
    col = "temperatura_promedio_mensual"
    df[col] = numeric(df[col])
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.plot(df.fecha, df[col], marker="o", markersize=3)
    style_time_axis(ax)
    ax.set_title("Comportamiento temporal de la temperatura promedio en Hidalgo")
    ax.set_ylabel("Temperatura promedio")
    ax.set_xlabel("Mes")
    fig.tight_layout()
    filename = "04_temperatura_promedio_hidalgo.png"
    save(fig, ctx, filename)
    return rec(4, "Temperatura promedio mensual", filename, "temperatura_hidalgo_limpia.xlsx", "limpio",
               "fecha, temperatura_promedio_mensual", "Representar una variable exógena potencialmente asociada con patrones de consumo y conservación de insumos.",
               "Los máximos y mínimos recurrentes permiten identificar estacionalidad climática.",
               "La periodicidad debe interpretarse como contexto, no como causalidad directa sobre ventas.",
               r"\bar{T}_m=\frac{1}{n_m}\sum_{i=1}^{n_m}T_{i,m}",
               "Sección 4.1.2, conjuntos de datos de variables exógenas.",
               "La temperatura agregada estatal puede no representar las condiciones exactas del establecimiento.")


def graph_climate_distribution(ctx: Context) -> GraphicRecord:
    df = load(ctx, "tizayuca")
    counts = df["clima"].fillna("SIN_DATO").astype(str).value_counts().head(ctx.top_n).sort_values()
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(wrap(counts.index, 28), counts.values)
    ax.set_title("Distribución de categorías climáticas registradas")
    ax.set_xlabel("Número de días")
    ax.set_ylabel("Categoría de clima")
    ax.grid(axis="x", alpha=0.22)
    for i, v in enumerate(counts.values):
        ax.text(v, i, f" {v:,}", va="center")
    fig.tight_layout()
    filename = "05_distribucion_categorias_clima.png"
    save(fig, ctx, filename)
    dominant = counts.idxmax()
    return rec(5, "Distribución del clima", filename, "dataset_tizayuca_limpio.xlsx", "limpio",
               "clima", "Verificar la frecuencia y el balance de las categorías climáticas antes de codificarlas.",
               f"La categoría más frecuente es '{dominant}'. Categorías muy escasas pueden generar variables dummy con baja variabilidad.",
               "Las barras comparan la frecuencia absoluta de cada estado del clima.",
               r"p(c_k)=\frac{n(c_k)}{N}",
               "EDA de variables categóricas y justificación de la codificación one-hot.",
               "La categoría describe condiciones registradas y puede contener simplificaciones o datos imputados.")


def graph_events_month(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "tizayuca"))
    cols = [c for c in ["es_festivo_mexicano", "es_fecha_pago"] if c in df.columns]
    for c in cols:
        df[c] = numeric(df[c]).fillna(0)
    monthly = df.set_index("fecha")[cols].resample("MS").sum().reset_index()
    fig, ax = plt.subplots(figsize=(12, 6.5))
    for c in cols:
        ax.plot(monthly.fecha, monthly[c], marker="o", markersize=2.5, label=human(c))
    style_time_axis(ax)
    ax.set_title("Frecuencia mensual de eventos comerciales y calendáricos")
    ax.set_ylabel("Número de días marcados")
    ax.set_xlabel("Mes")
    ax.legend()
    fig.tight_layout()
    filename = "06_eventos_festivos_fechas_pago.png"
    save(fig, ctx, filename)
    return rec(6, "Eventos comerciales y calendáricos", filename, "dataset_tizayuca_limpio.xlsx", "limpio",
               ", ".join(cols), "Mostrar la distribución temporal de festivos y fechas de pago que podrían modificar la demanda.",
               "Los picos indican meses con mayor concentración de eventos; sirven para justificar variables de proximidad y ventanas de eventos.",
               "La coincidencia temporal con ventas debe analizarse después, sin asumir causalidad.",
               r"E_{m,k}=\sum_{t\in m}I(evento_{t,k}=1)",
               "Ingeniería de características: festivos, quincenas y proximidad a eventos.",
               "El indicador binario mide presencia, no intensidad económica del evento.")


# -----------------------------------------------------------------------------
# 7-13. Ventas
# -----------------------------------------------------------------------------
def graph_daily_sales(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "ventas_diario"))
    col = "ventas_importe_real_2026_05"
    df[col] = numeric(df[col]).fillna(0)
    df["media_30d"] = df[col].rolling(30, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(df.fecha, df[col], linewidth=0.65, alpha=0.45, label="Venta diaria")
    ax.plot(df.fecha, df.media_30d, linewidth=1.8, label="Media móvil de 30 días")
    style_time_axis(ax)
    ax.set_title("Serie diaria de ventas reales y tendencia suavizada")
    ax.set_ylabel("Pesos constantes de mayo de 2026")
    ax.set_xlabel("Fecha")
    ax.legend()
    fig.tight_layout()
    filename = "07_serie_diaria_ventas_reales.png"
    save(fig, ctx, filename)
    return rec(7, "Serie diaria de ventas", filename, "ventas_limpias.xlsx", "diario_completo",
               "fecha, ventas_importe_real_2026_05", "Visualizar nivel, variabilidad, picos, ceros y tendencia de la variable financiera principal.",
               "La línea fina conserva la volatilidad diaria; la media móvil revela cambios persistentes del nivel de ventas.",
               "Los picos no deben eliminarse automáticamente: pueden corresponder a eventos reales o pedidos extraordinarios.",
               r"MA_{30,t}=\frac{1}{30}\sum_{i=0}^{29}y_{t-i}",
               "Sección 4.2.1, EDA de ventas; base para discutir no estacionariedad y volatilidad.",
               "La media móvil es descriptiva y utiliza información contemporánea; no debe confundirse con una característica predictiva sin desplazamiento.")


def graph_monthly_nominal_real_sales(ctx: Context) -> GraphicRecord:
    detail = to_date(load(ctx, "ventas_detalle"))
    cols = ["importe_nominal", "importe_real_2026_05"]
    monthly = monthly_sum(detail, cols)
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(monthly.fecha, monthly[cols[0]], marker="o", markersize=2.5, label="Importe nominal")
    ax.plot(monthly.fecha, monthly[cols[1]], marker="o", markersize=2.5, label="Importe real")
    style_time_axis(ax)
    ax.set_title("Comparación mensual de ventas nominales y ventas a precios constantes")
    ax.set_ylabel("Pesos")
    ax.set_xlabel("Mes")
    ax.legend()
    fig.tight_layout()
    filename = "08_ventas_nominales_vs_reales.png"
    save(fig, ctx, filename)
    diff = float((monthly[cols[1]] - monthly[cols[0]]).abs().mean())
    return rec(8, "Ventas nominales frente a reales", filename, "ventas_limpias.xlsx", "detalle",
               "fecha, importe_nominal, importe_real_2026_05", "Evidenciar el efecto práctico de la corrección inflacionaria sobre la serie de ingresos.",
               f"La separación promedio absoluta entre ambas series mensuales es de {diff:,.2f} pesos; las diferencias son mayores en periodos alejados del mes base.",
               "La serie real es la adecuada para comparar desempeño financiero a través del tiempo.",
               r"Ingreso^{real}_{t}=Ingreso^{nominal}_{t}\frac{INPC_{base}}{INPC_t}",
               "Justificación de la variable objetivo monetaria a precios constantes.",
               "Los importes reales dependen del índice general de precios y no de un deflactor específico del giro comercial.")


def graph_sales_distribution(ctx: Context) -> GraphicRecord:
    df = load(ctx, "ventas_diario")
    values = numeric(df["ventas_importe_real_2026_05"]).dropna()
    positive = values[values > 0]
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    ax.hist(positive, bins=min(40, max(10, int(math.sqrt(len(positive))))))
    ax.axvline(positive.median(), linestyle="--", linewidth=1.4, label=f"Mediana = {positive.median():,.0f}")
    ax.axvline(positive.mean(), linestyle=":", linewidth=1.4, label=f"Media = {positive.mean():,.0f}")
    ax.set_title("Distribución de ventas diarias positivas")
    ax.set_xlabel("Ventas reales diarias")
    ax.set_ylabel("Frecuencia")
    ax.legend()
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    filename = "09_distribucion_ventas_diarias.png"
    save(fig, ctx, filename)
    skew = float(positive.skew()) if len(positive) else float("nan")
    return rec(9, "Distribución de ventas diarias", filename, "ventas_limpias.xlsx", "diario_completo",
               "ventas_importe_real_2026_05", "Evaluar asimetría, dispersión y presencia de días de venta extraordinaria.",
               f"La asimetría muestral es {skew:.2f}. Una cola derecha prolongada evidencia pocos días con importes mucho mayores que el nivel habitual.",
               "La diferencia entre media y mediana permite identificar falta de simetría.",
               r"g_1=\frac{\frac{1}{N}\sum(y_i-\bar y)^3}{s^3}",
               "Caracterización estadística de la variable objetivo de ventas.",
               "Se excluyen ceros para describir la magnitud condicional de días con venta; la tasa de días sin venta se documenta por separado.")


def graph_sales_weekday_boxplot(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "ventas_diario"))
    col = "ventas_importe_real_2026_05"
    df[col] = numeric(df[col]).fillna(0)
    df["dia_semana"] = df.fecha.dt.dayofweek
    names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    data = [df.loc[df.dia_semana == i, col].values for i in range(7)]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.boxplot(data, labels=names, showfliers=False)
    ax.set_title("Distribución de ventas reales por día de la semana")
    ax.set_xlabel("Día de la semana")
    ax.set_ylabel("Ventas reales diarias")
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    filename = "10_ventas_por_dia_semana.png"
    save(fig, ctx, filename)
    medians = {names[i]: float(np.median(data[i])) for i in range(7)}
    best = max(medians, key=medians.get)
    return rec(10, "Ventas por día de la semana", filename, "ventas_limpias.xlsx", "diario_completo",
               "fecha, ventas_importe_real_2026_05", "Identificar microestacionalidad semanal y diferencias en dispersión entre días.",
               f"El día con mayor mediana es {best}. La caja representa el 50 % central y los bigotes la dispersión sin valores extremos.",
               "Las medianas distintas respaldan la incorporación del día de la semana y su codificación cíclica.",
               r"IQR=Q_{0.75}-Q_{0.25}",
               "EDA de estacionalidad semanal e ingeniería de características de calendario.",
               "La gráfica es descriptiva; las diferencias pueden estar condicionadas por festivos, promociones o crecimiento del negocio.")


def graph_sales_month_heatmap(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "ventas_diario"))
    col = "ventas_importe_real_2026_05"
    df[col] = numeric(df[col]).fillna(0)
    monthly = df.set_index("fecha")[col].resample("MS").sum().reset_index()
    monthly["anio"] = monthly.fecha.dt.year
    monthly["mes"] = monthly.fecha.dt.month
    pivot = monthly.pivot(index="anio", columns="mes", values=col)
    fig, ax = plt.subplots(figsize=(12, 5.8))
    image = ax.imshow(pivot.values, aspect="auto")
    ax.set_xticks(np.arange(12), ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index.astype(str))
    ax.set_title("Mapa de calor de ventas mensuales por año")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Año")
    fig.colorbar(image, ax=ax, label="Ventas reales mensuales")
    fig.tight_layout()
    filename = "11_mapa_calor_ventas_mes_anio.png"
    save(fig, ctx, filename)
    return rec(11, "Mapa de calor de ventas mensuales", filename, "ventas_limpias.xlsx", "diario_completo",
               "fecha, ventas_importe_real_2026_05", "Comparar simultáneamente estacionalidad mensual y evolución interanual.",
               "Las celdas de mayor intensidad representan meses con mayor facturación real; patrones verticales repetidos sugieren estacionalidad.",
               "Debe distinguirse entre estacionalidad y crecimiento estructural del negocio.",
               r"Y_{a,m}=\sum_{t\in(a,m)}y_t",
               "EDA temporal; figura central para discutir estacionalidad y tendencia.",
               "Los años incompletos contienen menos meses y no deben compararse mediante totales anuales sin normalización.")


def graph_product_mix(ctx: Context) -> GraphicRecord:
    df = load(ctx, "ventas_detalle")
    cols = [c for c in ["pastel", "galletas", "otros", "cupcakes"] if c in df.columns]
    totals = pd.Series({human(c): numeric(df[c]).fillna(0).sum() for c in cols}).sort_values()
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ax.barh(totals.index, totals.values)
    ax.set_title("Composición acumulada de productos vendidos")
    ax.set_xlabel("Cantidad registrada")
    ax.set_ylabel("Familia de producto")
    ax.grid(axis="x", alpha=0.22)
    for i, v in enumerate(totals.values):
        ax.text(v, i, f" {v:,.0f}", va="center")
    fig.tight_layout()
    filename = "12_composicion_productos_vendidos.png"
    save(fig, ctx, filename)
    share = totals.max() / totals.sum() * 100 if totals.sum() else 0
    return rec(12, "Composición de productos vendidos", filename, "ventas_limpias.xlsx", "detalle",
               ", ".join(cols), "Describir la estructura de la demanda por familia de producto.",
               f"La categoría dominante representa aproximadamente {share:.1f}% de las unidades clasificadas.",
               "Una mezcla concentrada implica que la demanda total puede estar impulsada por una familia específica.",
               r"Participación_k=\frac{\sum_t q_{k,t}}{\sum_j\sum_t q_{j,t}}\times100",
               "Contexto del negocio y caracterización de ventas por tipo de producto.",
               "Las categorías dependen de la calidad y exhaustividad del registro comercial.")


def graph_sales_profit(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "ventas_detalle"))
    cols = ["importe_real_2026_05", "ganancia_real_2026_05"]
    monthly = monthly_sum(df, cols)
    monthly["margen"] = np.where(monthly[cols[0]].abs() > 1e-9, monthly[cols[1]] / monthly[cols[0]] * 100, np.nan)
    fig, ax = plt.subplots(figsize=(12.5, 6.5))
    ax.plot(monthly.fecha, monthly.margen, marker="o", markersize=3)
    ax.axhline(monthly.margen.median(), linestyle="--", linewidth=1.1, label=f"Mediana = {monthly.margen.median():.1f}%")
    style_time_axis(ax)
    ax.set_title("Evolución mensual del margen de ganancia registrado")
    ax.set_ylabel("Margen sobre ventas (%)")
    ax.set_xlabel("Mes")
    ax.legend()
    fig.tight_layout()
    filename = "13_margen_ganancia_mensual.png"
    save(fig, ctx, filename)
    return rec(13, "Margen de ganancia mensual", filename, "ventas_limpias.xlsx", "detalle",
               "importe_real_2026_05, ganancia_real_2026_05", "Relacionar ingresos con rentabilidad y evidenciar variaciones financieras no visibles en las ventas brutas.",
               "Un mes puede mostrar ventas elevadas y margen reducido; por ello ingreso y ganancia no deben tratarse como equivalentes.",
               "La línea representa la proporción de ganancia registrada respecto al importe real mensual.",
               r"Margen_m=\frac{Ganancia^{real}_m}{Ventas^{real}_m}\times100",
               "Planeación financiera y análisis de rentabilidad histórica.",
               "La interpretación depende de cómo el sistema fuente define y calcula la columna Ganancia.")


# -----------------------------------------------------------------------------
# 14-17. Compras
# -----------------------------------------------------------------------------
def graph_daily_purchases(ctx: Context) -> GraphicRecord:
    df = to_date(load(ctx, "compras_diario"))
    col = "compras_total_real_2026_05"
    df[col] = numeric(df[col]).fillna(0)
    df["media_30d"] = df[col].rolling(30, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(df.fecha, df[col], linewidth=0.65, alpha=0.45, label="Compra diaria")
    ax.plot(df.fecha, df.media_30d, linewidth=1.8, label="Media móvil de 30 días")
    style_time_axis(ax)
    ax.set_title("Serie diaria de compras reales y tendencia suavizada")
    ax.set_ylabel("Pesos constantes de mayo de 2026")
    ax.set_xlabel("Fecha")
    ax.legend()
    fig.tight_layout()
    filename = "14_serie_diaria_compras_reales.png"
    save(fig, ctx, filename)
    return rec(14, "Serie diaria de compras", filename, "compras_limpias.xlsx", "pivot_diario",
               "fecha, compras_total_real_2026_05", "Visualizar periodicidad, intermitencia y magnitud de los egresos por abastecimiento.",
               "Los periodos prolongados en cero y los picos aislados son característicos de compras intermitentes.",
               "La intermitencia explica por qué métricas porcentuales como MAPE pueden ser inestables.",
               r"MA_{30,t}=\frac{1}{30}\sum_{i=0}^{29}c_{t-i}",
               "EDA de compras y justificación de modelos para demanda intermitente.",
               "Los ceros pueden representar ausencia real de compra, no datos faltantes.")


def graph_purchase_classification(ctx: Context) -> GraphicRecord:
    df = load(ctx, "compras_detalle")
    df["monto_real_2026_05"] = numeric(df["monto_real_2026_05"]).fillna(0)
    totals = df.groupby("clasificacion", dropna=False)["monto_real_2026_05"].sum().sort_values(ascending=False).head(ctx.top_n).sort_values()
    fig, ax = plt.subplots(figsize=(12, 7.2))
    ax.barh(wrap(totals.index, 36), totals.values)
    ax.set_title(f"Principales clasificaciones de compra por importe real (Top {len(totals)})")
    ax.set_xlabel("Importe acumulado real")
    ax.set_ylabel("Clasificación")
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "15_compras_por_clasificacion.png"
    save(fig, ctx, filename)
    return rec(15, "Compras por clasificación", filename, "compras_limpias.xlsx", "detalle",
               "clasificacion, monto_real_2026_05", "Identificar los grupos de insumo que concentran el mayor desembolso.",
               "Las barras superiores representan categorías con mayor impacto financiero acumulado y potencial prioridad de pronóstico.",
               "La clasificación debe revisarse por consistencia semántica antes de interpretar diferencias.",
               r"C_k=\sum_{i:clasificacion_i=k}Monto^{real}_i",
               "Caracterización del abastecimiento y selección de categorías operativamente relevantes.",
               "Los importes no consideran necesariamente frecuencia, perecibilidad ni criticidad del insumo.")


def graph_supplier_pareto(ctx: Context) -> GraphicRecord:
    df = load(ctx, "compras_detalle")
    df["monto_real_2026_05"] = numeric(df["monto_real_2026_05"]).fillna(0)
    totals = df.groupby("proveedor", dropna=False)["monto_real_2026_05"].sum().sort_values(ascending=False)
    top = totals.head(ctx.top_n)
    cumulative = top.cumsum() / totals.sum() * 100 if totals.sum() else top * 0
    fig, ax = plt.subplots(figsize=(12.5, 7))
    x = np.arange(len(top))
    ax.bar(x, top.values)
    ax.set_xticks(x, wrap(top.index, 18), rotation=45, ha="right")
    ax.set_title(f"Concentración del gasto por proveedor (Top {len(top)})")
    ax.set_ylabel("Importe real acumulado")
    ax.set_xlabel("Proveedor")
    ax.grid(axis="y", alpha=0.22)
    ax2 = ax.twinx()
    ax2.plot(x, cumulative.values, marker="o")
    ax2.axhline(80, linestyle="--", linewidth=1, label="Referencia 80%")
    ax2.set_ylabel("Porcentaje acumulado del gasto")
    ax2.set_ylim(0, 105)
    fig.tight_layout()
    filename = "16_pareto_proveedores.png"
    save(fig, ctx, filename)
    top_share = totals.head(ctx.top_n).sum() / totals.sum() * 100 if totals.sum() else 0
    return rec(16, "Concentración del gasto por proveedor", filename, "compras_limpias.xlsx", "detalle",
               "proveedor, monto_real_2026_05", "Evaluar dependencia de abastecimiento y concentración financiera mediante un diagrama de Pareto.",
               f"Los {len(top)} proveedores mostrados concentran {top_share:.1f}% del gasto total registrado.",
               "Las barras representan gasto individual y la curva el porcentaje acumulado.",
               r"P_k=\frac{\sum_{j=1}^{k}C_{(j)}}{\sum_{j=1}^{J}C_j}\times100",
               "Análisis de proveedores, riesgo de concentración y gestión de abastecimiento.",
               "El gasto histórico no mide desempeño, calidad, plazo de entrega ni posibilidad de sustitución.")


def graph_purchase_units(ctx: Context) -> GraphicRecord:
    df = load(ctx, "compras_detalle")
    counts = df["unidad"].fillna("nd").astype(str).value_counts().head(ctx.top_n).sort_values()
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(counts.index, counts.values)
    ax.set_title("Frecuencia de unidades de medida después de la normalización")
    ax.set_xlabel("Número de registros")
    ax.set_ylabel("Unidad normalizada")
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "17_unidades_medida_normalizadas.png"
    save(fig, ctx, filename)
    return rec(17, "Unidades de medida normalizadas", filename, "compras_limpias.xlsx", "detalle",
               "unidad", "Evidenciar el resultado de la homologación de abreviaturas y unidades de compra.",
               "Una lista reducida de categorías confirma que variantes como pza, pzs y pz fueron consolidadas.",
               "La normalización evita crear categorías artificialmente distintas para la misma unidad.",
               r"u^{*}=f(u),\quad f(\{pza,pzs,pz\})=pz",
               "Auditoría de limpieza semántica de datos de compras.",
               "La homologación textual no convierte magnitudes entre unidades físicamente distintas.")


# -----------------------------------------------------------------------------
# 18-22. Integración y calidad del maestro
# -----------------------------------------------------------------------------
def graph_sales_purchases_monthly(ctx: Context) -> GraphicRecord:
    df = load(ctx, "maestro")
    cols = ["ventas_importe_real_2026_05", "compras_total_real_2026_05"]
    monthly = monthly_sum(df, cols)
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(monthly.fecha, monthly[cols[0]], marker="o", markersize=2.5, label="Ventas")
    ax.plot(monthly.fecha, monthly[cols[1]], marker="o", markersize=2.5, label="Compras")
    style_time_axis(ax)
    ax.set_title("Integración mensual de ventas y compras a precios constantes")
    ax.set_ylabel("Pesos constantes de mayo de 2026")
    ax.set_xlabel("Mes")
    ax.legend()
    fig.tight_layout()
    filename = "18_ventas_compras_mensuales.png"
    save(fig, ctx, filename)
    return rec(18, "Ventas y compras integradas", filename, "dataset_maestro_diario.xlsx", "maestro",
               ", ".join(cols), "Demostrar la integración de ingresos y egresos dentro de una misma escala temporal y monetaria.",
               "La separación entre ambas curvas aproxima la holgura bruta disponible, aunque no constituye flujo de efectivo completo.",
               "Los desfases entre compra y venta pueden revelar anticipación de inventario o rezagos operativos.",
               r"Saldo^{operativo}_m=Ventas^{real}_m-Compras^{real}_m",
               "Construcción del dataset maestro y vínculo con planeación financiera.",
               "No incluye todos los costos, impuestos, cuentas por cobrar ni momento exacto de pago.")


def graph_operating_balance(ctx: Context) -> GraphicRecord:
    df = load(ctx, "maestro")
    cols = ["ventas_importe_real_2026_05", "compras_total_real_2026_05"]
    monthly = monthly_sum(df, cols)
    monthly["saldo"] = monthly[cols[0]] - monthly[cols[1]]
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.bar(monthly.fecha, monthly.saldo, width=20)
    ax.axhline(0, linewidth=1)
    style_time_axis(ax)
    ax.set_title("Saldo operativo mensual aproximado: ventas menos compras")
    ax.set_ylabel("Saldo real mensual")
    ax.set_xlabel("Mes")
    fig.tight_layout()
    filename = "19_saldo_operativo_mensual.png"
    save(fig, ctx, filename)
    negative = int((monthly.saldo < 0).sum())
    return rec(19, "Saldo operativo mensual aproximado", filename, "dataset_maestro_diario.xlsx", "maestro",
               "ventas_importe_real_2026_05, compras_total_real_2026_05", "Ilustrar la relación financiera básica entre entradas por ventas y desembolsos de compra.",
               f"Se observan {negative} meses con saldo negativo bajo esta aproximación; deben investigarse como posibles periodos de acumulación de inventario o baja demanda.",
               "Las barras bajo cero indican que las compras superaron las ventas del mes.",
               r"S_m=\sum_{t\in m}Ventas_t-\sum_{t\in m}Compras_t",
               "Puente entre EDA y simulación financiera.",
               "No es utilidad neta ni flujo de efectivo contable; es un indicador exploratorio limitado a dos componentes.")


def graph_zero_activity(ctx: Context) -> GraphicRecord:
    df = load(ctx, "maestro")
    cols = [c for c in ["ventas_importe_real_2026_05", "compras_total_real_2026_05", "ventas_registros", "compras_registros"] if c in df.columns]
    values = []
    for c in cols:
        s = numeric(df[c]).fillna(0)
        values.append({"variable": human(c), "porcentaje_cero": float((s == 0).mean() * 100)})
    out = pd.DataFrame(values).sort_values("porcentaje_cero")
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.barh(out.variable, out.porcentaje_cero)
    ax.set_title("Proporción de días sin actividad comercial registrada")
    ax.set_xlabel("Días con valor cero (%)")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.22)
    for i, v in enumerate(out.porcentaje_cero):
        ax.text(v, i, f" {v:.1f}%", va="center")
    fig.tight_layout()
    filename = "20_dias_sin_actividad.png"
    save(fig, ctx, filename)
    return rec(20, "Días sin actividad", filename, "dataset_maestro_diario.xlsx", "maestro",
               ", ".join(cols), "Cuantificar la intermitencia de las series operativas después de completar el calendario diario.",
               "Un porcentaje alto de ceros indica una serie intermitente y condiciona la elección de métricas y modelos.",
               "Cero es una observación válida cuando el calendario está completo; no debe confundirse con un dato ausente.",
               r"Z_x=\frac{1}{N}\sum_{t=1}^{N}I(x_t=0)\times100",
               "Calidad del dataset, small data e implicaciones para MAPE y modelado.",
               "La validez del cero depende de que la fuente original haya sido exhaustiva en ese día.")


def graph_missingness(ctx: Context) -> GraphicRecord:
    df = load(ctx, "maestro")
    missing = df.isna().mean().mul(100).sort_values(ascending=False)
    top = missing.head(ctx.top_n).sort_values()
    fig, ax = plt.subplots(figsize=(11.5, 7))
    ax.barh(wrap(top.index, 38), top.values)
    ax.set_title(f"Variables con mayor proporción de valores faltantes en el dataset maestro (Top {len(top)})")
    ax.set_xlabel("Valores faltantes (%)")
    ax.set_xlim(0, max(1, float(top.max()) * 1.15))
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "21_valores_faltantes_dataset_maestro.png"
    save(fig, ctx, filename)
    total_missing = int(df.isna().sum().sum())
    return rec(21, "Completitud del dataset maestro", filename, "dataset_maestro_diario.xlsx", "maestro",
               "todas las columnas", "Auditar la completitud después de uniones, codificación y relleno de fechas.",
               f"El dataset contiene {total_missing:,} celdas nulas. Barras iguales a cero documentan que la integración produjo un panel completo.",
               "Los valores faltantes deben distinguirse de ceros operativos legítimos.",
               r"M_j=\frac{\sum_{t=1}^{N}I(x_{t,j}\;es\;NA)}{N}\times100",
               "Auditoría de calidad antes de la ingeniería de características.",
               "Ausencia de nulos no garantiza corrección semántica ni ausencia de imputaciones discutibles.")


def graph_key_correlation(ctx: Context) -> GraphicRecord:
    df = load(ctx, "maestro")
    candidates = [
        "ventas_importe_real_2026_05", "ventas_ganancia_real_2026_05", "ventas_registros",
        "compras_total_real_2026_05", "compras_registros", "es_festivo_mexicano",
        "es_fecha_pago", "nacimientos_indice", "temperatura_promedio_mensual_hidalgo",
        "inpc_valor_mensual",
    ]
    cols = [c for c in candidates if c in df.columns]
    corr = df[cols].apply(pd.to_numeric, errors="coerce").corr()
    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(corr.values, vmin=-1, vmax=1)
    ax.set_xticks(np.arange(len(cols)), wrap([human(c) for c in cols], 18), rotation=45, ha="right")
    ax.set_yticks(np.arange(len(cols)), wrap([human(c) for c in cols], 18))
    ax.set_title("Matriz de correlación exploratoria de variables clave del dataset maestro")
    fig.colorbar(im, ax=ax, label="Correlación de Pearson")
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.tight_layout()
    filename = "22_correlacion_variables_clave_maestro.png"
    save(fig, ctx, filename)
    return rec(22, "Correlación exploratoria del maestro", filename, "dataset_maestro_diario.xlsx", "maestro",
               ", ".join(cols), "Explorar relaciones lineales iniciales entre variables financieras, operativas y exógenas.",
               "Valores cercanos a 1 o -1 indican asociación lineal fuerte; valores cercanos a cero no descartan relaciones no lineales.",
               "La matriz orienta análisis posteriores, pero no debe utilizarse para establecer causalidad.",
               r"r_{xy}=\frac{\sum_i(x_i-\bar{x})(y_i-\bar{y})}{\sqrt{\sum_i(x_i-\bar{x})^2\sum_i(y_i-\bar{y})^2}}",
               "Cierre del EDA y transición al diagnóstico de multicolinealidad e ingeniería de características.",
               "La correlación puede estar afectada por tendencia, estacionalidad, ceros e inflación.")


# -----------------------------------------------------------------------------
# 23-38. Ingeniería de características: evidencia académica de 02_feature_engineering_profesional.py
# -----------------------------------------------------------------------------
def load_model(ctx: Context, sheet: str = "modelo") -> pd.DataFrame:
    path = ctx.input_dir / "dataset_modelado_diario.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}")
    with pd.ExcelFile(path) as xls:
        if sheet not in xls.sheet_names:
            raise ValueError(f"{path.name} no contiene la hoja '{sheet}'. Hojas: {xls.sheet_names}")
    return pd.read_excel(path, sheet_name=sheet)


def graph_feature_family_counts(ctx: Context) -> GraphicRecord:
    dictionary = load_model(ctx, "diccionario")
    counts = dictionary["grupo"].fillna("Sin clasificación").value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    ax.barh(wrap(counts.index, 34), counts.values)
    ax.set_title("Composición del dataset de modelado por familia de características")
    ax.set_xlabel("Número de variables")
    ax.set_ylabel("Familia metodológica")
    ax.grid(axis="x", alpha=0.22)
    for i, value in enumerate(counts.values):
        ax.text(value, i, f" {int(value)}", va="center")
    fig.tight_layout()
    filename = "23_familias_ingenieria_caracteristicas.png"
    save(fig, ctx, filename)
    dominant = counts.idxmax()
    return rec(23, "Familias de características construidas", filename,
               "dataset_modelado_diario.xlsx", "diccionario", "grupo, variable",
               "Cuantificar la expansión dimensional producida por calendario, rezagos, ventanas móviles, clima y objetivos.",
               f"La familia dominante es '{dominant}' con {int(counts.max())} variables; esto evidencia que la representación histórica concentra gran parte de la dimensionalidad.",
               "Las barras representan conteos de columnas, no importancia predictiva.",
               r"p_g=\frac{n_g}{\sum_{h=1}^{G}n_h}\times100",
               "Sección 4.2.2, descripción del resultado de la ingeniería de características.",
               "Una familia numerosa puede contener redundancia y requiere diagnóstico posterior.",
               stage="Ingeniería de características")


def graph_dataset_expansion(ctx: Context) -> GraphicRecord:
    master = load(ctx, "maestro")
    model = load_model(ctx, "modelo")
    values = pd.Series({"Dataset maestro": len(master.columns), "Dataset modelado": len(model.columns)})
    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    ax.bar(values.index, values.values)
    ax.set_title("Expansión dimensional del dataset después del feature engineering")
    ax.set_ylabel("Número de columnas")
    ax.grid(axis="y", alpha=0.22)
    for i, value in enumerate(values.values):
        ax.text(i, value, f"{int(value)}", ha="center", va="bottom")
    fig.tight_layout()
    filename = "24_expansion_dimensional_feature_engineering.png"
    save(fig, ctx, filename)
    increase = len(model.columns) - len(master.columns)
    return rec(24, "Expansión dimensional del panel", filename,
               "dataset_maestro_diario.xlsx y dataset_modelado_diario.xlsx", "maestro / modelo",
               "número de columnas", "Mostrar cuánto aumenta la representación analítica al transformar datos operativos en predictores.",
               f"El proceso incorporó {increase} columnas netas. El aumento responde a la creación sistemática de información temporal y no a nuevas observaciones.",
               "La comparación debe leerse como enriquecimiento representacional, no como aumento del tamaño muestral.",
               r"p_{final}=p_{base}+p_{cal}+p_{exo}+p_{lags}+p_{roll}+p_{derivadas}",
               "Apertura de la sección de ingeniería de características.",
               "Una relación alta entre columnas y filas incrementa el riesgo de sobreajuste.", stage="Ingeniería de características")


def graph_history_trimming(ctx: Context) -> GraphicRecord:
    master = to_date(load(ctx, "maestro"))
    model = to_date(load_model(ctx, "modelo"))
    values = pd.Series({"Observaciones maestro": len(master), "Observaciones modelado": len(model),
                        "Historial descartado": max(0, len(master) - len(model))})
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ax.bar(values.index, values.values)
    ax.set_title("Efecto del historial mínimo sobre el número de observaciones")
    ax.set_ylabel("Número de días")
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.22)
    for i, value in enumerate(values.values):
        ax.text(i, value, f"{int(value)}", ha="center", va="bottom")
    fig.tight_layout()
    filename = "25_historial_minimo_y_observaciones.png"
    save(fig, ctx, filename)
    removed = len(master) - len(model)
    return rec(25, "Historial mínimo y pérdida controlada de filas", filename,
               "dataset_maestro_diario.xlsx y dataset_modelado_diario.xlsx", "maestro / modelo",
               "fecha y conteo de filas", "Documentar la eliminación de observaciones iniciales sin historial suficiente para rezagos de 28 días.",
               f"Se eliminaron {removed} filas iniciales; esta decisión garantiza que cada observación modelada disponga del mismo historial máximo.",
               "La pérdida ocurre al inicio de la serie y no es una eliminación aleatoria.",
               r"N_{modelo}=N_{maestro}-L_{max},\qquad L_{max}=28",
               "Justificación del periodo efectivo de modelado y del tamaño muestral final.",
               "Reducir filas es metodológicamente necesario, pero disminuye aún más el tamaño de una muestra pequeña.", stage="Ingeniería de características")


def graph_cyclical_month_encoding(ctx: Context) -> GraphicRecord:
    df = load_model(ctx, "modelo")
    required = ["mes", "mes_sin", "mes_cos"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas: {missing}")
    points = df[required].drop_duplicates("mes").sort_values("mes")
    fig, ax = plt.subplots(figsize=(7.5, 7.2))
    ax.scatter(points["mes_cos"], points["mes_sin"], s=70)
    ax.plot(points["mes_cos"].tolist() + [points["mes_cos"].iloc[0]],
            points["mes_sin"].tolist() + [points["mes_sin"].iloc[0]], linewidth=1)
    for _, row in points.iterrows():
        ax.text(row["mes_cos"], row["mes_sin"], f" {int(row['mes'])}")
    ax.axhline(0, linewidth=0.8)
    ax.axvline(0, linewidth=0.8)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Codificación cíclica del mes mediante seno y coseno")
    ax.set_xlabel("mes_cos")
    ax.set_ylabel("mes_sin")
    ax.grid(alpha=0.22)
    fig.tight_layout()
    filename = "26_codificacion_ciclica_mes.png"
    save(fig, ctx, filename)
    return rec(26, "Codificación cíclica del mes", filename, "dataset_modelado_diario.xlsx", "modelo",
               ", ".join(required), "Demostrar que diciembre y enero permanecen próximos en el espacio transformado.",
               "Los doce meses se distribuyen sobre una circunferencia; la distancia geométrica conserva la continuidad del ciclo anual.",
               "Meses consecutivos aparecen cercanos y los opuestos del año se ubican en extremos contrarios.",
               r"mes_{sin}=\sin\left(2\pi\frac{mes}{12}\right),\quad mes_{cos}=\cos\left(2\pi\frac{mes}{12}\right)",
               "Justificación matemática de la codificación de estacionalidad anual.",
               "La transformación representa periodicidad, pero no prueba que exista un efecto mensual sobre la demanda.", stage="Ingeniería de características")


def graph_cyclical_week_encoding(ctx: Context) -> GraphicRecord:
    df = load_model(ctx, "modelo")
    required = ["dia_semana", "dia_semana_sin", "dia_semana_cos"]
    points = df[required].drop_duplicates("dia_semana").sort_values("dia_semana")
    names = {0:"Lun",1:"Mar",2:"Mié",3:"Jue",4:"Vie",5:"Sáb",6:"Dom"}
    fig, ax = plt.subplots(figsize=(7.5, 7.2))
    ax.scatter(points["dia_semana_cos"], points["dia_semana_sin"], s=75)
    ax.plot(points["dia_semana_cos"].tolist() + [points["dia_semana_cos"].iloc[0]],
            points["dia_semana_sin"].tolist() + [points["dia_semana_sin"].iloc[0]], linewidth=1)
    for _, row in points.iterrows():
        ax.text(row["dia_semana_cos"], row["dia_semana_sin"], f" {names[int(row['dia_semana'])]}")
    ax.axhline(0, linewidth=0.8); ax.axvline(0, linewidth=0.8)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Codificación cíclica del día de la semana")
    ax.set_xlabel("dia_semana_cos"); ax.set_ylabel("dia_semana_sin")
    ax.grid(alpha=0.22)
    fig.tight_layout()
    filename = "27_codificacion_ciclica_dia_semana.png"
    save(fig, ctx, filename)
    return rec(27, "Codificación cíclica semanal", filename, "dataset_modelado_diario.xlsx", "modelo",
               ", ".join(required), "Representar la continuidad entre domingo y lunes evitando una discontinuidad numérica artificial.",
               "La estructura circular conserva la vecindad semanal y permite a los modelos aprender patrones periódicos.",
               "La posición angular, no el número entero original, expresa la relación temporal.",
               r"d_{sin}=\sin\left(2\pi\frac{d}{7}\right),\quad d_{cos}=\cos\left(2\pi\frac{d}{7}\right)",
               "Ingeniería de variables calendáricas y microestacionalidad semanal.",
               "No sustituye otros efectos de calendario como festivos, quincenas o fin de mes.", stage="Ingeniería de características")


def graph_lag_alignment(ctx: Context) -> GraphicRecord:
    df = to_date(load_model(ctx, "modelo"))
    base = "target_ventas_importe_real_2026_05"
    lag = "ventas_importe_real_2026_05_lag7"
    if lag not in df.columns:
        raise ValueError(f"No existe {lag}")
    sample = df.tail(min(180, len(df))).copy()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(sample.fecha, numeric(sample[base]), label="Venta observada")
    ax.plot(sample.fecha, numeric(sample[lag]), label="Venta de 7 días antes", alpha=0.8)
    style_time_axis(ax)
    ax.set_title("Alineación temporal entre la venta observada y su rezago semanal")
    ax.set_ylabel("Ventas reales")
    ax.set_xlabel("Fecha")
    ax.legend()
    fig.tight_layout()
    filename = "28_alineacion_rezago_7_dias.png"
    save(fig, ctx, filename)
    return rec(28, "Alineación de un rezago semanal", filename, "dataset_modelado_diario.xlsx", "modelo",
               f"{base}, {lag}", "Ilustrar cómo una observación histórica se desplaza para convertirse en predictor disponible.",
               "La segunda curva reproduce el comportamiento de la serie con siete días de desplazamiento; en la fecha t contiene el valor conocido en t−7.",
               "Una coincidencia visual recurrente sugiere persistencia semanal, pero debe confirmarse fuera de muestra.",
               r"x^{(7)}_t=y_{t-7}",
               "Explicación visual de predictores rezagados y prevención de fuga de información.",
               "La ventana de 180 días es ilustrativa y no resume toda la serie.", stage="Ingeniería de características")


def graph_lag_target_correlations(ctx: Context) -> GraphicRecord:
    df = load_model(ctx, "modelo")
    target = "target_ventas_importe_real_2026_05"
    lags = [1, 2, 3, 7, 14, 28]
    rows = []
    for lag in lags:
        col = f"ventas_importe_real_2026_05_lag{lag}"
        if col in df.columns:
            rows.append({"rezago": lag, "correlacion": numeric(df[col]).corr(numeric(df[target]))})
    out = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ax.bar(out["rezago"].astype(str), out["correlacion"])
    ax.axhline(0, linewidth=0.8)
    ax.set_title("Correlación contemporánea del objetivo con sus rezagos históricos")
    ax.set_xlabel("Rezago en días")
    ax.set_ylabel("Correlación de Pearson")
    ax.set_ylim(-1, 1)
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    filename = "29_correlacion_objetivo_rezagos.png"
    save(fig, ctx, filename)
    best = out.iloc[out.correlacion.abs().argmax()]
    return rec(29, "Relación del objetivo con sus rezagos", filename, "dataset_modelado_diario.xlsx", "modelo",
               "target de ventas y lag1, lag2, lag3, lag7, lag14, lag28",
               "Comparar la memoria lineal de corto, mediano y ciclo semanal/mensual aproximado.",
               f"El rezago con mayor asociación absoluta es {int(best.rezago)} días, con r={best.correlacion:.3f}.",
               "Barras altas sugieren mayor persistencia lineal, no necesariamente mayor importancia multivariada.",
               r"r_k=Corr(y_t,y_{t-k})",
               "Justificación empírica de las longitudes de rezago elegidas.",
               "La correlación puede estar influida por tendencia, estacionalidad y exceso de ceros.", stage="Ingeniería de características")


def graph_rolling_windows(ctx: Context) -> GraphicRecord:
    df = to_date(load_model(ctx, "modelo"))
    target = "target_ventas_importe_real_2026_05"
    cols = ["ventas_importe_real_2026_05_roll7_mean", "ventas_importe_real_2026_05_roll14_mean", "ventas_importe_real_2026_05_roll28_mean"]
    cols = [c for c in cols if c in df.columns]
    sample = df.tail(min(240, len(df)))
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(sample.fecha, numeric(sample[target]), linewidth=0.6, alpha=0.35, label="Objetivo diario")
    for col in cols:
        ax.plot(sample.fecha, numeric(sample[col]), label=col.split("roll")[1].replace("_mean", " días"))
    style_time_axis(ax)
    ax.set_title("Comparación de ventanas móviles históricas de 7, 14 y 28 días")
    ax.set_ylabel("Ventas reales")
    ax.set_xlabel("Fecha")
    ax.legend()
    fig.tight_layout()
    filename = "30_comparacion_ventanas_moviles.png"
    save(fig, ctx, filename)
    return rec(30, "Ventanas móviles multiescala", filename, "dataset_modelado_diario.xlsx", "modelo",
               f"{target}, " + ", ".join(cols), "Mostrar el compromiso entre sensibilidad y suavizado al ampliar la ventana histórica.",
               "La ventana de 7 días responde con rapidez; la de 28 días ofrece una tendencia más estable pero reacciona con mayor retraso.",
               "Las curvas fueron calculadas con información anterior al día de predicción.",
               r"\bar y^{(w)}_t=\frac{1}{w}\sum_{i=1}^{w}y_{t-i},\quad w\in\{7,14,28\}",
               "Justificación de estadísticas móviles para captar nivel reciente y tendencia.",
               "El suavizado puede ocultar picos comercialmente relevantes.", stage="Ingeniería de características")


def graph_rolling_statistics(ctx: Context) -> GraphicRecord:
    df = to_date(load_model(ctx, "modelo"))
    prefix = "ventas_importe_real_2026_05_roll28_"
    cols = [prefix + "mean", prefix + "std", prefix + "sum"]
    cols = [c for c in cols if c in df.columns]
    sample = df.tail(min(365, len(df))).copy()
    fig, axes = plt.subplots(len(cols), 1, figsize=(13, 8.5), sharex=True)
    if len(cols) == 1:
        axes = [axes]
    labels = {prefix+"mean":"Media móvil", prefix+"std":"Desviación móvil", prefix+"sum":"Suma móvil"}
    for ax, col in zip(axes, cols):
        ax.plot(sample.fecha, numeric(sample[col]))
        ax.set_ylabel(labels[col])
        ax.grid(alpha=0.22)
    axes[0].set_title("Estadísticos móviles de 28 días: nivel, volatilidad y acumulación")
    axes[-1].set_xlabel("Fecha")
    style_time_axis(axes[-1])
    fig.tight_layout()
    filename = "31_estadisticos_moviles_28_dias.png"
    save(fig, ctx, filename)
    return rec(31, "Estadísticos móviles de 28 días", filename, "dataset_modelado_diario.xlsx", "modelo",
               ", ".join(cols), "Distinguir tres propiedades históricas: nivel promedio, variabilidad y volumen acumulado.",
               "La media representa nivel local; la desviación mide inestabilidad; la suma expresa volumen del periodo.",
               "Cada panel utiliza la misma ventana, pero responde a una propiedad estadística distinta.",
               r"\mu_{w,t}=\frac{1}{w}\sum y_{t-i},\quad s_{w,t}=\sqrt{\frac{1}{w-1}\sum(y_{t-i}-\mu_{w,t})^2},\quad S_{w,t}=\sum y_{t-i}",
               "Descripción académica de ventanas móviles múltiples.",
               "Media y suma pueden resultar casi redundantes si la ventana es fija.", stage="Ingeniería de características")


def graph_event_proximity(ctx: Context) -> GraphicRecord:
    df = to_date(load_model(ctx, "modelo"))
    cols = ["es_fecha_pago", "dias_desde_pago", "dias_hasta_pago"]
    sample = df.tail(min(180, len(df))).copy()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.plot(sample.fecha, numeric(sample["dias_desde_pago"]), label="Días desde pago")
    ax.plot(sample.fecha, numeric(sample["dias_hasta_pago"]), label="Días hasta pago")
    events = sample[numeric(sample["es_fecha_pago"]).fillna(0) == 1]
    ax.scatter(events.fecha, np.zeros(len(events)), marker="|", s=150, label="Fecha de pago")
    style_time_axis(ax)
    ax.set_title("Representación de proximidad temporal a fechas de pago")
    ax.set_ylabel("Distancia en días")
    ax.set_xlabel("Fecha")
    ax.legend()
    fig.tight_layout()
    filename = "32_proximidad_fechas_pago.png"
    save(fig, ctx, filename)
    return rec(32, "Proximidad a eventos comerciales", filename, "dataset_modelado_diario.xlsx", "modelo",
               ", ".join(cols), "Mostrar cómo una bandera binaria se transforma en distancias temporales más informativas.",
               "Las trayectorias en forma de diente de sierra miden recencia y anticipación; los marcadores identifican el evento.",
               "La distancia permite diferenciar días previos y posteriores aunque ambos tengan bandera cero.",
               r"d^-_t=t-\max\{s<t:I_s=1\},\qquad d^+_t=\min\{s>t:I_s=1\}-t",
               "Ingeniería de características de festivos, quincenas y eventos.",
               "La variable indica cercanía temporal, no intensidad del efecto comercial.", stage="Ingeniería de características")


def graph_event_windows(ctx: Context) -> GraphicRecord:
    df = to_date(load_model(ctx, "modelo"))
    cols = ["festivos_7d", "festivos_30d", "pagos_7d", "pagos_30d"]
    cols = [c for c in cols if c in df.columns]
    sample = df.tail(min(365, len(df)))
    fig, ax = plt.subplots(figsize=(13, 6.5))
    for col in cols:
        ax.plot(sample.fecha, numeric(sample[col]), label=human(col))
    style_time_axis(ax)
    ax.set_title("Acumulación histórica de eventos en ventanas de 7 y 30 días")
    ax.set_ylabel("Número de eventos previos")
    ax.set_xlabel("Fecha")
    ax.legend(ncol=2)
    fig.tight_layout()
    filename = "33_ventanas_eventos_7_30_dias.png"
    save(fig, ctx, filename)
    return rec(33, "Ventanas históricas de eventos", filename, "dataset_modelado_diario.xlsx", "modelo",
               ", ".join(cols), "Representar la densidad reciente de festivos y fechas de pago en distintos horizontes.",
               "Una ventana corta captura concentración inmediata; una ventana larga resume el contexto mensual reciente.",
               "El desplazamiento de un día impide incorporar el evento del día objetivo como historia ya observada.",
               r"E^{(w)}_t=\sum_{i=1}^{w}I_{t-i}",
               "Justificación de acumuladores de eventos y control de fuga temporal.",
               "Eventos distintos reciben el mismo peso dentro de la ventana.", stage="Ingeniería de características")


def graph_recency_activity(ctx: Context) -> GraphicRecord:
    df = to_date(load_model(ctx, "modelo"))
    cols = ["dias_desde_ultima_venta", "dias_desde_ultima_compra"]
    sample = df.tail(min(365, len(df)))
    fig, ax = plt.subplots(figsize=(13, 6.5))
    for col in cols:
        ax.plot(sample.fecha, numeric(sample[col]), label=human(col))
    style_time_axis(ax)
    ax.set_title("Recencia de actividad comercial: días desde la última venta y compra")
    ax.set_ylabel("Días transcurridos")
    ax.set_xlabel("Fecha")
    ax.legend()
    fig.tight_layout()
    filename = "34_recencia_ventas_compras.png"
    save(fig, ctx, filename)
    return rec(34, "Recencia de actividad", filename, "dataset_modelado_diario.xlsx", "modelo",
               ", ".join(cols), "Cuantificar periodos de inactividad y comportamiento intermitente de ventas y compras.",
               "Los incrementos continuos representan rachas sin operación; el retorno a valores bajos ocurre después de una nueva actividad.",
               "La recencia resume información diferente al importe o al número de operaciones.",
               r"R_t=t-\max\{s<t:x_s>0\}",
               "Variables derivadas para small data y series intermitentes.",
               "Al inicio de la serie la recencia depende del tratamiento adoptado cuando no existe evento previo.", stage="Ingeniería de características")


def graph_financial_derived_indicators(ctx: Context) -> GraphicRecord:
    df = to_date(load_model(ctx, "modelo"))
    cols = ["ventas_vs_compras_ratio_7d", "ventas_minus_compras_7d"]
    sample = df.tail(min(365, len(df))).copy()
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    axes[0].plot(sample.fecha, numeric(sample[cols[0]]))
    axes[0].axhline(1, linestyle="--", linewidth=1)
    axes[0].set_ylabel("Razón ventas/compras")
    axes[0].grid(alpha=0.22)
    axes[1].plot(sample.fecha, numeric(sample[cols[1]]))
    axes[1].axhline(0, linestyle="--", linewidth=1)
    axes[1].set_ylabel("Ventas − compras")
    axes[1].set_xlabel("Fecha")
    axes[1].grid(alpha=0.22)
    axes[0].set_title("Indicadores derivados de equilibrio financiero en ventana de 7 días")
    style_time_axis(axes[1])
    fig.tight_layout()
    filename = "35_indicadores_financieros_derivados_7d.png"
    save(fig, ctx, filename)
    return rec(35, "Indicadores derivados de estabilidad financiera", filename, "dataset_modelado_diario.xlsx", "modelo",
               ", ".join(cols), "Integrar ventas y compras recientes en medidas relativas y absolutas de equilibrio operativo.",
               "Una razón superior a uno y una diferencia positiva indican que el promedio reciente de ventas supera al de compras.",
               "La razón y la diferencia responden a escalas distintas y son complementarias.",
               r"Q_t=\frac{\bar V^{(7)}_t}{\bar C^{(7)}_t},\qquad D_t=\bar V^{(7)}_t-\bar C^{(7)}_t",
               "Vínculo entre ingeniería de características y planeación financiera.",
               "La razón se vuelve inestable cuando las compras promedio son cero; el código reemplaza esos casos por cero.", stage="Ingeniería de características")


def graph_target_predictor_scatter(ctx: Context) -> GraphicRecord:
    df = load_model(ctx, "modelo")
    xcol = "ventas_importe_real_2026_05_roll7_mean"
    ycol = "target_ventas_importe_real_2026_05"
    work = df[[xcol, ycol]].apply(pd.to_numeric, errors="coerce").dropna()
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    ax.scatter(work[xcol], work[ycol], alpha=0.35, s=18)
    if len(work) > 1 and work[xcol].std() > 0:
        coef = np.polyfit(work[xcol], work[ycol], 1)
        x = np.linspace(work[xcol].min(), work[xcol].max(), 100)
        ax.plot(x, coef[0] * x + coef[1], linewidth=1.5)
    ax.set_title("Relación entre promedio histórico de 7 días y venta observada")
    ax.set_xlabel("Promedio de ventas de los 7 días anteriores")
    ax.set_ylabel("Venta observada")
    ax.grid(alpha=0.22)
    fig.tight_layout()
    filename = "36_relacion_media7_objetivo_ventas.png"
    save(fig, ctx, filename)
    corr = work[xcol].corr(work[ycol])
    return rec(36, "Relación predictor histórico–objetivo", filename, "dataset_modelado_diario.xlsx", "modelo",
               f"{xcol}, {ycol}", "Ilustrar la capacidad descriptiva de una característica histórica frente al objetivo contemporáneo.",
               f"La correlación lineal observada es r={corr:.3f}; la dispersión alrededor de la tendencia evidencia variabilidad no explicada por un único predictor.",
               "Cada punto es un día; la línea solo resume tendencia lineal.",
               r"y_t=\beta_0+\beta_1\bar y^{(7)}_t+\varepsilon_t",
               "Transición entre feature engineering y modelado predictivo.",
               "La asociación dentro de muestra no equivale a desempeño fuera de muestra.", stage="Ingeniería de características")


def graph_feature_target_heatmap(ctx: Context) -> GraphicRecord:
    df = load_model(ctx, "modelo")
    candidates = [
        "target_ventas_importe_real_2026_05", "target_compras_total_real_2026_05",
        "target_ventas_registros", "target_compras_registros",
        "ventas_importe_real_2026_05_lag1", "ventas_importe_real_2026_05_lag7",
        "ventas_importe_real_2026_05_roll7_mean", "ventas_importe_real_2026_05_roll28_std",
        "compras_total_real_2026_05_lag1", "compras_total_real_2026_05_lag7",
        "compras_total_real_2026_05_roll7_mean", "dias_desde_ultima_venta",
        "dias_desde_ultima_compra", "es_fecha_pago", "es_festivo_mexicano",
        "ventas_vs_compras_ratio_7d", "ventas_minus_compras_7d",
    ]
    cols = [c for c in candidates if c in df.columns]
    corr = df[cols].apply(pd.to_numeric, errors="coerce").corr()
    fig, ax = plt.subplots(figsize=(13, 11))
    im = ax.imshow(corr.values, vmin=-1, vmax=1)
    labels = wrap([human(c) for c in cols], 19)
    ax.set_xticks(np.arange(len(cols)), labels, rotation=55, ha="right")
    ax.set_yticks(np.arange(len(cols)), labels)
    ax.set_title("Matriz de correlación de objetivos y características ingenierizadas representativas")
    fig.colorbar(im, ax=ax, label="Correlación de Pearson")
    fig.tight_layout()
    filename = "37_correlacion_features_objetivos.png"
    save(fig, ctx, filename)
    return rec(37, "Correlación entre objetivos y features representativos", filename,
               "dataset_modelado_diario.xlsx", "modelo", ", ".join(cols),
               "Examinar relaciones lineales, redundancia potencial y diferencias entre objetivos monetarios y operativos.",
               "Los bloques de alta correlación entre rezagos y ventanas anticipan la necesidad de selección de características y PCA.",
               "La escala va de −1 a 1; asociaciones cercanas a cero pueden ocultar relaciones no lineales.",
               r"r_{jk}=Corr(x_j,x_k)",
               "Cierre de ingeniería de características y transición a multicolinealidad.",
               "La matriz es exploratoria y no controla autocorrelación, tendencia ni múltiples comparaciones.", stage="Ingeniería de características")


def graph_feature_completeness(ctx: Context) -> GraphicRecord:
    df = load_model(ctx, "modelo")
    missing = df.isna().mean().mul(100)
    zeros = df.select_dtypes(include=[np.number]).eq(0).mean().mul(100)
    top = pd.DataFrame({"nulos": missing, "ceros": zeros}).fillna(0)
    top["max"] = top[["nulos", "ceros"]].max(axis=1)
    top = top.sort_values("max", ascending=False).head(ctx.top_n).sort_values("max")
    fig, ax = plt.subplots(figsize=(12, 7.5))
    y = np.arange(len(top))
    ax.barh(y, top["ceros"], label="Ceros")
    ax.barh(y, top["nulos"], left=top["ceros"], label="Nulos")
    ax.set_yticks(y, wrap(top.index, 42))
    ax.set_title("Completitud y esparsidad de las características construidas")
    ax.set_xlabel("Porcentaje de observaciones")
    ax.legend()
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "38_esparsidad_features_modelado.png"
    save(fig, ctx, filename)
    return rec(38, "Completitud y esparsidad del dataset modelado", filename,
               "dataset_modelado_diario.xlsx", "modelo", "todas las características",
               "Verificar que el tratamiento final elimina nulos e identificar variables dominadas por ceros.",
               "La ausencia de nulos confirma un panel numéricamente completo; porcentajes altos de cero evidencian intermitencia o categorías poco frecuentes.",
               "Los ceros se interpretan como valores válidos únicamente cuando proceden de ausencia real de actividad.",
               r"Z_j=\frac{1}{N}\sum_{t=1}^{N}I(x_{t,j}=0)\times100,\qquad M_j=\frac{1}{N}\sum I(x_{t,j}=NA)\times100",
               "Auditoría final antes del diagnóstico dimensional y entrenamiento.",
               "La completitud sintáctica no garantiza validez semántica ni utilidad predictiva.", stage="Ingeniería de características")



# -----------------------------------------------------------------------------
# 39-50. Perfil del dataset y análisis dimensional: 03_perfil_dataset_y_dimensiones.py
# -----------------------------------------------------------------------------
def load_profile(ctx: Context, sheet: str) -> pd.DataFrame:
    """Carga el libro del perfil buscando primero en analysis_dir y después en input_dir."""
    candidates = []
    if ctx.analysis_dir is not None:
        candidates.append(ctx.analysis_dir / "01_perfil_dataset_y_dimensiones.xlsx")
    candidates.append(ctx.input_dir / "01_perfil_dataset_y_dimensiones.xlsx")
    candidates.append(ctx.input_dir.parent / "output" / "analisis_dimensional" / "01_perfil_dataset_y_dimensiones.xlsx")
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        searched = "\n - ".join(str(p) for p in candidates)
        raise FileNotFoundError(f"No se encontró 01_perfil_dataset_y_dimensiones.xlsx. Rutas revisadas:\n - {searched}")
    with pd.ExcelFile(path) as xls:
        if sheet not in xls.sheet_names:
            raise ValueError(f"{path.name} no contiene la hoja '{sheet}'. Hojas: {xls.sheet_names}")
    return pd.read_excel(path, sheet_name=sheet)


def profile_source_name() -> str:
    return "01_perfil_dataset_y_dimensiones.xlsx"


def graph_profile_general_structure(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "resumen_general")
    values = dict(zip(df["metrica"].astype(str), df["valor"]))
    metrics = ["filas", "columnas", "predictores", "objetivos"]
    labels = ["Observaciones", "Columnas", "Predictores", "Objetivos"]
    nums = [float(values.get(m, 0)) for m in metrics]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8))
    axes[0].bar([labels[0]], [nums[0]])
    axes[0].set_title("Tamaño muestral")
    axes[0].set_ylabel("Número de observaciones")
    axes[0].grid(axis="y", alpha=0.22)
    axes[0].text(0, nums[0], f"{int(nums[0]):,}", ha="center", va="bottom")
    axes[1].bar(labels[1:], nums[1:])
    axes[1].set_title("Estructura de variables")
    axes[1].set_ylabel("Número de columnas")
    axes[1].grid(axis="y", alpha=0.22)
    for i, value in enumerate(nums[1:]):
        axes[1].text(i, value, f"{int(value):,}", ha="center", va="bottom")
    fig.suptitle("Estructura general del dataset de modelado")
    fig.tight_layout()
    filename = "39_estructura_general_dataset_modelado.png"
    save(fig, ctx, filename)
    ratio = nums[2] / nums[0] if nums[0] else float("nan")
    return rec(39, "Estructura general del dataset", filename, profile_source_name(), "resumen_general",
               "filas, columnas, predictores, objetivos",
               "Presentar simultáneamente el tamaño muestral y la complejidad dimensional del panel de modelado.",
               f"El dataset contiene {int(nums[0]):,} observaciones y {int(nums[2]):,} predictores; la razón predictores/observaciones es {ratio:.3f}.",
               "Una razón elevada entre predictores y observaciones incrementa el riesgo de sobreajuste y justifica reducción dimensional.",
               r"R_{p/n}=\frac{p}{n}",
               "Inicio de la sección de perfil del dataset y diagnóstico de small data.",
               "La razón p/n es un indicador estructural; no determina por sí sola el desempeño de los modelos.",
               stage="Perfil y dimensionalidad")


def graph_profile_dimension_counts(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "resumen_dimensiones").sort_values("variables")
    fig, ax = plt.subplots(figsize=(11.8, 7.4))
    ax.barh(wrap(df["dimension"], 34), df["variables"])
    ax.set_title("Número de variables por dimensión metodológica")
    ax.set_xlabel("Variables")
    ax.set_ylabel("Dimensión")
    ax.grid(axis="x", alpha=0.22)
    for i, value in enumerate(df["variables"]):
        ax.text(value, i, f" {int(value)}", va="center")
    fig.tight_layout()
    filename = "40_variables_por_dimension_metodologica.png"
    save(fig, ctx, filename)
    dominant = df.loc[df["variables"].idxmax()]
    return rec(40, "Variables por dimensión metodológica", filename, profile_source_name(), "resumen_dimensiones",
               "dimension, variables", "Cuantificar qué familias explican la dimensionalidad total.",
               f"La dimensión dominante es '{dominant['dimension']}' con {int(dominant['variables'])} variables.",
               "Las dimensiones con más columnas son candidatas prioritarias para revisar redundancia y parsimonia.",
               r"p_g=\sum_{j=1}^{p}I(d_j=g)",
               "Descripción del dataset y justificación del análisis dimensional.",
               "El conteo no equivale a relevancia predictiva.", stage="Perfil y dimensionalidad")


def graph_profile_zero_by_dimension(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "resumen_dimensiones").copy()
    df["ceros_promedio"] = pd.to_numeric(df["ceros_promedio"], errors="coerce") * 100
    df = df.dropna(subset=["ceros_promedio"]).sort_values("ceros_promedio")
    fig, ax = plt.subplots(figsize=(11.8, 7.2))
    ax.barh(wrap(df["dimension"], 34), df["ceros_promedio"])
    ax.set_title("Esparsidad promedio por dimensión metodológica")
    ax.set_xlabel("Observaciones iguales a cero (%)")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.22)
    for i, value in enumerate(df["ceros_promedio"]):
        ax.text(value, i, f" {value:.1f}%", va="center")
    fig.tight_layout()
    filename = "41_esparsidad_promedio_por_dimension.png"
    save(fig, ctx, filename)
    top = df.iloc[-1]
    return rec(41, "Esparsidad promedio por dimensión", filename, profile_source_name(), "resumen_dimensiones",
               "dimension, ceros_promedio", "Comparar la intermitencia y concentración de ceros entre familias de predictores.",
               f"La mayor proporción promedio de ceros corresponde a '{top['dimension']}' con {top['ceros_promedio']:.1f}%.",
               "Una dimensión muy esparsa puede ser informativa, pero exige métricas y modelos robustos a ceros.",
               r"Z_g=\frac{1}{p_g}\sum_{j\in g}\left[\frac{1}{n}\sum_{i=1}^{n}I(x_{ij}=0)\right]100",
               "Diagnóstico de intermitencia, small data y calidad de predictores.",
               "Un cero puede representar ausencia real de actividad y no un error.", stage="Perfil y dimensionalidad")


def graph_profile_missing_by_dimension(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "resumen_dimensiones").copy()
    df["nulos_promedio"] = pd.to_numeric(df["nulos_promedio"], errors="coerce") * 100
    df = df.dropna(subset=["nulos_promedio"]).sort_values("nulos_promedio")
    fig, ax = plt.subplots(figsize=(11.8, 7.2))
    ax.barh(wrap(df["dimension"], 34), df["nulos_promedio"])
    ax.set_title("Valores faltantes promedio por dimensión metodológica")
    ax.set_xlabel("Valores nulos (%)")
    maxv = max(1.0, float(df["nulos_promedio"].max()) * 1.15)
    ax.set_xlim(0, maxv)
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "42_nulos_promedio_por_dimension.png"
    save(fig, ctx, filename)
    total = float(df["nulos_promedio"].mean()) if len(df) else 0
    return rec(42, "Nulos promedio por dimensión", filename, profile_source_name(), "resumen_dimensiones",
               "dimension, nulos_promedio", "Auditar la completitud del panel por familia de variables.",
               f"El promedio simple entre dimensiones es {total:.3f}% de valores nulos.",
               "Barras cercanas a cero indican que la fase de ingeniería produjo un panel completo.",
               r"M_g=\frac{1}{p_g}\sum_{j\in g}\frac{NA_j}{n}\times100",
               "Control de calidad previo a selección de características.",
               "La ausencia de nulos no garantiza ausencia de imputaciones o errores semánticos.", stage="Perfil y dimensionalidad")


def graph_profile_constants(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "resumen_dimensiones").copy()
    df["variables_constantes"] = pd.to_numeric(df["variables_constantes"], errors="coerce").fillna(0)
    df = df.sort_values("variables_constantes")
    fig, ax = plt.subplots(figsize=(11.5, 7))
    ax.barh(wrap(df["dimension"], 34), df["variables_constantes"])
    ax.set_title("Variables constantes detectadas por dimensión")
    ax.set_xlabel("Número de variables con un único valor")
    ax.grid(axis="x", alpha=0.22)
    for i, value in enumerate(df["variables_constantes"]):
        ax.text(value, i, f" {int(value)}", va="center")
    fig.tight_layout()
    filename = "43_variables_constantes_por_dimension.png"
    save(fig, ctx, filename)
    total = int(df["variables_constantes"].sum())
    return rec(43, "Variables constantes por dimensión", filename, profile_source_name(), "resumen_dimensiones",
               "dimension, variables_constantes", "Identificar columnas sin variabilidad y, por tanto, sin capacidad discriminante.",
               f"Se detectaron {total} variables constantes en el conjunto perfilado.",
               "Una variable constante no puede explicar diferencias entre observaciones y normalmente debe excluirse.",
               r"Var(X_j)=0\Rightarrow X_j=c\;\forall i",
               "Auditoría de baja varianza y depuración previa al modelado.",
               "Una variable constante en esta muestra podría variar en periodos futuros, aunque no aporta al ajuste actual.", stage="Perfil y dimensionalidad")


def graph_profile_cardinality_zero_scatter(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "perfil_variables").copy()
    df["valores_unicos"] = pd.to_numeric(df["valores_unicos"], errors="coerce")
    df["porcentaje_ceros"] = pd.to_numeric(df["porcentaje_ceros"], errors="coerce") * 100
    df = df.dropna(subset=["valores_unicos", "porcentaje_ceros"])
    fig, ax = plt.subplots(figsize=(11, 7))
    for dimension, part in df.groupby("dimension"):
        ax.scatter(part["valores_unicos"], part["porcentaje_ceros"], alpha=0.55, s=24, label=str(dimension))
    ax.set_xscale("symlog", linthresh=2)
    ax.set_title("Cardinalidad frente a esparsidad de las variables")
    ax.set_xlabel("Número de valores únicos (escala simétrica logarítmica)")
    ax.set_ylabel("Valores iguales a cero (%)")
    ax.grid(alpha=0.22)
    if df["dimension"].nunique() <= 12:
        ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    filename = "44_cardinalidad_vs_esparsidad_variables.png"
    save(fig, ctx, filename)
    return rec(44, "Cardinalidad frente a esparsidad", filename, profile_source_name(), "perfil_variables",
               "valores_unicos, porcentaje_ceros, dimension", "Distinguir variables constantes, binarias, discretas y continuas según su cardinalidad y concentración de ceros.",
               "Los puntos en la zona superior izquierda representan variables con pocos estados y alta esparsidad.",
               "La combinación de baja cardinalidad y muchos ceros puede indicar eventos raros o variables poco informativas.",
               r"K_j=|\{x_{1j},\ldots,x_{nj}\}|,\qquad Z_j=\frac{\sum_iI(x_{ij}=0)}{n}100",
               "Caracterización estructural de predictores y justificación de filtros de baja varianza.",
               "La gráfica no evalúa relación con los objetivos.", stage="Perfil y dimensionalidad")


def graph_profile_top_zero_variables(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "perfil_variables").copy()
    df["porcentaje_ceros"] = pd.to_numeric(df["porcentaje_ceros"], errors="coerce") * 100
    top = df.dropna(subset=["porcentaje_ceros"]).sort_values("porcentaje_ceros", ascending=False).head(ctx.top_n).sort_values("porcentaje_ceros")
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.barh(wrap(top["variable"], 42), top["porcentaje_ceros"])
    ax.set_title(f"Variables con mayor concentración de ceros (Top {len(top)})")
    ax.set_xlabel("Valores iguales a cero (%)")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "45_variables_mayor_concentracion_ceros.png"
    save(fig, ctx, filename)
    return rec(45, "Variables con mayor concentración de ceros", filename, profile_source_name(), "perfil_variables",
               "variable, porcentaje_ceros", "Identificar predictores individuales dominados por ausencia de actividad.",
               "Las primeras posiciones corresponden a columnas donde la señal positiva aparece en pocos días.",
               "Estas variables deben revisarse junto con su importancia predictiva antes de eliminarlas.",
               r"Z_j=\frac{1}{n}\sum_{i=1}^{n}I(x_{ij}=0)\times100",
               "Anexo de calidad del dataset y discusión sobre demanda intermitente.",
               "Una alta tasa de ceros puede representar un evento raro valioso.", stage="Perfil y dimensionalidad")


def graph_profile_variability(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "perfil_variables").copy()
    for col in ["media", "desviacion"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    valid = df[(df["media"].abs() > 1e-9) & df["desviacion"].notna()].copy()
    valid["coef_variacion_abs"] = valid["desviacion"].abs() / valid["media"].abs()
    valid = valid.replace([np.inf, -np.inf], np.nan).dropna(subset=["coef_variacion_abs"])
    top = valid.sort_values("coef_variacion_abs", ascending=False).head(ctx.top_n).sort_values("coef_variacion_abs")
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.barh(wrap(top["variable"], 42), top["coef_variacion_abs"])
    ax.set_title(f"Variables con mayor variabilidad relativa (Top {len(top)})")
    ax.set_xlabel("Coeficiente de variación absoluto")
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "46_coeficiente_variacion_variables.png"
    save(fig, ctx, filename)
    return rec(46, "Variabilidad relativa de las variables", filename, profile_source_name(), "perfil_variables",
               "media, desviacion", "Comparar dispersión relativa entre variables con escalas diferentes.",
               "Valores altos indican que la desviación es grande respecto a la media y pueden señalar volatilidad o intermitencia.",
               "El coeficiente es más interpretable cuando la media está alejada de cero.",
               r"CV_j=\frac{s_j}{|\bar{x}_j|}",
               "Diagnóstico de estabilidad y necesidad de escalamiento.",
               "El CV es inestable para medias cercanas a cero y no se interpreta igual en variables binarias.", stage="Perfil y dimensionalidad")


def graph_profile_iqr(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "perfil_variables").copy()
    for col in ["p25", "p75", "mediana"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["iqr"] = df["p75"] - df["p25"]
    top = df.dropna(subset=["iqr"]).sort_values("iqr", ascending=False).head(ctx.top_n).sort_values("iqr")
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.barh(wrap(top["variable"], 42), top["iqr"])
    ax.set_title(f"Variables con mayor rango intercuartílico (Top {len(top)})")
    ax.set_xlabel("IQR = P75 − P25")
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "47_rango_intercuartil_variables.png"
    save(fig, ctx, filename)
    return rec(47, "Rango intercuartílico de las variables", filename, profile_source_name(), "perfil_variables",
               "p25, p75, variable", "Medir la dispersión robusta del 50% central de cada variable.",
               "Las barras grandes identifican variables con amplitud central elevada sin depender directamente de valores extremos.",
               "El IQR complementa la desviación estándar en distribuciones asimétricas.",
               r"IQR_j=Q_{0.75,j}-Q_{0.25,j}",
               "Descripción estadística y detección preliminar de escalas heterogéneas.",
               "No es comparable entre variables con unidades distintas sin normalización.", stage="Perfil y dimensionalidad")


def graph_profile_target_boxplots(ctx: Context) -> GraphicRecord:
    targets = load_profile(ctx, "objetivos").copy()
    required = ["min", "25%", "50%", "75%", "max"]
    missing = [c for c in required if c not in targets.columns]
    if missing:
        raise ValueError(f"La hoja objetivos no contiene las columnas descriptivas requeridas: {missing}")
    stats = []
    labels = []
    for _, row in targets.iterrows():
        objective = str(row.get("objetivo", "objetivo"))
        values = {c: float(pd.to_numeric(pd.Series([row[c]]), errors="coerce").iloc[0]) for c in required}
        stats.append({
            "label": human(objective.replace("target_", "")),
            "whislo": values["min"], "q1": values["25%"], "med": values["50%"],
            "q3": values["75%"], "whishi": values["max"], "fliers": [],
        })
        labels.append(human(objective.replace("target_", "")))
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    ax.bxp(stats, showfliers=False)
    ax.set_xticklabels(wrap(labels, 18))
    ax.set_title("Resumen de distribución de las variables objetivo")
    ax.set_ylabel("Escala original de cada objetivo")
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    filename = "48_boxplot_resumen_objetivos.png"
    save(fig, ctx, filename)
    return rec(48, "Resumen distributivo de los objetivos", filename, profile_source_name(), "objetivos",
               "min, 25%, 50%, 75%, max", "Comparar posición central, dispersión y amplitud de los cuatro objetivos a partir de sus estadísticos descriptivos.",
               "La caja representa el rango intercuartílico, la línea central la mediana y los bigotes el mínimo y máximo observados.",
               "Las escalas monetarias y de conteo son distintas; la figura describe forma y amplitud, no igualdad de unidades.",
               r"IQR=Q_{0.75}-Q_{0.25}",
               "Caracterización de las variables objetivo antes del modelado.",
               "Los valores extremos pueden comprimir visualmente las cajas de objetivos con menor escala.", stage="Perfil y dimensionalidad")


def graph_profile_target_sparsity(ctx: Context) -> GraphicRecord:
    profile = load_profile(ctx, "perfil_variables").copy()
    targets = profile[profile["variable"].astype(str).str.startswith("target_")].copy()
    targets["porcentaje_ceros"] = pd.to_numeric(targets["porcentaje_ceros"], errors="coerce") * 100
    targets = targets.sort_values("porcentaje_ceros")
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    ax.barh(wrap([human(v.replace("target_", "")) for v in targets["variable"]], 25), targets["porcentaje_ceros"])
    ax.set_title("Intermitencia de las variables objetivo")
    ax.set_xlabel("Observaciones iguales a cero (%)")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.22)
    for i, value in enumerate(targets["porcentaje_ceros"]):
        ax.text(value, i, f" {value:.1f}%", va="center")
    fig.tight_layout()
    filename = "49_intermitencia_variables_objetivo.png"
    save(fig, ctx, filename)
    return rec(49, "Intermitencia de las variables objetivo", filename, profile_source_name(), "perfil_variables",
               "variable, porcentaje_ceros", "Cuantificar cuántos días presentan ausencia de ventas o compras en cada objetivo.",
               "Los objetivos con mayor proporción de ceros requieren especial cautela al usar MAPE y modelos continuos convencionales.",
               "Las barras permiten distinguir demanda intermitente de variabilidad monetaria.",
               r"Z_y=\frac{1}{n}\sum_{t=1}^{n}I(y_t=0)\times100",
               "Justificación de métricas de error y dificultad diferencial entre objetivos.",
               "El cero debe provenir de un calendario completo y una captura exhaustiva.", stage="Perfil y dimensionalidad")


def graph_profile_dimension_quality_matrix(ctx: Context) -> GraphicRecord:
    df = load_profile(ctx, "resumen_dimensiones").copy()
    cols = ["variables", "nulos_promedio", "ceros_promedio", "variables_constantes"]
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["nulos_promedio"] *= 100
    df["ceros_promedio"] *= 100
    matrix = df.set_index("dimension")[cols].copy()
    normalized = matrix.copy()
    for c in normalized.columns:
        mn, mx = normalized[c].min(), normalized[c].max()
        normalized[c] = 0 if mx == mn else (normalized[c] - mn) / (mx - mn)
    fig, ax = plt.subplots(figsize=(10.5, 7.8))
    im = ax.imshow(normalized.values, aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(cols)), ["N.º variables", "Nulos %", "Ceros %", "Constantes"])
    ax.set_yticks(np.arange(len(normalized.index)), wrap(normalized.index, 28))
    ax.set_title("Matriz normalizada de complejidad y calidad por dimensión")
    fig.colorbar(im, ax=ax, label="Intensidad relativa dentro de cada indicador")
    for i in range(len(matrix)):
        for j, c in enumerate(cols):
            value = matrix.iloc[i, j]
            label = f"{value:.1f}" if c in ["nulos_promedio", "ceros_promedio"] else f"{int(value)}"
            ax.text(j, i, label, ha="center", va="center", fontsize=7)
    fig.tight_layout()
    filename = "50_matriz_calidad_dimensiones.png"
    save(fig, ctx, filename)
    return rec(50, "Matriz de calidad por dimensión", filename, profile_source_name(), "resumen_dimensiones",
               ", ".join(cols), "Integrar en una sola figura complejidad, nulos, esparsidad y variables constantes por dimensión.",
               "Las celdas intensas señalan dimensiones relativamente altas en cada indicador; los números conservan la escala original.",
               "La normalización es por columna y permite comparar patrones, no magnitudes entre indicadores distintos.",
               r"z_{gk}=\frac{x_{gk}-\min_gx_{gk}}{\max_gx_{gk}-\min_gx_{gk}}",
               "Cierre del perfil dimensional y transición al diagnóstico de multicolinealidad.",
               "Un indicador alto no implica eliminación automática; debe combinarse con relevancia predictiva e interpretabilidad.", stage="Perfil y dimensionalidad")


# -----------------------------------------------------------------------------
# 51-62. Diagnóstico de multicolinealidad y redundancia
# -----------------------------------------------------------------------------
MULTICOL_TARGET_LABELS = {
    "filtro_target_ventas_import": "Importe de ventas",
    "filtro_target_compras_total": "Importe de compras",
    "filtro_target_ventas_regist": "Registros de ventas",
    "filtro_target_compras_regis": "Registros de compras",
}


def multicol_path(ctx: Context) -> Path:
    candidates = []
    if ctx.analysis_dir is not None:
        candidates.append(ctx.analysis_dir / "02_diagnostico_multicolinealidad.xlsx")
    candidates.extend([
        ctx.input_dir / "02_diagnostico_multicolinealidad.xlsx",
        ctx.input_dir.parent / "output" / "analisis_dimensional" / "02_diagnostico_multicolinealidad.xlsx",
    ])
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("No se encontró 02_diagnostico_multicolinealidad.xlsx.")


def load_multicol(ctx: Context, sheet: str) -> pd.DataFrame:
    path = multicol_path(ctx)
    with pd.ExcelFile(path) as xls:
        if sheet not in xls.sheet_names:
            raise ValueError(f"{path.name} no contiene la hoja '{sheet}'.")
    return pd.read_excel(path, sheet_name=sheet)


def multicol_sheets(ctx: Context, prefix: str) -> list[str]:
    with pd.ExcelFile(multicol_path(ctx)) as xls:
        return [s for s in xls.sheet_names if s.startswith(prefix)]


def target_from_sheet(sheet: str) -> str:
    return MULTICOL_TARGET_LABELS.get(sheet, sheet.replace("filtro_target_", "").replace("_", " ").title())


def graph_multicol_correlation_distribution(ctx: Context) -> GraphicRecord:
    df = load_multicol(ctx, "pares_correlacion_alta")
    values = numeric(df["correlacion_abs"]).dropna().clip(upper=1)
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    ax.hist(values, bins=min(20, max(6, int(np.sqrt(len(values))))))
    ax.axvline(0.92, linestyle="--", label="Umbral 0.92")
    ax.axvline(values.median(), linestyle=":", label=f"Mediana {values.median():.3f}")
    ax.set(title="Distribución de correlaciones absolutas consideradas redundantes",
           xlabel="Correlación absoluta", ylabel="Número de pares")
    ax.set_xlim(0.90, 1.005); ax.grid(axis="y", alpha=.22); ax.legend(); fig.tight_layout()
    filename="51_distribucion_correlaciones_altas.png"; save(fig,ctx,filename)
    return rec(51,"Distribución de correlaciones altas",filename,"02_diagnostico_multicolinealidad.xlsx","pares_correlacion_alta",
               "correlacion_abs","Mostrar la intensidad global de la redundancia lineal detectada.",
               f"Se identificaron {len(values)} pares; la mediana es {values.median():.3f}.",
               "Valores próximos a uno indican representaciones prácticamente equivalentes.",
               "|r_jk| >= 0.92","Apertura del diagnóstico de multicolinealidad.",
               "Solo representa pares que superaron el umbral.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_top_pairs(ctx: Context) -> GraphicRecord:
    df=load_multicol(ctx,"pares_correlacion_alta").copy(); df["correlacion_abs"]=numeric(df["correlacion_abs"]).clip(upper=1)
    top=df.nlargest(ctx.top_n,"correlacion_abs"); labels=top.variable_1.astype(str)+" ↔ "+top.variable_2.astype(str)
    fig,ax=plt.subplots(figsize=(13,8)); y=np.arange(len(top)); ax.barh(y,top.correlacion_abs)
    ax.set_yticks(y,wrap(labels,58)); ax.invert_yaxis(); ax.axvline(.92,linestyle="--",label="Umbral 0.92")
    ax.set_xlim(max(.90,float(top.correlacion_abs.min())-.015),1.005); ax.set_title("Pares de predictores con mayor correlación absoluta")
    ax.set_xlabel("Correlación absoluta"); ax.grid(axis="x",alpha=.22); ax.legend(); fig.tight_layout()
    filename="52_pares_predictores_mayor_correlacion.png"; save(fig,ctx,filename); strongest=top.iloc[0]
    return rec(52,"Pares de mayor correlación",filename,"02_diagnostico_multicolinealidad.xlsx","pares_correlacion_alta",
               "variable_1, variable_2, correlacion_abs","Identificar transformaciones que contienen información casi duplicada.",
               f"El par principal es {strongest.variable_1} y {strongest.variable_2}, con |r|={strongest.correlacion_abs:.4f}.",
               "Los pares más cercanos a uno requieren revisión prioritaria.","r_jk = cov(X_j,X_k)/(s_j s_k)",
               "Evidencia empírica de redundancia entre características.","Correlación alta no implica que una variable sea incorrecta.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_redundancy_network(ctx: Context) -> GraphicRecord:
    df=load_multicol(ctx,"pares_correlacion_alta").copy(); df["correlacion_abs"]=numeric(df["correlacion_abs"]).clip(upper=1)
    degree=pd.concat([df.variable_1,df.variable_2]).value_counts(); nodes=degree.head(min(ctx.top_n,16)).index.tolist()
    edges=df[df.variable_1.isin(nodes)&df.variable_2.isin(nodes)]
    theta=np.linspace(0,2*np.pi,len(nodes),endpoint=False); pos={n:(np.cos(a),np.sin(a)) for n,a in zip(nodes,theta)}
    fig,ax=plt.subplots(figsize=(10,9))
    for _,r in edges.iterrows():
        x1,y1=pos[r.variable_1]; x2,y2=pos[r.variable_2]; ax.plot([x1,x2],[y1,y2],alpha=.4,linewidth=.5+2*(r.correlacion_abs-.92)/.08)
    ax.scatter([pos[n][0] for n in nodes],[pos[n][1] for n in nodes],s=[100+40*degree[n] for n in nodes])
    for n in nodes:
        x,y=pos[n]; ax.text(1.12*x,1.12*y,"\n".join(textwrap.wrap(n,22)),ha="center",va="center",fontsize=7)
    ax.set_title("Red de redundancia entre los predictores más conectados"); ax.set_aspect("equal"); ax.axis("off"); fig.tight_layout()
    filename="53_red_redundancia_predictores.png"; save(fig,ctx,filename)
    return rec(53,"Red de redundancia",filename,"02_diagnostico_multicolinealidad.xlsx","pares_correlacion_alta",
               "variable_1, variable_2, correlacion_abs","Representar la multicolinealidad como una red de dependencias.",
               f"La variable más conectada es {degree.index[0]}, con {int(degree.iloc[0])} relaciones.",
               "El tamaño del nodo representa frecuencia de conexiones y la arista representa correlación.",
               "G=(V,E), E={(j,k): |r_jk|>=0.92}","Síntesis visual de grupos redundantes.",
               "Se muestran únicamente las variables más conectadas.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_variable_frequency(ctx: Context) -> GraphicRecord:
    df=load_multicol(ctx,"pares_correlacion_alta"); counts=pd.concat([df.variable_1,df.variable_2]).value_counts().head(ctx.top_n).sort_values()
    fig,ax=plt.subplots(figsize=(12,7.5)); ax.barh(wrap(counts.index,44),counts.values); ax.set_title("Variables más frecuentes en pares redundantes")
    ax.set_xlabel("Número de pares"); ax.grid(axis="x",alpha=.22); fig.tight_layout(); filename="54_frecuencia_variables_redundantes.png"; save(fig,ctx,filename)
    return rec(54,"Frecuencia de variables redundantes",filename,"02_diagnostico_multicolinealidad.xlsx","pares_correlacion_alta",
               "variable_1, variable_2","Priorizar variables que participan repetidamente en relaciones de alta correlación.",
               f"{counts.idxmax()} aparece en {int(counts.max())} pares.","Una frecuencia alta señala familias de transformaciones similares.",
               "d_j = suma I(|r_jk|>=0.92)","Priorización de variables para depuración.","La frecuencia no mide relación con el objetivo.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_decisions_by_target(ctx: Context) -> GraphicRecord:
    filter_sheets=multicol_sheets(ctx,"filtro_target_"); kept_sheets=multicol_sheets(ctx,"conservadas_target_")
    rows=[]
    for i,s in enumerate(filter_sheets): rows.append({"objetivo":target_from_sheet(s),"eliminadas":len(load_multicol(ctx,s)),"conservadas":len(load_multicol(ctx,kept_sheets[i]))})
    out=pd.DataFrame(rows); x=np.arange(len(out)); w=.38; fig,ax=plt.subplots(figsize=(11,6.5))
    ax.bar(x-w/2,out.conservadas,w,label="Conservadas"); ax.bar(x+w/2,out.eliminadas,w,label="Eliminadas")
    ax.set_xticks(x,wrap(out.objetivo,20)); ax.set_ylabel("Número de predictores"); ax.set_title("Resultado del filtro de correlación por objetivo")
    ax.legend(); ax.grid(axis="y",alpha=.22); fig.tight_layout(); filename="55_conservadas_eliminadas_por_objetivo.png"; save(fig,ctx,filename)
    return rec(55,"Conservadas y eliminadas por objetivo",filename,"02_diagnostico_multicolinealidad.xlsx","filtro_* y conservadas_*",
               "variable_conservada, variable_eliminada","Comparar el efecto de la depuración para cada objetivo.",
               "Cada objetivo conserva su propio conjunto porque la relevancia predictiva cambia.","Las barras comparan magnitud de conservación y eliminación.",
               "S_y = GreedyFilter(X,y,0.92)","Justificación de selección específica por objetivo.","El procedimiento codicioso depende del orden de evaluación.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_kept_dimensions(ctx: Context) -> GraphicRecord:
    kept=multicol_sheets(ctx,"conservadas_target_"); labels=list(MULTICOL_TARGET_LABELS.values()); rows=[]
    for i,s in enumerate(kept):
        for dim,val in load_multicol(ctx,s).dimension.value_counts().items(): rows.append({"objetivo":labels[i],"dimension":dim,"variables":val})
    pivot=pd.DataFrame(rows).pivot_table(index="dimension",columns="objetivo",values="variables",fill_value=0)
    fig,ax=plt.subplots(figsize=(12,8)); im=ax.imshow(pivot.values,aspect="auto"); ax.set_yticks(np.arange(len(pivot)),wrap(pivot.index,28))
    ax.set_xticks(np.arange(len(pivot.columns)),wrap(pivot.columns,18),rotation=20,ha="right"); ax.set_title("Dimensiones conservadas por objetivo")
    fig.colorbar(im,ax=ax,label="Número de variables")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]): ax.text(j,i,str(int(pivot.iloc[i,j])),ha="center",va="center",fontsize=8)
    fig.tight_layout(); filename="56_dimensiones_conservadas_por_objetivo.png"; save(fig,ctx,filename)
    return rec(56,"Dimensiones conservadas",filename,"02_diagnostico_multicolinealidad.xlsx","conservadas_*","variable, dimension",
               "Verificar que la reducción mantenga cobertura conceptual.","Las celdas muestran variables sobrevivientes de cada dimensión.",
               "Una dimensión pequeña puede seguir siendo predictivamente importante.","n_g,y = número de X_j conservadas en dimensión g",
               "Control de interpretabilidad tras la reducción.","El conteo no mide importancia individual.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_keep_drop_scatter(ctx: Context) -> GraphicRecord:
    fig,ax=plt.subplots(figsize=(9,8)); total=0
    for s in multicol_sheets(ctx,"filtro_target_"):
        df=load_multicol(ctx,s); x=numeric(df.corr_objetivo_eliminada); y=numeric(df.corr_objetivo_conservada)
        ax.scatter(x,y,alpha=.65,label=target_from_sheet(s)); total+=len(df)
    lim=max(ax.get_xlim()[1],ax.get_ylim()[1]); ax.plot([0,lim],[0,lim],linestyle="--",label="Igual relevancia")
    ax.set(xlim=(0,lim),ylim=(0,lim),xlabel="Correlación de eliminada",ylabel="Correlación de conservada",title="Relevancia conservada frente a eliminada")
    ax.grid(alpha=.22); ax.legend(fontsize=8); fig.tight_layout(); filename="57_relevancia_conservada_vs_eliminada.png"; save(fig,ctx,filename)
    return rec(57,"Relevancia conservada frente a eliminada",filename,"02_diagnostico_multicolinealidad.xlsx","filtro_*",
               "corr_objetivo_conservada, corr_objetivo_eliminada","Comprobar la regla de conservación por asociación con el objetivo.",
               f"Se representan {total} decisiones; los puntos deben ubicarse sobre o por encima de la diagonal.",
               "La distancia respecto a la diagonal expresa la ventaja de la variable conservada.","keep = argmax |Corr(X_j,y)|",
               "Validación gráfica de la regla codiciosa.","La correlación marginal no captura interacciones.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_relevance_gain(ctx: Context) -> GraphicRecord:
    rows=[]
    for s in multicol_sheets(ctx,"filtro_target_"):
        df=load_multicol(ctx,s); gain=numeric(df.corr_objetivo_conservada)-numeric(df.corr_objetivo_eliminada)
        rows.extend({"objetivo":target_from_sheet(s),"ganancia":v} for v in gain.dropna())
    data=pd.DataFrame(rows); grouped=list(data.groupby("objetivo")); fig,ax=plt.subplots(figsize=(11,6.8))
    ax.boxplot([g.ganancia.values for _,g in grouped],labels=wrap([k for k,_ in grouped],18),showfliers=False); ax.axhline(0)
    ax.set_title("Ganancia de relevancia al conservar una variable"); ax.set_ylabel("Delta de correlación absoluta"); ax.grid(axis="y",alpha=.22)
    fig.tight_layout(); filename="58_ganancia_relevancia_filtro.png"; save(fig,ctx,filename)
    return rec(58,"Ganancia de relevancia",filename,"02_diagnostico_multicolinealidad.xlsx","filtro_*",
               "corr_objetivo_conservada, corr_objetivo_eliminada","Cuantificar la ventaja de la variable conservada.",
               "Valores cercanos a cero corresponden a alternativas casi equivalentes.","La caja resume diferencias por objetivo.",
               "Delta = |Corr(X_keep,y)| - |Corr(X_drop,y)|","Evaluación cuantitativa de decisiones.","Una ventaja pequeña puede justificarse por interpretabilidad.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_vif_ranking(ctx: Context) -> GraphicRecord:
    df=load_multicol(ctx,"vif_opcional").copy(); raw=pd.to_numeric(df.vif,errors="coerce"); finite=raw.replace([np.inf,-np.inf],np.nan).dropna()
    cap=max(20.0,float(finite.quantile(.95)) if len(finite) else 20.0); df["vif_plot"]=raw.replace([np.inf,-np.inf],cap*1.08).fillna(0)
    top=df.nlargest(ctx.top_n,"vif_plot").sort_values("vif_plot"); fig,ax=plt.subplots(figsize=(12,8)); ax.barh(wrap(top.variable,45),top.vif_plot)
    ax.axvline(5,linestyle="--",label="VIF 5"); ax.axvline(10,linestyle=":",label="VIF 10"); ax.set_title("Variables con mayor VIF")
    ax.set_xlabel("VIF; infinitos representados en el límite gráfico"); ax.grid(axis="x",alpha=.22); ax.legend(); fig.tight_layout()
    filename="59_ranking_vif_variables.png"; save(fig,ctx,filename); inf_count=int(np.isinf(raw).sum())
    return rec(59,"Ranking de VIF",filename,"02_diagnostico_multicolinealidad.xlsx","vif_opcional","variable, vif",
               "Identificar dependencia multivariada entre predictores.",f"Se detectaron {inf_count} valores VIF infinitos.",
               "VIF alto indica que una variable puede explicarse mediante otras.","VIF_j = 1/(1-R_j^2)",
               "Complemento al análisis de pares.","Se calcula solo sobre las 80 variables de mayor varianza.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_vif_categories(ctx: Context) -> GraphicRecord:
    v=pd.to_numeric(load_multicol(ctx,"vif_opcional").vif,errors="coerce")
    cat=pd.Series(np.select([v<5,(v>=5)&(v<10),(v>=10)&np.isfinite(v),np.isinf(v)],
                            ["VIF < 5","5 a <10","VIF >=10","VIF infinito"],default="No calculable"))
    counts=cat.value_counts(); fig,ax=plt.subplots(figsize=(9,6.2)); ax.bar(counts.index,counts.values); ax.tick_params(axis="x",rotation=15)
    ax.set_title("Clasificación diagnóstica según VIF"); ax.set_ylabel("Número de variables"); ax.grid(axis="y",alpha=.22)
    fig.tight_layout(); filename="60_clasificacion_variables_vif.png"; save(fig,ctx,filename)
    return rec(60,"Clasificación por VIF",filename,"02_diagnostico_multicolinealidad.xlsx","vif_opcional","vif",
               "Resumir la gravedad de la multicolinealidad multivariada.","Las categorías distinguen niveles bajos, moderados, altos e infinitos.",
               "Una concentración alta respalda reducción dimensional.","VIF_j = 1/(1-R_j^2)","Síntesis académica del VIF.","Los umbrales 5 y 10 son orientativos.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_elimination_overlap(ctx: Context) -> GraphicRecord:
    sets={target_from_sheet(s):set(load_multicol(ctx,s).variable_eliminada.dropna().astype(str)) for s in multicol_sheets(ctx,"filtro_target_")}
    all_vars=set().union(*sets.values()); frequency=pd.Series({v:sum(v in values for values in sets.values()) for v in all_vars}); dist=frequency.value_counts().sort_index()
    fig,ax=plt.subplots(figsize=(9.5,6.3)); ax.bar(dist.index.astype(str),dist.values); ax.set_title("Consistencia de eliminaciones entre objetivos")
    ax.set_xlabel("Número de objetivos que eliminan la misma variable"); ax.set_ylabel("Número de variables"); ax.grid(axis="y",alpha=.22)
    fig.tight_layout(); filename="61_solapamiento_variables_eliminadas.png"; save(fig,ctx,filename); common=len(set.intersection(*sets.values()))
    return rec(61,"Solapamiento de eliminaciones",filename,"02_diagnostico_multicolinealidad.xlsx","filtro_*","variable_eliminada",
               "Evaluar si la redundancia es estable entre objetivos.",f"{common} variables son eliminadas por los cuatro objetivos.",
               "Las eliminadas consistentemente son candidatas a reducción global.","f_j = suma_y I(X_j eliminada)",
               "Definición de candidatos globales y específicos.","La coincidencia no sustituye validación fuera de muestra.",stage="Diagnóstico de multicolinealidad")


def graph_multicol_summary(ctx: Context) -> GraphicRecord:
    pairs=load_multicol(ctx,"pares_correlacion_alta"); filters=[load_multicol(ctx,s) for s in multicol_sheets(ctx,"filtro_target_")]
    kept=[load_multicol(ctx,s) for s in multicol_sheets(ctx,"conservadas_target_")]; unique=len(set(pairs.variable_1.astype(str))|set(pairs.variable_2.astype(str)))
    values=pd.Series({"Pares correlacionados":len(pairs),"Variables implicadas":unique,"Eliminadas promedio":np.mean([len(x) for x in filters]),"Conservadas promedio":np.mean([len(x) for x in kept])})
    fig,ax=plt.subplots(figsize=(10.5,6.5)); ax.bar(values.index,values.values); ax.tick_params(axis="x",rotation=18); ax.set_title("Síntesis del diagnóstico de multicolinealidad")
    ax.set_ylabel("Conteo"); ax.grid(axis="y",alpha=.22); fig.tight_layout(); filename="62_resumen_diagnostico_multicolinealidad.png"; save(fig,ctx,filename)
    return rec(62,"Síntesis de multicolinealidad",filename,"02_diagnostico_multicolinealidad.xlsx","Varias hojas",
               "pares, variables, conservadas y eliminadas","Cerrar la etapa con una visión cuantitativa de la redundancia.",
               "Integra pares detectados y magnitud de decisiones por objetivo.","Es evidencia diagnóstica previa a la selección definitiva.",
               "Reducción_y = p - |S_y|","Transición a selección de características.","Depende del umbral y del subconjunto VIF.",stage="Diagnóstico de multicolinealidad")



# -----------------------------------------------------------------------------
# 63-74. Selección de características y construcción del dataset reducido
# -----------------------------------------------------------------------------
SELECTION_TARGET_LABELS = {
    "target_ventas_importe_real_2026_05": "Importe de ventas",
    "target_compras_total_real_2026_05": "Importe de compras",
    "target_ventas_registros": "Registros de ventas",
    "target_compras_registros": "Registros de compras",
}

SELECTION_METHOD_LABELS = {
    "correlacion_abs": "Correlación absoluta",
    "informacion_mutua": "Información mutua",
    "random_forest": "Random Forest",
    "lasso_abs_coef": "Lasso |coeficiente|",
}


def selection_path(ctx: Context) -> Path:
    candidates = []
    if ctx.analysis_dir is not None:
        candidates.append(ctx.analysis_dir / "03_dataset_reducido_por_seleccion.xlsx")
    candidates.extend([
        ctx.input_dir / "03_dataset_reducido_por_seleccion.xlsx",
        ctx.input_dir.parent / "output" / "analisis_dimensional" / "03_dataset_reducido_por_seleccion.xlsx",
    ])
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("No se encontró 03_dataset_reducido_por_seleccion.xlsx en analysis-dir, input-dir ni output/analisis_dimensional.")


def load_selection(ctx: Context, sheet: str) -> pd.DataFrame:
    path = selection_path(ctx)
    with pd.ExcelFile(path) as xls:
        if sheet not in xls.sheet_names:
            raise ValueError(f"{path.name} no contiene la hoja '{sheet}'. Hojas: {xls.sheet_names}")
    return pd.read_excel(path, sheet_name=sheet)


def selection_target_label(value: str) -> str:
    return SELECTION_TARGET_LABELS.get(str(value), str(value).replace("target_", "").replace("_", " ").title())


def selection_method_label(value: str) -> str:
    return SELECTION_METHOD_LABELS.get(str(value), str(value).replace("_", " ").title())


def graph_selection_reduction_summary(ctx: Context) -> GraphicRecord:
    summary = load_selection(ctx, "resumen")
    values = dict(zip(summary["metrica"].astype(str), pd.to_numeric(summary["valor"], errors="coerce")))
    original = int(values.get("variables_originales", 0)); reduced = int(values.get("variables_reducidas", 0))
    removed = max(0, original - reduced); reduction = removed / original * 100 if original else 0
    series = pd.Series({"Predictores originales": original, "Predictores seleccionados": reduced, "Predictores eliminados": removed})
    fig, ax = plt.subplots(figsize=(9.5, 6.3)); ax.bar(series.index, series.values)
    ax.set_title("Resultado global de la selección de características"); ax.set_ylabel("Número de predictores")
    ax.tick_params(axis="x", rotation=12); ax.grid(axis="y", alpha=.22)
    for i, v in enumerate(series.values): ax.text(i, v, f"{int(v)}", ha="center", va="bottom")
    ax.text(.98, .92, f"Reducción = {reduction:.2f}%", transform=ax.transAxes, ha="right", bbox=dict(boxstyle="round", alpha=.12))
    fig.tight_layout(); filename="63_resultado_global_seleccion_caracteristicas.png"; save(fig, ctx, filename)
    return rec(63, "Resultado global de la selección", filename, "03_dataset_reducido_por_seleccion.xlsx", "resumen",
               "variables_originales, variables_reducidas, objetivos", "Cuantificar la magnitud real de la reducción obtenida.",
               f"Se conservaron {reduced} de {original} predictores y se eliminaron {removed}, equivalente a {reduction:.2f}%.",
               "Una reducción pequeña indica que el criterio de unión entre objetivos fue permisivo.",
               r"Reducción(\%)=\frac{p_{original}-p_{reducido}}{p_{original}}\times100",
               "Apertura de la sección de selección de características.",
               "La cantidad de variables no demuestra por sí misma mejora predictiva.", stage="Selección de características")


def graph_selection_counts_by_target(ctx: Context) -> GraphicRecord:
    ranking = load_selection(ctx, "ranking_variables").copy(); ranking["seleccionada"] = ranking["seleccionada"].astype(bool)
    out = ranking.groupby("target")["seleccionada"].agg(seleccionadas="sum", total="size").reset_index()
    out["no_seleccionadas"] = out["total"] - out["seleccionadas"]
    x=np.arange(len(out)); w=.38; fig,ax=plt.subplots(figsize=(11,6.5))
    ax.bar(x-w/2,out.seleccionadas,w,label="Seleccionadas"); ax.bar(x+w/2,out.no_seleccionadas,w,label="No seleccionadas")
    ax.set_xticks(x,wrap([selection_target_label(v) for v in out.target],20)); ax.set_ylabel("Número de variables")
    ax.set_title("Selección de características específica por objetivo"); ax.legend(); ax.grid(axis="y",alpha=.22)
    fig.tight_layout(); filename="64_variables_seleccionadas_por_objetivo.png"; save(fig,ctx,filename)
    return rec(64,"Variables seleccionadas por objetivo",filename,"03_dataset_reducido_por_seleccion.xlsx","ranking_variables",
               "target, seleccionada","Comparar la amplitud del subconjunto relevante para cada problema predictivo.",
               "Cada objetivo puede seleccionar una combinación diferente de predictores.",
               "Las barras distinguen la decisión binaria producida por el ranking compuesto.",
               r"I_{j,y}=I(rank_{j,y}\leq K\;\lor\;score_{j,y}\geq\tau)",
               "Justificación de selección específica por objetivo.",
               "La unión final puede ser mucho mayor que cada subconjunto individual.",stage="Selección de características")


def graph_selection_score_distribution(ctx: Context) -> GraphicRecord:
    df=load_selection(ctx,"ranking_variables").copy(); df["score_compuesto"]=pd.to_numeric(df.score_compuesto,errors="coerce")
    df["seleccionada"]=df.seleccionada.astype(bool)
    groups=[df.loc[~df.seleccionada,"score_compuesto"].dropna().values,df.loc[df.seleccionada,"score_compuesto"].dropna().values]
    fig,ax=plt.subplots(figsize=(9.5,6.5)); ax.boxplot(groups,labels=["No seleccionadas","Seleccionadas"],showfliers=False)
    ax.set_title("Distribución del score compuesto según decisión de selección"); ax.set_ylabel("Score compuesto normalizado")
    ax.grid(axis="y",alpha=.22); fig.tight_layout(); filename="65_distribucion_score_compuesto_seleccion.png"; save(fig,ctx,filename)
    med_sel=float(np.nanmedian(groups[1])) if len(groups[1]) else float('nan')
    return rec(65,"Distribución del score compuesto",filename,"03_dataset_reducido_por_seleccion.xlsx","ranking_variables",
               "score_compuesto, seleccionada","Mostrar la separación entre variables retenidas y descartadas.",
               f"La mediana del score de las seleccionadas es {med_sel:.3f}.",
               "Una superposición amplia indica que parte de la selección depende del criterio Top-K y no solo de un umbral absoluto.",
               r"Score_{j,y}=\frac{1}{M}\sum_{m=1}^{M}Score^{norm}_{j,y,m}",
               "Explicación de la función de decisión multicriterio.",
               "Los scores normalizados son relativos dentro de cada objetivo y método.",stage="Selección de características")


def graph_selection_top_features_per_target(ctx: Context) -> GraphicRecord:
    df=load_selection(ctx,"ranking_variables").copy(); df["score_compuesto"]=pd.to_numeric(df.score_compuesto,errors="coerce")
    targets=list(df.target.dropna().unique()); fig,axes=plt.subplots(len(targets),1,figsize=(12,3.8*len(targets)))
    axes=np.atleast_1d(axes)
    for ax,target in zip(axes,targets):
        top=df[df.target==target].nlargest(min(ctx.top_n,12),"score_compuesto").sort_values("score_compuesto")
        ax.barh(wrap(top.variable,42),top.score_compuesto); ax.set_title(selection_target_label(target)); ax.set_xlabel("Score compuesto")
        ax.grid(axis="x",alpha=.22)
    fig.suptitle("Características con mayor evidencia combinada por objetivo",y=.995); fig.tight_layout()
    filename="66_top_caracteristicas_score_compuesto.png"; save(fig,ctx,filename)
    return rec(66,"Top de características por objetivo",filename,"03_dataset_reducido_por_seleccion.xlsx","ranking_variables",
               "target, variable, score_compuesto","Identificar los predictores con mayor respaldo combinado para cada objetivo.",
               "Las variables superiores no necesariamente coinciden entre ventas, compras e indicadores operativos.",
               "El score sintetiza evidencia lineal, no lineal, de ensamble y regularización.",
               r"Score_{comp}=media(\rho,MI,RF,|\beta_{Lasso}|)_{normalizados}",
               "Resultados de selección por objetivo.",
               "El ranking no expresa causalidad ni garantiza estabilidad temporal.",stage="Selección de características")


def graph_selection_method_heatmap(ctx: Context) -> GraphicRecord:
    scores=load_selection(ctx,"scores_metodos").copy(); scores["score_norm"]=pd.to_numeric(scores.score_norm,errors="coerce")
    mean=scores.groupby(["variable","metodo"],as_index=False).score_norm.mean()
    importance=mean.groupby("variable").score_norm.mean().nlargest(min(ctx.top_n,18)).index
    pivot=mean[mean.variable.isin(importance)].pivot(index="variable",columns="metodo",values="score_norm").fillna(0)
    pivot=pivot.loc[importance]
    fig,ax=plt.subplots(figsize=(10.5,max(6,0.38*len(pivot)+2))); im=ax.imshow(pivot.values,aspect="auto",vmin=0,vmax=1)
    ax.set_yticks(np.arange(len(pivot)),wrap(pivot.index,38)); ax.set_xticks(np.arange(len(pivot.columns)),wrap([selection_method_label(c) for c in pivot.columns],18),rotation=20,ha="right")
    ax.set_title("Acuerdo y contraste de los métodos de importancia"); fig.colorbar(im,ax=ax,label="Score normalizado medio")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]): ax.text(j,i,f"{pivot.iloc[i,j]:.2f}",ha="center",va="center",fontsize=7)
    fig.tight_layout(); filename="67_matriz_scores_metodos_top_variables.png"; save(fig,ctx,filename)
    return rec(67,"Matriz de scores por método",filename,"03_dataset_reducido_por_seleccion.xlsx","scores_metodos",
               "variable, metodo, score_norm","Comparar cómo valoran los cuatro métodos a las variables más destacadas.",
               "Filas uniformemente altas muestran consenso; perfiles contrastantes revelan relaciones capturadas solo por ciertos métodos.",
               "La intensidad se interpreta dentro de la normalización de cada método y objetivo.",
               r"s^{norm}=\frac{s-\min(s)}{\max(s)-\min(s)}",
               "Comparación metodológica de criterios de importancia.",
               "Promediar objetivos puede ocultar relevancia específica.",stage="Selección de características")


def graph_selection_method_agreement(ctx: Context) -> GraphicRecord:
    scores=load_selection(ctx,"scores_metodos").copy(); scores["score_norm"]=pd.to_numeric(scores.score_norm,errors="coerce")
    pivot=scores.pivot_table(index=["target","variable"],columns="metodo",values="score_norm",aggfunc="mean")
    corr=pivot.corr(method="spearman")
    fig,ax=plt.subplots(figsize=(8,7)); im=ax.imshow(corr.values,vmin=-1,vmax=1)
    labels=[selection_method_label(c) for c in corr.columns]; ax.set_xticks(np.arange(len(labels)),wrap(labels,18),rotation=25,ha="right"); ax.set_yticks(np.arange(len(labels)),wrap(labels,18))
    ax.set_title("Concordancia entre métodos de selección (Spearman)"); fig.colorbar(im,ax=ax,label="Correlación de rangos")
    for i in range(len(labels)):
        for j in range(len(labels)): ax.text(j,i,f"{corr.iloc[i,j]:.2f}",ha="center",va="center")
    fig.tight_layout(); filename="68_concordancia_metodos_seleccion.png"; save(fig,ctx,filename)
    return rec(68,"Concordancia entre métodos",filename,"03_dataset_reducido_por_seleccion.xlsx","scores_metodos",
               "metodo, score_norm","Medir si los métodos ordenan las variables de manera semejante.",
               "Correlaciones altas indican consenso de ranking; valores bajos evidencian complementariedad metodológica.",
               "Se emplea Spearman porque interesa el orden relativo y no la escala original.",
               r"\rho_s=Corr(rank(s_m),rank(s_{m'}))",
               "Rigor de la combinación multicriterio.",
               "La concordancia puede variar entre objetivos aunque aquí se resume conjuntamente.",stage="Selección de características")


def graph_selection_dimensions_by_target(ctx: Context) -> GraphicRecord:
    df=load_selection(ctx,"ranking_variables").copy(); df=df[df.seleccionada.astype(bool)]
    pivot=df.pivot_table(index="dimension",columns="target",values="variable",aggfunc="count",fill_value=0)
    fig,ax=plt.subplots(figsize=(12,8)); im=ax.imshow(pivot.values,aspect="auto")
    ax.set_yticks(np.arange(len(pivot)),wrap(pivot.index,28)); ax.set_xticks(np.arange(len(pivot.columns)),wrap([selection_target_label(c) for c in pivot.columns],18),rotation=20,ha="right")
    ax.set_title("Cobertura dimensional de las variables seleccionadas"); fig.colorbar(im,ax=ax,label="Número de variables")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]): ax.text(j,i,str(int(pivot.iloc[i,j])),ha="center",va="center",fontsize=8)
    fig.tight_layout(); filename="69_dimensiones_seleccionadas_por_objetivo.png"; save(fig,ctx,filename)
    return rec(69,"Dimensiones seleccionadas por objetivo",filename,"03_dataset_reducido_por_seleccion.xlsx","ranking_variables",
               "dimension, target, seleccionada","Verificar que la selección conserve diversidad conceptual.",
               "La matriz muestra qué dimensiones aportan más variables a cada objetivo.",
               "Una dimensión con pocas variables puede seguir siendo estratégicamente relevante.",
               r"n_{g,y}=|\{X_j:d_j=g\land I_{j,y}=1\}|",
               "Análisis de interpretabilidad del dataset reducido.",
               "Los conteos no equivalen a contribución predictiva acumulada.",stage="Selección de características")


def graph_selection_overlap_targets(ctx: Context) -> GraphicRecord:
    df=load_selection(ctx,"ranking_variables"); selected=df[df.seleccionada.astype(bool)]
    freq=selected.groupby("variable").target.nunique(); dist=freq.value_counts().sort_index()
    fig,ax=plt.subplots(figsize=(9.5,6.3)); ax.bar(dist.index.astype(str),dist.values)
    ax.set_title("Estabilidad de selección entre los cuatro objetivos"); ax.set_xlabel("Número de objetivos que seleccionan la variable")
    ax.set_ylabel("Número de variables"); ax.grid(axis="y",alpha=.22)
    for i,v in enumerate(dist.values): ax.text(i,v,f"{int(v)}",ha="center",va="bottom")
    fig.tight_layout(); filename="70_solapamiento_seleccion_entre_objetivos.png"; save(fig,ctx,filename)
    common=int((freq==selected.target.nunique()).sum())
    return rec(70,"Solapamiento de selección entre objetivos",filename,"03_dataset_reducido_por_seleccion.xlsx","ranking_variables",
               "variable, target, seleccionada","Distinguir predictores globales de predictores específicos.",
               f"{common} variables fueron seleccionadas por los cuatro objetivos.",
               "Una frecuencia alta sugiere utilidad transversal; una frecuencia de uno indica especialización.",
               r"f_j=\sum_y I_{j,y}",
               "Definición del conjunto unido de predictores.",
               "La estabilidad entre objetivos no equivale a estabilidad temporal.",stage="Selección de características")


def graph_selection_rank_curves(ctx: Context) -> GraphicRecord:
    df=load_selection(ctx,"ranking_variables").copy(); df["rank_target"]=pd.to_numeric(df.rank_target,errors="coerce"); df["score_compuesto"]=pd.to_numeric(df.score_compuesto,errors="coerce")
    fig,ax=plt.subplots(figsize=(11.5,6.7))
    for target,g in df.sort_values("rank_target").groupby("target"):
        ax.plot(g.rank_target,g.score_compuesto,label=selection_target_label(target),linewidth=1.5)
    ax.axvline(40,linestyle="--",label="Referencia Top 40"); ax.set_xlim(1,min(150,float(df.rank_target.max())))
    ax.set_title("Curvas de decaimiento del score compuesto por posición"); ax.set_xlabel("Posición en el ranking"); ax.set_ylabel("Score compuesto")
    ax.grid(alpha=.22); ax.legend(fontsize=8); fig.tight_layout(); filename="71_curvas_score_por_ranking.png"; save(fig,ctx,filename)
    return rec(71,"Curvas de score por ranking",filename,"03_dataset_reducido_por_seleccion.xlsx","ranking_variables",
               "rank_target, score_compuesto, target","Visualizar qué tan rápido disminuye la evidencia al avanzar en el ranking.",
               "Una caída pronunciada sugiere una frontera natural; una curva plana indica dificultad para fijar un corte.",
               "La línea vertical representa el criterio Top-K configurado.",
               r"rank_{j,y}=orden\ descendente(Score_{j,y})",
               "Justificación gráfica del número de variables retenidas.",
               "El corte final también depende del umbral de score.",stage="Selección de características")


def graph_selection_lasso_sparsity(ctx: Context) -> GraphicRecord:
    scores=load_selection(ctx,"scores_metodos").copy(); lasso=scores[scores.metodo=="lasso_abs_coef"].copy()
    lasso["score"]=pd.to_numeric(lasso.score,errors="coerce").fillna(0)
    out=lasso.groupby("target").score.agg(total="size",no_cero=lambda s:int((s>1e-12).sum())).reset_index(); out["cero"]=out.total-out.no_cero
    x=np.arange(len(out)); fig,ax=plt.subplots(figsize=(11,6.5)); ax.bar(x,out.no_cero,label="Coeficiente no cero"); ax.bar(x,out.cero,bottom=out.no_cero,label="Coeficiente cero")
    ax.set_xticks(x,wrap([selection_target_label(v) for v in out.target],20)); ax.set_ylabel("Número de predictores"); ax.set_title("Contracción y esparsidad producida por LassoCV")
    ax.legend(); ax.grid(axis="y",alpha=.22); fig.tight_layout(); filename="72_esparsidad_coeficientes_lasso.png"; save(fig,ctx,filename)
    return rec(72,"Esparsidad de LassoCV",filename,"03_dataset_reducido_por_seleccion.xlsx","scores_metodos",
               "target, metodo, score","Mostrar cuántos coeficientes son contraídos exactamente a cero.",
               "Una mayor proporción de ceros representa una selección más parsimoniosa dentro del modelo lineal regularizado.",
               "Lasso reduce coeficientes mediante penalización L1.",
               r"\hat\beta=\arg\min_\beta\{RSS+\lambda\sum_j|\beta_j|\}",
               "Regularización y parsimonia metodológica.",
               "Lasso puede elegir arbitrariamente entre predictores altamente correlacionados.",stage="Selección de características")


def graph_selection_method_winners(ctx: Context) -> GraphicRecord:
    scores=load_selection(ctx,"scores_metodos").copy(); scores["score_norm"]=pd.to_numeric(scores.score_norm,errors="coerce")
    idx=scores.groupby(["target","variable"]).score_norm.idxmax(); winners=scores.loc[idx,"metodo"].map(selection_method_label).value_counts().sort_values()
    fig,ax=plt.subplots(figsize=(9.5,6.2)); ax.barh(winners.index,winners.values); ax.set_title("Método que aporta el mayor score por variable y objetivo")
    ax.set_xlabel("Número de combinaciones variable-objetivo"); ax.grid(axis="x",alpha=.22)
    for i,v in enumerate(winners.values): ax.text(v,i,f" {int(v)}",va="center")
    fig.tight_layout(); filename="73_metodo_dominante_por_variable_objetivo.png"; save(fig,ctx,filename)
    return rec(73,"Método dominante por variable-objetivo",filename,"03_dataset_reducido_por_seleccion.xlsx","scores_metodos",
               "target, variable, metodo, score_norm","Mostrar qué criterio aporta con mayor frecuencia la evidencia principal.",
               "La distribución revela si la selección está dominada por relaciones lineales, no lineales, ensambles o regularización.",
               "Se asigna como dominante el método con score normalizado máximo en cada combinación.",
               r"m^*_{j,y}=\arg\max_m s^{norm}_{j,y,m}",
               "Discusión de complementariedad entre métodos.",
               "El máximo no refleja la magnitud de la diferencia frente al segundo método.",stage="Selección de características")


def graph_selection_dataset_comparison(ctx: Context) -> GraphicRecord:
    ranking=load_selection(ctx,"ranking_variables").copy(); ranking["seleccionada"]=ranking.seleccionada.astype(bool)
    original=ranking.groupby("dimension").variable.nunique().rename("originales")
    selected=ranking[ranking.seleccionada].groupby("dimension").variable.nunique().rename("seleccionadas")
    out=pd.concat([original,selected],axis=1).fillna(0).sort_values("originales",ascending=True)
    fig,ax=plt.subplots(figsize=(12,7.5)); y=np.arange(len(out)); h=.38
    ax.barh(y-h/2,out.originales,h,label="Originales"); ax.barh(y+h/2,out.seleccionadas,h,label="Seleccionadas")
    ax.set_yticks(y,wrap(out.index,30)); ax.set_xlabel("Número de variables únicas"); ax.set_title("Cobertura dimensional antes y después de la selección")
    ax.legend(); ax.grid(axis="x",alpha=.22); fig.tight_layout(); filename="74_comparacion_dataset_completo_reducido.png"; save(fig,ctx,filename)
    p_full=int(ranking.variable.nunique()); p_red=int(ranking.loc[ranking.seleccionada,"variable"].nunique())
    return rec(74,"Comparación del dataset completo y reducido",filename,"03_dataset_reducido_por_seleccion.xlsx","ranking_variables",
               "dimension, variable, seleccionada","Evaluar cómo cambia la cobertura de dimensiones al construir el dataset reducido.",
               f"El universo contiene {p_full} predictores y la unión seleccionada conserva {p_red}.",
               "Barras similares evidencian una reducción conservadora; diferencias amplias señalan dimensiones depuradas.",
               r"p^{sel}_g=|\{X_j:d_j=g\land\max_y I_{j,y}=1\}|",
               "Cierre de selección y transición a PCA/modelado.",
               "El conteo dimensional no mide la información predictiva retenida.",stage="Selección de características")



# -----------------------------------------------------------------------------
# 75-86. Reducción dimensional mediante PCA: evidencia académica de 06_pca_reduccion_componentes.py
# -----------------------------------------------------------------------------
def pca_path(ctx: Context) -> Path:
    candidates = []
    if ctx.analysis_dir is not None:
        candidates.append(ctx.analysis_dir / "04_dataset_pca_componentes.xlsx")
    candidates.extend([
        ctx.input_dir / "04_dataset_pca_componentes.xlsx",
        ctx.input_dir.parent / "output" / "analisis_dimensional" / "04_dataset_pca_componentes.xlsx",
    ])
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("No se encontró 04_dataset_pca_componentes.xlsx en analysis-dir, input-dir ni output/analisis_dimensional")


def load_pca(ctx: Context, sheet: str) -> pd.DataFrame:
    path = pca_path(ctx)
    with pd.ExcelFile(path) as xls:
        if sheet not in xls.sheet_names:
            raise ValueError(f"{path.name} no contiene la hoja '{sheet}'. Hojas: {xls.sheet_names}")
    return pd.read_excel(path, sheet_name=sheet)


def graph_pca_reduction_summary(ctx: Context) -> GraphicRecord:
    loadings = load_pca(ctx, "cargas_componentes")
    pca = load_pca(ctx, "dataset_pca")
    original = len(loadings)
    components = len([c for c in pca.columns if str(c).startswith("pca_")])
    reduction = original - components
    values = pd.Series({"Predictores originales": original, "Componentes PCA": components, "Dimensiones eliminadas": reduction})
    fig, ax = plt.subplots(figsize=(9.5, 6.3))
    ax.bar(values.index, values.values)
    ax.set_title("Reducción dimensional obtenida mediante PCA")
    ax.set_ylabel("Número de dimensiones")
    ax.tick_params(axis="x", rotation=12)
    ax.grid(axis="y", alpha=.22)
    for i, v in enumerate(values.values): ax.text(i, v, f"{int(v)}", ha="center", va="bottom")
    fig.tight_layout(); filename="75_reduccion_dimensional_pca.png"; save(fig, ctx, filename)
    pct = reduction / original * 100 if original else 0
    return rec(75,"Reducción dimensional mediante PCA",filename,"dataset_modelado_diario.xlsx y 04_dataset_pca_componentes.xlsx","modelo / dataset_pca",
               "número de predictores y componentes","Cuantificar la compresión lograda conservando el umbral de varianza establecido.",
               f"PCA transformó {original} predictores en {components} componentes, una reducción de {pct:.1f}%.",
               "La reducción cuenta dimensiones; no implica una pérdida equivalente de información porque los componentes concentran varianza compartida.",
               r"Reducción(\%)=\frac{p-k}{p}\times100",
               "Apertura de la sección de reducción por componentes principales.",
               "El número de componentes depende del escalamiento, del conjunto de entrenamiento y del umbral de varianza.",stage="PCA")


def graph_pca_scree(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"varianza_explicada").copy(); df["varianza_explicada"]=pd.to_numeric(df.varianza_explicada,errors="coerce")
    x=np.arange(1,len(df)+1)
    fig,ax=plt.subplots(figsize=(12,6.5)); ax.plot(x,df.varianza_explicada*100,marker="o",markersize=2.5,linewidth=1)
    ax.set_title("Gráfico de sedimentación (Scree Plot) de los componentes principales")
    ax.set_xlabel("Número de componente"); ax.set_ylabel("Varianza explicada individual (%)"); ax.grid(alpha=.22)
    fig.tight_layout(); filename="76_scree_plot_pca.png"; save(fig,ctx,filename)
    return rec(76,"Scree Plot",filename,"04_dataset_pca_componentes.xlsx","varianza_explicada","componente, varianza_explicada",
               "Mostrar cómo disminuye la contribución marginal de cada componente.",
               "La pendiente pronunciada inicial identifica componentes informativos; la zona plana refleja rendimientos decrecientes.",
               "El punto de codo puede orientar una solución más parsimoniosa, aunque el código utiliza un criterio acumulado de 95%.",
               r"EVR_j=\frac{\lambda_j}{\sum_{h=1}^{p}\lambda_h}",
               "Justificación visual del número de componentes.",
               "El codo es parcialmente subjetivo y no sustituye la validación predictiva.",stage="PCA")


def graph_pca_cumulative_variance(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"varianza_explicada").copy(); df["varianza_acumulada"]=pd.to_numeric(df.varianza_acumulada,errors="coerce")
    x=np.arange(1,len(df)+1); threshold=.95
    reached=np.where(df.varianza_acumulada.to_numpy()>=threshold)[0]; k=int(reached[0]+1) if len(reached) else len(df)
    fig,ax=plt.subplots(figsize=(12,6.5)); ax.plot(x,df.varianza_acumulada*100,linewidth=1.8)
    ax.axhline(95,linestyle="--",label="Umbral 95%"); ax.axvline(k,linestyle=":",label=f"{k} componentes")
    ax.scatter([k],[df.varianza_acumulada.iloc[k-1]*100],s=55); ax.set_ylim(0,101)
    ax.set_title("Varianza explicada acumulada y criterio de retención")
    ax.set_xlabel("Número de componentes"); ax.set_ylabel("Varianza acumulada (%)"); ax.grid(alpha=.22); ax.legend()
    fig.tight_layout(); filename="77_varianza_acumulada_pca.png"; save(fig,ctx,filename)
    return rec(77,"Varianza acumulada y umbral de retención",filename,"04_dataset_pca_componentes.xlsx","varianza_explicada",
               "componente, varianza_acumulada","Demostrar el punto exacto en que se alcanza la proporción de información definida.",
               f"El umbral de 95% se alcanza con {k} componentes.",
               "La curva suma la contribución ordenada de los componentes; el cruce con 95% define la dimensión final.",
               r"VEA_k=\sum_{j=1}^{k}EVR_j\geq0.95",
               "Fundamento cuantitativo de la retención de componentes.",
               "Conservar varianza no garantiza conservar toda la información relevante para cada objetivo.",stage="PCA")


def graph_pca_marginal_contribution(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"varianza_explicada").copy(); vals=pd.to_numeric(df.varianza_explicada,errors="coerce").fillna(0)*100
    top=min(ctx.top_n,len(vals)); shown=vals.iloc[:top]
    fig,ax=plt.subplots(figsize=(11,6.5)); ax.bar(np.arange(1,top+1),shown.values)
    ax.set_title(f"Contribución individual de los primeros {top} componentes")
    ax.set_xlabel("Componente"); ax.set_ylabel("Varianza explicada (%)"); ax.grid(axis="y",alpha=.22)
    fig.tight_layout(); filename="78_contribucion_primeros_componentes.png"; save(fig,ctx,filename)
    share=shown.sum()
    return rec(78,"Contribución de los primeros componentes",filename,"04_dataset_pca_componentes.xlsx","varianza_explicada",
               "varianza_explicada","Comparar la concentración de información en la parte inicial de la solución PCA.",
               f"Los primeros {top} componentes concentran {share:.1f}% de la varianza total.",
               "Barras altas representan ejes latentes que resumen una mayor proporción de variabilidad original.",
               r"VE_{1:q}=\sum_{j=1}^{q}EVR_j",
               "Discusión de concentración y rendimientos decrecientes.",
               "Una alta varianza explicada no equivale necesariamente a mayor relación con las variables objetivo.",stage="PCA")


def graph_pca_variance_milestones(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"varianza_explicada").copy(); cum=pd.to_numeric(df.varianza_acumulada,errors="coerce").to_numpy()
    thresholds=[.50,.70,.80,.90,.95]; counts=[]
    for t in thresholds:
        idx=np.where(cum>=t)[0]; counts.append(int(idx[0]+1) if len(idx) else len(cum))
    fig,ax=plt.subplots(figsize=(9.5,6.3)); labels=[f"{int(t*100)}%" for t in thresholds]; ax.bar(labels,counts)
    ax.set_title("Componentes requeridos para distintos niveles de varianza acumulada")
    ax.set_xlabel("Varianza objetivo"); ax.set_ylabel("Número de componentes"); ax.grid(axis="y",alpha=.22)
    for i,v in enumerate(counts): ax.text(i,v,f"{v}",ha="center",va="bottom")
    fig.tight_layout(); filename="79_componentes_por_umbral_varianza.png"; save(fig,ctx,filename)
    return rec(79,"Componentes requeridos por umbral",filename,"04_dataset_pca_componentes.xlsx","varianza_explicada",
               "varianza_acumulada","Mostrar la relación de compromiso entre compacidad y conservación de varianza.",
               "Cada barra indica la dimensión mínima necesaria para alcanzar un nivel acumulado específico.",
               "Umbrales más altos conservan más variabilidad, pero reducen menos la dimensionalidad.",
               r"k_\alpha=\min\{k:VEA_k\geq\alpha\}",
               "Análisis de sensibilidad del umbral de 95%.",
               "La elección final debe contrastarse con desempeño fuera de muestra e interpretabilidad.",stage="PCA")


def graph_pca_loadings_heatmap(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"cargas_componentes").copy(); pcs=[c for c in df.columns if str(c).startswith("pca_")][:6]
    if not pcs: raise ValueError("No se encontraron columnas pca_ en cargas_componentes")
    vals=df[pcs].apply(pd.to_numeric,errors="coerce").fillna(0)
    importance=vals.abs().max(axis=1); top_idx=importance.nlargest(min(ctx.top_n,len(df))).index
    mat=vals.loc[top_idx]; labels=df.loc[top_idx,"variable"].astype(str)
    fig,ax=plt.subplots(figsize=(11,8)); im=ax.imshow(mat.values,aspect="auto",vmin=-float(mat.abs().max().max()),vmax=float(mat.abs().max().max()))
    ax.set_xticks(np.arange(len(pcs)),pcs); ax.set_yticks(np.arange(len(mat)),wrap(labels,34)); ax.set_title("Mapa de cargas de las variables más influyentes en los primeros componentes")
    fig.colorbar(im,ax=ax,label="Carga factorial"); fig.tight_layout(); filename="80_mapa_cargas_primeros_componentes.png"; save(fig,ctx,filename)
    return rec(80,"Mapa de cargas de los primeros componentes",filename,"04_dataset_pca_componentes.xlsx","cargas_componentes",
               "variable y cargas pca_01 a pca_06","Interpretar qué variables originales definen los ejes latentes iniciales.",
               "Valores absolutos altos indican contribución fuerte; el signo representa dirección dentro del eje y puede invertirse sin cambiar la solución.",
               "Patrones semejantes por filas permiten reconocer familias de variables que participan conjuntamente.",
               r"PC_j=\sum_{i=1}^{p}w_{ij}Z_i",
               "Interpretación sustantiva de componentes principales.",
               "Las cargas no son coeficientes causales y su signo es arbitrario.",stage="PCA")


def graph_pca_pc1_loadings(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"cargas_componentes").copy(); col="pca_01"; df[col]=pd.to_numeric(df[col],errors="coerce")
    top=df.assign(abs_carga=df[col].abs()).nlargest(min(ctx.top_n,len(df)),"abs_carga").sort_values(col)
    fig,ax=plt.subplots(figsize=(12,7)); ax.barh(wrap(top.variable,38),top[col]); ax.axvline(0,linewidth=.8)
    ax.set_title("Variables con mayor carga absoluta en el primer componente principal")
    ax.set_xlabel("Carga en PCA 1"); ax.grid(axis="x",alpha=.22); fig.tight_layout(); filename="81_cargas_primer_componente.png"; save(fig,ctx,filename)
    return rec(81,"Cargas del primer componente",filename,"04_dataset_pca_componentes.xlsx","cargas_componentes",
               "variable, pca_01","Identificar el significado estadístico del eje que concentra la mayor varianza.",
               "Las variables con mayor magnitud son las que más definen PCA 1; signos opuestos representan contrastes dentro del mismo patrón.",
               "La interpretación debe centrarse en magnitudes y familias conceptuales, no solo en el signo.",
               r"PC_1=w_{11}Z_1+\cdots+w_{p1}Z_p",
               "Explicación narrativa del primer componente.",
               "Una etiqueta sustantiva del componente requiere revisar conjuntamente todas las cargas dominantes.",stage="PCA")


def graph_pca_variable_contribution(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"cargas_componentes").copy(); pcs=[c for c in df.columns if str(c).startswith("pca_")][:10]
    vals=df[pcs].apply(pd.to_numeric,errors="coerce").fillna(0)
    contribution=(vals**2).sum(axis=1); top=pd.DataFrame({"variable":df.variable,"contribucion":contribution}).nlargest(min(ctx.top_n,len(df)),"contribucion").sort_values("contribucion")
    fig,ax=plt.subplots(figsize=(12,7)); ax.barh(wrap(top.variable,38),top.contribucion); ax.set_title("Contribución acumulada de variables a los primeros diez componentes")
    ax.set_xlabel("Suma de cargas al cuadrado"); ax.grid(axis="x",alpha=.22); fig.tight_layout(); filename="82_contribucion_variables_primeros_componentes.png"; save(fig,ctx,filename)
    return rec(82,"Contribución acumulada de variables",filename,"04_dataset_pca_componentes.xlsx","cargas_componentes",
               "cargas de los primeros diez componentes","Detectar variables cuya información se distribuye de manera relevante entre varios componentes iniciales.",
               "Una barra alta indica que la variable está bien representada dentro del subespacio inicial.",
               "Se suman las cargas al cuadrado para evitar cancelación entre signos.",
               r"h_i^2(q)=\sum_{j=1}^{q}w_{ij}^2",
               "Evaluación de representación de variables originales.",
               "La medida depende del número de componentes considerado y no incorpora directamente la varianza de cada componente.",stage="PCA")


def graph_pca_component_time_series(ctx: Context) -> GraphicRecord:
    df=to_date(load_pca(ctx,"dataset_pca")); pcs=[c for c in df.columns if str(c).startswith("pca_")][:3]
    fig,ax=plt.subplots(figsize=(13,6.7))
    for c in pcs: ax.plot(df.fecha,pd.to_numeric(df[c],errors="coerce"),label=c,linewidth=.9,alpha=.8)
    style_time_axis(ax); ax.set_title("Evolución temporal de los tres primeros componentes principales")
    ax.set_xlabel("Fecha"); ax.set_ylabel("Puntuación del componente"); ax.legend(); fig.tight_layout(); filename="83_series_temporales_componentes_pca.png"; save(fig,ctx,filename)
    return rec(83,"Trayectoria temporal de componentes",filename,"04_dataset_pca_componentes.xlsx","dataset_pca",
               "fecha, pca_01, pca_02, pca_03","Examinar cambios estructurales y patrones temporales dentro del espacio reducido.",
               "Picos o cambios persistentes señalan fechas en las que múltiples variables originales se desplazaron conjuntamente.",
               "Cada serie es una combinación lineal estandarizada y no conserva unidades económicas originales.",
               r"t_{rj}=Z_r w_j",
               "Análisis temporal del dataset PCA y transición al modelado.",
               "Las puntuaciones no deben interpretarse como ventas, compras o utilidad directa.",stage="PCA")


def graph_pca_score_plane(ctx: Context) -> GraphicRecord:
    df=to_date(load_pca(ctx,"dataset_pca")); required=["pca_01","pca_02"]
    for c in required: df[c]=pd.to_numeric(df[c],errors="coerce")
    order=np.arange(len(df)); fig,ax=plt.subplots(figsize=(9,7.5)); sc=ax.scatter(df.pca_01,df.pca_02,c=order,s=14,alpha=.65)
    ax.axhline(0,linewidth=.7); ax.axvline(0,linewidth=.7); ax.set_title("Plano factorial de observaciones: PCA 1 frente a PCA 2")
    ax.set_xlabel("PCA 1"); ax.set_ylabel("PCA 2"); ax.grid(alpha=.18); fig.colorbar(sc,ax=ax,label="Orden temporal de la observación")
    fig.tight_layout(); filename="84_plano_factorial_pca1_pca2.png"; save(fig,ctx,filename)
    return rec(84,"Plano factorial PCA 1-PCA 2",filename,"04_dataset_pca_componentes.xlsx","dataset_pca",
               "pca_01, pca_02 y orden temporal","Visualizar agrupamientos, trayectorias y observaciones atípicas en las dos direcciones principales.",
               "Puntos alejados del centro representan días con configuraciones multivariadas inusuales; el gradiente temporal permite detectar desplazamientos estructurales.",
               "La distancia en el plano aproxima similitud solo respecto a los dos primeros componentes.",
               r"d_{rs}^{(2)}=\sqrt{(t_{r1}-t_{s1})^2+(t_{r2}-t_{s2})^2}",
               "Exploración del espacio latente y detección visual de periodos atípicos.",
               "Dos componentes pueden explicar una fracción limitada de la varianza total.",stage="PCA")


def graph_pca_target_correlations(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"dataset_pca"); pcs=[c for c in df.columns if str(c).startswith("pca_")][:min(20,len([c for c in df.columns if str(c).startswith('pca_')]))]
    targets=[c for c in df.columns if str(c).startswith("target_")]
    corr=df[pcs+targets].apply(pd.to_numeric,errors="coerce").corr().loc[pcs,targets]
    fig,ax=plt.subplots(figsize=(11,8)); im=ax.imshow(corr.values,aspect="auto",vmin=-1,vmax=1)
    ax.set_yticks(np.arange(len(pcs)),pcs); ax.set_xticks(np.arange(len(targets)),wrap([human(t.replace('target_','')) for t in targets],20),rotation=20,ha="right")
    ax.set_title("Correlación de los primeros componentes con las variables objetivo"); fig.colorbar(im,ax=ax,label="Correlación de Pearson")
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]): ax.text(j,i,f"{corr.iloc[i,j]:.2f}",ha="center",va="center",fontsize=7)
    fig.tight_layout(); filename="85_correlacion_componentes_objetivos.png"; save(fig,ctx,filename)
    return rec(85,"Correlación entre componentes y objetivos",filename,"04_dataset_pca_componentes.xlsx","dataset_pca",
               "primeros componentes y cuatro objetivos","Examinar qué ejes latentes presentan asociación lineal inicial con cada problema predictivo.",
               "Componentes con correlación elevada pueden ser útiles para un objetivo, aunque PCA fue construido sin utilizar las variables objetivo.",
               "PCA maximiza varianza de predictores y no relevancia supervisada.",
               r"r_{PC_j,y}=Corr(t_j,y)",
               "Puente entre reducción no supervisada y evaluación predictiva.",
               "Una correlación baja no descarta relaciones no lineales o interacciones entre componentes.",stage="PCA")


def graph_pca_component_correlation(ctx: Context) -> GraphicRecord:
    df=load_pca(ctx,"dataset_pca"); pcs=[c for c in df.columns if str(c).startswith("pca_")][:min(15,len([c for c in df.columns if str(c).startswith('pca_')]))]
    corr=df[pcs].apply(pd.to_numeric,errors="coerce").corr()
    fig,ax=plt.subplots(figsize=(9,8)); im=ax.imshow(corr.values,vmin=-1,vmax=1)
    ax.set_xticks(np.arange(len(pcs)),pcs,rotation=45,ha="right"); ax.set_yticks(np.arange(len(pcs)),pcs)
    ax.set_title("Ortogonalidad empírica de los primeros componentes"); fig.colorbar(im,ax=ax,label="Correlación")
    fig.tight_layout(); filename="86_ortogonalidad_componentes_pca.png"; save(fig,ctx,filename)
    off=corr.to_numpy().copy(); np.fill_diagonal(off,np.nan); max_abs=float(np.nanmax(np.abs(off)))
    return rec(86,"Ortogonalidad de componentes",filename,"04_dataset_pca_componentes.xlsx","dataset_pca",
               "primeros quince componentes","Verificar que los componentes resultantes sean linealmente no correlacionados.",
               f"La mayor correlación absoluta fuera de la diagonal es {max_abs:.4f}; valores próximos a cero evidencian ortogonalidad numérica.",
               "La diagonal vale uno y las celdas externas deberían aproximarse a cero.",
               r"Cov(PC_j,PC_k)=0\quad j\neq k",
               "Cierre del PCA y justificación de su utilidad frente a multicolinealidad.",
               "La ortogonalidad se refiere a relaciones lineales; no implica independencia estadística completa.",stage="PCA")


PCA_GRAPH_FUNCTIONS: list[Callable[[Context], GraphicRecord]] = [
    graph_pca_reduction_summary,
    graph_pca_scree,
    graph_pca_cumulative_variance,
    graph_pca_marginal_contribution,
    graph_pca_variance_milestones,
    graph_pca_loadings_heatmap,
    graph_pca_pc1_loadings,
    graph_pca_variable_contribution,
    graph_pca_component_time_series,
    graph_pca_score_plane,
    graph_pca_target_correlations,
    graph_pca_component_correlation,
]

SELECTION_GRAPH_FUNCTIONS: list[Callable[[Context], GraphicRecord]] = [
    graph_selection_reduction_summary,
    graph_selection_counts_by_target,
    graph_selection_score_distribution,
    graph_selection_top_features_per_target,
    graph_selection_method_heatmap,
    graph_selection_method_agreement,
    graph_selection_dimensions_by_target,
    graph_selection_overlap_targets,
    graph_selection_rank_curves,
    graph_selection_lasso_sparsity,
    graph_selection_method_winners,
    graph_selection_dataset_comparison,
]

MULTICOL_GRAPH_FUNCTIONS: list[Callable[[Context], GraphicRecord]] = [
    graph_multicol_correlation_distribution, graph_multicol_top_pairs,
    graph_multicol_redundancy_network, graph_multicol_variable_frequency,
    graph_multicol_decisions_by_target, graph_multicol_kept_dimensions,
    graph_multicol_keep_drop_scatter, graph_multicol_relevance_gain,
    graph_multicol_vif_ranking, graph_multicol_vif_categories,
    graph_multicol_elimination_overlap, graph_multicol_summary,
]

PROFILE_GRAPH_FUNCTIONS: list[Callable[[Context], GraphicRecord]] = [
    graph_profile_general_structure,
    graph_profile_dimension_counts,
    graph_profile_zero_by_dimension,
    graph_profile_missing_by_dimension,
    graph_profile_constants,
    graph_profile_cardinality_zero_scatter,
    graph_profile_top_zero_variables,
    graph_profile_variability,
    graph_profile_iqr,
    graph_profile_target_boxplots,
    graph_profile_target_sparsity,
    graph_profile_dimension_quality_matrix,
]

FEATURE_GRAPH_FUNCTIONS: list[Callable[[Context], GraphicRecord]] = [
    graph_feature_family_counts,
    graph_dataset_expansion,
    graph_history_trimming,
    graph_cyclical_month_encoding,
    graph_cyclical_week_encoding,
    graph_lag_alignment,
    graph_lag_target_correlations,
    graph_rolling_windows,
    graph_rolling_statistics,
    graph_event_proximity,
    graph_event_windows,
    graph_recency_activity,
    graph_financial_derived_indicators,
    graph_target_predictor_scatter,
    graph_feature_target_heatmap,
    graph_feature_completeness,
]


GRAPH_FUNCTIONS: list[Callable[[Context], GraphicRecord]] = [
    graph_source_coverage,
    graph_inpc_series,
    graph_inflation_factor,
    graph_temperature,
    graph_climate_distribution,
    graph_events_month,
    graph_daily_sales,
    graph_monthly_nominal_real_sales,
    graph_sales_distribution,
    graph_sales_weekday_boxplot,
    graph_sales_month_heatmap,
    graph_product_mix,
    graph_sales_profit,
    graph_daily_purchases,
    graph_purchase_classification,
    graph_supplier_pareto,
    graph_purchase_units,
    graph_sales_purchases_monthly,
    graph_operating_balance,
    graph_zero_activity,
    graph_missingness,
    graph_key_correlation,
] + FEATURE_GRAPH_FUNCTIONS + PROFILE_GRAPH_FUNCTIONS + MULTICOL_GRAPH_FUNCTIONS + SELECTION_GRAPH_FUNCTIONS + PCA_GRAPH_FUNCTIONS


def write_summary_workbook(ctx: Context, records: list[GraphicRecord]) -> None:
    summaries: dict[str, pd.DataFrame] = {}
    for key in ["inpc", "temperatura", "tizayuca", "compras_detalle", "compras_diario", "ventas_detalle", "ventas_diario", "maestro"]:
        try:
            df = load(ctx, key)
            numeric_df = df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                summaries[key[:31]] = numeric_df.describe().T.reset_index().rename(columns={"index": "variable"})
        except Exception:
            continue
    try:
        for sheet_name in ["resumen_general", "resumen_dimensiones", "perfil_variables", "objetivos"]:
            summaries[f"perfil_{sheet_name}"[:31]] = load_profile(ctx, sheet_name)
    except Exception:
        pass
    try:
        with pd.ExcelFile(multicol_path(ctx)) as xls:
            for sheet_name in xls.sheet_names:
                summaries[f"multicol_{sheet_name}"[:31]] = load_multicol(ctx, sheet_name)
    except Exception:
        pass
    try:
        with pd.ExcelFile(selection_path(ctx)) as xls:
            for sheet_name in xls.sheet_names:
                summaries[f"seleccion_{sheet_name}"[:31]] = load_selection(ctx, sheet_name)
    except Exception:
        pass
    try:
        model = load_model(ctx, "modelo")
        numeric_model = model.select_dtypes(include=[np.number])
        if not numeric_model.empty:
            summaries["modelo"] = numeric_model.describe().T.reset_index().rename(columns={"index": "variable"})
        dictionary = load_model(ctx, "diccionario")
        summaries["diccionario_features"] = dictionary
    except Exception:
        pass
    try:
        with pd.ExcelFile(pca_path(ctx)) as xls:
            for sheet_name in xls.sheet_names:
                summaries[f"pca_{sheet_name}"[:31]] = pd.read_excel(pca_path(ctx), sheet_name=sheet_name)
    except Exception:
        pass
    with pd.ExcelWriter(ctx.graphics_dir / "RESUMEN_ESTADISTICO_METODOLOGIA_PCA.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([asdict(r) for r in records]).to_excel(writer, sheet_name="indice_graficas", index=False)
        for name, df in summaries.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def write_manifest(ctx: Context, records: list[GraphicRecord]) -> None:
    generated = datetime.now().astimezone().isoformat()
    payload = {
        "titulo": "Manifiesto académico de gráficas de limpieza, ingeniería de características, perfil dimensional, multicolinealidad, selección de características y PCA",
        "codigos_fuente": ["01_clean_eda.py", "02_feature_engineering_profesional.py", "03_perfil_dataset_y_dimensiones.py", "04_diagnostico_multicolinealidad.py", "05_seleccion_caracteristicas_dataset_reducido.py", "06_pca_reduccion_componentes.py"],
        "generador": Path(__file__).name,
        "fecha_generacion": generated,
        "directorio_entrada": str(ctx.input_dir),
        "directorio_graficas": str(ctx.graphics_dir),
        "ecuaciones_clave": {
            "factor_ajuste": "F_t = INPC_base / INPC_t",
            "valor_real": "Valor_real_t = Valor_nominal_t × F_t",
            "media_movil": "MA_w,t = (1/w) Σ y_(t-i)",
            "participacion": "Participación_k = total_k / total × 100",
            "correlacion_pearson": "r_xy = cov(x,y) / (s_x s_y)",
            "rezago": "x_t^(k) = y_(t-k)",
            "ventana_movil_sin_fuga": "MA_w,t = (1/w) Σ_(i=1)^w y_(t-i)",
            "codificacion_ciclica": "sin(2πx/P), cos(2πx/P)",
            "porcentaje_ceros": "Z_j = (1/n) Σ I(x_ij = 0) × 100",
            "coeficiente_variacion": "CV_j = s_j / |media_j|",
            "rango_intercuartil": "IQR_j = Q3_j - Q1_j",
            "umbral_correlacion": "|r_jk| >= 0.92",
            "vif": "VIF_j = 1 / (1 - R_j^2)",
            "normalizacion_minmax": "s_norm = (s - min(s)) / (max(s) - min(s))",
            "score_compuesto": "Score = promedio de scores normalizados",
            "lasso": "min RSS + lambda * suma |beta_j|",
            "pca_componente": "PC_j = suma_i w_ij Z_i",
            "varianza_acumulada": "VEA_k = suma_(j=1)^k EVR_j",
        },
        "graficas": [asdict(r) for r in records],
    }
    (ctx.graphics_dir / "MANIFIESTO_METODOLOGIA_PCA.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame([asdict(r) for r in records]).to_csv(
        ctx.graphics_dir / "INDICE_GRAFICAS_METODOLOGIA_PCA.csv", index=False, encoding="utf-8-sig"
    )

    lines = [
        "# Manifiesto académico de gráficas: limpieza, ingeniería de características, perfil dimensional, multicolinealidad, selección de características y PCA",
        "",
        f"**Códigos metodológicos ilustrados:** `01_clean_eda.py`, `02_feature_engineering_profesional.py`, `03_perfil_dataset_y_dimensiones.py`, `04_diagnostico_multicolinealidad.py` y `05_seleccion_caracteristicas_dataset_reducido.py` y `06_pca_reduccion_componentes.py`  ",
        f"**Fecha de generación:** {generated}  ",
        f"**Número de figuras catalogadas:** {len(records)}",
        "",
        "## Propósito metodológico",
        "",
        "Este conjunto de figuras documenta la transformación de fuentes heterogéneas en un panel diario, numérico y monetariamente comparable, y posteriormente la construcción de variables temporales, exógenas, rezagadas, móviles y derivadas para el modelado predictivo. Las gráficas se organizan desde la trazabilidad de las fuentes hasta la auditoría del dataset maestro. Cada figura incluye su fundamento matemático, criterio de lectura, limitaciones y ubicación sugerida dentro de la tesis.",
        "",
        "## Ecuaciones de transformación principales",
        "",
        r"1. **Factor de actualización:** $F_t=\frac{INPC_{base}}{INPC_t}$.",
        r"2. **Conversión a moneda constante:** $Valor^{real}_t=Valor^{nominal}_t\times F_t$.",
        r"3. **Agregación diaria:** $X_d=\sum_{i\in d}x_i$.",
        r"4. **Media móvil descriptiva:** $MA_{w,t}=\frac{1}{w}\sum_{i=0}^{w-1}y_{t-i}$.",
        r"5. **Participación por categoría:** $p_k=\frac{X_k}{\sum_jX_j}\times100$.",
        r"6. **Correlación de Pearson:** $r_{xy}=\frac{\sum_i(x_i-\bar{x})(y_i-\bar{y})}{\sqrt{\sum_i(x_i-\bar{x})^2\sum_i(y_i-\bar{y})^2}}$.",
        "",
        r"7. **Rezago:** $x_t^{(k)}=y_{t-k}$.",
        r"8. **Ventana móvil sin fuga:** $MA_{w,t}=rac{1}{w}\sum_{i=1}^{w}y_{t-i}$.",
        r"9. **Codificación cíclica:** $z_{sin}=\sin(2\pi x/P)$ y $z_{cos}=\cos(2\pi x/P)$.",
        "",
        "## Catálogo de figuras",
        "",
    ]
    for r in sorted(records, key=lambda x: x.orden):
        lines.extend([
            f"### Figura {r.orden}. {r.titulo}", "",
            f"- **Estado:** {r.estado}",
            f"- **Archivo:** `{r.archivo}`",
            f"- **Fuente y hoja:** `{r.fuente}` / `{r.hoja}`",
            f"- **Variables:** {r.variables_utilizadas}",
            f"- **Objetivo académico:** {r.objetivo}",
            f"- **Interpretación:** {r.interpretacion}",
            f"- **Criterio de lectura:** {r.criterio_lectura}",
            f"- **Fundamento o ecuación:** {r.ecuacion_o_fundamento}",
            f"- **Ubicación sugerida:** {r.uso_tesis}",
            f"- **Limitaciones:** {r.limitaciones}", "",
        ])
    lines.extend([
        "## Secuencia narrativa recomendada para el capítulo de desarrollo", "",
        "1. Iniciar con la cobertura temporal para justificar la compatibilidad de las fuentes.",
        "2. Explicar la deflactación mediante INPC y demostrar visualmente su efecto.",
        "3. Caracterizar variables exógenas: clima, temperatura, festivos y fechas de pago.",
        "4. Describir ventas desde cuatro perspectivas: tiempo, distribución, estacionalidad y mezcla de productos.",
        "5. Describir compras desde intermitencia, clasificación, proveedores y unidades normalizadas.",
        "6. Cerrar el EDA con la integración ventas-compras, la auditoría de ceros/nulos y la correlación exploratoria.",
        "7. Introducir la expansión dimensional y el historial mínimo requerido.",
        "8. Explicar codificaciones cíclicas, rezagos, ventanas móviles y proximidad a eventos.",
        "9. Presentar indicadores financieros derivados, relaciones con objetivos y auditoría final del dataset modelado.",
        "10. Exponer la estructura general, la razón predictores/observaciones y la distribución por dimensiones.",
        "11. Analizar nulos, ceros, constantes, cardinalidad y dispersión de las variables.",
        "12. Caracterizar la distribución e intermitencia de los cuatro objetivos y cerrar con la matriz de calidad dimensional.",
        "13. Presentar la distribución de correlaciones altas, los pares principales y la red de redundancia.",
        "14. Explicar las decisiones de conservación y eliminación específicas para cada objetivo.",
        "15. Complementar el análisis por pares con VIF y cerrar con la síntesis de reducción potencial.",
        "16. Presentar la magnitud de reducción y la selección específica para cada objetivo.",
        "17. Comparar scores, concordancia de métodos, cobertura dimensional y solapamiento entre objetivos.",
        "18. Explicar la contracción Lasso, el método dominante y cerrar comparando dataset completo y reducido.",
        "19. Cuantificar la reducción PCA y presentar el Scree Plot, la varianza acumulada y los umbrales alternativos.",
        "20. Interpretar las cargas, la contribución de variables y las trayectorias temporales de los componentes.",
        "21. Cerrar con el plano factorial, la relación con objetivos y la verificación de ortogonalidad.",
        "",
        "## Nota de rigor", "",
        "Las figuras son descriptivas. Ninguna asociación visual prueba causalidad ni desempeño predictivo. La capacidad de pronóstico debe establecerse posteriormente mediante partición temporal, validación Rolling-Origin y métricas fuera de muestra.",
    ])
    (ctx.graphics_dir / "MANIFIESTO_METODOLOGIA_PCA.md").write_text("\n".join(lines), encoding="utf-8")


def generate_all(input_dir: Path, graphics_dir: Path | None = None, dpi: int = 220,
                 top_n: int = 12, continue_missing: bool = True,
                 analysis_dir: Path | None = None) -> list[GraphicRecord]:
    repo_root = Path(__file__).resolve().parents[1]
    graphics_dir = graphics_dir or (repo_root / "imagenes")
    ctx = Context(input_dir=input_dir, graphics_dir=graphics_dir, dpi=dpi, top_n=top_n, analysis_dir=analysis_dir)
    configure_logging(graphics_dir)
    records: list[GraphicRecord] = []
    for index, function in enumerate(GRAPH_FUNCTIONS, start=1):
        try:
            logging.info("Generando figura %02d: %s", index, function.__name__)
            records.append(function(ctx))
        except Exception as exc:
            logging.exception("No fue posible generar %s", function.__name__)
            if not continue_missing:
                raise
            records.append(GraphicRecord(
                orden=index, etapa="Proceso metodológico", titulo=function.__name__, archivo="",
                fuente="", hoja="", variables_utilizadas="", objetivo="",
                interpretacion="", criterio_lectura="", ecuacion_o_fundamento="",
                uso_tesis="", limitaciones=f"No generada: {type(exc).__name__}: {exc}",
                estado="no_generada",
            ))
    write_manifest(ctx, records)
    write_summary_workbook(ctx, records)
    logging.info("Finalizado. Resultados en %s", graphics_dir.resolve())
    return records


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    graphics_dir = args.graphics_dir or (repo_root / "imagenes")
    generate_all(args.input_dir, graphics_dir, args.dpi, args.top_n, args.continuar_con_faltantes, args.analysis_dir)
    print(f"Gráficas académicas y manifiesto generados en: {graphics_dir.resolve()}")


if __name__ == "__main__":
    main()
