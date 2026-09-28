from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


SOURCE = Path(r"C:\Python\tesis\documentacion\TESIS_AGO2026_Rev57_(ZUJ).docx")
OUTPUT = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev58_(ZUJ)_Corregida.docx")


QUESTION = (
    "¿Qué precisión ofrece, frente a modelos de referencia y mediante validación temporal, "
    "un modelo híbrido que integra métodos estadísticos y aprendizaje automático para estimar "
    "el importe total semanal de compras y su distribución porcentual entre los principales "
    "insumos registrados de Cup&Cake, microempresa de repostería creativa de Tizayuca, Hidalgo, "
    "con los datos disponibles del 5 de diciembre de 2016 al 11 de mayo de 2026 y una evaluación "
    "final comprendida entre el 24 de marzo y el 28 de julio de 2025?"
)

OBJECTIVE = (
    "Determinar la precisión que ofrece, frente a modelos de referencia y mediante validación "
    "temporal, un modelo híbrido que integra métodos estadísticos y aprendizaje automático para "
    "estimar el importe total semanal de compras y su distribución porcentual entre los principales "
    "insumos registrados de Cup&Cake, microempresa de repostería creativa de Tizayuca, Hidalgo, "
    "con los datos disponibles del 5 de diciembre de 2016 al 11 de mayo de 2026 y una evaluación "
    "final comprendida entre el 24 de marzo y el 28 de julio de 2025."
)

SUMMARY_1 = (
    "Esta investigación desarrolló y evaluó un modelo híbrido que integra métodos estadísticos y "
    "de aprendizaje automático para estimar el importe total semanal de compras y su distribución "
    "porcentual entre los principales insumos de Cup&Cake, microempresa de repostería creativa de "
    "Tizayuca, Hidalgo. Se integraron registros de compras, ventas y variables de calendario "
    "disponibles entre el 5 de diciembre de 2016 y el 11 de mayo de 2026. La evaluación final "
    "comprendió objetivos entre el 24 de marzo y el 28 de julio de 2025 y utilizó validación temporal "
    "rolling window, una ventana de entrenamiento de 52 semanas, avance de tres semanas y horizontes "
    "de una a cuatro semanas."
)

SUMMARY_2 = (
    "La evaluación produjo seis orígenes monetarios por horizonte y entre tres y cinco observaciones "
    "válidas por horizonte para la composición. El modelo híbrido obtuvo RMSE de 521.60, 695.41, "
    "801.62 y 700.88 MXN para los horizontes de una a cuatro semanas, respectivamente, y solo alcanzó "
    "el menor RMSE entre los comparadores principales en el horizonte de tres semanas. En la "
    "distribución porcentual no existió un método dominante. Debido a la muestra reducida, 29 semanas "
    "de compras estimadas por promedio simple y la cobertura no certificada, el contraste de H1 fue "
    "no confirmatorio. El procedimiento se considera una aportación reproducible de carácter "
    "evaluativo exploratorio y un apoyo revisable para la planeación, no una orden automática de compra."
)

ABSTRACT_1 = (
    "This study developed and evaluated a hybrid model combining statistical and machine-learning "
    "methods to estimate the total weekly purchasing amount and its percentage allocation among the "
    "main inputs of Cup&Cake, a creative baking microenterprise in Tizayuca, Hidalgo, Mexico. Purchase, "
    "sales, and calendar records available from December 5, 2016, to May 11, 2026, were integrated. "
    "The final evaluation covered targets from March 24 to July 28, 2025, and used rolling-window "
    "temporal validation, a 52-week training window, a three-week step, and one- to four-week horizons."
)

ABSTRACT_2 = (
    "The evaluation produced six monetary forecast origins per horizon and between three and five valid "
    "composition observations per horizon. The hybrid model obtained RMSE values of MXN 521.60, 695.41, "
    "801.62, and 700.88 for horizons one through four, respectively, and achieved the lowest RMSE among "
    "the main comparators only at the three-week horizon. No single percentage-allocation method "
    "dominated. Because of the small evaluation sample, 29 purchasing weeks estimated by simple "
    "averaging, and uncertified record coverage, the H1 assessment was non-confirmatory. The procedure "
    "is therefore presented as a reproducible exploratory evaluation and a revisable planning aid, not "
    "as an automated purchasing order."
)


def set_text(paragraph, text: str) -> None:
    paragraph.text = text


def delete_paragraph(paragraph) -> None:
    element = paragraph._element
    element.getparent().remove(element)
    paragraph._p = paragraph._element = None


def insert_paragraph_after(paragraph, text: str, style: str | None = None):
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    from docx.text.paragraph import Paragraph

    new_para = Paragraph(new_p, paragraph._parent)
    if style:
        new_para.style = style
    new_para.add_run(text)
    return new_para


def normalize_sort(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.casefold()


doc = Document(SOURCE)
stats = {"replaced": 0, "deleted": 0, "highlights": 0, "references_sorted": 0}

# Remove visible editorial highlighting while preserving text and character formatting.
for paragraph in doc.paragraphs:
    for run in paragraph.runs:
        if run.font.highlight_color is not None:
            run.font.highlight_color = None
            stats["highlights"] += 1
        rpr = run._r.get_or_add_rPr()
        for element in list(rpr):
            if element.tag == qn("w:shd"):
                rpr.remove(element)

for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    if run.font.highlight_color is not None:
                        run.font.highlight_color = None
                        stats["highlights"] += 1


def replace_exact(old: str, new: str) -> None:
    matches = [p for p in doc.paragraphs if p.text.strip() == old.strip()]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one exact match, found {len(matches)}: {old[:90]}")
    set_text(matches[0], new)
    stats["replaced"] += 1


replace_exact("Tolcayuca, Hidalgo. 28, agosto 2025.", "Tolcayuca, Hidalgo, septiembre de 2026.")
replace_exact(
    "Esta investigación se propone desarrollar un modelo híbrido que integre métodos estadísticos y de aprendizaje automático para estimar el importe total semanal de compras y su distribución porcentual entre los principales insumos de Cup&Cake, una microempresa de repostería creativa ubicada en Tizayuca, Hidalgo. El problema de estudio se enmarca en la planeación del presupuesto de abastecimiento bajo condiciones de datos limitados y variación temporal. Se consideran registros históricos de compras y ventas, junto con variables calendáricas y exógenas que estén disponibles en el momento de emitir cada pronóstico. El importe objetivo se delimita a las categorías presupuestarias elegibles; categorías fuera del alcance, como combustible, muebles, herramienta, imputados y otros, no forman parte del objetivo.",
    SUMMARY_1,
)
replace_exact(
    "La evaluación se plantea mediante validación temporal rolling window, con una ventana de entrenamiento de 52 semanas, avance de tres semanas, un bloque final de 20 semanas para evaluación y horizontes de pronóstico de una a cuatro semanas. El desempeño del modelo híbrido se contrastará con modelos de referencia usando métricas de error monetario; la distribución porcentual se evaluará con métricas de error de participación. El diseño busca determinar la precisión que puede ofrecer el procedimiento en este caso y aportar evidencia para valorar su posible uso como apoyo a la planeación, sin presuponer que la integración híbrida mejore el desempeño ni que sustituya la decisión de la persona responsable.",
    SUMMARY_2,
)
replace_exact(
    "This study proposes the development of a hybrid model combining statistical methods and machine learning to estimate the total weekly purchasing amount and its percentage allocation among the main inputs of Cup&Cake, a creative baking microenterprise in Tizayuca, Hidalgo, Mexico. The research addresses procurement-budget planning under limited-data and time-varying conditions. It considers historical purchasing and sales records, together with calendar and exogenous variables that are available when each forecast is issued. The monetary target is restricted to eligible budget categories; out-of-scope items, including fuel, furniture, tools, imputed categories, and others, are excluded.",
    ABSTRACT_1,
)
replace_exact(
    "The proposed evaluation uses rolling window temporal validation, a 52-week training window, a three-week step, a final 20-week evaluation block, and forecast horizons of one to four weeks. The hybrid model is to be compared with reference models using monetary error metrics, while the percentage allocation is to be assessed with share-error metrics. The design aims to determine the accuracy attainable in this case and provide evidence for assessing the method as a possible aid to procurement planning. It does not presuppose that hybrid integration improves forecast performance or replaces the decision-maker.",
    ABSTRACT_2,
)
replace_exact(
    "¿Qué precisión ofrece un modelo híbrido que integra métodos estadísticos y aprendizaje automático, mediante evaluación temporal de su precisión frente a modelos de referencia, para estimar el importe total semanal de compras y su distribución porcentual entre los principales insumos, como apoyo a la planeación del presupuesto de abastecimiento en una microempresa de repostería creativa de Tizayuca, Hidalgo?",
    QUESTION,
)
replace_exact(
    "Desarrollar un modelo híbrido que integra métodos estadísticos y aprendizaje automático, mediante evaluación temporal de su precisión frente a modelos de referencia, para el pronóstico del importe total semanal de compras y su distribución porcentual entre los principales insumos, como apoyo a la planeación del presupuesto de abastecimiento de una microempresa de repostería creativa de Tizayuca, Hidalgo",
    OBJECTIVE,
)

# Replace the generic methodology opening with a study-specific statement and remove filler.
method_open = next(p for p in doc.paragraphs if p.text.startswith("Investigar significa llevar a cabo"))
set_text(
    method_open,
    "Este capítulo describe el diseño evaluativo exploratorio utilizado para desarrollar y comparar el modelo híbrido y el procedimiento de distribución porcentual. Se documentan las fuentes, la unidad semanal de análisis, la auditoría de cobertura, la construcción del panel, los modelos de referencia, la selección interna, la evaluación temporal final y los criterios de interpretación. La reproducibilidad se sustenta en el manifiesto de ejecución, las huellas digitales de las fuentes y el código, y los productos exportados por la corrida run_20260924T195600Z_86a6f5.",
)
stats["replaced"] += 1
for prefix in [
    "Para que un conocimiento sea científico",
    "Como se ha dicho, se puede investigar",
    "La investigación se puede llevar a cabo de diferentes formas",
    "Se trata de uno de los tipos de investigación más frecuentes",
    "Otra manera de clasificar los diferentes tipos de investigación",
    "La investigación cuantitativa se basa en el estudio",
    "Podemos encontrar diferentes tipos de investigaciones",
    "Otro tipo de clasificación se puede extraer",
    "Este tipo de investigación se basa en el estudio de la realidad",
    "Atendiendo al proceso lógico empleado para inferir",
]:
    matches = [p for p in doc.paragraphs if p.text.startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one paragraph for deletion, found {len(matches)}: {prefix}")
    delete_paragraph(matches[0])
    stats["deleted"] += 1

# Resolve the protocol conflict and align the method with the executed run.
replace_exact(
    "Se propone una validación de ventana deslizante con 52 semanas de entrenamiento y avance de una semana. Su viabilidad se verificará según la cobertura efectiva, los rezagos y el número de observaciones utilizables; cualquier ajuste se justificará en la etapa de desarrollo. Se generarán pronósticos directos para h=1, h=2, h=3 y h=4, con h=1 como horizonte principal. Las métricas se reportarán por horizonte. La suma de los cuatro pronósticos será un consolidado de cuatro semanas y no equivaldrá necesariamente a un mes calendario.",
    "La corrida aplicó validación de ventana deslizante con 52 semanas de entrenamiento y avance de tres semanas. Se generaron pronósticos directos para h=1, h=2, h=3 y h=4, con h=1 como horizonte principal, y las métricas se reportaron por horizonte. La suma de los cuatro pronósticos representa un consolidado de 28 días y no equivale necesariamente a un mes calendario.",
)
replace_exact(
    "El estudio será longitudinal y retrospectivo porque analizará registros históricos en su secuencia temporal. Se revisarán las fuentes disponibles del periodo 2022–2026 y se documentarán las fechas efectivas de inicio y corte para ventas y compras, sin asumir cobertura completa. El modelado se limitará a los periodos cuya disponibilidad y continuidad puedan verificarse.",
    "El estudio fue longitudinal-retrospectivo y evaluativo exploratorio. El panel configurado abarcó del 5 de diciembre de 2016 al 11 de mayo de 2026. La validación interna utilizó orígenes del 18 de noviembre de 2024 al 10 de febrero de 2025; la evaluación final empleó seis orígenes del 24 de marzo al 7 de julio de 2025, con fechas objetivo hasta el 28 de julio de 2025. Estas fechas describen el alcance de la corrida y no implican cobertura exhaustiva de todas las semanas.",
)
replace_exact(
    "El procedimiento comprende recolección y depuración de registros, agregación semanal, diagnóstico temporal, ingeniería de características, selección de componentes e integración del modelo híbrido, estimación de la distribución porcentual, evaluación fuera de muestra y comunicación de resultados. El pipeline implementa una versión inicial de este flujo. La verificación técnica del software se distingue de la ejecución científica con datos reales, que permanece pendiente de aprobar fuentes, cobertura, catálogo y protocolo de evaluación.",
    "El procedimiento comprendió recolección y depuración de registros, agregación semanal, diagnóstico temporal, ingeniería de características, selección de componentes e integración del modelo híbrido, estimación de la distribución porcentual, evaluación fuera de muestra y comunicación de resultados. La corrida run_20260924T195600Z_86a6f5 se ejecutó con fuentes aprobadas y un catálogo y una cobertura trazables. La verificación técnica del software se mantuvo separada de la evaluación de precisión: aprobar controles de consistencia no se interpretó como validación predictiva ni como confirmación de H1.",
)

# Bring key methodological statements into the past tense without changing their substance.
past_replacements = {
    "La aplicación se delimitará al caso de Cup&Cake.": "La aplicación se delimitó al caso de Cup&Cake.",
    "Se prevé comunicar los pronósticos": "Los pronósticos se comunicaron",
    "Los resultados no se generalizarán": "Los resultados no se generalizaron",
    "Se documentará el contexto": "Se documentó el contexto",
    "La evaluación cuantitativa se realizará": "La evaluación cuantitativa se realizó",
    "Solo se incluirán estimaciones": "Solo se incluyeron estimaciones",
    "La investigación describirá": "La investigación describió",
    "Se integrarán los registros": "Se integraron los registros",
    "Las variables exógenas se incorporarán": "Las variables exógenas se incorporaron",
    "Los eventos de calendario conocidos podrán utilizarse": "Los eventos de calendario conocidos se utilizaron",
    "los indicadores económicos y meteorológicos deberán representar": "los indicadores económicos y meteorológicos debían representar",
    "Se adoptará un diseño": "Se adoptó un diseño",
    "Se evaluarán la precisión": "Se evaluaron la precisión",
    "se conservarán como comparadores": "se conservaron como comparadores",
    "se utilizará una referencia": "se utilizó una referencia",
    "Todos los métodos se evaluarán": "Todos los métodos se evaluaron",
    "se distinguirán": "se distinguieron",
    "La comparación contrastará": "La comparación contrastó",
    "Se utilizarán las mismas": "Se utilizaron las mismas",
    "No se emplearán": "No se emplearon",
    "se comparará": "se comparó",
    "Se evaluarán por separado": "Se evaluaron por separado",
    "se especificarán": "se especificaron",
    "se controlará": "se controló",
    "El pipeline sólo admitirá": "El pipeline solo admitió",
    "se bloqueará": "se bloqueó",
    "Cada ejecución exportará": "La ejecución exportó",
    "este diccionario documentará": "este diccionario documentó",
    "se desplazarán": "se desplazaron",
    "se tratarán": "se trataron",
    "se almacenará": "se almacenó",
    "podrán utilizarse": "se reservaron",
    "se excluirán": "se excluyeron",
    "Se recopilarán y estructurarán": "Se recopilaron y estructuraron",
    "Se verificará": "Se verificó",
    "La consolidación contemplará": "La consolidación contempló",
    "Se homologarán": "Se homologaron",
    "Se obtendrán": "Se obtuvieron",
    "Se examinará": "Se examinó",
    "no se asumirán": "no se asumieron",
    "se equiparará": "se equiparó",
    "Las características candidatas se evaluarán": "Las características candidatas se evaluaron",
    "medirá": "midió",
    "se utilizará": "se utilizó",
    "será una medida": "fue una medida",
    "Se propone utilizar": "Se utilizó",
    "se reportará": "se reportó",
    "no será": "no fue",
    "se indicarán": "se indicaron",
    "se evaluará": "se evaluó",
    "Se calculará": "Se calculó",
    "se presentará": "se presentó",
    "se excluirán únicamente": "se excluyeron únicamente",
    "permanecerán": "permanecieron",
}

in_method = False
for p in doc.paragraphs:
    if p.text.strip() == "METODOLOGÍA":
        in_method = True
    elif p.text.strip() == "DESARROLLO":
        in_method = False
    if not in_method or not p.text:
        continue
    new_text = p.text
    for old, new in past_replacements.items():
        new_text = new_text.replace(old, new)
    if new_text != p.text:
        set_text(p, new_text)
        stats["replaced"] += 1

# Add an explicit ethics and data-governance subsection after the final methodology paragraph.
method_end = next(p for p in doc.paragraphs if p.text.startswith("La herramienta no calcula cantidades físicas"))
ethics_heading = insert_paragraph_after(method_end, "Consideraciones éticas y tratamiento de datos", "Heading 3")
insert_paragraph_after(
    ethics_heading,
    "Cup&Cake autorizó el uso académico de sus registros para esta investigación. El tratamiento se limitó a los campos necesarios para construir las variables analíticas y evaluar el procedimiento. Los nombres de clientes, proveedores, responsables y demás identificadores personales o administrativos se excluyeron del conjunto de predictores y de los productos presentados. Los resultados se reportaron de forma agregada por semana y categoría; el acceso a los archivos de origen quedó restringido al proyecto. Esta autorización no elimina la obligación de conservar confidencialidad, trazabilidad y minimización de datos en futuras actualizaciones.",
    "Normal",
)

# Make the exploratory scope explicit at the first design declaration.
replace_exact(
    "Tipo de tesis: estudio aplicado, cuantitativo, no experimental y evaluativo, basado en un caso de estudio longitudinal-retrospectivo.",
    "Tipo de tesis: estudio aplicado, cuantitativo, no experimental y evaluativo exploratorio, basado en un caso de estudio longitudinal-retrospectivo.",
)

# Correct the two Makridakis 2018 labels according to alphabetical title order in APA 7.
for p in doc.paragraphs:
    text = p.text
    if not text:
        continue
    new = text
    if "Statistical and machine learning forecasting methods" in text:
        new = re.sub(r"\(2018b\)", "(2018a)", new)
    if "The M4 competition: Results" in text:
        new = re.sub(r"\(2018a\)", "(2018b)", new)
    if "mayor complejidad no garantiza" in text or "Con independencia de la frecuencia" in text:
        new = new.replace("Makridakis et al., 2018", "Makridakis et al., 2018a")
    if "competencia M4" in text or "evidencia amplia de M4" in text:
        new = new.replace("Makridakis et al., 2018, 2020", "Makridakis et al., 2018b, 2020")
        new = new.replace("Makridakis et al. (2018)", "Makridakis et al. (2018b)")
        new = new.replace("Makridakis et al., 2018)", "Makridakis et al., 2018b)")
    if new != text:
        set_text(p, new)
        stats["replaced"] += 1

# Normalize a few recurring editorial issues.
for p in doc.paragraphs:
    text = p.text
    if not text:
        continue
    new = text.replace("aprendizaje .", "aprendizaje automático.")
    new = new.replace("DISCUSION", "DISCUSIÓN") if text.strip() == "DISCUSION" else new
    new = new.replace("Procedimiento Metodológico", "Procedimiento metodológico") if text.strip() == "Procedimiento Metodológico" else new
    if new != text:
        set_text(p, new)
        stats["replaced"] += 1

# Sort bibliography paragraphs alphabetically while preserving their existing paragraph formatting.
paras = doc.paragraphs
ref_heading_index = next(i for i, p in enumerate(paras) if p.text.strip() == "REFERENCIAS")
annex_index = next(i for i, p in enumerate(paras) if p.text.strip().startswith("Anexo A Diccionario"))
reference_paras = [p for p in paras[ref_heading_index + 1 : annex_index] if p.text.strip()]
reference_texts = sorted((p.text for p in reference_paras), key=normalize_sort)
if len(reference_paras) != len(reference_texts):
    raise RuntimeError("Reference paragraph mismatch")
for p, text in zip(reference_paras, reference_texts):
    set_text(p, text)
stats["references_sorted"] = len(reference_paras)

# Ensure all figure/table captions participate in the rebuilt list of figures.
for p in doc.paragraphs:
    if re.match(r"^(Figura|Tabla|Imagen)\s+\d+\s*[.\-]", p.text.strip(), re.IGNORECASE):
        try:
            p.style = doc.styles["Caption"]
        except KeyError:
            pass

# Ask Word to refresh fields when the file is opened, in addition to the explicit refresh step.
settings = doc.settings._element
update_fields = settings.find(qn("w:updateFields"))
if update_fields is None:
    update_fields = OxmlElement("w:updateFields")
    settings.append(update_fields)
update_fields.set(qn("w:val"), "true")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUTPUT)
print(f"Saved: {OUTPUT}")
print(stats)
