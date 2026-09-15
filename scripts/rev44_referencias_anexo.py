from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
from copy import deepcopy
from lxml import etree as E
import json

p=Path('documentacion/TESIS_AGO2026_Rev44_(ZUJ)_12sep2026.docx')
raw=p.read_bytes()
with ZipFile(p) as z: items=[(i,z.read(i.filename)) for i in z.infolist()]
root=E.fromstring(dict((i.filename,b) for i,b in items)['word/document.xml'])
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}; W='{'+ns['w']+'}'
label='Anexo A'; name='Anexo_Diccionario_Datos'
text=lambda n: ''.join(n.xpath('.//w:t/text()',namespaces=ns))
before=text(root)
heading=[n for n in root.xpath('//w:p',namespaces=ns) if text(n)=='Anexo A Diccionario de datos']
assert len(heading)==1
assert not root.xpath('//w:bookmarkStart[@w:name="'+name+'"]',namespaces=ns)
id_=str(max([int(n.get(W+'id')) for n in root.xpath('//w:bookmarkStart',namespaces=ns)]+[0])+1)
def run(s,pr):
    r=E.Element(W+'r')
    if pr is not None:r.append(deepcopy(pr))
    t=E.SubElement(r,W+'t');t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=s
    return r
count=0
for t in list(root.xpath('//w:t',namespaces=ns)):
    if label not in (t.text or ''):continue
    r=t.getparent(); par=r.getparent()
    assert r.tag==W+'r' and par.tag==W+'p'
    assert len(r.findall(W+'t'))==1 and not r.xpath('.//w:fldChar|.//w:instrText',namespaces=ns)
    pr=r.find(W+'rPr'); bits=t.text.split(label); nodes=[]
    for j,bit in enumerate(bits):
        if bit:nodes.append(run(bit,pr))
        if j==len(bits)-1:break
        if par is heading[0]:
            start=E.Element(W+'bookmarkStart');start.set(W+'id',id_);start.set(W+'name',name)
            end=E.Element(W+'bookmarkEnd');end.set(W+'id',id_)
            nodes.extend([start,run(label,pr),end])
        else:
            field=E.Element(W+'fldSimple');field.set(W+'instr',' REF '+name+' \\h ');field.set(W+'dirty','true')
            field.append(run(label,pr));nodes.append(field);count+=1
    index=par.index(r);par.remove(r)
    for j,n in enumerate(nodes):par.insert(index+j,n)
assert count>=4 and text(root)==before
assert len(root.xpath('//w:bookmarkStart[@w:name="'+name+'"]',namespaces=ns))==1
assert len(root.xpath('//w:bookmarkEnd[@w:id="'+id_+'"]',namespaces=ns))==1
assert len(root.xpath('//w:fldSimple[contains(@w:instr,"REF '+name+'")]',namespaces=ns))==count
out=Path('output/rev44_referencias_anexo');out.mkdir(exist_ok=True)
backup=out/('Rev44_antes_REF_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.docx');backup.write_bytes(raw)
candidate=out/'Rev44_REF_verificado.docx'
with ZipFile(candidate,'w') as z:
    for i,b in items:z.writestr(i,E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True) if i.filename=='word/document.xml' else b)
with ZipFile(candidate) as z:
    assert z.testzip() is None
    assert all(z.read(i.filename)==b for i,b in items if i.filename!='word/document.xml')
assert p.read_bytes()==raw
p.write_bytes(candidate.read_bytes())
print(json.dumps({'references':count,'bookmark':name,'backup':str(backup),'visible_text_unchanged':True},ensure_ascii=False))
