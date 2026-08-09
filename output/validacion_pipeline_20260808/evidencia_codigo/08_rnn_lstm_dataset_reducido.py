from __future__ import annotations

"""Ajuste temporal y evaluacion final de RNN/LSTM.

Los hiperparametros se seleccionan en un bloque de validacion situado antes de
los ultimos ``TEST_DAYS``. La prueba final nunca participa en la seleccion.
Despues, la configuracion ganadora se reentrena con todo el historial anterior
a la prueba y se evalua una sola vez sobre ese tramo intacto.
"""

import json
import math
import random
from typing import Any, Mapping

import numpy as np
import pandas as pd

from config_metodologia import (
    DATE_COLUMN,
    TARGET_COLUMNS,
    ensure_output_dir,
    load_model_dataset,
    trim_trailing_inactive_target,
)


DATASET_TO_USE = "pca"
TEST_DAYS = 90
TUNING_VALIDATION_DAYS = 60
EPOCHS = 60
PATIENCE = 8
RANDOM_STATE = 42
ENABLE_HYPERPARAMETER_TUNING = True

# Rejilla compacta para que el experimento sea reproducible y razonable en CPU.
# El pipeline puede sustituirla antes de invocar ``main``.
DEFAULT_PARAM_GRIDS: dict[str, list[dict[str, Any]]] = {
    "rnn_simple": [
        {"lookback": 14, "units": 24, "dense_units": 12, "learning_rate": 1e-3, "batch_size": 16},
        {"lookback": 28, "units": 32, "dense_units": 16, "learning_rate": 1e-3, "batch_size": 16},
    ],
    "lstm": [
        {"lookback": 14, "units": 24, "dense_units": 12, "learning_rate": 1e-3, "batch_size": 16},
        {"lookback": 28, "units": 32, "dense_units": 16, "learning_rate": 1e-3, "batch_size": 16},
    ],
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


def make_sequences(x: np.ndarray, y: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
    if len(x) <= lookback:
        raise ValueError(f"Se requieren mas de {lookback} filas para construir secuencias.")
    xs, ys = [], []
    for i in range(lookback, len(x)):
        xs.append(x[i - lookback : i])
        ys.append(y[i])
    return np.asarray(xs), np.asarray(ys)


def metricas(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float).ravel()
    y_pred = np.asarray(y_pred, dtype=float).ravel()
    error = y_true - y_pred
    valid = np.abs(y_true) >= 1e-8
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(math.sqrt(np.mean(error**2))),
        "mape": float(np.mean(np.abs(error[valid]) / np.abs(y_true[valid])) * 100) if valid.any() else math.nan,
    }


def _json_params(params: Mapping[str, Any]) -> str:
    return json.dumps(dict(params), ensure_ascii=False, sort_keys=True)


def _set_seed(tf_module: Any) -> None:
    random.seed(RANDOM_STATE)
    np.random.seed(RANDOM_STATE)
    tf_module.keras.utils.set_random_seed(RANDOM_STATE)
    try:
        tf_module.config.experimental.enable_op_determinism()
    except Exception:
        pass


def _build_model(model_name: str, params: Mapping[str, Any], n_features: int, keras: Any):
    layers = keras.layers
    recurrent = layers.SimpleRNN if model_name == "rnn_simple" else layers.LSTM
    model = keras.Sequential(
        [
            layers.Input(shape=(int(params["lookback"]), n_features)),
            recurrent(int(params["units"])),
            layers.Dense(int(params["dense_units"]), activation="relu"),
            layers.Dense(1),
        ]
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=float(params["learning_rate"])),
        loss="mae",
    )
    return model


def main() -> None:
    try:
        from sklearn.preprocessing import StandardScaler
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError(
            "Faltan dependencias para RNN/LSTM. Instala tensorflow y scikit-learn."
        ) from exc

    _set_seed(tf)
    out_dir = ensure_output_dir()
    df = load_dataset_variant()
    predictors = [
        column for column in df.columns
        if column not in TARGET_COLUMNS + [DATE_COLUMN]
        and pd.api.types.is_numeric_dtype(df[column])
    ]
    max_lookback = max(int(p["lookback"]) for grid in DEFAULT_PARAM_GRIDS.values() for p in grid)

    result_rows: list[dict[str, Any]] = []
    best_rows: list[dict[str, Any]] = []
    tuning_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []

    for target in TARGET_COLUMNS:
        target_df, excluded_trailing_days = trim_trailing_inactive_target(df, target, TEST_DAYS)
        test_start = len(target_df) - TEST_DAYS
        validation_start = test_start - TUNING_VALIDATION_DAYS
        if validation_start <= max_lookback:
            raise ValueError(
                f"No hay historial suficiente para ajuste temporal y prueba final de '{target}'."
            )
        candidates_by_model: dict[str, list[dict[str, Any]]] = {}
        for model_name, grid in DEFAULT_PARAM_GRIDS.items():
            candidates_by_model[model_name] = grid if ENABLE_HYPERPARAMETER_TUNING else grid[:1]

        selected: dict[str, tuple[dict[str, Any], int, dict[str, float]]] = {}
        for model_name, candidates in candidates_by_model.items():
            for candidate_number, params in enumerate(candidates, start=1):
                lookback = int(params["lookback"])
                scaler_x = StandardScaler()
                scaler_y = StandardScaler()
                fit = target_df.iloc[:validation_start]
                validation_context = target_df.iloc[validation_start - lookback : test_start]

                x_fit = scaler_x.fit_transform(
                    fit[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
                )
                y_fit = scaler_y.fit_transform(fit[[target]].fillna(0)).ravel()
                x_val_context = scaler_x.transform(
                    validation_context[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
                )
                y_val_context = scaler_y.transform(validation_context[[target]].fillna(0)).ravel()
                x_train, y_train = make_sequences(x_fit, y_fit, lookback)
                x_val, _ = make_sequences(x_val_context, y_val_context, lookback)
                y_val_true = validation_context[target].iloc[lookback:].fillna(0).to_numpy(dtype=float)

                tf.keras.backend.clear_session()
                _set_seed(tf)
                model = _build_model(model_name, params, len(predictors), tf.keras)
                early_stopping = tf.keras.callbacks.EarlyStopping(
                    monitor="val_loss", patience=PATIENCE, restore_best_weights=True
                )
                history = model.fit(
                    x_train,
                    y_train,
                    validation_data=(x_val, y_val_context[lookback:]),
                    epochs=EPOCHS,
                    batch_size=int(params["batch_size"]),
                    shuffle=False,
                    callbacks=[early_stopping],
                    verbose=0,
                )
                pred_val = scaler_y.inverse_transform(model.predict(x_val, verbose=0)).ravel()
                val_metrics = metricas(y_val_true, np.maximum(pred_val, 0))
                best_epoch = int(np.argmin(history.history["val_loss"]) + 1)
                tuning_rows.append(
                    {
                        "dataset": DATASET_TO_USE,
                        "target": target,
                        "modelo": model_name,
                        "candidato": candidate_number,
                        "hiperparametros": _json_params(params),
                        "fecha_inicio_validacion": target_df.iloc[validation_start][DATE_COLUMN].date(),
                        "fecha_fin_validacion": target_df.iloc[test_start - 1][DATE_COLUMN].date(),
                        "fecha_fin_efectiva_objetivo": target_df[DATE_COLUMN].max().date(),
                        "dias_cola_sin_cobertura_excluidos": excluded_trailing_days,
                        "epocas_entrenadas": len(history.history["loss"]),
                        "mejor_epoca": best_epoch,
                        **{f"{key}_validacion": value for key, value in val_metrics.items()},
                    }
                )

            model_candidates = [row for row in tuning_rows if row["target"] == target and row["modelo"] == model_name]
            winner = min(model_candidates, key=lambda row: (row["rmse_validacion"], row["mae_validacion"], row["candidato"]))
            winner["es_mejor"] = True
            selected[model_name] = (
                json.loads(winner["hiperparametros"]),
                int(winner["mejor_epoca"]),
                {"mae": winner["mae_validacion"], "rmse": winner["rmse_validacion"], "mape": winner["mape_validacion"]},
            )

        for model_name, (params, best_epoch, val_metrics) in selected.items():
            lookback = int(params["lookback"])
            development = target_df.iloc[:test_start]
            test_context = target_df.iloc[test_start - lookback :]
            scaler_x = StandardScaler()
            scaler_y = StandardScaler()
            x_development = scaler_x.fit_transform(
                development[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
            )
            y_development = scaler_y.fit_transform(development[[target]].fillna(0)).ravel()
            x_test_context = scaler_x.transform(
                test_context[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
            )
            y_test_context = scaler_y.transform(test_context[[target]].fillna(0)).ravel()
            x_train, y_train = make_sequences(x_development, y_development, lookback)
            x_test, _ = make_sequences(x_test_context, y_test_context, lookback)

            tf.keras.backend.clear_session()
            _set_seed(tf)
            model = _build_model(model_name, params, len(predictors), tf.keras)
            model.fit(
                x_train,
                y_train,
                epochs=max(1, best_epoch),
                batch_size=int(params["batch_size"]),
                shuffle=False,
                verbose=0,
            )
            pred_scaled = model.predict(x_test, verbose=0)
            y_pred = np.maximum(scaler_y.inverse_transform(pred_scaled).ravel(), 0)
            y_true = test_context[target].iloc[lookback:].fillna(0).to_numpy(dtype=float)
            test_metrics = metricas(y_true, y_pred)
            params_text = _json_params(params)
            result_rows.append(
                {
                    "dataset": DATASET_TO_USE,
                    "target": target,
                    "modelo": model_name,
                    "hiperparametros": params_text,
                    "mejor_epoca": best_epoch,
                    "mae_validacion": val_metrics["mae"],
                    "rmse_validacion": val_metrics["rmse"],
                    "mape_validacion": val_metrics["mape"],
                    "fecha_fin_efectiva_objetivo": target_df[DATE_COLUMN].max().date(),
                    "dias_cola_sin_cobertura_excluidos": excluded_trailing_days,
                    **test_metrics,
                }
            )
            best_rows.append(
                {
                    "dataset": DATASET_TO_USE,
                    "target": target,
                    "modelo": model_name,
                    "hiperparametros": params_text,
                    "mejor_epoca": best_epoch,
                    "criterio_seleccion": "menor_rmse_validacion_temporal",
                }
            )
            dates = test_context[DATE_COLUMN].iloc[lookback:].dt.date.to_numpy()
            prediction_rows.extend(
                {
                    "dataset": DATASET_TO_USE,
                    "target": target,
                    "modelo": model_name,
                    "fecha": date,
                    "real": float(real),
                    "prediccion": float(prediction),
                }
                for date, real, prediction in zip(dates, y_true, y_pred)
            )

    tuning = pd.DataFrame(tuning_rows)
    if "es_mejor" not in tuning:
        tuning["es_mejor"] = False
    tuning["es_mejor"] = tuning["es_mejor"].fillna(False).astype(bool)
    results = pd.DataFrame(result_rows)
    overall_best = (
        results.loc[results.groupby(["dataset", "target"])["rmse"].idxmin()]
        .sort_values(["dataset", "target"])
        .reset_index(drop=True)
    )

    output_xlsx = out_dir / f"06_rnn_lstm_{DATASET_TO_USE}.xlsx"
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        results.to_excel(writer, sheet_name="resultados", index=False)
        pd.DataFrame(best_rows).to_excel(writer, sheet_name="mejores_hiperparametros", index=False)
        tuning.to_excel(writer, sheet_name="detalle_ajuste", index=False)
        overall_best.to_excel(writer, sheet_name="mejor_configuracion", index=False)
        pd.DataFrame(prediction_rows).to_excel(writer, sheet_name="predicciones_prueba", index=False)
    print(f"Archivo generado: {output_xlsx}")


if __name__ == "__main__":
    main()
