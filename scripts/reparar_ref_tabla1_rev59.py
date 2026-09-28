from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


DOCX = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev59_(ZUJ)_Final.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS = {"w": W[1:-1]}
TEXT = (
    "Con el propósito de sintetizar las principales contribuciones de la literatura revisada, "
    "en la Tabla 1 se presentan los estudios más relevantes relacionados con la aplicación de "
    "inteligencia artificial, analítica de datos y adopción tecnológica en la gestión empresarial "
    "y el pronóstico de demanda."
)

with ZipFile(DOCX, "r") as source:
    xml = source.read("word/document.xml")
root = etree.fromstring(xml)
matches = []
for paragraph in root.xpath("//w:body/w:p", namespaces=NS):
    text = "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()
    if text.startswith("Con el propósito de sintetizar las principales contribuciones"):
        matches.append(paragraph)
if len(matches) != 1:
    raise RuntimeError(f"Párrafo objetivo no único: {len(matches)}")

paragraph = matches[0]
for child in list(paragraph):
    if child.tag != W + "pPr":
        paragraph.remove(child)
run = etree.SubElement(paragraph, W + "r")
text_node = etree.SubElement(run, W + "t")
text_node.text = TEXT

updated = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
with NamedTemporaryFile(delete=False, suffix=".docx", dir=DOCX.parent) as handle:
    tmp = Path(handle.name)
try:
    with ZipFile(DOCX, "r") as source, ZipFile(tmp, "w", ZIP_DEFLATED) as target:
        for info in source.infolist():
            payload = updated if info.filename == "word/document.xml" else source.read(info.filename)
            target.writestr(info, payload)
    os.replace(tmp, DOCX)
finally:
    if tmp.exists():
        tmp.unlink()

print("flattened_missing_ref=xref_tabla_01")
