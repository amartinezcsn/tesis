import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


INPUT = Path("tmp/auditoria_rev55/citas_con_paginas.json")
OUTPUT = Path("tmp/auditoria_rev55/auditoria_clasificada.json")


def norm(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def section_for(index):
    if index < 204:
        return "Introducción"
    if index < 428:
        return "Estado del Arte"
    if index < 442:
        return "Síntesis del estado del arte y planteamiento del problema"
    if index < 459:
        return "Contexto del caso de estudio"
    if index < 476:
        return "Justificación"
    if index < 680:
        return "Marco teórico"
    if index >= 1000:
        return "Discusión"
    return "Capítulos metodológicos y de resultados"


NO_TRACE = {
    192: ("La afirmación es plausible, pero GEM (2023) no aparece en la lista de referencias de la Rev55.", "Agregar la referencia completa y precisar el informe/página utilizados."),
    196: ("La cifra de empresas y empleo se atribuye a INEGI (2023), pero la obra no aparece en la bibliografía.", "Agregar el documento/tabulado exacto de INEGI y verificar las cifras y el universo estadístico."),
    234: ("Maldonado Guzmán, Pinzón Castro y García Pérez de Lema (2018) no figura en la bibliografía.", "Incorporar la referencia completa o sustituirla por una fuente localizable."),
    236: ("Maldonado Guzmán y Garza Reyes (2020) no figura en la bibliografía.", "Incorporar la referencia completa o eliminar la atribución."),
    362: ("La fila de la tabla cita Maldonado-Guzmán et al. (2018), obra ausente en la bibliografía.", "Agregar la referencia completa y comprobar el alcance del estudio."),
    378: ("La fila de la tabla cita Maldonado-Guzmán y Garza-Reyes (2020), obra ausente en la bibliografía.", "Agregar la referencia completa y comprobar el alcance del estudio."),
}

NO_MATCH = {
    197: ("El informe OECD/OCDE citado trata digitalización y escalamiento de PYMES, pero no se localizó sustento para la cifra exacta de menos de 25% de microempresas con analítica avanzada en países en desarrollo.", "Eliminar la cifra o reemplazarla por un dato con tabla y página verificables."),
    198: ("Hübner sustenta tasas de devolución y reducción de desperdicio; la segunda afirmación sobre crecimiento, expansión e inversión no queda demostrada por las otras obras. Además, el DOI asignado a Cao et al. (2025) pertenece a otro artículo.", "Separar las afirmaciones, conservar Hübner para devoluciones y retirar/reemplazar Cao et al."),
    217: ("Syntetos y Boylan (2005) evalúan estimadores de demanda intermitente, pero no sustentan por sí solos toda la clasificación ADI-CV² ni el método TSB, desarrollado posteriormente.", "Citar la fuente específica de la clasificación y la publicación original de TSB."),
    226: ("La referencia Alekseeva et al. (2021) no es verificable con los datos aportados: el DOI 10.3390/su131910663 corresponde a un estudio de conservación comunitaria en Namibia.", "Sustituir por una fuente real sobre barreras de adopción de IA en PYMES."),
    229: ("La obra atribuida a Alekseeva, Ginevičius y Stankevičienė no pudo verificarse y el DOI de la bibliografía corresponde a otro tema.", "Reemplazar la cita y corregir la bibliografía."),
    354: ("La fuente Alekseeva et al. (2021) de la tabla no es trazable; el DOI registrado pertenece a otro artículo.", "Rehacer la fila con una fuente verificable."),
    436: ("La afirmación depende de Alekseeva et al. (2021), cuya referencia y DOI no corresponden a un estudio de adopción de IA en PYMES.", "Reemplazar la cita por evidencia verificable."),
    439: ("Mikalef et al. (2020) no aparece correctamente identificado en la bibliografía y Alekseeva et al. tiene un DOI ajeno. Las fuentes listadas no sostienen de forma trazable el vacío afirmado.", "Corregir Mikalef 2020 y sustituir Alekseeva; documentar el vacío con una revisión verificable."),
    440: ("Dubey estudia analítica/IA y desempeño en manufactura; Hyndman trata pronósticos. Ninguna fuente demuestra que la integración ingresos-inventarios sea escasamente abordada en microempresas.", "Añadir una revisión específica sobre integración de pronóstico e inventarios en microempresas o reformular como vacío por investigar."),
    442: ("García-Pérez et al. (2020) revisan gestión del conocimiento en organizaciones intensivas en conocimiento, no prácticas de decisión de propietarios de MIPYMES.", "Usar una fuente centrada en toma de decisiones y conocimiento tácito en MIPYMES."),
    459: ("La cita combina una referencia Alekseeva no verificable y una mención de Poveda-Valverde sin año.", "Corregir la cita a Poveda-Valverde y Fierro Barragán (2026) y retirar/reemplazar Alekseeva."),
    658: ("Hyndman y Athanasopoulos no desarrollan la métrica de error composicional ponderada propuesta ni la regla específica para totales cero.", "Presentar el procedimiento como decisión metodológica propia y respaldar la parte composicional con Aitchison u otra fuente especializada."),
}

PARTIAL = {
    193: ("El contenido sobre aprendizaje emprendedor y prueba iterativa es compatible con las obras, pero Minniti y Bygrave está fechado como 2018 aunque el DOI y el volumen corresponden a 2001.", "Corregir el año de Minniti y Bygrave y revisar la edición citada."),
    194: ("OECD sustenta brechas de digitalización/capacidades y Kantis condiciones emprendedoras; el párrafo extiende ese respaldo a pronóstico de demanda e inventarios sin evidencia específica.", "Separar la afirmación general de capacidades de las afirmaciones operativas y citar fuentes específicas."),
    195: ("El informe del BID puede respaldar aprendizaje y desafíos emprendedores, pero los efectos concretos de errores, desperdicio y baja productividad requieren ubicación o fuente más directa.", "Agregar página/sección del informe o moderar la afirmación."),
    204: ("Hübner et al. documentan reducción de devoluciones/desperdicio asociada a Foodforecast, pero no realizan una evaluación directa de precisión del pronóstico como afirma el párrafo.", "Eliminar la afirmación de mejora de precisión o citar un estudio que mida error predictivo."),
    210: ("Spiliotis et al. comparan métodos estadísticos y de ML en SKU diarios y respaldan la cautela sobre superioridad; no sustentan directamente la agregación semanal de registros de una microempresa.", "Mantener la cita para la comparación de modelos y citar aparte la agregación/intermitencia."),
    216: ("Hyndman y Athanasopoulos respaldan caracterización previa, patrones y evaluación temporal; no desarrollan de forma directa el riesgo de que una arquitectura de IA aprenda huecos de captura en small data.", "Dividir el párrafo y añadir una fuente sobre datos faltantes/fuga de información en ML."),
    220: ("Borsato sustenta la dimensión estética y artística de la repostería; la evolución sectorial y el valor comercial/experiencial se presentan con mayor amplitud que la evidencia localizada.", "Acotar el texto a estética y creatividad o añadir una fuente sectorial económica."),
    224: ("Mikalef y Dubey relacionan capacidades analíticas/dinámicas con innovación y desempeño, pero no estudian específicamente panadería ni todas las mejoras operativas enumeradas.", "Presentar la aplicación al sector alimentario como inferencia y citar Aprodu para el contexto panadero."),
    239: ("Poveda-Valverde y Fierro Barragán respaldan barreras de infraestructura, presupuesto y talento en PYMES latinoamericanas; la concentración exacta en logística, manufactura y telecomunicaciones requiere matiz.", "Conservar las barreras y ajustar la enumeración sectorial a lo reportado en la revisión."),
    266: ("El preprint MCDFN respalda la arquitectura y el desempeño comparativo; la bibliografía duplica la obra y la presenta además como artículo de Expert Systems with Applications sin datos verificables.", "Conservar una sola entrada como preprint arXiv y actualizar si existe publicación formal."),
    298: ("La revisión respalda intermitencia, ajuste, métricas y partición; la etiqueta small data es una interpretación razonable, no una conclusión textual única.", "Mantener la cita y formular small data como condición del caso."),
    402: ("La revisión latinoamericana respalda barreras de adopción; la afirmación sobre concentración sectorial debe ajustarse a las categorías efectivamente sintetizadas.", "Precisar los sectores/categorías con base en la tabla de resultados de la revisión."),
    434: ("Góngora Chonillo aborda riesgo financiero e IA en microempresas, pero el párrafo añade generalizaciones sobre demanda, cadena de suministro y ausencia de modelos predictivos.", "Acotar la afirmación al riesgo financiero o añadir fuentes específicas para demanda y cadena de suministro."),
    435: ("Hyndman y Athanasopoulos explican el valor de pronosticar para decisiones; no sustentan literalmente que errores sistemáticos produzcan sobrecostos y desabasto en microempresas alimentarias.", "Conservar la relación general y citar literatura de inventarios para costos y faltantes."),
    438: ("Mikalef et al. respaldan capacidades de analítica y desempeño, pero la carencia de capital humano y la baja absorción tecnológica de empresas pequeñas no son el foco directo del estudio.", "Añadir una fuente de adopción tecnológica en PYMES."),
    476: ("Las fuentes cubren pronóstico y soporte a decisiones, pero la cita al final intenta respaldar el temario completo, incluida composición porcentual y small data.", "Eliminar la cita global o distribuir referencias específicas en los apartados correspondientes."),
    480: ("El libro respalda métodos de juicio, variables conocidas y evaluación temporal; la conservación del momento de disponibilidad es una regla metodológica derivada.", "Presentar la última oración como criterio del estudio o añadir una fuente sobre data leakage."),
    498: ("La fuente respalda frecuencia/horizonte y agregación; no documenta la delimitación particular entre importes, recetas, existencias y unidades físicas de Cup&Cake.", "Citar solo la regla general y presentar la delimitación aplicada como decisión propia."),
    501: ("La definición de serie y frecuencia es compatible con la fuente; la distinción entre ausencia de compra y ausencia de registro es una decisión de calidad de datos del caso.", "Añadir una fuente sobre datos faltantes o explicitar que es una regla de depuración propia."),
    518: ("La fuente sustenta diagnósticos y evaluación temporal; la selección de características con toda la serie como fuga de información requiere una referencia más específica.", "Añadir una fuente sobre leakage o validación anidada en series temporales."),
    524: ("Las fuentes respaldan Croston y el tratamiento cuidadoso de atípicos; la distinción concreta entre error y compra extraordinaria depende de auditoría del caso.", "Presentar la distinción como procedimiento de auditoría y no como hallazgo de la fuente."),
    542: ("La descripción de ARIMA y residuos es correcta; la conclusión sobre microempresas es una inferencia del autor, no una proposición de la fuente.", "Separar la explicación técnica de la inferencia contextual."),
    548: ("Breiman respalda Random Forest e interacciones; no cubre la ingeniería temporal ni reglas de disponibilidad futura en pronóstico.", "Añadir una fuente de ML para series temporales o presentar esas reglas como diseño propio."),
    553: ("Friedman respalda boosting, tasa de aprendizaje y etapas; el optimismo por ajustar sobre el bloque final pertenece a validación temporal, no al artículo de boosting.", "Agregar una referencia de evaluación fuera de muestra."),
    555: ("Hyndman y Athanasopoulos cubren redes autorregresivas, pero no respaldan íntegramente la descripción de RNN ni la conclusión sobre small data y definición de modelo híbrido.", "Citar Hewamalage et al. para RNN y dejar la delimitación del híbrido como definición propia."),
    556: ("Kuhn y Johnson respaldan selección y ajuste dentro del entrenamiento; la exigencia de que cada familia responda una pregunta conceptual es criterio de diseño del estudio.", "Separar el criterio propio del respaldo metodológico."),
    577: ("Las fuentes respaldan la estructura híbrida y la diferencia entre residuales de ajuste y errores genuinos; la implementación concreta en Cup&Cake es una decisión metodológica propia.", "Mantener las citas y distinguir explícitamente evidencia externa de adaptación local."),
    625: ("La fuente respalda Fourier y estacionalidad; la conversión de calendario diario a semanas y el límite de interacciones son decisiones aplicadas al tamaño de muestra.", "Presentar esas decisiones como criterios del estudio."),
    645: ("La fuente respalda interpretación de RMSE/MAE; la fijación previa del criterio de H1 es una regla de protocolo no desarrollada por el libro.", "Citar la fuente solo para métricas y presentar la regla de decisión como protocolo propio."),
    659: ("Shmueli y Tashman respaldan separar predicción, evaluación fuera de muestra y explicación; no definen el criterio conjunto particular de H1.", "Distinguir el criterio de la hipótesis como decisión del estudio."),
    670: ("Power respalda el papel de los sistemas de soporte a decisiones; no equipara de forma específica precisión, costos de implementación y retorno de inversión.", "Presentar la distinción económica como delimitación propia o añadir una fuente de evaluación de beneficios."),
    673: ("Hyndman et al. respaldan coherencia jerárquica y evaluación fuera de muestra; el problema composicional requiere además una fuente especializada.", "Añadir Aitchison u otra referencia de datos composicionales."),
    674: ("Shmueli sustenta la diferencia entre explicar y predecir, pero no el criterio específico de confirmación conjunta de H1.", "Presentar la regla de confirmación como definición previa del estudio."),
}

URL_RULES = [
    ("hyndman & athanasopoulos", "https://otexts.com/fpp3/"),
    ("hyndman y athanasopoulos", "https://otexts.com/fpp3/"),
    ("hyndman & koehler", "https://doi.org/10.1016/j.ijforecast.2006.03.001"),
    ("hyndman et al.", "https://doi.org/10.1016/j.csda.2011.03.006"),
    ("huber y stuckenschmidt", "https://doi.org/10.1016/j.ijforecast.2020.02.005"),
    ("hubner et al.", "https://doi.org/10.1111/jiec.13528"),
    ("hübner et al.", "https://doi.org/10.1111/jiec.13528"),
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
    ("alekseeva", "https://doi.org/10.3390/su131910663"),
    ("cao et al.", "https://doi.org/10.3390/analytics4010003"),
]

BIB_ISSUES = {
    2: ("Duplicada/incompleta", "Duplica la obra de Abrar del registro 3 y la presenta como artículo de Expert Systems with Applications sin volumen, páginas ni DOI editorial."),
    3: ("Preferida", "Entrada trazable como preprint arXiv; conservar una sola versión."),
    6: ("DOI incorrecto", "El DOI 10.3390/su131910663 corresponde a un artículo sobre conservación comunitaria en Namibia, no a adopción de IA en PYMES."),
    7: ("No verificable", "No se localizó de forma confiable la obra con ese título/autores; además duplica temáticamente el registro 6."),
    8: ("No verificable", "Referencia genérica sin DOI/editorial precisa; no fue posible identificar la obra exacta."),
    10: ("Datos insuficientes", "La URL remite al sitio institucional, no al informe específico citado."),
    15: ("No verificable", "No se localizó la obra exacta con esos autores, título y revista."),
    23: ("DOI incorrecto", "El DOI 10.3390/analytics4010003 corresponde a Golshan et al., sobre inteligencia competitiva en startups."),
    31: ("No verificable", "Entrada sin volumen, número, páginas ni DOI; no se localizó la obra exacta."),
    36: ("Metadatos incorrectos", "El artículo es International Journal of Forecasting 36(4), 1420-1438; no volumen 135 ni artículo 113322."),
    42: ("No verificable", "Entrada incompleta; no se localizó esa obra exacta en Journal of Forecasting."),
    55: ("Año por corregir", "La obra de Information & Management 57(2), 103169 se cita habitualmente como 2020, no 2019."),
    56: ("Año incorrecto", "El DOI y el volumen corresponden al artículo publicado en 2001, no 2018."),
    60: ("Duplicada", "Duplica el registro 59 de OECD/OCDE (2022)."),
    65: ("Duplicada/incompleta", "Duplica el registro 66 y carece de datos editoriales verificables."),
    66: ("Fuente débil", "Registro de ResearchGate sin publicación primaria identificada."),
    68: ("Datos insuficientes", "Entrada sin autores completos, volumen, páginas ni DOI."),
}


def urls_for(citation_text):
    lowered = norm(citation_text)
    urls = []
    for needle, url in URL_RULES:
        if norm(needle) in lowered and url not in urls:
            urls.append(url)
    return " | ".join(urls)


def default_rationale(citations):
    c = norm(citations)
    if "hyndman & athanasopoulos" in c or "hyndman y athanasopoulos" in c:
        return "La afirmación técnica se encuentra dentro del alcance del manual de pronóstico y series temporales citado."
    if "makridakis" in c:
        return "La afirmación coincide con los resultados y el alcance comparativo de la competencia M4."
    if "power" in c:
        return "La afirmación corresponde al uso de sistemas de soporte para organizar información y apoyar, no sustituir, decisiones."
    return "La afirmación central es coherente con el tema, método o resultado principal de la fuente citada."


def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = []
    status_counts = Counter()
    unique = defaultdict(lambda: {"count": 0, "pdf_pages": set(), "printed_pages": set(), "statuses": [], "urls": set()})

    for order, item in enumerate(data["citation_paragraphs"], start=1):
        index = item["paragraph_index"]
        citation_text = "; ".join(c["raw"] for c in item["citations"])
        if index in NO_TRACE:
            status = "No trazable"
            rationale, action = NO_TRACE[index]
        elif index in NO_MATCH:
            status = "No coincide"
            rationale, action = NO_MATCH[index]
        elif index in PARTIAL:
            status = "Coincidencia parcial"
            rationale, action = PARTIAL[index]
        else:
            status = "Coincide"
            rationale = default_rationale(citation_text)
            action = "Conservar; opcionalmente añadir página o sección de la fuente para mayor trazabilidad."

        status_counts[status] += 1
        location = "Fila de tabla" if item.get("container") == "table_row" else "Párrafo"
        context = item.get("context_text") or item["text"]
        row = {
            "id": order,
            "pdf_page": item["pdf_page"],
            "printed_page": item.get("printed_page"),
            "citation_paragraph_on_page": item.get("citation_paragraph_on_page"),
            "docx_paragraph": index,
            "location": location,
            "section": section_for(index),
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
        worst = max(bucket["statuses"], key=lambda value: severity[value])
        unique_rows.append(
            {
                "citation": label,
                "count": bucket["count"],
                "pdf_pages": ", ".join(map(str, sorted(bucket["pdf_pages"]))),
                "printed_pages": ", ".join(map(str, sorted(bucket["printed_pages"]))),
                "worst_status": worst,
                "urls": " | ".join(sorted(bucket["urls"])),
            }
        )

    all_citation_text = " ".join(row["citations"] for row in rows)
    bibliography = []
    for number, entry in enumerate(data["references"], start=1):
        text = entry["text"]
        first_author = text.split(",", 1)[0].strip()
        years = re.findall(r"\((\d{4}[a-z]?)\)", text)
        year = years[0] if years else ""
        count = len(re.findall(re.escape(norm(first_author)), norm(all_citation_text))) if first_author else 0
        if year and year not in all_citation_text:
            count = 0
        status, issue = BIB_ISSUES.get(number, ("Sin anomalía evidente", "No se detectó un problema bibliográfico evidente en esta revisión de correspondencia."))
        bibliography.append(
            {
                "number": number,
                "entry": text,
                "cited_estimate": count,
                "metadata_status": status,
                "issue": issue,
            }
        )

    hyndman_rows = [row for row in rows if "hyndman & athanasopoulos" in norm(row["citations"]) or "hyndman y athanasopoulos" in norm(row["citations"])]
    data.update(
        {
            "audit_rows": rows,
            "unique_citations": unique_rows,
            "bibliography_audit": bibliography,
            "hyndman_rows": hyndman_rows,
            "summary": {
                "citation_paragraphs": len(rows),
                "citation_groups": sum(len(item["citations"]) for item in data["citation_paragraphs"]),
                "unique_raw_citations": len(unique_rows),
                "hyndman_2021_occurrences": len(hyndman_rows),
                "status_counts": dict(status_counts),
                "bibliography_entries": len(bibliography),
                "bibliography_known_issues": len(BIB_ISSUES),
            },
        }
    )
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
