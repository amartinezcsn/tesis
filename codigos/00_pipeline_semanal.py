"""Ejecuta el pipeline semanal reproducible de la tesis.

Orden: agregación -> características -> perfil -> análisis temporal ->
rolling-window -> reportes -> exportación DSS. Las fases diarias anteriores no
se modifican ni se ejecutan.
"""

import subprocess
import sys
from pathlib import Path

from config_semanal import DAILY_MASTER_PATH, WEEKLY_MASTER_PATH, WEEKLY_MODEL_PATH, ensure_output_dir
from trazabilidad import write_experiment_manifest


STAGES = (
    "02_agregar_semanal.py",
    "03_features_semanales.py",
    "04_perfil_semanal.py",
    "04_analisis_series_temporales_semanal.py",
    "06_modelos_rolling_window.py",
    "07_reportes_semanales.py",
    "08_exportar_dss_semanal.py",
)


def main() -> None:
    """Ejecuta las etapas en orden y detiene el flujo ante el primer error."""
    scripts_dir = Path(__file__).resolve().parent
    for stage in STAGES:
        print(f"\n=== Etapa semanal: {stage} ===")
        subprocess.run([sys.executable, str(scripts_dir / stage)], check=True)
    write_experiment_manifest(
        ensure_output_dir() / "00_trazabilidad_ejecucion.json",
        {"maestro_diario": DAILY_MASTER_PATH, "maestro_semanal": WEEKLY_MASTER_PATH, "dataset_modelado": WEEKLY_MODEL_PATH},
        [scripts_dir / stage for stage in (*STAGES, "config_semanal.py", "trazabilidad.py")],
    )
    print("Manifiesto generado: output/semanal/00_trazabilidad_ejecucion.json")


if __name__ == "__main__":
    main()
