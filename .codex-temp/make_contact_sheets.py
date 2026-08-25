from pathlib import Path

from PIL import Image, ImageDraw

root = Path(r"C:\Python\tesis\.codex-temp\rev35-pdf-render")
pages = sorted(root.glob("page-*.png"), key=lambda path: int(path.stem.split("-")[-1]))
output = root / "contact"
output.mkdir(exist_ok=True)

thumb_width, thumb_height, cols, rows = 170, 220, 5, 4
for start in range(0, len(pages), cols * rows):
    group = pages[start : start + cols * rows]
    canvas = Image.new("RGB", (cols * thumb_width, rows * thumb_height), "white")
    draw = ImageDraw.Draw(canvas)
    for index, path in enumerate(group):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height))
        row, column = divmod(index, cols)
        x, y = column * thumb_width, row * thumb_height
        canvas.paste(image, (x, y))
        draw.text((x + 4, y + 4), str(int(path.stem.split("-")[-1])), fill="red", stroke_width=1, stroke_fill="white")
    canvas.save(output / f"sheet-{start // (cols * rows) + 1:02d}.jpg", quality=85)
