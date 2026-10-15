from pathlib import Path
import re

from docx import Document


DOCX = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev62_(ZUJ)_Final.docx")


def normalize(text: str) -> str:
    return " ".join(text.split())


doc = Document(DOCX)
paragraphs = list(doc.paragraphs)
image_paragraphs = [
    (index, paragraph)
    for index, paragraph in enumerate(paragraphs)
    if paragraph._p.xpath(".//w:drawing")
]
updated = []

for position, (paragraph_index, paragraph) in enumerate(image_paragraphs):
    doc_properties = paragraph._p.xpath(".//wp:docPr")
    if not doc_properties:
        continue

    prop = doc_properties[0]
    existing_description = prop.get("descr", "")
    if (prop.get("descr") or prop.get("title")) and not existing_description.startswith("Figura ."):
        continue

    caption = ""
    for candidate in paragraphs[paragraph_index + 1 : paragraph_index + 6]:
        text = normalize(candidate.text)
        if text.lower().startswith(("figura ", "gráfica ", "ilustración ")):
            caption = re.sub(r"^Figura\s*\.\s*", "Figura: ", text, flags=re.IGNORECASE)
            break

    if not caption:
        caption = f"Figura académica {position + 1} de la tesis"

    description = f"{caption}. Representación visual descrita e interpretada en el texto contiguo."
    prop.set("descr", description)
    prop.set("title", caption)
    updated.append((prop.get("id"), caption))

doc.save(DOCX)

print(f"Textos alternativos agregados: {len(updated)}")
for image_id, caption in updated:
    print(f"{image_id}: {caption}")
