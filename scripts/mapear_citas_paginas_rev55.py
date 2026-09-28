import json
import os
import re
import unicodedata
from pathlib import Path

import pdfplumber


INVENTORY = Path(os.environ.get("AUDIT_INVENTORY", "tmp/auditoria_rev55/inventario_citas.json"))
PDF = Path(os.environ.get("AUDIT_PDF", "tmp/auditoria_rev55/Rev55.pdf"))
OUTPUT = Path(os.environ.get("AUDIT_MAPPED", "tmp/auditoria_rev55/citas_con_paginas.json"))


def normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().replace("‐", "-").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9%]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def anchors(text, width=7):
    words = normalize(text).split()
    if len(words) <= width:
        return [" ".join(words)] if words else []
    starts = sorted(set([0, max(0, len(words) // 4), max(0, len(words) // 2), max(0, 3 * len(words) // 4), len(words) - width]))
    return [" ".join(words[start : start + width]) for start in starts]


def printed_page(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if re.fullmatch(r"\d{1,3}", line):
            return int(line)
    return None


def main():
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    with pdfplumber.open(PDF) as book:
        raw_pages = [page.extract_text() or "" for page in book.pages]
    pages = [normalize(text) for text in raw_pages]
    printed = [printed_page(text) for text in raw_pages]

    last_page = 0
    unmatched = []
    ambiguous = []
    for item in data["citation_paragraphs"]:
        text = item.get("context_text") or item["text"]
        item_anchors = anchors(text)
        scores = []
        for page_index, page in enumerate(pages):
            score = sum(1 for anchor in item_anchors if anchor and anchor in page)
            if score:
                scores.append((score, page_index))
        if scores:
            best_score = max(score for score, _ in scores)
            candidates = [page for score, page in scores if score == best_score]
            forward = [page for page in candidates if page >= max(0, last_page - 1)]
            chosen = min(forward, key=lambda page: abs(page - last_page)) if forward else min(candidates, key=lambda page: abs(page - last_page))
            if len(candidates) > 1:
                ambiguous.append((item["paragraph_index"], [page + 1 for page in candidates], best_score))
        else:
            chosen = last_page
            unmatched.append(item["paragraph_index"])
        last_page = max(last_page, chosen)
        item["pdf_page"] = chosen + 1
        item["printed_page"] = printed[chosen]

    per_page = {}
    for item in data["citation_paragraphs"]:
        key = item["pdf_page"]
        per_page[key] = per_page.get(key, 0) + 1
        item["citation_paragraph_on_page"] = per_page[key]

    data["mapping_diagnostics"] = {"unmatched": unmatched, "ambiguous": ambiguous}
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"mapped={len(data['citation_paragraphs'])}")
    print(f"unmatched={unmatched}")
    print(f"ambiguous_count={len(ambiguous)}")
    print("first_last", data["citation_paragraphs"][0]["pdf_page"], data["citation_paragraphs"][-1]["pdf_page"])


if __name__ == "__main__":
    main()
