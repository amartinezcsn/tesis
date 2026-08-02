from __future__ import annotations

"""
PIPELINE MAESTRO DE TESIS
=========================

Producto integrador para ejecutar, en orden, toda la metodología:

1. Limpieza y construcción del dataset maestro.
2. Ingeniería de características.
3. Perfil del dataset y análisis dimensional.
4. Diagnóstico de multicolinealidad.
5. Selección de características y dataset reducido.
6. Reducción dimensional por PCA.
7. Modelos estadísticos y de ML con Rolling-Origin.
8. Redes recurrentes RNN/LSTM.

El programa reutiliza los scripts metodológicos existentes y genera una bitácora,
un manifiesto JSON y un resumen Excel de la ejecución.

Ejemplo de ejecución completa:

    python pipeline_maestro_tesis.py \
        --raw-dir "C:/Python/tesis/datasets/xlsx" \
        --input-dir "C:/Python/tesis/input" \
        --output-dir "C:/Python/tesis/output/analisis_dimensional"

Ejecución sin redes neuronales:

    python pipeline_maestro_tesis.py --sin-rnn

Reanudar desde el dataset de modelado existente:

    python pipeline_maestro_tesis.py --desde perfil
"""

import argparse
import importlib.util
import json
import logging
import platform
import shutil
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Callable

import pandas as pd


# -----------------------------------------------------------------------------
# Definición del flujo
# -----------------------------------------------------------------------------
SCRIPT_FILES = {
    "limpieza": "01_clean_eda.py",
    "ingenieria": "02_feature_engineering_profesional.py",
    "perfil": "03_perfil_dataset_y_dimensiones.py",
    "multicolinealidad": "04_diagnostico_multicolinealidad.py",
    "seleccion": "05_seleccion_caracteristicas_dataset_reducido.py",
    "pca": "06_pca_reduccion_componentes.py",
    "modelos": "07_modelos_estadisticos_ml_rolling_origin.py",
    "rnn": "08_rnn_lstm_dataset_reducido.py",
}

STAGE_ORDER = list(SCRIPT_FILES)
DATASET_VARIANTS = ("completo", "reducido", "pca")
RNN_VARIANTS = ("reducido", "pca")

RAW_REQUIRED_FILES = (
    "INPC_2022_2026.csv",
    "Temperatura_Tizayuca.csv",
    "Dataset_Tizayuca_2022_2026.xlsx",
    "Compras.xlsx",
    "Ventas.xlsx",
)


@dataclass
class StageResult:
    etapa: str
    variante: str
    estado: str
    inicio: str
    fin: str
    duracion_segundos: float
    mensaje: str


class PipelineError(RuntimeError):
    """Error controlado del pipeline metodológico."""


# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecuta el flujo metodológico completo de la tesis.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Carpeta que contiene los ocho scripts metodológicos.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path(r"C:/Python/tesis/datasets/xlsx"),
        help="Carpeta de archivos originales.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(r"C:/Python/tesis/input"),
        help="Carpeta para datasets maestro y de modelado.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(r"C:/Python/tesis/output/analisis_dimensional"),
        help="Carpeta para diagnósticos y resultados de modelos.",
    )
    parser.add_argument(
        "--desde",
        choices=STAGE_ORDER,
        default="limpieza",
        help="Primera etapa que se ejecutará.",
    )
    parser.add_argument(
        "--hasta",
        choices=STAGE_ORDER,
        default="rnn",
        help="Última etapa que se ejecutará.",
    )
    parser.add_argument(
        "--variantes-modelos",
        nargs="+",
        choices=DATASET_VARIANTS,
        default=list(DATASET_VARIANTS),
        help="Versiones del dataset evaluadas con Rolling-Origin.",
    )
    parser.add_argument(
        "--variantes-rnn",
        nargs="+",
        choices=RNN_VARIANTS,
        default=list(RNN_VARIANTS),
        help="Versiones del dataset evaluadas con RNN/LSTM.",
    )
    parser.add_argument(
        "--sin-rnn",
        action="store_true",
        help="Omite RNN/LSTM, útil cuando TensorFlow no está instalado.",
    )
    parser.add_argument(
        "--continuar-con-error",
        action="store_true",
        help="Continúa con etapas independientes después de un error.",
    )
    parser.add_argument(
        "--copiar-codigos",
        action="store_true",
        help="Copia los scripts usados a una carpeta de evidencia reproducible.",
    )
    return parser.parse_args()


def configure_logging(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "pipeline_tesis.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    return log_path


def load_module(module_name: str, path: Path) -> ModuleType:
    if not path.exists():
        raise PipelineError(f"No se encontró el script requerido: {path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise PipelineError(f"No fue posible cargar el módulo: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def validate_stage_range(start: str, end: str) -> list[str]:
    start_index = STAGE_ORDER.index(start)
    end_index = STAGE_ORDER.index(end)
    if start_index > end_index:
        raise PipelineError("La etapa indicada en --desde debe ser anterior o igual a --hasta.")
    return STAGE_ORDER[start_index : end_index + 1]


def validate_raw_inputs(raw_dir: Path) -> None:
    missing = [name for name in RAW_REQUIRED_FILES if not (raw_dir / name).exists()]
    if missing:
        formatted = "\n  - ".join(missing)
        raise PipelineError(
            "Faltan archivos originales para la etapa de limpieza:\n"
            f"  - {formatted}\n"
            f"Carpeta revisada: {raw_dir}"
        )


def validate_excel(path: Path, sheet: str | None = None) -> None:
    if not path.exists():
        raise PipelineError(f"No se generó o no existe el archivo esperado: {path}")
    if path.stat().st_size == 0:
        raise PipelineError(f"El archivo está vacío: {path}")
    if sheet is not None:
        with pd.ExcelFile(path) as excel:
            if sheet not in excel.sheet_names:
                raise PipelineError(
                    f"El archivo {path.name} no contiene la hoja requerida '{sheet}'."
                )


def run_tracked(
    etapa: str,
    variante: str,
    action: Callable[[], None],
    results: list[StageResult],
) -> bool:
    start_dt = datetime.now()
    started = time.perf_counter()
    logging.info("INICIO | %s | %s", etapa, variante or "general")
    try:
        action()
        status = "correcto"
        message = "Etapa finalizada sin errores."
        success = True
        logging.info("FIN CORRECTO | %s | %s", etapa, variante or "general")
    except Exception as exc:  # se registra el error completo en la bitácora
        status = "error"
        message = f"{type(exc).__name__}: {exc}"
        success = False
        logging.error("ERROR | %s | %s | %s", etapa, variante or "general", message)
        logging.debug(traceback.format_exc())
    end_dt = datetime.now()
    results.append(
        StageResult(
            etapa=etapa,
            variante=variante or "general",
            estado=status,
            inicio=start_dt.isoformat(timespec="seconds"),
            fin=end_dt.isoformat(timespec="seconds"),
            duracion_segundos=round(time.perf_counter() - started, 3),
            mensaje=message,
        )
    )
    return success


def configure_shared_module(
    scripts_dir: Path,
    input_dir: Path,
    output_dir: Path,
) -> ModuleType:
    config = load_module("config_metodologia", scripts_dir / "config_metodologia.py")
    config.DATASET_PATH = input_dir / "dataset_modelado_diario.xlsx"
    config.SHEET_NAME = "modelo"
    config.BASE_OUTPUT_DIR = output_dir
    return config


def copy_reproducibility_evidence(scripts_dir: Path, output_dir: Path) -> None:
    evidence_dir = output_dir / "evidencia_codigo"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    names = ["config_metodologia.py", "README_metodologia.md", *SCRIPT_FILES.values()]
    for name in names:
        source = scripts_dir / name
        if source.exists():
            shutil.copy2(source, evidence_dir / name)
    shutil.copy2(Path(__file__).resolve(), evidence_dir / Path(__file__).name)


def write_execution_products(
    output_dir: Path,
    args: argparse.Namespace,
    results: list[StageResult],
    log_path: Path,
) -> None:
    result_rows = [asdict(item) for item in results]
    result_df = pd.DataFrame(result_rows)

    generated_files = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file():
            generated_files.append(
                {
                    "archivo": str(path.relative_to(output_dir)),
                    "tamano_bytes": path.stat().st_size,
                    "fecha_modificacion": datetime.fromtimestamp(path.stat().st_mtime).isoformat(
                        timespec="seconds"
                    ),
                }
            )
    files_df = pd.DataFrame(generated_files)

    summary_path = output_dir / "00_resumen_ejecucion_pipeline.xlsx"
    with pd.ExcelWriter(summary_path, engine="openpyxl") as writer:
        result_df.to_excel(writer, sheet_name="etapas", index=False)
        files_df.to_excel(writer, sheet_name="archivos_generados", index=False)
        pd.DataFrame(
            {
                "parametro": [
                    "fecha_ejecucion",
                    "python",
                    "sistema_operativo",
                    "scripts_dir",
                    "raw_dir",
                    "input_dir",
                    "output_dir",
                    "bitacora",
                ],
                "valor": [
                    datetime.now().isoformat(timespec="seconds"),
                    sys.version.replace("\n", " "),
                    platform.platform(),
                    str(args.scripts_dir.resolve()),
                    str(args.raw_dir.resolve()),
                    str(args.input_dir.resolve()),
                    str(args.output_dir.resolve()),
                    str(log_path.resolve()),
                ],
            }
        ).to_excel(writer, sheet_name="configuracion", index=False)

    manifest = {
        "producto": "Pipeline metodológico integrado de tesis",
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "configuracion": {
            "scripts_dir": str(args.scripts_dir.resolve()),
            "raw_dir": str(args.raw_dir.resolve()),
            "input_dir": str(args.input_dir.resolve()),
            "output_dir": str(args.output_dir.resolve()),
            "desde": args.desde,
            "hasta": args.hasta,
            "variantes_modelos": args.variantes_modelos,
            "variantes_rnn": [] if args.sin_rnn else args.variantes_rnn,
        },
        "resultados": result_rows,
        "archivos_generados": generated_files,
    }
    (output_dir / "00_manifiesto_pipeline.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# -----------------------------------------------------------------------------
# Ejecución principal
# -----------------------------------------------------------------------------
def main() -> int:
    args = parse_args()
    args.scripts_dir = args.scripts_dir.expanduser()
    args.raw_dir = args.raw_dir.expanduser()
    args.input_dir = args.input_dir.expanduser()
    args.output_dir = args.output_dir.expanduser()

    args.input_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = configure_logging(args.output_dir)
    results: list[StageResult] = []

    try:
        stages = validate_stage_range(args.desde, args.hasta)
        logging.info("Etapas solicitadas: %s", ", ".join(stages))

        # Carga y redirecciona la configuración común antes de importar los análisis.
        configure_shared_module(args.scripts_dir, args.input_dir, args.output_dir)

        if args.copiar_codigos:
            copy_reproducibility_evidence(args.scripts_dir, args.output_dir)

        # 1) Limpieza y dataset maestro
        if "limpieza" in stages:
            validate_raw_inputs(args.raw_dir)
            clean = load_module("tesis_clean_eda", args.scripts_dir / SCRIPT_FILES["limpieza"])
            clean.BASE_DIR = args.raw_dir
            clean.OUT_DIR = args.input_dir

            ok = run_tracked("limpieza", "general", clean.main, results)
            if ok:
                validate_excel(args.input_dir / "dataset_maestro_diario.xlsx", "maestro")
            elif not args.continuar_con_error:
                raise PipelineError("La etapa de limpieza no finalizó correctamente.")

        # 2) Ingeniería de características
        if "ingenieria" in stages:
            validate_excel(args.input_dir / "dataset_maestro_diario.xlsx", "maestro")
            feature = load_module(
                "tesis_feature_engineering", args.scripts_dir / SCRIPT_FILES["ingenieria"]
            )
            feature.BASE_DIR = args.input_dir
            feature.INPUT_FILE = args.input_dir / "dataset_maestro_diario.xlsx"
            feature.OUTPUT_FILE = args.input_dir / "dataset_modelado_diario.xlsx"
            feature.SUMMARY_FILE = args.input_dir / "feature_engineering_resumen.md"

            ok = run_tracked("ingenieria", "general", feature.main, results)
            if ok:
                validate_excel(args.input_dir / "dataset_modelado_diario.xlsx", "modelo")
            elif not args.continuar_con_error:
                raise PipelineError("La ingeniería de características no finalizó correctamente.")

        # Todas las etapas siguientes requieren el dataset de modelado.
        if any(stage in stages for stage in STAGE_ORDER[2:]):
            validate_excel(args.input_dir / "dataset_modelado_diario.xlsx", "modelo")

        # 3) Perfil dimensional
        if "perfil" in stages:
            module = load_module("tesis_perfil", args.scripts_dir / SCRIPT_FILES["perfil"])
            ok = run_tracked("perfil", "general", module.main, results)
            if not ok and not args.continuar_con_error:
                raise PipelineError("El perfil del dataset no finalizó correctamente.")

        # 4) Multicolinealidad
        if "multicolinealidad" in stages:
            module = load_module(
                "tesis_multicolinealidad", args.scripts_dir / SCRIPT_FILES["multicolinealidad"]
            )
            ok = run_tracked("multicolinealidad", "general", module.main, results)
            if not ok and not args.continuar_con_error:
                raise PipelineError("El diagnóstico de multicolinealidad falló.")

        # 5) Selección de características
        if "seleccion" in stages:
            module = load_module("tesis_seleccion", args.scripts_dir / SCRIPT_FILES["seleccion"])
            ok = run_tracked("seleccion", "reducido", module.main, results)
            if ok:
                validate_excel(
                    args.output_dir / "03_dataset_reducido_por_seleccion.xlsx",
                    "dataset_reducido",
                )
            elif not args.continuar_con_error:
                raise PipelineError("La selección de características falló.")

        # 6) PCA
        if "pca" in stages:
            module = load_module("tesis_pca", args.scripts_dir / SCRIPT_FILES["pca"])
            ok = run_tracked("pca", "pca", module.main, results)
            if ok:
                validate_excel(args.output_dir / "04_dataset_pca_componentes.xlsx", "dataset_pca")
            elif not args.continuar_con_error:
                raise PipelineError("La reducción PCA falló.")

        # 7) Comparación Rolling-Origin para cada variante
        if "modelos" in stages:
            module = load_module("tesis_modelos", args.scripts_dir / SCRIPT_FILES["modelos"])
            for variant in args.variantes_modelos:
                module.DATASET_TO_USE = variant
                ok = run_tracked("modelos_rolling_origin", variant, module.main, results)
                if not ok and not args.continuar_con_error:
                    raise PipelineError(f"Falló el modelado Rolling-Origin para '{variant}'.")

        # 8) RNN/LSTM para reducido y PCA
        if "rnn" in stages and not args.sin_rnn:
            module = load_module("tesis_rnn", args.scripts_dir / SCRIPT_FILES["rnn"])
            for variant in args.variantes_rnn:
                module.DATASET_TO_USE = variant
                ok = run_tracked("rnn_lstm", variant, module.main, results)
                if not ok and not args.continuar_con_error:
                    raise PipelineError(f"Falló RNN/LSTM para '{variant}'.")
        elif "rnn" in stages and args.sin_rnn:
            logging.info("RNN/LSTM omitido por parámetro --sin-rnn.")
            now = datetime.now().isoformat(timespec="seconds")
            results.append(
                StageResult(
                    etapa="rnn_lstm",
                    variante="todas",
                    estado="omitido",
                    inicio=now,
                    fin=now,
                    duracion_segundos=0.0,
                    mensaje="Etapa omitida mediante --sin-rnn.",
                )
            )

    except Exception as exc:
        logging.error("PIPELINE INTERRUMPIDO: %s", exc)
        if not results or results[-1].estado != "error":
            now = datetime.now().isoformat(timespec="seconds")
            results.append(
                StageResult(
                    etapa="pipeline",
                    variante="general",
                    estado="error",
                    inicio=now,
                    fin=now,
                    duracion_segundos=0.0,
                    mensaje=f"{type(exc).__name__}: {exc}",
                )
            )
        write_execution_products(args.output_dir, args, results, log_path)
        return 1

    write_execution_products(args.output_dir, args, results, log_path)
    errors = sum(item.estado == "error" for item in results)
    logging.info("Pipeline terminado. Errores registrados: %d", errors)
    logging.info("Resumen: %s", args.output_dir / "00_resumen_ejecucion_pipeline.xlsx")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
