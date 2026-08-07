from __future__ import annotations

"""
Comparacion y ajuste de modelos con validacion Rolling-Origin.

El ajuste de hiperparametros se realiza exclusivamente con origenes anteriores
a los reservados para la evaluacion final. De esta forma, el ranking final no
se utiliza para escoger los parametros que luego se reportan en ese ranking.
"""

from itertools import product
from typing import Any, Iterable, Mapping, Sequence
import json
import math
import warnings

import numpy as np
import pandas as pd

from config_metodologia import DATE_COLUMN, TARGET_COLUMNS, ensure_output_dir, load_model_dataset


DATASET_TO_USE = "pca"
ROLLING_INITIAL_DAYS = 730
ROLLING_STEP_DAYS = 30
FORECAST_HORIZON_DAYS = 30

# El pipeline maestro puede sobrescribir estos valores.
ENABLE_HYPERPARAMETER_TUNING = True
TUNING_MAX_ORIGINS = 4
FINAL_EVALUATION_ORIGINS = 3
RANDOM_STATE = 42

MODEL_NAMES = (
    "regresion_lineal_multivariable",
    "arbol_decision",
    "random_forest",
    "arima_111",
    "sarima_semanal",
)

# Listas explicitas para mantener una busqueda razonable en un dataset pequeno.
# La funcion publica acepta rejillas distintas mediante ``param_grids``.
DEFAULT_PARAM_GRIDS: dict[str, list[dict[str, Any]]] = {
    "regresion_lineal_multivariable": [
        {"fit_intercept": True},
        {"fit_intercept": False},
    ],
    "arbol_decision": [
        {"max_depth": depth, "min_samples_leaf": leaf}
        for depth, leaf in product((5, 10, None), (2, 5))
    ],
    "random_forest": [
        {
            "n_estimators": trees,
            "max_depth": depth,
            "min_samples_leaf": leaf,
            "max_features": feature_fraction,
        }
        for trees, depth, leaf, feature_fraction in (
            (150, 8, 2, "sqrt"),
            (150, None, 5, "sqrt"),
            (300, 8, 5, 0.7),
            (300, None, 2, 0.7),
        )
    ],
    "arima_111": [
        {"order": order}
        for order in ((1, 0, 1), (1, 1, 1), (2, 1, 1), (1, 1, 2))
    ],
    "sarima_semanal": [
        {"order": (1, 1, 1), "seasonal_order": seasonal}
        for seasonal in ((0, 1, 1, 7), (1, 0, 1, 7), (1, 1, 0, 7))
    ],
}

DEFAULT_MODEL_PARAMS: dict[str, dict[str, Any]] = {
    "regresion_lineal_multivariable": {"fit_intercept": True},
    "arbol_decision": {"min_samples_leaf": 5},
    "random_forest": {
        "n_estimators": 300,
        "min_samples_leaf": 5,
    },
    "arima_111": {"order": (1, 1, 1)},
    "sarima_semanal": {"order": (1, 1, 1), "seasonal_order": (1, 0, 1, 7)},
}


def load_dataset_variant() -> pd.DataFrame:
    out_dir = ensure_output_dir()
    if DATASET_TO_USE == "reducido":
        df = pd.read_excel(out_dir / "03_dataset_reducido_por_seleccion.xlsx", sheet_name="dataset_reducido")
    elif DATASET_TO_USE == "pca":
        df = pd.read_excel(out_dir / "04_dataset_pca_componentes.xlsx", sheet_name="dataset_pca")
    else:
        df = load_model_dataset()
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
    return df.sort_values(DATE_COLUMN).reset_index(drop=True)


def metricas(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float).ravel()
    y_pred = np.asarray(y_pred, dtype=float).ravel()
    error = y_true - y_pred
    mae = float(np.mean(np.abs(error)))
    rmse = float(math.sqrt(np.mean(error**2)))
    valid = np.abs(y_true) >= 1e-8
    mape = float(np.mean(np.abs(error[valid]) / np.abs(y_true[valid])) * 100) if valid.any() else math.nan
    return {"mae": mae, "rmse": rmse, "mape": mape}


def _expand_grid(grid: Mapping[str, Sequence[Any]] | Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Convierte una rejilla cartesiana o una lista explicita en candidatos."""
    if not isinstance(grid, Mapping):
        return [dict(candidate) for candidate in grid]
    keys = list(grid)
    return [dict(zip(keys, values)) for values in product(*(grid[key] for key in keys))]


def _json_params(params: Mapping[str, Any]) -> str:
    return json.dumps(dict(params), ensure_ascii=False, sort_keys=True)


def _clean_xy(
    train: pd.DataFrame,
    test: pd.DataFrame,
    predictors: list[str],
    target: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    x_train = train[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
    x_test = test[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
    y_train = train[target].fillna(0).astype(float)
    return x_train, x_test, y_train


def _forecast_model(
    model_name: str,
    params: Mapping[str, Any],
    train: pd.DataFrame,
    test: pd.DataFrame,
    predictors: list[str],
    target: str,
) -> np.ndarray:
    """Entrena un candidato y devuelve un pronostico no negativo."""
    if model_name in MODEL_NAMES[:3]:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import LinearRegression
        from sklearn.tree import DecisionTreeRegressor

        x_train, x_test, y_train = _clean_xy(train, test, predictors, target)
        if model_name == "regresion_lineal_multivariable":
            model = LinearRegression(**params)
        elif model_name == "arbol_decision":
            model = DecisionTreeRegressor(random_state=RANDOM_STATE, **params)
        else:
            model = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1, **params)
        model.fit(x_train, y_train)
        prediction = model.predict(x_test)
    else:
        from statsmodels.tsa.arima.model import ARIMA
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        y_train = train[target].fillna(0).astype(float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if model_name == "arima_111":
                fitted = ARIMA(y_train, order=tuple(params["order"])).fit()
            elif model_name == "sarima_semanal":
                fitted = SARIMAX(
                    y_train,
                    order=tuple(params["order"]),
                    seasonal_order=tuple(params["seasonal_order"]),
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                ).fit(disp=False)
            else:
                raise ValueError(f"Modelo no soportado: {model_name}")
        prediction = fitted.forecast(steps=len(test)).to_numpy()
    return np.maximum(np.asarray(prediction, dtype=float).ravel(), 0)


def rolling_origins(row_count: int) -> list[int]:
    return list(
        range(
            ROLLING_INITIAL_DAYS,
            row_count - FORECAST_HORIZON_DAYS + 1,
            ROLLING_STEP_DAYS,
        )
    )


def split_tuning_and_evaluation_origins(
    row_count: int,
    evaluation_origins: int = FINAL_EVALUATION_ORIGINS,
) -> tuple[list[int], list[int]]:
    """Separa ajuste y prueba, cubriendo exactamente el tramo final reservado."""
    evaluation_days = evaluation_origins * FORECAST_HORIZON_DAYS
    evaluation_start = row_count - evaluation_days
    if evaluation_start < ROLLING_INITIAL_DAYS:
        raise ValueError(
            "No hay historial suficiente para reservar los origenes de evaluacion solicitados."
        )
    tuning = [
        origin
        for origin in rolling_origins(row_count)
        if origin + FORECAST_HORIZON_DAYS <= evaluation_start
    ]
    evaluation = list(
        range(evaluation_start, row_count, FORECAST_HORIZON_DAYS)
    )
    return tuning, evaluation


def buscar_mejores_hiperparametros(
    df: pd.DataFrame,
    predictors: list[str],
    target: str,
    origins: Iterable[int] | None = None,
    param_grids: Mapping[
        str, Mapping[str, Sequence[Any]] | Sequence[Mapping[str, Any]]
    ] | None = None,
    max_origins: int | None = TUNING_MAX_ORIGINS,
) -> tuple[dict[str, dict[str, Any]], pd.DataFrame, pd.DataFrame]:
    """Busca hiperparametros con validacion temporal y RMSE promedio.

    Parameters
    ----------
    df:
        Dataset ordenado cronologicamente.
    predictors:
        Variables disponibles para los modelos supervisados.
    target:
        Variable objetivo que se optimiza.
    origins:
        Indices donde inicia cada bloque de validacion. Si se omite se usan los
        origenes Rolling-Origin posibles.
    param_grids:
        Rejillas por modelo. Puede ser una lista de configuraciones explicitas o
        un diccionario ``parametro -> valores``.
    max_origins:
        Limita el costo usando los origenes de ajuste mas recientes. ``None``
        evalua todos.

    Returns
    -------
    mejores_parametros, resumen_candidatos, detalle_por_origen
    """
    selected_origins = list(rolling_origins(len(df)) if origins is None else origins)
    if max_origins is not None and max_origins > 0:
        selected_origins = selected_origins[-max_origins:]
    if not selected_origins:
        raise ValueError("No hay origenes temporales suficientes para ajustar hiperparametros.")

    grids = DEFAULT_PARAM_GRIDS if param_grids is None else param_grids
    detail_rows: list[dict[str, Any]] = []

    for model_name, grid in grids.items():
        for candidate_number, params in enumerate(_expand_grid(grid), start=1):
            params_text = _json_params(params)
            for origin in selected_origins:
                train = df.iloc[:origin].copy()
                test = df.iloc[origin : origin + FORECAST_HORIZON_DAYS].copy()
                base_row = {
                    "dataset": DATASET_TO_USE,
                    "target": target,
                    "modelo": model_name,
                    "candidato": candidate_number,
                    "hiperparametros": params_text,
                    "origen": origin,
                    "fecha_inicio_validacion": test[DATE_COLUMN].min().date(),
                    "fecha_fin_validacion": test[DATE_COLUMN].max().date(),
                }
                try:
                    prediction = _forecast_model(model_name, params, train, test, predictors, target)
                    detail_rows.append(
                        {**base_row, "estado": "correcto", **metricas(test[target].to_numpy(), prediction)}
                    )
                except Exception as exc:
                    detail_rows.append(
                        {
                            **base_row,
                            "estado": "error",
                            "error": f"{type(exc).__name__}: {exc}",
                            "mae": math.nan,
                            "rmse": math.nan,
                            "mape": math.nan,
                        }
                    )

    detail = pd.DataFrame(detail_rows)
    valid = detail.loc[detail["estado"] == "correcto"].copy()
    if valid.empty:
        raise RuntimeError("Ningun candidato pudo evaluarse; revisa las dependencias y las rejillas.")

    summary = (
        valid.groupby(["dataset", "target", "modelo", "candidato", "hiperparametros"], as_index=False)
        .agg(
            origenes_evaluados=("rmse", "size"),
            mae_promedio=("mae", "mean"),
            rmse_promedio=("rmse", "mean"),
            rmse_desviacion=("rmse", "std"),
            mape_promedio=("mape", "mean"),
        )
        .sort_values(["modelo", "rmse_promedio", "mae_promedio"])
    )
    summary["es_mejor"] = False
    best_params: dict[str, dict[str, Any]] = {}
    for model_name, group in summary.groupby("modelo", sort=False):
        best_index = group.index[0]
        summary.loc[best_index, "es_mejor"] = True
        best_params[model_name] = json.loads(summary.loc[best_index, "hiperparametros"])

    return best_params, summary.reset_index(drop=True), detail.reset_index(drop=True)


def empirical_forecasts(train: pd.DataFrame, test: pd.DataFrame, target: str) -> dict[str, np.ndarray]:
    return {
        "empirico_ultimo_valor": np.repeat(float(train[target].iloc[-1]), len(test)),
        "empirico_promedio_7d": np.repeat(float(train[target].tail(7).mean()), len(test)),
    }


def model_forecasts(
    train: pd.DataFrame,
    test: pd.DataFrame,
    predictors: list[str],
    target: str,
    params_by_model: Mapping[str, Mapping[str, Any]],
) -> dict[str, np.ndarray]:
    predictions: dict[str, np.ndarray] = {}
    for model_name, params in params_by_model.items():
        try:
            predictions[model_name] = _forecast_model(
                model_name, params, train, test, predictors, target
            )
        except Exception:
            # Las dependencias opcionales o un ajuste numericamente inestable no
            # deben eliminar los resultados de los demas modelos.
            continue
    return predictions


def rolling_origin_evaluation(
    df: pd.DataFrame,
    best_params_by_target: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
    origins: Iterable[int] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    predictors = [
        column
        for column in df.columns
        if column not in TARGET_COLUMNS + [DATE_COLUMN]
        and pd.api.types.is_numeric_dtype(df[column])
    ]
    selected_origins = list(rolling_origins(len(df)) if origins is None else origins)

    for target in TARGET_COLUMNS:
        target_params = (
            best_params_by_target.get(target, DEFAULT_MODEL_PARAMS)
            if best_params_by_target is not None
            else DEFAULT_MODEL_PARAMS
        )
        for origin in selected_origins:
            train = df.iloc[:origin].copy()
            test = df.iloc[origin : origin + FORECAST_HORIZON_DAYS].copy()
            y_true = test[target].to_numpy(dtype=float)
            all_predictions = empirical_forecasts(train, test, target)
            all_predictions.update(model_forecasts(train, test, predictors, target, target_params))

            for model_name, y_pred in all_predictions.items():
                params = target_params.get(model_name, {})
                rows.append(
                    {
                        "dataset": DATASET_TO_USE,
                        "target": target,
                        "modelo": model_name,
                        "hiperparametros": _json_params(params),
                        "fecha_inicio_prueba": test[DATE_COLUMN].min().date(),
                        "fecha_fin_prueba": test[DATE_COLUMN].max().date(),
                        **metricas(y_true, y_pred),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    out_dir = ensure_output_dir()
    df = load_dataset_variant()
    predictors = [
        column
        for column in df.columns
        if column not in TARGET_COLUMNS + [DATE_COLUMN]
        and pd.api.types.is_numeric_dtype(df[column])
    ]
    origins = rolling_origins(len(df))
    if not origins:
        raise ValueError(
            f"Se requieren mas de {ROLLING_INITIAL_DAYS + FORECAST_HORIZON_DAYS} filas "
            "para ejecutar Rolling-Origin."
        )

    best_by_target: dict[str, dict[str, dict[str, Any]]] = {}
    tuning_summaries: list[pd.DataFrame] = []
    tuning_details: list[pd.DataFrame] = []

    if ENABLE_HYPERPARAMETER_TUNING:
        available_tuning_origins, evaluation_origins = split_tuning_and_evaluation_origins(
            len(df), FINAL_EVALUATION_ORIGINS
        )
        if not available_tuning_origins:
            raise ValueError("No hay origenes anteriores a la evaluacion final para realizar el ajuste.")
        for target in TARGET_COLUMNS:
            best, summary, detail = buscar_mejores_hiperparametros(
                df,
                predictors,
                target,
                origins=available_tuning_origins,
                max_origins=TUNING_MAX_ORIGINS,
            )
            best_by_target[target] = best
            tuning_summaries.append(summary)
            tuning_details.append(detail)
    else:
        evaluation_origins = origins
        best_by_target = {target: DEFAULT_MODEL_PARAMS for target in TARGET_COLUMNS}

    results = rolling_origin_evaluation(df, best_by_target, evaluation_origins)
    ranking = (
        results.groupby(["dataset", "target", "modelo", "hiperparametros"], as_index=False)
        .agg(
            origenes_evaluados=("rmse", "size"),
            mae_promedio=("mae", "mean"),
            rmse_promedio=("rmse", "mean"),
            rmse_desviacion=("rmse", "std"),
            mape_promedio=("mape", "mean"),
        )
        .sort_values(["target", "rmse_promedio"])
    )
    best_rows = [
        {
            "dataset": DATASET_TO_USE,
            "target": target,
            "modelo": model_name,
            "hiperparametros": _json_params(params),
        }
        for target, models in best_by_target.items()
        for model_name, params in models.items()
    ]

    output_xlsx = out_dir / f"05_modelos_rolling_origin_{DATASET_TO_USE}.xlsx"
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        results.to_excel(writer, sheet_name="resultados_por_origen", index=False)
        ranking.to_excel(writer, sheet_name="ranking_modelos", index=False)
        pd.DataFrame(best_rows).to_excel(writer, sheet_name="mejores_hiperparametros", index=False)
        if tuning_summaries:
            pd.concat(tuning_summaries, ignore_index=True).to_excel(
                writer, sheet_name="resumen_ajuste", index=False
            )
            pd.concat(tuning_details, ignore_index=True).to_excel(
                writer, sheet_name="detalle_ajuste", index=False
            )

    print(f"Archivo generado: {output_xlsx}")


if __name__ == "__main__":
    main()
