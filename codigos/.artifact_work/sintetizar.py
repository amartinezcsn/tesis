from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\Python\tesis")
WORK = ROOT / "codigos" / ".artifact_work"
START = pd.Timestamp("2022-01-03")
END = pd.Timestamp("2024-01-22")
HOLDOUT_START = pd.Timestamp("2023-11-06")
WEEKS = pd.date_range(START, END, freq="W-MON")


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, np.generic):
        return value.item()
    return value


def payload(frame: pd.DataFrame, metadata: list[list[object]], date_columns: list[str], numeric_columns: list[str]):
    return {
        "headers": list(frame.columns),
        "rows": [[clean_value(v) for v in row] for row in frame.itertuples(index=False, name=None)],
        "metadata": metadata,
        "date_columns": date_columns,
        "numeric_columns": numeric_columns,
    }


def purchases_payload():
    source = ROOT / "datasets" / "xlsx" / "Compras.xlsx"
    raw = pd.read_excel(source, sheet_name="Hoja1")
    raw["FECHA"] = pd.to_datetime(raw["FECHA"], errors="coerce", dayfirst=True)
    raw["semana_inicio"] = raw["FECHA"].dt.to_period("W-SUN").dt.start_time
    data = raw.loc[raw["semana_inicio"].between(START, END)].copy()
    data["es_sintetico"] = False
    data["metodo_sintesis"] = ""

    missing = [w for w in WEEKS if w < HOLDOUT_START and w not in set(data["semana_inicio"])]
    generated = []
    for week in missing:
        available_weeks = sorted(data.loc[data["semana_inicio"] < week, "semana_inicio"].dropna().unique())[-8:]
        history = data.loc[data["semana_inicio"].isin(available_weeks)].copy()
        weekly_totals = history.groupby("semana_inicio")["MONTO"].sum()
        synthetic_total = round(float(weekly_totals.median()), 2)
        by_description = history.groupby("DESCRIPCION", dropna=True)["MONTO"].sum()
        by_description = by_description.loc[by_description > 0]
        shares = by_description / by_description.sum()
        amounts = (shares * synthetic_total).round(2)
        amounts.iloc[-1] += round(synthetic_total - float(amounts.sum()), 2)
        recent = history.sort_values("FECHA").drop_duplicates("DESCRIPCION", keep="last").set_index("DESCRIPCION")
        rows = []
        for number, (description, amount) in enumerate(amounts.items(), start=1):
            ref = recent.loc[description]
            rows.append({
                "PROVEEDOR": "SINTETICO_ENTRENAMIENTO",
                "FECHA": week,
                "NUMERO": f"SYN-C-{week:%Y%m%d}-{number:03d}",
                "CANT": 1.0,
                "U#MEDIDA": "semana",
                "DESCRIPCION": description,
                "MONTO": float(amount),
                "P#UNITARIO": float(amount),
                "CLASIFICACION": ref.get("CLASIFICACION"),
                "SUBCLASIFICACION": ref.get("SUBCLASIFICACION"),
                "semana_inicio": week,
                "es_sintetico": True,
                "metodo_sintesis": "mediana causal de 8 semanas y participacion historica por descripcion",
            })
        addition = pd.DataFrame(rows, columns=data.columns)
        data = pd.concat([data, addition], ignore_index=True)
        generated.append((week.strftime("%Y-%m-%d"), len(addition), synthetic_total))

    data = data.sort_values(["FECHA", "es_sintetico", "NUMERO"], kind="stable").reset_index(drop=True)
    metadata = [
        ["Archivo fuente", str(source)],
        ["Periodo", f"{START:%Y-%m-%d} a {END:%Y-%m-%d}"],
        ["Inicio de holdout real", f"{HOLDOUT_START:%Y-%m-%d}"],
        ["Semanas sintetizadas", len(generated)],
        ["Filas sintetizadas", int(data["es_sintetico"].sum())],
        ["Metodo", "Mediana causal de totales de las 8 semanas previas; distribucion por participacion historica de descripcion."],
        ["Restriccion", "Usar filas sinteticas solo para entrenamiento. No usarlas como objetivos de evaluacion ni evidencia observada."],
        ["Semanas generadas", ", ".join(x[0] for x in generated)],
    ]
    return payload(data, metadata, ["FECHA", "semana_inicio"], ["CANT", "MONTO", "P#UNITARIO"])


def sales_payload():
    source = ROOT / "datasets" / "xlsx" / "Ventas.xlsx"
    raw = pd.read_excel(source, sheet_name="Hoja1")
    raw["Fecha"] = pd.to_datetime(raw["Fecha"], errors="coerce", dayfirst=True)
    raw["Fecha/Hora"] = pd.to_datetime(raw["Fecha/Hora"], errors="coerce", dayfirst=True)
    raw["semana_inicio"] = raw["Fecha"].dt.to_period("W-SUN").dt.start_time
    data = raw.loc[raw["semana_inicio"].between(START, END)].copy()
    data["es_sintetico"] = False
    data["metodo_sintesis"] = ""

    missing = [w for w in WEEKS if w < HOLDOUT_START and w not in set(data["semana_inicio"])]
    generated = []
    for week in missing:
        available_weeks = sorted(data.loc[data["semana_inicio"] < week, "semana_inicio"].dropna().unique())[-8:]
        history = data.loc[data["semana_inicio"].isin(available_weeks)]
        weekly_totals = history.groupby("semana_inicio")["Importe"].sum()
        synthetic_total = round(float(weekly_totals.median()), 2)
        row = {column: None for column in data.columns}
        row.update({
            "Number": f"SYN-V-{week:%Y%m%d}",
            "Status": "Sintetico_entrenamiento",
            "Fecha/Hora": week,
            "Cantidad": 1.0,
            "Total de �tems": 1.0,
            "Descri. Items": "Venta semanal sintetica para continuidad temporal",
            "Subtotal": synthetic_total,
            "Descuento": 0.0,
            "Tasa": 0.0,
            "Env�o": 0.0,
            "Importe": synthetic_total,
            "Fecha": week,
            "A�o": week.year,
            "Mes": week.month,
            "D�a": week.day,
            "NumPedido": f"SYN-V-{week:%Y%m%d}",
            "semana_inicio": week,
            "es_sintetico": True,
            "metodo_sintesis": "mediana causal del total de las 8 semanas previas",
        })
        data = pd.concat([data, pd.DataFrame([row], columns=data.columns)], ignore_index=True)
        generated.append((week.strftime("%Y-%m-%d"), synthetic_total))

    data = data.sort_values(["Fecha", "es_sintetico", "Number"], kind="stable").reset_index(drop=True)
    metadata = [
        ["Archivo fuente", str(source)],
        ["Periodo", f"{START:%Y-%m-%d} a {END:%Y-%m-%d}"],
        ["Inicio de holdout real", f"{HOLDOUT_START:%Y-%m-%d}"],
        ["Semanas sintetizadas", len(generated)],
        ["Filas sintetizadas", int(data["es_sintetico"].sum())],
        ["Metodo", "Mediana causal del importe semanal de las 8 semanas previas."],
        ["Restriccion", "Usar filas sinteticas solo para entrenamiento. No usarlas como objetivos de evaluacion ni evidencia observada."],
        ["Semanas generadas", ", ".join(x[0] for x in generated)],
    ]
    numeric = ["Cantidad", "Total de �tems", "Subtotal", "Descuento", "Tasa", "Env�o", "Importe", "Ganancia", "A�o", "Mes", "D�a", "Pastel", "Galletas", "Otros", "Cupcakes", "Pedido"]
    return payload(data, metadata, ["Fecha/Hora", "Fecha", "semana_inicio"], numeric)


WORK.mkdir(parents=True, exist_ok=True)
(WORK / "compras.json").write_text(json.dumps(purchases_payload(), ensure_ascii=False, allow_nan=False), encoding="utf-8")
(WORK / "ventas.json").write_text(json.dumps(sales_payload(), ensure_ascii=False, allow_nan=False), encoding="utf-8")
