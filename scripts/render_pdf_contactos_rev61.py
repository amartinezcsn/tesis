from pathlib import Path
import math

import pypdfium2 as pdfium
from PIL import Image, ImageDraw


PDF = Path(r"C:\Python\tesis\tmp\rev61_render\TESIS_SEP2026_Rev61_QA_word_v4.pdf")
OUT = Path(r"C:\Python\tesis\tmp\rev61_render\final_png")
CONTACTS = Path(r"C:\Python\tesis\tmp\rev61_render\final_contacts")
OUT.mkdir(parents=True, exist_ok=True)
CONTACTS.mkdir(parents=True, exist_ok=True)

pdf = pdfium.PdfDocument(str(PDF))
page_paths = []
for index in range(len(pdf)):
    bitmap = pdf[index].render(scale=1.65)
    image = bitmap.to_pil().convert("RGB")
    path = OUT / f"page-{index + 1:03d}.png"
    image.save(path, optimize=True)
    page_paths.append(path)

thumb_w = 1000
label_h = 34
gap = 14
for start in range(0, len(page_paths), 4):
    chunk = page_paths[start : start + 4]
    thumbs = []
    for path in chunk:
        image = Image.open(path).convert("RGB")
        ratio = thumb_w / image.width
        image = image.resize((thumb_w, int(image.height * ratio)), Image.Resampling.LANCZOS)
        thumbs.append((path, image))
    thumb_h = max(image.height for _, image in thumbs)
    sheet = Image.new("RGB", (2 * thumb_w + 3 * gap, 2 * (thumb_h + label_h) + 3 * gap), "#d0d0d0")
    draw = ImageDraw.Draw(sheet)
    for position, (path, image) in enumerate(thumbs):
        row, col = divmod(position, 2)
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        draw.text((x, y), path.stem, fill="black")
        sheet.paste(image, (x, y + label_h))
    end = start + len(chunk)
    sheet.save(CONTACTS / f"contact-{start + 1:03d}-{end:03d}.png", optimize=True)

print(f"pages={len(page_paths)} contacts={math.ceil(len(page_paths) / 4)}")
