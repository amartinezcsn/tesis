from pathlib import Path
import math

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

PDF = Path(r"C:\Python\tesis\tmp\rev58_render\TESIS_SEP2026_Rev58_Final_QA.pdf")
OUT = Path(r"C:\Python\tesis\tmp\rev58_render\final_png")
CONTACTS = Path(r"C:\Python\tesis\tmp\rev58_render\final_contacts")
OUT.mkdir(parents=True, exist_ok=True)
CONTACTS.mkdir(parents=True, exist_ok=True)

pdf = pdfium.PdfDocument(str(PDF))
page_paths = []
for index in range(len(pdf)):
    bitmap = pdf[index].render(scale=1.55)
    image = bitmap.to_pil().convert("RGB")
    path = OUT / f"page-{index + 1:03d}.png"
    image.save(path, optimize=True)
    page_paths.append(path)

thumb_w = 520
label_h = 26
gap = 10
for start in range(0, len(page_paths), 6):
    chunk = page_paths[start : start + 6]
    thumbs = []
    for path in chunk:
        im = Image.open(path).convert("RGB")
        ratio = thumb_w / im.width
        im = im.resize((thumb_w, int(im.height * ratio)), Image.Resampling.LANCZOS)
        thumbs.append((path, im))
    thumb_h = max(im.height for _, im in thumbs)
    sheet = Image.new("RGB", (3 * thumb_w + 4 * gap, 2 * (thumb_h + label_h) + 3 * gap), "#d0d0d0")
    draw = ImageDraw.Draw(sheet)
    for position, (path, im) in enumerate(thumbs):
        row, col = divmod(position, 3)
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        draw.text((x, y), path.stem, fill="black")
        sheet.paste(im, (x, y + label_h))
    end = start + len(chunk)
    sheet.save(CONTACTS / f"contact-{start + 1:03d}-{end:03d}.png", optimize=True)

print(f"pages={len(page_paths)} contacts={math.ceil(len(page_paths)/6)}")
