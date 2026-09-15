from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree
from shutil import copy2
from datetime import datetime

source = Path(r'C:\Python\tesis\documentacion\TESIS_AGO2026_Rev42_(ZUJ)_11sep2026.docx')
backup_dir = source.parents[1] / 'output' / 'revision42_justificacion'
backup_dir.mkdir(parents=True, exist_ok=True)
backup = backup_dir / ('respaldo_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.docx')
copy2(source, backup)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
w = '{' + ns['w'] + '}'
with ZipFile(source) as z:
    entries = [(i, z.read(i.filename)) for i in z.infolist()]
root = etree.fromstring(dict((i.filename, b) for i, b in entries)['word/document.xml'])
paragraphs = root.findall('w:body/w:p', ns)
def text(p):
    return ''.join(p.itertext()) if False else ''.join(p.xpath('.//w:t/text()', namespaces=ns))
start = next(i for i,p in enumerate(paragraphs) if text(p).strip() == 'Justificación')
end = next(i for i in range(start+1, len(paragraphs)) if text(paragraphs[i]).strip() == 'Hipótesis')
targets = [p for p in paragraphs[start+1:end] if text(p).strip() and text(p).strip() not in {'Relevancia social','Conveniencia','Valor teórico','Implicaciones prácticas'}]
replacement = [
'Esta investigación se propone generar evidencia sobre el uso de herramientas de pronóstico semanal en una microempresa con recursos tecnológicos y analíticos limitados. Las restricciones financieras, tecnológicas y de personal especializado dificultan que las microempresas adopten soluciones basadas en datos. Por ello, evaluar modelos a partir de la información disponible permitirá identificar alternativas cuya pertinencia pueda valorarse en función de sus capacidades operativas (Alekseeva et al., 2021; Poveda-Valverde & Fierro Barragán, 2026).',
'En Cup&Cake, el estudio buscará determinar si el modelo híbrido mejora la estimación del importe semanal de compras y su distribución porcentual entre los principales insumos frente a modelos de referencia. Los resultados podrían aportar información útil para el responsable de la planeación del presupuesto de abastecimiento. Asimismo, el procedimiento podrá servir como referencia para otras microempresas con condiciones semejantes, aunque su aplicación requerirá evaluar las características y los datos de cada negocio.',
'El estudio atiende una necesidad operativa concreta de Cup&Cake: estimar, con horizontes de una a cuatro semanas, el importe total de las compras y su distribución porcentual entre los principales insumos. Se propone aprovechar los registros históricos de ventas y compras e incorporar variables exógenas disponibles al momento del pronóstico para desarrollar un procedimiento de apoyo a la planeación del presupuesto de abastecimiento.',
'Se comparará la precisión del modelo híbrido con la de modelos de referencia mediante validación temporal de ventana deslizante. Este contraste permitirá determinar si la integración de métodos estadísticos y aprendizaje automático aporta mejoras en el pronóstico fuera de muestra frente a alternativas más sencillas, sin presuponer la superioridad de una mayor complejidad algorítmica (Makridakis et al., 2018; Spiliotis et al., 2022).',
'El valor teórico esperado de la investigación consiste en aportar evidencia empírica sobre el desempeño de métodos de pronóstico semanal en un contexto de datos limitados e intermitencia de las compras. La literatura señala que la precisión de los modelos depende de la cantidad y calidad de los datos, la granularidad temporal, las variables disponibles y el protocolo de evaluación; por tanto, su superioridad requiere contrastación empírica (Hewamalage et al., 2021; Giannopoulos et al., 2025).',
'El estudio permitirá examinar la precisión de un modelo híbrido que integre métodos estadísticos y aprendizaje automático, así como la de un procedimiento de distribución porcentual del importe semanal entre los principales insumos. También se analizará si las variables exógenas disponibles antes de cada pronóstico aportan información adicional. La contribución prevista será principalmente empírica y metodológica, circunscrita al caso de estudio, y podrá orientar investigaciones posteriores en microempresas con características semejantes.',
'Se propone desarrollar para Cup&Cake un procedimiento reproducible para depurar e integrar los registros diarios, agregarlos semanalmente, construir variables predictivas, generar pronósticos y estimar la distribución porcentual del importe entre los principales insumos. Su precisión se evaluará fuera de muestra mediante métricas de error monetario y de participación. Se prevé presentar los resultados en un tablero de inteligencia de negocios que permita consultar el importe semanal esperado de compras, su consolidado mensual y la distribución presupuestaria entre los principales insumos.',
'El tablero tendrá como propósito apoyar la planeación y revisión del presupuesto de abastecimiento. No generará órdenes automáticas de compra ni calculará cantidades físicas por insumo, pues estas funciones requerirían información adicional sobre recetas, existencias, merma, costos de faltante, tiempos de entrega y unidades de medida homologadas. Los posibles beneficios operativos dependerán de los resultados obtenidos y de su posterior aplicación en la empresa.',
'La investigación se justifica por la necesidad de evaluar si un modelo híbrido que integre métodos estadísticos y aprendizaje automático puede mejorar el pronóstico del importe semanal de compras y su distribución porcentual entre los principales insumos de Cup&Cake. Se propone contrastar su precisión frente a modelos de referencia mediante evaluación temporal, con el propósito de aportar elementos para la planeación del presupuesto de abastecimiento. Su alcance no comprende la medición de efectos sobre inventarios, merma, rentabilidad o expansión comercial.'
]
assert len(targets) == len(replacement), (len(targets), len(replacement))
for p, value in zip(targets, replacement):
    assert not p.xpath('.//w:ins | .//w:del | .//w:fldChar | .//w:commentRangeStart', namespaces=ns), 'Complex paragraph needs manual handling'
    nodes = p.xpath('.//w:t', namespaces=ns)
    assert nodes
    nodes[0].text = value
    for node in nodes[1:]:
        node.text = ''
new_xml = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
temp = backup_dir / 'actualizado.docx'
with ZipFile(temp, 'w', ZIP_DEFLATED) as z:
    for info, data in entries:
        z.writestr(info, new_xml if info.filename == 'word/document.xml' else data)
with ZipFile(temp) as z:
    assert z.testzip() is None
    verified = etree.fromstring(z.read('word/document.xml'))
    ps = verified.findall('w:body/w:p', ns)
    assert len(ps) == len(paragraphs)
    old = etree.fromstring(dict((i.filename,b) for i,b in entries)['word/document.xml'])
    oldps = old.findall('w:body/w:p',ns)
    assert all(etree.tostring(a) == etree.tostring(b) for i,(a,b) in enumerate(zip(oldps,ps)) if not start < i < end)
copy2(temp, source)
print(f'Actualizados {len(targets)} párrafos. Respaldo: {backup}')
