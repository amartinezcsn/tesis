import difflib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


INPUT = Path("tmp/auditoria_rev56/citas_con_paginas.json")
OLD_AUDIT = Path("tmp/auditoria_rev55/auditoria_clasificada.json")
OUTPUT = Path("tmp/auditoria_rev56/auditoria_clasificada.json")


def norm(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("‐", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


URL_RULES = [
    ("hyndman & athanasopoulos", "https://otexts.com/fpp3/"),
    ("hyndman y athanasopoulos", "https://otexts.com/fpp3/"),
    ("hyndman & koehler", "https://doi.org/10.1016/j.ijforecast.2006.03.001"),
    ("hyndman et al.", "https://doi.org/10.1016/j.csda.2011.03.006"),
    ("huber y stuckenschmidt", "https://doi.org/10.1016/j.ijforecast.2020.02.005"),
    ("hubner et al.", "https://doi.org/10.1111/jiec.13528"),
    ("abrar et al.", "https://doi.org/10.48550/arXiv.2405.15598"),
    ("giannopoulos et al.", "https://doi.org/10.1080/00207543.2025.2578701"),
    ("spiliotis et al.", "https://doi.org/10.1007/s12351-020-00605-2"),
    ("syntetos", "https://doi.org/10.1016/j.ijforecast.2004.10.001"),
    ("bates & granger", "https://doi.org/10.2307/3008764"),
    ("aitchison", "https://doi.org/10.1111/j.2517-6161.1982.tb01195.x"),
    ("breiman", "https://doi.org/10.1023/A:1010933404324"),
    ("friedman", "https://doi.org/10.1214/aos/1013203451"),
    ("zhang", "https://doi.org/10.1016/S0925-2312(01)00702-0"),
    ("tashman", "https://doi.org/10.1016/S0169-2070(00)00065-0"),
    ("shmueli", "https://doi.org/10.1214/10-STS330"),
    ("poveda", "https://doi.org/10.3390/su18073603"),
    ("valdez-juarez", "https://doi.org/10.1142/S0219649218500077"),
    ("garcia-perez-de-lema y maldonado-guzman", "https://doi.org/10.1142/S0219649218500077"),
    ("maldonado-guzman y garza-reyes", "https://doi.org/10.1108/IJIS-10-2019-0094"),
]


MANUAL_RULES = [
    (
        "una planificacion inadecuada de la demanda en el sector de panaderia",
        "Coincide",
        "Hübner sustenta las tasas de devolución y la reducción de desperdicio; Makridakis y Spiliotis respaldan que la complejidad no garantiza superioridad y que el desempeño debe evaluarse empíricamente.",
        "Conservar. La afirmación quedó separada y ajustada al alcance de las fuentes.",
    ),
    (
        "las aplicaciones descritas se han estudiado principalmente",
        "Coincidencia parcial",
        "Poveda-Valverde y Fierro Barragán respaldan las barreras de infraestructura, presupuesto y talento; la limitada evidencia específica en repostería creativa es una síntesis de la revisión realizada.",
        "Conservar indicando que la limitación sectorial corresponde al resultado de la búsqueda documental.",
    ),
    (
        "mediante una revision sistematica de aplicaciones de inteligencia artificial en pymes latinoamericanas",
        "Coincide",
        "La revisión sistemática citada documenta barreras de infraestructura tecnológica, recursos financieros y talento especializado en PYMES latinoamericanas.",
        "Conservar.",
    ),
    (
        "valdez-juarez, garcia-perez-de-lema y maldonado-guzman (2018) analizaron datos",
        "Coincide",
        "La publicación estudia 412 PYMES industriales y de servicios del noroeste de México y relaciona TIC, gestión del conocimiento, innovación y rentabilidad.",
        "Conservar.",
    ),
    (
        "maldonado-guzman y garza-reyes (2020) estudiaron la adopcion de practicas de ecoinnovacion",
        "Coincide",
        "La redacción describe correctamente el estudio sobre adopción de ecoinnovación en la industria automotriz y delimita que no aborda transformación digital ni pronósticos.",
        "Conservar.",
    ),
    (
        "valdez-juarez et al. (2018) | mexico | tic; gestion del conocimiento",
        "Coincide",
        "La fila resume de forma consistente el contexto, método y resultados del estudio verificable de Valdez-Juárez et al.",
        "Conservar.",
    ),
    (
        "maldonado-guzman y garza-reyes (2020) | mexico | ecoinnovacion",
        "Coincide",
        "La fila refleja el tema, sector y alcance real de la publicación sobre ecoinnovación automotriz.",
        "Conservar.",
    ),
    (
        "en el ambito latinoamericano, la adopcion de soluciones basadas en inteligencia artificial",
        "Coincide",
        "La fuente respalda las barreras de infraestructura, presupuesto y talento en la adopción de IA por PYMES latinoamericanas.",
        "Conservar.",
    ),
    (
        "los antecedentes revisados muestran que los resultados obtenidos en organizaciones con capacidades analiticas",
        "Coincidencia parcial",
        "Mikalef respalda el papel de las capacidades analíticas y Poveda-Valverde las barreras regionales; la conclusión sobre transferencia a microempresas es una inferencia explícita de la revisión.",
        "Conservar como síntesis, evitando presentarla como resultado textual de una sola fuente.",
    ),
    (
        "esta investigacion propone generar evidencia sobre el uso de herramientas de pronostico semanal",
        "Coincidencia parcial",
        "Poveda-Valverde respalda las barreras de adopción; la elección de evaluar modelos con los datos disponibles es una decisión del estudio.",
        "Conservar distinguiendo la evidencia externa de la decisión metodológica propia.",
    ),
]


def urls_for(citation_text):
    lowered = norm(citation_text)
    urls = []
    for needle, url in URL_RULES:
        if norm(needle) in lowered and url not in urls:
            urls.append(url)
    return " | ".join(urls)


def manual_classification(text):
    normalized = norm(text)
    for needle, status, rationale, action in MANUAL_RULES:
        if needle in normalized:
            return status, rationale, action
    return None


def manual_section(text):
    normalized = norm(text)
    if "una planificacion inadecuada de la demanda en el sector de panaderia" in normalized:
        return "Introducción"
    if any(
        needle in normalized
        for needle in [
            "las aplicaciones descritas se han estudiado principalmente",
            "mediante una revision sistematica de aplicaciones de inteligencia artificial en pymes latinoamericanas",
            "valdez-juarez, garcia-perez-de-lema y maldonado-guzman (2018) analizaron datos",
            "maldonado-guzman y garza-reyes (2020) estudiaron la adopcion de practicas de ecoinnovacion",
            "valdez-juarez et al. (2018) | mexico | tic; gestion del conocimiento",
            "maldonado-guzman y garza-reyes (2020) | mexico | ecoinnovacion",
        ]
    ):
        return "Estado del Arte"
    if any(
        needle in normalized
        for needle in [
            "en el ambito latinoamericano, la adopcion de soluciones basadas en inteligencia artificial",
            "los antecedentes revisados muestran que los resultados obtenidos en organizaciones con capacidades analiticas",
        ]
    ):
        return "Síntesis del estado del arte y planteamiento del problema"
    if "esta investigacion propone generar evidencia sobre el uso de herramientas de pronostico semanal" in normalized:
        return "Justificación"
    return ""


def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    old_data = json.loads(OLD_AUDIT.read_text(encoding="utf-8"))
    old_rows = old_data["audit_rows"]
    exact_old = {norm(row["paragraph_text"]): row for row in old_rows}

    rows = []
    status_counts = Counter()
    unique = defaultdict(lambda: {"count": 0, "pdf_pages": set(), "printed_pages": set(), "statuses": [], "urls": set()})

    for order, item in enumerate(data["citation_paragraphs"], start=1):
        context = item.get("context_text") or item["text"]
        citation_text = "; ".join(c["raw"] for c in item["citations"])
        manual = manual_classification(context)
        old = None
        if manual:
            status, rationale, action = manual
            section = manual_section(context)
        else:
            old = exact_old.get(norm(context))
            if old is None:
                old = max(old_rows, key=lambda row: difflib.SequenceMatcher(None, norm(context), norm(row["paragraph_text"])).ratio())
                score = difflib.SequenceMatcher(None, norm(context), norm(old["paragraph_text"])).ratio()
                if score < 0.92:
                    raise RuntimeError(f"Unclassified changed paragraph {item['paragraph_index']} with similarity {score:.3f}: {context[:180]}")
            status = old["status"]
            rationale = old["rationale"].replace("Rev55", "Rev56")
            action = old["recommended_action"]
            section = old["section"]

        status_counts[status] += 1
        row = {
            "id": order,
            "pdf_page": item["pdf_page"],
            "printed_page": item.get("printed_page"),
            "citation_paragraph_on_page": item.get("citation_paragraph_on_page"),
            "docx_paragraph": item["paragraph_index"],
            "location": "Fila de tabla" if item.get("container") == "table_row" else "Párrafo",
            "section": section,
            "citations": citation_text,
            "paragraph_text": context,
            "status": status,
            "rationale": rationale,
            "recommended_action": action,
            "source_urls": urls_for(citation_text),
        }
        rows.append(row)

        for citation in item["citations"]:
            label = citation["raw"]
            bucket = unique[label]
            bucket["count"] += 1
            bucket["pdf_pages"].add(item["pdf_page"])
            if item.get("printed_page") is not None:
                bucket["printed_pages"].add(item["printed_page"])
            bucket["statuses"].append(status)
            for url in urls_for(label).split(" | "):
                if url:
                    bucket["urls"].add(url)

    severity = {"Coincide": 0, "Coincidencia parcial": 1, "No trazable": 2, "No coincide": 3}
    unique_rows = []
    for label, bucket in sorted(unique.items(), key=lambda pair: (-pair[1]["count"], pair[0])):
        unique_rows.append(
            {
                "citation": label,
                "count": bucket["count"],
                "pdf_pages": ", ".join(map(str, sorted(bucket["pdf_pages"]))),
                "printed_pages": ", ".join(map(str, sorted(bucket["printed_pages"]))),
                "worst_status": max(bucket["statuses"], key=lambda value: severity[value]),
                "urls": " | ".join(sorted(bucket["urls"])),
            }
        )

    old_bib = {norm(item["entry"]): item for item in old_data["bibliography_audit"]}
    bibliography = []
    for number, entry in enumerate(data["references"], start=1):
        text = entry["text"]
        first_author = text.split(",", 1)[0].strip()
        years = re.findall(r"\((\d{4}[a-z]?)\)", text)
        year = years[0] if years else ""
        all_citation_text = " ".join(row["citations"] for row in rows)
        count = len(re.findall(re.escape(norm(first_author)), norm(all_citation_text))) if first_author else 0
        if year and year not in all_citation_text:
            count = 0

        if "researchgate.net/publication/370666295" in norm(text):
            metadata_status = "Fuente débil"
            issue = "Se conservó una sola entrada, pero solo se identificó el registro de ResearchGate y no una publicación primaria con datos editoriales completos."
        elif norm(text) in old_bib:
            previous = old_bib[norm(text)]
            metadata_status = previous["metadata_status"]
            issue = previous["issue"].replace("Rev55", "Rev56")
        elif "10.1108/IJIS-10-2019-0094" in text or "10.1142/S0219649218500077" in text:
            metadata_status = "Verificada"
            issue = "Autores, título, publicación y DOI coinciden con registros académicos localizables."
        else:
            metadata_status = "Revisar"
            issue = "Entrada nueva o modificada que requiere comprobación bibliográfica adicional."
        bibliography.append(
            {
                "number": number,
                "entry": text,
                "cited_estimate": count,
                "metadata_status": metadata_status,
                "issue": issue,
            }
        )

    hyndman_rows = [
        row
        for row in rows
        if "hyndman & athanasopoulos" in norm(row["citations"])
        or "hyndman y athanasopoulos" in norm(row["citations"])
    ]
    bibliography_known_issues = sum(
        1 for row in bibliography if row["metadata_status"] not in {"Sin anomalía evidente", "Preferida", "Verificada"}
    )
    data.update(
        {
            "audit_rows": rows,
            "unique_citations": unique_rows,
            "bibliography_audit": bibliography,
            "hyndman_rows": hyndman_rows,
            "missing_sources": [
                "Global Entrepreneurship Monitor (GEM, 2023)",
                "Instituto Nacional de Estadística y Geografía (INEGI, 2023)",
            ],
            "summary": {
                "citation_paragraphs": len(rows),
                "citation_groups": sum(len(item["citations"]) for item in data["citation_paragraphs"]),
                "unique_raw_citations": len(unique_rows),
                "hyndman_2021_occurrences": len(hyndman_rows),
                "status_counts": dict(status_counts),
                "bibliography_entries": len(bibliography),
                "bibliography_known_issues": bibliography_known_issues,
            },
        }
    )
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
