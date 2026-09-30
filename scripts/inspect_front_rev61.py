from zipfile import ZipFile
from lxml import etree

path = r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev61_(ZUJ)_Final.docx"
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
wns = ns["w"]
with ZipFile(path) as archive:
    root = etree.fromstring(archive.read("word/document.xml"))

paragraphs = root.xpath("//w:body/w:p", namespaces=ns)
for index, paragraph in enumerate(paragraphs[:180]):
    text = "".join(paragraph.xpath(".//w:t/text()", namespaces=ns)).strip()
    page_breaks = len(paragraph.xpath('.//w:br[@w:type="page"]', namespaces=ns))
    page_before = paragraph.xpath("./w:pPr/w:pageBreakBefore", namespaces=ns)
    styles = paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=ns)
    instructions = " | ".join(paragraph.xpath(".//w:instrText/text()", namespaces=ns))
    if page_breaks or text in {"ÍNDICE", "ÍNDICE DE TABLAS", "ÍNDICE DE IMÁGENES", "RESUMEN"} or "TOC " in instructions:
        values = [node.get(f"{{{wns}}}val") for node in page_before]
        print(index, repr(text[:80]), "br", page_breaks, "pb", values, "style", styles, "instr", instructions)
