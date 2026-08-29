"""Utilidades para registrar la reproducibilidad de cada corrida semanal."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from config_semanal import (
    DATE_COLUMN,
    EXPERIMENT_SEED,
    FINAL_EVALUATION_WEEKS,
    HORIZON_WEEKS,
    LAG_WEEKS,
    OUTPUT_DIR,
    RANDOM_STATE,
    ROLLING_WINDOWS,
    STEP_WEEKS,
    TARGET_COLUMN,
    WINDOW_WEEKS,
)


def file_fingerprint(path: Path) -> dict[str, str | int | None]:
    """Devuelve identidad verificable de una fuente sin copiar su contenido."""
    if not path.exists():
        return {"ruta": str(path), "existe": False, "tamano_bytes": None, "sha256": None}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"ruta": str(path), "existe": True, "tamano_bytes": path.stat().st_size, "sha256": digest}


def installed_versions() -> dict[str, str | None]:
    """Registra las bibliotecas que afectan las estimaciones reproducibles."""
    names = ("numpy", "pandas", "openpyxl", "scikit-learn", "statsmodels", "scipy", "matplotlib")
    result = {}
    for name in names:
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = None
    return result


def write_experiment_manifest(output_path: Path, inputs: dict[str, Path], code_files: list[Path]) -> None:
    """Escribe el manifiesto que vincula resultados, datos, código y entorno."""
    payload = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "frecuencia": "semanal",
        "objetivo": TARGET_COLUMN,
        "columna_temporal": DATE_COLUMN,
        "parametros": {
            "ventana_semanas": WINDOW_WEEKS,
            "horizonte_semanas": HORIZON_WEEKS,
            "paso_semanas": STEP_WEEKS,
            "evaluacion_final_semanas": FINAL_EVALUATION_WEEKS,
            "rezagos": list(LAG_WEEKS),
            "ventanas_moviles": list(ROLLING_WINDOWS),
            "semilla": EXPERIMENT_SEED,
            "random_state": RANDOM_STATE,
        },
        "entorno": {"python": sys.version, "plataforma": platform.platform(), "paquetes": installed_versions()},
        "fuentes": {name: file_fingerprint(path) for name, path in inputs.items()},
        "codigo": {path.name: file_fingerprint(path) for path in code_files},
        "restriccion_sinteticos": "Los datos sintéticos se mantienen fuera de las entradas de modelado y no se usan en H1/H2.",
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
