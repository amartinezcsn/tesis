"""Genera el paquete curado de figuras para revisión editorial de la tesis.

No modifica el DOCX. Lee únicamente artefactos persistidos de corridas
completadas y guarda PNG, SVG, datos derivados y un manifiesto.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "output/run_20261013T193604Z_157556"
ABLATIONS = {
    "Solo compras": ROOT / "output/run_20261013T194927Z_fe8b96",
    "Compras + ventas": ROOT / "output/run_20261013T195442Z_5fed8f",
    "Compras + calendario": ROOT / "output/run_20261013T195837Z_713fcd",
    "Modelo completo": ROOT / "output/run_20261013T194232Z_d0a239",
}
OUT = ROOT / "documentacion/figuras_propuesta_20261013"

COLORS = {
    "hibrido": "#0072B2",
    "ultimo_valor": "#D55E00",
    "estadistico": "#009E73",
    "ml": "#CC79A7",
    "gris": "#5F6368",
    "claro": "#D9EAF3",
}


def setup():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.titlesize": 11,
        "axes.labelsize": 9.5,
        "legend.fontsize": 8.5,
        "figure.titlesize": 13,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.22,
        "grid.linewidth": 0.7,
    })


def save(fig, stem, title, chapter, sources, data=None):
    fig.subplots_adjust(top=0.88)
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if data is not None:
        data.to_csv(OUT / f"{stem}_datos.csv", index=False)
    return {
        "id": stem,
        "titulo": title,
        "capitulo_sugerido": chapter,
        "fuentes": sources,
    }


def fig01_process():
    parts = pd.read_csv(RUN / "particiones.csv", parse_dates=["origen", "fecha_objetivo",
        "entrenamiento_inicio", "ultima_etiqueta_entrenamiento"])
    evalp = parts[parts.etapa.eq("evaluacion")]
    fig, (ax, timeline) = plt.subplots(2, 1, figsize=(11.5, 6.2),
        gridspec_kw={"height_ratios": [1.05, 1]})
    ax.axis("off")
    labels = ["Fuentes\nauditadas", "Cobertura y\ncatálogo", "Panel semanal\ncon huecos",
        "Selección\ninterna", "Pronóstico\ndel total", "Composición y\nasignación"]
    xs = np.linspace(0.06, 0.94, len(labels))
    for i, (x, label) in enumerate(zip(xs, labels)):
        rect = patches.FancyBboxPatch((x - .072, .39), .144, .28,
            boxstyle="round,pad=0.015", fc="#EAF2F8" if i < 4 else "#DDEBF7",
            ec="#3B6E8F", lw=1.2, transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(x, .53, label, ha="center", va="center", transform=ax.transAxes,
            fontsize=9.5, weight="bold" if i in (3, 4, 5) else "normal")
        if i < len(labels)-1:
            ax.annotate("", xy=(xs[i+1]-.078, .53), xytext=(x+.078, .53),
                xycoords=ax.transAxes, arrowprops=dict(arrowstyle="->", color="#3B6E8F", lw=1.4))
    ax.text(.5, .16, "La evaluación final no retroalimenta la selección del modelo ni de categorías.",
        ha="center", transform=ax.transAxes, color=COLORS["gris"])
    for h, grp in evalp.groupby("horizonte"):
        timeline.scatter(grp.fecha_objetivo, [h]*len(grp), s=30, marker="o",
            label=f"H{h}", alpha=.78)
    origins = sorted(evalp.origen.unique())
    for origin in origins:
        timeline.axvline(origin, color="#B0B0B0", lw=.45, alpha=.28)
    timeline.set_yticks([1,2,3,4], ["H1", "H2", "H3", "H4"])
    timeline.set_ylabel("Horizonte")
    timeline.set_xlabel("Fecha objetivo de evaluación final")
    timeline.set_title("Diseño rolling-origin con paso semanal y 17 orígenes")
    timeline.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    timeline.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    timeline.grid(axis="x", alpha=.2)
    fig.suptitle("Proceso analítico y separación temporal de la evaluación")
    return save(fig, "P01_proceso_validacion", "Proceso analítico y separación temporal de la evaluación",
        "Metodología", ["particiones.csv"], evalp)


def fig02_coverage():
    panel = pd.read_csv(RUN / "panel_semanal.csv", parse_dates=["semana_inicio"])
    cov = pd.read_csv(RUN / "cobertura.csv", parse_dates=["semana_inicio"])
    states = ["observada", "cero_confirmado", "incierta", "incompleta", "desconocida"]
    palette = {"observada":"#56B4E9", "cero_confirmado":"#009E73", "incierta":"#E69F00",
        "incompleta":"#F0E442", "desconocida":"#B8B8B8"}
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 6.4), sharex=True,
        gridspec_kw={"height_ratios":[.55, 2.3]})
    for i, state in enumerate(states):
        dates = cov.loc[cov.estado.eq(state), "semana_inicio"]
        ax1.scatter(dates, np.zeros(len(dates)), marker="s", s=15, color=palette[state], label=state)
    ax1.set_yticks([]); ax1.set_title("Estado documentado de cada semana", loc="left")
    ax1.legend(ncol=5, loc="upper center", bbox_to_anchor=(.5, 1.45), frameon=False)
    observed = panel.total.notna()
    ax2.plot(panel.semana_inicio, panel.total.where(observed), color=COLORS["hibrido"], lw=1.25)
    ax2.scatter(panel.loc[observed & panel.total.eq(0), "semana_inicio"],
        panel.loc[observed & panel.total.eq(0), "total"], s=11, color=COLORS["ultimo_valor"],
        label="Cero elegible observado")
    ax2.set_ylabel("Importe elegible semanal (MXN nominales)")
    ax2.set_xlabel("Semana de inicio")
    ax2.set_title("Serie semanal conservando los huecos de captura", loc="left")
    ax2.legend(frameon=False)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("Cobertura y evolución del gasto semanal elegible")
    data = panel[["semana_inicio","total"]].merge(cov[["semana_inicio","estado"]], on="semana_inicio")
    return save(fig, "P02_cobertura_serie", "Cobertura y evolución del gasto semanal elegible",
        "Desarrollo", ["panel_semanal.csv", "cobertura.csv"], data)


def fig03_categories():
    panel = pd.read_csv(RUN / "panel_semanal.csv", parse_dates=["semana_inicio"]).set_index("semana_inicio")
    selection = json.loads((RUN / "seleccion.json").read_text(encoding="utf-8"))
    cutoff = pd.Timestamp(selection["corte_desarrollo"])
    selected = selection["categorias"]
    history = panel.loc[panel.index < cutoff].drop(columns="total")
    sums = history.sum().sort_values(ascending=False)
    sums = sums[sums.gt(0)]
    cumulative = sums.cumsum()/sums.sum()*100
    top = sums.head(15)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 8.8),
        gridspec_kw={"height_ratios":[1.1, 1.35], "hspace":.48})
    colors = [COLORS["hibrido"] if c in selected else "#AAB7B8" for c in top.index]
    ax1.bar(np.arange(len(top)), top.values, color=colors)
    ax1.set_xticks(np.arange(len(top)), top.index, rotation=42, ha="right")
    ax1.set_ylabel("Importe acumulado (MXN)")
    ax1b = ax1.twinx(); ax1b.grid(False)
    ax1b.plot(np.arange(len(top)), cumulative.loc[top.index], color=COLORS["ultimo_valor"],
        marker="o", ms=3.5, lw=1.5)
    ax1b.axhline(80, ls="--", color=COLORS["gris"], lw=1)
    ax1b.set_ylabel("Participación acumulada (%)")
    ax1.set_title("Pareto calculado solo con el conjunto de desarrollo", loc="left")
    positive = panel.loc[(panel.index < cutoff) & panel.total.gt(0), selected].copy()
    shares = positive.div(panel.loc[positive.index, "total"], axis=0)*100
    recent = shares.tail(60).T
    im = ax2.imshow(recent, aspect="auto", interpolation="nearest", cmap="Blues", vmin=0,
        vmax=max(10, np.nanpercentile(recent.values, 95)))
    ax2.set_yticks(range(len(recent.index)), recent.index)
    ticks = np.linspace(0, len(recent.columns)-1, 6).astype(int)
    ax2.set_xticks(ticks, [recent.columns[i].strftime("%Y-%m-%d") for i in ticks], rotation=25, ha="right")
    ax2.set_title("Participación observada de categorías principales en las últimas 60 semanas positivas", loc="left")
    ax2.set_xlabel("Semana"); ax2.set_ylabel("Categoría")
    fig.colorbar(im, ax=ax2, label="Participación del total semanal (%)", fraction=.025, pad=.02)
    fig.suptitle("Selección de categorías y variación de la composición")
    data = pd.DataFrame({"categoria":sums.index, "importe":sums.values,
        "participacion_acumulada_pct":cumulative.values, "seleccionada":sums.index.isin(selected)})
    return save(fig, "P03_pareto_composicion", "Selección de categorías y variación de la composición",
        "Desarrollo", ["panel_semanal.csv", "seleccion.json"], data)


def fig04_predictions():
    pred = pd.read_csv(RUN / "predicciones.csv", parse_dates=["origen","fecha_objetivo"])
    d = pred[(pred.horizonte.eq(1)) & pred.modelo.isin(["hibrido","ultimo_valor"])].copy()
    wide = d.pivot(index="fecha_objetivo", columns="modelo", values="prediccion")
    real = d.groupby("fecha_objetivo").real.first()
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.plot(real.index, real, color="black", marker="o", lw=1.7, label="Observado")
    ax.plot(wide.index, wide.hibrido, color=COLORS["hibrido"], marker="s", lw=1.45, label="Híbrido")
    ax.plot(wide.index, wide.ultimo_valor, color=COLORS["ultimo_valor"], marker="^", lw=1.35,
        ls="--", label="Último valor")
    ax.set_ylabel("Importe semanal (MXN nominales)"); ax.set_xlabel("Fecha objetivo")
    ax.set_title("Evaluación final sobre fechas comunes del horizonte principal", loc="left")
    ax.legend(frameon=False, ncol=3)
    ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    fig.suptitle("Importe observado y pronósticos fuera de muestra")
    out = wide.join(real.rename("real")).reset_index()
    return save(fig, "P04_observado_pronosticado", "Importe observado y pronósticos fuera de muestra",
        "Resultados", ["predicciones.csv"], out)


def fig05_metrics():
    metrics = pd.read_csv(RUN / "metricas.csv")
    models = ["hibrido", "ultimo_valor", "ss_arima111", "nn_residual__ss_arima111"]
    labels = {"hibrido":"Híbrido", "ultimo_valor":"Último valor", "ss_arima111":"Estado espacial ARIMA",
        "nn_residual__ss_arima111":"Red residual"}
    colors = [COLORS["hibrido"], COLORS["ultimo_valor"], COLORS["estadistico"], COLORS["ml"]]
    d = metrics[metrics.modelo.isin(models) & metrics.comparacion.eq("principal_fechas_comunes")]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharex=True)
    x=np.arange(1,5); width=.19
    for j, model in enumerate(models):
        q=d[d.modelo.eq(model)].set_index("horizonte")
        axes[0].bar(x+(j-1.5)*width, q.rmse.reindex(x), width, color=colors[j], label=labels[model])
        axes[1].bar(x+(j-1.5)*width, q.mae.reindex(x), width, color=colors[j], label=labels[model])
    for ax, metric in zip(axes,["RMSE", "MAE"]):
        ax.set_xticks(x, [f"H{i}" for i in x]); ax.set_xlabel("Horizonte semanal")
        ax.set_ylabel(f"{metric} (MXN)"); ax.set_title(metric)
    axes[0].legend(frameon=False, ncol=2, loc="upper left")
    fig.suptitle("Errores monetarios en la evaluación final")
    return save(fig, "P05_metricas_monetarias", "Errores monetarios en la evaluación final",
        "Resultados", ["metricas.csv"], d)


def fig06_composition_error():
    m = pd.read_csv(RUN / "metricas_composicion.csv")
    h1=m[(m.horizonte.eq(1)) & ~m.insumo_id.eq("PROMEDIO_MACRO")].copy()
    cats = h1.groupby("insumo_id").mae_pp.mean().sort_values(ascending=True).index
    fig, (ax1, ax2)=plt.subplots(1,2,figsize=(11.5,5.5),gridspec_kw={"width_ratios":[1.35,1]})
    y=np.arange(len(cats)); height=.36
    for off,model,color,label in [(-height/2,"participacion_historica",COLORS["ultimo_valor"],"Histórica"),
        (height/2,"participacion_ewm",COLORS["hibrido"],"EWM")]:
        q=h1[h1.modelo.eq(model)].set_index("insumo_id").reindex(cats)
        ax1.barh(y+off,q.mae_pp,height,color=color,label=label)
    ax1.set_yticks(y,cats); ax1.set_xlabel("MAE (puntos porcentuales)")
    ax1.set_title("Por categoría en H1",loc="left"); ax1.legend(frameon=False)
    macro=m[m.insumo_id.eq("PROMEDIO_MACRO")]
    for model,color,label,marker in [("participacion_historica",COLORS["ultimo_valor"],"Histórica","^"),
        ("participacion_ewm",COLORS["hibrido"],"EWM","o")]:
        q=macro[macro.modelo.eq(model)].sort_values("horizonte")
        ax2.plot(q.horizonte,q.mae_pp,marker=marker,color=color,label=label,lw=1.6)
    ax2.set_xticks([1,2,3,4],["H1","H2","H3","H4"]); ax2.set_ylabel("MAE macro (puntos porcentuales)")
    ax2.set_title("Promedio macro por horizonte",loc="left"); ax2.legend(frameon=False)
    fig.suptitle("Error de la distribución porcentual del presupuesto")
    return save(fig,"P06_error_composicion","Error de la distribución porcentual del presupuesto",
        "Resultados",["metricas_composicion.csv"],m)


def fig07_hypothesis():
    pred=pd.read_csv(RUN/"predicciones.csv",parse_dates=["fecha_objetivo"])
    p=pred[(pred.horizonte.eq(1)) & pred.modelo.isin(["hibrido","ultimo_valor"])]
    w=p.pivot(index="fecha_objetivo",columns="modelo",values=["real","prediccion"])
    real=w["real"].hibrido; money=(real-w["prediccion"].ultimo_valor)**2-(real-w["prediccion"].hibrido)**2
    comp=pd.read_csv(RUN/"composicion.csv",parse_dates=["fecha_objetivo"])
    c=comp[(comp.horizonte.eq(1)) & comp.modelo.isin(["participacion_historica","participacion_ewm"])].copy()
    c["ae_pp"]=(c.real-c.prediccion).abs()*100
    cm=c.groupby(["fecha_objetivo","modelo"]).ae_pp.mean().unstack()
    cdiff=cm.participacion_historica-cm.participacion_ewm
    hyp=json.loads((RUN/"hipotesis.json").read_text(encoding="utf-8"))
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(11.5,6.8),sharex=False)
    ax1.axhline(0,color="black",lw=.8); ax1.plot(money.index,money.values,marker="o",color=COLORS["hibrido"],lw=1)
    ax1.axhline(hyp["importe"]["media"],color=COLORS["ultimo_valor"],ls="--",label="Media pareada")
    ax1.set_ylabel("Diferencia de error cuadrático (MXN²)"); ax1.set_title("Componente monetario",loc="left")
    ax1.legend(frameon=False)
    ax2.axhline(0,color="black",lw=.8); ax2.plot(cdiff.index,cdiff.values,marker="s",color=COLORS["estadistico"],lw=1)
    ax2.axhline(hyp["composicion"]["media"],color=COLORS["ultimo_valor"],ls="--",label="Media pareada")
    ax2.set_ylabel("Diferencia de MAE (puntos porcentuales)"); ax2.set_xlabel("Fecha objetivo")
    ax2.set_title("Componente de composición",loc="left"); ax2.legend(frameon=False)
    fig.suptitle("Diferencias de pérdida para el contraste H1\nValores positivos favorecen el método propuesto")
    data=pd.concat([money.rename("diferencia_monetaria_mxn2"),cdiff.rename("diferencia_composicion_pp")],axis=1).reset_index()
    return save(fig,"P07_contraste_H1","Diferencias de pérdida para el contraste H1",
        "Resultados",["predicciones.csv","composicion.csv","hipotesis.json"],data)


def fig08_ablation():
    rows=[]
    for scenario,path in ABLATIONS.items():
        d=pd.read_csv(path/"metricas.csv")
        d=d[(d.modelo.eq("hibrido")) & d.comparacion.eq("principal_fechas_comunes")]
        for _,r in d.iterrows(): rows.append({"escenario":scenario,"horizonte":r.horizonte,"rmse":r.rmse})
    data=pd.DataFrame(rows); base=data[data.escenario.eq("Solo compras")].set_index("horizonte").rmse
    data["delta_rmse_vs_compras"]=data.apply(lambda r:r.rmse-base.loc[r.horizonte],axis=1)
    fig,ax=plt.subplots(figsize=(10.5,5.2)); ax.axhline(0,color="black",lw=.8)
    palette=[COLORS["ultimo_valor"],"#56B4E9",COLORS["estadistico"],COLORS["hibrido"]]
    markers=["o","s","^","D"]
    for (scenario,q),color,marker in zip(data.groupby("escenario",sort=False),palette,markers):
        if scenario=="Solo compras": continue
        ax.plot(q.horizonte,q.delta_rmse_vs_compras,marker=marker,lw=1.7,color=color,label=scenario)
    ax.set_xticks([1,2,3,4],["H1","H2","H3","H4"]); ax.set_xlabel("Horizonte semanal")
    ax.set_ylabel("Cambio de RMSE frente a solo compras (MXN)")
    ax.legend(frameon=False); ax.set_title("Valores negativos indican menor error",loc="left")
    fig.suptitle("Ablación de ventas y variables de calendario")
    return save(fig,"P08_ablaciones","Ablación de ventas y variables de calendario",
        "Discusión",[str(p.name)+"/metricas.csv" for p in ABLATIONS.values()],data)


def fig09_budget():
    future=pd.read_csv(RUN/"pronostico_futuro.csv")
    agg=pd.read_csv(RUN/"pronostico_4_semanas.csv").sort_values("importe_4_semanas")
    pivot=future.pivot(index="horizonte",columns="insumo_id",values="importe").fillna(0)
    order=agg.sort_values("importe_4_semanas",ascending=False).insumo_id.tolist()
    pivot=pivot.reindex(columns=order)
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(11.5,5.5),gridspec_kw={"width_ratios":[1.2,1]})
    cmap=plt.get_cmap("tab20"); bottom=np.zeros(len(pivot))
    for i,col in enumerate(pivot.columns):
        ax1.bar(pivot.index,pivot[col],bottom=bottom,label=col,color=cmap(i%20))
        bottom+=pivot[col].values
    ax1.set_xticks([1,2,3,4],["H1","H2","H3","H4"]); ax1.set_ylabel("Importe (MXN)")
    ax1.set_title("Asignación por semana futura",loc="left")
    ax2.barh(np.arange(len(agg)),agg.importe_4_semanas,color=COLORS["hibrido"])
    ax2.set_yticks(np.arange(len(agg)),agg.insumo_id); ax2.set_xlabel("Importe de cuatro semanas (MXN)")
    ax2.set_title("Presupuesto agregado",loc="left")
    ax1.legend(ncol=2,fontsize=7,frameon=False,bbox_to_anchor=(1.02,-.12),loc="upper center")
    fig.suptitle("Emisión histórica del presupuesto y reconciliación por categoría")
    return save(fig,"P09_presupuesto","Emisión histórica del presupuesto y reconciliación por categoría",
        "Resultados",["pronostico_futuro.csv","pronostico_4_semanas.csv"],agg)


def main():
    setup()
    manifest=[fig01_process(),fig02_coverage(),fig03_categories(),fig04_predictions(),
        fig05_metrics(),fig06_composition_error(),fig07_hypothesis(),fig08_ablation(),fig09_budget()]
    for item in manifest:
        for ext in ("png","svg"):
            path=OUT/f"{item['id']}.{ext}"
            item[f"sha256_{ext}"]=hashlib.sha256(path.read_bytes()).hexdigest()
    pd.DataFrame(manifest).to_csv(OUT/"manifiesto_figuras.csv",index=False)
    (OUT/"manifiesto_figuras.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Figuras guardadas en: {OUT}")


if __name__ == "__main__":
    main()
