from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\Python\tesis\codigos")
WORK = ROOT / ".artifact_work"
INPUT_DIR = ROOT / "outputs" / "complemento_rolling_2022_2024"
START = pd.Timestamp("2022-01-03")
END = pd.Timestamp("2024-01-22")
HOLDOUT_START = pd.Timestamp("2023-11-06")
REVIEW_DATE = pd.Timestamp("2026-09-12")


def normalized(value):
    if pd.isna(value) or not str(value).strip():
        return None
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.upper()).strip()


def slug(value):
    text = normalized(value) or "SIN_NOMBRE"
    return re.sub(r"[^A-Z0-9]+", "_", text).strip("_").lower()


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, np.generic):
        return value.item()
    return value


def payload(frame, metadata, date_columns, numeric_columns):
    return {
        "headers": list(frame.columns),
        "rows": [[clean_value(v) for v in row] for row in frame.itertuples(index=False, name=None)],
        "metadata": metadata,
        "date_columns": date_columns,
        "numeric_columns": numeric_columns,
    }


purchases_path = INPUT_DIR / "Compras_complementadas_entrenamiento.xlsx"
sales_path = INPUT_DIR / "Ventas_complementadas_entrenamiento.xlsx"
purchases = pd.read_excel(purchases_path, sheet_name="Datos")
purchases["FECHA"] = pd.to_datetime(purchases["FECHA"])
purchases["semana_inicio"] = pd.to_datetime(purchases["semana_inicio"])
purchases["descripcion_normalizada"] = purchases["DESCRIPCION"].map(normalized)
purchases["clasificacion_normalizada"] = purchases["CLASIFICACION"].map(normalized)
purchases["es_sintetico"] = purchases["es_sintetico"].fillna(False).astype(bool)
real = purchases.loc[~purchases["es_sintetico"]].copy()

catalog_rows = []
for description, group in purchases.groupby("descripcion_normalizada", sort=True):
    real_group = real.loc[real["descripcion_normalizada"].eq(description)]
    basis = real_group if not real_group.empty else group
    class_stats = (basis.dropna(subset=["clasificacion_normalizada"])
                   .groupby("clasificacion_normalizada", as_index=False)
                   .agg(monto=("MONTO", "sum"), filas=("MONTO", "size"))
                   .sort_values(["monto", "filas", "clasificacion_normalizada"], ascending=[False, False, True]))
    chosen = None if class_stats.empty else class_stats.iloc[0]["clasificacion_normalizada"]
    conflict = len(class_stats) > 1
    if chosen in (None, "NO DEFINIDO"):
        insumo_id = f"detalle_{slug(description)}"
        rule = "descripcion_individual_sin_clasificacion_valida"
    elif chosen in ("OTROS", "TOTAL"):
        insumo_id = f"categoria_{slug(chosen)}"
        rule = "clasificacion_reservada_con_prefijo"
    else:
        insumo_id = slug(chosen)
        rule = "clasificacion_dominante_por_monto" if conflict else "clasificacion_unica"
    catalog_rows.append({
        "descripcion_normalizada": description,
        "insumo_id": insumo_id,
        "aprobado": True,
        "clasificacion_elegida": chosen,
        "regla_asignacion": rule,
        "clasificaciones_detectadas": " | ".join(class_stats["clasificacion_normalizada"].astype(str)),
        "filas_reales": int(len(real_group)),
        "monto_real": round(float(real_group["MONTO"].sum()), 2),
    })
catalog = pd.DataFrame(catalog_rows)

coverage_rows = []
for week, group in purchases.groupby("semana_inicio", sort=True):
    is_synthetic = group["es_sintetico"].all()
    if group["es_sintetico"].any() and not is_synthetic:
        raise ValueError(f"Semana con mezcla real/sintetica: {week:%Y-%m-%d}")
    if is_synthetic and week >= HOLDOUT_START:
        raise ValueError(f"Semana sintetica dentro del holdout: {week:%Y-%m-%d}")
    coverage_rows.append({
        "semana_inicio": week,
        "estado": "sintetica_entrenamiento" if is_synthetic else "observada",
        "evidencia": ("Mediana causal de 8 semanas; filas marcadas es_sintetico=True"
                      if is_synthetic else "Registros originales conservados en el archivo complementado"),
        "fecha_revision": REVIEW_DATE,
        "registros_detectados": int(len(group)),
        "importe_total": round(float(group["MONTO"].sum()), 2),
    })
coverage = pd.DataFrame(coverage_rows)
expected_weeks = pd.date_range(START, END, freq="W-MON")
if list(coverage["semana_inicio"]) != list(expected_weeks):
    raise ValueError("La cobertura de compras no contiene todas las semanas del periodo.")

sales = pd.read_excel(sales_path, sheet_name="Datos")
sales["semana_inicio"] = pd.to_datetime(sales["semana_inicio"])
sales["es_sintetico"] = sales["es_sintetico"].fillna(False).astype(bool)
weekly_sales_rows = []
for week, group in sales.groupby("semana_inicio", sort=True):
    is_synthetic = group["es_sintetico"].all()
    if group["es_sintetico"].any() and not is_synthetic:
        raise ValueError(f"Ventas con mezcla real/sintetica: {week:%Y-%m-%d}")
    if is_synthetic and week >= HOLDOUT_START:
        raise ValueError(f"Venta sintetica dentro del holdout: {week:%Y-%m-%d}")
    weekly_sales_rows.append({
        "semana_inicio": week,
        "importe_nominal": round(float(pd.to_numeric(group["Importe"], errors="coerce").sum()), 2),
        "available_at": week + pd.Timedelta(weeks=1),
        "es_sintetico": is_synthetic,
        "metodo_sintesis": "mediana causal del total de las 8 semanas previas" if is_synthetic else "",
        "fuente": "Ventas_complementadas_entrenamiento.xlsx",
    })
weekly_sales = pd.DataFrame(weekly_sales_rows)
if list(weekly_sales["semana_inicio"]) != list(expected_weeks):
    raise ValueError("Las ventas semanales no contienen todas las semanas del periodo.")

common_metadata = [
    ["Periodo", f"{START:%Y-%m-%d} a {END:%Y-%m-%d}"],
    ["Inicio de holdout real", f"{HOLDOUT_START:%Y-%m-%d}"],
    ["Regla de evaluación", "No se permiten valores sintéticos desde el inicio del holdout."],
]
catalog_metadata = common_metadata + [
    ["Fuente", str(purchases_path)],
    ["Criterio", "Clasificación válida; conflictos resueltos por mayor importe real; NO DEFINIDO queda separado por descripción."],
    ["Descripciones", len(catalog)],
    ["Insumos resultantes", catalog["insumo_id"].nunique()],
    ["Conflictos resueltos", int(catalog["regla_asignacion"].eq("clasificacion_dominante_por_monto").sum())],
]
coverage_metadata = common_metadata + [
    ["Fuente", str(purchases_path)],
    ["Semanas observadas", int(coverage["estado"].eq("observada").sum())],
    ["Semanas sintéticas de entrenamiento", int(coverage["estado"].eq("sintetica_entrenamiento").sum())],
]
sales_metadata = common_metadata + [
    ["Fuente", str(sales_path)],
    ["Semanas observadas", int((~weekly_sales["es_sintetico"]).sum())],
    ["Semanas sintéticas de entrenamiento", int(weekly_sales["es_sintetico"].sum())],
]

(WORK / "catalogo_pipeline.json").write_text(json.dumps(payload(catalog, catalog_metadata, [], ["filas_reales", "monto_real"]), ensure_ascii=False, allow_nan=False), encoding="utf-8")
(WORK / "cobertura_pipeline.json").write_text(json.dumps(payload(coverage, coverage_metadata, ["semana_inicio", "fecha_revision"], ["registros_detectados", "importe_total"]), ensure_ascii=False, allow_nan=False), encoding="utf-8")
(WORK / "ventas_semanales_pipeline.json").write_text(json.dumps(payload(weekly_sales, sales_metadata, ["semana_inicio", "available_at"], ["importe_nominal"]), ensure_ascii=False, allow_nan=False), encoding="utf-8")

summary = {
    "catalog_rows": len(catalog),
    "catalog_ids": int(catalog["insumo_id"].nunique()),
    "catalog_conflicts": int(catalog["regla_asignacion"].eq("clasificacion_dominante_por_monto").sum()),
    "coverage_weeks": len(coverage),
    "synthetic_purchase_weeks": int(coverage["estado"].eq("sintetica_entrenamiento").sum()),
    "sales_weeks": len(weekly_sales),
    "synthetic_sales_weeks": int(weekly_sales["es_sintetico"].sum()),
}
print(json.dumps(summary, ensure_ascii=False))
