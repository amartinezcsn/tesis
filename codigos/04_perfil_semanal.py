"""Genera controles de calidad para el dataset semanal de modelado."""

import pandas as pd

from config_semanal import DATE_COLUMN, TARGET_COLUMN, WEEKLY_MODEL_PATH, ensure_output_dir


def main() -> None:
    """Reporta cobertura, ceros y composición de predictores semanales."""
    model = pd.read_excel(WEEKLY_MODEL_PATH, sheet_name="modelo_semanal")
    model[DATE_COLUMN] = pd.to_datetime(model[DATE_COLUMN])
    predictors = [column for column in model if column not in {DATE_COLUMN, TARGET_COLUMN}]
    variable_profile = pd.DataFrame(
        {
            "variable": predictors,
            "grupo": ["histórica" if c.startswith("hist_") else "exógena" for c in predictors],
            "nulos": [int(model[c].isna().sum()) for c in predictors],
            "ceros_pct": [float((model[c].fillna(0) == 0).mean()) for c in predictors],
            "valores_unicos": [int(model[c].nunique(dropna=True)) for c in predictors],
        }
    )
    general = pd.DataFrame(
        {
            "metrica": ["semanas", "inicio", "fin", "predictores", "ceros_objetivo_pct"],
            "valor": [
                len(model),
                str(model[DATE_COLUMN].min().date()),
                str(model[DATE_COLUMN].max().date()),
                len(predictors),
                float((model[TARGET_COLUMN].fillna(0) == 0).mean()),
            ],
        }
    )
    output = ensure_output_dir() / "01_perfil_semanal.xlsx"
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        general.to_excel(writer, sheet_name="resumen", index=False)
        variable_profile.to_excel(writer, sheet_name="variables", index=False)
        model[[DATE_COLUMN, TARGET_COLUMN]].to_excel(writer, sheet_name="objetivo", index=False)
    print(f"Archivo generado: {output}")


if __name__ == "__main__":
    main()
