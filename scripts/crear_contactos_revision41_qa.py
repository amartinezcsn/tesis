"""Crea hojas de contacto para revisar visualmente todas las páginas."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SOURCE = Path(r"C:\Python\tesis\output\revision41_render\pages")
OUTPUT = Path(r"C:\Python\tesis\output\revision41_render\contactos")
OUTPUT.mkdir(parents=True, exist_ok=True)
pages = sorted(SOURCE.glob("page-*.png"))
columns, rows = 5, 4
thumb_width, thumb_height = 190, 246
label_height, gap = 20, 8
font = ImageFont.load_default()

for sheet_index, start in enumerate(range(0, len(pages), columns * rows), 1):
    group = pages[start:start + columns * rows]
    canvas = Image.new("RGB", (columns * (thumb_width + gap) + gap, rows * (thumb_height + label_height + gap) + gap), "#d9d9d9")
    draw = ImageDraw.Draw(canvas)
    for offset, page_path in enumerate(group):
        image = Image.open(page_path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height))
        col, row = offset % columns, offset // columns
        x = gap + col * (thumb_width + gap)
        y = gap + row * (thumb_height + label_height + gap)
        canvas.paste(image, (x + (thumb_width - image.width) // 2, y))
        label = f"Página {start + offset + 1}"
        draw.text((x + 4, y + thumb_height + 3), label, fill="black", font=font)
    canvas.save(OUTPUT / f"contacto-{sheet_index:02d}.png")

print(f"Páginas: {len(pages)}; hojas de contacto: {(len(pages) + columns * rows - 1) // (columns * rows)}")
