from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "output" / "run_20261013T193604Z_157556" / "particiones.csv"
OUT = ROOT / "documentacion" / "figuras_rev66"


def main():
    df = pd.read_csv(PARTS)
    df = df.rename(columns={
        "etapa": "stage",
        "origen": "origin",
        "fecha_objetivo": "target_date",
        "entrenamiento_inicio": "train_start",
        "ultima_etiqueta_entrenamiento": "train_end",
    })
    for col in ("train_start", "train_end", "origin", "target_date"):
        df[col] = pd.to_datetime(df[col])

    origins = (
        df.groupby(["stage", "origin"], as_index=False)
        .agg(train_start=("train_start", "min"), train_end=("train_end", "max"))
        .sort_values(["stage", "origin"])
    )
    is_internal = origins["stage"].str.lower().str.contains("interna")
    internal = origins[is_internal].head(3)
    evaluation = origins[~is_internal]

    plt.rcParams.update({
        "font.family": "Times New Roman",
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.labelsize": 10.5,
    })
    fig = plt.figure(figsize=(11.2, 7.1), constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.25, 1])

    ax = fig.add_subplot(gs[0])
    blue = "#2F5597"
    colors = ["#70AD47", "#FFC000", "#ED7D31", "#C00000"]
    for row_no, (_, row) in enumerate(internal.iterrows()):
        y = 2 - row_no
        ax.barh(y, row["origin"] - row["train_start"], left=row["train_start"],
                height=0.34, color=blue, alpha=0.88)
        ax.axvline(row["origin"], ymin=(y + 0.05) / 3.15, ymax=(y + 0.95) / 3.15,
                   color="#222222", lw=1.1)
        for h, color in enumerate(colors, start=1):
            target = row["origin"] + pd.Timedelta(weeks=h - 1)
            ax.scatter(target, y, marker="s", s=55, color=color, edgecolor="white", zorder=5)
        ax.text(row["train_start"] + pd.Timedelta(days=182), y, "52 semanas",
                color="white", ha="center", va="center", fontweight="bold")
        ax.text(row["train_start"] - pd.Timedelta(days=10), y, f"Ventana {row_no + 1}",
                ha="right", va="center", fontweight="bold")

    first_origin = internal.iloc[0]["origin"]
    ax.text(internal.iloc[0]["train_start"], -0.48,
            "Cada barra inicia y termina una semana después que la anterior.",
            ha="left", va="center", fontsize=9.5, color="#333333")
    ax.text(first_origin - pd.Timedelta(days=4), 2.12,
            "Origen: límite entre entrenamiento y pronóstico",
            ha="right", va="bottom", fontsize=9, color="#333333")
    for h, color in enumerate(colors, start=1):
        ax.scatter([], [], marker="s", s=55, color=color, label=f"h={h}")
    ax.legend(loc="upper right", ncol=4, frameon=False, title="Semanas objetivo")
    ax.set_yticks([])
    ax.set_ylim(-0.62, 2.82)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.grid(axis="x", color="#D9D9D9", lw=0.7)
    ax.set_title("A. Mecánica de la ventana deslizante: ancho constante y avance semanal",
                 loc="left", fontweight="bold")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)

    ax2 = fig.add_subplot(gs[1])
    internal_all = origins[origins["stage"].str.lower().str.contains("interna")]
    ax2.scatter(internal_all["origin"], [1] * len(internal_all), s=75,
                color=blue, label=f"Selección interna: {len(internal_all)} ventanas")
    ax2.scatter(evaluation["origin"], [0] * len(evaluation), s=55,
                color="#C55A11", label=f"Evaluación final: {len(evaluation)} ventanas candidatas")
    ax2.set_yticks([0, 1], ["Evaluación final", "Selección interna"])
    ax2.set_ylim(-0.55, 1.55)
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%Y"))
    ax2.grid(axis="x", color="#E6E6E6", lw=0.7)
    ax2.set_title("B. Ventanas generadas por la corrida canónica",
                  loc="left", fontweight="bold")
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=2, frameon=False)
    ax2.text(0.995, 0.06,
             "Las métricas utilizan únicamente objetivos observados: seis folds válidos por horizonte.",
             transform=ax2.transAxes, ha="right", va="bottom", fontsize=9, color="#444444")
    for spine in ("top", "right", "left"):
        ax2.spines[spine].set_visible(False)

    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "Figura_8_rolling_window_52_semanas.png"
    svg = OUT / "Figura_8_rolling_window_52_semanas.svg"
    fig.savefig(png, dpi=320, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(png)
    print(svg)


if __name__ == "__main__":
    main()
