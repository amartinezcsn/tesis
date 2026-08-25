"""Ejecuta el pipeline semanal reproducible de la tesis.

Orden: agregación -> características -> perfil -> rolling-window -> reportes ->
exportación DSS. Las fases diarias anteriores no se modifican ni se ejecutan.
"""

import subprocess
import sys
from pathlib import Path


STAGES = (
    "02_agregar_semanal.py",
    "03_features_semanales.py",
    "04_perfil_semanal.py",
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


if __name__ == "__main__":
    main()
