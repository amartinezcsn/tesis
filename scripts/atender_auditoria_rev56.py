from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx import Document


SOURCE = Path(r"C:\Python\tesis\documentacion\TESIS_AGO2026_Rev56_(ZUJ).docx")
OUTPUT = Path(r"C:\Python\tesis\documentacion\TESIS_AGO2026_Rev57_(ZUJ).docx")


def normalized(text: str) -> str:
    return " ".join(text.split())


def set_paragraph_text(paragraph, new_text: str) -> None:
    run_properties = None
    if paragraph.runs and paragraph.runs[0]._r.rPr is not None:
        run_properties = deepcopy(paragraph.runs[0]._r.rPr)
    paragraph.clear()
    run = paragraph.add_run(new_text)
    if run_properties is not None:
        run._r.insert(0, run_properties)


def replace_paragraph(document, fragment: str, new_text: str) -> None:
    matches = [p for p in document.paragraphs if fragment in normalized(p.text)]
    if len(matches) != 1:
        raise RuntimeError(f"Se esperaba un párrafo para {fragment!r}; encontrados: {len(matches)}")
    set_paragraph_text(matches[0], new_text)


def delete_paragraph(paragraph) -> None:
    element = paragraph._element
    element.getparent().remove(element)
    paragraph._p = paragraph._element = None


def delete_reference(document, fragment: str) -> None:
    matches = [p for p in document.paragraphs if fragment in normalized(p.text)]
    if len(matches) != 1:
        raise RuntimeError(f"Se esperaba una referencia para {fragment!r}; encontrados: {len(matches)}")
    delete_paragraph(matches[0])


def replace_reference(document, fragment: str, new_text: str) -> None:
    matches = [p for p in document.paragraphs if fragment in normalized(p.text)]
    if len(matches) != 1:
        raise RuntimeError(f"Se esperaba una referencia para {fragment!r}; encontrados: {len(matches)}")
    set_paragraph_text(matches[0], new_text)


def insert_reference_before(document, before_fragment: str, text: str) -> None:
    matches = [p for p in document.paragraphs if before_fragment in normalized(p.text)]
    if len(matches) != 1:
        raise RuntimeError(f"Se esperaba un punto de inserción para {before_fragment!r}; encontrados: {len(matches)}")
    target = matches[0]
    inserted = target.insert_paragraph_before(text)
    inserted.style = target.style
    inserted.paragraph_format.left_indent = target.paragraph_format.left_indent
    inserted.paragraph_format.first_line_indent = target.paragraph_format.first_line_indent
    inserted.paragraph_format.space_before = target.paragraph_format.space_before
    inserted.paragraph_format.space_after = target.paragraph_format.space_after
    inserted.paragraph_format.line_spacing = target.paragraph_format.line_spacing


def set_cell_text(cell, text: str) -> None:
    set_paragraph_text(cell.paragraphs[0], text)
    for extra in list(cell.paragraphs[1:]):
        delete_paragraph(extra)


def find_table_row(document, first_cell_fragment: str):
    matches = []
    for table in document.tables:
        for row in table.rows:
            if first_cell_fragment in normalized(row.cells[0].text):
                matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(f"Se esperaba una fila para {first_cell_fragment!r}; encontrados: {len(matches)}")
    return matches[0]


doc = Document(SOURCE)

# El Estado del Arte contenía una decisión metodológica repetida. Se elimina de
# esta sección porque la frecuencia semanal ya se justifica y operacionaliza en
# el marco teórico y la metodología.
delete_reference(doc, "Agregación temporal y horizonte de planeación")
delete_reference(
    doc,
    "La elección del horizonte debe responder a la frecuencia efectiva de decisión",
)

# Introducción: fuentes faltantes, metadatos y afirmaciones sobredimensionadas.
replace_paragraph(
    doc,
    "Un emprendimiento surge a partir de una idea",
    "Un emprendimiento surge cuando una persona identifica una oportunidad para ofrecer un producto o servicio y organiza recursos para desarrollarla. El Global Entrepreneurship Monitor 2023/2024 sitúa la actividad emprendedora como un componente de la salud de las economías y analiza las condiciones que favorecen o limitan su desarrollo (Global Entrepreneurship Monitor, 2024).",
)
replace_paragraph(
    doc,
    "Los emprendimientos o microempresas enfrentan importantes desafíos",
    "Los emprendimientos o microempresas enfrentan desafíos de planeación y aprendizaje durante sus primeras etapas. Minniti y Bygrave (2001) explican que el proceso emprendedor es dinámico y se nutre del aprendizaje derivado de la interacción con el entorno y de las decisiones bajo incertidumbre. Ries (2017), desde la perspectiva lean startup, describe la validación iterativa de supuestos y el ajuste del modelo de negocio mediante experimentación.",
)
replace_paragraph(
    doc,
    "La Organización para la Cooperación y el Desarrollo Económicos",
    "La Organización para la Cooperación y el Desarrollo Económicos documenta brechas de digitalización y capacidades en las pequeñas empresas, las cuales limitan el aprovechamiento sistemático de información para gestionar el negocio (OCDE, 2021). Las consecuencias específicas de esas brechas sobre el pronóstico de compras y el inventario deben evaluarse en cada contexto. Kantis, Federico y García (2020) señalan que las capacidades de gestión durante las etapas tempranas influyen en la organización interna, el uso de recursos y las posibilidades de crecimiento.",
)
replace_paragraph(
    doc,
    "Cuando se observa que el producto o servicio ofrecido recibe una aceptación",
    "Cuando un producto o servicio obtiene aceptación en el mercado aparecen nuevos retos de coordinación, capacidad y planeación. El aprendizaje emprendedor puede desarrollarse de manera progresiva conforme se toman decisiones y se recibe información del entorno (Minniti y Bygrave, 2001). Los efectos concretos sobre desperdicio, productividad y compras requieren evidencia propia del sector y del negocio analizado.",
)
replace_paragraph(
    doc,
    "Las microempresas representan el núcleo del aparato productivo",
    "Las microempresas constituyen la mayoría de las unidades económicas de México. Los resultados oportunos de los Censos Económicos 2024 indican que en 2023 operaron 5,451,113 unidades económicas del sector privado y empresas paraestatales; 95.5% eran microempresas y empleaban 41.5% del personal ocupado (INEGI, 2025). Estas cifras delimitan su importancia económica, pero no demuestran por sí mismas limitaciones específicas en planeación financiera, inventarios o cadena de suministro.",
)
replace_paragraph(
    doc,
    "Uno de los principales retos que enfrentan las microempresas es la escasa adopción",
    "Las pequeñas empresas presentan brechas de adopción digital y de capacidades para aprovechar tecnologías avanzadas (OCDE, 2021). La magnitud de esas brechas y sus efectos sobre decisiones de compras, inventarios e ingresos varían según el país, el sector y la empresa. Por ello, la utilidad de herramientas analíticas para una microempresa de repostería debe evaluarse con datos del caso, sin atribuir a la OCDE una proporción no documentada.",
)

# Estado del arte: delimitar el alcance de cada fuente y separar las decisiones del estudio.
replace_paragraph(
    doc,
    "Uno de los estudios más relevantes es el de Hübner et al. (2024)",
    "Hübner et al. (2024) analizaron la implementación del servicio de aprendizaje automático Foodforecast en panaderías de Alemania. El estudio aplicó una evaluación de ciclo de vida y comparó los impactos directos del sistema con los beneficios asociados a la reducción de devoluciones de productos de panadería. Los autores reportaron una reducción promedio de 30% en devoluciones durante 2022, según los informes de ventas utilizados. El trabajo aporta evidencia sobre reducción de desperdicio e impactos ambientales, pero no realiza una evaluación independiente del error de pronóstico.",
)
replace_paragraph(
    doc,
    "Los registros diarios de ventas y compras en negocios de pequeña escala",
    "La agregación temporal debe corresponder a la frecuencia de la decisión y modifica tanto la variabilidad como el número de observaciones disponibles (Hyndman & Athanasopoulos, 2021). En series de compras, la conveniencia de resumir registros diarios por semana debe comprobarse con la cobertura y la finalidad de planeación de cada caso. Con independencia de la frecuencia elegida, los modelos de aprendizaje automático deben compararse con métodos estadísticos establecidos y no asumirse superiores por su mayor complejidad (Spiliotis et al., 2022).",
)
replace_paragraph(
    doc,
    "El pronóstico constituye una fase posterior a la caracterización de la serie",
    "El pronóstico constituye una fase posterior a la caracterización de la serie. Antes de comparar algoritmos conviene examinar la frecuencia, la tendencia, la autocorrelación y la estabilidad de los patrones estacionales (Hyndman & Athanasopoulos, 2021). La validación y el preprocesamiento también deben respetar el orden temporal para evitar que información posterior intervenga en el ajuste (Bergmeir & Benítez, 2012). Cuando existen huecos de captura, primero debe distinguirse una ausencia de registro de un valor económico igual a cero; esta distinción corresponde a la depuración del caso.",
)
replace_paragraph(
    doc,
    "En series con semanas sin movimiento, el intervalo promedio entre ocurrencias",
    "En series con periodos sin movimiento, el intervalo promedio entre ocurrencias (ADI) y el cuadrado del coeficiente de variación de los importes positivos (CV²) permiten clasificar patrones de demanda (Syntetos et al., 2005). Esta clasificación orienta el diagnóstico, pero no determina por sí sola el modelo ganador. Croston-SBA constituye una corrección para demanda intermitente (Syntetos & Boylan, 2005), mientras que TSB incorpora una actualización explícita de la probabilidad de ocurrencia (Teunter et al., 2011).",
)
replace_paragraph(
    doc,
    "La industria de la repostería ha experimentado una evolución significativa",
    "Borsato (2023) examina la repostería como una forma de estética comestible en la que convergen técnicas culinarias y expresión artística. Desde ese alcance, la repostería creativa o cake design puede caracterizarse por el énfasis en el diseño y la personalización de productos para celebraciones y ocasiones especiales. La fuente no se utiliza para inferir por sí sola una transformación económica de toda la industria.",
)
replace_paragraph(
    doc,
    "La innovación tecnológica ha adquirido un papel relevante dentro de la industria alimentaria",
    "Las capacidades de analítica de datos pueden relacionarse con innovación y desempeño organizacional, aunque la evidencia de Mikalef et al. (2019) y Dubey et al. (2021) no se limita al sector panadero. Para este sector, Aprodu et al. (2025) revisan aplicaciones de tecnologías de Industria 4.0. En conjunto, estas fuentes permiten plantear que la digitalización puede apoyar actividades operativas, pero sus efectos sobre pedidos, inventarios y producción deben comprobarse en cada organización.",
)
replace_paragraph(
    doc,
    "Las aplicaciones descritas se han estudiado principalmente en contextos",
    "Las aplicaciones descritas se han estudiado principalmente en contextos con mayor disponibilidad de datos y capacidades tecnológicas. Para las PYMES latinoamericanas, Poveda-Valverde y Fierro Barragán (2026) identifican barreras de infraestructura, presupuesto y talento especializado. La búsqueda documental realizada para este capítulo encontró poca evidencia directamente referida a microempresas de repostería creativa; este resultado delimita la revisión efectuada y no demuestra la inexistencia de otros estudios.",
)
replace_paragraph(
    doc,
    "Como complemento regional, Poveda Valverde y Fierro Barragán (2026)",
    "Como complemento regional, Poveda-Valverde y Fierro Barragán (2026), en una revisión sistemática sobre inteligencia artificial en PYMES latinoamericanas, identifican restricciones de infraestructura, presupuesto y talento especializado, además de una distribución heterogénea de aplicaciones entre actividades empresariales. Estos resultados justifican desarrollar estudios aplicados y reproducibles en organizaciones con menor disponibilidad de datos, sin atribuir a la revisión una concentración sectorial más precisa que la informada por sus autores.",
)

# Tabla de investigaciones relevantes.
row = find_table_row(doc, "Abrar et al. (2024)")
set_cell_text(row.cells[4], "Preprint arXiv; modelo híbrido CNN-LSTM con XAI")
set_cell_text(row.cells[6], "Arquitectura compleja evaluada con mayor disponibilidad de datos; evidencia aún como preprint.")

row = find_table_row(doc, "Giannopoulos et al. (2025)")
set_cell_text(row.cells[2], "demanda intermitente; ML; evaluación")
set_cell_text(row.cells[7], "Sustenta la validación rolling-origin y el uso cauteloso de métricas; small data corresponde a la condición de esta tesis.")

row = find_table_row(doc, "Poveda-Valverde y Fierro Barragán (2026)")
set_cell_text(row.cells[5], "Persisten barreras de infraestructura, presupuesto y talento; las aplicaciones revisadas abarcan distintas actividades empresariales.")
set_cell_text(row.cells[7], "Refuerza el vacío regional identificado por esta revisión y la necesidad de evidencia aplicada en microempresas.")

# Síntesis, contexto y justificación.
replace_paragraph(
    doc,
    "Las microempresas operan en entornos caracterizados por alta incertidumbre financiera",
    "Góngora Chonillo (2023) aborda la evaluación del riesgo financiero en microempresas mediante inteligencia artificial. Esta referencia sustenta la relevancia de analizar información financiera en empresas pequeñas, pero no demuestra afirmaciones generales sobre variabilidad de la demanda, inventarios o gestión de la cadena de suministro.",
)
replace_paragraph(
    doc,
    "Esta situación resulta especialmente crítica en microempresas del sector alimentario",
    "En empresas del sector alimentario, la perecibilidad y la variación de la demanda vuelven relevante coordinar compras, producción e inventarios. Los pronósticos aportan información para la planeación, pero no eliminan la incertidumbre ni determinan por sí solos los costos o faltantes de inventario (Hyndman & Athanasopoulos, 2021). En esta tesis, los efectos financieros y operativos se mantendrán separados de las métricas de precisión predictiva.",
)
replace_paragraph(
    doc,
    "En el ámbito de la gestión operativa y de la cadena de suministro",
    "La incorporación de analítica avanzada e inteligencia artificial se relaciona con capacidades organizacionales y orientación estratégica hacia la innovación (Dubey et al., 2021). En las PYMES latinoamericanas también intervienen restricciones de infraestructura, presupuesto y talento especializado (Poveda-Valverde & Fierro Barragán, 2026). Estas condiciones deben considerarse al valorar la adopción tecnológica en una microempresa.",
)
replace_paragraph(
    doc,
    "Los antecedentes revisados muestran que los resultados obtenidos en organizaciones",
    "Consideradas conjuntamente, las fuentes muestran que las capacidades analíticas influyen en el aprovechamiento de los datos y que las PYMES latinoamericanas enfrentan barreras de adopción (Mikalef et al., 2019; Poveda-Valverde & Fierro Barragán, 2026). Esta síntesis justifica evaluar la aplicabilidad de las herramientas en empresas de menor escala, sin presentarla como un resultado textual de una sola publicación ni anticipar efectos antes de la evaluación empírica.",
)
replace_paragraph(
    doc,
    "En el contexto de las micro, pequeñas y medianas empresas (MIPYMES)",
    "En una microempresa, la experiencia del propietario puede concentrar parte del conocimiento utilizado para decidir. Para el caso analizado, la investigación deberá documentar qué decisiones se apoyan en registros y cuáles dependen de conocimiento no formalizado, sin generalizar esta condición a todas las MIPYMES ni atribuirla a una fuente que estudia organizaciones basadas en conocimiento.",
)
replace_paragraph(
    doc,
    "Esta investigación propone generar evidencia sobre el uso de herramientas de pronóstico semanal",
    "Poveda-Valverde y Fierro Barragán (2026) documentan restricciones de infraestructura, presupuesto y talento especializado que pueden dificultar la adopción de soluciones basadas en datos en PYMES latinoamericanas. A partir de ese contexto, esta investigación evaluará herramientas de pronóstico semanal con la información disponible en una microempresa y valorará su pertinencia de acuerdo con sus capacidades operativas. Esta última decisión corresponde al diseño del estudio.",
)

# Marco teórico: conservar la teoría y marcar de forma explícita las reglas propias.
replace_paragraph(
    doc,
    "El presente marco teórico desarrolla los fundamentos conceptuales y matemáticos",
    "El presente marco teórico desarrolla los fundamentos conceptuales y matemáticos de una propuesta híbrida para pronosticar el importe total semanal de compras y su distribución porcentual entre los principales insumos de Cup&Cake. Se revisan la planeación del presupuesto de abastecimiento, las series temporales semanales, los métodos estadísticos y de aprendizaje automático, las estrategias de integración, el análisis composicional y la evaluación fuera de muestra. Las referencias específicas se presentan en los apartados donde se desarrolla cada concepto.",
)
replace_paragraph(
    doc,
    "La experiencia del responsable del negocio puede aportar información",
    "La experiencia del responsable del negocio puede aportar información sobre celebraciones, cambios de proveedores o adquisiciones extraordinarias que no aparece explícitamente en una serie. Ese conocimiento permite interpretar registros y proponer variables, mientras que las reglas de pronóstico hacen reproducible la estimación. Como criterio del estudio, se distinguirán los hechos documentados de las expectativas y se conservará la fecha en que cada dato estuvo disponible.",
)
replace_paragraph(
    doc,
    "La perecibilidad aporta contexto a la periodicidad de las compras",
    "La frecuencia y el nivel de agregación deben responder a la decisión analizada (Hyndman & Athanasopoulos, 2021). En el caso propuesto, la escala semanal se utilizará para revisar el presupuesto de abastecimiento. Esta delimitación no equivale a planificar inventarios físicos: traducir importes a unidades requeriría precios, recetas, existencias y condiciones de suministro que quedan fuera del pronóstico monetario.",
)
replace_paragraph(
    doc,
    "Una serie temporal es una secuencia ordenada de observaciones",
    "Una serie temporal es una secuencia ordenada de observaciones registradas con un índice temporal definido (Hyndman & Athanasopoulos, 2021). Para depurar los datos del caso, la agregación semanal conservará un calendario consistente y distinguirá una semana sin compras de una semana sin registro. Los huecos no se rellenarán automáticamente con cero, porque esa sustitución cambiaría el significado del objetivo; esta es una regla de calidad de datos del estudio.",
)
replace_paragraph(
    doc,
    "La autocorrelación parcial y las pruebas de dependencia conjunta",
    "La autocorrelación parcial y las pruebas de dependencia conjunta pueden complementar el diagnóstico (Hyndman & Athanasopoulos, 2021). La selección de características y la validación deben respetar el orden temporal; utilizar toda la serie para definir variables antes de evaluar un bloque reservado puede introducir información posterior en el procedimiento (Bergmeir & Benítez, 2012). En este estudio, cualquier diagnóstico que determine ajustes se calculará únicamente con el historial disponible en cada origen.",
)
replace_paragraph(
    doc,
    "La estimación z corresponde al tamaño de los eventos positivos",
    "Las estimaciones z y a corresponden, respectivamente, al tamaño de los eventos positivos y al intervalo entre ellos. El procedimiento constituye una referencia para demanda intermitente, no una garantía de superioridad (Hyndman & Athanasopoulos, 2021). Como procedimiento de auditoría del caso, los picos se contrastarán con la fuente para distinguir posibles errores de registro de compras extraordinarias; no se eliminarán únicamente por su magnitud (Kuhn & Johnson, 2013).",
)
replace_paragraph(
    doc,
    "El componente de medias móviles de ARIMA opera sobre innovaciones",
    "El componente de medias móviles de ARIMA opera sobre innovaciones y no equivale a promediar observaciones anteriores. Las variantes estacionales añaden operadores asociados a una periodicidad definida, y la selección debe considerar la longitud del historial y el diagnóstico de residuos (Hyndman & Athanasopoulos, 2021). Para esta investigación, el tamaño de la empresa no se utilizará por sí solo como criterio para excluir una familia estadística.",
)
replace_paragraph(
    doc,
    "Los árboles permiten representar interacciones y relaciones no lineales",
    "Los árboles y los bosques aleatorios permiten representar interacciones y relaciones no lineales (Breiman, 2001). En pronóstico de series temporales, las entradas deben construirse con información disponible en el origen, como rezagos y variables de calendario (Bontempi et al., 2013). La profundidad, el tamaño mínimo de los nodos y la diversidad de árboles se tratarán como decisiones de diseño; el modelo no se considerará inmune a errores de captura o datos faltantes.",
)
replace_paragraph(
    doc,
    "La tasa de aprendizaje y el número de etapas controlan",
    "La tasa de aprendizaje y el número de etapas controlan la magnitud de la adaptación en gradient boosting (Friedman, 2001). Estas técnicas pueden aprovechar interacciones entre calendario e historial, pero su configuración debe realizarse antes de la evaluación final. Ajustar el número de etapas con el mismo bloque utilizado para reportar precisión produciría una comparación optimista (Tashman, 2000).",
)
replace_paragraph(
    doc,
    "Una red autorregresiva aproxima una relación entre rezagos",
    "Una red autorregresiva aproxima mediante una función no lineal la relación entre rezagos de una serie (Hyndman & Athanasopoulos, 2021). Las redes neuronales recurrentes incorporan estados internos y mecanismos de memoria, además de parámetros y decisiones de ajuste; su desempeño depende del tamaño y las características de los datos (Hewamalage et al., 2021). En esta tesis, la presencia de una red recurrente no se utilizará como condición para definir un modelo como híbrido.",
)
replace_paragraph(
    doc,
    "La selección de familias tendrá sentido si permite examinar",
    "Como criterio de diseño, cada familia candidata deberá responder una pregunta pertinente sobre el objetivo, por ejemplo, si aportan valor la no linealidad o la memoria temporal. La selección y el ajuste se realizarán con información anterior a las semanas de evaluación, de acuerdo con el principio de separar entrenamiento, validación y prueba (Kuhn & Johnson, 2013).",
)
replace_paragraph(
    doc,
    "Si el segundo componente se entrena con errores del primero",
    "Los modelos híbridos pueden combinar componentes lineales y no lineales, y los errores de ajuste del primer componente no deben confundirse con errores predictivos genuinos (Hyndman & Athanasopoulos, 2021; Zhang, 2003). Como adaptación metodológica para Cup&Cake, los errores usados por el segundo componente se generarán respetando el orden temporal y la suma se evaluará en semanas no utilizadas para configurar el procedimiento.",
)
replace_paragraph(
    doc,
    "La periodicidad debe corresponder al índice temporal",
    "La periodicidad debe corresponder al índice temporal y puede representarse mediante términos de Fourier cuando la estacionalidad lo justifique (Hyndman & Athanasopoulos, 2021). Para este estudio, los eventos diarios se convertirán en indicadores semanales de presencia o proximidad. El número de armónicos y de interacciones se limitará de acuerdo con el historial disponible; ambas son decisiones de diseño del caso.",
)
replace_paragraph(
    doc,
    "Las medidas se interpretarán en moneda y deberán reportarse por horizonte",
    "RMSE y MAE resumen el error en las mismas unidades del objetivo y deben interpretarse por horizonte (Hyndman & Athanasopoulos, 2021). Un RMSE menor representa una menor media de errores cuadrados, pero no implica necesariamente menos errores extremos. Como regla previa del protocolo, H1 tendrá un criterio principal de comparación fijado antes del análisis final y las demás métricas se informarán como evidencia complementaria.",
)
replace_paragraph(
    doc,
    "El contraste de H1 tendrá dos componentes",
    "La evaluación fuera de muestra debe mantenerse separada del ajuste y de la explicación causal (Shmueli, 2010; Tashman, 2000). Como definición previa de esta investigación, el contraste de H1 considerará la precisión del importe total y de su distribución; mejorar solo uno se describirá como evidencia favorable para ese componente. No se escogerá retrospectivamente el horizonte más conveniente ni se interpretará una diferencia de error como efecto financiero.",
)
replace_paragraph(
    doc,
    "La evaluación de costos de implementación y beneficios organizacionales",
    "La precisión predictiva, los costos de implementación y los beneficios organizacionales corresponden a dimensiones distintas. En esta investigación, una reducción de MAE o RMSE no se denominará retorno de inversión, y los resultados se presentarán como información para apoyar la decisión, no como sustituto de la información operativa del responsable. Esta separación constituye una delimitación económica del estudio; Power (2002) sustenta el papel complementario de los sistemas de apoyo a decisiones.",
)
replace_paragraph(
    doc,
    "La composición añade un problema propio",
    "Los datos composicionales requieren conservar proporciones válidas dentro de un total (Aitchison, 1982). Por ello, el procedimiento evaluará por separado el importe y las participaciones frente a sus respectivas referencias. La coherencia de suma corresponde a la representación jerárquica, mientras que la precisión exige evidencia fuera de muestra (Hyndman & Athanasopoulos, 2021; Hyndman et al., 2011).",
)
replace_paragraph(
    doc,
    "La investigación se desarrollará como una evaluación predictiva",
    "Shmueli (2010) distingue los objetivos explicativos de los predictivos. Con base en esa distinción, esta investigación se define como una evaluación predictiva del presupuesto semanal de abastecimiento. Como regla previa del estudio, H1 requerirá evidencia favorable en el importe total y en las participaciones; una mejora aislada se informará como resultado de ese componente y no como confirmación de la hipótesis conjunta.",
)

# Bibliografía: eliminar entradas no verificables o ya no utilizadas.
for fragment in [
    "Banco Interamericano de Desarrollo (BID). (2019). Emprender en América Latina",
    "Bertsimas, D., Dunn, J., & Pawlowski, C. (2021)",
    "García-Sánchez, A., Fernández, M., & Ruiz, P. (2023)",
    "Hyndman, R. J., Athanasopoulos, G., Wang, E., & Wang, Y. (2023)",
    "PraveenaSri, P., Padma, V., Muruguesan, R., & Usha, S. (2023)",
    "Ramírez-Montoya, M. S., et al. (2022)",
]:
    delete_reference(doc, fragment)

replace_reference(
    doc,
    "Huber, J., & Stuckenschmidt, H. (2020)",
    "Huber, J., & Stuckenschmidt, H. (2020). Daily retail demand forecasting using machine learning with emphasis on calendric special days. International Journal of Forecasting, 36(4), 1420–1438. https://doi.org/10.1016/j.ijforecast.2020.02.005",
)
replace_reference(
    doc,
    "Mikalef, P., Krogstie, J., Pappas, I., & Pavlou, P. (2019)",
    "Mikalef, P., Krogstie, J., Pappas, I. O., & Pavlou, P. A. (2020). Investigating the effects of big data analytics capabilities on firm performance: The mediating role of dynamic capabilities. Information & Management, 57(2), 103169. https://doi.org/10.1016/j.im.2019.103169",
)
replace_reference(
    doc,
    "Minniti, M., & Bygrave, W. (2018)",
    "Minniti, M., & Bygrave, W. (2001). A dynamic model of entrepreneurial learning. Entrepreneurship Theory and Practice, 25(3), 5–16. https://doi.org/10.1177/104225870102500301",
)

# Incorporar las fuentes antes ausentes y las referencias originales de ADI-CV² y TSB.
insert_reference_before(
    doc,
    "Góngora Chonillo, J. T. (2023)",
    "Global Entrepreneurship Monitor. (2024). Global Entrepreneurship Monitor 2023/2024 global report: 25 years and growing. https://www.gemconsortium.org/report/51377",
)
insert_reference_before(
    doc,
    "Kahneman, D. (2011)",
    "Instituto Nacional de Estadística y Geografía (INEGI). (2025, 25 de junio). Estadísticas a propósito del Día de las Micro, Pequeñas y Medianas Empresas (mipymes) [Comunicado de prensa 71/25]. https://www.inegi.org.mx/contenidos/saladeprensa/aproposito/2025/EAP_MIPYMES_25.pdf",
)
insert_reference_before(
    doc,
    "Syntetos, A. A., & Boylan, J. E. (2005)",
    "Syntetos, A. A., Boylan, J. E., & Croston, J. D. (2005). On the categorization of demand patterns. Journal of the Operational Research Society, 56(5), 495–503. https://doi.org/10.1057/palgrave.jors.2601841",
)
insert_reference_before(
    doc,
    "Tibshirani, R. (1996)",
    "Teunter, R. H., Syntetos, A. A., & Babai, M. Z. (2011). Intermittent demand: Linking forecasting to inventory obsolescence. European Journal of Operational Research, 214(3), 606–615. https://doi.org/10.1016/j.ejor.2011.05.018",
)

doc.core_properties.title = "Tesis Cup&Cake Revisión 57"
doc.save(OUTPUT)
print(OUTPUT)
