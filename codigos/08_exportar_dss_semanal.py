"""Prepara datos auditables para el tablero de presupuesto semanal.

El archivo exportado contiene resultados históricos validados. Un pronóstico de
una semana futura sólo debe agregarse cuando exista un archivo de variables
exógenas futuras con calendario, INPC publicado y clima pronosticado; este
módulo evita fabricar dichos valores cuando la fuente no está disponible.
"""

import json

import numpy as np
import pandas as pd

from config_semanal import FORECAST_HORIZONS, PRIMARY_BASELINE, PRIMARY_HORIZON_WEEKS, TARGET_COLUMN, DATE_COLUMN, WEEKLY_MODEL_PATH, ensure_output_dir


def _records(frame: pd.DataFrame) -> list[dict]:
    """Convierte tablas a registros JSON sin emitir NaN no estándar."""
    clean = frame.replace([np.inf, -np.inf], np.nan).replace({np.nan: None})
    return clean.to_dict(orient="records")


def main() -> None:
    """Exporta métricas y predicciones de evaluación a JSON para el DSS."""
    output_dir = ensure_output_dir()
    source = output_dir / "02_modelos_rolling_window.xlsx"
    metrics = pd.read_excel(source, sheet_name="metricas")
    predictions = pd.read_excel(source, sheet_name="predicciones")
    h1 = pd.read_excel(source, sheet_name="contraste_h1")
    h2 = pd.read_excel(source, sheet_name="contraste_h2")
    monthly = pd.read_excel(source, sheet_name="consolidado_4_semanas")
    dictionary = pd.read_excel(WEEKLY_MODEL_PATH, sheet_name="diccionario")
    exogenous = dictionary.loc[dictionary["grupo"].eq("exógena")].fillna("")
    coverage = pd.read_excel(source, sheet_name="cobertura")
    for column in ("origen_pronostico", "semana_prueba"):
        predictions[column] = pd.to_datetime(predictions[column]).dt.strftime("%Y-%m-%d")
    payload = {
        "producto": "DSS semanal de presupuesto de abastecimiento",
        "objetivo": TARGET_COLUMN,
        "frecuencia": "semanal",
        "ventana_entrenamiento_semanas": 52,
        "horizontes_evaluados_semanas": list(FORECAST_HORIZONS),
        "horizonte_principal_semanas": PRIMARY_HORIZON_WEEKS,
        "horizonte_complementario_semanas": SECONDARY_HORIZON_WEEKS if 'SECONDARY_HORIZON_WEEKS' in globals() else 4,
        "linea_base_primaria": PRIMARY_BASELINE,
        "consolidado_mensual": "Suma de pronósticos directos h=1+h=2+h=3+h=4; no es un modelo mensual independiente.",
        "metricas": _records(metrics),
        "contraste_h1": _records(h1),
        "contraste_h2": _records(h2),
        "cobertura": _records(coverage),
        "predicciones_validacion": _records(predictions),
        "consolidados_4_semanas_validacion": monthly.to_dict(orient="records"),
        "variables_exogenas_registradas": exogenous.to_dict(orient="records"),
        "pronostico_futuro": {
            "estado": "no_disponible",
            "motivo": "No existe un archivo de exógenas futuras validado para la fecha de emisión.",
            "requisitos": [
                "calendario y fechas comerciales futuras",
                "último INPC publicado",
                "temperatura pronosticada o una regla de disponibilidad documentada",
            ],
        },
        "advertencia": "El archivo comunica evaluación histórica. No emite una compra futura sin variables exógenas registradas y disponibles ex ante.",
    }
    target = output_dir / "04_dss_semanal.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Archivo generado: {target}")


if __name__ == "__main__":
    main()
