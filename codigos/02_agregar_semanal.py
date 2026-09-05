"""Agrega los registros diarios a una unidad semanal reproducible.

Entradas
--------
``input/dataset_maestro_diario.xlsx`` (hoja ``maestro``).

Salida
------
``input/dataset_maestro_semanal.xlsx`` con una fila por semana de lunes a
domingo. Las semanas parciales inicial y final se excluyen para no comparar
periodos de distinta duración.
"""

import pandas as pd

from config_semanal import (
    DAILY_MASTER_PATH,
    DATE_COLUMN,
    PURCHASE_COLUMN,
    SALES_COLUMNS,
    TEMPERATURE_COLUMN,
    WEEKLY_MASTER_PATH,
    WEEK_FREQUENCY,
)


def _week_start(dates: pd.Series) -> pd.Series:
    """Devuelve el lunes asociado a cada fecha."""
    return dates.dt.to_period(WEEK_FREQUENCY).dt.start_time


def aggregate_daily_to_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    """Construye importes, eventos y covariables agregados por semana.

    Los importes y conteos se suman. El INPC se conserva como último valor de
    la semana, la temperatura se promedia y los eventos se cuentan. La
    disponibilidad ex ante se controla en la siguiente fase; aquí sólo se
    preserva la fuente observada.
    """
    required = {"fecha", PURCHASE_COLUMN, *SALES_COLUMNS}
    missing = sorted(required.difference(daily.columns))
    if missing:
        raise ValueError(f"Faltan columnas obligatorias del maestro diario: {', '.join(missing)}")

    frame = daily.copy()
    frame["fecha"] = pd.to_datetime(frame["fecha"])
    if frame["fecha"].isna().any():
        raise ValueError("El maestro diario contiene fechas inválidas o nulas.")
    if frame["fecha"].duplicated().any():
        raise ValueError("El maestro diario contiene fechas duplicadas; no se puede agregar de forma segura.")
    frame = frame.sort_values("fecha").reset_index(drop=True)
    frame[DATE_COLUMN] = _week_start(frame["fecha"])

    sums = [*SALES_COLUMNS, PURCHASE_COLUMN]
    aggregations: dict[str, str] = {column: "sum" for column in sums if column in frame}
    aggregations.update(
        {
            "es_festivo_mexicano": "sum",
            "es_fecha_pago": "sum",
            "nacimientos_indice": "mean",
            "inpc_valor_mensual": "last",
            TEMPERATURE_COLUMN: "mean",
            "fecha": "count",
        }
    )
    available = {key: value for key, value in aggregations.items() if key in frame.columns}
    weekly = frame.groupby(DATE_COLUMN, as_index=False).agg(available)
    weekly = weekly.rename(columns={"fecha": "dias_observados"})

    # Sólo se conservan semanas completas. Con ello, las sumas de importes y
    # eventos mantienen una base temporal comparable.
    weekly = weekly.loc[weekly["dias_observados"].eq(7)].copy()
    if weekly.empty:
        raise ValueError("No se encontraron semanas calendario completas en el maestro diario.")
    weekly = weekly.rename(
        columns={
            PURCHASE_COLUMN: "compras_importe_semanal",
            "es_festivo_mexicano": "eventos_festivos_semana",
            "es_fecha_pago": "eventos_pago_semana",
            "nacimientos_indice": "nacimientos_indice_semanal",
            "inpc_valor_mensual": "inpc_observado_semana",
            TEMPERATURE_COLUMN: "temperatura_observada_semana",
        }
    )
    weekly["mes"] = weekly[DATE_COLUMN].dt.month.astype(int)
    weekly["trimestre"] = weekly[DATE_COLUMN].dt.quarter.astype(int)
    weekly["semana_anio"] = weekly[DATE_COLUMN].dt.isocalendar().week.astype(int)
    weekly["es_san_valentin"] = weekly[DATE_COLUMN].apply(
        lambda date: int(pd.Timestamp(date.year, 2, 14).to_period(WEEK_FREQUENCY).start_time == date)
    )
    weekly["es_dia_nino"] = weekly[DATE_COLUMN].apply(
        lambda date: int(pd.Timestamp(date.year, 4, 30).to_period(WEEK_FREQUENCY).start_time == date)
    )
    weekly["es_dia_madre"] = weekly[DATE_COLUMN].apply(
        lambda date: int(pd.Timestamp(date.year, 5, 10).to_period(WEEK_FREQUENCY).start_time == date)
    )
    return weekly.sort_values(DATE_COLUMN).reset_index(drop=True)


def main() -> None:
    """Ejecuta la agregación y documenta sus reglas en el libro de salida."""
    daily = pd.read_excel(DAILY_MASTER_PATH, sheet_name="maestro")
    weekly = aggregate_daily_to_weekly(daily)
    metadata = pd.DataFrame(
        {
            "campo": ["unidad_analisis", "semana", "semanas", "fecha_inicio", "fecha_fin"],
            "valor": [
                "semana calendario completa",
                "lunes a domingo",
                len(weekly),
                str(weekly[DATE_COLUMN].min().date()),
                str(weekly[DATE_COLUMN].max().date()),
            ],
        }
    )
    WEEKLY_MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(WEEKLY_MASTER_PATH, engine="openpyxl") as writer:
        weekly.to_excel(writer, sheet_name="semanal", index=False)
        metadata.to_excel(writer, sheet_name="metadatos", index=False)
    print(f"Archivo generado: {WEEKLY_MASTER_PATH}")


if __name__ == "__main__":
    main()
