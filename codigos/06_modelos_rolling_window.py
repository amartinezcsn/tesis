"""Evalúa modelos semanales con rolling-window (ventana deslizante).

La ventana de entrenamiento contiene siempre las 52 semanas inmediatamente
anteriores al pronóstico. Cada iteración avanza una semana, incorpora la
observación recién conocida y excluye la semana más antigua.

H1 compara modelos contra la línea base primaria de último valor observado.
H2 compara el mismo modelo con predictores históricos y con el conjunto
enriquecido de variables exógenas. Se reportan por separado los horizontes
directos h=1 y h=4; los cuatro horizontes h=1..4 alimentan un consolidado
mensual de pronósticos semanales.
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
    MONTHLY_CONSOLIDATION_HORIZONS,
    PRIMARY_BASELINE,
    RANDOM_STATE,
    SIGNIFICANCE_LEVEL,
    STEP_WEEKS,
    SECONDARY_HORIZON_WEEKS,
    TARGET_COLUMN,
    TUNING_WINDOWS,
    WEEKLY_MODEL_PATH,
    WINDOW_WEEKS,
    ensure_output_dir,
)


ML_GRIDS = {
    "ridge": [{"alpha": 0.1}, {"alpha": 1.0}, {"alpha": 10.0}],
    "ridge_log1p": [{"alpha": 0.1}, {"alpha": 1.0}, {"alpha": 10.0}],
    "random_forest": [
        {"n_estimators": 300, "max_depth": 4, "min_samples_leaf": 3},
        {"n_estimators": 500, "max_depth": None, "min_samples_leaf": 4},
    ],
    "random_forest_log1p": [
        {"n_estimators": 300, "max_depth": 4, "min_samples_leaf": 3},
        {"n_estimators": 500, "max_depth": None, "min_samples_leaf": 4},
    ],
    "hist_gradient": [
        {"learning_rate": 0.05, "max_leaf_nodes": 7, "l2_regularization": 1.0},
        {"learning_rate": 0.10, "max_leaf_nodes": 5, "l2_regularization": 2.0},
    ],
    "hist_gradient_log1p": [
        {"learning_rate": 0.05, "max_leaf_nodes": 7, "l2_regularization": 1.0},
        {"learning_rate": 0.10, "max_leaf_nodes": 5, "l2_regularization": 2.0},
    ],
    "hurdle_hist_gradient": [
        {"learning_rate": 0.05, "max_leaf_nodes": 7, "l2_regularization": 1.0},
        {"learning_rate": 0.10, "max_leaf_nodes": 5, "l2_regularization": 2.0},
    ],
}
STATISTICAL_MODELS = ("arima", "ets", "croston_sba", "tsb")


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


def reject_synthetic_targets(frame: pd.DataFrame) -> None:
    """Impide que valores sintéticos se usen como evidencia de desempeño.

    La extensión sintética de cobertura se guarda en un archivo independiente
    para pruebas técnicas o análisis de sensibilidad. Si una tabla con esa
    procedencia llega por error al conjunto de modelado, la ejecución se
    detiene antes de entrenar, seleccionar hiperparámetros o contrastar H1/H2.
    """
    if "es_sintetico" in frame.columns:
        flagged = pd.to_numeric(frame["es_sintetico"], errors="coerce").fillna(0).ne(0)
        if flagged.any():
            raise ValueError(
                "El dataset de modelado contiene filas sintéticas. Exclúyelas: "
                "los datos sintéticos no pueden utilizarse en ajuste, evaluación ni H1/H2."
            )
    if "origen_objetivo" in frame.columns:
        synthetic = frame["origen_objetivo"].astype(str).str.strip().str.lower().eq("sintetico")
        if synthetic.any():
            raise ValueError(
                "El dataset de modelado declara objetivos sintéticos. Usa exclusivamente "
                "semanas observadas para resultados inferenciales."
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


def iter_rolling_windows(row_count: int, horizon: int = HORIZON_WEEKS) -> list[int]:
    """Devuelve índices donde inicia el bloque de prueba de rolling-window."""
    # h=4 requiere 52 pares completos origen-objetivo para el ajuste directo.
    first = WINDOW_WEEKS + horizon - 1
    last = row_count - horizon
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
    """Ajusta modelos directos, logarítmicos o hurdle sin valores negativos.

    Las variantes ``*_log1p`` comprimen picos y revierten la transformación al
    pronosticar. ``hurdle_hist_gradient`` estima primero la probabilidad de
    compra y después el importe positivo; su salida es el valor esperado
    ``P(compra) × E(importe | compra)``.
    """
    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import Ridge

    x_train, x_test, y_train = prepare_xy(train, test, features)
    if name == "hurdle_hist_gradient":
        occurrence = (y_train > 0).astype(int)
        if occurrence.sum() == 0:
            return np.zeros(len(x_test))
        if occurrence.sum() == len(occurrence):
            probability = np.ones(len(x_test))
        else:
            classifier = HistGradientBoostingClassifier(random_state=RANDOM_STATE, **params)
            classifier.fit(x_train, occurrence)
            probability = classifier.predict_proba(x_test)[:, 1]
        positive_mask = occurrence.astype(bool)
        if positive_mask.sum() < 2:
            return np.maximum(probability * float(y_train[positive_mask].mean()), 0)
        amount_model = HistGradientBoostingRegressor(random_state=RANDOM_STATE, **params)
        amount_model.fit(x_train.loc[positive_mask], np.log1p(y_train[positive_mask]))
        positive_amount = np.maximum(np.expm1(amount_model.predict(x_test)), 0)
        return np.maximum(probability * positive_amount, 0)

    logarithmic = name.endswith("_log1p")
    base_name = name.removesuffix("_log1p")
    if base_name == "ridge":
        model = Ridge(**params)
    elif base_name == "random_forest":
        model = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1, **params)
    elif base_name == "hist_gradient":
        model = HistGradientBoostingRegressor(random_state=RANDOM_STATE, **params)
    else:
        raise ValueError(f"Modelo ML no soportado: {name}")
    model.fit(x_train, np.log1p(y_train) if logarithmic else y_train)
    prediction = model.predict(x_test)
    if logarithmic:
        # Ridge puede extrapolar linealmente en escala logarítmica. Se acota la
        # inversa al mayor importe observado dentro de la ventana de ajuste,
        # evitando montos implausibles que invalidarían la comparación.
        prediction = np.clip(prediction, 0, np.log1p(np.max(y_train)))
        return np.maximum(np.expm1(prediction), 0)
    return np.maximum(prediction, 0)


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

    if name == "tsb":
        nonzero = y[y > 0]
        if not len(nonzero):
            return np.zeros(steps)
        alpha, beta = 0.1, 0.1
        probability = float(y[0] > 0)
        amount = float(nonzero[0])
        for value in y[1:]:
            occurred = float(value > 0)
            probability += beta * (occurred - probability)
            if occurred:
                amount += alpha * (value - amount)
        return np.repeat(max(probability * amount, 0), steps)

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


def direct_ml_samples(frame: pd.DataFrame, origin: int, horizon: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye muestras directas sin filtrar compras futuras.

    Para estimar ``h`` semanas adelante, los predictores históricos proceden
    del origen del pronóstico y las exógenas del periodo objetivo (calendario o
    último valor publicado). Durante el ajuste, cada fila se alinea con su
    objetivo situado ``h-1`` semanas después. Así, una característica histórica
    de una semana intermedia nunca revela una compra aún desconocida.
    """
    historical = [c for c in frame.columns if c.startswith("hist_")]
    exogenous = [c for c in frame.columns if c.startswith("exog_")]
    start = origin - WINDOW_WEEKS - horizon + 1
    contexts = np.arange(start, origin - horizon + 1)
    targets = contexts + horizon - 1
    if len(contexts) != WINDOW_WEEKS or contexts.min() < 0:
        raise ValueError("No hay historia suficiente para construir la muestra directa.")

    train = pd.DataFrame(index=range(len(contexts)))
    train[historical] = frame.iloc[contexts][historical].reset_index(drop=True)
    train[exogenous] = frame.iloc[targets][exogenous].reset_index(drop=True)
    train[TARGET_COLUMN] = frame.iloc[targets][TARGET_COLUMN].to_numpy(dtype=float)

    target_index = origin + horizon - 1
    if target_index >= len(frame):
        raise ValueError("El horizonte directo rebasa la cobertura disponible.")
    test = pd.DataFrame(index=[0])
    test[historical] = frame.iloc[[origin]][historical].reset_index(drop=True)
    test[exogenous] = frame.iloc[[target_index]][exogenous].reset_index(drop=True)
    return train, test


def tune_parameters(
    frame: pd.DataFrame, origins: Iterable[int], model: str, feature_set: str, horizon: int
) -> dict:
    """Elige hiperparámetros con ventanas anteriores a la evaluación final."""
    candidates = candidate_parameters(model)
    scores: list[tuple[float, dict]] = []
    for params in candidates:
        losses = []
        for origin in origins:
            train = frame.iloc[origin - WINDOW_WEEKS : origin]
            if model in STATISTICAL_MODELS:
                prediction = forecast_statistical(model, train, horizon)[-1:]
                actual = float(frame.iloc[origin + horizon - 1][TARGET_COLUMN])
            else:
                direct_train, direct_test = direct_ml_samples(frame, origin, horizon)
                features = select_features(direct_train, feature_set == "historico_exogeno")
                prediction = forecast_ml(model, params, direct_train, direct_test, features)
                actual = float(frame.iloc[origin + horizon - 1][TARGET_COLUMN])
            losses.append(float((actual - prediction[0]) ** 2))
        scores.append((float(np.mean(losses)), params))
    return min(scores, key=lambda item: item[0])[1]


def evaluate_windows(
    frame: pd.DataFrame, origins: Iterable[int], model: str, feature_set: str, params: dict, horizon: int
) -> list[dict]:
    """Genera una fila por predicción; es la evidencia auditable de H1 y H2."""
    rows: list[dict] = []
    for origin in origins:
        train = frame.iloc[origin - WINDOW_WEEKS : origin]
        if model in BASELINE_NAMES:
            prediction = empirical_forecasts(train, horizon)[model][-1:]
            features = []
        elif model in STATISTICAL_MODELS:
            prediction = forecast_statistical(model, train, horizon)[-1:]
            features = []
        else:
            direct_train, direct_test = direct_ml_samples(frame, origin, horizon)
            features = select_features(direct_train, feature_set == "historico_exogeno")
            prediction = forecast_ml(model, params, direct_train, direct_test, features)
        mase_scale, rmsse_scale = scales_from_training(train)
        observed = frame.iloc[origin + horizon - 1]
        actual = float(observed[TARGET_COLUMN])
        error = actual - float(prediction[0])
        rows.append(
            {
                "semana_origen": frame.iloc[origin][DATE_COLUMN],
                "semana_prueba": observed[DATE_COLUMN],
                "horizonte_semanas": horizon,
                "modelo": model,
                "feature_set": feature_set,
                "hiperparametros": json.dumps(params, ensure_ascii=False, sort_keys=True),
                "variables_seleccionadas": "; ".join(features),
                "real": actual,
                "prediccion": float(prediction[0]),
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
    for keys, group in predictions.groupby(["horizonte_semanas", "modelo", "feature_set", "hiperparametros"], dropna=False):
        real = group["real"].to_numpy(dtype=float)
        absolute = group["error_absoluto"].to_numpy(dtype=float)
        squared = group["error_cuadrado"].to_numpy(dtype=float)
        nonzero = np.abs(real) > 1e-8
        mase = absolute / group["escala_mase"].replace(0, np.nan).to_numpy(dtype=float)
        rmsse_terms = squared / group["escala_rmsse"].replace(0, np.nan).to_numpy(dtype=float)
        rows.append(
            {
                "horizonte_semanas": keys[0],
                "modelo": keys[1],
                "feature_set": keys[2],
                "hiperparametros": keys[3],
                "semanas_evaluadas": len(group),
                "mae": float(np.mean(absolute)),
                "rmse": float(np.sqrt(np.mean(squared))),
                "mase": float(np.nanmean(mase)),
                "rmsse": float(np.sqrt(np.nanmean(rmsse_terms))),
                "mape_diagnostico": float(np.mean(absolute[nonzero] / np.abs(real[nonzero])) * 100) if nonzero.any() else math.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["rmse", "mae"]).reset_index(drop=True)


def newey_west_long_run_variance(values: np.ndarray, max_lag: int) -> float:
    """Estima la varianza de largo plazo con ponderación Bartlett."""
    centered = values - np.mean(values)
    variance = float(np.mean(centered**2))
    for lag in range(1, min(max_lag, len(values) - 1) + 1):
        covariance = float(np.mean(centered[lag:] * centered[:-lag]))
        variance += 2 * (1 - lag / (max_lag + 1)) * covariance
    return max(variance, 0.0)


def diebold_mariano_test(left: pd.DataFrame, right: pd.DataFrame, hypothesis: str, horizon: int = HORIZON_WEEKS) -> dict:
    """Contrasta unilateralmente si ``right`` reduce el error de ``left``."""
    joined = left.merge(right, on="semana_prueba", suffixes=("_left", "_right")).sort_values("semana_prueba")
    difference = (joined["error_cuadrado_left"] - joined["error_cuadrado_right"]).to_numpy(dtype=float)
    n = len(difference)
    mean = float(np.mean(difference)) if n else math.nan
    lrv = newey_west_long_run_variance(difference, max(horizon - 1, 0)) if n > 1 else math.nan
    raw_statistic = mean / math.sqrt(lrv / n) if n > 1 and lrv > 0 else math.nan
    correction_term = (n + 1 - 2 * horizon + horizon * (horizon - 1) / n) / n if n else math.nan
    correction = math.sqrt(correction_term) if correction_term > 0 else math.nan
    statistic = raw_statistic * correction if not math.isnan(raw_statistic) and not math.isnan(correction) else math.nan
    try:
        from scipy.stats import t as t_distribution
        pvalue = float(t_distribution.sf(statistic, df=n - 1)) if n > 1 and not math.isnan(statistic) else math.nan
    except ImportError:
        pvalue = math.nan
    return {
        "hipotesis": hypothesis, "semanas": n, "diferencia_media_error_cuadrado": mean,
        "estadistico_dm": statistic, "varianza_largo_plazo": lrv, "rezagos_hac": max(horizon - 1, 0),
        "p_unilateral": pvalue,
    }


def holm_adjust(pvalues: pd.Series) -> pd.Series:
    """Aplica Holm-Bonferroni y conserva el orden original de las pruebas."""
    adjusted = pd.Series(np.nan, index=pvalues.index, dtype=float)
    valid = pvalues.dropna().sort_values()
    running_max = 0.0
    total = len(valid)
    for rank, (index, value) in enumerate(valid.items()):
        candidate = min(1.0, float(value) * (total - rank))
        running_max = max(running_max, candidate)
        adjusted.loc[index] = running_max
    return adjusted


def hypothesis_tables(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye resultados reproducibles de H1 y H2."""
    h1_rows = []
    for horizon in (HORIZON_WEEKS, SECONDARY_HORIZON_WEEKS):
        scoped = predictions.loc[predictions["horizonte_semanas"].eq(horizon)]
        baseline = scoped.loc[scoped["modelo"].eq(PRIMARY_BASELINE)]
        candidates = scoped.loc[~scoped["modelo"].isin(BASELINE_NAMES)]
        for (model, feature_set, hyperparameters), candidate in candidates.groupby(
            ["modelo", "feature_set", "hiperparametros"], dropna=False
        ):
            if not candidate.empty:
                result = diebold_mariano_test(
                    baseline, candidate, f"H{horizon}:{model} ({feature_set}) vs {PRIMARY_BASELINE}", horizon
                )
                result["horizonte_semanas"] = horizon
                result["modelo"] = model
                result["feature_set"] = feature_set
                result["hiperparametros"] = hyperparameters
                h1_rows.append(result)
    h2_rows = []
    for horizon in (HORIZON_WEEKS, SECONDARY_HORIZON_WEEKS):
        scoped = predictions.loc[predictions["horizonte_semanas"].eq(horizon)]
        for model in ML_GRIDS:
            historical = scoped.loc[(scoped["modelo"] == model) & (scoped["feature_set"] == "historico")]
            enriched = scoped.loc[(scoped["modelo"] == model) & (scoped["feature_set"] == "historico_exogeno")]
            if not historical.empty and not enriched.empty:
                result = diebold_mariano_test(historical, enriched, f"H2 h={horizon}:{model} histórico vs enriquecido", horizon)
                result["horizonte_semanas"] = horizon
                h2_rows.append(result)
    h1 = pd.DataFrame(h1_rows)
    if not h1.empty:
        h1["p_holm"] = holm_adjust(h1["p_unilateral"])
        h1["significativo_holm_0_05"] = h1["p_holm"].le(SIGNIFICANCE_LEVEL)
        h1["criterio_h1"] = "DM unilateral con corrección Harvey-Leybourne-Newbold y ajuste Holm"
    h2 = pd.DataFrame(h2_rows)
    if not h2.empty:
        h2["criterio_h2"] = "DM unilateral con corrección Harvey-Leybourne-Newbold; exploratorio sin ajuste múltiple"
    return h1, h2


def monthly_consolidation(predictions: pd.DataFrame) -> pd.DataFrame:
    """Suma pronósticos directos h=1..h=4 por origen y configuración.

    La salida es un presupuesto de cuatro semanas consecutivas, no un modelo
    mensual independiente. Sólo se construye cuando los cuatro horizontes
    requeridos fueron generados con la misma información disponible en origen.
    """
    horizons = set(MONTHLY_CONSOLIDATION_HORIZONS)
    scoped = predictions.loc[predictions["horizonte_semanas"].isin(horizons)].copy()
    keys = ["semana_origen", "modelo", "feature_set"]
    rows = []
    for values, group in scoped.groupby(keys, dropna=False):
        if set(group["horizonte_semanas"]) != horizons:
            continue
        rows.append(
            {
                **dict(zip(keys, values)),
                "hiperparametros_por_horizonte": json.dumps(
                    dict(zip(group["horizonte_semanas"].astype(str), group["hiperparametros"])),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "horizontes_sumados": "h=1+h=2+h=3+h=4",
                "importe_real_4_semanas": float(group["real"].sum()),
                "importe_pronosticado_4_semanas": float(group["prediccion"].sum()),
                "error_absoluto_4_semanas": float(abs(group["real"].sum() - group["prediccion"].sum())),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Ejecuta el experimento semanal y exporta predicciones, métricas e hipótesis."""
    validate_optional_dependencies()
    frame = pd.read_excel(WEEKLY_MODEL_PATH, sheet_name="modelo_semanal")
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN])
    reject_synthetic_targets(frame)
    frame, tail = trim_unobserved_tail(frame)
    # Se usan orígenes comunes compatibles con h=4. Así la consolidación
    # mensual compara exactamente las mismas decisiones de pronóstico entre
    # h=1, h=2, h=3 y h=4.
    origins = iter_rolling_windows(len(frame), SECONDARY_HORIZON_WEEKS)
    tuning_origins, evaluation_origins = split_tuning_evaluation(origins)

    rows: list[dict] = []
    for horizon in MONTHLY_CONSOLIDATION_HORIZONS:
        configurations: list[tuple[str, str, dict]] = []
        for baseline in BASELINE_NAMES:
            configurations.append((baseline, "referencia", {}))
        for model in STATISTICAL_MODELS:
            configurations.append((model, "univariado", {}))
        for model in ML_GRIDS:
            for feature_set in ("historico", "historico_exogeno"):
                configurations.append(
                    (model, feature_set, tune_parameters(frame, tuning_origins, model, feature_set, horizon))
                )
        for model, feature_set, params in configurations:
            rows.extend(evaluate_windows(frame, evaluation_origins, model, feature_set, params, horizon))
    predictions = pd.DataFrame(rows)
    summary = summarize_predictions(predictions)
    h1, h2 = hypothesis_tables(predictions)
    monthly = monthly_consolidation(predictions)
    coverage = pd.DataFrame(
        {
            "metrica": ["semanas_disponibles", "semanas_cola_excluidas", "ventana_entrenamiento", "semanas_evaluacion", "baseline_primaria", "horizonte_principal", "horizonte_secundario", "consolidado"],
            "valor": [len(frame), tail, WINDOW_WEEKS, len(evaluation_origins), PRIMARY_BASELINE, HORIZON_WEEKS, SECONDARY_HORIZON_WEEKS, "h=1+h=2+h=3+h=4"],
        }
    )
    output = ensure_output_dir() / "02_modelos_rolling_window.xlsx"
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        predictions.to_excel(writer, sheet_name="predicciones", index=False)
        summary.to_excel(writer, sheet_name="metricas", index=False)
        h1.to_excel(writer, sheet_name="contraste_h1", index=False)
        h2.to_excel(writer, sheet_name="contraste_h2", index=False)
        monthly.to_excel(writer, sheet_name="consolidado_4_semanas", index=False)
        coverage.to_excel(writer, sheet_name="cobertura", index=False)
    print(f"Archivo generado: {output}")


if __name__ == "__main__":
    main()
