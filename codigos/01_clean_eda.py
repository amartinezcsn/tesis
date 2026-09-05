from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(r"C:/Python/tesis/datasets/xlsx")
OUT_DIR = Path(r"C:/Python/tesis/input")

START_DATE = pd.Timestamp("2022-01-01")
END_DATE = pd.Timestamp("2026-05-31")
INPC_BASE = pd.Timestamp("2026-05-01")
OECD_INPC_FILE = "oecd_mexico_prices_2022_2026.csv"


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def clean_text(value):
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    if not text:
        return pd.NA
    text = " ".join(text.split())
    return text


def clean_upper(value):
    value = clean_text(value)
    if pd.isna(value):
        return pd.NA
    return strip_accents(value).upper()


def clean_lower(value):
    value = clean_text(value)
    if pd.isna(value):
        return pd.NA
    return strip_accents(value).lower()


def normalize_measure(value):
    value = clean_text(value)
    if pd.isna(value):
        return pd.NA
    key = strip_accents(value).lower()
    mapping = {
        "pz": "pz",
        "pza": "pz",
        "pzs": "pz",
        "paq": "paq",
        "paquete": "paq",
        "kg": "kg",
        "kilo": "kg",
        "g": "g",
        "gr": "g",
        "gramo": "g",
        "lts": "lts",
        "lt": "lts",
        "l": "lts",
        "bot": "bot",
        "botella": "bot",
        "cj": "cj",
        "caja": "cj",
        "mt": "mt",
        "metro": "mt",
        "tick": "tick",
        "kit": "kit",
        "nd": "nd",
        "na": "nd",
    }
    return mapping.get(key, key)


def parse_any_date(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True, format="mixed")
    if parsed.isna().all():
        parsed = pd.to_datetime(series, errors="coerce")
    return parsed


def save_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def build_inpc() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa el nivel del índice de la inflación anual reportada cada mes."""
    inflation = pd.read_csv(BASE_DIR / "INPC_2022_2026.csv")
    inflation["fecha"] = pd.to_datetime(inflation["Fecha"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    inflation = inflation.loc[inflation["fecha"].between(START_DATE, END_DATE), ["fecha", "Valor"]]
    inflation = inflation.rename(columns={"Valor": "inflacion_anual_pct"}).drop_duplicates("fecha", keep="last")

    index_raw = pd.read_csv(BASE_DIR / OECD_INPC_FILE)
    index_raw = index_raw.loc[
        index_raw["REF_AREA"].eq("MEX")
        & index_raw["FREQ"].eq("M")
        & index_raw["MEASURE"].eq("CPI")
        & index_raw["UNIT_MEASURE"].eq("IX")
        & index_raw["EXPENDITURE"].eq("_T")
        & index_raw["ADJUSTMENT"].eq("N")
        & index_raw["TRANSFORMATION"].eq("_Z")
    ].copy()
    index_raw["fecha"] = pd.to_datetime(index_raw["TIME_PERIOD"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    index_raw["inpc_indice"] = pd.to_numeric(index_raw["OBS_VALUE"], errors="coerce")
    index_raw = index_raw.loc[index_raw["fecha"].between(START_DATE, END_DATE), ["fecha", "inpc_indice"]]
    index_raw = index_raw.drop_duplicates("fecha", keep="last")

    clean = index_raw.merge(inflation, on="fecha", how="left").sort_values("fecha")
    if clean["fecha"].duplicated().any() or clean["inpc_indice"].isna().any():
        raise ValueError("La serie mensual del nivel del INPC tiene duplicados o valores faltantes.")
    base_value = clean.loc[clean["fecha"].eq(INPC_BASE), "inpc_indice"].iloc[0]
    clean["factor_ajuste_a_2026_05"] = base_value / clean["inpc_indice"]
    clean["fecha"] = clean["fecha"].dt.date
    meta = pd.DataFrame(
        {
            "métrica": [
                "fecha_base", "nivel_base_inpc", "criterio_ajuste", "variable_archivo_original",
                "fuente_nivel_indice", "serie_nivel", "consulta_api",
            ],
            "valor": [
                str(INPC_BASE.date()), float(base_value),
                "importe_real = importe_nominal × INPC_mayo_2026 / INPC_mes",
                "inflación anualizada reportada mensualmente; no se usa como nivel del índice",
                "OCDE, G20 Prices, México", "CPI nacional mensual, unidad IX, sin ajuste",
                "https://sdmx.oecd.org/public/rest/v1/data/OECD.SDD.TPS,DSD_G20_PRICES%40DF_G20_PRICES,1.0/MEX.M......",
            ],
        }
    )
    return clean, meta


def build_temperature() -> pd.DataFrame:
    try:
        raw = pd.read_csv(BASE_DIR / "Temperatura_Tizayuca.csv")
    except Exception:
        raw = pd.read_csv(BASE_DIR / "Temperatura_Tizayuca.csv", encoding="latin1")
    raw["Estado"] = raw["Estado"].astype(str)
    raw = raw.loc[raw["Estado"].str.contains("HIDALGO", case=False, na=False)].copy()
    raw["fecha"] = pd.to_datetime(raw["fecha"], dayfirst=True, errors="coerce")
    raw = raw.loc[(raw["fecha"] >= START_DATE) & (raw["fecha"] <= END_DATE)].copy()
    raw = raw.sort_values("fecha")
    clean = raw.loc[:, ["fecha", "Valor"]].rename(columns={"Valor": "temperatura_promedio_mensual"})
    clean["fecha"] = clean["fecha"].dt.date
    return clean


def build_dataset_tizayuca() -> pd.DataFrame:
    raw = pd.read_excel(BASE_DIR / "Dataset_Tizayuca_2022_2026.xlsx")
    raw["fecha"] = pd.to_datetime(raw["Fecha"], errors="coerce")
    raw = raw.loc[(raw["fecha"] >= START_DATE) & (raw["fecha"] <= END_DATE)].copy()
    clean = raw.loc[:, ["fecha", "EsFestivoMexicano", "EsFechaPago", "TemperaturaMax", "TemperaturaMin", "Clima", "NacimientosIndice"]].copy()
    clean = clean.rename(
        columns={
            "EsFestivoMexicano": "es_festivo_mexicano",
            "EsFechaPago": "es_fecha_pago",
            "TemperaturaMax": "temperatura_max",
            "TemperaturaMin": "temperatura_min",
            "Clima": "clima",
            "NacimientosIndice": "nacimientos_indice",
        }
    )
    clean["clima"] = clean["clima"].map(clean_upper)
    clean["fecha"] = clean["fecha"].dt.date
    return clean.sort_values("fecha").reset_index(drop=True)


def build_compras(inpc: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(BASE_DIR / "Compras.xlsx")
    raw["fecha"] = pd.to_datetime(raw["FECHA"], errors="coerce")
    raw = raw.loc[(raw["fecha"] >= START_DATE) & (raw["fecha"] <= END_DATE)].copy()
    raw = raw.drop_duplicates().copy()

    raw["proveedor"] = raw["PROVEEDOR"].map(clean_upper)
    raw["numero"] = raw["NUMERO"].map(clean_text)
    raw["cantidad"] = pd.to_numeric(raw["CANT"], errors="coerce")
    raw["unidad"] = raw["U#MEDIDA"].map(normalize_measure)
    raw["descripcion"] = raw["DESCRIPCION"].map(clean_text)
    raw["monto_nominal"] = pd.to_numeric(raw["MONTO"], errors="coerce")
    raw["precio_unitario_nominal"] = pd.to_numeric(raw["P#UNITARIO"], errors="coerce")
    raw["clasificacion"] = raw["CLASIFICACION"].map(clean_upper)
    raw["subclasificacion"] = raw["SUBCLASIFICACION"].map(clean_upper)
    raw["fecha_mes"] = raw["fecha"].dt.to_period("M").dt.to_timestamp().dt.date

    clean_detail = raw.merge(inpc, left_on="fecha_mes", right_on="fecha", how="left", suffixes=("", "_inpc"))
    clean_detail = clean_detail.rename(columns={"inpc_indice": "inpc_indice_mensual"})
    clean_detail["factor_ajuste_a_2026_05"] = clean_detail["factor_ajuste_a_2026_05"].fillna(1.0)
    clean_detail["monto_real_2026_05"] = clean_detail["monto_nominal"] * clean_detail["factor_ajuste_a_2026_05"]
    clean_detail["precio_unitario_real_2026_05"] = clean_detail["precio_unitario_nominal"] * clean_detail["factor_ajuste_a_2026_05"]

    clean_detail = clean_detail.loc[
        :,
        [
            "fecha",
            "proveedor",
            "numero",
            "cantidad",
            "unidad",
            "descripcion",
            "monto_nominal",
            "monto_real_2026_05",
            "precio_unitario_nominal",
            "precio_unitario_real_2026_05",
            "clasificacion",
            "subclasificacion",
            "factor_ajuste_a_2026_05",
        ],
    ].copy()

    clean_detail = clean_detail.dropna(subset=["fecha", "monto_nominal", "clasificacion"]).copy()
    clean_detail["fecha"] = clean_detail["fecha"].dt.date
    clean_detail = clean_detail.sort_values(["fecha", "clasificacion", "proveedor"]).reset_index(drop=True)

    full_dates = pd.DataFrame({"fecha": pd.date_range(START_DATE, END_DATE, freq="D").date})
    pivot = (
        clean_detail.pivot_table(
            index="fecha",
            columns="clasificacion",
            values="monto_real_2026_05",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    pivot.columns = ["fecha"] + [f"compras_{c.lower().replace(' ', '_')}_real_2026_05" for c in pivot.columns[1:]]
    totals = (
        clean_detail.groupby("fecha", as_index=False)
        .agg(
            compras_registros=("monto_real_2026_05", "size"),
            compras_total_real_2026_05=("monto_real_2026_05", "sum"),
            compras_total_nominal=("monto_nominal", "sum"),
            compras_cantidad_total=("cantidad", "sum"),
        )
    )
    totals["fecha"] = pd.to_datetime(totals["fecha"]).dt.date
    pivot["fecha"] = pd.to_datetime(pivot["fecha"]).dt.date
    daily = full_dates.merge(totals, on="fecha", how="left").merge(pivot, on="fecha", how="left")
    fill_cols = [c for c in daily.columns if c != "fecha"]
    daily[fill_cols] = daily[fill_cols].fillna(0)
    daily = daily.sort_values("fecha").reset_index(drop=True)
    return clean_detail, daily


def build_ventas(inpc: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(BASE_DIR / "Ventas.xlsx")
    fecha_from_fecha = parse_any_date(raw["Fecha"])
    fecha_from_hora = parse_any_date(raw["Fecha/Hora"])
    raw["fecha"] = fecha_from_fecha.fillna(fecha_from_hora)
    raw = raw.loc[(raw["fecha"] >= START_DATE) & (raw["fecha"] <= END_DATE)].copy()

    # Keep rows with monetary value and a valid date; many rows have blank status but still represent orders.
    raw = raw.loc[raw["Importe"].notna()].copy()

    raw["pedido_id"] = raw["Number"].fillna(raw["NumPedido"]).astype(str).replace("nan", pd.NA)
    raw["status_normalizado"] = raw["Status"].map(clean_lower)
    raw.loc[raw["status_normalizado"].isna(), "status_normalizado"] = "sin_estado"
    raw["nombre"] = raw["Nombre"].map(clean_upper)
    raw["vendedor"] = raw["Vendedor"].map(clean_upper)
    raw["observacion"] = raw["Observación"].map(clean_text)
    raw["descripcion_items"] = raw["Descri. Items"].map(clean_text)
    raw["cantidad"] = pd.to_numeric(raw["Cantidad"], errors="coerce")
    raw["total_items"] = pd.to_numeric(raw["Total de ítems"], errors="coerce")
    raw["subtotal_nominal"] = pd.to_numeric(raw["Subtotal"], errors="coerce")
    raw["descuento_nominal"] = pd.to_numeric(raw["Descuento"], errors="coerce")
    raw["tasa"] = pd.to_numeric(raw["Tasa"], errors="coerce")
    raw["envio_nominal"] = pd.to_numeric(raw["Envío"], errors="coerce")
    raw["importe_nominal"] = pd.to_numeric(raw["Importe"], errors="coerce")
    raw["ganancia_nominal"] = pd.to_numeric(raw["Ganancia"], errors="coerce")
    raw["pastel"] = pd.to_numeric(raw["Pastel"], errors="coerce")
    raw["galletas"] = pd.to_numeric(raw["Galletas"], errors="coerce")
    raw["otros"] = pd.to_numeric(raw["Otros"], errors="coerce")
    raw["cupcakes"] = pd.to_numeric(raw["Cupcakes"], errors="coerce")
    raw["detalle_producto_disponible"] = (
        raw["descripcion_items"].notna()
        | raw[["pastel", "galletas", "otros", "cupcakes"]].notna().any(axis=1)
    ).astype(int)
    raw["fecha_mes"] = raw["fecha"].dt.to_period("M").dt.to_timestamp().dt.date

    clean_detail = raw.merge(inpc, left_on="fecha_mes", right_on="fecha", how="left", suffixes=("", "_inpc"))
    clean_detail = clean_detail.rename(columns={"inpc_indice": "inpc_indice_mensual"})
    clean_detail["factor_ajuste_a_2026_05"] = clean_detail["factor_ajuste_a_2026_05"].fillna(1.0)
    clean_detail["importe_real_2026_05"] = clean_detail["importe_nominal"] * clean_detail["factor_ajuste_a_2026_05"]
    clean_detail["subtotal_real_2026_05"] = clean_detail["subtotal_nominal"] * clean_detail["factor_ajuste_a_2026_05"]
    clean_detail["ganancia_real_2026_05"] = clean_detail["ganancia_nominal"] * clean_detail["factor_ajuste_a_2026_05"]
    clean_detail["envio_real_2026_05"] = clean_detail["envio_nominal"] * clean_detail["factor_ajuste_a_2026_05"]
    clean_detail["descuento_real_2026_05"] = clean_detail["descuento_nominal"] * clean_detail["factor_ajuste_a_2026_05"]

    clean_detail = clean_detail.loc[
        :,
        [
            "fecha",
            "pedido_id",
            "status_normalizado",
            "cantidad",
            "total_items",
            "descripcion_items",
            "subtotal_nominal",
            "subtotal_real_2026_05",
            "descuento_nominal",
            "descuento_real_2026_05",
            "tasa",
            "envio_nominal",
            "envio_real_2026_05",
            "importe_nominal",
            "importe_real_2026_05",
            "ganancia_nominal",
            "ganancia_real_2026_05",
            "nombre",
            "vendedor",
            "observacion",
            "pastel",
            "galletas",
            "otros",
            "cupcakes",
            "detalle_producto_disponible",
            "factor_ajuste_a_2026_05",
        ],
    ].copy()

    clean_detail = clean_detail.dropna(subset=["fecha", "importe_nominal"]).copy()
    clean_detail["fecha"] = clean_detail["fecha"].dt.date
    clean_detail = clean_detail.sort_values(["fecha", "importe_nominal"], ascending=[True, False]).reset_index(drop=True)

    full_dates = pd.DataFrame({"fecha": pd.date_range(START_DATE, END_DATE, freq="D").date})
    daily = (
        clean_detail.groupby("fecha", as_index=False)
        .agg(
            ventas_registros=("importe_nominal", "size"),
            ventas_pedidos_unicos=("pedido_id", pd.Series.nunique),
            ventas_importe_nominal=("importe_nominal", "sum"),
            ventas_importe_real_2026_05=("importe_real_2026_05", "sum"),
            ventas_subtotal_nominal=("subtotal_nominal", "sum"),
            ventas_subtotal_real_2026_05=("subtotal_real_2026_05", "sum"),
            ventas_ganancia_nominal=("ganancia_nominal", "sum"),
            ventas_ganancia_real_2026_05=("ganancia_real_2026_05", "sum"),
            ventas_envio_nominal=("envio_nominal", "sum"),
            ventas_envio_real_2026_05=("envio_real_2026_05", "sum"),
            ventas_descuento_nominal=("descuento_nominal", "sum"),
            ventas_descuento_real_2026_05=("descuento_real_2026_05", "sum"),
            ventas_cantidad_total=("cantidad", "sum"),
            ventas_total_items=("total_items", "sum"),
            ventas_pastel=("pastel", "sum"),
            ventas_galletas=("galletas", "sum"),
            ventas_otros=("otros", "sum"),
            ventas_cupcakes=("cupcakes", "sum"),
            ventas_detalle_registros=("detalle_producto_disponible", "sum"),
            ventas_clientes_unicos=("nombre", pd.Series.nunique),
            ventas_vendedor_unico=("vendedor", pd.Series.nunique),
        )
    )
    daily["fecha"] = pd.to_datetime(daily["fecha"]).dt.date
    daily = full_dates.merge(daily, on="fecha", how="left")
    fill_cols = [c for c in daily.columns if c != "fecha"]
    daily[fill_cols] = daily[fill_cols].fillna(0)
    product_cols = ["ventas_pastel", "ventas_galletas", "ventas_otros", "ventas_cupcakes"]
    daily.loc[daily["ventas_detalle_registros"].eq(0), product_cols] = np.nan
    daily = daily.sort_values("fecha").reset_index(drop=True)
    return clean_detail, daily


def build_master(
    inpc: pd.DataFrame,
    temp: pd.DataFrame,
    compras_daily: pd.DataFrame,
    ventas_daily: pd.DataFrame,
) -> pd.DataFrame:
    full_dates = pd.DataFrame({"fecha": pd.date_range(START_DATE, END_DATE, freq="D").date})

    # Temporal features derived from the patterns already present in Dataset_Tizayuca.
    holiday_month_days = {
        (1, 6),
        (2, 14),
        (4, 30),
        (5, 10),
        (11, 1),
        (11, 2),
        (12, 24),
        (12, 25),
        (12, 31),
    }
    master = full_dates.copy()
    master["fecha_dt"] = pd.to_datetime(master["fecha"])
    master["es_festivo_mexicano"] = master["fecha_dt"].apply(
        lambda d: 1 if (d.month, d.day) in holiday_month_days else 0
    )
    master["es_fecha_pago"] = master["fecha_dt"].apply(
        lambda d: 1 if (d.day == 15 or d.day == d.days_in_month) else 0
    )
    nacimientos_map = {2022: 100.0, 2023: 96.3, 2024: 88.4, 2025: 84.0, 2026: 82.0}
    master["nacimientos_indice"] = master["fecha_dt"].dt.year.map(nacimientos_map)

    # Monthly temperature and INPC are repeated for every day in the month.
    temp_daily = temp.copy()
    temp_daily["fecha"] = pd.to_datetime(temp_daily["fecha"]).dt.date
    master["fecha_mes"] = pd.to_datetime(master["fecha"]).dt.to_period("M").dt.to_timestamp().dt.date
    temp_daily["fecha_mes"] = pd.to_datetime(temp_daily["fecha"]).dt.to_period("M").dt.to_timestamp().dt.date
    inpc_daily = inpc.copy()
    inpc_daily["fecha"] = pd.to_datetime(inpc_daily["fecha"]).dt.date

    master = master.merge(
        temp_daily.rename(columns={"temperatura_promedio_mensual": "temperatura_promedio_mensual_hidalgo"})[
            ["fecha_mes", "temperatura_promedio_mensual_hidalgo"]
        ],
        on="fecha_mes",
        how="left",
    )
    master = master.merge(
        inpc_daily[["fecha", "inpc_indice", "inflacion_anual_pct"]]
        .assign(fecha_mes=lambda d: pd.to_datetime(d["fecha"]).dt.to_period("M").dt.to_timestamp().dt.date)
        [["fecha_mes", "inpc_indice", "inflacion_anual_pct"]],
        on="fecha_mes",
        how="left",
    )
    master = master.merge(
        ventas_daily[
            [
                "fecha",
                "ventas_registros",
                "ventas_pedidos_unicos",
                "ventas_importe_real_2026_05",
                "ventas_ganancia_real_2026_05",
                "ventas_envio_real_2026_05",
                "ventas_descuento_real_2026_05",
                "ventas_cantidad_total",
                "ventas_total_items",
                "ventas_pastel",
                "ventas_galletas",
                "ventas_otros",
                "ventas_cupcakes",
                "ventas_detalle_registros",
                "ventas_clientes_unicos",
                "ventas_vendedor_unico",
            ]
        ],
        on="fecha",
        how="left",
    )
    compras_keep = [
        "fecha",
        "compras_registros",
        "compras_total_real_2026_05",
        "compras_cantidad_total",
    ] + [c for c in compras_daily.columns if c.startswith("compras_") and c.endswith("_real_2026_05") and c not in {"compras_total_real_2026_05"}]
    master = master.merge(compras_daily[compras_keep], on="fecha", how="left")

    # Keep a categorical weather signal, but encode it so the final master remains numeric.
    clima_source = build_dataset_tizayuca()[["fecha", "clima"]].copy()
    clima_source["fecha"] = pd.to_datetime(clima_source["fecha"]).dt.date
    clima_cols = full_dates.merge(clima_source, on="fecha", how="left")
    clima_cols["clima"] = clima_cols["clima"].fillna("SIN_DATO")
    clima_dummies = pd.get_dummies(clima_cols["clima"], prefix="clima", dtype=int)
    master = pd.concat([master.reset_index(drop=True), clima_dummies.reset_index(drop=True)], axis=1)

    product_cols = {"ventas_pastel", "ventas_galletas", "ventas_otros", "ventas_cupcakes"}
    fill_zero_cols = [
        c for c in master.columns
        if c != "fecha" and c not in {"fecha_dt", "fecha_mes"} and c not in product_cols
    ]
    master[fill_zero_cols] = master[fill_zero_cols].fillna(0)

    master = master.drop(columns=["fecha_dt", "fecha_mes"])
    master = master.sort_values("fecha").reset_index(drop=True)
    return master


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    inpc_clean, inpc_meta = build_inpc()
    temp_clean = build_temperature()
    dataset_clean = build_dataset_tizayuca()
    compras_detail, compras_daily = build_compras(inpc_clean)
    ventas_detail, ventas_daily = build_ventas(inpc_clean)
    master_daily = build_master(inpc_clean, temp_clean, compras_daily, ventas_daily)

    save_excel(OUT_DIR / "inpc_limpio.xlsx", {"limpio": inpc_clean, "meta": inpc_meta})
    save_excel(OUT_DIR / "temperatura_hidalgo_limpia.xlsx", {"limpio": temp_clean})
    save_excel(OUT_DIR / "dataset_tizayuca_limpio.xlsx", {"limpio": dataset_clean})
    save_excel(OUT_DIR / "compras_limpias.xlsx", {"detalle": compras_detail, "pivot_diario": compras_daily})
    save_excel(OUT_DIR / "ventas_limpias.xlsx", {"detalle": ventas_detail, "diario_completo": ventas_daily})
    save_excel(OUT_DIR / "dataset_maestro_diario.xlsx", {"maestro": master_daily})

    summary = []
    summary.append("# Resumen de limpieza y EDA")
    summary.append("")
    summary.append("## Dataset_Tizayuca")
    summary.append(f"- Filas: {len(dataset_clean)}")
    summary.append(f"- Rango: {dataset_clean['fecha'].min()} a {dataset_clean['fecha'].max()}")
    summary.append("")
    summary.append("## INPC")
    summary.append(f"- Filas: {len(inpc_clean)}")
    summary.append(f"- Base de ajuste correcta con nivel del índice: {INPC_BASE.date()}")
    summary.append("- INPC_2022_2026.csv se interpreta como inflación anualizada mensual y no como nivel del índice")
    summary.append("")
    summary.append("## Temperatura Hidalgo")
    summary.append(f"- Filas: {len(temp_clean)}")
    summary.append(f"- Rango: {temp_clean['fecha'].min()} a {temp_clean['fecha'].max()}")
    summary.append("")
    summary.append("## Compras")
    summary.append(f"- Detalle limpio: {len(compras_detail)} filas")
    summary.append(f"- Pivot diario: {len(compras_daily)} días")
    summary.append(f"- Clasificaciones: {compras_daily.columns[1:].tolist()}")
    summary.append("")
    summary.append("## Ventas")
    summary.append(f"- Detalle limpio: {len(ventas_detail)} filas")
    summary.append(f"- Diario: {len(ventas_daily)} días")
    summary.append(f"- Rango: {ventas_detail['fecha'].min()} a {ventas_detail['fecha'].max()}")
    summary.append("")
    summary.append("## Maestro")
    summary.append(f"- Filas: {len(master_daily)}")
    summary.append(f"- Columnas: {len(master_daily.columns)}")
    summary.append(f"- Rango: {master_daily['fecha'].min()} a {master_daily['fecha'].max()}")

    (OUT_DIR / "eda_resumen.md").write_text("\n".join(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
