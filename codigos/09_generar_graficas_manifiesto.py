from __future__ import annotations

"""
CÓDIGO 09: GENERACIÓN DE GRÁFICAS Y MANIFIESTO EXPLICATIVO
===========================================================

Lee los archivos Excel producidos por el flujo metodológico y genera:

1. Gráficas PNG representativas de cada etapa.
2. Un manifiesto Markdown con explicación académica y sencilla.
3. Un manifiesto JSON para trazabilidad y reproducibilidad.
4. Un índice CSV con la relación entre gráfica, fuente e interpretación.

Ejemplo:
    python 09_generar_graficas_manifiesto.py \
        --input-dir "C:/Python/tesis/input" \
        --output-dir "C:/Python/tesis/output/analisis_dimensional"

Dependencias:
    pip install pandas numpy matplotlib openpyxl
"""

import argparse
import json
import logging
import textwrap
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


TARGET_LABELS = {
    "target_ventas_importe_real_2026_05": "Importe de ventas",
    "target_compras_total_real_2026_05": "Importe de compras",
    "target_ventas_registros": "Registros de ventas",
    "target_compras_registros": "Registros de compras",
}

MODEL_LABELS = {
    "empirico_ultimo_valor": "Último valor",
    "empirico_promedio_7d": "Promedio 7 días",
    "regresion_lineal_multivariable": "Regresión lineal",
    "arbol_decision": "Árbol de decisión",
    "random_forest": "Random Forest",
    "arima_111": "ARIMA(1,1,1)",
    "sarima_semanal": "SARIMA semanal",
    "rnn_simple": "RNN simple",
    "lstm": "LSTM",
}


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
    limitaciones: str
    estado: str = "generada"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera gráficas y manifiesto a partir de los outputs de la tesis.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(r"C:/Python/tesis/input"),
        help="Carpeta del dataset maestro y dataset de modelado.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(r"C:/Python/tesis/output/analisis_dimensional"),
        help="Carpeta donde están los Excel metodológicos.",
    )
    parser.add_argument(
        "--graphics-dir",
        type=Path,
        default=None,
        help="Carpeta de salida de las gráficas. Por defecto: output-dir/graficas_metodologia.",
    )
    parser.add_argument("--dpi", type=int, default=180, help="Resolución de imágenes PNG.")
    parser.add_argument(
        "--top-n", type=int, default=15, help="Número máximo de variables o modelos mostrados por gráfica."
    )
    parser.add_argument(
        "--continuar-con-faltantes",
        action="store_true",
        help="Continúa y documenta archivos faltantes en lugar de detenerse.",
    )
    return parser.parse_args()


def configure_logging(graphics_dir: Path) -> None:
    graphics_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(graphics_dir / "generacion_graficas.log", mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def read_excel_required(path: Path, sheet: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo requerido: {path}")
    with pd.ExcelFile(path) as excel:
        if sheet not in excel.sheet_names:
            raise ValueError(f"{path.name} no contiene la hoja '{sheet}'. Hojas: {excel.sheet_names}")
    return pd.read_excel(path, sheet_name=sheet)


def save_figure(fig: plt.Figure, path: Path, dpi: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def wrap_labels(values: pd.Series | list[str], width: int = 34) -> list[str]:
    return ["\n".join(textwrap.wrap(str(value), width=width)) for value in values]


def target_label(value: str) -> str:
    return TARGET_LABELS.get(value, value.replace("target_", "").replace("_", " ").title())


def model_label(value: str) -> str:
    return MODEL_LABELS.get(value, value.replace("_", " ").title())


def graph_dimension_distribution(output_dir: Path, graphics_dir: Path, dpi: int, top_n: int) -> GraphicRecord:
    source = output_dir / "01_perfil_dataset_y_dimensiones.xlsx"
    df = read_excel_required(source, "resumen_dimensiones").sort_values("variables", ascending=True)
    if len(df) > top_n:
        df = df.tail(top_n)

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.barh(wrap_labels(df["dimension"]), df["variables"])
    ax.set_title("Distribución de variables por dimensión metodológica")
    ax.set_xlabel("Número de variables")
    ax.set_ylabel("Dimensión")
    ax.grid(axis="x", alpha=0.25)
    for idx, value in enumerate(df["variables"]):
        ax.text(value, idx, f" {int(value)}", va="center")
    fig.tight_layout()

    filename = "01_distribucion_variables_por_dimension.png"
    save_figure(fig, graphics_dir / filename, dpi)
    dominant = df.sort_values("variables", ascending=False).iloc[0]
    return GraphicRecord(
        1,
        "Perfil del dataset",
        "Distribución de variables por dimensión",
        filename,
        source.name,
        "resumen_dimensiones",
        "dimension, variables",
        "Mostrar cómo se distribuye la dimensionalidad entre calendario, rezagos, ventanas móviles y otras familias.",
        f"La dimensión con más variables es '{dominant['dimension']}' con {int(dominant['variables'])} columnas. Las barras largas identifican las familias que más incrementan la complejidad del dataset.",
        "Una concentración alta en rezagos o ventanas móviles justifica aplicar diagnóstico de redundancia y reducción dimensional.",
        "La gráfica cuenta columnas; no mide por sí sola la calidad predictiva de cada dimensión.",
    )


def graph_data_quality(output_dir: Path, graphics_dir: Path, dpi: int, top_n: int) -> GraphicRecord:
    source = output_dir / "01_perfil_dataset_y_dimensiones.xlsx"
    df = read_excel_required(source, "perfil_variables")
    df["porcentaje_ceros"] = pd.to_numeric(df["porcentaje_ceros"], errors="coerce")
    df["porcentaje_nulos"] = pd.to_numeric(df["porcentaje_nulos"], errors="coerce")
    top = df.sort_values(["porcentaje_nulos", "porcentaje_ceros"], ascending=False).head(top_n).copy()

    fig, ax = plt.subplots(figsize=(12, 8))
    y = np.arange(len(top))
    ax.barh(y, top["porcentaje_ceros"] * 100, label="Ceros")
    ax.barh(y, top["porcentaje_nulos"] * 100, left=top["porcentaje_ceros"] * 100, label="Nulos")
    ax.set_yticks(y)
    ax.set_yticklabels(wrap_labels(top["variable"], 38))
    ax.invert_yaxis()
    ax.set_title(f"Variables con mayor concentración de ceros y nulos (Top {len(top)})")
    ax.set_xlabel("Porcentaje de observaciones")
    ax.legend()
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    filename = "02_calidad_variables_ceros_nulos.png"
    save_figure(fig, graphics_dir / filename, dpi)
    max_row = top.iloc[0]
    return GraphicRecord(
        2,
        "Perfil del dataset",
        "Concentración de ceros y nulos",
        filename,
        source.name,
        "perfil_variables",
        "variable, porcentaje_ceros, porcentaje_nulos",
        "Detectar variables escasas, incompletas o dominadas por ceros que podrían aportar poca información estable.",
        f"La primera variable del ranking es '{max_row['variable']}'. Una barra extensa significa que gran parte de sus registros no presenta actividad o información disponible.",
        "Las variables con muchos ceros deben evaluarse junto con su relevancia predictiva; no deben eliminarse automáticamente.",
        "Un cero puede ser un valor real de ausencia de operación y no necesariamente un problema de calidad.",
    )


def graph_high_correlations(output_dir: Path, graphics_dir: Path, dpi: int, top_n: int) -> GraphicRecord:
    source = output_dir / "02_diagnostico_multicolinealidad.xlsx"
    df = read_excel_required(source, "pares_correlacion_alta").sort_values("correlacion_abs", ascending=False).head(top_n)
    labels = df["variable_1"].astype(str) + "  ↔  " + df["variable_2"].astype(str)

    fig, ax = plt.subplots(figsize=(13, 8))
    ax.barh(np.arange(len(df)), df["correlacion_abs"])
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels(wrap_labels(labels, 54))
    ax.invert_yaxis()
    ax.set_xlim(max(0, float(df["correlacion_abs"].min()) - 0.03), 1.005)
    ax.set_title(f"Pares de variables con mayor correlación absoluta (Top {len(df)})")
    ax.set_xlabel("Correlación absoluta")
    ax.axvline(0.92, linestyle="--", linewidth=1, label="Umbral 0.92")
    ax.legend()
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    filename = "03_pares_mayor_multicolinealidad.png"
    save_figure(fig, graphics_dir / filename, dpi)
    strongest = df.iloc[0]
    return GraphicRecord(
        3,
        "Diagnóstico de multicolinealidad",
        "Pares con mayor correlación absoluta",
        filename,
        source.name,
        "pares_correlacion_alta",
        "variable_1, variable_2, correlacion_abs",
        "Evidenciar qué predictores contienen información lineal muy similar y podrían ser redundantes.",
        f"El par más relacionado es '{strongest['variable_1']}' y '{strongest['variable_2']}', con correlación absoluta de {strongest['correlacion_abs']:.4f}.",
        "Los pares por encima de 0.92 deben revisarse para conservar la variable más relacionada con el objetivo o la más interpretable.",
        "La correlación solamente identifica relaciones lineales entre pares y no sustituye al análisis VIF o a la validación predictiva.",
    )


def graph_vif(output_dir: Path, graphics_dir: Path, dpi: int, top_n: int) -> GraphicRecord:
    source = output_dir / "02_diagnostico_multicolinealidad.xlsx"
    df = read_excel_required(source, "vif_opcional")
    if "vif" not in df.columns:
        raise ValueError("La hoja vif_opcional no contiene la columna 'vif'. Instale statsmodels y regenere el diagnóstico.")
    df["vif"] = pd.to_numeric(df["vif"], errors="coerce").replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["vif"]).sort_values("vif", ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(np.arange(len(df)), df["vif"])
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels(wrap_labels(df["variable"], 45))
    ax.invert_yaxis()
    ax.set_title(f"Variables con mayor Factor de Inflación de la Varianza (Top {len(df)})")
    ax.set_xlabel("VIF")
    ax.axvline(5, linestyle="--", linewidth=1, label="Referencia VIF = 5")
    ax.axvline(10, linestyle=":", linewidth=1, label="Referencia VIF = 10")
    ax.legend()
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    filename = "04_variables_mayor_vif.png"
    save_figure(fig, graphics_dir / filename, dpi)
    top = df.iloc[0]
    return GraphicRecord(
        4,
        "Diagnóstico de multicolinealidad",
        "Variables con mayor VIF",
        filename,
        source.name,
        "vif_opcional",
        "variable, vif",
        "Complementar el análisis de correlación mediante una medida de redundancia de cada variable respecto al conjunto de predictores.",
        f"La variable con mayor VIF es '{top['variable']}' con {top['vif']:.2f}. Valores altos indican que puede explicarse ampliamente mediante otras variables.",
        "VIF superiores a 5 requieren revisión y valores superiores a 10 suelen considerarse evidencia fuerte de multicolinealidad.",
        "Los umbrales son referencias prácticas y deben combinarse con interpretabilidad y desempeño fuera de muestra.",
    )


def graph_feature_ranking(output_dir: Path, graphics_dir: Path, dpi: int, top_n: int) -> GraphicRecord:
    source = output_dir / "03_dataset_reducido_por_seleccion.xlsx"
    df = read_excel_required(source, "ranking_variables")
    selected = df[df["seleccionada"].astype(bool)].copy()
    agg = (
        selected.groupby("variable", as_index=False)
        .agg(score_compuesto=("score_compuesto", "mean"), objetivos=("target", "nunique"))
        .sort_values(["score_compuesto", "objetivos"], ascending=False)
        .head(top_n)
        .sort_values("score_compuesto", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(wrap_labels(agg["variable"], 45), agg["score_compuesto"])
    ax.set_title(f"Variables seleccionadas con mayor puntuación compuesta (Top {len(agg)})")
    ax.set_xlabel("Puntuación compuesta normalizada")
    ax.set_ylabel("Variable")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    filename = "05_ranking_caracteristicas_seleccionadas.png"
    save_figure(fig, graphics_dir / filename, dpi)
    strongest = agg.iloc[-1]
    return GraphicRecord(
        5,
        "Selección de características",
        "Ranking de características seleccionadas",
        filename,
        source.name,
        "ranking_variables",
        "variable, score_compuesto, seleccionada, target",
        "Mostrar las variables que concentran mayor evidencia combinada de correlación, información mutua, Random Forest y Lasso.",
        f"La variable con mayor puntuación media es '{strongest['variable']}' con score {strongest['score_compuesto']:.4f}, considerando su aparición en {int(strongest['objetivos'])} objetivo(s).",
        "Una puntuación alta significa consistencia entre los métodos de selección, pero no garantiza por sí sola causalidad ni estabilidad futura.",
        "El score es relativo a los métodos y umbrales configurados; puede cambiar al modificar el periodo o los hiperparámetros.",
    )


def graph_reduction_comparison(output_dir: Path, graphics_dir: Path, dpi: int, _: int) -> GraphicRecord:
    profile = read_excel_required(output_dir / "01_perfil_dataset_y_dimensiones.xlsx", "resumen_general")
    reduced = read_excel_required(output_dir / "03_dataset_reducido_por_seleccion.xlsx", "resumen")
    pca = read_excel_required(output_dir / "04_dataset_pca_componentes.xlsx", "varianza_explicada")

    pmap = dict(zip(profile["metrica"].astype(str), profile["valor"]))
    rmap = dict(zip(reduced["metrica"].astype(str), reduced["valor"]))
    original = int(float(pmap.get("predictores", 0)))
    reduced_count = int(float(rmap.get("variables_reducidas", rmap.get("predictores_reducidos", 0))))
    pca_count = len(pca)
    data = pd.DataFrame({"versión": ["Completo", "Selección", "PCA"], "variables": [original, reduced_count, pca_count]})

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(data["versión"], data["variables"])
    ax.set_title("Comparación de dimensionalidad entre versiones del dataset")
    ax.set_ylabel("Número de predictores o componentes")
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(data["variables"]):
        ax.text(idx, value, f"{int(value)}", ha="center", va="bottom")
    fig.tight_layout()

    filename = "06_comparacion_reduccion_dimensional.png"
    save_figure(fig, graphics_dir / filename, dpi)
    reduction_selection = 100 * (1 - reduced_count / original) if original else np.nan
    reduction_pca = 100 * (1 - pca_count / original) if original else np.nan
    return GraphicRecord(
        6,
        "Reducción dimensional",
        "Comparación de dimensionalidad",
        filename,
        "01_perfil_dataset_y_dimensiones.xlsx; 03_dataset_reducido_por_seleccion.xlsx; 04_dataset_pca_componentes.xlsx",
        "resumen_general; resumen; varianza_explicada",
        "predictores, variables_reducidas, número de componentes",
        "Comparar de forma directa el tamaño del dataset completo, la selección de variables y la representación PCA.",
        f"La selección reduce aproximadamente {reduction_selection:.1f}% y PCA reduce {reduction_pca:.1f}% respecto a {original} predictores originales.",
        "Una mayor reducción mejora compacidad, pero puede disminuir interpretabilidad o perder información predictiva.",
        "El número de componentes PCA no equivale a variables interpretables de negocio.",
    )


def graph_pca_variance(output_dir: Path, graphics_dir: Path, dpi: int, _: int) -> GraphicRecord:
    source = output_dir / "04_dataset_pca_componentes.xlsx"
    df = read_excel_required(source, "varianza_explicada")
    x = np.arange(1, len(df) + 1)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(x, df["varianza_acumulada"] * 100)
    ax.axhline(95, linestyle="--", linewidth=1, label="Objetivo 95 %")
    ax.set_title("Varianza acumulada conservada mediante PCA")
    ax.set_xlabel("Número de componentes principales")
    ax.set_ylabel("Varianza acumulada (%)")
    ax.set_ylim(0, 101)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()

    filename = "07_varianza_acumulada_pca.png"
    save_figure(fig, graphics_dir / filename, dpi)
    reached = int(np.argmax(df["varianza_acumulada"].to_numpy() >= 0.95) + 1)
    final_variance = float(df["varianza_acumulada"].iloc[-1] * 100)
    return GraphicRecord(
        7,
        "PCA",
        "Varianza acumulada de los componentes",
        filename,
        source.name,
        "varianza_explicada",
        "componente, varianza_explicada, varianza_acumulada",
        "Justificar cuántos componentes son necesarios para conservar al menos 95 % de la información estadística.",
        f"El umbral de 95 % se alcanza en el componente {reached}; el dataset PCA termina con {len(df)} componentes y conserva {final_variance:.2f}% de varianza.",
        "El punto donde la curva cruza 95 % define la dimensionalidad necesaria bajo el criterio configurado.",
        "La varianza explicada mide conservación estadística, no garantiza el menor error de pronóstico.",
    )


def graph_pca_loadings(output_dir: Path, graphics_dir: Path, dpi: int, top_n: int) -> GraphicRecord:
    source = output_dir / "04_dataset_pca_componentes.xlsx"
    df = read_excel_required(source, "cargas_componentes")
    component = "pca_01"
    top = df.assign(carga_abs=df[component].abs()).nlargest(top_n, "carga_abs").sort_values(component)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(wrap_labels(top["variable"], 45), top[component])
    ax.axvline(0, linewidth=0.8)
    ax.set_title(f"Variables con mayor contribución al primer componente ({component})")
    ax.set_xlabel("Carga del componente")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    filename = "08_cargas_primer_componente_pca.png"
    save_figure(fig, graphics_dir / filename, dpi)
    strongest = top.loc[top["carga_abs"].idxmax()]
    return GraphicRecord(
        8,
        "PCA",
        "Cargas del primer componente principal",
        filename,
        source.name,
        "cargas_componentes",
        f"variable, {component}",
        "Facilitar una interpretación parcial del componente principal mediante las variables originales con mayor peso absoluto.",
        f"La mayor carga absoluta en {component} corresponde a '{strongest['variable']}' con valor {strongest[component]:.4f}.",
        "Las cargas positivas y negativas indican direcciones opuestas dentro del componente; la magnitud expresa contribución relativa.",
        "Un componente combina muchas variables, por lo que no debe nombrarse únicamente con base en una sola carga.",
    )


def load_rolling_rankings(output_dir: Path) -> pd.DataFrame:
    frames = []
    for variant in ("completo", "reducido", "pca"):
        path = output_dir / f"05_modelos_rolling_origin_{variant}.xlsx"
        if path.exists():
            frame = read_excel_required(path, "ranking_modelos")
            frame["archivo_fuente"] = path.name
            frames.append(frame)
    if not frames:
        raise FileNotFoundError("No se encontraron archivos 05_modelos_rolling_origin_*.xlsx")
    return pd.concat(frames, ignore_index=True)


def graph_best_rolling_models(output_dir: Path, graphics_dir: Path, dpi: int, _: int) -> GraphicRecord:
    df = load_rolling_rankings(output_dir)
    df["rmse_promedio"] = pd.to_numeric(df["rmse_promedio"], errors="coerce")
    best = df.loc[df.groupby(["dataset", "target"])["rmse_promedio"].idxmin()].copy()
    best["grupo"] = best["dataset"].astype(str).str.title() + " | " + best["target"].map(target_label)
    best = best.sort_values("rmse_promedio", ascending=True)

    fig, ax = plt.subplots(figsize=(13, 8))
    ax.barh(wrap_labels(best["grupo"], 42), best["rmse_promedio"])
    ax.set_title("Mejor modelo Rolling-Origin por dataset y objetivo")
    ax.set_xlabel("RMSE promedio (menor es mejor)")
    ax.grid(axis="x", alpha=0.25)
    for idx, (_, row) in enumerate(best.iterrows()):
        ax.text(row["rmse_promedio"], idx, " " + model_label(row["modelo"]), va="center", fontsize=8)
    fig.tight_layout()

    filename = "09_mejores_modelos_rolling_origin.png"
    save_figure(fig, graphics_dir / filename, dpi)
    winner = best.iloc[0]
    return GraphicRecord(
        9,
        "Modelado Rolling-Origin",
        "Mejor modelo por dataset y objetivo",
        filename,
        "; ".join(sorted(df["archivo_fuente"].unique())),
        "ranking_modelos",
        "dataset, target, modelo, rmse_promedio",
        "Comparar los modelos con validación temporal repetida y mostrar el menor RMSE para cada combinación de dataset y objetivo.",
        f"El menor RMSE mostrado corresponde a {model_label(winner['modelo'])} para {target_label(winner['target'])} en el dataset {winner['dataset']}, con {winner['rmse_promedio']:.4f}.",
        "En cada barra, menor longitud significa mejor desempeño promedio fuera de muestra dentro de su objetivo.",
        "No deben compararse directamente magnitudes de RMSE entre objetivos expresados en unidades distintas.",
    )


def graph_rolling_stability(output_dir: Path, graphics_dir: Path, dpi: int, _: int) -> GraphicRecord:
    frames = []
    for variant in ("completo", "reducido", "pca"):
        path = output_dir / f"05_modelos_rolling_origin_{variant}.xlsx"
        if path.exists():
            frame = read_excel_required(path, "resultados_por_origen")
            frames.append(frame)
    if not frames:
        raise FileNotFoundError("No se encontraron resultados Rolling-Origin.")
    df = pd.concat(frames, ignore_index=True)
    target = "target_ventas_importe_real_2026_05"
    subset = df[df["target"] == target].copy()
    subset["fecha_inicio_prueba"] = pd.to_datetime(subset["fecha_inicio_prueba"])
    ranking = subset.groupby(["dataset", "modelo"], as_index=False)["rmse"].mean().nsmallest(4, "rmse")
    keys = set(zip(ranking["dataset"], ranking["modelo"]))
    subset = subset[subset.apply(lambda r: (r["dataset"], r["modelo"]) in keys, axis=1)]

    fig, ax = plt.subplots(figsize=(12, 7))
    for (dataset, model), group in subset.groupby(["dataset", "modelo"]):
        group = group.sort_values("fecha_inicio_prueba")
        ax.plot(group["fecha_inicio_prueba"], group["rmse"], marker="o", label=f"{dataset} | {model_label(model)}")
    ax.set_title("Estabilidad temporal del RMSE para el importe de ventas")
    ax.set_xlabel("Inicio de ventana de prueba")
    ax.set_ylabel("RMSE")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()

    filename = "10_estabilidad_rmse_rolling_origin_ventas.png"
    save_figure(fig, graphics_dir / filename, dpi)
    return GraphicRecord(
        10,
        "Modelado Rolling-Origin",
        "Estabilidad temporal del error",
        filename,
        "05_modelos_rolling_origin_completo.xlsx; 05_modelos_rolling_origin_reducido.xlsx; 05_modelos_rolling_origin_pca.xlsx",
        "resultados_por_origen",
        "fecha_inicio_prueba, dataset, modelo, target, rmse",
        "Mostrar si los modelos mantienen un error estable a través de diferentes periodos de validación y no solamente un buen promedio global.",
        "Las líneas con valores bajos y poca variación representan modelos más precisos y estables en diferentes orígenes de pronóstico.",
        "Picos aislados revelan periodos difíciles o sensibilidad del modelo a cambios operativos.",
        "La gráfica se centra en el importe de ventas y en los cuatro mejores pares dataset-modelo por RMSE promedio.",
    )


def load_rnn_results(output_dir: Path) -> pd.DataFrame:
    frames = []
    for variant in ("reducido", "pca"):
        path = output_dir / f"06_rnn_lstm_{variant}.xlsx"
        if path.exists():
            with pd.ExcelFile(path) as excel:
                sheet = excel.sheet_names[0]
            frame = pd.read_excel(path, sheet_name=sheet)
            frame["archivo_fuente"] = path.name
            frames.append(frame)
    if not frames:
        raise FileNotFoundError("No se encontraron archivos 06_rnn_lstm_*.xlsx")
    return pd.concat(frames, ignore_index=True)


def graph_rnn_comparison(output_dir: Path, graphics_dir: Path, dpi: int, _: int) -> GraphicRecord:
    df = load_rnn_results(output_dir)
    df["grupo"] = df["dataset"].astype(str).str.title() + " | " + df["target"].map(target_label) + " | " + df["modelo"].map(model_label)
    df = df.sort_values("rmse", ascending=True)

    fig, ax = plt.subplots(figsize=(13, 9))
    ax.barh(wrap_labels(df["grupo"], 48), df["rmse"])
    ax.set_title("Comparación de RNN y LSTM por dataset y objetivo")
    ax.set_xlabel("RMSE en prueba final de 90 días")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()

    filename = "11_comparacion_rnn_lstm_rmse.png"
    save_figure(fig, graphics_dir / filename, dpi)
    winner = df.iloc[0]
    return GraphicRecord(
        11,
        "Redes neuronales recurrentes",
        "Comparación RNN y LSTM",
        filename,
        "; ".join(sorted(df["archivo_fuente"].unique())),
        "primera hoja",
        "dataset, target, modelo, rmse",
        "Comparar el error de RNN simple y LSTM usando las versiones reducida y PCA del dataset.",
        f"El menor RMSE dentro de esta prueba corresponde a {model_label(winner['modelo'])}, dataset {winner['dataset']}, objetivo {target_label(winner['target'])}, con {winner['rmse']:.4f}.",
        "Para cada objetivo deben compararse las barras de RNN y LSTM dentro de la misma escala y versión del dataset.",
        "Estos resultados proceden de una prueba final de 90 días y no son directamente equivalentes a la validación Rolling-Origin.",
    )


def graph_method_summary(output_dir: Path, graphics_dir: Path, dpi: int, _: int) -> GraphicRecord:
    profile = read_excel_required(output_dir / "01_perfil_dataset_y_dimensiones.xlsx", "resumen_general")
    reduced = read_excel_required(output_dir / "03_dataset_reducido_por_seleccion.xlsx", "resumen")
    pca = read_excel_required(output_dir / "04_dataset_pca_componentes.xlsx", "varianza_explicada")
    corr = read_excel_required(output_dir / "02_diagnostico_multicolinealidad.xlsx", "pares_correlacion_alta")

    pmap = dict(zip(profile["metrica"].astype(str), profile["valor"]))
    rmap = dict(zip(reduced["metrica"].astype(str), reduced["valor"]))
    values = [
        int(float(pmap.get("predictores", 0))),
        len(corr),
        int(float(rmap.get("variables_reducidas", rmap.get("predictores_reducidos", 0)))),
        len(pca),
    ]
    labels = ["Predictores\noriginales", "Pares con\ncorrelación alta", "Variables\nseleccionadas", "Componentes\nPCA"]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values)
    ax.set_title("Indicadores principales del proceso de reducción dimensional")
    ax.set_ylabel("Cantidad")
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(values):
        ax.text(idx, value, str(value), ha="center", va="bottom")
    fig.tight_layout()

    filename = "12_resumen_cuantitativo_metodologia.png"
    save_figure(fig, graphics_dir / filename, dpi)
    return GraphicRecord(
        12,
        "Síntesis metodológica",
        "Indicadores cuantitativos del flujo",
        filename,
        "01_perfil_dataset_y_dimensiones.xlsx; 02_diagnostico_multicolinealidad.xlsx; 03_dataset_reducido_por_seleccion.xlsx; 04_dataset_pca_componentes.xlsx",
        "resúmenes metodológicos",
        "predictores, pares correlacionados, variables seleccionadas, componentes PCA",
        "Presentar en una sola figura los principales tamaños y resultados intermedios del análisis dimensional.",
        f"El proceso parte de {values[0]} predictores, identifica {values[1]} pares altamente correlacionados, conserva {values[2]} variables por selección y representa la información mediante {values[3]} componentes PCA.",
        "La figura permite explicar el tránsito desde el dataset original hacia dos estrategias alternativas de reducción.",
        "Las barras representan conceptos diferentes; se comparan como conteos metodológicos, no como métricas de desempeño.",
    )


def write_manifest(records: list[GraphicRecord], graphics_dir: Path, input_dir: Path, output_dir: Path) -> None:
    generated_at = datetime.now().isoformat(timespec="seconds")
    successful = [record for record in records if record.estado == "generada"]
    failed = [record for record in records if record.estado != "generada"]

    json_payload = {
        "titulo": "Manifiesto de gráficas del flujo metodológico de tesis",
        "fecha_generacion": generated_at,
        "input_dir": str(input_dir.resolve()),
        "output_dir": str(output_dir.resolve()),
        "graphics_dir": str(graphics_dir.resolve()),
        "total_graficas_generadas": len(successful),
        "total_graficas_no_generadas": len(failed),
        "graficas": [asdict(record) for record in records],
        "reglas_generales_interpretacion": [
            "Las gráficas descriptivas explican estructura y calidad; no prueban capacidad predictiva.",
            "Correlación y VIF identifican redundancia, pero la decisión final debe considerar interpretabilidad y validación temporal.",
            "PCA conserva varianza estadística, aunque sus componentes reducen la interpretación directa de negocio.",
            "MAE y RMSE deben compararse dentro del mismo objetivo y unidad de medida.",
            "Los resultados Rolling-Origin y RNN/LSTM no deben mezclarse como si utilizaran el mismo esquema de validación.",
            "MAPE requiere cautela cuando el valor real puede ser cero o cercano a cero.",
        ],
    }
    (graphics_dir / "MANIFIESTO_GRAFICAS.json").write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Manifiesto explicativo de gráficas del flujo metodológico",
        "",
        f"**Fecha de generación:** {generated_at}",
        f"**Directorio de datos intermedios:** `{input_dir}`",
        f"**Directorio de resultados:** `{output_dir}`",
        f"**Gráficas generadas:** {len(successful)}",
        "",
        "## Propósito",
        "",
        "Este manifiesto documenta la relación entre cada gráfica, el archivo Excel del que proviene y la interpretación que puede incorporarse al capítulo metodológico o de resultados de la tesis. Las imágenes no sustituyen las tablas completas; funcionan como evidencia visual sintetizada.",
        "",
        "## Reglas generales de lectura",
        "",
        "1. Las gráficas descriptivas muestran estructura, concentración y calidad, pero no demuestran capacidad predictiva.",
        "2. Correlación y VIF se utilizan para detectar redundancia; la eliminación debe considerar también relevancia financiera y desempeño fuera de muestra.",
        "3. PCA conserva varianza, pero transforma las variables en componentes menos interpretables.",
        "4. MAE y RMSE deben compararse únicamente dentro del mismo objetivo y unidad.",
        "5. Rolling-Origin y la prueba final de RNN/LSTM son esquemas de evaluación diferentes; no deben compararse sin aclararlo.",
        "6. MAPE puede ser inestable o no calculable cuando los valores reales contienen ceros.",
        "",
        "## Catálogo de gráficas",
        "",
    ]

    for record in sorted(records, key=lambda r: r.orden):
        lines.extend(
            [
                f"### {record.orden}. {record.titulo}",
                "",
                f"- **Etapa:** {record.etapa}",
                f"- **Estado:** {record.estado}",
                f"- **Imagen:** `{record.archivo}`",
                f"- **Fuente:** `{record.fuente}`",
                f"- **Hoja:** `{record.hoja}`",
                f"- **Variables utilizadas:** {record.variables_utilizadas}",
                f"- **Objetivo visual:** {record.objetivo}",
                f"- **Interpretación principal:** {record.interpretacion}",
                f"- **Criterio de lectura:** {record.criterio_lectura}",
                f"- **Limitaciones:** {record.limitaciones}",
                "",
            ]
        )

    lines.extend(
        [
            "## Uso recomendado en la tesis",
            "",
            "Las gráficas 1 y 2 pueden colocarse en la caracterización del dataset. Las gráficas 3 y 4 respaldan el diagnóstico de multicolinealidad. Las gráficas 5 a 8 documentan las estrategias de reducción dimensional. Las gráficas 9 y 10 corresponden a la validación temporal Rolling-Origin. La gráfica 11 presenta los resultados de redes recurrentes bajo prueba final. La gráfica 12 puede emplearse como cierre visual del flujo metodológico.",
            "",
            "## Reproducibilidad",
            "",
            "Todas las imágenes se generan directamente desde los archivos Excel producidos por los scripts metodológicos. Para reproducirlas se debe ejecutar este código después de completar las etapas de perfil, multicolinealidad, selección, PCA, Rolling-Origin y RNN/LSTM.",
        ]
    )
    (graphics_dir / "MANIFIESTO_GRAFICAS.md").write_text("\n".join(lines), encoding="utf-8")

    pd.DataFrame([asdict(record) for record in records]).to_csv(
        graphics_dir / "INDICE_GRAFICAS.csv", index=False, encoding="utf-8-sig"
    )


def generate_all(
    input_dir: Path,
    output_dir: Path,
    graphics_dir: Path | None = None,
    dpi: int = 180,
    top_n: int = 15,
    continue_missing: bool = True,
) -> list[GraphicRecord]:
    """Genera todas las gráficas y devuelve el catálogo del manifiesto."""
    graphics_dir = graphics_dir or (output_dir / "graficas_metodologia")
    configure_logging(graphics_dir)

    graph_functions: list[Callable[[Path, Path, int, int], GraphicRecord]] = [
        graph_dimension_distribution,
        graph_data_quality,
        graph_high_correlations,
        graph_vif,
        graph_feature_ranking,
        graph_reduction_comparison,
        graph_pca_variance,
        graph_pca_loadings,
        graph_best_rolling_models,
        graph_rolling_stability,
        graph_rnn_comparison,
        graph_method_summary,
    ]

    records: list[GraphicRecord] = []
    for index, function in enumerate(graph_functions, start=1):
        try:
            logging.info("Generando gráfica %02d: %s", index, function.__name__)
            records.append(function(output_dir, graphics_dir, dpi, top_n))
        except Exception as exc:
            logging.exception("No fue posible generar %s", function.__name__)
            if not continue_missing:
                raise
            records.append(
                GraphicRecord(
                    orden=index,
                    etapa="No disponible",
                    titulo=function.__name__,
                    archivo="",
                    fuente="",
                    hoja="",
                    variables_utilizadas="",
                    objetivo="",
                    interpretacion="",
                    criterio_lectura="",
                    limitaciones=f"No generada: {type(exc).__name__}: {exc}",
                    estado="no_generada",
                )
            )

    write_manifest(records, graphics_dir, input_dir, output_dir)
    logging.info("Proceso finalizado. Carpeta: %s", graphics_dir.resolve())
    return records


def main() -> None:
    args = parse_args()
    graphics_dir = args.graphics_dir or (args.output_dir / "graficas_metodologia")
    generate_all(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        graphics_dir=graphics_dir,
        dpi=args.dpi,
        top_n=args.top_n,
        continue_missing=args.continuar_con_faltantes,
    )
    print(f"Gráficas y manifiestos generados en: {graphics_dir.resolve()}")


if __name__ == "__main__":
    main()
