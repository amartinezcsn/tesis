from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DATA = json.loads(Path(r"C:\Python\tesis\.pptx_build\thesis_extract.json").read_text(encoding="utf-8"))
paragraphs = DATA["paragraphs"]

print("HEADINGS")
for p in paragraphs:
    style = p["style"].lower()
    text = p["text"]
    if "heading" in style or "título" in style or "titulo" in style:
        print(f'{p["index"]:04d}\t{p["style"]}\t{text}')

terms = [
    "pregunta de investigación",
    "objetivo general",
    "hipótesis",
    "conclusiones",
    "resultado",
    "rmse",
    "mape",
    "lstm",
    "rnn",
    "híbr",
    "rolling-origin",
    "rolling origin",
    "sistema de soporte",
]

print("\nKEYWORD CONTEXT")
for term in terms:
    print(f"\n## {term}")
    found = 0
    for pos, p in enumerate(paragraphs):
        if term.casefold() in p["text"].casefold():
            lo = max(0, pos - 1)
            hi = min(len(paragraphs), pos + 3)
            for q in paragraphs[lo:hi]:
                print(f'{q["index"]:04d}\t{q["style"]}\t{q["text"]}')
            print()
            found += 1
            if found >= 8:
                break

print("\nMETRIC TABLES")
for table in DATA["tables"]:
    flat = " | ".join(" | ".join(row) for row in table["rows"])
    low = flat.casefold()
    if any(term in low for term in ("rmse", "mape", "mae", "lstm", "rnn", "elastic", "ridge", "lasso")):
        print(f'\nTABLE {table["index"]}')
        for row in table["rows"][:14]:
            print(" || ".join(row))
