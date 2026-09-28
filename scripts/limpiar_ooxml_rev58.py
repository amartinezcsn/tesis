from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import os
import xml.etree.ElementTree as ET


DOCX = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev58_(ZUJ)_Final.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def patch_xml(data: bytes, name: str):
    root = ET.fromstring(data)
    parents = {child: parent for parent in root.iter() for child in parent}
    removed_fields = 0
    removed_highlights = 0
    removed_run_shading = 0

    for node in list(root.iter(W + "fldSimple")):
        instruction = node.attrib.get(W + "instr", "")
        visible_text = "".join(t.text or "" for t in node.iter(W + "t"))
        if "TOC" in instruction and "No se encontraron entradas de tabla de contenido" in visible_text:
            parent = parents.get(node)
            if parent is not None:
                parent.remove(node)
                removed_fields += 1

    parents = {child: parent for parent in root.iter() for child in parent}
    for node in list(root.iter(W + "highlight")):
        parent = parents.get(node)
        if parent is not None:
            parent.remove(node)
            removed_highlights += 1

    parents = {child: parent for parent in root.iter() for child in parent}
    for node in list(root.iter(W + "shd")):
        parent = parents.get(node)
        if parent is not None and parent.tag == W + "rPr":
            parent.remove(node)
            removed_run_shading += 1

    if removed_fields or removed_highlights or removed_run_shading:
        return (
            ET.tostring(root, encoding="utf-8", xml_declaration=True),
            removed_fields,
            removed_highlights,
            removed_run_shading,
        )
    return data, 0, 0, 0


def main():
    totals = [0, 0, 0]
    with NamedTemporaryFile(delete=False, suffix=".docx", dir=DOCX.parent) as tmp_handle:
        tmp_path = Path(tmp_handle.name)

    try:
        with ZipFile(DOCX, "r") as source, ZipFile(tmp_path, "w", ZIP_DEFLATED) as target:
            for info in source.infolist():
                payload = source.read(info.filename)
                if info.filename.startswith("word/") and info.filename.endswith(".xml"):
                    payload, fields, highlights, shading = patch_xml(payload, info.filename)
                    totals[0] += fields
                    totals[1] += highlights
                    totals[2] += shading
                target.writestr(info, payload)
        os.replace(tmp_path, DOCX)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    print(f"Campos de error retirados: {totals[0]}")
    print(f"Resaltados retirados: {totals[1]}")
    print(f"Sombreados de texto retirados: {totals[2]}")


if __name__ == "__main__":
    main()
