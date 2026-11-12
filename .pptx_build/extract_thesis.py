from __future__ import annotations

import json
from pathlib import Path

from docx import Document


SOURCE = Path(r"C:\Python\tesis\documentacion\TESIS_OCT2026_Rev68_(ZUJ)_Final.docx")
OUTPUT = Path(r"C:\Python\tesis\.pptx_build\thesis_extract.json")


def clean(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split())


doc = Document(SOURCE)
paragraphs = []
for index, paragraph in enumerate(doc.paragraphs):
    text = clean(paragraph.text)
    if not text:
        continue
    paragraphs.append(
        {
            "index": index,
            "style": paragraph.style.name if paragraph.style else "",
            "text": text,
        }
    )

tables = []
for table_index, table in enumerate(doc.tables):
    rows = []
    for row in table.rows:
        rows.append([clean(cell.text) for cell in row.cells])
    tables.append({"index": table_index, "rows": rows})

payload = {
    "source": str(SOURCE),
    "core_properties": {
        "title": doc.core_properties.title,
        "subject": doc.core_properties.subject,
        "author": doc.core_properties.author,
        "last_modified_by": doc.core_properties.last_modified_by,
        "created": doc.core_properties.created.isoformat() if doc.core_properties.created else None,
        "modified": doc.core_properties.modified.isoformat() if doc.core_properties.modified else None,
    },
    "section_count": len(doc.sections),
    "paragraphs": paragraphs,
    "tables": tables,
}
OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"paragraph_count": len(paragraphs), "table_count": len(tables), "output": str(OUTPUT)}, ensure_ascii=False))
