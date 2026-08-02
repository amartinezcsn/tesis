from __future__ import annotations

"""
CÓDIGO 11 — GRÁFICAS ACADÉMICAS PARA RNN Y LSTM
=================================================

Genera evidencia visual y un manifiesto académico a partir de:
- 06_rnn_lstm_reducido.xlsx
- 06_rnn_lstm_pca.xlsx
- 03_dataset_reducido_por_seleccion.xlsx (opcional, para estructura de entrada)
- 04_dataset_pca_componentes.xlsx (opcional, para estructura de entrada)

Salidas:
- 16 figuras PNG.
- MANIFIESTO_RNN_LSTM.md y .json.
- INDICE_GRAFICAS_RNN_LSTM.csv.
- RESUMEN_ESTADISTICO_RNN_LSTM.xlsx.

Ejemplo:
python 11_generar_graficas_rnn_lstm.py \
  --analysis-dir "C:/Python/tesis/output/analisis_dimensional" \
  --graphics-dir "C:/Python/tesis/output/graficas_rnn_lstm" \
  --dpi 300
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

LOOKBACK_DAYS = 28
TEST_DAYS = 90
EPOCHS = 80
BATCH_SIZE = 16
TARGETS = [
    "target_ventas_importe_real_2026_05",
    "target_compras_total_real_2026_05",
    "target_ventas_registros",
    "target_compras_registros",
]
TARGET_LABELS = {
    "target_ventas_importe_real_2026_05": "Importe de ventas",
    "target_compras_total_real_2026_05": "Importe de compras",
    "target_ventas_registros": "Registros de ventas",
    "target_compras_registros": "Registros de compras",
}
MODEL_LABELS = {"rnn_simple": "RNN simple", "lstm": "LSTM"}
DATASET_LABELS = {"reducido": "Dataset reducido", "pca": "Dataset PCA", "completo": "Dataset completo"}


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
    analysis_dir: Path
    graphics_dir: Path
    dpi: int
    top_n: int
    continuar: bool


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Genera gráficas académicas para la etapa RNN/LSTM.")
    p.add_argument("--analysis-dir", type=Path, default=Path(r"C:/Python/tesis/output/analisis_dimensional"))
    p.add_argument("--graphics-dir", type=Path, default=None)
    p.add_argument("--dpi", type=int, default=220)
    p.add_argument("--top-n", type=int, default=12)
    p.add_argument("--continuar-con-faltantes", action="store_true")
    return p.parse_args()


def configure_logging(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(path / "generacion_rnn_lstm.log", mode="w", encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )


def save(fig: plt.Figure, ctx: Context, filename: str) -> None:
    fig.savefig(ctx.graphics_dir / filename, dpi=ctx.dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def wrap(values, width=28):
    return ["\n".join(textwrap.wrap(str(v), width=width)) for v in values]


def target_label(value: str) -> str:
    return TARGET_LABELS.get(value, value.replace("target_", "").replace("_", " ").title())


def model_label(value: str) -> str:
    return MODEL_LABELS.get(value, value.replace("_", " ").title())


def dataset_label(value: str) -> str:
    return DATASET_LABELS.get(value, str(value).title())


def find_file(ctx: Context, filename: str) -> Path:
    candidates = [ctx.analysis_dir / filename, Path.cwd() / filename, Path("/mnt/data") / filename]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(filename)


def load_results(ctx: Context) -> pd.DataFrame:
    frames = []
    for variant in ["reducido", "pca", "completo"]:
        filename = f"06_rnn_lstm_{variant}.xlsx"
        try:
            path = find_file(ctx, filename)
        except FileNotFoundError:
            if ctx.continuar:
                logging.warning("No se encontró %s", filename)
                continue
            if variant == "completo":
                continue
            raise
        df = pd.read_excel(path)
        required = {"dataset", "target", "modelo", "mae", "rmse", "mape"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{filename} no contiene columnas requeridas: {sorted(missing)}")
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No se encontró ningún archivo 06_rnn_lstm_*.xlsx")
    out = pd.concat(frames, ignore_index=True)
    for c in ["mae", "rmse", "mape"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def load_variant_dataset(ctx: Context, variant: str) -> pd.DataFrame | None:
    mapping = {
        "reducido": ("03_dataset_reducido_por_seleccion.xlsx", "dataset_reducido"),
        "pca": ("04_dataset_pca_componentes.xlsx", "dataset_pca"),
    }
    if variant not in mapping:
        return None
    filename, sheet = mapping[variant]
    try:
        path = find_file(ctx, filename)
    except FileNotFoundError:
        return None
    return pd.read_excel(path, sheet_name=sheet)


def rec(order, title, filename, source, sheet, variables, objective, interpretation, reading, equation, use, limitations):
    return GraphicRecord(order, "Redes recurrentes RNN/LSTM", title, filename, source, sheet, variables,
                         objective, interpretation, reading, equation, use, limitations)


def graph_temporal_partition(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    fig, ax = plt.subplots(figsize=(12, 5.8))
    n = 1584
    datasets = []
    for variant in sorted(results.dataset.unique()):
        df = load_variant_dataset(ctx, variant)
        datasets.append((variant, len(df) if df is not None else n))
    y = np.arange(len(datasets))
    for i, (variant, total) in enumerate(datasets):
        train_end = total - TEST_DAYS
        ax.barh(i, train_end, left=0, label="Entrenamiento" if i == 0 else None)
        ax.barh(i, TEST_DAYS, left=train_end, label="Prueba" if i == 0 else None)
        ax.axvspan(train_end - LOOKBACK_DAYS, train_end, alpha=0.15)
        ax.text(train_end / 2, i, f"Entrenamiento: {train_end} días", ha="center", va="center", fontsize=9)
        ax.text(train_end + TEST_DAYS / 2, i, f"Prueba: {TEST_DAYS}", ha="center", va="center", fontsize=9)
    ax.set_yticks(y, [dataset_label(v) for v, _ in datasets])
    ax.set_xlabel("Índice temporal diario")
    ax.set_title("Partición temporal utilizada para entrenamiento y prueba de RNN/LSTM")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    filename = "01_particion_temporal_rnn_lstm.png"
    save(fig, ctx, filename)
    return rec(1, "Partición temporal de entrenamiento y prueba", filename,
               "Datasets reducido/PCA y configuración de 08_rnn_lstm_dataset_reducido.py", "Varias",
               "fecha, LOOKBACK_DAYS, TEST_DAYS", "Documentar que la prueba corresponde a los últimos 90 días y no a una muestra aleatoria.",
               "El bloque final se reserva íntegramente para evaluación; los 28 días previos aportan contexto para formar la primera secuencia de prueba.",
               "La separación cronológica evita entrenar con observaciones posteriores al periodo pronosticado.",
               r"Train=\{1,\ldots,N-90\},\quad Test=\{N-89,\ldots,N\}",
               "Metodología de partición temporal para redes recurrentes.",
               "Es una sola partición final, no una validación Rolling-Origin; por ello su incertidumbre temporal está menos caracterizada.")


def graph_sequence_window(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(1, LOOKBACK_DAYS + 2)
    ax.scatter(x[:-1], np.zeros(LOOKBACK_DAYS), s=55, label="Observaciones de entrada")
    ax.scatter([x[-1]], [0], s=90, marker="*", label="Objetivo a predecir")
    for i in range(LOOKBACK_DAYS):
        ax.plot([x[i], x[-1]], [0, 0], alpha=0.08)
    ax.axvspan(0.5, LOOKBACK_DAYS + 0.5, alpha=0.12)
    ax.text((LOOKBACK_DAYS + 1) / 2, 0.12, "Ventana histórica de 28 días", ha="center")
    ax.text(x[-1], -0.13, "día t", ha="center")
    ax.set_yticks([])
    ax.set_xticks([1, 7, 14, 21, 28, 29], ["t-28", "t-22", "t-15", "t-8", "t-1", "t"])
    ax.set_title("Conversión de la serie temporal en secuencias supervisadas")
    ax.set_xlabel("Posición temporal")
    ax.legend()
    fig.tight_layout()
    filename = "02_ventana_supervisada_28_dias.png"
    save(fig, ctx, filename)
    return rec(2, "Ventana supervisada de 28 días", filename, "08_rnn_lstm_dataset_reducido.py", "make_sequences",
               "x[i-28:i], y[i]", "Ilustrar cómo cada ejemplo de entrenamiento utiliza 28 días previos para estimar el valor del día siguiente.",
               "La red recibe un tensor temporal y aprende dependencias entre posiciones consecutivas.",
               "Cada ventana termina en t-1; el objetivo corresponde a t, evitando incluir el valor futuro dentro de la entrada.",
               r"X_t=[x_{t-28},\ldots,x_{t-1}],\quad y_t=y(t)",
               "Explicación de la preparación supervisada de datos para RNN y LSTM.",
               "El horizonte efectivo es de un día; el código evalúa 90 predicciones de un paso construidas sobre el contexto final.")


def graph_architecture(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.axis("off")
    boxes = [
        (0.04, 0.38, 0.18, 0.25, "Entrada\n28 × p"),
        (0.28, 0.38, 0.18, 0.25, "RNN simple o LSTM\n32 unidades"),
        (0.52, 0.38, 0.16, 0.25, "Dense\n16 ReLU"),
        (0.74, 0.38, 0.14, 0.25, "Salida\n1 valor"),
    ]
    for x, y, w, h, txt in boxes:
        rect = plt.Rectangle((x, y), w, h, fill=False, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, txt, ha="center", va="center", fontsize=11)
    for i in range(len(boxes)-1):
        x1 = boxes[i][0] + boxes[i][2]
        x2 = boxes[i+1][0]
        ax.annotate("", xy=(x2, 0.505), xytext=(x1, 0.505), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.text(0.5, 0.78, "Arquitectura base evaluada", ha="center", fontsize=15)
    ax.text(0.5, 0.20, "Optimizador: Adam | Función de pérdida: MAE | EarlyStopping: paciencia 10", ha="center", fontsize=10)
    filename = "03_arquitectura_rnn_lstm.png"
    save(fig, ctx, filename)
    return rec(3, "Arquitectura de las redes recurrentes", filename, "08_rnn_lstm_dataset_reducido.py", "Sequential",
               "entrada, capa recurrente, Dense(16), Dense(1)", "Representar la arquitectura común utilizada para comparar RNN simple y LSTM.",
               "La única diferencia estructural entre modelos es el tipo de capa recurrente; las capas densas y la salida son equivalentes.",
               "La comparación es más controlada porque mantiene constante el resto de la arquitectura.",
               r"\hat y_t=W_2\,ReLU(W_1h_t+b_1)+b_2",
               "Configuración del experimento de aprendizaje profundo.",
               "No se realizó búsqueda exhaustiva de hiperparámetros; los resultados corresponden a una arquitectura base.")


def graph_input_dimensions(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    rows=[]
    for variant in sorted(results.dataset.unique()):
        df=load_variant_dataset(ctx, variant)
        if df is None: continue
        predictors=[c for c in df.columns if c not in TARGETS+["fecha"]]
        rows.append({"dataset":variant,"predictores":len(predictors),"valores_por_secuencia":len(predictors)*LOOKBACK_DAYS})
    data=pd.DataFrame(rows)
    if data.empty: raise ValueError("No se encontraron datasets de entrada")
    fig, ax=plt.subplots(figsize=(9.5,6.2))
    x=np.arange(len(data)); width=.36
    ax.bar(x-width/2,data.predictores,width,label="Predictores")
    ax.bar(x+width/2,data.valores_por_secuencia,width,label="Valores por secuencia (28×p)")
    ax.set_yscale("log")
    ax.set_xticks(x,[dataset_label(v) for v in data.dataset])
    ax.set_ylabel("Cantidad (escala logarítmica)")
    ax.set_title("Dimensionalidad de la entrada recurrente por variante del dataset")
    ax.legend(); ax.grid(axis="y",alpha=.2)
    fig.tight_layout(); filename="04_dimensionalidad_entrada_recurrente.png"; save(fig,ctx,filename)
    return rec(4,"Dimensionalidad de entrada de las redes",filename,"03_dataset_reducido... / 04_dataset_pca...","dataset_reducido / dataset_pca",
               "número de predictores y 28×p", "Comparar la carga informativa que recibe cada secuencia según la representación del dataset.",
               "PCA reduce el número de canales de entrada frente al dataset reducido; cada ejemplo contiene 28 veces el número de predictores.",
               "La escala logarítmica permite comparar predictores y valores totales de una secuencia.",
               r"Dim(X)=N_{seq}\times 28\times p",
               "Justificación del control de dimensionalidad antes del aprendizaje profundo.",
               "Menos entradas reducen complejidad, pero PCA disminuye interpretabilidad de los canales.")


def graph_rmse(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    fig, axes=plt.subplots(2,2,figsize=(14,10)); axes=axes.ravel()
    for ax,target in zip(axes,TARGETS):
        sub=results[results.target==target].copy(); labels=[f"{dataset_label(d)}\n{model_label(m)}" for d,m in zip(sub.dataset,sub.modelo)]
        ax.bar(np.arange(len(sub)),sub.rmse); ax.set_xticks(np.arange(len(sub)),wrap(labels,18),rotation=30,ha="right")
        ax.set_title(target_label(target)); ax.set_ylabel("RMSE"); ax.grid(axis="y",alpha=.2)
    fig.suptitle("Comparación de RMSE entre RNN simple y LSTM",fontsize=15); fig.tight_layout()
    filename="05_comparacion_rmse_rnn_lstm.png"; save(fig,ctx,filename)
    return rec(5,"Comparación de RMSE",filename,"06_rnn_lstm_reducido.xlsx y 06_rnn_lstm_pca.xlsx","Sheet1",
               "dataset, target, modelo, rmse","Comparar la penalización de errores grandes entre arquitecturas y representaciones.",
               "Una barra menor representa mejor ajuste predictivo para el objetivo correspondiente.",
               "La comparación debe hacerse dentro de cada objetivo, no entre unidades monetarias y conteos.",
               r"RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}",
               "Resultados de desempeño predictivo de redes recurrentes.",
               "Cada métrica proviene de una única partición final de 90 días.")


def graph_mae(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    fig, axes=plt.subplots(2,2,figsize=(14,10)); axes=axes.ravel()
    for ax,target in zip(axes,TARGETS):
        sub=results[results.target==target].copy(); labels=[f"{dataset_label(d)}\n{model_label(m)}" for d,m in zip(sub.dataset,sub.modelo)]
        ax.bar(np.arange(len(sub)),sub.mae); ax.set_xticks(np.arange(len(sub)),wrap(labels,18),rotation=30,ha="right")
        ax.set_title(target_label(target)); ax.set_ylabel("MAE"); ax.grid(axis="y",alpha=.2)
    fig.suptitle("Comparación de MAE entre RNN simple y LSTM",fontsize=15); fig.tight_layout()
    filename="06_comparacion_mae_rnn_lstm.png"; save(fig,ctx,filename)
    return rec(6,"Comparación de MAE",filename,"06_rnn_lstm_reducido.xlsx y 06_rnn_lstm_pca.xlsx","Sheet1",
               "dataset, target, modelo, mae","Comparar la magnitud promedio de los errores en las unidades originales.",
               "MAE resume el error típico sin penalizar cuadráticamente los valores extremos.",
               "Una menor barra significa menor desviación absoluta promedio.",
               r"MAE=\frac{1}{n}\sum_{i=1}^{n}|y_i-\hat y_i|",
               "Evaluación de precisión media de las redes.",
               "No muestra la dirección del sesgo ni la distribución temporal de los errores.")


def graph_mape(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    fig, axes=plt.subplots(2,2,figsize=(14,10)); axes=axes.ravel()
    for ax,target in zip(axes,TARGETS):
        sub=results[results.target==target].copy(); labels=[f"{dataset_label(d)}\n{model_label(m)}" for d,m in zip(sub.dataset,sub.modelo)]
        ax.bar(np.arange(len(sub)),sub.mape); ax.set_xticks(np.arange(len(sub)),wrap(labels,18),rotation=30,ha="right")
        ax.set_title(target_label(target)); ax.set_ylabel("MAPE (%)"); ax.grid(axis="y",alpha=.2)
    fig.suptitle("Diagnóstico del MAPE en RNN y LSTM",fontsize=15); fig.tight_layout()
    filename="07_diagnostico_mape_rnn_lstm.png"; save(fig,ctx,filename)
    return rec(7,"Diagnóstico del MAPE",filename,"06_rnn_lstm_reducido.xlsx y 06_rnn_lstm_pca.xlsx","Sheet1",
               "dataset, target, modelo, mape","Mostrar la inestabilidad del error porcentual cuando existen valores reales pequeños o iguales a cero.",
               "MAPE muy elevado no necesariamente implica el mismo deterioro observado en MAE o RMSE; puede estar dominado por denominadores pequeños.",
               "Debe interpretarse junto con la tasa de ceros de cada objetivo.",
               r"MAPE=\frac{100}{n}\sum_i\left|\frac{y_i-\hat y_i}{y_i}\right|",
               "Discusión crítica de métricas para series intermitentes.",
               "El código excluye denominadores cercanos a cero, pero los valores pequeños siguen amplificando el porcentaje.")


def graph_winners(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    winners=results.loc[results.groupby(["dataset","target"])["rmse"].idxmin()].copy()
    pivot=winners.pivot(index="target",columns="dataset",values="rmse")
    fig,ax=plt.subplots(figsize=(10.5,7.2)); im=ax.imshow(pivot.values,aspect="auto")
    ax.set_xticks(np.arange(len(pivot.columns)),[dataset_label(c) for c in pivot.columns])
    ax.set_yticks(np.arange(len(pivot.index)),[target_label(i) for i in pivot.index])
    for i,target in enumerate(pivot.index):
        for j,dataset in enumerate(pivot.columns):
            row=winners[(winners.target==target)&(winners.dataset==dataset)]
            if not row.empty: ax.text(j,i,f"{model_label(row.iloc[0].modelo)}\nRMSE={row.iloc[0].rmse:.2f}",ha="center",va="center",fontsize=8)
    fig.colorbar(im,ax=ax,label="RMSE"); ax.set_title("Arquitectura ganadora por dataset y objetivo"); fig.tight_layout()
    filename="08_arquitectura_ganadora_por_objetivo.png"; save(fig,ctx,filename)
    return rec(8,"Arquitectura ganadora por objetivo",filename,"06_rnn_lstm_*.xlsx","Sheet1",
               "dataset, target, modelo, rmse","Identificar si RNN simple o LSTM obtiene el menor RMSE en cada combinación.",
               "La etiqueta muestra el modelo ganador y su error absoluto.",
               "El ganador se determina de forma independiente para cada dataset y objetivo.",
               r"m^*_{d,y}=\arg\min_m RMSE_{d,y,m}",
               "Síntesis de comparación arquitectónica.",
               "Una diferencia pequeña no demuestra superioridad estadística; no hay repeticiones con distintas semillas.")


def graph_lstm_gain(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    p=results.pivot_table(index=["dataset","target"],columns="modelo",values="rmse").reset_index()
    if not {"rnn_simple","lstm"}.issubset(p.columns): raise ValueError("Faltan ambos modelos")
    p["mejora_pct"]=(p.rnn_simple-p.lstm)/p.rnn_simple*100
    fig,ax=plt.subplots(figsize=(12,7)); labels=[f"{dataset_label(d)} — {target_label(t)}" for d,t in zip(p.dataset,p.target)]
    ax.barh(np.arange(len(p)),p.mejora_pct); ax.set_yticks(np.arange(len(p)),wrap(labels,42)); ax.axvline(0,linewidth=1)
    ax.set_xlabel("Mejora de LSTM respecto a RNN simple en RMSE (%)"); ax.set_title("Ganancia relativa de LSTM frente a RNN simple"); ax.grid(axis="x",alpha=.2)
    fig.tight_layout(); filename="09_mejora_lstm_vs_rnn.png"; save(fig,ctx,filename)
    return rec(9,"Mejora relativa de LSTM",filename,"06_rnn_lstm_*.xlsx","Sheet1",
               "rmse de rnn_simple y lstm","Cuantificar si la memoria controlada de LSTM produce una mejora práctica frente a una RNN simple.",
               "Valores positivos favorecen LSTM; valores negativos favorecen RNN simple.",
               "La magnitud porcentual permite comparar objetivos con escalas distintas.",
               r"Mejora_{LSTM}=\frac{RMSE_{RNN}-RMSE_{LSTM}}{RMSE_{RNN}}\times100",
               "Discusión de la contribución de las compuertas LSTM.",
               "No incorpora costo computacional ni incertidumbre por inicialización aleatoria.")


def graph_dataset_effect(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    p=results.pivot_table(index=["modelo","target"],columns="dataset",values="rmse").reset_index()
    available=[c for c in ["reducido","pca"] if c in p.columns]
    if len(available)<2: raise ValueError("Se requieren resultados reducido y PCA")
    p["diferencia_pct"]=(p["pca"]-p["reducido"])/p["reducido"]*100
    fig,ax=plt.subplots(figsize=(12,7)); labels=[f"{model_label(m)} — {target_label(t)}" for m,t in zip(p.modelo,p.target)]
    ax.barh(np.arange(len(p)),p.diferencia_pct); ax.set_yticks(np.arange(len(p)),wrap(labels,42)); ax.axvline(0,linewidth=1)
    ax.set_xlabel("Cambio de RMSE de PCA respecto al reducido (%)"); ax.set_title("Efecto de la representación de entrada sobre RNN/LSTM"); ax.grid(axis="x",alpha=.2)
    fig.tight_layout(); filename="10_efecto_dataset_reducido_vs_pca.png"; save(fig,ctx,filename)
    return rec(10,"Efecto del dataset reducido frente a PCA",filename,"06_rnn_lstm_reducido.xlsx y 06_rnn_lstm_pca.xlsx","Sheet1",
               "dataset, modelo, target, rmse","Evaluar si la compacidad PCA mejora o deteriora el desempeño respecto a variables seleccionadas interpretables.",
               "Valores negativos indican que PCA reduce el RMSE; positivos indican que el dataset reducido fue mejor.",
               "La comparación se realiza para la misma arquitectura y objetivo.",
               r"\Delta_{PCA}=\frac{RMSE_{PCA}-RMSE_{red}}{RMSE_{red}}\times100",
               "Comparación de estrategias de reducción dimensional para deep learning.",
               "PCA puede mejorar estabilidad numérica, pero sacrifica interpretabilidad.")


def graph_mae_rmse_gap(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    data=results.copy(); data["gap"]=(data.rmse-data.mae)/data.rmse*100
    fig,ax=plt.subplots(figsize=(11,7))
    for model,sub in data.groupby("modelo"):
        ax.scatter(sub.mae,sub.rmse,s=70,label=model_label(model))
        for _,r in sub.iterrows(): ax.annotate(dataset_label(r.dataset)[8:]+"/"+target_label(r.target)[:8],(r.mae,r.rmse),fontsize=6,xytext=(3,3),textcoords="offset points")
    lim=max(data.rmse.max(),data.mae.max())*1.05; ax.plot([0,lim],[0,lim],linestyle="--",linewidth=1)
    ax.set_xlabel("MAE"); ax.set_ylabel("RMSE"); ax.set_title("Separación entre error medio y penalización de errores grandes"); ax.legend(); ax.grid(alpha=.2)
    fig.tight_layout(); filename="11_relacion_mae_rmse_redes.png"; save(fig,ctx,filename)
    return rec(11,"Relación entre MAE y RMSE",filename,"06_rnn_lstm_*.xlsx","Sheet1",
               "mae, rmse","Detectar combinaciones donde algunos errores grandes elevan sustancialmente el RMSE.",
               "Cuanto más alejado se encuentre un punto por encima de la diagonal, mayor es la influencia de errores extremos.",
               "La diagonal representa igualdad teórica entre ambas métricas.",
               r"RMSE\geq MAE",
               "Análisis de severidad y heterogeneidad del error.",
               "Las métricas agregadas no permiten localizar temporalmente los errores extremos.")


def graph_multicriteria(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    d=results.copy()
    for metric in ["mae","rmse","mape"]:
        d[metric+"_norm"]=d.groupby("target")[metric].transform(lambda s:(s-s.min())/(s.max()-s.min()) if s.max()>s.min() else 0)
    d["score"]=(d.mae_norm+d.rmse_norm+d.mape_norm)/3
    d=d.sort_values(["target","score"])
    fig,axes=plt.subplots(2,2,figsize=(14,10)); axes=axes.ravel()
    for ax,target in zip(axes,TARGETS):
        sub=d[d.target==target]; labels=[f"{dataset_label(x)}\n{model_label(m)}" for x,m in zip(sub.dataset,sub.modelo)]
        ax.bar(np.arange(len(sub)),sub.score); ax.set_xticks(np.arange(len(sub)),wrap(labels,18),rotation=30,ha="right"); ax.set_title(target_label(target)); ax.set_ylabel("Score normalizado"); ax.grid(axis="y",alpha=.2)
    fig.suptitle("Score multicriterio de RNN y LSTM",fontsize=15); fig.tight_layout()
    filename="12_score_multicriterio_rnn_lstm.png"; save(fig,ctx,filename)
    return rec(12,"Score multicriterio",filename,"06_rnn_lstm_*.xlsx","Sheet1",
               "mae, rmse, mape","Sintetizar el desempeño conjunto de las tres métricas después de normalizarlas por objetivo.",
               "Un score menor representa mejor equilibrio relativo.",
               "La normalización evita mezclar escalas monetarias y de conteo.",
               r"S=\frac{MAE^{norm}+RMSE^{norm}+MAPE^{norm}}{3}",
               "Síntesis complementaria del rendimiento de las redes.",
               "El peso uniforme es una decisión analítica y MAPE puede distorsionar el score en series con ceros.")


def graph_training_configuration(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    values=pd.Series({"Lookback":LOOKBACK_DAYS,"Prueba":TEST_DAYS,"Épocas máximas":EPOCHS,"Batch size":BATCH_SIZE,"Unidades recurrentes":32,"Neuronas densas":16,"Paciencia":10})
    fig,ax=plt.subplots(figsize=(10.5,6.5)); ax.barh(values.index,values.values); ax.set_title("Configuración base del entrenamiento RNN/LSTM"); ax.set_xlabel("Valor del hiperparámetro"); ax.grid(axis="x",alpha=.2)
    for i,v in enumerate(values.values): ax.text(v,i,f" {int(v)}",va="center")
    fig.tight_layout(); filename="13_configuracion_entrenamiento_redes.png"; save(fig,ctx,filename)
    return rec(13,"Configuración de entrenamiento",filename,"08_rnn_lstm_dataset_reducido.py","Constantes y model.fit",
               "LOOKBACK_DAYS, TEST_DAYS, EPOCHS, BATCH_SIZE, unidades, paciencia","Resumir los principales hiperparámetros que controlan la capacidad y el proceso de ajuste.",
               "La figura documenta una configuración base reproducible.",
               "EarlyStopping puede detener el entrenamiento antes de las 80 épocas.",
               r"\theta^*=\arg\min_\theta MAE_{val}(\theta)",
               "Tabla o figura de configuración experimental.",
               "El output actual no conserva el número real de épocas ejecutadas ni la historia de pérdida.")


def graph_sample_parameter_ratio(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    rows=[]
    for variant in sorted(results.dataset.unique()):
        df=load_variant_dataset(ctx,variant)
        if df is None: continue
        p=len([c for c in df.columns if c not in TARGETS+["fecha"]])
        n_train=len(df)-TEST_DAYS-LOOKBACK_DAYS
        # Approximate trainable parameters for recurrent layer + dense layers.
        rnn_params=32*(p+32+1)+32*16+16+16*1+1
        lstm_params=4*32*(p+32+1)+32*16+16+16*1+1
        rows.extend([{"dataset":variant,"modelo":"rnn_simple","parametros":rnn_params,"secuencias":n_train,"ratio":rnn_params/max(n_train,1)},
                     {"dataset":variant,"modelo":"lstm","parametros":lstm_params,"secuencias":n_train,"ratio":lstm_params/max(n_train,1)}])
    d=pd.DataFrame(rows)
    if d.empty: raise ValueError("No hay datasets para estimar parámetros")
    fig,ax=plt.subplots(figsize=(10.5,6.5)); labels=[f"{dataset_label(x)}\n{model_label(m)}" for x,m in zip(d.dataset,d.modelo)]
    ax.bar(np.arange(len(d)),d.ratio); ax.set_xticks(np.arange(len(d)),wrap(labels,18)); ax.set_ylabel("Parámetros aproximados por secuencia de entrenamiento"); ax.set_title("Complejidad del modelo frente al tamaño muestral"); ax.grid(axis="y",alpha=.2)
    fig.tight_layout(); filename="14_complejidad_parametros_vs_muestra.png"; save(fig,ctx,filename)
    return rec(14,"Complejidad paramétrica frente a la muestra",filename,"Datasets de entrada y arquitectura del código 08","Varias","predictores, secuencias, parámetros estimados",
               "Ilustrar el riesgo de sobreajuste al relacionar la capacidad de la red con el número de secuencias disponibles.",
               "LSTM posee aproximadamente cuatro veces más parámetros recurrentes que una RNN simple con igual número de unidades.",
               "Una razón elevada señala alta capacidad relativa frente a una muestra pequeña.",
               r"Params_{RNN}=u(p+u+1),\quad Params_{LSTM}=4u(p+u+1)",
               "Discusión de Small Data y complejidad de aprendizaje profundo.",
               "Es una estimación estructural; no sustituye una curva de aprendizaje ni validación con múltiples semillas.")


def graph_target_zero_rate(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    rows=[]
    for variant in sorted(results.dataset.unique()):
        df=load_variant_dataset(ctx,variant)
        if df is None: continue
        for target in TARGETS:
            if target in df:
                s=pd.to_numeric(df[target],errors="coerce").fillna(0).iloc[-TEST_DAYS:]
                rows.append({"dataset":variant,"target":target,"ceros":(s==0).mean()*100})
    d=pd.DataFrame(rows)
    if d.empty: raise ValueError("No se pudieron calcular ceros")
    fig,ax=plt.subplots(figsize=(11.5,7)); x=np.arange(len(TARGETS)); width=.35
    for j,(variant,sub) in enumerate(d.groupby("dataset")):
        vals=[float(sub.loc[sub.target==t,"ceros"].iloc[0]) for t in TARGETS]
        ax.bar(x+(j-.5)*width,vals,width,label=dataset_label(variant))
    ax.set_xticks(x,wrap([target_label(t) for t in TARGETS],20)); ax.set_ylabel("Días con valor cero en prueba (%)"); ax.set_title("Intermitencia de los objetivos en el periodo de prueba"); ax.legend(); ax.grid(axis="y",alpha=.2)
    fig.tight_layout(); filename="15_intermitencia_objetivos_periodo_prueba.png"; save(fig,ctx,filename)
    return rec(15,"Intermitencia en el periodo de prueba",filename,"03_dataset_reducido... / 04_dataset_pca...","últimos 90 días",
               "targets y porcentaje de ceros","Relacionar la frecuencia de ceros con la inestabilidad del MAPE y la dificultad predictiva.",
               "Los objetivos con más ceros suelen presentar errores porcentuales extremos y mayor dificultad para redes entrenadas con pérdidas continuas.",
               "La tasa se calcula únicamente sobre el bloque final de prueba.",
               r"Z_y=\frac{1}{90}\sum_{t\in Test}I(y_t=0)\times100",
               "Análisis crítico de los resultados RNN/LSTM.",
               "Cero puede ser una observación operativa legítima; no debe tratarse automáticamente como dato faltante.")


def graph_summary(ctx: Context, results: pd.DataFrame) -> GraphicRecord:
    winners=results.loc[results.groupby(["dataset","target"])["rmse"].idxmin()]
    metrics=pd.Series({
        "Combinaciones evaluadas":len(results),
        "Datasets":results.dataset.nunique(),
        "Objetivos":results.target.nunique(),
        "Arquitecturas":results.modelo.nunique(),
        "Victorias LSTM":int((winners.modelo=="lstm").sum()),
        "Victorias RNN":int((winners.modelo=="rnn_simple").sum()),
    })
    fig,ax=plt.subplots(figsize=(10,6.5)); ax.barh(metrics.index,metrics.values); ax.set_title("Síntesis cuantitativa del experimento RNN/LSTM"); ax.set_xlabel("Cantidad"); ax.grid(axis="x",alpha=.2)
    for i,v in enumerate(metrics.values): ax.text(v,i,f" {int(v)}",va="center")
    fig.tight_layout(); filename="16_resumen_experimento_rnn_lstm.png"; save(fig,ctx,filename)
    return rec(16,"Resumen del experimento RNN/LSTM",filename,"06_rnn_lstm_*.xlsx","Sheet1",
               "combinaciones, datasets, objetivos, arquitecturas y ganadores","Cerrar la etapa con una síntesis de alcance experimental.",
               "El número de victorias muestra qué arquitectura obtuvo menor RMSE en más combinaciones.",
               "Debe leerse junto con la magnitud de las diferencias, no solo con el conteo de ganadores.",
               r"W_m=\sum_{d,y}I\left(m=\arg\min_j RMSE_{d,y,j}\right)",
               "Cierre de la sección de redes recurrentes.",
               "El experimento no registra múltiples ejecuciones, intervalos de confianza ni curvas de entrenamiento.")


def build_manifest(records: list[GraphicRecord], ctx: Context, results: pd.DataFrame) -> None:
    df=pd.DataFrame([asdict(r) for r in records])
    df.to_csv(ctx.graphics_dir/"INDICE_GRAFICAS_RNN_LSTM.csv",index=False,encoding="utf-8-sig")
    payload={"generado":datetime.now().isoformat(),"configuracion":{"lookback":LOOKBACK_DAYS,"test_days":TEST_DAYS,"epochs":EPOCHS,"batch_size":BATCH_SIZE},"graficas":[asdict(r) for r in records]}
    (ctx.graphics_dir/"MANIFIESTO_RNN_LSTM.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Manifiesto académico de gráficas RNN/LSTM","",f"Generado: {datetime.now():%Y-%m-%d %H:%M}","",
           "## Alcance metodológico","",
           "Este módulo documenta la preparación de secuencias, la arquitectura base y la comparación de RNN simple y LSTM sobre los datasets reducido y PCA.",
           "Los resultados proceden de una única partición temporal final de 90 días; no son directamente equivalentes a la evaluación Rolling-Origin de los modelos tradicionales.",""]
    for r in records:
        lines += [f"## Figura {r.orden}. {r.titulo}","",f"- **Archivo:** `{r.archivo}`",f"- **Fuente:** {r.fuente}",f"- **Hoja:** {r.hoja}",f"- **Variables:** {r.variables_utilizadas}",f"- **Objetivo:** {r.objetivo}",f"- **Interpretación:** {r.interpretacion}",f"- **Criterio de lectura:** {r.criterio_lectura}",f"- **Ecuación o fundamento:** `{r.ecuacion_o_fundamento}`",f"- **Uso sugerido en tesis:** {r.uso_tesis}",f"- **Limitaciones:** {r.limitaciones}",""]
    (ctx.graphics_dir/"MANIFIESTO_RNN_LSTM.md").write_text("\n".join(lines),encoding="utf-8")
    winners=results.loc[results.groupby(["dataset","target"])["rmse"].idxmin()].copy()
    with pd.ExcelWriter(ctx.graphics_dir/"RESUMEN_ESTADISTICO_RNN_LSTM.xlsx",engine="openpyxl") as w:
        df.to_excel(w,sheet_name="indice_graficas",index=False)
        results.to_excel(w,sheet_name="resultados",index=False)
        winners.to_excel(w,sheet_name="ganadores_rmse",index=False)


def main() -> None:
    args=parse_args()
    graphics_dir=args.graphics_dir or args.analysis_dir/"graficas_rnn_lstm"
    ctx=Context(args.analysis_dir,graphics_dir,args.dpi,args.top_n,args.continuar_con_faltantes)
    configure_logging(graphics_dir)
    results=load_results(ctx)
    funcs: list[Callable[[Context,pd.DataFrame],GraphicRecord]]=[
        graph_temporal_partition, graph_sequence_window, graph_architecture, graph_input_dimensions,
        graph_rmse, graph_mae, graph_mape, graph_winners, graph_lstm_gain, graph_dataset_effect,
        graph_mae_rmse_gap, graph_multicriteria, graph_training_configuration, graph_sample_parameter_ratio,
        graph_target_zero_rate, graph_summary,
    ]
    records=[]
    for fn in funcs:
        try:
            r=fn(ctx,results); records.append(r); logging.info("Generada: %s",r.archivo)
        except Exception as exc:
            logging.exception("No se pudo generar %s: %s",fn.__name__,exc)
            if not ctx.continuar: raise
    build_manifest(records,ctx,results)
    logging.info("Proceso terminado. Gráficas generadas: %d",len(records))


if __name__=="__main__":
    main()
