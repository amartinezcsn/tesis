from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


SOURCE = Path(r"C:\Python\tesis\documentacion\TESIS_OCT2026_Rev64_(ZUJ)_Correcciones_Director.docx")
OUTPUT = Path(r"C:\Python\tesis\documentacion\TESIS_OCT2026_Rev65_(ZUJ)_Times_New_Roman.docx")
FONT = "Times New Roman"


def set_rfonts(rpr):
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn(f"w:{attr}"), FONT)
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        key = qn(f"w:{attr}")
        if key in rfonts.attrib:
            del rfonts.attrib[key]


def under_math(element):
    parent = element.getparent()
    while parent is not None:
        if parent.tag in {qn("m:oMath"), qn("m:oMathPara")}:
            return True
        parent = parent.getparent()
    return False


doc = Document(SOURCE)

# Define Times New Roman en todos los estilos, incluidos los estilos internos
# empleados por índices, captions, listas, tablas, encabezados y pies.
for style in doc.styles:
    if hasattr(style, "font"):
        style.font.name = FONT
    if hasattr(style._element, "get_or_add_rPr"):
        rpr = style._element.get_or_add_rPr()
        set_rfonts(rpr)

# Refuerza el valor predeterminado del documento para texto sin formato directo.
styles_root = doc.styles._element
doc_defaults = styles_root.find(qn("w:docDefaults"))
if doc_defaults is None:
    doc_defaults = OxmlElement("w:docDefaults")
    styles_root.insert(0, doc_defaults)
rpr_default = doc_defaults.find(qn("w:rPrDefault"))
if rpr_default is None:
    rpr_default = OxmlElement("w:rPrDefault")
    doc_defaults.insert(0, rpr_default)
rpr = rpr_default.find(qn("w:rPr"))
if rpr is None:
    rpr = OxmlElement("w:rPr")
    rpr_default.append(rpr)
set_rfonts(rpr)

# Homologa cualquier fuente aplicada directamente en el documento y sus partes
# relacionadas. Se excluyen deliberadamente los objetos matemáticos OMML.
parts = {doc.part}
for rel in doc.part.rels.values():
    if rel.is_external:
        continue
    target = rel.target_part
    if hasattr(target, "element"):
        parts.add(target)
for part in parts:
    root = getattr(part, "element", None)
    if root is None:
        continue
    for rpr_node in root.xpath(".//w:rPr"):
        if not under_math(rpr_node):
            set_rfonts(rpr_node)

doc.core_properties.comments = (
    "Revisión 65: homologación tipográfica integral a Times New Roman; "
    "Cambria Math se conserva exclusivamente en ecuaciones de Word."
)
doc.save(OUTPUT)
print(OUTPUT)
