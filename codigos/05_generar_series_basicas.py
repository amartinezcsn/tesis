from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "output" / "run_20261013T193604Z_157556"
OUT = ROOT / "documentacion" / "figuras_individuales_propuesta_20261015"
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#1F4E79"
ORANGE = "#C55A11"
GREEN = "#548235"
GRAY = "#666666"


def finish(fig, stem):
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def style(ax, title, ylabel=None, xlabel=None):
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", pad=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=11)
    ax.grid(axis="y", alpha=0.22, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)


panel = pd.read_csv(RUN / "panel_semanal.csv", parse_dates=["semana_inicio"])
panel = panel.sort_values("semana_inicio").reset_index(drop=True)
panel["total"] = pd.to_numeric(panel["total"], errors="coerce").fillna(0.0)

# Se conserva toda la serie disponible; las ausencias y los ceros se interpretan
# posteriormente con la auditoría de cobertura, no se eliminan del diagnóstico.
s = panel.set_index("semana_inicio")["total"]

rolling = pd.DataFrame({
    "importe_semanal": s,
    "media_movil_13": s.rolling(13, min_periods=6).mean(),
    "mediana_movil_13": s.rolling(13, min_periods=6).median(),
})
rolling.to_csv(OUT / "ST02_tendencia_movil_datos.csv", index_label="semana_inicio")
fig, ax = plt.subplots(figsize=(10.8, 5.8))
ax.plot(s.index, s.values, color="#A6A6A6", linewidth=0.9, alpha=0.75, label="Importe semanal")
ax.plot(rolling.index, rolling["media_movil_13"], color=BLUE, linewidth=2.0, label="Media móvil de 13 semanas")
ax.plot(rolling.index, rolling["mediana_movil_13"], color=ORANGE, linewidth=2.0, label="Mediana móvil de 13 semanas")
style(ax, "Evolución local del importe semanal", "Importe semanal (MXN)", "Semana de inicio")
ax.legend(frameon=False, ncol=2, fontsize=9, loc="upper left")
finish(fig, "ST02_tendencia_movil")

positive = s[s > 0]
pd.DataFrame({"importe_positivo": positive.values}).to_csv(OUT / "ST03_histograma_datos.csv", index=False)
fig, ax = plt.subplots(figsize=(9.6, 5.8))
bins = min(30, max(10, int(np.sqrt(len(positive)))))
ax.hist(positive.values, bins=bins, color=BLUE, edgecolor="white", alpha=0.9)
ax.axvline(positive.median(), color=ORANGE, linestyle="--", linewidth=2, label=f"Mediana: ${positive.median():,.0f}")
style(ax, "Distribución de los importes semanales positivos", "Número de semanas", "Importe semanal (MXN)")
ax.legend(frameon=False, fontsize=9)
finish(fig, "ST03_histograma_importes")

fig, ax = plt.subplots(figsize=(9.6, 3.8))
ax.boxplot(positive.values, vert=False, patch_artist=True,
           boxprops=dict(facecolor="#D9EAF7", edgecolor=BLUE),
           medianprops=dict(color=ORANGE, linewidth=2),
           whiskerprops=dict(color=BLUE), capprops=dict(color=BLUE),
           flierprops=dict(marker="o", markersize=3, markerfacecolor=GRAY, markeredgecolor=GRAY, alpha=0.45))
style(ax, "Dispersión y valores extremos del importe semanal positivo", None, "Importe semanal (MXN)")
ax.set_yticks([])
finish(fig, "ST04_caja_importes")

lag = 1
lag_df = pd.DataFrame({"importe_t_menos_1": s.shift(lag), "importe_t": s}).dropna()
lag_df.to_csv(OUT / "ST05_rezago_1_datos.csv", index=False)
fig, ax = plt.subplots(figsize=(7.2, 6.2))
ax.scatter(lag_df["importe_t_menos_1"], lag_df["importe_t"], s=24, alpha=0.55, color=BLUE, edgecolors="none")
lim = max(lag_df.max())
ax.plot([0, lim], [0, lim], color=ORANGE, linestyle="--", linewidth=1.4, label="Referencia 1:1")
style(ax, "Relación entre semanas consecutivas", "Importe en la semana t (MXN)", "Importe en la semana t-1 (MXN)")
ax.legend(frameon=False, fontsize=9)
finish(fig, "ST05_rezago_1")

max_lag = 26
x = s.to_numpy(dtype=float)
x = x - np.nanmean(x)
den = np.nansum(x * x)
acf = [1.0]
for k in range(1, max_lag + 1):
    acf.append(float(np.nansum(x[k:] * x[:-k]) / den) if den else np.nan)
acf_df = pd.DataFrame({"rezago": range(max_lag + 1), "autocorrelacion": acf})
acf_df.to_csv(OUT / "ST06_autocorrelacion_datos.csv", index=False)
fig, ax = plt.subplots(figsize=(9.6, 5.5))
ax.vlines(acf_df["rezago"], 0, acf_df["autocorrelacion"], color=BLUE, linewidth=2)
ax.scatter(acf_df["rezago"], acf_df["autocorrelacion"], color=BLUE, s=25)
band = 1.96 / np.sqrt(len(x))
ax.axhspan(-band, band, color="#D9EAF7", alpha=0.8, label="Referencia aproximada del 95 %")
ax.axhline(0, color=GRAY, linewidth=0.8)
style(ax, "Autocorrelación del importe semanal", "Autocorrelación", "Rezago (semanas)")
ax.set_xticks(range(0, max_lag + 1, 2))
ax.legend(frameon=False, fontsize=9)
finish(fig, "ST06_autocorrelacion")

monthly = panel.assign(mes=panel["semana_inicio"].dt.month).groupby("mes")["total"].agg(["median", "mean", "count"]).reset_index()
monthly.to_csv(OUT / "ST07_perfil_mensual_datos.csv", index=False)
fig, ax = plt.subplots(figsize=(9.8, 5.6))
months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
ax.plot(monthly["mes"], monthly["median"], marker="o", color=BLUE, linewidth=2.2, label="Mediana")
ax.plot(monthly["mes"], monthly["mean"], marker="o", color=ORANGE, linewidth=1.8, label="Media")
style(ax, "Perfil descriptivo del importe semanal por mes", "Importe semanal (MXN)", "Mes")
ax.set_xticks(range(1, 13), months)
ax.legend(frameon=False, fontsize=9)
finish(fig, "ST07_perfil_mensual")

print(f"Figuras temporales generadas en {OUT}")
