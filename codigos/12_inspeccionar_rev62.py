from docx import Document

p = r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev62_(ZUJ)_Final.docx"
d = Document(p)
for i, x in enumerate(d.paragraphs):
    if 230 <= i <= 275 or 390 <= i <= 470:
        text = " ".join(x.text.split())
        line = f"{i}\t{x.style.name if x.style else ''}\t{text[:300]}"
        print(line.encode("cp1252", "replace").decode("cp1252"))
