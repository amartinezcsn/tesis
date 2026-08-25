from pathlib import Path

from docx import Document


SOURCE = Path("documentacion/TESIS_AGO2026_Rev39_(ZUJ)_22ago2026_JustificacionAlineada.docx")
OUTPUT = Path("documentacion/TESIS_AGO2026_Rev40_(ZUJ)_24ago2026_HorizonteSemanal.docx")
OLD = "PREDICCIÓN DEL PRESUPUESTO DE ABASTECIMIENTO MEDIANTE APRENDIZAJE AUTOMÁTICO: EVALUACIÓN COMPARATIVA EN UNA MICROEMPRESA DE REPOSTERÍA"
NEW = (
    "PRONÓSTICO SEMANAL DEL PRESUPUESTO DE ABASTECIMIENTO MEDIANTE MODELOS "
    "ESTADÍSTICOS Y APRENDIZAJE AUTOMÁTICO CON VALIDACIÓN DE VENTANA DESLIZANTE: "
    "ESTUDIO DE CASO EN UNA MICROEMPRESA DE REPOSTERÍA CREATIVA DE TIZAYUCA, HIDALGO"
)


def normalize(text: str) -> str:
    return " ".join(text.upper().strip("“”\\\"").split())


document = Document(SOURCE)
title = next((p for p in document.paragraphs if normalize(p.text) == OLD), None)
if title is None:
    raise RuntimeError("No se encontró el título esperado; no se realizó ningún cambio.")

if not title.runs:
    raise RuntimeError("El párrafo del título no contiene formato reutilizable.")

first_run = title.runs[0]
for run in title.runs[1:]:
    run.text = ""
first_run.text = NEW

document.save(OUTPUT)
print(OUTPUT)
