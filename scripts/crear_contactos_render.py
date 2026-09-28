from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path("tmp/render_rev54_estado_arte")
FILES = sorted(
    ROOT.glob("page-*.png"),
    key=lambda path: int(path.stem.split("-")[-1]),
)

for offset in range(0, len(FILES), 9):
    canvas = Image.new("RGB", (1530, 2100), "#d8d8d8")
    draw = ImageDraw.Draw(canvas)
    for index, path in enumerate(FILES[offset : offset + 9]):
        image = Image.open(path).convert("RGB")
        image.thumbnail((490, 650))
        x = (index % 3) * 510 + (500 - image.width) // 2
        y = (index // 3) * 690 + 30
        canvas.paste(image, (x, y))
        draw.text((index % 3 * 510 + 10, index // 3 * 690 + 8), path.stem, fill="black")
    output = ROOT / f"contact-{offset // 9 + 1:02d}.jpg"
    canvas.save(output, quality=88)
    print(output)
