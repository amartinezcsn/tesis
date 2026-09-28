import json
import os
import re
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from lxml import etree


SOURCE = Path(os.environ.get("AUDIT_DOCX", "documentacion/TESIS_AGO2026_Rev55_(ZUJ).docx"))
OUTPUT = Path(os.environ.get("AUDIT_INVENTORY", "tmp/auditoria_rev55/inventario_citas.json"))

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
YEAR = r"(?:19|20)\d{2}[a-z]?"
PARENTHETICAL = re.compile(r"\(([^()]*?\b" + YEAR + r"\b[^()]*)\)")
NARRATIVE = re.compile(
    r"\b([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÜÑáéíóúüñ'’-]+(?:\s+(?:et\s+al\.|&|y|e|[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÜÑáéíóúüñ'’-]+)){0,5})\s*\((" + YEAR + r")\)"
)


def paragraph_text(paragraph):
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()


def paragraph_style(paragraph):
    values = paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS)
    return values[0] if values else ""


def citations(text):
    found = []
    occupied = []
    for match in PARENTHETICAL.finditer(text):
        content = match.group(1).strip()
        if re.search(r"\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b", content, re.I):
            continue
        if re.search(r"\b" + YEAR + r"\b", content) and not re.fullmatch(r"\d+(?:\.\d+)*", content):
            found.append({"type": "parenthetical", "raw": f"({content})", "content": content})
            occupied.append(match.span())
    for match in NARRATIVE.finditer(text):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        found.append(
            {
                "type": "narrative",
                "raw": match.group(0),
                "content": f"{match.group(1)}, {match.group(2)}",
            }
        )
    return found


def main():
    with ZipFile(SOURCE) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))

    paragraphs = []
    section = ""
    in_references = False
    references = []
    occurrence_counter = Counter()

    for index, paragraph in enumerate(root.xpath(".//w:body//w:p", namespaces=NS), start=1):
        text = paragraph_text(paragraph)
        if not text:
            continue
        style = paragraph_style(paragraph)
        upper = text.upper().strip()
        if upper == "REFERENCIAS":
            in_references = True
            section = text
        elif upper.startswith("ANEXO "):
            in_references = False
            section = text
        elif style.lower().startswith("heading") or re.match(r"^\d+(?:\.\d+)*\s+", text):
            section = text

        if in_references and upper != "REFERENCIAS":
            references.append({"paragraph_index": index, "text": text})
            continue

        found = citations(text)
        for item in found:
            occurrence_counter[item["raw"]] += 1
        if found:
            rows = paragraph.xpath("ancestor::w:tr[1]", namespaces=NS)
            if rows:
                cells = []
                for cell in rows[0].xpath("./w:tc", namespaces=NS):
                    cell_text = " ".join(
                        filter(
                            None,
                            (paragraph_text(item) for item in cell.xpath(".//w:p", namespaces=NS)),
                        )
                    )
                    cells.append(cell_text)
                container = "table_row"
                context_text = " | ".join(cells)
            else:
                container = "body_paragraph"
                context_text = text
            paragraphs.append(
                {
                    "paragraph_index": index,
                    "style": style,
                    "section": section,
                    "text": text,
                    "container": container,
                    "context_text": context_text,
                    "citations": found,
                }
            )

    payload = {
        "source": str(SOURCE.resolve()),
        "citation_paragraphs": paragraphs,
        "references": references,
        "raw_citation_counts": occurrence_counter.most_common(),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"citation_paragraphs={len(paragraphs)}")
    print(f"raw_citations={sum(occurrence_counter.values())}")
    print(f"bibliography_paragraphs={len(references)}")
    print("top_citations")
    for raw, count in occurrence_counter.most_common(20):
        print(count, raw)


if __name__ == "__main__":
    main()
