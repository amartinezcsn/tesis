from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from shutil import copy2
from datetime import datetime

source = Path(r'C:\Python\tesis\documentacion\TESIS_AGO2026_Rev42_(ZUJ)_11sep2026.docx')
out = source.parents[1] / 'output' / 'revision42_hipotesis'
out.mkdir(parents=True, exist_ok=True)
backup = out / ('respaldo_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.docx')
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(source) as z:
    entries = [(i, z.read(i.filename)) for i in z.infolist()]
original = dict((i.filename, b) for i,b in entries)
root = etree.fromstring(original['word/document.xml'])
body = root.find('w:body',ns)
def text(p):
    return ''.join(p.xpath('.//w:t/text()',namespaces=ns)).strip()
ps = body.findall('w:p',ns)
h1 = [p for p in ps if text(p).startswith('H1.')]
h2 = [p for p in ps if text(p).startswith('H2.')]
h2heading = [p for p in ps if text(p) == 'Hipótesis de investigación (H2)']
assert len(h1) == len(h2) == len(h2heading) == 1
value = ('H1. El modelo híbrido que integre métodos estadísticos y aprendizaje automático, '
         'junto con el procedimiento de distribución porcentual entre los principales insumos, '
         'presentará menores errores de pronóstico fuera de muestra que los respectivos modelos '
         'de referencia para estimar el importe total semanal de compras y su composición porcentual '
         'en Cup&Cake, utilizando información disponible al momento del pronóstico y los mismos '
         'periodos y horizontes de evaluación.')
assert not h1[0].xpath('.//w:ins | .//w:del | .//w:fldChar',namespaces=ns)
unchanged = [etree.tostring(p) for p in body if p not in [h1[0],h2[0],h2heading[0]]]
nodes = h1[0].xpath('.//w:t',namespaces=ns)
nodes[0].text = value
for n in nodes[1:]:
    n.text = ''
body.remove(h2[0])
body.remove(h2heading[0])
assert unchanged == [etree.tostring(p) for p in body if p is not h1[0]]
copy2(source, backup)
candidate = out / 'actualizado.docx'
with ZipFile(candidate,'w') as z:
    for info,data in entries:
        z.writestr(info, etree.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True) if info.filename == 'word/document.xml' else data)
with ZipFile(candidate) as z:
    assert z.testzip() is None
    assert all(z.read(name) == data for name,data in original.items() if name != 'word/document.xml')
copy2(candidate,source)
print(value)
print('Respaldo: ' + str(backup))
