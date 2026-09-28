"""Comparación aislada de Prophet y LSTM contra una corrida híbrida existente.

Este módulo no modifica el pipeline científico ni sus artefactos. Consume el
panel, las particiones y las predicciones de una corrida terminada, reproduce
sus mismos orígenes de evaluación y escribe resultados en otro directorio.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExperimentalConfig:
    training_window_weeks: int = 52
    lstm_lookback_weeks: int = 8
    lstm_units: int = 4
    lstm_epochs: int = 80
    lstm_patience: int = 10
    lstm_min_sequences: int = 24
    seed: int = 42
    prophet_n_changepoints: int = 5
    prophet_changepoint_prior_scale: float = 0.01


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(baseline_dir: Path):
    required = ["panel_semanal.csv", "particiones.csv", "predicciones.csv", "manifiesto.json"]
    missing = [name for name in required if not (baseline_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"La corrida base no contiene: {missing}")
    panel = pd.read_csv(baseline_dir / "panel_semanal.csv", parse_dates=["semana_inicio"])
    panel = panel.set_index("semana_inicio").sort_index()
    partitions = pd.read_csv(
        baseline_dir / "particiones.csv", parse_dates=["origen", "fecha_objetivo"]
    )
    baseline = pd.read_csv(
        baseline_dir / "predicciones.csv", parse_dates=["origen", "fecha_objetivo"]
    )
    manifest = json.loads((baseline_dir / "manifiesto.json").read_text(encoding="utf-8"))
    return panel, partitions, baseline, manifest


def evaluation_grid(partitions: pd.DataFrame) -> pd.DataFrame:
    grid = partitions.loc[
        partitions.etapa.eq("evaluacion") & partitions.objetivo_observado.astype(bool),
        ["origen", "fecha_objetivo", "horizonte"],
    ].drop_duplicates()
    if grid.empty:
        raise ValueError("La corrida base no contiene objetivos observados de evaluación.")
    return grid.sort_values(["origen", "horizonte"]).reset_index(drop=True)


def prophet_prediction(history: pd.Series, target_date: pd.Timestamp, cfg: ExperimentalConfig) -> float:
    from prophet import Prophet

    observed = history.dropna()
    if len(observed) < cfg.lstm_min_sequences:
        raise ValueError(f"Prophet: solo {len(observed)} observaciones disponibles.")
    frame = pd.DataFrame({"ds": observed.index, "y": observed.to_numpy(dtype=float)})
    model = Prophet(
        growth="linear",
        daily_seasonality=False,
        weekly_seasonality=False,
        yearly_seasonality=False,
        n_changepoints=min(cfg.prophet_n_changepoints, max(0, len(frame) - 2)),
        changepoint_prior_scale=cfg.prophet_changepoint_prior_scale,
        seasonality_mode="additive",
        uncertainty_samples=0,
    )
    model.fit(frame)
    forecast = model.predict(pd.DataFrame({"ds": [target_date]}))
    value = float(forecast.yhat.iloc[0])
    if not np.isfinite(value):
        raise ValueError("Prophet produjo un pronóstico no finito.")
    return max(0.0, value)


def _lstm_sequences(
    series: pd.Series,
    origin_position: int,
    horizon: int,
    cfg: ExperimentalConfig,
):
    lookback = cfg.lstm_lookback_weeks
    first_target = max(0, origin_position - cfg.training_window_weeks)
    history = series.iloc[:origin_position]
    observed = history.dropna()
    if observed.empty:
        raise ValueError("LSTM sin historia observada.")
    log_observed = np.log1p(observed.to_numpy(dtype=float))
    center = float(log_observed.mean())
    scale = float(log_observed.std()) or 1.0

    def encode(start: int, stop: int) -> np.ndarray:
        block = series.iloc[start:stop]
        missing = block.isna().to_numpy(dtype=float)
        log_total = np.log1p(block.fillna(0).to_numpy(dtype=float))
        normalized = np.where(missing.astype(bool), 0.0, (log_total - center) / scale)
        weeks = block.index.isocalendar().week.to_numpy(dtype=float)
        return np.column_stack(
            [normalized, missing, np.sin(2 * np.pi * weeks / 52.1775), np.cos(2 * np.pi * weeks / 52.1775)]
        ).astype("float32")

    xs, ys = [], []
    for target in range(first_target, origin_position):
        sample_origin = target - horizon + 1
        if sample_origin - lookback < 0 or pd.isna(series.iloc[target]):
            continue
        xs.append(encode(sample_origin - lookback, sample_origin))
        ys.append((np.log1p(float(series.iloc[target])) - center) / scale)
    if len(xs) < cfg.lstm_min_sequences:
        raise ValueError(f"LSTM: solo {len(xs)} secuencias; mínimo {cfg.lstm_min_sequences}.")
    test = encode(origin_position - lookback, origin_position)[None, :, :]
    return np.asarray(xs, dtype="float32"), np.asarray(ys, dtype="float32"), test, center, scale


def lstm_prediction(
    series: pd.Series,
    origin_position: int,
    horizon: int,
    cfg: ExperimentalConfig,
) -> tuple[float, int, int]:
    import tensorflow as tf

    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    tf.keras.utils.set_random_seed(cfg.seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass
    x_train, y_train, x_test, center, scale = _lstm_sequences(
        series, origin_position, horizon, cfg
    )
    tf.keras.backend.clear_session()
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(cfg.lstm_lookback_weeks, x_train.shape[2])),
            tf.keras.layers.LSTM(
                cfg.lstm_units,
                activation="tanh",
                recurrent_activation="sigmoid",
                kernel_regularizer=tf.keras.regularizers.l2(0.01),
                recurrent_regularizer=tf.keras.regularizers.l2(0.01),
            ),
            tf.keras.layers.Dense(1),
        ]
    )
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.005), loss="mse")
    callback = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=cfg.lstm_patience, restore_best_weights=True
    )
    history = model.fit(
        x_train,
        y_train,
        validation_split=0.2,
        epochs=cfg.lstm_epochs,
        batch_size=8,
        shuffle=False,
        callbacks=[callback],
        verbose=0,
    )
    scaled = float(model.predict(x_test, verbose=0).ravel()[0])
    value = float(np.expm1(scaled * scale + center))
    if not np.isfinite(value):
        raise ValueError("LSTM produjo un pronóstico no finito.")
    best_epoch = int(np.argmin(history.history["val_loss"]) + 1)
    return max(0.0, value), len(x_train), best_epoch


def metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (horizon, model), group in predictions.groupby(["horizonte", "modelo"]):
        error = group.real.to_numpy(float) - group.prediccion.to_numpy(float)
        rows.append(
            {
                "horizonte": int(horizon),
                "modelo": model,
                "n": len(group),
                "rmse": float(np.sqrt(np.mean(error**2))),
                "mae": float(np.mean(np.abs(error))),
                "sesgo": float(np.mean(-error)),
            }
        )
    for model, group in predictions.groupby("modelo"):
        error = group.real.to_numpy(float) - group.prediccion.to_numpy(float)
        rows.append(
            {
                "horizonte": "todos",
                "modelo": model,
                "n": len(group),
                "rmse": float(np.sqrt(np.mean(error**2))),
                "mae": float(np.mean(np.abs(error))),
                "sesgo": float(np.mean(-error)),
            }
        )
    return pd.DataFrame(rows)


def robustness(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separar objetivos positivos y contar victorias sin ocultar los ceros."""
    positive_rows = []
    positive = predictions.loc[predictions.real.gt(0)]
    for model, group in positive.groupby("modelo"):
        error = group.real.to_numpy(float) - group.prediccion.to_numpy(float)
        positive_rows.append(
            {
                "modelo": model,
                "n_objetivos_positivos": len(group),
                "rmse_objetivos_positivos": float(np.sqrt(np.mean(error**2))),
                "mae_objetivos_positivos": float(np.mean(np.abs(error))),
                "sesgo_objetivos_positivos": float(np.mean(-error)),
                "predicciones_truncadas_en_cero": int(group.prediccion.eq(0).sum()),
            }
        )
    wide = predictions.pivot_table(
        index=["origen", "fecha_objetivo", "horizonte", "real"],
        columns="modelo",
        values="prediccion",
    ).reset_index()
    model_names = ["hibrido_base", "prophet", "lstm"]
    errors = pd.DataFrame({name: (wide[name] - wide.real).abs() for name in model_names})
    winners = errors.idxmin(axis=1)
    win_rows = []
    for name in model_names:
        win_rows.append(
            {
                "modelo": name,
                "victorias_error_absoluto": int(winners.eq(name).sum()),
                "casos_comparados": len(wide),
                "predicciones_exactamente_cero": int(wide[name].eq(0).sum()),
            }
        )
    return pd.DataFrame(positive_rows), pd.DataFrame(win_rows)


def run(baseline_dir: Path, output_dir: Path, cfg: ExperimentalConfig) -> Path:
    panel, partitions, baseline, baseline_manifest = load_inputs(baseline_dir)
    grid = evaluation_grid(partitions)
    output_dir.mkdir(parents=True, exist_ok=False)
    experimental_rows, failures = [], []
    for row in grid.itertuples(index=False):
        positions = np.flatnonzero(panel.index == row.origen)
        if len(positions) != 1:
            raise ValueError(f"Origen fuera del panel: {row.origen}")
        origin_position = int(positions[0])
        start = max(0, origin_position - cfg.training_window_weeks)
        history = panel.total.iloc[start:origin_position]
        real = float(panel.at[row.fecha_objetivo, "total"])
        for model_name in ("prophet", "lstm"):
            try:
                if model_name == "prophet":
                    prediction = prophet_prediction(history, row.fecha_objetivo, cfg)
                    n_train = int(history.notna().sum())
                    best_epoch = None
                else:
                    prediction, n_train, best_epoch = lstm_prediction(
                        panel.total, origin_position, int(row.horizonte), cfg
                    )
                experimental_rows.append(
                    {
                        "origen": row.origen,
                        "fecha_objetivo": row.fecha_objetivo,
                        "horizonte": int(row.horizonte),
                        "modelo": model_name,
                        "real": real,
                        "prediccion": prediction,
                        "n_entrenamiento": n_train,
                        "mejor_epoca": best_epoch,
                    }
                )
            except Exception as exc:
                failures.append(
                    {
                        "origen": row.origen,
                        "fecha_objetivo": row.fecha_objetivo,
                        "horizonte": int(row.horizonte),
                        "modelo": model_name,
                        "error": str(exc),
                    }
                )
    experimental = pd.DataFrame(experimental_rows)
    experimental.to_csv(output_dir / "predicciones_experimentales.csv", index=False)
    failure_columns = ["origen", "fecha_objetivo", "horizonte", "modelo", "error"]
    pd.DataFrame(failures, columns=failure_columns).to_csv(
        output_dir / "fallos_experimentales.csv", index=False
    )
    base = baseline.loc[baseline.modelo.eq("hibrido"), [
        "origen", "fecha_objetivo", "horizonte", "modelo", "real", "prediccion"
    ]].copy()
    base["modelo"] = "hibrido_base"
    comparison = pd.concat([base, experimental[base.columns]], ignore_index=True)
    counts = comparison.groupby(["horizonte", "modelo"]).size().unstack(fill_value=0)
    expected_models = {"hibrido_base", "prophet", "lstm"}
    if not expected_models.issubset(counts.columns) or not (counts[list(expected_models)].nunique(axis=1) == 1).all():
        raise ValueError("Los modelos no produjeron las mismas fechas; revisar fallos_experimentales.csv.")
    comparison.to_csv(output_dir / "predicciones_comparables.csv", index=False)
    result_metrics = metrics(comparison)
    result_metrics.to_csv(output_dir / "metricas_comparativas.csv", index=False)
    positive_metrics, wins = robustness(comparison)
    positive_metrics.to_csv(output_dir / "metricas_objetivos_positivos.csv", index=False)
    wins.to_csv(output_dir / "victorias_y_ceros.csv", index=False)

    overall = result_metrics.loc[result_metrics.horizonte.eq("todos")].set_index("modelo")
    base_rmse = float(overall.at["hibrido_base", "rmse"])
    lines = [
        "# Prueba aislada de Prophet y LSTM",
        "",
        f"Corrida base: `{baseline_dir.name}`.",
        f"Predicciones comparables: {int(overall.at['hibrido_base', 'n'])} por modelo.",
        "",
        "| Modelo | RMSE global | MAE global | Cambio RMSE vs. híbrido |",
        "|---|---:|---:|---:|",
    ]
    for model in ["hibrido_base", "prophet", "lstm"]:
        rmse = float(overall.at[model, "rmse"])
        mae = float(overall.at[model, "mae"])
        change = 100 * (rmse - base_rmse) / base_rmse
        lines.append(f"| {model} | {rmse:.3f} | {mae:.3f} | {change:+.2f}% |")
    lines += [
        "",
        f"Objetivos iguales a cero: {int(base.real.eq(0).sum())} de {len(base)}.",
        "",
        "| Modelo | RMSE sólo positivos | MAE sólo positivos | Victorias por error absoluto | Predicciones cero |",
        "|---|---:|---:|---:|---:|",
    ]
    positive_by_model = positive_metrics.set_index("modelo")
    wins_by_model = wins.set_index("modelo")
    for model in ["hibrido_base", "prophet", "lstm"]:
        lines.append(
            f"| {model} | {float(positive_by_model.at[model, 'rmse_objetivos_positivos']):.3f} "
            f"| {float(positive_by_model.at[model, 'mae_objetivos_positivos']):.3f} "
            f"| {int(wins_by_model.at[model, 'victorias_error_absoluto'])} "
            f"| {int(wins_by_model.at[model, 'predicciones_exactamente_cero'])} |"
        )
    lines += [
        "",
        "Resultado exploratorio: el número de orígenes es pequeño; no constituye por sí solo evidencia suficiente para modificar la tesis.",
        "Los modelos experimentales no se incorporaron al híbrido ni a sus artefactos.",
    ]
    (output_dir / "resumen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    versions = {}
    for package in ("prophet", "tensorflow", "numpy", "pandas"):
        versions[package] = importlib.metadata.version(package)
    manifest = {
        "tipo": "experimento_aislado_no_incorporado_a_la_tesis",
        "creado_utc": datetime.now(timezone.utc).isoformat(),
        "corrida_base": str(baseline_dir.resolve()),
        "estado_corrida_base": baseline_manifest.get("estado"),
        "configuracion": asdict(cfg),
        "versiones": versions,
        "entradas": {
            name: sha256(baseline_dir / name)
            for name in ("panel_semanal.csv", "particiones.csv", "predicciones.csv", "manifiesto.json")
        },
    }
    (output_dir / "manifiesto_experimental.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return output_dir


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or Path("output") / f"experimental_prophet_lstm_{stamp}"
    result = run(args.baseline_dir, output, ExperimentalConfig())
    print(f"Resultados experimentales guardados en: {result.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
