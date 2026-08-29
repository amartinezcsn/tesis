"""Genera reportes legibles de los resultados semanales."""

import os

import pandas as pd

from config_semanal import HORIZON_WEEKS, PRIMARY_BASELINE, SECONDARY_HORIZON_WEEKS, ensure_output_dir


def main() -> None:
    """Exporta una síntesis Markdown y una gráfica de comparación por RMSE."""
    output_dir = ensure_output_dir()
    source = output_dir / "02_modelos_rolling_window.xlsx"
    metrics = pd.read_excel(source, sheet_name="metricas")
    h1 = pd.read_excel(source, sheet_name="contraste_h1")
    h2 = pd.read_excel(source, sheet_name="contraste_h2")
    monthly = pd.read_excel(source, sheet_name="consolidado_4_semanas")
    primary_metrics = metrics.loc[metrics["horizonte_semanas"].eq(HORIZON_WEEKS)].reset_index(drop=True)
    secondary_metrics = metrics.loc[metrics["horizonte_semanas"].eq(SECONDARY_HORIZON_WEEKS)].reset_index(drop=True)
    winner_h1 = primary_metrics.iloc[0]
    winner_h4 = secondary_metrics.iloc[0]

    lines = [
        "# Resultados del pronóstico semanal",
        "",
        "## Configuración de referencia",
        f"- Línea base primaria para H1: `{PRIMARY_BASELINE}`.",
        f"- Mejor h=1: `{winner_h1['modelo']}` ({winner_h1['feature_set']}); RMSE {winner_h1['rmse']:.4f}; MAE {winner_h1['mae']:.4f}.",
        f"- Mejor h=4: `{winner_h4['modelo']}` ({winner_h4['feature_set']}); RMSE {winner_h4['rmse']:.4f}; MAE {winner_h4['mae']:.4f}.",
        f"- Consolidado mensual: {len(monthly)} presupuestos históricos de cuatro semanas, cada uno como suma de h=1+h=2+h=3+h=4.",
        "",
        "## Interpretación",
        "- H1 y H2 se interpretan con las tablas de contraste y no sólo con el ranking.",
        "- MAPE es diagnóstico: no se usa para seleccionar el modelo ni aceptar hipótesis.",
        "- H1 se interpreta principalmente en h=1; h=4 se reporta como evidencia complementaria de planeación.",
        "- El consolidado mensual no equivale a un modelo mensual independiente.",
    ]
    (output_dir / "03_resumen_resultados_semanales.md").write_text("\n".join(lines), encoding="utf-8")

    try:
        # ``Agg`` permite generar el PNG en servidores y automatizaciones sin
        # una interfaz gráfica. La caché también se mantiene dentro del
        # proyecto para no depender del perfil local del usuario.
        os.environ.setdefault("MPLBACKEND", "Agg")
        os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".matplotlib"))
        import matplotlib.pyplot as plt

        figure, axes = plt.subplots(1, 2, figsize=(16, max(5, len(primary_metrics) * 0.32)))
        for axis, horizon, data in zip(axes, (HORIZON_WEEKS, SECONDARY_HORIZON_WEEKS), (primary_metrics, secondary_metrics)):
            ordered = data.sort_values("rmse", ascending=True).copy()
            labels = ordered["modelo"] + " | " + ordered["feature_set"]
            axis.barh(labels, ordered["rmse"], color="#356b8c")
            axis.invert_yaxis()
            axis.set_xlabel(f"RMSE semanal directo h={horizon}")
            axis.set_title(f"Comparación h={horizon}")
        figure.suptitle("Rolling-window: horizontes h=1 y h=4 separados")
        figure.tight_layout()
        figure.savefig(output_dir / "03_ranking_rmse_semanal.png", dpi=180)
        plt.close(figure)
    except ImportError:
        pass

    print(f"Reportes generados en: {output_dir}")


if __name__ == "__main__":
    main()
