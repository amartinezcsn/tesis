from __future__ import annotations

"""
CÓDIGO 10 — GRÁFICAS ACADÉMICAS DE VALIDACIÓN ROLLING-ORIGIN
================================================================

Genera evidencia visual, tablas de síntesis y un manifiesto académico a partir de:

- 05_modelos_rolling_origin_completo.xlsx
- 05_modelos_rolling_origin_reducido.xlsx
- 05_modelos_rolling_origin_pca.xlsx

Salidas:
- 16 figuras PNG listas para tesis.
- MANIFIESTO_ROLLING_ORIGIN.md
- MANIFIESTO_ROLLING_ORIGIN.json
- INDICE_GRAFICAS_ROLLING_ORIGIN.csv
- RESUMEN_ESTADISTICO_ROLLING_ORIGIN.xlsx
- generacion_rolling_origin.log

Ejemplo:
    python 10_generar_graficas_rolling_origin.py \
        --analysis-dir "C:/Python/tesis/output/analisis_dimensional" \
        --graphics-dir "C:/Python/tesis/output/graficas_rolling_origin" \
        --dpi 300

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
    "arima_111": "ARIMA optimizado",
    "sarima_semanal": "SARIMA semanal optimizado",
}

DATASET_LABELS = {
    "completo": "Completo",
    "reducido": "Reducido",
    "pca": "PCA",
}

EMPIRICAL_MODELS = {"empirico_ultimo_valor", "empirico_promedio_7d"}


@dataclass
class GraphicRecord:
    orden: int
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
    etapa: str = "Evaluación Rolling-Origin"
    estado: str = "generada"


@dataclass
class Context:
    analysis_dir: Path
    graphics_dir: Path
    dpi: int
    top_n: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera gráficas académicas para los modelos con validación Rolling-Origin.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=Path(r"C:/Python/tesis/output/analisis_dimensional"),
        help="Carpeta que contiene los tres Excel de Rolling-Origin.",
    )
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
            logging.FileHandler(graphics_dir / "generacion_rolling_origin.log", mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def target_label(value: str) -> str:
    return TARGET_LABELS.get(value, value.replace("target_", "").replace("_", " ").title())


def model_label(value: str) -> str:
    return MODEL_LABELS.get(value, value.replace("_", " ").title())


def dataset_label(value: str) -> str:
    return DATASET_LABELS.get(value, str(value).title())


def wrap(values, width: int = 32) -> list[str]:
    return ["\n".join(textwrap.wrap(str(value), width=width)) for value in values]


def save(fig: plt.Figure, ctx: Context, filename: str) -> None:
    fig.savefig(ctx.graphics_dir / filename, dpi=ctx.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def record(order: int, title: str, filename: str, sheet: str, variables: str,
           objective: str, interpretation: str, reading: str, equation: str,
           use: str, limitations: str) -> GraphicRecord:
    return GraphicRecord(
        order,
        title,
        filename,
        "05_modelos_rolling_origin_completo/reducido/pca.xlsx",
        sheet,
        variables,
        objective,
        interpretation,
        reading,
        equation,
        use,
        limitations,
    )


def load_outputs(ctx: Context) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    results_frames = []
    ranking_frames = []
    missing = []
    for variant in ["completo", "reducido", "pca"]:
        path = ctx.analysis_dir / f"05_modelos_rolling_origin_{variant}.xlsx"
        if not path.exists():
            missing.append(path.name)
            continue
        with pd.ExcelFile(path) as xls:
            required = {"resultados_por_origen", "ranking_modelos"}
            if not required.issubset(xls.sheet_names):
                raise ValueError(f"{path.name} no contiene las hojas requeridas: {required}")
        results_frames.append(pd.read_excel(path, sheet_name="resultados_por_origen"))
        ranking_frames.append(pd.read_excel(path, sheet_name="ranking_modelos"))
    if not results_frames:
        raise FileNotFoundError("No se encontró ningún archivo 05_modelos_rolling_origin_*.xlsx")

    results = pd.concat(results_frames, ignore_index=True)
    ranking = pd.concat(ranking_frames, ignore_index=True)
    for col in ["mae", "rmse", "mape"]:
        results[col] = pd.to_numeric(results[col], errors="coerce")
    for col in ["mae_promedio", "rmse_promedio", "mape_promedio"]:
        ranking[col] = pd.to_numeric(ranking[col], errors="coerce")
    results["fecha_inicio_prueba"] = pd.to_datetime(results["fecha_inicio_prueba"], errors="coerce")
    results["fecha_fin_prueba"] = pd.to_datetime(results["fecha_fin_prueba"], errors="coerce")
    return results, ranking, missing


def graph_validation_scheme(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    periods = (
        results[["fecha_inicio_prueba", "fecha_fin_prueba"]]
        .drop_duplicates()
        .sort_values("fecha_inicio_prueba")
        .reset_index(drop=True)
    )
    show = periods.iloc[: min(12, len(periods))].copy()
    fig, ax = plt.subplots(figsize=(13, 7))
    for i, row in show.iterrows():
        train_start = show["fecha_inicio_prueba"].min() - pd.Timedelta(days=730)
        train_end = row["fecha_inicio_prueba"] - pd.Timedelta(days=1)
        ax.barh(i, (train_end - train_start).days + 1, left=mdates.date2num(train_start), height=0.55,
                label="Entrenamiento" if i == 0 else None)
        ax.barh(i, (row["fecha_fin_prueba"] - row["fecha_inicio_prueba"]).days + 1,
                left=mdates.date2num(row["fecha_inicio_prueba"]), height=0.55,
                label="Prueba" if i == 0 else None)
    ax.set_yticks(range(len(show)), [f"Origen {i+1}" for i in range(len(show))])
    ax.invert_yaxis()
    ax.xaxis_date()
    locator = mdates.AutoDateLocator(minticks=5, maxticks=9)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.set_title("Esquema de validación temporal Rolling-Origin")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Ventana de evaluación")
    ax.legend()
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "01_esquema_validacion_rolling_origin.png"
    save(fig, ctx, filename)
    return record(
        1, "Esquema de validación Rolling-Origin", filename, "resultados_por_origen",
        "fecha_inicio_prueba, fecha_fin_prueba",
        "Representar la expansión secuencial del entrenamiento y la evaluación sobre bloques futuros de 30 días.",
        "Cada fila corresponde a un origen distinto. La región de entrenamiento utiliza únicamente el pasado y la región de prueba contiene observaciones posteriores.",
        "Las ventanas se desplazan cronológicamente; nunca se mezclan aleatoriamente observaciones pasadas y futuras.",
        r"Train_o=\{1,\ldots,t_o\},\qquad Test_o=\{t_o+1,\ldots,t_o+h\}",
        "Sección de validación temporal estricta y diseño experimental.",
        "La figura muestra solamente los primeros orígenes para conservar legibilidad; el archivo contiene todas las ventanas.",
    )


def graph_origin_coverage(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    summary = (
        results.groupby(["dataset", "target"], as_index=False)
        .agg(origenes=("fecha_inicio_prueba", "nunique"), inicio=("fecha_inicio_prueba", "min"), fin=("fecha_fin_prueba", "max"))
    )
    pivot = summary.pivot(index="target", columns="dataset", values="origenes")
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    x = np.arange(len(pivot.index))
    width = 0.24
    for idx, dataset in enumerate(pivot.columns):
        values = pivot[dataset].fillna(0).values
        ax.bar(x + (idx - (len(pivot.columns)-1)/2) * width, values, width, label=dataset_label(dataset))
    ax.set_xticks(x, wrap([target_label(v) for v in pivot.index], 20))
    ax.set_ylabel("Número de orígenes evaluados")
    ax.set_title("Cobertura de ventanas Rolling-Origin por objetivo y dataset")
    ax.legend()
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    filename = "02_cobertura_origenes_por_objetivo.png"
    save(fig, ctx, filename)
    return record(
        2, "Cobertura de orígenes por objetivo", filename, "resultados_por_origen",
        "dataset, target, fecha_inicio_prueba",
        "Verificar que todos los objetivos y variantes se evaluaron con la misma cantidad de ventanas temporales.",
        "Barras iguales indican un diseño balanceado y hacen comparable el promedio de errores entre variantes.",
        "Una diferencia en el número de orígenes debe investigarse antes de comparar métricas promedio.",
        r"O_{d,y}=\left|\{o:(d,y,o)\text{ fue evaluado}\}\right|",
        "Auditoría del diseño experimental y reproducibilidad.",
        "La igualdad en el número de ventanas no garantiza igualdad de dificultad entre objetivos.",
    )


def graph_rmse_ranking(ctx: Context, ranking: pd.DataFrame) -> GraphicRecord:
    targets = list(ranking["target"].dropna().unique())
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    axes = axes.ravel()
    for ax, target in zip(axes, targets):
        subset = ranking[ranking.target == target].copy()
        subset["etiqueta"] = subset["modelo"].map(model_label) + " — " + subset["dataset"].map(dataset_label)
        subset = subset.sort_values("rmse_promedio").head(ctx.top_n).sort_values("rmse_promedio")
        ax.barh(wrap(subset.etiqueta, 30), subset.rmse_promedio)
        ax.set_title(target_label(target))
        ax.set_xlabel("RMSE promedio")
        ax.grid(axis="x", alpha=0.22)
    for ax in axes[len(targets):]:
        ax.axis("off")
    fig.suptitle("Ranking de modelos por RMSE promedio", fontsize=15)
    fig.tight_layout()
    filename = "03_ranking_rmse_por_objetivo.png"
    save(fig, ctx, filename)
    return record(
        3, "Ranking por RMSE promedio", filename, "ranking_modelos",
        "dataset, target, modelo, rmse_promedio",
        "Comparar el desempeño promedio de todos los modelos y representaciones para cada variable objetivo.",
        "Las barras más cortas corresponden a menor penalización cuadrática de errores y, por tanto, mejor desempeño bajo RMSE.",
        "La comparación debe realizarse dentro de cada objetivo porque las escalas monetarias y operativas son diferentes.",
        r"RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}",
        "Resultados comparativos de modelos y selección del candidato principal.",
        "RMSE es sensible a errores extremos y no expresa por sí solo estabilidad temporal.",
    )


def graph_best_model_matrix(ctx: Context, ranking: pd.DataFrame) -> GraphicRecord:
    best = ranking.loc[ranking.groupby(["dataset", "target"])["rmse_promedio"].idxmin()].copy()
    targets = sorted(best.target.unique())
    datasets = [d for d in ["completo", "reducido", "pca"] if d in best.dataset.unique()]
    matrix = np.zeros((len(targets), len(datasets)))
    annotations = np.empty_like(matrix, dtype=object)
    for i, target in enumerate(targets):
        for j, dataset in enumerate(datasets):
            row = best[(best.target == target) & (best.dataset == dataset)]
            if row.empty:
                matrix[i, j] = np.nan
                annotations[i, j] = "Sin dato"
            else:
                matrix[i, j] = row.rmse_promedio.iloc[0]
                annotations[i, j] = model_label(row.modelo.iloc[0]) + f"\nRMSE={row.rmse_promedio.iloc[0]:.3g}"
    norm = matrix.copy()
    for i in range(norm.shape[0]):
        vals = norm[i]
        finite = np.isfinite(vals)
        if finite.any() and np.nanmax(vals) > np.nanmin(vals):
            norm[i, finite] = (vals[finite] - np.nanmin(vals)) / (np.nanmax(vals) - np.nanmin(vals))
        else:
            norm[i, finite] = 0
    fig, ax = plt.subplots(figsize=(11.5, 8))
    im = ax.imshow(norm, aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(datasets)), [dataset_label(d) for d in datasets])
    ax.set_yticks(range(len(targets)), wrap([target_label(t) for t in targets], 24))
    ax.set_title("Mejor modelo por objetivo y variante del dataset")
    for i in range(len(targets)):
        for j in range(len(datasets)):
            text_color = "white" if np.isfinite(norm[i, j]) and norm[i, j] < 0.45 else "black"
            ax.text(
                j, i, annotations[i, j], ha="center", va="center", fontsize=8,
                color=text_color,
            )
    fig.colorbar(im, ax=ax, label="RMSE relativo dentro del objetivo")
    fig.tight_layout()
    filename = "04_mejor_modelo_por_dataset_objetivo.png"
    save(fig, ctx, filename)
    return record(
        4, "Mejor modelo por dataset y objetivo", filename, "ranking_modelos",
        "dataset, target, modelo, rmse_promedio",
        "Resumir qué algoritmo obtiene el menor RMSE para cada combinación de representación y objetivo.",
        "Cada celda muestra el nombre del ganador y su RMSE. La intensidad se normaliza por objetivo para evitar comparar escalas incompatibles.",
        "Debe observarse tanto la repetición del modelo ganador como la sensibilidad a la representación completa, reducida o PCA.",
        r"m^*_{d,y}=\arg\min_m RMSE_{d,y,m}",
        "Síntesis ejecutiva de resultados predictivos.",
        "Un ganador por promedio puede no ser el más estable en todas las ventanas.",
    )


def graph_improvement_baseline(ctx: Context, ranking: pd.DataFrame) -> GraphicRecord:
    baseline = ranking[ranking.modelo == "empirico_promedio_7d"][["dataset", "target", "rmse_promedio"]].rename(columns={"rmse_promedio": "rmse_base"})
    work = ranking.merge(baseline, on=["dataset", "target"], how="left")
    work["mejora_pct"] = (work.rmse_base - work.rmse_promedio) / work.rmse_base * 100
    best = work.loc[work.groupby(["dataset", "target"])["mejora_pct"].idxmax()].copy()
    best["etiqueta"] = best.target.map(target_label) + " — " + best.dataset.map(dataset_label)
    best = best.sort_values("mejora_pct")
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.barh(wrap(best.etiqueta, 36), best.mejora_pct)
    ax.axvline(0, linewidth=1)
    ax.set_title("Mejora del mejor modelo frente al promedio empírico de 7 días")
    ax.set_xlabel("Reducción relativa de RMSE (%)")
    ax.grid(axis="x", alpha=0.22)
    for i, row in best.reset_index(drop=True).iterrows():
        ax.text(row.mejora_pct, i, f" {model_label(row.modelo)} ({row.mejora_pct:.1f}%)", va="center", fontsize=8)
    fig.tight_layout()
    filename = "05_mejora_frente_linea_base_empirica.png"
    save(fig, ctx, filename)
    return record(
        5, "Mejora frente a la línea base empírica", filename, "ranking_modelos",
        "rmse_promedio del modelo y del promedio empírico de 7 días",
        "Cuantificar si los modelos avanzados aportan una mejora real respecto al método empírico de referencia.",
        "Valores positivos indican reducción del error; valores negativos significan que la línea base empírica fue superior.",
        "La magnitud relativa facilita comparar objetivos con escalas distintas.",
        r"Mejora(\%)=\frac{RMSE_{base}-RMSE_m}{RMSE_{base}}\times100",
        "Contraste entre posprueba analítica y método de control.",
        "La mejora porcentual puede ser inestable cuando el error base es muy pequeño.",
    )


def graph_mae_rmse(ctx: Context, ranking: pd.DataFrame) -> GraphicRecord:
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    targets = list(ranking.target.unique())
    for ax, target in zip(axes.ravel(), targets):
        sub = ranking[ranking.target == target]
        for dataset, group in sub.groupby("dataset"):
            ax.scatter(group.mae_promedio, group.rmse_promedio, label=dataset_label(dataset), alpha=0.8)
        finite = sub[["mae_promedio", "rmse_promedio"]].replace([np.inf, -np.inf], np.nan).dropna()
        if not finite.empty:
            lim = max(finite.max()) * 1.05
            ax.plot([0, lim], [0, lim], linestyle="--", linewidth=1)
        ax.set_title(target_label(target))
        ax.set_xlabel("MAE promedio")
        ax.set_ylabel("RMSE promedio")
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8)
    fig.suptitle("Relación entre MAE y RMSE por modelo", fontsize=15)
    fig.tight_layout()
    filename = "06_relacion_mae_rmse_modelos.png"
    save(fig, ctx, filename)
    return record(
        6, "Relación MAE–RMSE", filename, "ranking_modelos",
        "mae_promedio, rmse_promedio",
        "Evaluar si el desempeño está condicionado por errores extremos además del error absoluto típico.",
        "Cuanto mayor sea la separación vertical respecto a la diagonal MAE=RMSE, mayor es el efecto de errores grandes.",
        "Modelos cercanos al origen presentan menor error en ambas métricas.",
        r"MAE=\frac{1}{n}\sum|e_i|,\qquad RMSE=\sqrt{\frac{1}{n}\sum e_i^2}",
        "Discusión de métricas y costo de errores extremos.",
        "MAE y RMSE mantienen las unidades del objetivo, por lo que no deben compararse entre objetivos distintos.",
    )


def graph_metric_rank_agreement(ctx: Context, ranking: pd.DataFrame) -> GraphicRecord:
    rows = []
    for (dataset, target), group in ranking.groupby(["dataset", "target"]):
        group = group.copy()
        for metric in ["mae_promedio", "rmse_promedio", "mape_promedio"]:
            group[f"rank_{metric}"] = group[metric].rank(method="average", ascending=True, na_option="bottom")
        corr = group[["rank_mae_promedio", "rank_rmse_promedio", "rank_mape_promedio"]].corr(method="spearman")
        rows.append(corr)
    mean_corr = sum(rows) / len(rows)
    labels = ["MAE", "RMSE", "MAPE"]
    fig, ax = plt.subplots(figsize=(7.8, 6.8))
    im = ax.imshow(mean_corr.values, vmin=-1, vmax=1)
    ax.set_xticks(range(3), labels)
    ax.set_yticks(range(3), labels)
    ax.set_title("Concordancia promedio entre rankings de métricas")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{mean_corr.iloc[i, j]:.2f}", ha="center", va="center")
    fig.colorbar(im, ax=ax, label="Correlación de rangos de Spearman")
    fig.tight_layout()
    filename = "07_concordancia_rankings_metricas.png"
    save(fig, ctx, filename)
    return record(
        7, "Concordancia entre métricas", filename, "ranking_modelos",
        "rankings de MAE, RMSE y MAPE",
        "Determinar si las métricas conducen a conclusiones semejantes sobre el orden de los modelos.",
        "Valores altos indican que dos métricas ordenan de forma parecida; valores bajos revelan criterios de evaluación diferentes.",
        "Una baja concordancia con MAPE puede asociarse con objetivos que contienen ceros o valores pequeños.",
        r"\rho_s=Corr(rank(M_a),rank(M_b))",
        "Justificación de una evaluación multicriterio.",
        "El promedio resume múltiples objetivos y datasets, por lo que puede ocultar desacuerdos particulares.",
    )


def graph_temporal_rmse(ctx: Context, results: pd.DataFrame, ranking: pd.DataFrame) -> GraphicRecord:
    winners = ranking.loc[ranking.groupby(["dataset", "target"])["rmse_promedio"].idxmin()][["dataset", "target", "modelo"]]
    selected = results.merge(winners, on=["dataset", "target", "modelo"], how="inner")
    targets = list(selected.target.unique())
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    for ax, target in zip(axes.ravel(), targets):
        sub = selected[selected.target == target]
        for dataset, group in sub.groupby("dataset"):
            group = group.sort_values("fecha_inicio_prueba")
            ax.plot(group.fecha_inicio_prueba, group.rmse, marker="o", markersize=3, label=dataset_label(dataset))
        locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.set_title(target_label(target))
        ax.set_ylabel("RMSE por origen")
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8)
    fig.suptitle("Evolución temporal del RMSE del mejor modelo", fontsize=15)
    fig.tight_layout()
    filename = "08_evolucion_temporal_rmse_ganadores.png"
    save(fig, ctx, filename)
    return record(
        8, "Evolución temporal del RMSE", filename, "resultados_por_origen y ranking_modelos",
        "fecha_inicio_prueba, rmse del modelo ganador",
        "Evaluar la estabilidad del modelo ganador a través de diferentes periodos futuros.",
        "Picos de RMSE identifican ventanas difíciles, cambios de régimen o eventos no capturados por el modelo.",
        "Una línea baja y estable es preferible a un promedio bajo acompañado de episodios extremos.",
        r"RMSE_o=\sqrt{\frac{1}{h}\sum_{i=1}^{h}(y_{o,i}-\hat y_{o,i})^2}",
        "Análisis de robustez temporal y riesgo predictivo.",
        "La figura sigue al ganador promedio; otro modelo podría superar al ganador en ventanas específicas.",
    )


def graph_rmse_distribution(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    model_order = list(results.groupby("modelo").rmse.median().sort_values().index)
    data = [results.loc[results.modelo == model, "rmse"].dropna().values for model in model_order]
    fig, ax = plt.subplots(figsize=(13.5, 7.5))
    ax.boxplot(data, tick_labels=wrap([model_label(m) for m in model_order], 18), showfliers=False)
    ax.set_title("Distribución del RMSE por modelo en todas las ventanas")
    ax.set_ylabel("RMSE por origen")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    filename = "09_distribucion_rmse_por_modelo.png"
    save(fig, ctx, filename)
    return record(
        9, "Distribución del RMSE por modelo", filename, "resultados_por_origen",
        "modelo, rmse",
        "Comparar mediana, dispersión y asimetría del error a lo largo de todos los orígenes.",
        "La línea central es la mediana; la caja representa el 50 % central de errores. Cajas más compactas indican mayor estabilidad.",
        "La comparación global mezcla objetivos de distintas escalas y debe complementarse con las figuras por objetivo.",
        r"IQR_{RMSE}=Q_{0.75}(RMSE)-Q_{0.25}(RMSE)",
        "Discusión de estabilidad y variabilidad del desempeño.",
        "Al mezclar escalas, los objetivos monetarios tienen mayor peso visual que los objetivos de conteo.",
    )


def graph_stability_cv(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    stability = (
        results.groupby(["dataset", "target", "modelo"], as_index=False)
        .agg(media_rmse=("rmse", "mean"), desviacion_rmse=("rmse", "std"))
    )
    stability["cv_rmse"] = stability.desviacion_rmse / stability.media_rmse.replace(0, np.nan)
    best_stable = stability.sort_values("cv_rmse").groupby(["dataset", "target"], as_index=False).first()
    best_stable["etiqueta"] = best_stable.target.map(target_label) + " — " + best_stable.dataset.map(dataset_label)
    best_stable = best_stable.sort_values("cv_rmse")
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.barh(wrap(best_stable.etiqueta, 36), best_stable.cv_rmse)
    ax.set_title("Modelo más estable por objetivo y dataset")
    ax.set_xlabel("Coeficiente de variación del RMSE")
    ax.grid(axis="x", alpha=0.22)
    for i, row in best_stable.reset_index(drop=True).iterrows():
        ax.text(row.cv_rmse, i, f" {model_label(row.modelo)}", va="center", fontsize=8)
    fig.tight_layout()
    filename = "10_estabilidad_modelos_cv_rmse.png"
    save(fig, ctx, filename)
    return record(
        10, "Estabilidad mediante coeficiente de variación", filename, "resultados_por_origen",
        "media y desviación estándar del RMSE",
        "Identificar el modelo con menor variabilidad relativa del error en cada problema.",
        "Valores pequeños indican que el error cambia menos entre ventanas respecto a su nivel promedio.",
        "Debe analizarse junto con el RMSE medio, porque un modelo estable puede ser consistentemente impreciso.",
        r"CV_{RMSE}=\frac{s(RMSE_o)}{\overline{RMSE}_o}",
        "Evaluación de robustez y riesgo operativo.",
        "El CV puede ser inestable cuando el RMSE medio se aproxima a cero.",
    )


def graph_win_counts(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    idx = results.groupby(["dataset", "target", "fecha_inicio_prueba"])["rmse"].idxmin()
    wins = results.loc[idx].groupby("modelo").size().sort_values()
    fig, ax = plt.subplots(figsize=(10.5, 6.8))
    ax.barh(wrap([model_label(m) for m in wins.index], 25), wins.values)
    ax.set_title("Número de ventanas ganadas por modelo")
    ax.set_xlabel("Orígenes con menor RMSE")
    ax.grid(axis="x", alpha=0.22)
    for i, value in enumerate(wins.values):
        ax.text(value, i, f" {int(value)}", va="center")
    fig.tight_layout()
    filename = "11_ventanas_ganadas_por_modelo.png"
    save(fig, ctx, filename)
    return record(
        11, "Ventanas ganadas por modelo", filename, "resultados_por_origen",
        "modelo y RMSE mínimo por origen",
        "Medir con qué frecuencia cada modelo fue el mejor en una ventana temporal concreta.",
        "Un alto número de victorias indica capacidad de adaptación a distintos periodos, aunque no considera la magnitud de las derrotas.",
        "Debe contrastarse con el RMSE promedio y la estabilidad.",
        r"W_m=\sum_o I\left(m=\arg\min_j RMSE_{j,o}\right)",
        "Comparación dinámica de modelos.",
        "Los empates numéricos se asignan al primer mínimo encontrado.",
    )


def graph_dataset_sensitivity(ctx: Context, ranking: pd.DataFrame) -> GraphicRecord:
    work = ranking.copy()
    work["rmse_relativo"] = work.groupby("target")["rmse_promedio"].transform(lambda s: s / s.min())
    pivot = work.pivot_table(index="modelo", columns="dataset", values="rmse_relativo", aggfunc="mean")
    pivot = pivot.reindex([m for m in MODEL_LABELS if m in pivot.index])
    fig, ax = plt.subplots(figsize=(10, 7.5))
    im = ax.imshow(pivot.values, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), [dataset_label(c) for c in pivot.columns])
    ax.set_yticks(range(len(pivot.index)), wrap([model_label(i) for i in pivot.index], 24))
    ax.set_title("Sensibilidad del desempeño a la representación del dataset")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = pivot.iloc[i, j]
            ax.text(j, i, "—" if pd.isna(value) else f"{value:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, label="RMSE relativo promedio")
    fig.tight_layout()
    filename = "12_sensibilidad_modelos_dataset.png"
    save(fig, ctx, filename)
    return record(
        12, "Sensibilidad a la representación del dataset", filename, "ranking_modelos",
        "modelo, dataset, rmse_promedio normalizado",
        "Evaluar si un modelo mejora o empeora al utilizar predictores completos, seleccionados o componentes PCA.",
        "Valores cercanos a uno indican proximidad al mejor resultado del objetivo; valores mayores representan pérdida relativa de desempeño.",
        "Las líneas base y modelos univariados pueden mostrar resultados idénticos porque no usan los predictores exógenos.",
        r"RMSE^{rel}_{d,y,m}=\frac{RMSE_{d,y,m}}{\min_{d,m}RMSE_{d,y,m}}",
        "Comparación entre dataset completo, reducido y PCA.",
        "El promedio entre objetivos resume escalas después de normalizar, pero puede ocultar efectos específicos.",
    )


def graph_empirical_vs_advanced(ctx: Context, ranking: pd.DataFrame) -> GraphicRecord:
    work = ranking.copy()
    work["familia"] = np.where(work.modelo.isin(EMPIRICAL_MODELS), "Métodos empíricos", "Modelos avanzados")
    best = (
        work.sort_values("rmse_promedio")
        .groupby(["dataset", "target", "familia"], as_index=False)
        .first()
    )
    pivot = best.pivot_table(index=["dataset", "target"], columns="familia", values="rmse_promedio")
    pivot = pivot.dropna()
    labels = [f"{target_label(t)} — {dataset_label(d)}" for d, t in pivot.index]
    y = np.arange(len(pivot))
    fig, ax = plt.subplots(figsize=(12.5, 8))
    ax.plot(pivot["Métodos empíricos"], y, "o", label="Mejor empírico")
    ax.plot(pivot["Modelos avanzados"], y, "o", label="Mejor avanzado")
    for i in range(len(pivot)):
        ax.plot([pivot.iloc[i]["Métodos empíricos"], pivot.iloc[i]["Modelos avanzados"]], [i, i], linewidth=1)
    ax.set_yticks(y, wrap(labels, 38))
    ax.set_xlabel("RMSE promedio")
    ax.set_title("Mejor método empírico frente al mejor modelo avanzado")
    ax.legend()
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "13_empirico_vs_modelos_avanzados.png"
    save(fig, ctx, filename)
    return record(
        13, "Método empírico frente a modelos avanzados", filename, "ranking_modelos",
        "mejor rmse_promedio por familia",
        "Contrastar directamente la línea base operativa con el mejor enfoque estadístico o de aprendizaje automático.",
        "El punto más cercano a cero identifica la familia superior. Segmentos cortos indican que la complejidad adicional produce poca ganancia.",
        "La comparación se realiza por objetivo y dataset para mantener la escala.",
        r"\Delta RMSE=RMSE^*_{empírico}-RMSE^*_{avanzado}",
        "Contraste del grupo de control frente a la intervención analítica.",
        "La categoría avanzada agrupa modelos con supuestos y complejidad muy diferentes.",
    )


def graph_mape_diagnostics(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    diag = (
        results.groupby(["target", "modelo"], as_index=False)
        .agg(mape_mediana=("mape", "median"), mape_p95=("mape", lambda s: s.quantile(.95)),
             porcentaje_no_finito=("mape", lambda s: 100 * (~np.isfinite(s)).mean()))
    )
    targets = list(diag.target.unique())
    fig, axes = plt.subplots(2, 2, figsize=(15, 10.5))
    for ax, target in zip(axes.ravel(), targets):
        sub = diag[diag.target == target].sort_values("mape_mediana")
        ax.barh(wrap(sub.modelo.map(model_label), 22), sub.mape_mediana)
        ax.set_title(target_label(target))
        ax.set_xlabel("MAPE mediana (%)")
        ax.grid(axis="x", alpha=0.22)
    fig.suptitle("Diagnóstico de estabilidad del MAPE", fontsize=15)
    fig.tight_layout()
    filename = "14_diagnostico_mape_por_objetivo.png"
    save(fig, ctx, filename)
    return record(
        14, "Diagnóstico del MAPE", filename, "resultados_por_origen",
        "target, modelo, mape",
        "Mostrar la sensibilidad del error porcentual ante objetivos con ceros o valores pequeños.",
        "MAPE elevado o no finito puede reflejar denominadores cercanos a cero más que un deterioro proporcional ordinario.",
        "Para series intermitentes deben priorizarse MAE y RMSE y considerar métricas complementarias como WAPE, sMAPE o MASE.",
        r"MAPE=\frac{100}{n}\sum_i\left|\frac{y_i-\hat y_i}{y_i}\right|",
        "Discusión crítica de métricas de evaluación.",
        "La implementación excluye denominadores cercanos a cero; aun así, valores pequeños pueden inflar el porcentaje.",
    )


def graph_critical_origins(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    best_origin = results.groupby(["dataset", "target", "fecha_inicio_prueba"], as_index=False).rmse.min()
    critical = best_origin.sort_values("rmse", ascending=False).head(ctx.top_n).copy()
    critical["etiqueta"] = critical.fecha_inicio_prueba.dt.strftime("%Y-%m-%d") + "\n" + critical.target.map(target_label) + " — " + critical.dataset.map(dataset_label)
    critical = critical.sort_values("rmse")
    fig, ax = plt.subplots(figsize=(12.5, 8))
    ax.barh(wrap(critical.etiqueta, 42), critical.rmse)
    ax.set_title(f"Ventanas temporales más difíciles aun con el mejor modelo (Top {len(critical)})")
    ax.set_xlabel("Menor RMSE disponible en el origen")
    ax.grid(axis="x", alpha=0.22)
    fig.tight_layout()
    filename = "15_origenes_temporales_mas_dificiles.png"
    save(fig, ctx, filename)
    return record(
        15, "Orígenes temporales más difíciles", filename, "resultados_por_origen",
        "mínimo RMSE por dataset, objetivo y fecha de inicio",
        "Detectar periodos donde todos los modelos enfrentaron mayor dificultad predictiva.",
        "Una barra extensa indica que incluso el mejor algoritmo disponible cometió errores elevados en esa ventana.",
        "Estas fechas deben contrastarse con eventos comerciales, cambios operativos, datos atípicos o rupturas estructurales.",
        r"D_o=\min_m RMSE_{m,o}",
        "Análisis de errores, eventos atípicos y limitaciones del modelo.",
        "Los valores monetarios dominan por escala; la interpretación debe realizarse dentro del objetivo correspondiente.",
    )


def graph_multicriteria_score(ctx: Context, ranking: pd.DataFrame) -> GraphicRecord:
    work = ranking.copy()
    metrics = ["mae_promedio", "rmse_promedio", "mape_promedio"]
    for metric in metrics:
        work[f"norm_{metric}"] = work.groupby(["dataset", "target"])[metric].transform(
            lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else 0
        )
    work["score_multicriterio"] = work[[f"norm_{m}" for m in metrics]].mean(axis=1, skipna=True)
    best = work.sort_values("score_multicriterio").groupby(["dataset", "target"], as_index=False).first()
    best["etiqueta"] = best.target.map(target_label) + " — " + best.dataset.map(dataset_label)
    best = best.sort_values("score_multicriterio")
    fig, ax = plt.subplots(figsize=(12, 7.5))
    ax.barh(wrap(best.etiqueta, 38), best.score_multicriterio)
    ax.set_title("Modelo ganador mediante score multicriterio normalizado")
    ax.set_xlabel("Score promedio normalizado (menor es mejor)")
    ax.grid(axis="x", alpha=0.22)
    for i, row in best.reset_index(drop=True).iterrows():
        ax.text(row.score_multicriterio, i, f" {model_label(row.modelo)}", va="center", fontsize=8)
    fig.tight_layout()
    filename = "16_score_multicriterio_modelos.png"
    save(fig, ctx, filename)
    return record(
        16, "Score multicriterio de modelos", filename, "ranking_modelos",
        "MAE, RMSE y MAPE normalizados",
        "Integrar las tres métricas en una síntesis comparable dentro de cada objetivo y dataset.",
        "Un score menor indica un balance más favorable entre error absoluto, penalización cuadrática y error relativo.",
        "El resultado debe contrastarse con estabilidad temporal y mejora frente a la línea base.",
        r"S_m=\frac{1}{3}\left(MAE_m^{norm}+RMSE_m^{norm}+MAPE_m^{norm}\right)",
        "Selección multicriterio del modelo candidato.",
        "La ponderación es uniforme y MAPE puede ser poco fiable en series con ceros; el score es una síntesis exploratoria.",
    )


def write_manifest(ctx: Context, records: list[GraphicRecord], missing: list[str]) -> None:
    ordered = sorted(records, key=lambda r: r.orden)
    index = pd.DataFrame([asdict(r) for r in ordered])
    index.to_csv(ctx.graphics_dir / "INDICE_GRAFICAS_ROLLING_ORIGIN.csv", index=False, encoding="utf-8-sig")

    payload = {
        "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
        "etapa": "Modelos estadísticos y ML con validación Rolling-Origin",
        "archivos_faltantes": missing,
        "numero_graficas": len(ordered),
        "graficas": [asdict(r) for r in ordered],
    }
    (ctx.graphics_dir / "MANIFIESTO_ROLLING_ORIGIN.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Manifiesto académico de gráficas Rolling-Origin",
        "",
        f"Fecha de generación: {payload['fecha_generacion']}",
        "",
        "## Propósito metodológico",
        "",
        "Documentar la comparación de métodos empíricos, modelos estadísticos y algoritmos de aprendizaje automático mediante particiones temporales expansivas. Las figuras deben interpretarse por objetivo y complementarse entre sí: precisión promedio, estabilidad, frecuencia de victorias y mejora frente a la línea base.",
        "",
        "## Ecuaciones centrales",
        "",
        r"- $MAE=\frac{1}{n}\sum_{i=1}^{n}|y_i-\hat y_i|$",
        r"- $RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}$",
        r"- $MAPE=\frac{100}{n}\sum_{i=1}^{n}|(y_i-\hat y_i)/y_i|$",
        r"- $Train_o=\{1,\ldots,t_o\}$ y $Test_o=\{t_o+1,\ldots,t_o+h\}$",
        "",
    ]
    if missing:
        lines += ["## Archivos no encontrados", "", *[f"- {name}" for name in missing], ""]
    for r in ordered:
        lines += [
            f"## Figura {r.orden}. {r.titulo}", "",
            f"- **Archivo:** `{r.archivo}`",
            f"- **Fuente:** {r.fuente}",
            f"- **Hoja:** {r.hoja}",
            f"- **Variables:** {r.variables_utilizadas}",
            f"- **Objetivo académico:** {r.objetivo}",
            f"- **Interpretación:** {r.interpretacion}",
            f"- **Criterio de lectura:** {r.criterio_lectura}",
            f"- **Ecuación o fundamento:** `{r.ecuacion_o_fundamento}`",
            f"- **Uso sugerido en la tesis:** {r.uso_tesis}",
            f"- **Limitaciones:** {r.limitaciones}", "",
        ]
    (ctx.graphics_dir / "MANIFIESTO_ROLLING_ORIGIN.md").write_text("\n".join(lines), encoding="utf-8")


def write_summary(ctx: Context, results: pd.DataFrame, ranking: pd.DataFrame, records: list[GraphicRecord]) -> None:
    winners = ranking.loc[ranking.groupby(["dataset", "target"])["rmse_promedio"].idxmin()].copy()
    stability = (
        results.groupby(["dataset", "target", "modelo"], as_index=False)
        .agg(rmse_media=("rmse", "mean"), rmse_std=("rmse", "std"), rmse_mediana=("rmse", "median"),
             rmse_p95=("rmse", lambda s: s.quantile(.95)), origenes=("fecha_inicio_prueba", "nunique"))
    )
    stability["cv_rmse"] = stability.rmse_std / stability.rmse_media.replace(0, np.nan)
    with pd.ExcelWriter(ctx.graphics_dir / "RESUMEN_ESTADISTICO_ROLLING_ORIGIN.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([asdict(r) for r in records]).to_excel(writer, sheet_name="indice_graficas", index=False)
        results.to_excel(writer, sheet_name="resultados_consolidados", index=False)
        ranking.to_excel(writer, sheet_name="ranking_consolidado", index=False)
        winners.to_excel(writer, sheet_name="ganadores_rmse", index=False)
        stability.to_excel(writer, sheet_name="estabilidad_rmse", index=False)


def main() -> None:
    args = parse_args()
    graphics_dir = args.graphics_dir or (args.analysis_dir / "graficas_rolling_origin")
    ctx = Context(args.analysis_dir, graphics_dir, args.dpi, args.top_n)
    configure_logging(graphics_dir)
    results, ranking, missing = load_outputs(ctx)
    if missing and not args.continuar_con_faltantes:
        raise FileNotFoundError("Faltan archivos: " + ", ".join(missing))

    generators: list[Callable[[], GraphicRecord]] = [
        lambda: graph_validation_scheme(ctx, results),
        lambda: graph_origin_coverage(ctx, results),
        lambda: graph_rmse_ranking(ctx, ranking),
        lambda: graph_best_model_matrix(ctx, ranking),
        lambda: graph_improvement_baseline(ctx, ranking),
        lambda: graph_mae_rmse(ctx, ranking),
        lambda: graph_metric_rank_agreement(ctx, ranking),
        lambda: graph_temporal_rmse(ctx, results, ranking),
        lambda: graph_rmse_distribution(ctx, results),
        lambda: graph_stability_cv(ctx, results),
        lambda: graph_win_counts(ctx, results),
        lambda: graph_dataset_sensitivity(ctx, ranking),
        lambda: graph_empirical_vs_advanced(ctx, ranking),
        lambda: graph_mape_diagnostics(ctx, results),
        lambda: graph_critical_origins(ctx, results),
        lambda: graph_multicriteria_score(ctx, ranking),
    ]

    records = []
    for generator in generators:
        try:
            rec = generator()
            records.append(rec)
            logging.info("Generada: %s", rec.archivo)
        except Exception as exc:
            logging.exception("Error al generar una figura: %s", exc)
            if not args.continuar_con_faltantes:
                raise

    write_manifest(ctx, records, missing)
    write_summary(ctx, results, ranking, records)
    logging.info("Proceso terminado. Figuras generadas: %s", len(records))
    print(f"Carpeta generada: {graphics_dir}")
    print(f"Figuras generadas: {len(records)}")


if __name__ == "__main__":
    main()
