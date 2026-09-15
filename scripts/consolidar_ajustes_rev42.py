from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from copy import deepcopy
import json

ROOT=Path(r'C:\Python\tesis')
SOURCE=ROOT/'output/revision42_marco_teorico/TESIS_Rev42_marco_actualizado.docx'
TARGET=ROOT/'documentacion/TESIS_AGO2026_Rev42_(ZUJ)_12sep2026_actualizada.docx'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'w':W,'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(SOURCE) as z:
    entries=[(i,z.read(i.filename)) for i in z.infolist()]
root=E.fromstring(dict((i.filename,b) for i,b in entries)['word/document.xml'])
changes=[]
for p in root.xpath('//w:body/w:p',namespaces=NS):
    old=''.join(p.xpath('.//w:t/text()',namespaces=NS))
    new=old
    if old.startswith('El presente marco teórico'):
        new='El presente marco teórico desarrolla los fundamentos conceptuales y matemáticos que sustentan la propuesta de un modelo híbrido para pronosticar el importe total semanal de compras y su distribución porcentual entre los principales insumos de Cup&Cake. Para ello, se abordan la planeación del presupuesto de abastecimiento, las características de las series temporales semanales, los métodos estadísticos y de aprendizaje automático, y las estrategias para su integración. Posteriormente, se examinan los fundamentos de la distribución porcentual de las compras, el tratamiento de datos limitados y la evaluación del desempeño predictivo fuera de muestra mediante métricas de error monetario y de participación porcentual. Finalmente, se analiza el uso de los pronósticos como apoyo a la planeación de compras en el contexto de la microempresa (Hyndman & Athanasopoulos, 2021; Power, 2002).'
    elif old.startswith('Para contrastar las hipótesis, H1'):
        new='Para contrastar H1, se comparará el modelo híbrido y el procedimiento de distribución porcentual con sus respectivos modelos de referencia, utilizando las mismas semanas y horizontes de evaluación y únicamente información disponible antes de cada pronóstico. Se evaluarán por separado el error del importe total semanal y el error de participación de los principales insumos. Los análisis con y sin variables exógenas tendrán carácter complementario y no constituirán una segunda hipótesis. La evidencia favorable deberá abarcar ambos componentes de H1; una mejora aislada en el importe total no será suficiente para respaldarla. El protocolo de contraste, las métricas principales y el tratamiento de comparaciones múltiples se especificarán antes de examinar el conjunto de evaluación final.'
    elif old.startswith('La evaluación comparativa calculará') and 'H2' in old:
        new='La evaluación comparativa calculará la discrepancia entre los valores observados y pronosticados del importe total semanal y de la participación porcentual de los principales insumos. H1 se contrastará frente a las respectivas líneas base. La comparación de configuraciones equivalentes con y sin variables exógenas se utilizará como análisis complementario del aporte de dichas variables.'
    elif old.startswith('Ninguna configuración estadística') and 'H2' in old:
        new='El respaldo empírico de H1 se determinará una vez desarrollado y evaluado el modelo híbrido y el procedimiento de distribución porcentual. No se anticipa su aceptación o rechazo. El análisis complementario de variables exógenas permitirá examinar si su incorporación aporta mejoras bajo configuraciones y periodos comparables, sin formular una segunda hipótesis.'
    elif old.startswith('H1 se contrastó principalmente'):
        new='El contraste de H1 se realizará después del desarrollo del modelo y de la evaluación fuera de muestra. Se reportarán por separado los errores del importe total semanal y de la distribución porcentual, junto con sus referencias y la incertidumbre de las diferencias. Mientras no se complete este procedimiento, no corresponde afirmar que la hipótesis ha sido respaldada o rechazada.'
    else:
        new=new.replace('el contraste de H1 y H2','el contraste de H1').replace('aceptar H1 o H2','contrastar H1').replace('contrastes H1 y H2','contraste de H1')
    if new!=old:
        ts=p.xpath('.//w:t',namespaces=NS)
        ts[0].text=new
        for t in ts[1:]: t.text=''
        changes.append({'before':old,'after':new})
assert len(changes)==9,len(changes)
xml=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(TARGET,'w') as z:
    for i,b in entries:z.writestr(i,xml if i.filename=='word/document.xml' else b)
with ZipFile(TARGET) as z: assert z.testzip() is None
assert not root.xpath('//w:t[contains(text(),"H2")]',namespaces=NS)
report={'output':str(TARGET),'changes':changes,'native_equations':len(root.xpath('//m:oMath',namespaces=NS)),'note':'Los capítulos de desarrollo y resultados heredados requieren una revisión de alcance independiente; no se han validado sus cifras.'}
(ROOT/'output/revision42_marco_teorico/consolidacion_12sep.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'output':str(TARGET),'paragraphs_changed':len(changes),'native_equations':report['native_equations']},ensure_ascii=False))
