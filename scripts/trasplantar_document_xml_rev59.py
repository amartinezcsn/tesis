from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile


BASE = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev58_(ZUJ)_Corregida.docx")
DONOR = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev59_(ZUJ)_Final.docx")
OUTPUT = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev59_(ZUJ)_Final.docx")


with ZipFile(DONOR, "r") as source:
    document_xml = source.read("word/document.xml")

with NamedTemporaryFile(delete=False, suffix=".docx", dir=OUTPUT.parent) as handle:
    tmp = Path(handle.name)

try:
    with ZipFile(BASE, "r") as source, ZipFile(tmp, "w", ZIP_DEFLATED) as target:
        for info in source.infolist():
            payload = document_xml if info.filename == "word/document.xml" else source.read(info.filename)
            target.writestr(info, payload)
    os.replace(tmp, OUTPUT)
finally:
    if tmp.exists():
        tmp.unlink()

print(f"saved={OUTPUT}")
