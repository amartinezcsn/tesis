from pathlib import Path
from PIL import Image, ImageDraw

source = Path(r"C:\Python\tesis\tmp\rev57_png")
output = Path(r"C:\Python\tesis\tmp\rev57_contacts")
output.mkdir(parents=True, exist_ok=True)
files = sorted(source.glob("page-*.png"))
per_sheet = 6
thumb_w = 510

for start in range(0, len(files), per_sheet):
    group = files[start:start + per_sheet]
    rendered = []
    for path in group:
        image = Image.open(path).convert("RGB")
        height = round(image.height * thumb_w / image.width)
        image = image.resize((thumb_w, height), Image.Resampling.LANCZOS)
        rendered.append((path, image))
    cell_h = max(image.height for _, image in rendered) + 34
    canvas = Image.new("RGB", (thumb_w * 3 + 40, cell_h * 2 + 30), "#d8d8d8")
    draw = ImageDraw.Draw(canvas)
    for i, (path, image) in enumerate(rendered):
        x = 10 + (i % 3) * (thumb_w + 10)
        y = 10 + (i // 3) * cell_h
        canvas.paste(image, (x, y + 24))
        draw.text((x + 4, y + 4), path.stem, fill="black")
    first = start + 1
    last = start + len(group)
    canvas.save(output / f"contact-{first:03d}-{last:03d}.png")
