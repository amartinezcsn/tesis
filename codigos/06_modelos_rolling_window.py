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
from collections.abc import Iterable

import numpy as np
import pandas as pd

from config_semanal import (
    BASELINE_NAMES,
    DATE_COLUMN,
    FINAL_EVALUATION_WEEKS,
    HORIZON_WEEKS,
    MAX_FEATURES,
    PRIMARY_BASELINE,
    RANDOM_STATE,
    STEP_WEEKS,
    TARGET_COLUMN,
    TUNING_WINDOWS,
    WEEKLY_MODEL_PATH,
    WINDOW_WEEKS,
    ensure_output_dir,
)


ML_GRIDS = {
    "ridge": [{"alpha": 0.1}, {"alpha": 1.0}, {"alpha": 10.0}],
    "random_forest": [
        {"n_estimators": 300, "max_depth": 4, "min_samples_leaf": 3},
        {"n_estimators": 500, "max_depth": None, "min_samples_leaf": 4},
    ],
    "hist_gradient": [
        {"learning_rate": 0.05, "max_leaf_nodes": 7, "l2_regularization": 1.0},
        {"learning_rate": 0.10, "max_leaf_nodes": 5, "l2_regularization": 2.0},
    ],
}
STATISTICAL_MODELS = ("arima", "ets", "croston_sba")


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
    if tail >= FINAL_EVALUATION_WEEKS:
        return frame.iloc[: active[-1] + 1].copy(), int(tail)
    return frame.copy(), 0


def iter_rolling_windows(row_count: int) -> list[int]:
    """Devuelve índices donde inicia el bloque de prueba de rolling-window."""
    first = WINDOW_WEEKS
    last = row_count - HORIZON_WEEKS
    if last < first:
        return []
    return list(range(first, last + 1, STEP_WEEKS))


def split_tuning_evaluation(origins: list[int]) -> tuple[list[int], list[int]]:
    """Reserva semanas finales para evaluación sin usarlas para ajuste."""
    if len(origins) <= FINAL_EVALUATION_WEEKS:
        raise ValueError("No hay suficientes semanas para reservar la evaluación final.")
    evaluation = origins[-FINAL_EVALUATION_WEEKS:]
    tuning = origins[:-FINAL_EVALUATION_WEEKS][-TUNING_WINDOWS:]
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
    scores = train[usable].corrwith(train[TARGET_COLUMN]).abs().fillna(0)
    return scores.sort_values(ascending=False).head(MAX_FEATURES).index.tolist()


def prepare_xy(train: pd.DataFrame, test: pd.DataFrame, features: list[str]):
    """Imputa usando sólo información del entrenamiento y devuelve X, y."""
    x_train = train[features].replace([np.inf, -np.inf], np.nan)
    medians = x_train.median(numeric_only=True).fillna(0)
    x_train = x_train.fillna(medians).fillna(0)
    x_test = test[features].replace([np.inf, -np.inf], np.nan).fillna(medians).fillna(0)
    return x_train, x_test, train[TARGET_COLUMN].fillna(0).to_numpy(dtype=float)


def forecast_ml(name: str, params: dict, train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> np.ndarray:
    """Ajusta un modelo tabular y devuelve predicciones no negativas."""
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import Ridge

    x_train, x_test, y_train = prepare_xy(train, test, features)
    if name == "ridge":
        model = Ridge(**params)
    elif name == "random_forest":
        model = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1, **params)
    elif name == "hist_gradient":
        model = HistGradientBoostingRegressor(random_state=RANDOM_STATE, **params)
    else:
        raise ValueError(f"Modelo ML no soportado: {name}")
    model.fit(x_train, y_train)
    return np.maximum(model.predict(x_test), 0)


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
            fitted = ARIMA(y, order=(1, 0, 1)).fit()
            return np.maximum(np.asarray(fitted.forecast(steps=steps), dtype=float), 0)
        if name == "ets":
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            fitted = ExponentialSmoothing(y, trend="add", seasonal=None).fit(optimized=True)
            return np.maximum(np.asarray(fitted.forecast(steps), dtype=float), 0)
    except Exception:
        return np.repeat(float(np.mean(y[-4:])), steps)
    raise ValueError(f"Modelo estadístico no soportado: {name}")


def empirical_forecasts(train: pd.DataFrame, steps: int) -> dict[str, np.ndarray]:
    """Calcula referencias empíricas predefinidas para cada semana de prueba."""
    y = train[TARGET_COLUMN].fillna(0).to_numpy(dtype=float)
    seasonal = y[-52] if len(y) >= 52 else np.nan
    return {
        "empirico_ultimo_valor": np.repeat(y[-1], steps),
        "empirico_promedio_4s": np.repeat(float(np.mean(y[-4:])), steps),
        "empirico_estacional_52s": np.repeat(seasonal, steps),
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


def tune_parameters(frame: pd.DataFrame, origins: Iterable[int], model: str, feature_set: str) -> dict:
    """Elige hiperparámetros con ventanas anteriores a la evaluación final."""
    candidates = candidate_parameters(model)
    scores: list[tuple[float, dict]] = []
    for params in candidates:
        losses = []
        for origin in origins:
            train = frame.iloc[origin - WINDOW_WEEKS : origin]
            test = frame.iloc[origin : origin + HORIZON_WEEKS]
            if model in STATISTICAL_MODELS:
                prediction = forecast_statistical(model, train, len(test))
            else:
                features = select_features(train, feature_set == "historico_exogeno")
                prediction = forecast_ml(model, params, train, test, features)
            losses.append(float(np.mean((test[TARGET_COLUMN].to_numpy() - prediction) ** 2)))
        scores.append((float(np.mean(losses)), params))
    return min(scores, key=lambda item: item[0])[1]


def evaluate_windows(frame: pd.DataFrame, origins: Iterable[int], model: str, feature_set: str, params: dict) -> list[dict]:
    """Genera una fila por predicción; es la evidencia auditable de H1 y H2."""
    rows: list[dict] = []
    for origin in origins:
        train = frame.iloc[origin - WINDOW_WEEKS : origin]
        test = frame.iloc[origin : origin + HORIZON_WEEKS]
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
        for (_, observed), predicted in zip(test.iterrows(), prediction):
            actual = float(observed[TARGET_COLUMN])
            error = actual - float(predicted)
            rows.append(
                {
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
    for keys, group in predictions.groupby(["modelo", "feature_set", "hiperparametros"], dropna=False):
        real = group["real"].to_numpy(dtype=float)
        absolute = group["error_absoluto"].to_numpy(dtype=float)
        squared = group["error_cuadrado"].to_numpy(dtype=float)
        nonzero = np.abs(real) > 1e-8
        mase = absolute / group["escala_mase"].replace(0, np.nan).to_numpy(dtype=float)
        rmsse_terms = squared / group["escala_rmsse"].replace(0, np.nan).to_numpy(dtype=float)
        rows.append(
            {
                "modelo": keys[0],
                "feature_set": keys[1],
                "hiperparametros": keys[2],
                "semanas_evaluadas": len(group),
                "mae": float(np.mean(absolute)),
                "rmse": float(np.sqrt(np.mean(squared))),
                "mase": float(np.nanmean(mase)),
                "rmsse": float(np.sqrt(np.nanmean(rmsse_terms))),
                "mape_diagnostico": float(np.mean(absolute[nonzero] / np.abs(real[nonzero])) * 100) if nonzero.any() else math.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["rmse", "mae"]).reset_index(drop=True)


def paired_loss_test(left: pd.DataFrame, right: pd.DataFrame, hypothesis: str) -> dict:
    """Prueba unilateral simple sobre diferencias de error cuadrado alineadas."""
    joined = left.merge(right, on="semana_prueba", suffixes=("_left", "_right"))
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
    return {"hipotesis": hypothesis, "semanas": n, "diferencia_media_error_cuadrado": mean, "t": statistic, "p_unilateral": pvalue}


def hypothesis_tables(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye resultados reproducibles de H1 y H2."""
    h1_rows = []
    baseline = predictions.loc[predictions["modelo"].eq(PRIMARY_BASELINE)]
    for model in predictions.loc[~predictions["modelo"].isin(BASELINE_NAMES), "modelo"].unique():
        candidate = predictions.loc[(predictions["modelo"] == model) & (predictions["feature_set"] != "historico")]
        if not candidate.empty:
            h1_rows.append(paired_loss_test(baseline, candidate, f"H1:{model} vs {PRIMARY_BASELINE}"))
    h2_rows = []
    for model in ML_GRIDS:
        historical = predictions.loc[(predictions["modelo"] == model) & (predictions["feature_set"] == "historico")]
        enriched = predictions.loc[(predictions["modelo"] == model) & (predictions["feature_set"] == "historico_exogeno")]
        if not historical.empty and not enriched.empty:
            h2_rows.append(paired_loss_test(historical, enriched, f"H2:{model} histórico vs enriquecido"))
    return pd.DataFrame(h1_rows), pd.DataFrame(h2_rows)


def main() -> None:
    """Ejecuta el experimento semanal y exporta predicciones, métricas e hipótesis."""
    validate_optional_dependencies()
    frame = pd.read_excel(WEEKLY_MODEL_PATH, sheet_name="modelo_semanal")
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN])
    frame, tail = trim_unobserved_tail(frame)
    origins = iter_rolling_windows(len(frame))
    tuning_origins, evaluation_origins = split_tuning_evaluation(origins)

    configurations: list[tuple[str, str, dict]] = []
    for baseline in BASELINE_NAMES:
        configurations.append((baseline, "referencia", {}))
    for model in STATISTICAL_MODELS:
        configurations.append((model, "univariado", {}))
    for model in ML_GRIDS:
        for feature_set in ("historico", "historico_exogeno"):
            configurations.append((model, feature_set, tune_parameters(frame, tuning_origins, model, feature_set)))

    rows: list[dict] = []
    for model, feature_set, params in configurations:
        rows.extend(evaluate_windows(frame, evaluation_origins, model, feature_set, params))
    predictions = pd.DataFrame(rows)
    summary = summarize_predictions(predictions)
    h1, h2 = hypothesis_tables(predictions)
    coverage = pd.DataFrame(
        {
            "metrica": ["semanas_disponibles", "semanas_cola_excluidas", "ventana_entrenamiento", "semanas_evaluacion", "baseline_primaria"],
            "valor": [len(frame), tail, WINDOW_WEEKS, len(evaluation_origins), PRIMARY_BASELINE],
        }
    )
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
