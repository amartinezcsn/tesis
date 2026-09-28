from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

import pypdfium2 as pdfium
from lxml import etree


DOCX = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev59_(ZUJ)_Final.docx")
PDF = Path(r"C:\Python\tesis\tmp\rev59_render\TESIS_SEP2026_Rev59_QA_1.pdf")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value).strip().casefold()


def ptext(paragraph) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()


pdf = pdfium.PdfDocument(str(PDF))
page_texts = [norm(pdf[i].get_textpage().get_text_range()) for i in range(len(pdf))]


def printed_page(text: str, start_physical: int = 11) -> int:
    needle = norm(text)
    probes = [needle]
    if len(needle) > 95:
        probes.extend([needle[:95], needle[:70]])
    for idx in range(start_physical - 1, len(page_texts)):
        if any(probe and probe in page_texts[idx] for probe in probes):
            return idx  # physical page is idx+1; continuous printed page is physical-1 = idx
    raise RuntimeError(f"No se localizó en el PDF: {text!r}")


with ZipFile(DOCX, "r") as archive:
    document_xml = archive.read("word/document.xml")

root = etree.fromstring(document_xml)
body_paragraphs = root.xpath("//w:body/w:p", namespaces=NS)

# Map every TOC bookmark to the printed page of its target heading.
toc_updates = []
for paragraph in body_paragraphs:
    anchors = paragraph.xpath(".//w:hyperlink/@w:anchor", namespaces=NS)
    if not anchors:
        continue
    anchor = anchors[0]
    if not anchor.startswith("_Toc"):
        continue
    targets = root.xpath(f'//w:bookmarkStart[@w:name="{anchor}"]/ancestor::w:p[1]', namespaces=NS)
    if len(targets) != 1:
        continue
    title = ptext(targets[0])
    page = printed_page(title)
    texts = paragraph.xpath(".//w:t", namespaces=NS)
    if not texts:
        continue
    old = texts[-1].text or ""
    if re.fullmatch(r"\d+", old.strip()):
        texts[-1].text = str(page)
        toc_updates.append((title, page))

# Static new TOC entries.
for paragraph in body_paragraphs:
    text = ptext(paragraph)
    if text.startswith("Análisis de sensibilidad de la imputación") and "PENDIENTE" in text:
        page = printed_page("Análisis de sensibilidad de la imputación")
    elif text.startswith("Anexo B Paquete de reproducibilidad") and "PENDIENTE" in text:
        page = printed_page("Anexo B Paquete de reproducibilidad")
    else:
        continue
    for node in paragraph.xpath(".//w:t", namespaces=NS):
        if node.text and "PENDIENTE" in node.text:
            node.text = node.text.replace("PENDIENTE", str(page))

# Static table/figure index lies between its heading and RESUMEN.
index_heading = next(p for p in body_paragraphs if ptext(p) == "ÍNDICE DE TABLAS Y FIGURAS")
summary_heading = next(p for p in body_paragraphs if ptext(p) == "RESUMEN")
node = index_heading.getnext()
caption_updates = []
while node is not None and node is not summary_heading:
    following = node.getnext()
    if node.tag == W + "p":
        text = ptext(node)
        if "PENDIENTE" in text and re.match(r"^(Tabla|Figura)\s+\d+[.\-]", text):
            caption = text.rsplit("PENDIENTE", 1)[0].rstrip(" \t")
            page = printed_page(caption)
            for text_node in node.xpath(".//w:t", namespaces=NS):
                if text_node.text and "PENDIENTE" in text_node.text:
                    text_node.text = text_node.text.replace("PENDIENTE", str(page))
            caption_updates.append((caption, page))
    node = following

updated_xml = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
with NamedTemporaryFile(delete=False, suffix=".docx", dir=DOCX.parent) as handle:
    tmp = Path(handle.name)
try:
    with ZipFile(DOCX, "r") as source, ZipFile(tmp, "w", ZIP_DEFLATED) as target:
        for info in source.infolist():
            payload = updated_xml if info.filename == "word/document.xml" else source.read(info.filename)
            target.writestr(info, payload)
    os.replace(tmp, DOCX)
finally:
    if tmp.exists():
        tmp.unlink()

print(f"toc_updates={len(toc_updates)} caption_updates={len(caption_updates)}")
for caption, page in caption_updates:
    print(f"{page}\t{caption}")
