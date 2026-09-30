from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import os

from lxml import etree


DOCX = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev61_(ZUJ)_Final.docx")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = f"{{{NS['w']}}}"
TARGETS = {"ÍNDICE DE TABLAS", "ÍNDICE DE IMÁGENES"}


with ZipFile(DOCX, "r") as archive:
    document_xml = archive.read("word/document.xml")

root = etree.fromstring(document_xml)
updated = []
for paragraph in root.xpath("//w:body/w:p", namespaces=NS):
    text = "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()
    if text not in TARGETS:
        continue
    ppr = paragraph.find(W + "pPr")
    if ppr is None:
        ppr = etree.Element(W + "pPr")
        paragraph.insert(0, ppr)
    style = ppr.find(W + "pStyle")
    if style is None:
        style = etree.Element(W + "pStyle")
        ppr.insert(0, style)
    style.set(W + "val", "Normal")
    for page_break_before in list(ppr.findall(W + "pageBreakBefore")):
        ppr.remove(page_break_before)
    outline = ppr.find(W + "outlineLvl")
    if outline is None:
        outline = etree.Element(W + "outlineLvl")
        ppr.append(outline)
    outline.set(W + "val", "9")
    updated.append(text)

if set(updated) != TARGETS:
    raise RuntimeError(f"No se actualizaron ambos encabezados: {updated}")

payload = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
with NamedTemporaryFile(delete=False, suffix=".docx", dir=DOCX.parent) as handle:
    temporary = Path(handle.name)
try:
    with ZipFile(DOCX, "r") as source, ZipFile(temporary, "w", ZIP_DEFLATED) as target:
        for info in source.infolist():
            target.writestr(info, payload if info.filename == "word/document.xml" else source.read(info.filename))
    os.replace(temporary, DOCX)
finally:
    if temporary.exists():
        temporary.unlink()

print("updated=" + ", ".join(updated))
