"""Evalúa modelos semanales con rolling-window (ventana deslizante).

La ventana de entrenamiento contiene siempre las 52 semanas inmediatamente
anteriores al pronóstico. Cada iteración avanza una semana, incorpora la
observación recién conocida y excluye la semana más antigua.

H1 compara modelos contra la línea base primaria de promedio móvil de cuatro
semanas. H2 compara el mismo modelo con predictores históricos y con el
conjunto enriquecido de variables exógenas.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable

import numpy as np
import pandas as pd

from config_semanal import (
    BASELINE_NAMES,
    FINAL_EVALUATION_ORIGINS,
    FORECAST_HORIZONS,
    H1_MIN_RMSE_REDUCTION,
    DATE_COLUMN,
    MAX_FEATURES,
    PRIMARY_BASELINE,
    PRIMARY_HORIZON_WEEKS,
    RANDOM_STATE,
    SARIMA_SEASONAL_PERIOD_WEEKS,
    SIGNIFICANCE_ALPHA,
    STEP_WEEKS,
    TARGET_COLUMN,
    TUNING_WINDOWS,
    WEEKLY_DELAYED_EXOGENOUS,
    WEEKLY_MODEL_PATH,
    WINDOW_WEEKS,
    ensure_output_dir,
)


ML_GRIDS = {
    "ridge": [{"alpha": 0.1}, {"alpha": 1.0}, {"alpha": 10.0}],
    "lasso": [
        {"alpha": 0.1, "max_iter": 50000, "tol": 1e-3},
        {"alpha": 1.0, "max_iter": 50000, "tol": 1e-3},
        {"alpha": 10.0, "max_iter": 50000, "tol": 1e-3},
    ],
    "random_forest": [
        {"n_estimators": 300, "max_depth": 4, "min_samples_leaf": 3},
        {"n_estimators": 500, "max_depth": None, "min_samples_leaf": 4},
    ],
    "hist_gradient": [
        {"learning_rate": 0.05, "max_leaf_nodes": 7, "l2_regularization": 1.0},
        {"learning_rate": 0.10, "max_leaf_nodes": 5, "l2_regularization": 2.0},
    ],
}
STATISTICAL_MODELS = ("arima", "ets", "sarima", "croston_sba")
TARGET_HISTORY_PREFIX = "hist_compras_importe_semanal_"


def validate_optional_dependencies() -> None:
    """Verifica dependencias antes de iniciar una corrida costosa.

    El mensaje explica cómo instalar los paquetes en el entorno aislado del
    proyecto, en lugar de fallar más adelante dentro de un modelo concreto.
    """
    unavailable = []
    for package in ("sklearn", "statsmodels", "scipy"):
        try:
            __import__(package)
        except Exception as exc:  # ImportError o instalación parcial/corrupta.
            unavailable.append(f"{package} ({type(exc).__name__})")
    if unavailable:
        raise RuntimeError(
            "Las dependencias analíticas no están disponibles correctamente: "
            + ", ".join(unavailable)
            + ". Instala codigos/requirements_pipeline_semanal.txt en un entorno aislado antes de ejecutar modelos."
        )


def trim_unobserved_tail(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Recorta una cola prolongada de ceros atribuible a falta de cobertura.

    La fuente de compras termina antes que ventas. Si el objetivo contiene una
    cola de ceros de al menos 16 semanas, dicha cola se interpreta como
    cobertura ausente y se excluye del análisis, conservando los ceros internos.
    """
    values = frame[TARGET_COLUMN].fillna(0).to_numpy(dtype=float)
    active = np.flatnonzero(np.abs(values) > 1e-8)
    if not len(active):
        raise ValueError("El objetivo semanal no contiene compras positivas.")
    tail = len(frame) - active[-1] - 1
    if tail >= FINAL_EVALUATION_ORIGINS:
        return frame.iloc[: active[-1] + 1].copy(), int(tail)
    return frame.copy(), 0


def iter_rolling_windows(row_count: int, horizon: int = PRIMARY_HORIZON_WEEKS) -> list[int]:
    """Devuelve orígenes cuyo bloque futuro cabe en el dataset."""
    if horizon < 1:
        raise ValueError("El horizonte debe ser mayor que cero.")
    first = WINDOW_WEEKS
    last = row_count - horizon
    if last < first:
        return []
    return list(range(first, last + 1, STEP_WEEKS))


def split_tuning_evaluation(origins: list[int]) -> tuple[list[int], list[int]]:
    """Reserva semanas finales para evaluación sin usarlas para ajuste."""
    if len(origins) <= FINAL_EVALUATION_ORIGINS:
        raise ValueError("No hay suficientes orígenes para reservar la evaluación final.")
    evaluation = origins[-FINAL_EVALUATION_ORIGINS:]
    tuning = origins[:-FINAL_EVALUATION_ORIGINS][-TUNING_WINDOWS:]
    if not tuning:
        raise ValueError("No hay ventanas previas para ajustar hiperparámetros.")
    return tuning, evaluation


def select_features(train: pd.DataFrame, include_exogenous: bool) -> list[str]:
    """Selecciona hasta ``MAX_FEATURES`` variables usando sólo el entrenamiento.

    La selección por correlación es deliberadamente simple y trazable. Las
    variables constantes se excluyen y los predictores con mayor relación
    absoluta con el objetivo se conservan para el ajuste del modelo.
    """
    candidates = [c for c in train.columns if c.startswith("hist_")]
    if include_exogenous:
        candidates.extend(c for c in train.columns if c.startswith("exog_"))
    usable = [c for c in candidates if train[c].nunique(dropna=True) > 1]
    if not usable:
        raise ValueError(
            "No hay predictores variables disponibles en la ventana de entrenamiento."
        )
    scores = train[usable].corrwith(train[TARGET_COLUMN]).abs().fillna(0)
    return scores.sort_values(ascending=False).head(MAX_FEATURES).index.tolist()


def prepare_xy(train: pd.DataFrame, test: pd.DataFrame, features: list[str]):
    """Imputa usando sólo información del entrenamiento y devuelve X, y."""
    x_train = train[features].replace([np.inf, -np.inf], np.nan)
    medians = x_train.median(numeric_only=True).fillna(0)
    x_train = x_train.fillna(medians).fillna(0)
    x_test = test[features].replace([np.inf, -np.inf], np.nan).fillna(medians).fillna(0)
    return x_train, x_test, train[TARGET_COLUMN].fillna(0).to_numpy(dtype=float)


def _fit_ml_model(name: str, params: dict):
    """Construye el modelo supervisado de la rejilla metodológica."""
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import Lasso, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if name == "ridge":
        return make_pipeline(StandardScaler(), Ridge(**params))
    if name == "lasso":
        return make_pipeline(StandardScaler(), Lasso(random_state=RANDOM_STATE, **params))
    if name == "random_forest":
        # Un solo proceso hace la corrida reproducible y evita que el número
        # de núcleos físicos del equipo cambie el comportamiento del pipeline.
        return RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=1, **params)
    if name == "hist_gradient":
        return HistGradientBoostingRegressor(random_state=RANDOM_STATE, **params)
    raise ValueError(f"Modelo ML no soportado: {name}")


def forecast_ml(name: str, params: dict, train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> np.ndarray:
    """Pronostica recursivamente sin usar predictores históricos futuros."""
    x_train, _, y_train = prepare_xy(train, test.iloc[:0], features)
    model = _fit_ml_model(name, params)
    model.fit(x_train, y_train)

    history = train[TARGET_COLUMN].fillna(0).to_numpy(dtype=float).tolist()
    origin_row = train.iloc[-1]
    predictions: list[float] = []
    for step, (_, test_row) in enumerate(test.iterrows()):
        row = test_row.copy()
        if step > 0:
            row = _recursive_feature_row(row, origin_row, features, history)
        _, x_test, _ = prepare_xy(train, pd.DataFrame([row]), features)
        predicted = float(np.maximum(model.predict(x_test)[0], 0))
        predictions.append(predicted)
        history.append(predicted)
    return np.asarray(predictions, dtype=float)


def _recursive_feature_row(
    row: pd.Series,
    origin_row: pd.Series,
    features: list[str],
    target_history: list[float],
) -> pd.Series:
    """Construye una fila futura con historia conocida o predicha.

    Para H=4, las ventas futuras no están disponibles. Sus predictores
    históricos se mantienen en el último estado conocido; los predictores del
    objetivo se actualizan con las predicciones previas. INPC y temperatura se
    conservan en su último valor publicado/observado para impedir fuga.
    """
    result = row.copy()
    for feature in features:
        if feature.startswith(TARGET_HISTORY_PREFIX):
            result[feature] = _target_history_value(feature, target_history)
        elif feature.startswith("hist_") or feature in WEEKLY_DELAYED_EXOGENOUS:
            result[feature] = origin_row.get(feature, np.nan)
    return result


def _target_history_value(feature: str, history: list[float]) -> float:
    suffix = feature[len(TARGET_HISTORY_PREFIX) :]
    lag_match = re.fullmatch(r"lag_(\d+)s", suffix)
    if lag_match:
        lag = int(lag_match.group(1))
        return float(history[-lag]) if len(history) >= lag else 0.0
    window_match = re.fullmatch(r"(media|desv)_(\d+)s", suffix)
    if window_match:
        kind, size_text = window_match.groups()
        values = np.asarray(history[-int(size_text) :], dtype=float)
        if not len(values):
            return 0.0
        if kind == "media":
            return float(np.mean(values))
        return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return 0.0


def forecast_statistical(name: str, train: pd.DataFrame, steps: int) -> np.ndarray:
    """Ajusta alternativas univariadas compatibles con una ventana de 52 semanas."""
    y = train[TARGET_COLUMN].fillna(0).to_numpy(dtype=float)
    if name == "croston_sba":
        nonzero = np.flatnonzero(y > 0)
        if len(nonzero) == 0:
            return np.zeros(steps)
        alpha = 0.1
        demand, interval = y[nonzero[0]], max(nonzero[0] + 1, 1)
        elapsed = 0
        for value in y:
            elapsed += 1
            if value > 0:
                demand += alpha * (value - demand)
                interval += alpha * (elapsed - interval)
                elapsed = 0
        return np.repeat(max((1 - alpha / 2) * demand / max(interval, 1e-8), 0), steps)

    try:
        if name == "arima":
            from statsmodels.tsa.arima.model import ARIMA
            fitted = ARIMA(y, order=(1, 1, 1)).fit()
            return np.maximum(np.asarray(fitted.forecast(steps=steps), dtype=float), 0)
        if name == "ets":
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            fitted = ExponentialSmoothing(y, trend="add", seasonal=None).fit(optimized=True)
            return np.maximum(np.asarray(fitted.forecast(steps), dtype=float), 0)
        if name == "sarima":
            from statsmodels.tsa.statespace.sarimax import SARIMAX

            fitted = SARIMAX(
                y,
                order=(1, 1, 1),
                seasonal_order=(0, 0, 1, SARIMA_SEASONAL_PERIOD_WEEKS),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)
            return np.maximum(np.asarray(fitted.forecast(steps=steps), dtype=float), 0)
    except Exception:
        return np.repeat(float(np.mean(y[-4:])), steps)
    raise ValueError(f"Modelo estadístico no soportado: {name}")


def empirical_forecasts(train: pd.DataFrame, steps: int) -> dict[str, np.ndarray]:
    """Calcula referencias empíricas predefinidas para cada semana de prueba."""
    y = train[TARGET_COLUMN].fillna(0).to_numpy(dtype=float)
    if len(y) >= 52:
        seasonal = y[-52 : -52 + steps]
        if len(seasonal) < steps:
            seasonal = np.pad(seasonal, (0, steps - len(seasonal)), mode="edge")
    else:
        seasonal = np.repeat(y[-1], steps)
    return {
        "empirico_ultimo_valor": np.repeat(y[-1], steps),
        "empirico_promedio_4s": np.repeat(float(np.mean(y[-4:])), steps),
        "empirico_estacional_52s": np.asarray(seasonal, dtype=float),
    }


def scales_from_training(train: pd.DataFrame) -> tuple[float, float]:
    """Obtiene escalas MASE y RMSSE sólo a partir del entrenamiento."""
    y = train[TARGET_COLUMN].fillna(0).to_numpy(dtype=float)
    naive_errors = np.diff(y)
    mae_scale = float(np.mean(np.abs(naive_errors))) if len(naive_errors) else math.nan
    mse_scale = float(np.mean(naive_errors**2)) if len(naive_errors) else math.nan
    return mae_scale, mse_scale


def candidate_parameters(name: str) -> list[dict]:
    """Devuelve rejillas compactas; los estadísticos no requieren ajuste amplio."""
    return ML_GRIDS.get(name, [{}])


def tune_parameters(frame: pd.DataFrame, origins: Iterable[int], model: str, feature_set: str, horizon: int) -> dict:
    """Elige hiperparámetros con orígenes anteriores a la evaluación final."""
    candidates = candidate_parameters(model)
    scores: list[tuple[float, dict]] = []
    for params in candidates:
        losses = []
        for origin in origins:
            train = frame.iloc[origin - WINDOW_WEEKS : origin]
            test = frame.iloc[origin : origin + horizon]
            if model in STATISTICAL_MODELS:
                prediction = forecast_statistical(model, train, len(test))
            else:
                features = select_features(train, feature_set == "historico_exogeno")
                prediction = forecast_ml(model, params, train, test, features)
            losses.append(float(np.mean((test[TARGET_COLUMN].to_numpy() - prediction) ** 2)))
        scores.append((float(np.mean(losses)), params))
    return min(scores, key=lambda item: item[0])[1]


def evaluate_windows(
    frame: pd.DataFrame,
    origins: Iterable[int],
    model: str,
    feature_set: str,
    params: dict,
    horizon: int,
) -> list[dict]:
    """Genera una fila por paso y origen para auditar H1 y H2."""
    rows: list[dict] = []
    for origin in origins:
        train = frame.iloc[origin - WINDOW_WEEKS : origin]
        test = frame.iloc[origin : origin + horizon]
        if model in BASELINE_NAMES:
            prediction = empirical_forecasts(train, len(test))[model]
            features = []
        elif model in STATISTICAL_MODELS:
            prediction = forecast_statistical(model, train, len(test))
            features = []
        else:
            features = select_features(train, feature_set == "historico_exogeno")
            prediction = forecast_ml(model, params, train, test, features)
        mase_scale, rmsse_scale = scales_from_training(train)
        for step, ((_, observed), predicted) in enumerate(zip(test.iterrows(), prediction), start=1):
            actual = float(observed[TARGET_COLUMN])
            error = actual - float(predicted)
            rows.append(
                {
                    "horizonte": horizon,
                    "origen_pronostico": frame.iloc[origin][DATE_COLUMN],
                    "paso_horizonte": step,
                    "semana_prueba": observed[DATE_COLUMN],
                    "modelo": model,
                    "feature_set": feature_set,
                    "hiperparametros": json.dumps(params, ensure_ascii=False, sort_keys=True),
                    "variables_seleccionadas": "; ".join(features),
                    "real": actual,
                    "prediccion": float(predicted),
                    "error_absoluto": abs(error),
                    "error_cuadrado": error**2,
                    "escala_mase": mase_scale,
                    "escala_rmsse": rmsse_scale,
                }
            )
    return rows


def summarize_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Calcula métricas agregadas sin usar MAPE como criterio de selección."""
    rows = []
    for keys, group in predictions.groupby(
        ["horizonte", "modelo", "feature_set", "hiperparametros"], dropna=False
    ):
        real = group["real"].to_numpy(dtype=float)
        absolute = group["error_absoluto"].to_numpy(dtype=float)
        squared = group["error_cuadrado"].to_numpy(dtype=float)
        nonzero = np.abs(real) > 1e-8
        mase = absolute / group["escala_mase"].replace(0, np.nan).to_numpy(dtype=float)
        rmsse_terms = squared / group["escala_rmsse"].replace(0, np.nan).to_numpy(dtype=float)
        rows.append(
            {
                "horizonte": keys[0],
                "modelo": keys[1],
                "feature_set": keys[2],
                "hiperparametros": keys[3],
                "observaciones_evaluadas": len(group),
                "mae": float(np.mean(absolute)),
                "rmse": float(np.sqrt(np.mean(squared))),
                "mase": float(np.nanmean(mase)),
                "rmsse": float(np.sqrt(np.nanmean(rmsse_terms))),
                "mape_diagnostico": float(np.mean(absolute[nonzero] / np.abs(real[nonzero])) * 100) if nonzero.any() else math.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["horizonte", "rmse", "mae"]).reset_index(drop=True)


def paired_loss_test(
    left: pd.DataFrame,
    right: pd.DataFrame,
    hypothesis: str,
    minimum_reduction: float | None = H1_MIN_RMSE_REDUCTION,
) -> dict:
    """Contrasta pérdidas cuadráticas pareadas en los mismos orígenes/pasos."""
    keys = ["horizonte", "origen_pronostico", "paso_horizonte"]
    joined = left.merge(right, on=keys, suffixes=("_left", "_right"))
    difference = joined["error_cuadrado_left"] - joined["error_cuadrado_right"]
    n = len(difference)
    mean = float(difference.mean()) if n else math.nan
    std = float(difference.std(ddof=1)) if n > 1 else math.nan
    statistic = mean / (std / math.sqrt(n)) if n > 1 and std > 0 else math.nan
    try:
        from scipy.stats import t as t_distribution
        pvalue = float(t_distribution.sf(statistic, df=n - 1)) if n > 1 and not math.isnan(statistic) else math.nan
    except ImportError:
        pvalue = math.nan
    baseline_rmse = float(np.sqrt(np.mean(joined["error_cuadrado_left"]))) if n else math.nan
    candidate_rmse = float(np.sqrt(np.mean(joined["error_cuadrado_right"]))) if n else math.nan
    reduction = (
        float((baseline_rmse - candidate_rmse) / baseline_rmse)
        if baseline_rmse > 0
        else math.nan
    )
    significant = bool(not math.isnan(pvalue) and pvalue < SIGNIFICANCE_ALPHA)
    improves = bool(not math.isnan(reduction) and reduction > 0)
    meets_threshold = (
        bool(not math.isnan(reduction) and reduction >= minimum_reduction)
        if minimum_reduction is not None
        else None
    )
    return {
        "hipotesis": hypothesis,
        "horizonte": int(joined["horizonte"].iloc[0]) if n else math.nan,
        "observaciones_pareadas": n,
        "rmse_referencia": baseline_rmse,
        "rmse_configuracion": candidate_rmse,
        "reduccion_rmse": reduction,
        "diferencia_media_error_cuadrado": mean,
        "t": statistic,
        "p_unilateral": pvalue,
        "alpha": SIGNIFICANCE_ALPHA,
        "significativo": significant,
        "umbral_reduccion": minimum_reduction,
        "cumple_umbral_20pct": meets_threshold,
        "cumple_direccion_mejora": improves,
        "apoya_hipotesis": significant and (meets_threshold if minimum_reduction is not None else improves),
    }


def hypothesis_tables(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye resultados reproducibles de H1 y H2."""
    h1_rows = []
    for horizon in sorted(predictions["horizonte"].unique()):
        baseline = predictions.loc[
            (predictions["horizonte"] == horizon) & predictions["modelo"].eq(PRIMARY_BASELINE)
        ]
        candidates = predictions.loc[
            (predictions["horizonte"] == horizon)
            & ~predictions["modelo"].isin(BASELINE_NAMES)
        ]
        for (model, feature_set), candidate in candidates.groupby(["modelo", "feature_set"]):
            if not candidate.empty:
                h1_rows.append(
                    paired_loss_test(
                        baseline,
                        candidate,
                        f"H1:H{horizon}:{model}/{feature_set} vs {PRIMARY_BASELINE}",
                    )
                )
    h2_rows = []
    for horizon in sorted(predictions["horizonte"].unique()):
        for model in ML_GRIDS:
            historical = predictions.loc[
                (predictions["horizonte"] == horizon)
                & predictions["modelo"].eq(model)
                & predictions["feature_set"].eq("historico")
            ]
            enriched = predictions.loc[
                (predictions["horizonte"] == horizon)
                & predictions["modelo"].eq(model)
                & predictions["feature_set"].eq("historico_exogeno")
            ]
            if not historical.empty and not enriched.empty:
                h2_rows.append(
                    paired_loss_test(
                        historical,
                        enriched,
                        f"H2:H{horizon}:{model} histórico vs enriquecido",
                        minimum_reduction=None,
                    )
                )
    return pd.DataFrame(h1_rows), pd.DataFrame(h2_rows)


def main() -> None:
    """Ejecuta el experimento semanal y exporta predicciones, métricas e hipótesis."""
    validate_optional_dependencies()
    frame = pd.read_excel(WEEKLY_MODEL_PATH, sheet_name="modelo_semanal")
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN])
    frame, tail = trim_unobserved_tail(frame)

    rows: list[dict] = []
    coverage_rows: list[dict] = []
    for horizon in FORECAST_HORIZONS:
        origins = iter_rolling_windows(len(frame), horizon)
        tuning_origins, evaluation_origins = split_tuning_evaluation(origins)
        configurations: list[tuple[str, str, dict]] = [
            (baseline, "referencia", {}) for baseline in BASELINE_NAMES
        ]
        configurations.extend((model, "univariado", {}) for model in STATISTICAL_MODELS)
        for model in ML_GRIDS:
            for feature_set in ("historico", "historico_exogeno"):
                configurations.append(
                    (
                        model,
                        feature_set,
                        tune_parameters(frame, tuning_origins, model, feature_set, horizon),
                    )
                )
        for model, feature_set, params in configurations:
            rows.extend(
                evaluate_windows(frame, evaluation_origins, model, feature_set, params, horizon)
            )
        coverage_rows.append(
            {
                "horizonte": horizon,
                "semanas_disponibles": len(frame),
                "semanas_cola_excluidas": tail,
                "ventana_entrenamiento": WINDOW_WEEKS,
                "origenes_ajuste": len(tuning_origins),
                "origenes_evaluacion": len(evaluation_origins),
                "pasos_evaluados": len(evaluation_origins) * horizon,
                "baseline_primaria": PRIMARY_BASELINE,
            }
        )
    predictions = pd.DataFrame(rows)
    summary = summarize_predictions(predictions)
    h1, h2 = hypothesis_tables(predictions)
    coverage = pd.DataFrame(coverage_rows)
    output = ensure_output_dir() / "02_modelos_rolling_window.xlsx"
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        predictions.to_excel(writer, sheet_name="predicciones", index=False)
        summary.to_excel(writer, sheet_name="metricas", index=False)
        h1.to_excel(writer, sheet_name="contraste_h1", index=False)
        h2.to_excel(writer, sheet_name="contraste_h2", index=False)
        coverage.to_excel(writer, sheet_name="cobertura", index=False)
    print(f"Archivo generado: {output}")


if __name__ == "__main__":
    main()
