from pathlib import Path

from PIL import Image, ImageDraw


OUT = Path(r"C:\Python\tesis\.codex-temp\rev34-pdf-qa")
files = sorted(OUT.glob("page-*.png"))
width, height = 460, 595
cols, rows = 3, 3

for start in range(0, len(files), cols * rows):
    canvas = Image.new("RGB", (cols * width, rows * height), "white")
    draw = ImageDraw.Draw(canvas)
    for index, image_path in enumerate(files[start : start + cols * rows]):
        image = Image.open(image_path).convert("RGB").resize((width, height))
        x = (index % cols) * width
        y = (index // cols) * height
        canvas.paste(image, (x, y))
        draw.text((x + 8, y + 8), f"Página {start + index + 1}", fill="red", stroke_width=1, stroke_fill="white")
    canvas.save(OUT / f"contact-{start // (cols * rows) + 1:02d}.jpg", quality=90)
