from __future__ import annotations

"""
Codigo 06: preparacion y entrenamiento base de RNN/LSTM.

Objetivo:
- Usar ventanas temporales supervisadas para redes recurrentes.
- Comparar RNN simple y LSTM con MAE, RMSE y MAPE.
- Trabajar preferentemente con dataset reducido o PCA para controlar dimensionalidad.

Requisito:
pip install tensorflow scikit-learn

Nota metodologica:
Las redes recurrentes requieren mas cuidado por el tamano del dataset. En una
microempresa, deben compararse contra modelos mas simples para justificar su uso.
"""

import math
import numpy as np
import pandas as pd

from config_metodologia import DATE_COLUMN, TARGET_COLUMNS, ensure_output_dir, load_model_dataset


DATASET_TO_USE = "pca"
LOOKBACK_DAYS = 28
TEST_DAYS = 90
EPOCHS = 80
BATCH_SIZE = 16


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
    xs, ys = [], []
    for i in range(lookback, len(x)):
        xs.append(x[i - lookback : i])
        ys.append(y[i])
    return np.asarray(xs), np.asarray(ys)


def metricas(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    error = y_true - y_pred
    mae = float(np.mean(np.abs(error)))
    rmse = float(math.sqrt(np.mean(error**2)))
    denominator = np.where(np.abs(y_true) < 1e-8, np.nan, np.abs(y_true))
    mape = float(np.nanmean(np.abs(error) / denominator) * 100)
    return {"mae": mae, "rmse": rmse, "mape": mape}


def main() -> None:
    try:
        from sklearn.preprocessing import StandardScaler
        from tensorflow.keras.callbacks import EarlyStopping
        from tensorflow.keras.layers import Dense, LSTM, SimpleRNN
        from tensorflow.keras.models import Sequential
    except ImportError as exc:
        raise SystemExit(
            "Faltan dependencias para RNN/LSTM. Instala: pip install tensorflow scikit-learn"
        ) from exc

    out_dir = ensure_output_dir()
    df = load_dataset_variant()
    predictors = [column for column in df.columns if column not in TARGET_COLUMNS + [DATE_COLUMN]]
    train = df.iloc[:-TEST_DAYS].copy()
    test_context = df.iloc[-(TEST_DAYS + LOOKBACK_DAYS) :].copy()

    rows = []
    for target in TARGET_COLUMNS:
        scaler_x = StandardScaler()
        scaler_y = StandardScaler()

        x_train_raw = train[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
        y_train_raw = train[[target]].fillna(0)
        x_test_raw = test_context[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
        y_test_raw = test_context[[target]].fillna(0)

        x_train_scaled = scaler_x.fit_transform(x_train_raw)
        y_train_scaled = scaler_y.fit_transform(y_train_raw).ravel()
        x_test_scaled = scaler_x.transform(x_test_raw)
        y_test_scaled = scaler_y.transform(y_test_raw).ravel()

        x_train, y_train = make_sequences(x_train_scaled, y_train_scaled, LOOKBACK_DAYS)
        x_test, _ = make_sequences(x_test_scaled, y_test_scaled, LOOKBACK_DAYS)
        y_true = y_test_raw.iloc[LOOKBACK_DAYS:].to_numpy().ravel()

        model_specs = {
            "rnn_simple": SimpleRNN,
            "lstm": LSTM,
        }

        for model_name, recurrent_layer in model_specs.items():
            model = Sequential(
                [
                    recurrent_layer(32, input_shape=(x_train.shape[1], x_train.shape[2])),
                    Dense(16, activation="relu"),
                    Dense(1),
                ]
            )
            model.compile(optimizer="adam", loss="mae")
            model.fit(
                x_train,
                y_train,
                epochs=EPOCHS,
                batch_size=BATCH_SIZE,
                validation_split=0.2,
                shuffle=False,
                callbacks=[EarlyStopping(patience=10, restore_best_weights=True)],
                verbose=0,
            )

            pred_scaled = model.predict(x_test, verbose=0)
            y_pred = scaler_y.inverse_transform(pred_scaled).ravel()
            y_pred = np.maximum(y_pred, 0)
            rows.append({"dataset": DATASET_TO_USE, "target": target, "modelo": model_name, **metricas(y_true, y_pred)})

    output_xlsx = out_dir / f"06_rnn_lstm_{DATASET_TO_USE}.xlsx"
    pd.DataFrame(rows).to_excel(output_xlsx, index=False)
    print(f"Archivo generado: {output_xlsx}")


if __name__ == "__main__":
    main()
