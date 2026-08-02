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
- MANIFIESTO_CLEAN_EDA.md con interpretación académica.
- MANIFIESTO_CLEAN_EDA.json para trazabilidad.
- INDICE_GRAFICAS_CLEAN_EDA.csv.
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
        description="Genera gráficas académicas de los outputs de 01_clean_eda.py.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-dir", type=Path, default=Path(r"C:/Python/tesis/input"))
    parser.add_argument("--graphics-dir", type=Path, default=None)
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
            logging.FileHandler(graphics_dir / "generacion_clean_eda.log", mode="w", encoding="utf-8"),
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
]


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
    with pd.ExcelWriter(ctx.graphics_dir / "RESUMEN_ESTADISTICO_CLEAN_EDA.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([asdict(r) for r in records]).to_excel(writer, sheet_name="indice_graficas", index=False)
        for name, df in summaries.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)


def write_manifest(ctx: Context, records: list[GraphicRecord]) -> None:
    generated = datetime.now().astimezone().isoformat()
    payload = {
        "titulo": "Manifiesto académico de gráficas de limpieza y análisis exploratorio",
        "codigo_fuente": "01_clean_eda.py",
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
        },
        "graficas": [asdict(r) for r in records],
    }
    (ctx.graphics_dir / "MANIFIESTO_CLEAN_EDA.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame([asdict(r) for r in records]).to_csv(
        ctx.graphics_dir / "INDICE_GRAFICAS_CLEAN_EDA.csv", index=False, encoding="utf-8-sig"
    )

    lines = [
        "# Manifiesto académico de gráficas: limpieza, EDA e integración",
        "",
        f"**Código metodológico ilustrado:** `01_clean_eda.py`  ",
        f"**Fecha de generación:** {generated}  ",
        f"**Número de figuras catalogadas:** {len(records)}",
        "",
        "## Propósito metodológico",
        "",
        "Este conjunto de figuras documenta la transformación de fuentes heterogéneas en un panel diario, numérico y monetariamente comparable. Las gráficas se organizan desde la trazabilidad de las fuentes hasta la auditoría del dataset maestro. Cada figura incluye su fundamento matemático, criterio de lectura, limitaciones y ubicación sugerida dentro de la tesis.",
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
        "6. Cerrar con la integración ventas-compras, la auditoría de ceros/nulos y la correlación exploratoria.",
        "",
        "## Nota de rigor", "",
        "Las figuras son descriptivas. Ninguna asociación visual prueba causalidad ni desempeño predictivo. La capacidad de pronóstico debe establecerse posteriormente mediante partición temporal, validación Rolling-Origin y métricas fuera de muestra.",
    ])
    (ctx.graphics_dir / "MANIFIESTO_CLEAN_EDA.md").write_text("\n".join(lines), encoding="utf-8")


def generate_all(input_dir: Path, graphics_dir: Path | None = None, dpi: int = 220,
                 top_n: int = 12, continue_missing: bool = True) -> list[GraphicRecord]:
    graphics_dir = graphics_dir or (input_dir / "graficas_clean_eda")
    ctx = Context(input_dir=input_dir, graphics_dir=graphics_dir, dpi=dpi, top_n=top_n)
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
                orden=index, etapa="Limpieza y EDA", titulo=function.__name__, archivo="",
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
    graphics_dir = args.graphics_dir or (args.input_dir / "graficas_clean_eda")
    generate_all(args.input_dir, graphics_dir, args.dpi, args.top_n, args.continuar_con_faltantes)
    print(f"Gráficas académicas y manifiesto generados en: {graphics_dir.resolve()}")


if __name__ == "__main__":
    main()
