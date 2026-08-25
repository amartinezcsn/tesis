"""Prepara datos auditables para el tablero de presupuesto semanal.

El archivo exportado contiene resultados históricos validados. Un pronóstico de
una semana futura sólo debe agregarse cuando exista un archivo de variables
exógenas futuras con calendario, INPC publicado y clima pronosticado; este
módulo evita fabricar dichos valores cuando la fuente no está disponible.
"""

import json

import pandas as pd

from config_semanal import DATE_COLUMN, ensure_output_dir


def main() -> None:
    """Exporta métricas y predicciones de evaluación a JSON para el DSS."""
    output_dir = ensure_output_dir()
    source = output_dir / "02_modelos_rolling_window.xlsx"
    metrics = pd.read_excel(source, sheet_name="metricas")
    predictions = pd.read_excel(source, sheet_name="predicciones")
    h1 = pd.read_excel(source, sheet_name="contraste_h1")
    h2 = pd.read_excel(source, sheet_name="contraste_h2")
    predictions["semana_prueba"] = pd.to_datetime(predictions["semana_prueba"]).dt.strftime("%Y-%m-%d")
    payload = {
        "frecuencia": "semanal",
        "ventana_entrenamiento_semanas": 52,
        "horizonte_principal_semanas": 1,
        "consolidado_mensual": "Suma de pronósticos semanales; requiere exógenas futuras válidas.",
        "metricas": metrics.to_dict(orient="records"),
        "contraste_h1": h1.to_dict(orient="records"),
        "contraste_h2": h2.to_dict(orient="records"),
        "predicciones_validacion": predictions.to_dict(orient="records"),
        "advertencia": "El archivo comunica evaluación histórica. No emite una compra futura sin variables exógenas disponibles ex ante.",
    }
    target = output_dir / "04_dss_semanal.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Archivo generado: {target}")


if __name__ == "__main__":
    main()
