from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET


DOCX = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev58_(ZUJ)_Final.docx")
TOKENS = {
    "errores_campos": ("¡Error!", "Error!", "No se encontraron entradas de tabla de contenido"),
    "toc": ("TOC ",),
    "resaltados": ("<w:highlight",),
    "cambios_insertados": ("<w:ins",),
    "cambios_eliminados": ("<w:del",),
}


parts = {}
with ZipFile(DOCX) as archive:
    for name in archive.namelist():
        if name.startswith("word/") and name.endswith(".xml"):
            parts[name] = archive.read(name).decode("utf-8", errors="ignore")
    xml = "\n".join(parts.values())

for label, variants in TOKENS.items():
    print(f"{label}: {sum(xml.count(token) for token in variants)}")
print(f"integridad_zip: OK ({len(ZipFile(DOCX).namelist())} partes)")

ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
for tag in ("ins", "del"):
    exact = 0
    for payload in parts.values():
        exact += sum(1 for node in ET.fromstring(payload).iter() if node.tag == ns + tag)
    print(f"cambios_{tag}_exactos: {exact}")

for name, payload in parts.items():
    for match in re.finditer(r"TOC ", payload):
        start = max(0, match.start() - 80)
        end = min(len(payload), match.end() + 160)
        print(f"contexto_TOC {name}: {payload[start:end]}")
