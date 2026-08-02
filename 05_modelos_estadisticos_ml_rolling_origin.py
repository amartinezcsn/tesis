from __future__ import annotations

"""
Codigo 05: comparacion inicial de modelos con validacion Rolling-Origin.

Objetivo:
- Comparar metodo empirico contra modelos estadisticos y de aprendizaje automatico.
- Mantener particiones temporales, coherentes con series de tiempo.
- Reportar MAE, RMSE y MAPE para ventas, compras e indicadores operativos.

Modelos incluidos:
- Metodo empirico: ultimo valor observado y promedio movil de 7 dias.
- Regresion lineal, arbol de decision y random forest si scikit-learn esta instalado.
- ARIMA/SARIMA si statsmodels esta instalado.

Este script puede ejecutarse con el dataset completo, reducido o PCA cambiando DATASET_TO_USE.
"""

from pathlib import Path
import math

import numpy as np
import pandas as pd

from config_metodologia import DATE_COLUMN, TARGET_COLUMNS, ensure_output_dir, load_model_dataset


# Opciones:
# "completo": usa C:/Python/tesis/output/dataset_modelado_diario.xlsx
# "reducido": usa 03_dataset_reducido_por_seleccion.xlsx
# "pca": usa 04_dataset_pca_componentes.xlsx
DATASET_TO_USE = "completo"
ROLLING_INITIAL_DAYS = 730
ROLLING_STEP_DAYS = 30
FORECAST_HORIZON_DAYS = 30


def load_dataset_variant() -> pd.DataFrame:
    out_dir = ensure_output_dir()
    if DATASET_TO_USE == "reducido":
        path = out_dir / "03_dataset_reducido_por_seleccion.xlsx"
        df = pd.read_excel(path, sheet_name="dataset_reducido")
    elif DATASET_TO_USE == "pca":
        path = out_dir / "04_dataset_pca_componentes.xlsx"
        df = pd.read_excel(path, sheet_name="dataset_pca")
    else:
        df = load_model_dataset()
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    return df.sort_values(DATE_COLUMN).reset_index(drop=True)


def metricas(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    error = y_true - y_pred
    mae = float(np.mean(np.abs(error)))
    rmse = float(math.sqrt(np.mean(error**2)))
    denominator = np.where(np.abs(y_true) < 1e-8, np.nan, np.abs(y_true))
    mape = float(np.nanmean(np.abs(error) / denominator) * 100)
    return {"mae": mae, "rmse": rmse, "mape": mape}


def empirical_forecasts(train: pd.DataFrame, test: pd.DataFrame, target: str) -> dict[str, np.ndarray]:
    last_value = float(train[target].iloc[-1])
    rolling_7 = float(train[target].tail(7).mean())
    return {
        "empirico_ultimo_valor": np.repeat(last_value, len(test)),
        "empirico_promedio_7d": np.repeat(rolling_7, len(test)),
    }


def sklearn_forecasts(train: pd.DataFrame, test: pd.DataFrame, predictors: list[str], target: str) -> dict[str, np.ndarray]:
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import LinearRegression
        from sklearn.tree import DecisionTreeRegressor
    except ImportError:
        return {}

    x_train = train[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
    x_test = test[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
    y_train = train[target].fillna(0)

    models = {
        "regresion_lineal_multivariable": LinearRegression(),
        "arbol_decision": DecisionTreeRegressor(random_state=42, min_samples_leaf=5),
        "random_forest": RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=5, n_jobs=-1),
    }

    predictions = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions[name] = np.maximum(model.predict(x_test), 0)
    return predictions


def statsmodels_forecasts(train: pd.DataFrame, test: pd.DataFrame, target: str) -> dict[str, np.ndarray]:
    try:
        from statsmodels.tsa.arima.model import ARIMA
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except ImportError:
        return {}

    y_train = train[target].astype(float)
    predictions = {}

    arima = ARIMA(y_train, order=(1, 1, 1)).fit()
    predictions["arima_111"] = np.maximum(arima.forecast(steps=len(test)).to_numpy(), 0)

    sarima = SARIMAX(
        y_train,
        order=(1, 1, 1),
        seasonal_order=(1, 0, 1, 7),
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False)
    predictions["sarima_semanal"] = np.maximum(sarima.forecast(steps=len(test)).to_numpy(), 0)

    return predictions


def rolling_origin_evaluation(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    predictors = [column for column in df.columns if column not in TARGET_COLUMNS + [DATE_COLUMN]]

    for target in TARGET_COLUMNS:
        start = ROLLING_INITIAL_DAYS
        while start + FORECAST_HORIZON_DAYS <= len(df):
            train = df.iloc[:start].copy()
            test = df.iloc[start : start + FORECAST_HORIZON_DAYS].copy()
            y_true = test[target].to_numpy(dtype=float)

            all_predictions = {}
            all_predictions.update(empirical_forecasts(train, test, target))
            all_predictions.update(statsmodels_forecasts(train, test, target))
            all_predictions.update(sklearn_forecasts(train, test, predictors, target))

            for model_name, y_pred in all_predictions.items():
                scores = metricas(y_true, y_pred)
                rows.append(
                    {
                        "dataset": DATASET_TO_USE,
                        "target": target,
                        "modelo": model_name,
                        "fecha_inicio_prueba": test[DATE_COLUMN].min().date(),
                        "fecha_fin_prueba": test[DATE_COLUMN].max().date(),
                        **scores,
                    }
                )

            start += ROLLING_STEP_DAYS

    return pd.DataFrame(rows)


def main() -> None:
    out_dir = ensure_output_dir()
    df = load_dataset_variant()
    results = rolling_origin_evaluation(df)

    ranking = (
        results.groupby(["dataset", "target", "modelo"], as_index=False)
        .agg(mae_promedio=("mae", "mean"), rmse_promedio=("rmse", "mean"), mape_promedio=("mape", "mean"))
        .sort_values(["target", "rmse_promedio"])
    )

    output_xlsx = out_dir / f"05_modelos_rolling_origin_{DATASET_TO_USE}.xlsx"
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        results.to_excel(writer, sheet_name="resultados_por_origen", index=False)
        ranking.to_excel(writer, sheet_name="ranking_modelos", index=False)

    print(f"Archivo generado: {output_xlsx}")


if __name__ == "__main__":
    main()
