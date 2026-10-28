from pathlib import Path
import sys
import unicodedata

from pypdf import PdfReader


PDF = Path(r"C:\Python\tesis\tmp\rev67_render\TESIS_OCT2026_Rev67_(ZUJ)_Glosario_Complementado.pdf")


def norm(value):
    value = unicodedata.normalize("NFKD", value.lower())
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).split())


reader = PdfReader(PDF)
texts = [page.extract_text() or "" for page in reader.pages]
queries = sys.argv[1:] or [
    "AGRADECIMIENTOS", "CAPÍTULO I INTRODUCCIÓN", "1.2.2 Pregunta de investigación",
    "1.3 Hipótesis y criterio de evaluación", "1.4.1 Objetivo general",
    "2.1 Revisión de evidencia empírica", "3.5 Diseño evaluativo y líneas base",
    "3.7 Delimitación temporal", "3.8.4 Modelos de referencia y arquitectura híbrida",
    "3.8.5 Validación temporal rolling window", "3.8.8 Consideraciones éticas",
    "3.9.2 Preparación de fuentes y cobertura semanal",
    "3.9.5 Definición de categorías y distribución presupuestaria",
    "3.9.6 Modelos y validación temporal", "3.9.8 Alcance y trazabilidad",
    "4.2 Análisis de sensibilidad", "4.3 Diseño efectivo de evaluación",
    "4.4 Rendimiento comparativo", "4.5 Distribución porcentual",
    "4.6 Evaluación exploratoria", "4.7 Alcance de los resultados",
    "4.8.4 Validez y limitaciones", "5.1 Conclusiones", "5.3 Trabajo futuro",
    "GLOSARIO", "REFERENCIAS", "Anexo B Paquete de reproducibilidad",
]
for query in queries:
    hits = [i + 1 for i, text in enumerate(texts) if norm(query) in norm(text)]
    printed = ["front" if page < 14 else page - 13 for page in hits]
    print(f"{query}\tphysical={hits}\tprinted={printed}")
