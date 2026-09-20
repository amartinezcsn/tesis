"""Diagnóstico reproducible de la serie semanal de compras.

Esta etapa separa el análisis temporal descriptivo del experimento predictivo.
La caracterización se calcula sobre semanas observadas; las últimas semanas de
evaluación se excluyen del diagnóstico usado para justificar modelos, con el fin
de no incorporar información del bloque final de prueba.
"""

from __future__ import annotations

import json
import math
import os
import warnings
from pathlib import Path

_MPL_CACHE = Path(__file__).resolve().parents[1] / ".codex-temp" / "matplotlib"
_MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CACHE))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, kpss, pacf

from config_semanal import DATE_COLUMN, FINAL_EVALUATION_WEEKS, WEEKLY_MASTER_PATH, ensure_output_dir, primary_coverage_block


SERIES_COLUMN = "compras_importe_semanal"
ANALYSIS_DIRNAME = "series_temporales"
INTERMITTENCY_ADI_THRESHOLD = 1.32
INTERMITTENCY_CV2_THRESHOLD = 0.49
ROBUST_Z_THRESHOLD = 3.5


def trim_unobserved_tail(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Excluye la cola posterior al último importe positivo observado."""
    values = pd.to_numeric(frame[SERIES_COLUMN], errors="coerce").fillna(0).to_numpy(float)
    active = np.flatnonzero(np.abs(values) > 1e-8)
    if not len(active):
        raise ValueError("La serie semanal no contiene compras positivas observadas.")
    tail = len(frame) - active[-1] - 1
    return frame.iloc[: active[-1] + 1].copy(), int(tail)


def classify_intermittency(values: np.ndarray) -> dict[str, float | str | int]:
    """Calcula ADI, CV² y la clasificación Syntetos-Boylan."""
    values = np.asarray(values, dtype=float)
    positive = values[values > 0]
    if not len(positive):
        return {
            "semanas": len(values), "semanas_positivas": 0, "ceros_pct": 100.0,
            "adi": math.inf, "cv2_importes_positivos": math.nan,
            "clasificacion": "sin demanda positiva",
        }
    adi = float(len(values) / len(positive))
    mean_positive = float(np.mean(positive))
    cv2 = float((np.std(positive, ddof=1) / mean_positive) ** 2) if len(positive) > 1 and mean_positive else math.nan
    if adi < INTERMITTENCY_ADI_THRESHOLD and cv2 < INTERMITTENCY_CV2_THRESHOLD:
        label = "suave"
    elif adi >= INTERMITTENCY_ADI_THRESHOLD and cv2 < INTERMITTENCY_CV2_THRESHOLD:
        label = "intermitente"
    elif adi < INTERMITTENCY_ADI_THRESHOLD and cv2 >= INTERMITTENCY_CV2_THRESHOLD:
        label = "errática"
    else:
        label = "irregular (lumpy)"
    return {
        "semanas": int(len(values)), "semanas_positivas": int(len(positive)),
        "ceros_pct": float(np.mean(values == 0) * 100), "adi": adi,
        "cv2_importes_positivos": cv2, "clasificacion": label,
    }


def robust_outlier_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Marca valores extremos con mediana y MAD sin eliminarlos."""
    result = frame[[DATE_COLUMN, SERIES_COLUMN]].copy()
    values = result[SERIES_COLUMN].to_numpy(float)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    result["z_robusto"] = 0.0 if mad <= 1e-12 else 0.6745 * (values - median) / mad
    result["es_atipico_robusto"] = result["z_robusto"].abs().gt(ROBUST_Z_THRESHOLD)
    return result


def stationarity_tests(values: np.ndarray, transformation: str) -> list[dict]:
    """Aplica ADF y KPSS como pruebas complementarias."""
    rows: list[dict] = []
    series = np.asarray(values, dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            statistic, pvalue, lags, observations, *_ = adfuller(series, autolag="AIC")
            rows.append({
                "transformacion": transformation, "prueba": "ADF",
                "hipotesis_nula": "raíz unitaria / no estacionaria",
                "estadistico": float(statistic), "p_valor": float(pvalue),
                "rezagos": int(lags), "observaciones": int(observations),
                "decision_0_05": "rechazar H0" if pvalue <= 0.05 else "no rechazar H0",
            })
        except (ValueError, np.linalg.LinAlgError) as exc:
            rows.append({"transformacion": transformation, "prueba": "ADF", "error": str(exc)})
        try:
            statistic, pvalue, lags, _ = kpss(series, regression="c", nlags="auto")
            rows.append({
                "transformacion": transformation, "prueba": "KPSS",
                "hipotesis_nula": "estacionaria en nivel",
                "estadistico": float(statistic), "p_valor": float(pvalue),
                "rezagos": int(lags), "observaciones": int(len(series)),
                "decision_0_05": "rechazar H0" if pvalue <= 0.05 else "no rechazar H0",
            })
        except (ValueError, np.linalg.LinAlgError) as exc:
            rows.append({"transformacion": transformation, "prueba": "KPSS", "error": str(exc)})
    return rows


def autocorrelation_table(values: np.ndarray, max_lag: int = 52) -> pd.DataFrame:
    """Calcula ACF y PACF con un límite compatible con la muestra."""
    values = np.asarray(values, dtype=float)
    acf_lag = min(max_lag, len(values) - 2)
    pacf_lag = min(max_lag, max(1, len(values) // 2 - 1))
    acf_values = acf(values, nlags=acf_lag, fft=True)
    pacf_values = pacf(values, nlags=pacf_lag, method="ywmle")
    critical = 1.96 / math.sqrt(len(values))
    return pd.DataFrame([
        {
            "rezago": lag, "acf": float(acf_values[lag]),
            "pacf": float(pacf_values[lag]) if lag <= pacf_lag else math.nan,
            "limite_aprox_95": critical,
            "acf_fuera_limite": bool(abs(acf_values[lag]) > critical) if lag else False,
            "pacf_fuera_limite": bool(abs(pacf_values[lag]) > critical) if lag and lag <= pacf_lag else False,
        }
        for lag in range(acf_lag + 1)
    ])


def stl_components(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float | str]]:
    """Descompone con periodo 52 y reporta su carácter exploratorio."""
    values = frame[SERIES_COLUMN].to_numpy(float)
    if len(values) < 104:
        return pd.DataFrame(), {"periodo": 52, "estado": "no calculado", "motivo": "se requieren al menos dos ciclos anuales"}
    fit = STL(values, period=52, robust=True).fit()
    components = frame[[DATE_COLUMN, SERIES_COLUMN]].copy()
    components["tendencia_stl"] = fit.trend
    components["estacional_stl"] = fit.seasonal
    components["residuo_stl"] = fit.resid
    residual_variance = float(np.var(fit.resid))
    seasonal_strength = max(0.0, 1.0 - residual_variance / max(float(np.var(fit.seasonal + fit.resid)), 1e-12))
    trend_strength = max(0.0, 1.0 - residual_variance / max(float(np.var(fit.trend + fit.resid)), 1e-12))
    cycles = float(len(values) / 52)
    conclusive_strength = cycles >= 3
    return components, {
        "periodo": 52, "estado": "exploratorio no concluyente" if not conclusive_strength else "exploratorio",
        "ciclos_aproximados": cycles,
        "fuerza_estacional": seasonal_strength if conclusive_strength else None,
        "fuerza_tendencia": trend_strength if conclusive_strength else None,
        "advertencia": "La longitud del bloque continuo aporta menos de tres ciclos anuales; la descomposición se conserva sólo como visualización y sus índices de fuerza no se interpretan.",
    }


def build_temporal_tables(frame: pd.DataFrame, development: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Construye tablas auditables para el diagnóstico y las figuras."""
    full = frame[[DATE_COLUMN, SERIES_COLUMN, "semana_anio", "mes"]].copy()
    full["media_movil_4s"] = full[SERIES_COLUMN].rolling(4, min_periods=1).mean()
    full["mediana_movil_13s"] = full[SERIES_COLUMN].rolling(13, min_periods=1).median()
    full["media_movil_26s"] = full[SERIES_COLUMN].rolling(26, min_periods=1).mean()
    full["es_bloque_evaluacion"] = False
    full.loc[full.index[-FINAL_EVALUATION_WEEKS:], "es_bloque_evaluacion"] = True
    aggregation = {"count": "observaciones", "mean": "media", "median": "mediana", "std": "desviacion"}
    seasonal_week = development.groupby("semana_anio")[SERIES_COLUMN].agg(["count", "mean", "median", "std", "min", "max"]).reset_index().rename(columns=aggregation)
    seasonal_month = development.groupby("mes")[SERIES_COLUMN].agg(["count", "mean", "median", "std", "min", "max"]).reset_index().rename(columns=aggregation)
    return {
        "serie": full, "perfil_semana": seasonal_week, "perfil_mes": seasonal_month,
        "atipicos": robust_outlier_table(frame),
    }


def save_figures(tables: dict[str, pd.DataFrame], acf_table: pd.DataFrame, stl: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """Genera figuras sobrias y devuelve un manifiesto de trazabilidad."""
    plt.style.use("seaborn-v0_8-whitegrid")
    color, accent = "#1f4e79", "#c55a11"
    manifest = []
    series = tables["serie"]

    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.plot(series[DATE_COLUMN], series[SERIES_COLUMN], color="#7f8c8d", linewidth=1.1, label="Importe semanal")
    ax.plot(series[DATE_COLUMN], series["mediana_movil_13s"], color=color, linewidth=2.1, label="Mediana móvil 13 semanas")
    evaluation = series[series["es_bloque_evaluacion"]]
    if not evaluation.empty:
        ax.axvspan(evaluation[DATE_COLUMN].min(), evaluation[DATE_COLUMN].max(), color=accent, alpha=0.10, label="Bloque final de evaluación")
    ax.set(title="Serie semanal observada del importe de compras", xlabel="Semana", ylabel="Pesos reales de mayo de 2026")
    ax.legend(frameon=False); fig.tight_layout()
    path = output_dir / "01_serie_semanal_compras.png"; fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig)
    manifest.append((1, path.name, "Serie semanal, tendencia robusta y bloque final reservado."))

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    valid = acf_table[acf_table["rezago"] > 0]
    axes[0].stem(valid["rezago"], valid["acf"], linefmt=color, markerfmt="o", basefmt=" ")
    pacf_valid = valid.dropna(subset=["pacf"])
    axes[1].stem(pacf_valid["rezago"], pacf_valid["pacf"], linefmt=accent, markerfmt="o", basefmt=" ")
    limit = float(acf_table["limite_aprox_95"].iloc[0])
    for ax, label in zip(axes, ("ACF", "PACF")):
        ax.axhline(limit, color="#666666", linestyle="--", linewidth=0.9); ax.axhline(-limit, color="#666666", linestyle="--", linewidth=0.9); ax.set_ylabel(label)
    axes[0].set_title("Dependencia temporal en el bloque de desarrollo"); axes[1].set_xlabel("Rezago semanal")
    fig.tight_layout(); path = output_dir / "02_acf_pacf_semanal.png"; fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig)
    manifest.append((2, path.name, "ACF y PACF calculadas sin utilizar las semanas finales de evaluación."))

    profile = tables["perfil_semana"]
    fig, ax = plt.subplots(figsize=(12, 5)); ax.plot(profile["semana_anio"], profile["mediana"], color=color, linewidth=1.8, marker="o", markersize=3)
    ax.set(title="Perfil exploratorio por semana del año", xlabel="Semana del año", ylabel="Mediana del importe semanal")
    fig.tight_layout(); path = output_dir / "03_perfil_semana_anio.png"; fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig)
    manifest.append((3, path.name, "Perfil anual exploratorio; no implica estacionalidad estable."))

    outliers = tables["atipicos"]
    fig, ax = plt.subplots(figsize=(12, 5)); ax.plot(outliers[DATE_COLUMN], outliers[SERIES_COLUMN], color="#95a5a6", linewidth=1.0)
    flagged = outliers[outliers["es_atipico_robusto"]]; ax.scatter(flagged[DATE_COLUMN], flagged[SERIES_COLUMN], color=accent, s=35, label="Atípico robusto |z| > 3.5", zorder=3)
    ax.set(title="Detección robusta de importes semanales atípicos", xlabel="Semana", ylabel="Pesos reales de mayo de 2026")
    if not flagged.empty: ax.legend(frameon=False)
    fig.tight_layout(); path = output_dir / "04_atipicos_robustos.png"; fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig)
    manifest.append((4, path.name, "Los atípicos se identifican para interpretación; no se eliminan automáticamente."))

    if not stl.empty:
        fig, axes = plt.subplots(4, 1, figsize=(12, 9), sharex=True)
        for ax, column, label, c in zip(axes, (SERIES_COLUMN, "tendencia_stl", "estacional_stl", "residuo_stl"), ("Observada", "Tendencia", "Estacional", "Residuo"), ("#7f8c8d", color, accent, "#6c3483")):
            ax.plot(stl[DATE_COLUMN], stl[column], color=c, linewidth=1.2); ax.set_ylabel(label)
        axes[0].set_title("Descomposición STL semanal exploratoria (periodo 52)"); axes[-1].set_xlabel("Semana")
        fig.tight_layout(); path = output_dir / "05_descomposicion_stl_exploratoria.png"; fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig)
        manifest.append((5, path.name, "Descomposición exploratoria limitada por el número de ciclos anuales."))
    return pd.DataFrame(manifest, columns=["numero", "archivo", "proposito"])


def main() -> None:
    """Ejecuta el diagnóstico y exporta tablas abiertas, figuras y resumen."""
    weekly = pd.read_excel(WEEKLY_MASTER_PATH, sheet_name="semanal")
    weekly[DATE_COLUMN] = pd.to_datetime(weekly[DATE_COLUMN])
    observed, coverage_gaps = primary_coverage_block(
        weekly, SERIES_COLUMN, activity_column="ventas_importe_real_2026_05"
    )
    excluded_weeks = int(observed.attrs.get("semanas_excluidas", len(weekly) - len(observed)))
    if len(observed) <= FINAL_EVALUATION_WEEKS:
        raise ValueError("No hay semanas suficientes para separar desarrollo y evaluación.")
    development = observed.iloc[:-FINAL_EVALUATION_WEEKS].copy()
    evaluation = observed.iloc[-FINAL_EVALUATION_WEEKS:].copy()
    values = development[SERIES_COLUMN].to_numpy(float)
    output_dir = ensure_output_dir() / ANALYSIS_DIRNAME; output_dir.mkdir(parents=True, exist_ok=True)
    tables = build_temporal_tables(observed, development)
    intermittency = classify_intermittency(values)
    stationarity = pd.DataFrame(stationarity_tests(values, "nivel") + stationarity_tests(np.log1p(values), "log1p"))
    autocorrelations = autocorrelation_table(values)
    stl, stl_summary = stl_components(development)
    ljung_lags = [lag for lag in (1, 4, 13, 26, 52) if lag < len(values)]
    ljung = acorr_ljungbox(values, lags=ljung_lags, return_df=True).reset_index().rename(columns={"index": "rezago", "lb_stat": "estadistico_ljung_box", "lb_pvalue": "p_valor"})
    summary = {
        "serie": SERIES_COLUMN, "frecuencia": "semanal, lunes a domingo",
        "semanas_fuente": int(len(weekly)), "semanas_bloque_continuo_principal": int(len(observed)),
        "semanas_excluidas_por_cobertura": excluded_weeks, "brechas_cobertura_identificadas": int(len(coverage_gaps)),
        "semanas_desarrollo_diagnostico": int(len(development)),
        "semanas_evaluacion_reservadas": int(len(evaluation)),
        "inicio_bloque_principal": str(observed[DATE_COLUMN].min().date()), "fin_bloque_principal": str(observed[DATE_COLUMN].max().date()),
        "inicio_evaluacion": str(evaluation[DATE_COLUMN].min().date()),
        "media_desarrollo": float(np.mean(values)), "mediana_desarrollo": float(np.median(values)),
        "desviacion_desarrollo": float(np.std(values, ddof=1)), "minimo_desarrollo": float(np.min(values)),
        "maximo_desarrollo": float(np.max(values)), "atipicos_robustos_observados": int(tables["atipicos"]["es_atipico_robusto"].sum()),
        **intermittency, "stl": stl_summary,
        "limitacion": "Los diagnósticos orientan la selección de modelos; no prueban causalidad ni garantizan estacionalidad estable.",
    }
    tables["serie"].to_csv(output_dir / "serie_semanal.csv", index=False, encoding="utf-8-sig")
    tables["perfil_semana"].to_csv(output_dir / "perfil_semana_anio.csv", index=False, encoding="utf-8-sig")
    tables["perfil_mes"].to_csv(output_dir / "perfil_mes.csv", index=False, encoding="utf-8-sig")
    tables["atipicos"].to_csv(output_dir / "atipicos_robustos.csv", index=False, encoding="utf-8-sig")
    coverage_gaps.to_csv(output_dir / "brechas_cobertura.csv", index=False, encoding="utf-8-sig")
    stationarity.to_csv(output_dir / "pruebas_estacionariedad.csv", index=False, encoding="utf-8-sig")
    autocorrelations.to_csv(output_dir / "acf_pacf.csv", index=False, encoding="utf-8-sig")
    ljung.to_csv(output_dir / "ljung_box.csv", index=False, encoding="utf-8-sig")
    if not stl.empty: stl.to_csv(output_dir / "componentes_stl.csv", index=False, encoding="utf-8-sig")
    manifest = save_figures(tables, autocorrelations, stl, output_dir)
    manifest.to_csv(output_dir / "manifiesto_figuras.csv", index=False, encoding="utf-8-sig")
    (output_dir / "resumen_diagnostico.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Diagnóstico temporal generado en: {output_dir}")


if __name__ == "__main__":
    main()
