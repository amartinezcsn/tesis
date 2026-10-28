from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from docx import Document
from pypdf import PdfReader


ROOT = Path(r"C:\Python\tesis")
DOCX = ROOT / "documentacion" / "TESIS_OCT2026_Rev68_(ZUJ)_Final.docx"
PDF = ROOT / "tmp" / "rev68_render" / "TESIS_OCT2026_Rev68_(ZUJ)_Final.pdf"
OUT = ROOT / "tmp" / "rev68_bibliometria" / "auditoria_bibliometrica.json"
CACHE = ROOT / "tmp" / "rev67_bibliometria" / "crossref_cache.json"


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def reference_parts(text: str):
    year_match = re.search(r"\((\d{4})([a-z]?)(?:,[^)]*)?\)", text)
    year = int(year_match.group(1)) if year_match else None
    suffix = year_match.group(2) if year_match else ""
    doi_match = re.search(r"https?://doi\.org/([^\s]+)", text, re.I)
    doi = doi_match.group(1).rstrip(".,)") if doi_match else ""
    before_year = text[: year_match.start()] if year_match else text
    first_author = before_year.split(",", 1)[0].strip().rstrip(".")
    after_year = text[year_match.end():].strip().lstrip(". ") if year_match else ""
    title = after_year.split(". ", 1)[0].strip().rstrip(".")
    return first_author, year, suffix, doi, title


def aliases(first_author: str):
    key = norm(first_author)
    special = {
        "global entrepreneurship monitor": ["global entrepreneurship monitor", "gem"],
        "instituto nacional de estadistica y geografia inegi": ["instituto nacional de estadistica y geografia", "inegi"],
        "oecd": ["oecd", "ocde"],
    }
    if key in special:
        return special[key]
    return [key]


def crossref_get(doi: str, cache: dict):
    if doi in cache:
        return cache[doi]
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(url, headers={
        "User-Agent": "TesisBibliometricAudit/1.0 (mailto:bibliometria@example.invalid)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))["message"]
            result = {"ok": True, "message": payload, "http": response.status}
    except Exception as exc:
        result = {"ok": False, "error": str(exc), "http": getattr(exc, "code", None)}
    cache[doi] = result
    time.sleep(0.08)
    return result


doc = Document(DOCX)
paragraphs = list(doc.paragraphs)
ref_idx = next(i for i, p in enumerate(paragraphs) if p.text.strip() == "REFERENCIAS")
annex_idx = next(i for i, p in enumerate(paragraphs[ref_idx + 1:], ref_idx + 1) if p.text.strip().startswith("Anexo A"))
references = [p.text.strip() for p in paragraphs[ref_idx + 1:annex_idx] if p.text.strip()]
body_text = "\n".join(p.text for p in paragraphs[:ref_idx])
body_norm = norm(body_text)

reader = PdfReader(PDF)
page_texts = [page.extract_text() or "" for page in reader.pages]
ref_physical = next(i + 1 for i, text in enumerate(page_texts) if "REFERENCIAS" in [line.strip() for line in text.splitlines()])
body_pages = page_texts[: ref_physical - 1]
body_page_norm = [norm(text) for text in body_pages]

cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
records = []
for number, reference in enumerate(references, 1):
    first_author, year, suffix, doi, title = reference_parts(reference)
    author_aliases = aliases(first_author)
    year_token = f"{year}{suffix}" if year else ""
    exact_pages = []
    base_pages = []
    for physical, text in enumerate(body_page_norm, 1):
        author_hit = any(alias in text for alias in author_aliases)
        if not author_hit or year is None:
            continue
        if norm(year_token) in text:
            exact_pages.append(physical)
        if str(year) in text:
            base_pages.append(physical)
    physical_pages = exact_pages or base_pages
    printed_pages = sorted({p - 13 for p in physical_pages if p >= 14})
    citation_status = "Citada" if exact_pages else ("Citada sin desambiguación" if base_pages else "No localizada")

    verification = "Sin DOI"
    metadata = {}
    issues = []
    if doi:
        result = crossref_get(doi, cache)
        if result.get("ok"):
            msg = result["message"]
            cr_title = (msg.get("title") or [""])[0]
            cr_container = (msg.get("container-title") or [""])[0]
            cr_authors = msg.get("author") or []
            cr_first = cr_authors[0].get("family", "") if cr_authors else ""
            date_parts = ((msg.get("published-print") or msg.get("published-online") or msg.get("issued") or {}).get("date-parts") or [[None]])[0]
            cr_year = date_parts[0]
            title_score = 1.0 if norm(cr_title) and norm(cr_title) in norm(reference) else SequenceMatcher(None, norm(title), norm(cr_title)).ratio()
            author_match = any(norm(alias) in norm(cr_first) or norm(cr_first) in norm(alias) for alias in author_aliases) if cr_first else first_author in {"OECD"}
            year_match = cr_year == year
            if title_score >= 0.90 and author_match and year_match:
                verification = "Verificada con Crossref"
            elif title_score >= 0.82 and author_match and (year_match or (cr_year and abs(cr_year - year) <= 1)):
                verification = "Verificada con diferencia menor"
                if not year_match:
                    issues.append(f"Año en tesis {year}; Crossref {cr_year}")
            else:
                verification = "Corrección necesaria"
                if title_score < 0.90:
                    issues.append(f"Título difiere de Crossref (similitud {title_score:.2f})")
                if not author_match:
                    issues.append(f"Primer autor difiere de Crossref: {cr_first}")
                if not year_match:
                    issues.append(f"Año en tesis {year}; Crossref {cr_year}")
            metadata = {
                "crossref_title": cr_title,
                "crossref_year": cr_year,
                "crossref_first_author": cr_first,
                "crossref_container": cr_container,
                "crossref_type": msg.get("type", ""),
                "crossref_publisher": msg.get("publisher", ""),
                "crossref_url": msg.get("URL", f"https://doi.org/{doi}"),
                "title_similarity": round(title_score, 3),
            }
        else:
            verification = "DOI no verificado"
            issues.append(result.get("error", "Error no identificado"))
    else:
        url_match = re.search(r"https?://\S+", reference)
        if url_match:
            verification = "URL institucional pendiente de revisión manual"
            metadata["url"] = url_match.group(0).rstrip(".,)")
        else:
            verification = "Libro o informe sin DOI; revisión manual"

    records.append({
        "id": f"REF-{number:02d}", "reference": reference, "first_author": first_author,
        "year": year, "suffix": suffix, "title": title, "doi": doi,
        "citation_status": citation_status, "citation_count_pages": len(printed_pages),
        "citation_pages": printed_pages, "verification": verification,
        "issues": issues, **metadata,
    })

CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

# Citas potencialmente huérfanas: autor/año en el cuerpo que no empata con una referencia.
candidate_pairs = set()
patterns = [
    re.compile(r"([A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’-]+)(?:\s+et\s+al\.)?\s*\((\d{4}[a-z]?)\)"),
    re.compile(r"\(([A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’-]+)(?:\s+(?:&|y)\s+[A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'’-]+|\s+et\s+al\.)?,\s*(\d{4}[a-z]?)"),
]
for pattern in patterns:
    for surname, year_token in pattern.findall(body_text):
        candidate_pairs.add((norm(surname), year_token.lower()))

ref_pairs = set()
for record in records:
    for alias in aliases(record["first_author"]):
        ref_pairs.add((norm(alias).split()[-1], f'{record["year"]}{record["suffix"]}'.lower()))
        ref_pairs.add((norm(alias).split()[-1], str(record["year"])))
orphans = sorted([pair for pair in candidate_pairs if pair not in ref_pairs])

summary = {
    "reference_count": len(records),
    "with_doi": sum(bool(r["doi"]) for r in records),
    "citation_status": dict(Counter(r["citation_status"] for r in records)),
    "verification_status": dict(Counter(r["verification"] for r in records)),
    "orphan_candidates": orphans,
    "reference_heading_physical_page": ref_physical,
}
OUT.write_text(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(OUT)
