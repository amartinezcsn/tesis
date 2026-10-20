from pathlib import Path
import sys
from PIL import Image, ImageDraw

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Python\tesis\tmp\rev64_render_1")
files = sorted(OUT.glob("page-*.png"))
width, height = 410, 530
cols, rows = 4, 4
for start in range(0, len(files), cols * rows):
    canvas = Image.new("RGB", (cols * width, rows * height), "white")
    draw = ImageDraw.Draw(canvas)
    for index, image_path in enumerate(files[start:start + cols * rows]):
        image = Image.open(image_path).convert("RGB").resize((width, height))
        x = (index % cols) * width
        y = (index // cols) * height
        canvas.paste(image, (x, y))
        draw.text((x + 7, y + 7), f"Página {start + index + 1}", fill="red", stroke_width=1, stroke_fill="white")
    canvas.save(OUT / f"contact-{start // (cols * rows) + 1:02d}.jpg", quality=90)
print(len(files))
