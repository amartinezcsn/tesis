from __future__ import annotations

import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


DOCX = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev59_(ZUJ)_Final.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS = {"w": W[1:-1]}


def ptext(paragraph) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()


def add_right_dotted_tab(paragraph, position: str) -> None:
    ppr = paragraph.find(W + "pPr")
    if ppr is None:
        ppr = etree.Element(W + "pPr")
        paragraph.insert(0, ppr)
    tabs = ppr.find(W + "tabs")
    if tabs is None:
        tabs = etree.SubElement(ppr, W + "tabs")
    for old in list(tabs):
        if old.tag == W + "tab" and old.get(W + "val") == "right":
            tabs.remove(old)
    tab = etree.SubElement(tabs, W + "tab")
    tab.set(W + "val", "right")
    tab.set(W + "leader", "dot")
    tab.set(W + "pos", position)


with ZipFile(DOCX, "r") as source:
    xml = source.read("word/document.xml")
root = etree.fromstring(xml)
paragraphs = root.xpath("//w:body/w:p", namespaces=NS)
index_heading = next(p for p in paragraphs if ptext(p) == "ÍNDICE DE TABLAS Y FIGURAS")
summary = next(p for p in paragraphs if ptext(p) == "RESUMEN")
node = index_heading.getnext()
updated = 0
while node is not None and node is not summary:
    following = node.getnext()
    if node.tag == W + "p" and re.match(r"^(Tabla|Figura)\s+\d+[.\-]", ptext(node)):
        add_right_dotted_tab(node, "9362")
        updated += 1
    node = following

for paragraph in paragraphs:
    text = ptext(paragraph)
    if text.startswith("Análisis de sensibilidad de la imputación") or text.startswith("Anexo B Paquete de reproducibilidad"):
        if paragraph.getparent() is root.find(W + "body") and "PENDIENTE" not in text:
            # Only the static contents-list entry has a tab element.
            if paragraph.xpath(".//w:tab", namespaces=NS):
                add_right_dotted_tab(paragraph, "9962")
                updated += 1

payload = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
with NamedTemporaryFile(delete=False, suffix=".docx", dir=DOCX.parent) as handle:
    tmp = Path(handle.name)
try:
    with ZipFile(DOCX, "r") as source, ZipFile(tmp, "w", ZIP_DEFLATED) as target:
        for info in source.infolist():
            target.writestr(info, payload if info.filename == "word/document.xml" else source.read(info.filename))
    os.replace(tmp, DOCX)
finally:
    if tmp.exists():
        tmp.unlink()

print(f"tab_stops_updated={updated}")
