"""Genera reportes legibles de los resultados semanales."""

import os

import pandas as pd

from config_semanal import (
    FORECAST_HORIZONS,
    PRIMARY_BASELINE,
    PRIMARY_HORIZON_WEEKS,
    ensure_output_dir,
)


def main() -> None:
    """Exporta una síntesis Markdown y una gráfica de comparación por RMSE."""
    output_dir = ensure_output_dir()
    source = output_dir / "02_modelos_rolling_window.xlsx"
    metrics = pd.read_excel(source, sheet_name="metricas")
    h1 = pd.read_excel(source, sheet_name="contraste_h1")
    h2 = pd.read_excel(source, sheet_name="contraste_h2")
    primary_metrics = metrics.loc[metrics["horizonte"].eq(PRIMARY_HORIZON_WEEKS)]
    if primary_metrics.empty:
        raise ValueError("No hay métricas para el horizonte principal.")
    winner = primary_metrics.iloc[0]
    horizons = ", ".join(f"H={h}" for h in FORECAST_HORIZONS)
    h1_primary = h1.loc[h1["horizonte"].eq(PRIMARY_HORIZON_WEEKS)]
    h2_primary = h2.loc[h2["horizonte"].eq(PRIMARY_HORIZON_WEEKS)]
    supported_h1 = int(h1_primary["apoya_hipotesis"].fillna(False).sum()) if not h1_primary.empty else 0
    supported_h2 = int(h2_primary["apoya_hipotesis"].fillna(False).sum()) if not h2_primary.empty else 0

    lines = [
        "# Resultados del pronóstico semanal",
        "",
        "## Configuración de referencia",
        f"- Horizontes evaluados: {horizons}; el principal es H={PRIMARY_HORIZON_WEEKS}.",
        f"- Línea base primaria para H1: `{PRIMARY_BASELINE}`.",
        f"- Modelo con menor RMSE: `{winner['modelo']}` ({winner['feature_set']}).",
        f"- RMSE: {winner['rmse']:.4f}; MAE: {winner['mae']:.4f}; MASE: {winner['mase']:.4f}.",
        f"- Contrastes H1 con apoyo estadístico y umbral de 20% en H=1: {supported_h1}.",
        f"- Contrastes H2 con apoyo estadístico y mejora direccional en H=1: {supported_h2}.",
        "",
        "## Interpretación",
        "- H1 y H2 se interpretan con las tablas de contraste y no sólo con el ranking.",
        "- MAPE es diagnóstico: no se usa para seleccionar el modelo ni aceptar hipótesis.",
        "- Las conclusiones se limitan a precisión del presupuesto semanal.",
    ]
    (output_dir / "03_resumen_resultados_semanales.md").write_text("\n".join(lines), encoding="utf-8")

    try:
        # ``Agg`` permite generar el PNG en servidores y automatizaciones sin
        # una interfaz gráfica. La caché también se mantiene dentro del
        # proyecto para no depender del perfil local del usuario.
        os.environ.setdefault("MPLBACKEND", "Agg")
        os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".matplotlib"))
        import matplotlib.pyplot as plt

        ordered = metrics.sort_values("rmse", ascending=True).copy()
        labels = ordered["modelo"] + " | " + ordered["feature_set"]
        figure, axis = plt.subplots(figsize=(10, max(4, len(ordered) * 0.35)))
        axis.barh(labels, ordered["rmse"], color="#356b8c")
        axis.invert_yaxis()
        axis.set_xlabel("RMSE semanal")
        axis.set_title("Comparación de modelos mediante rolling-window")
        figure.tight_layout()
        figure.savefig(output_dir / "03_ranking_rmse_semanal.png", dpi=180)
        plt.close(figure)
    except ImportError:
        pass

    print(f"Reportes generados en: {output_dir}")


if __name__ == "__main__":
    main()
