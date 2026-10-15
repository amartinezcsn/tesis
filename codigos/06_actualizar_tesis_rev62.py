from pathlib import Path
import csv
import re
from copy import deepcopy

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "documentacion"
FIGS = DOCS / "figuras_individuales_propuesta_20261015"
RUN = ROOT / "output" / "run_20261013T193604Z_157556"
SRC = DOCS / "TESIS_SEP2026_Rev61_(ZUJ)_Final.docx"
OUT = DOCS / "TESIS_SEP2026_Rev62_(ZUJ)_Final.docx"
AUDIT = DOCS / "auditoria_elementos_rev62.csv"


def clear_paragraph(p):
    for child in list(p._p):
        if child.tag != qn("w:pPr"):
            p._p.remove(child)


def set_keep_with_next(p, value=True):
    pPr = p._p.get_or_add_pPr()
    node = pPr.find(qn("w:keepNext"))
    if value and node is None:
        pPr.append(OxmlElement("w:keepNext"))
    elif not value and node is not None:
        pPr.remove(node)


def set_keep_together(p, value=True):
    pPr = p._p.get_or_add_pPr()
    node = pPr.find(qn("w:keepLines"))
    if value and node is None:
        pPr.append(OxmlElement("w:keepLines"))
    elif not value and node is not None:
        pPr.remove(node)


def insert_paragraph_after(paragraph, text="", style=None):
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = paragraph._parent.add_paragraph()
    new_para._p.getparent().remove(new_para._p)
    new_p.getparent().replace(new_p, new_para._p)
    if style:
        new_para.style = style
    if text:
        new_para.add_run(text)
    return new_para


def add_field(paragraph, instruction, display):
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instruction)
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = str(display)
    r.append(t)
    fld.append(r)
    paragraph._p.append(fld)
    return fld


def add_caption(paragraph, label, number, title, source, bookmark_id, seq_instruction=None):
    clear_paragraph(paragraph)
    paragraph.style = "Caption"
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_keep_with_next(paragraph, False)
    set_keep_together(paragraph, True)
    paragraph.add_run(f"{label} ")
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bookmark_id))
    start.set(qn("w:name"), f"_Ref{label}{number}".replace(" ", ""))
    paragraph._p.append(start)
    add_field(paragraph, seq_instruction or f"SEQ {label} \\* ARABIC", number)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bookmark_id))
    paragraph._p.append(end)
    paragraph.add_run(f". {title} Fuente: {source}")
    return f"_Ref{label}{number}".replace(" ", "")


def add_ref(paragraph, label, bookmark, number, lead, tail):
    paragraph.add_run(lead)
    paragraph.add_run(f"{label} ")
    add_field(paragraph, f"REF {bookmark} \\h", number)
    paragraph.add_run(tail)


def replace_image(paragraph, image_path, width=6.05):
    clear_paragraph(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_keep_with_next(paragraph, True)
    set_keep_together(paragraph, True)
    paragraph.add_run().add_picture(str(image_path), width=Inches(width))


def move_after(node_paragraph, target_paragraph):
    target_paragraph._p.addnext(node_paragraph._p)


def insert_figure_block(after_paragraph, image_path, number, title, intro, interpretation, bookmark_id):
    intro_p = insert_paragraph_after(after_paragraph, style="Normal")
    intro_p.paragraph_format.space_before = Pt(6)
    intro_p.add_run(intro + " ")
    intro_p.add_run("La ")
    intro_p.add_run("Figura ")
    add_field(intro_p, f"REF _RefFigura{number} \\h", number)
    intro_p.add_run(" presenta esta evidencia.")
    set_keep_with_next(intro_p, True)

    img_p = insert_paragraph_after(intro_p, style="Normal")
    replace_image(img_p, image_path)

    cap_p = insert_paragraph_after(img_p, style="Caption")
    add_caption(cap_p, "Figura", number, title, "elaboración propia con resultados de la corrida run_20261013T193604Z_157556.", bookmark_id)

    post_p = insert_paragraph_after(cap_p, interpretation, style="Normal")
    post_p.paragraph_format.space_after = Pt(6)
    return post_p


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcPr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_border(cell, color="D9D9D9"):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tcPr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = borders.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), color)


doc = Document(SRC)

# Actualiza identificadores de corrida en todo el texto sin alterar el formato de los párrafos.
for p in list(doc.paragraphs) + [p for t in doc.tables for row in t.rows for cell in row.cells for p in cell.paragraphs]:
    for run in p.runs:
        if "run_20260924T195600Z_86a6f5" in run.text:
            run.text = run.text.replace("run_20260924T195600Z_86a6f5", "run_20261013T193604Z_157556")

# Localiza las quince figuras de contenido originales. La imagen de portada se excluye.
captions = [p for p in doc.paragraphs if p.style and p.style.name == "Caption" and p.text.strip().startswith("Figura ")]
images = [p for p in doc.paragraphs if p._p.xpath(".//w:drawing|.//w:pict")][1:]
assert len(captions) == 15, len(captions)
assert len(images) == 15, len(images)

figure_specs = [
    ("I03_cobertura_semanal.png", "Cobertura semanal de las fuentes integradas en el panel analítico.", "La cobertura distingue semanas observadas de periodos sin información y evita interpretar automáticamente una ausencia como importe igual a cero.", "La lectura conjunta de fechas y fuentes permite delimitar el tramo con información comparable antes de construir variables o evaluar modelos."),
    ("I01_flujo_proceso.png", "Flujo metodológico desde la integración de fuentes hasta la asignación presupuestaria y la validación.", "El proceso completo se organizó como una secuencia reproducible que conecta auditoría, modelado, evaluación y comunicación del presupuesto.", "La separación entre preparación, selección interna y evaluación final reduce el riesgo de utilizar información futura y conserva la trazabilidad de cada resultado."),
    ("I04_serie_semanal.png", "Serie semanal del importe elegible y delimitación de los periodos de evaluación.", "La inspección inicial de la variable objetivo debe preceder al diagnóstico y a la comparación de modelos.", "La serie muestra cambios de nivel, semanas con valor nulo y episodios de mayor dispersión; por ello, el desempeño no debe resumirse con una única partición aleatoria."),
    ("ST02_tendencia_movil.png", "Evolución local del importe semanal mediante media y mediana móviles de trece semanas.", "Para describir la evolución local sin confundirla con un pronóstico, se compararon dos resúmenes móviles sobre la serie observada.", "La distancia entre media y mediana móvil revela la influencia de semanas de importe elevado. Estas curvas son descriptivas y no sustituyen la validación temporal."),
    ("ST03_histograma_importes.png", "Distribución de los importes semanales positivos.", "La distribución marginal complementa la lectura cronológica y permite valorar asimetría y concentración.", "La concentración en importes bajos y la cola hacia valores altos justifican reportar métricas sensibles y robustas, además de conservar la escala monetaria en la interpretación."),
    ("I06_mapa_composicion.png", "Composición porcentual observada por categoría analítica.", "La asignación del total exige examinar por separado la estructura composicional de las compras.", "El patrón confirma que las participaciones no son independientes: el aumento relativo de una categoría modifica necesariamente el espacio disponible para las demás."),
    ("I05_pareto_categorias.png", "Concentración acumulada del gasto por categoría analítica.", "La selección de categorías elegibles se evaluó también desde su contribución acumulada al importe.", "La concentración observada permite priorizar categorías de mayor peso sin eliminar automáticamente componentes pequeños que sean operativamente necesarios."),
    ("I02_validacion_temporal.png", "Esquema de validación temporal con orígenes sucesivos y horizonte de cuatro semanas.", "La evaluación reproduce el momento en que se emitiría el presupuesto y mantiene el orden temporal de la información.", "Cada origen utiliza únicamente el historial disponible y reserva las semanas posteriores para medir error, lo que evita una comparación optimista por fuga temporal."),
    ("I14_ablaciones.png", "Análisis de ablación de las fuentes y componentes del modelo.", "Para determinar qué información aporta valor se compararon configuraciones que retiran grupos de predictores de manera controlada.", "Las diferencias deben interpretarse como sensibilidad dentro de estas particiones y no como una prueba universal de superioridad de una fuente."),
    ("I16_presupuesto_agregado.png", "Asignación agregada del presupuesto pronosticado por categoría analítica.", "La salida operativa integra el pronóstico monetario con las participaciones estimadas por categoría.", "La presentación agregada facilita revisar prioridades de compra y comprobar que la suma de asignaciones coincide con el total pronosticado."),
    (None, None, None, None),
    ("I08_rmse.png", "RMSE por modelo y horizonte de pronóstico.", "El rendimiento monetario se comparó por horizonte para evitar que un promedio global oculte degradaciones específicas.", "Un RMSE menor indica menor penalización cuadrática del error; su lectura se complementa con MAE y con el número de observaciones disponible en cada horizonte."),
    ("I10_error_composicion_categoria.png", "Error absoluto de participación por categoría analítica.", "Además del total monetario, se examinó dónde se concentra el error de distribución entre categorías.", "Las categorías con mayor error requieren cautela en la asignación, aunque su impacto operativo también depende de su participación en el presupuesto."),
    ("I07_observado_pronosticado.png", "Valores observados y pronosticados del importe semanal en los horizontes evaluados.", "La comparación directa entre valores observados y pronosticados permite complementar las métricas agregadas.", "La proximidad a la referencia visual debe interpretarse junto con el horizonte, pues una coincidencia puntual no sustituye el resumen de errores de todos los orígenes."),
    ("I12_H1_monetario.png", "Diferencias pareadas de pérdida monetaria entre el modelo propuesto y la línea base.", "El contraste de la hipótesis se formuló con pérdidas pareadas para conservar la correspondencia entre origen y horizonte.", "Las diferencias negativas favorecen al modelo propuesto; la conclusión debe considerar su dispersión y el tamaño efectivo de la evaluación, no sólo el signo del promedio."),
]

bookmark_id = 1000
figure_no = 0
control_anchor = None
for idx, (cap, img, spec) in enumerate(zip(captions, images, figure_specs), start=1):
    if spec[0] is None:
        # La antigua figura de controles se reemplaza más adelante por una tabla editable.
        control_anchor = cap
        img._p.getparent().remove(img._p)
        clear_paragraph(cap)
        continue
    figure_no += 1
    filename, title, intro, interpretation = spec
    replace_image(img, FIGS / filename)
    move_after(cap, img)
    bookmark_id += 1
    bookmark = add_caption(cap, "Figura", figure_no, title, "elaboración propia con resultados de la corrida run_20261013T193604Z_157556.", bookmark_id)
    # Se incorpora referencia cruzada en el párrafo inmediatamente anterior al elemento.
    intro_p = insert_paragraph_after(img._p.getprevious() if False else cap, "", style="Normal")
    # Reordenar: intro -> imagen -> pie -> interpretación.
    intro_p._p.getparent().remove(intro_p._p)
    img._p.addprevious(intro_p._p)
    intro_p.add_run(intro + " Como se muestra en la Figura ")
    add_field(intro_p, f"REF {bookmark} \\h", figure_no)
    intro_p.add_run(", la evidencia se presenta de manera independiente.")
    set_keep_with_next(intro_p, True)
    post_p = insert_paragraph_after(cap, interpretation, style="Normal")
    post_p.paragraph_format.space_after = Pt(6)

# Añade diagnósticos básicos independientes después del histograma.
anchor = captions[4]._p.getnext()
anchor_p = None
for p in doc.paragraphs:
    if p._p is anchor:
        anchor_p = p
        break
if anchor_p is None:
    anchor_p = captions[4]

for file_name, title, intro, interpretation in [
    ("ST04_caja_importes.png", "Dispersión y valores extremos del importe semanal positivo.", "El diagrama de caja resume la dispersión sin imponer una distribución simétrica.", "Los puntos más alejados se conservaron como observaciones a auditar; su magnitud no constituye por sí sola evidencia de error de captura."),
    ("ST05_rezago_1.png", "Relación entre importes de semanas consecutivas.", "La gráfica de rezago examina visualmente la continuidad entre una semana y la siguiente.", "La dispersión respecto de la diagonal indica que el último valor no basta para explicar toda la variación, aunque existen agrupamientos asociados a semanas de importe reducido."),
    ("ST06_autocorrelacion.png", "Autocorrelación del importe semanal hasta veintiséis rezagos.", "La dependencia lineal se examinó mediante la función de autocorrelación antes de definir predictores rezagados.", "Las correlaciones positivas en varios rezagos justifican considerar memoria temporal, pero las bandas son referencias aproximadas y no demuestran causalidad ni estabilidad fuera de la muestra."),
]:
    figure_no += 1
    bookmark_id += 1
    anchor_p = insert_figure_block(anchor_p, FIGS / file_name, figure_no, title, intro, interpretation, bookmark_id)

# Convierte la imagen de controles en una tabla editable.
if control_anchor is not None:
    clear_paragraph(control_anchor)
    control_anchor.style = "Normal"
    control_anchor.add_run("Los controles de coherencia se resumen en la Tabla ")
    add_field(control_anchor, "REF _RefTabla6 \\h", 6)
    control_anchor.add_run(", que documenta el resultado de cada comprobación antes de emitir el presupuesto.")
    set_keep_with_next(control_anchor, True)

    cap_tbl = insert_paragraph_after(control_anchor, style="Caption")
    bookmark_id += 1
    add_caption(cap_tbl, "Tabla", 6, "Controles de coherencia de la corrida validada.", "elaboración propia con base en controles.csv de la corrida run_20261013T193604Z_157556.", bookmark_id, "SEQ Tabla \\r 6 \\* ARABIC")
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.autofit = False
    headers = ["Control", "Resultado", "Detalle"]
    for j, text in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = text
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade_cell(cell, "1F4E79")
        set_cell_border(cell)
        for r in cell.paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.bold = True
            r.font.size = Pt(9)
    import pandas as pd
    controls = pd.read_csv(RUN / "controles.csv")
    for i, row in controls.iterrows():
        cells = table.add_row().cells
        values = [str(row["control"]), "Aprobado" if bool(row["aprobado"]) else "No aprobado", "Sin observaciones" if pd.isna(row.get("detalle")) else str(row.get("detalle"))]
        for j, value in enumerate(values):
            cells[j].text = value
            cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(cells[j])
            if i % 2:
                shade_cell(cells[j], "EAF2F8")
            for p in cells[j].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8.5)
        cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.columns[0].width = Inches(3.65)
    table.columns[1].width = Inches(1.0)
    table.columns[2].width = Inches(1.45)
    cap_tbl._p.addnext(table._tbl)
    post_tbl = insert_paragraph_after(cap_tbl, "Los siete controles fueron aprobados. En conjunto verifican reconciliación, no negatividad, cierre porcentual, reproducibilidad y disponibilidad de los cuatro horizontes futuros.", style="Normal")
    table._tbl.addnext(post_tbl._p)

# Añade el segundo contraste de H1 como figura independiente después de la última figura del cuerpo.
last_cap = captions[-1]
last_post = last_cap
figure_no += 1
bookmark_id += 1
insert_figure_block(last_post, FIGS / "I13_H1_composicion.png", figure_no,
                    "Diferencias pareadas de pérdida composicional entre el modelo propuesto y la línea base.",
                    "El componente composicional de la hipótesis se presenta por separado para evitar mezclar escalas y criterios de error.",
                    "Las diferencias negativas favorecen al método propuesto. La inferencia se limita a los orígenes y horizontes observados y debe leerse junto con la evidencia monetaria.", bookmark_id)

# Elimina pies residuales que sólo repetían la fuente de figuras sustituidas.
for p in list(doc.paragraphs):
    if p.style and p.style.name == "Caption" and p.text.strip().lower().startswith("fuente:"):
        p._p.getparent().remove(p._p)

# Anexo nuevo para diagnósticos complementarios ya aprobados.
doc.add_page_break()
doc.add_heading("Anexo C Diagnósticos complementarios y sensibilidad", level=1)
anchor = doc.paragraphs[-1]
for file_name, title, intro, interpretation in [
    ("I09_mae.png", "MAE por modelo y horizonte de pronóstico.", "El MAE se reporta como complemento del RMSE para expresar el error absoluto en unidades monetarias.", "La comparación conjunta permite identificar si el orden entre modelos depende de la penalización adicional que el RMSE asigna a errores grandes."),
    ("I11_error_composicion_macro.png", "Error composicional agregado por macrogrupo.", "La agregación por macrogrupo permite revisar si los errores por categoría se concentran en familias operativas relacionadas.", "Este resumen no reemplaza el análisis por categoría, pero ayuda a priorizar la revisión gerencial de las asignaciones."),
    ("I15_presupuesto_semanal.png", "Asignación semanal detallada del presupuesto pronosticado.", "El detalle semanal se conserva como evidencia operativa complementaria de la asignación agregada.", "La desagregación permite revisar cambios entre horizontes sin saturar el capítulo principal de resultados."),
]:
    figure_no += 1
    bookmark_id += 1
    anchor = insert_figure_block(anchor, FIGS / file_name, figure_no, title, intro, interpretation, bookmark_id)

# Separa las tablas que contenían dos o tres ecuaciones consecutivas. Cada
# ecuación conserva su numeración y recibe un párrafo explicativo propio.
equation_explanations = {
    22: "La Ecuación 22 define la estimación penalizada mediante la suma del error cuadrático y la penalización L1. El parámetro de regularización controla cuánto se contraen los coeficientes y, por tanto, debe seleccionarse únicamente con datos de entrenamiento.",
    23: "La Ecuación 23 presenta la alternativa con penalización L2. A diferencia de Lasso, esta formulación reduce la magnitud de los coeficientes sin imponer necesariamente valores exactamente iguales a cero.",
    26: "La Ecuación 26 define el MAE por horizonte como el promedio de los errores absolutos. La medida conserva unidades monetarias y asigna el mismo peso lineal a cada desviación.",
    27: "La Ecuación 27 define el RMSE por horizonte. Al elevar los errores al cuadrado, la medida penaliza con mayor intensidad las desviaciones de mayor magnitud.",
    31: "La Ecuación 31 agrega los importes elegibles por categoría para obtener el total semanal. La igualdad se calcula sólo con los registros incluidos por las reglas documentadas de alcance.",
    32: "La Ecuación 32 expresa la imputación del importe de una categoría mediante el promedio de sus semanas observadas. El procedimiento se aplica exclusivamente a las semanas marcadas como ausentes y no reemplaza ceros confirmados.",
    33: "La Ecuación 33 aplica el mismo principio a las ventas semanales. El conjunto de observaciones válidas se define con la cobertura disponible antes de calcular el promedio.",
    34: "La Ecuación 34 calcula la participación de cada categoría respecto del total semanal elegible. La expresión sólo se evalúa cuando el denominador es positivo.",
    35: "La Ecuación 35 obtiene el remanente elegible después de sumar las categorías principales. El operador máximo evita participaciones negativas por diferencias numéricas o de redondeo.",
    36: "La Ecuación 36 estima una participación histórica ponderada. El parámetro alfa controla el decaimiento de las observaciones anteriores y se determina sin usar información posterior al origen.",
    37: "La Ecuación 37 combina el pronóstico estadístico y el de aprendizaje automático. El peso depende del horizonte y se selecciona en la validación interna.",
    38: "La Ecuación 38 describe la corrección residual aplicada al pronóstico ARIMA y restringe el resultado a valores no negativos. El residual utilizado por la red se calcula respecto de la predicción estadística.",
    39: "La Ecuación 39 formaliza los orígenes, la ventana de entrenamiento y la semana objetivo. Esta notación garantiza que la evaluación respete el orden temporal.",
    40: "La Ecuación 40 reúne las expresiones de RMSE y MAE utilizadas en la salida operativa. Ambas se calculan por horizonte sobre los mismos orígenes disponibles, aunque conservan distinta sensibilidad a errores grandes.",
    41: "La Ecuación 41 escala el MAE con una referencia ingenua calculada dentro del historial de entrenamiento. El denominador no utiliza semanas de la evaluación final.",
    42: "La Ecuación 42 agrega los cuatro horizontes y calcula la participación de cada categoría en el presupuesto consolidado. La suma de asignaciones debe reconciliarse con el total agregado.",
}

for table in list(doc.tables):
    xml = table._tbl.xml
    if "EcuacionMT" not in xml or len(table.rows) <= 1:
        continue
    original = table._tbl
    parent = original.getparent()
    insert_at = parent.index(original)
    for source_index, row in enumerate(table.rows):
        eq_text = row.cells[-1].text
        match = re.search(r"(\d+)", eq_text)
        eq_no = int(match.group(1)) if match else None
        new_tbl = deepcopy(original)
        new_rows = new_tbl.findall(qn("w:tr"))
        for idx, tr in enumerate(new_rows):
            if idx != source_index:
                new_tbl.remove(tr)
        parent.insert(insert_at, new_tbl)
        insert_at += 1
        p_el = OxmlElement("w:p")
        parent.insert(insert_at, p_el)
        insert_at += 1
        p_obj = doc.add_paragraph()
        p_obj._p.getparent().remove(p_obj._p)
        p_el.getparent().replace(p_el, p_obj._p)
        p_obj.style = "Normal"
        p_obj.add_run(equation_explanations.get(eq_no, f"La Ecuación {eq_no} se interpreta de acuerdo con las variables definidas en el texto precedente."))
        set_keep_together(p_obj, True)
    parent.remove(original)

# Reconstruye el índice de imágenes como una lista estática y verificable. Se
# evita actualizar el campo TOF heredado porque el documento fuente contiene
# límites de campo frágiles que pueden abarcar contenido posterior.
figure_captions_final = [p for p in doc.paragraphs if p.style and p.style.name == "Caption" and p.text.strip().startswith("Figura")]
figure_titles = [re.sub(r"^Figura\s*\.\s*", "", p.text.strip()).split(" Fuente:")[0].strip() for p in figure_captions_final]
paras_now = doc.paragraphs
idx_heading = next(i for i, p in enumerate(paras_now) if p.text.strip() == "ÍNDICE DE IMÁGENES")
old_entries = []
for p in paras_now[idx_heading + 1:]:
    if p.style and p.style.name == "toc 1":
        old_entries.append(p)
    elif old_entries:
        break
for n, p in enumerate(old_entries, start=1):
    clear_paragraph(p)
    if n <= len(figure_titles):
        p.add_run(f"Figura {n}. {figure_titles[n-1]}\tPÁG")
    else:
        p._p.getparent().remove(p._p)
anchor_index = old_entries[min(len(old_entries), len(figure_titles)) - 1]
for n in range(len(old_entries) + 1, len(figure_titles) + 1):
    anchor_index = insert_paragraph_after(anchor_index, f"Figura {n}. {figure_titles[n-1]}\tPÁG", style="toc 1")

# Añade la nueva tabla de controles al índice de tablas sin actualizar el campo
# heredado. El número de página se sustituye después del primer render.
paras_now = doc.paragraphs
tbl_heading = next(i for i, p in enumerate(paras_now) if p.text.strip() == "ÍNDICE DE TABLAS")
tbl_entries = []
for p in paras_now[tbl_heading + 1:]:
    if p.style and p.style.name == "toc 1":
        tbl_entries.append(p)
    elif tbl_entries:
        break
if not any("Tabla 6." in p.text for p in tbl_entries):
    insert_paragraph_after(tbl_entries[-1], "Tabla 6. Controles de coherencia de la corrida validada.\tPÁG", style="toc 1")

# Reglas editoriales de párrafo y ecuaciones.
equation_pat = re.compile(r"ecuaci[oó]n\s*\((\d+)\)", re.I)
audit_rows = []
for i, p in enumerate(doc.paragraphs):
    text = " ".join(p.text.split())
    is_caption = bool(p.style and p.style.name == "Caption")
    has_image = bool(p._p.xpath(".//w:drawing|.//w:pict"))
    math_count = len(p._p.xpath(".//m:oMath"))
    refs = len(p._p.xpath(".//w:fldSimple[contains(@w:instr,'REF ')]"))
    if has_image or is_caption or math_count or equation_pat.search(text):
        audit_rows.append({"parrafo": i, "estilo": p.style.name if p.style else "", "imagen": has_image,
                           "pie": is_caption, "objetos_matematicos": math_count,
                           "referencias_cruzadas": refs, "texto": text[:300]})
    # Evita ecuaciones aisladas del párrafo que las explica.
    if math_count or equation_pat.search(text):
        set_keep_together(p, True)

with AUDIT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=audit_rows[0].keys())
    writer.writeheader()
    writer.writerows(audit_rows)

# Solicita a Word actualizar índices, numeración y referencias al abrir.
settings = doc.settings._element
update = settings.find(qn("w:updateFields"))
if update is None:
    update = OxmlElement("w:updateFields")
    settings.append(update)
update.set(qn("w:val"), "true")

# Metadatos de revisión.
doc.core_properties.title = "Modelo híbrido de inteligencia artificial para la planeación del presupuesto de abastecimiento"
doc.core_properties.comments = "Revisión 62: reorganización visual, gráficas básicas de series temporales, referencias cruzadas y explicación individual de elementos académicos."
doc.save(OUT)
print(OUT)
print(AUDIT)
print(f"Figuras numeradas: {figure_no}")
