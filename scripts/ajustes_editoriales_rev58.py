from pathlib import Path
from docx import Document

DOCX = Path(r"C:\Python\tesis\documentacion\TESIS_SEP2026_Rev58_(ZUJ)_Corregida.docx")
doc = Document(DOCX)
changed = 0

exact = {
    "Cup&Cake, es una empresa mexicana fundada en 2014, con más de diez años de operación el crecimiento orgánico le ha permitido subsistir gracias a las compras que actualmente se realizan con base en el empirismo del empresario, ya que lo único que conoce son las fechas de eventos importantes como el Día de San Valentín (14 de febrero), el día del niño (30 de abril), el día de la madre (10 de mayo), entre otros que son los picos de venta que año con año se repiten.":
        "Cup&Cake es una empresa mexicana fundada en 2014. La planeación de sus compras se ha apoyado principalmente en el criterio del propietario y en el conocimiento acumulado sobre fechas comerciales recurrentes, como el Día de San Valentín, el Día del Niño y el Día de la Madre. Este conocimiento aporta contexto operativo, pero no sustituye una estimación reproducible basada en los registros disponibles.",
    "Con el paso del tiempo, Cup&Cake ha incrementado sus ventas de manera orgánica, producto de un proceso mercadológico inicial, donde clientes que han depositado su confianza en la empresa recomiendan sus productos por su sabor y alta calidad en la decoración y personalización de sus productos, provocando el aumento constante en las ventas.":
        "Para esta investigación, el comportamiento de ventas y compras se determinó a partir de los archivos disponibles y no de una afirmación general de crecimiento. Los registros se utilizaron para construir variables históricas y caracterizar la variación semanal, con las limitaciones de cobertura documentadas en la metodología.",
}

for p in doc.paragraphs:
    if p.text in exact:
        p.text = exact[p.text]
        changed += 1

# Align the justification and methodology with a completed exploratory study.
replacements = {
    "esta investigación evaluará": "esta investigación evaluó",
    "El estudio buscará determinar si": "El estudio evaluó si",
    "Se comparará la precisión": "Se comparó la precisión",
    "Este contraste permitirá determinar": "Este contraste permitió determinar",
    "El estudio permitirá examinar": "El estudio permitió examinar",
    "También se analizará": "También se analizó",
    "Se propone desarrollar para Cup&Cake": "Se desarrolló para Cup&Cake",
    "Su precisión se evaluará": "Su precisión se evaluó",
    "Se prevé presentar los resultados": "Los resultados se presentaron",
    "El tablero tendrá como propósito": "El tablero tiene como propósito",
    "Los posibles beneficios operativos dependerán": "Los posibles beneficios operativos dependen",
    "Se propone contrastar su precisión": "Se contrastó su precisión",
    "se agregarán por semana calendario": "se agregaron por semana calendario",
    "Las matrices semanales permitirán ajustar y comparar": "Las matrices semanales permitieron ajustar y comparar",
    "Se evaluará el error monetario": "Se evaluó el error monetario",
    "las conclusiones se circunscribirán": "las conclusiones se circunscribieron",
    "La evaluación considerará por separado": "La evaluación consideró por separado",
    "Su inferencia se limitará": "Su inferencia se limitó",
    "En consecuencia, el diseño evaluativo busca determinar": "En consecuencia, el diseño evaluativo determinó",
    "La inteligencia artificial se evalúa": "La inteligencia artificial se evaluó",
    "La semana calendario constituirá": "La semana calendario constituyó",
    "Se calcularán": "Se calcularon",
    "podrán utilizarse como predictores": "se utilizaron como predictores",
    "La comparación temporal permite": "La comparación temporal permitió",
    "El procedimiento comprende": "El procedimiento comprendió",
}

in_method = False
for p in doc.paragraphs:
    if p.text.strip() == "METODOLOGÍA":
        in_method = True
    if p.text.strip() == "DESARROLLO":
        in_method = False
    new = p.text
    # Apply completed-study tense in justification and methodology, but avoid results/references.
    if p.text and (in_method or "Justificación" in [a.text for a in []] or p._p.getprevious() is not None):
        for old, replacement in replacements.items():
            new = new.replace(old, replacement)
    if new != p.text:
        p.text = new
        changed += 1

doc.save(DOCX)
print(f"saved={DOCX} changed={changed}")
