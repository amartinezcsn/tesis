from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT = Path(r"C:\Python\tesis\imagenes")
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#1f4e79"
LIGHT = "#d9eaf7"
GREEN = "#2e7d32"
ORANGE = "#d97706"
GRAY = "#5f6b76"
RED = "#b42318"


def setup(title, figsize=(14, 5.5)):
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(title, fontsize=18, fontweight="semibold", pad=18)
    return fig, ax


def box(ax, x, y, w, h, text, fc=LIGHT, ec=BLUE, fontsize=10, color="#17202a"):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.7, edgecolor=ec, facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=color, wrap=True)
    return patch


def arrow(ax, x1, y1, x2, y2, color=GRAY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=14, linewidth=1.6, color=color))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# I01. Trazabilidad del pipeline
fig, ax = setup("Trazabilidad del pipeline analítico de la investigación", (15, 5.2))
labels = [
    "Fuentes\nVentas · compras\nINPC · clima · calendario",
    "Auditoría y limpieza\nHomologación · fechas\nvalores reales",
    "Dataset maestro\n1,612 días\n65 variables",
    "Ingeniería de características\nRezagos · ventanas\neventos exógenos",
    "Representaciones\nCompleto · reducido\nPCA",
    "Validación temporal\nRolling-Origin\n3 orígenes finales",
    "Modelos y DSS\nComparación contra\nlínea base empírica",
]
xs = [0.015, 0.155, 0.295, 0.435, 0.575, 0.715, 0.855]
for i, (x, label) in enumerate(zip(xs, labels)):
    fc = "#e8f1f8" if i < 3 else "#edf6ed" if i < 6 else "#fff3dd"
    ec = BLUE if i < 3 else GREEN if i < 6 else ORANGE
    box(ax, x, 0.37, 0.125, 0.28, label, fc=fc, ec=ec, fontsize=9.5)
    if i < len(labels) - 1:
        arrow(ax, x + 0.126, 0.51, xs[i + 1] - 0.006, 0.51)
ax.text(0.5, 0.17,
        "Principio de control: cada transformación conserva fecha, fuente, cobertura y reglas reproducibles; "
        "las características históricas utilizan exclusivamente información anterior al día pronosticado.",
        ha="center", va="center", fontsize=10.5, color=GRAY)
save(fig, "88_pipeline_trazabilidad_tesis.png")


# I02. Diseño de evaluación comparativa
fig, ax = setup("Diseño evaluativo: comparación temporal contra la línea base", (14, 6.2))
box(ax, 0.06, 0.62, 0.20, 0.20, "Datos históricos ordenados\n2022–2026", fc="#e8f1f8")
box(ax, 0.40, 0.67, 0.22, 0.16, "Línea base empírica\nÚltimo valor y promedio de 7 días", fc="#fff3dd", ec=ORANGE)
box(ax, 0.40, 0.43, 0.22, 0.16, "Modelos candidatos\nARIMA · SARIMA · regresión\nárboles · RF · RNN/LSTM", fc="#edf6ed", ec=GREEN)
box(ax, 0.73, 0.55, 0.21, 0.22, "Evaluación Rolling-Origin\nMAE · RMSE · MAPE\npor ventana y promedio", fc="#f0ebf8", ec="#6b4fa1")
box(ax, 0.73, 0.20, 0.21, 0.18, "Contraste de H1\nReducción relativa de RMSE\nUmbral: 20%", fc="#fde8e7", ec=RED)
arrow(ax, 0.26, 0.72, 0.39, 0.75)
arrow(ax, 0.26, 0.69, 0.39, 0.52)
arrow(ax, 0.62, 0.75, 0.72, 0.68)
arrow(ax, 0.62, 0.51, 0.72, 0.61)
arrow(ax, 0.835, 0.55, 0.835, 0.39)
ax.text(0.5, 0.08,
        "No se emplea partición aleatoria: cada modelo aprende del pasado y se evalúa en observaciones futuras no vistas.",
        ha="center", fontsize=10.5, color=GRAY)
save(fig, "89_diseno_evaluacion_temporal.png")


# I03. Arquitectura DSS
fig, ax = setup("Arquitectura funcional del sistema de soporte a la decisión (DSS)", (14.5, 5.7))
labels = [
    (0.04, "Artefactos del pipeline\nExcel · JSON · métricas\nmodelos ganadores", BLUE, "#e8f1f8"),
    (0.29, "Capa de integración\nEstructura JavaScript\ntrazabilidad por objetivo", GREEN, "#edf6ed"),
    (0.54, "Lógica analítica\nComparación con línea base\nreducción RMSE y H1", "#6b4fa1", "#f0ebf8"),
    (0.79, "Interfaz DSS\nFiltros · KPI · ventanas\nlectura ejecutiva", ORANGE, "#fff3dd"),
]
for i, (x, text, ec, fc) in enumerate(labels):
    box(ax, x, 0.45, 0.17, 0.26, text, fc=fc, ec=ec, fontsize=10)
    if i < len(labels) - 1:
        arrow(ax, x + 0.175, 0.58, labels[i + 1][0] - 0.008, 0.58)
box(ax, 0.34, 0.14, 0.32, 0.15,
    "Salvaguarda metodológica\nLa decisión permanece bajo responsabilidad humana; "
    "el tablero no actualiza datos automáticamente.",
    fc="#fde8e7", ec=RED, fontsize=10)
arrow(ax, 0.875, 0.45, 0.66, 0.26, color=RED)
save(fig, "90_arquitectura_funcional_dss.png")


# I05. Flujo operativo
fig, ax = setup("Flujo de decisión operativa apoyado por el DSS", (14, 5.4))
labels = [
    "Pronóstico por objetivo\nventas o compras",
    "Revisión de cobertura\ny estabilidad temporal",
    "Comparación contra\nlínea base empírica",
    "Estimación de riesgo\ny requerimiento",
    "Revisión del responsable\ndel negocio",
    "Decisión y registro\noperativo",
]
xs = [0.04, 0.205, 0.37, 0.535, 0.70, 0.865]
for i, (x, label) in enumerate(zip(xs, labels)):
    ec = BLUE if i < 2 else GREEN if i < 4 else ORANGE
    fc = "#e8f1f8" if i < 2 else "#edf6ed" if i < 4 else "#fff3dd"
    box(ax, x, 0.41, 0.125, 0.25, label, fc=fc, ec=ec, fontsize=9.2)
    if i < len(labels) - 1:
        arrow(ax, x + 0.127, 0.535, xs[i + 1] - 0.006, 0.535)
ax.text(0.5, 0.20,
        "Regla de uso: si la cobertura está desactualizada, el error es inestable o la mejora no supera el umbral, "
        "el resultado se interpreta como apoyo diagnóstico y no como autorización automática de compra.",
        ha="center", va="center", fontsize=10.2, color=GRAY)
save(fig, "91_flujo_decision_operativa_dss.png")

print("Activos científicos Rev33 generados.")
