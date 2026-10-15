from pathlib import Path
import sys
from PIL import Image, ImageDraw

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Python\tesis\tmp\rev62_render_1")
files = sorted(root.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
for offset in range(0, len(files), 12):
    batch = files[offset:offset + 12]
    canvas = Image.new("RGB", (1800, 2400), "#d8d8d8")
    draw = ImageDraw.Draw(canvas)
    for j, path in enumerate(batch):
        img = Image.open(path).convert("RGB")
        img.thumbnail((420, 700))
        x = (j % 4) * 450 + (420 - img.width) // 2
        y = (j // 4) * 800 + 45
        canvas.paste(img, (x, y))
        draw.text((j % 4 * 450 + 12, j // 4 * 800 + 12), path.stem, fill="black")
    canvas.save(root / f"contact-{offset // 12 + 1:02d}.jpg", quality=90)
print(len(files), "pages", (len(files) + 11) // 12, "contact sheets")
