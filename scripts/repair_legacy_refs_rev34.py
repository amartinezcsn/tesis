from pathlib import Path
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

DOC=Path(r"C:\Python\tesis\documentacion\TESIS_AGO2026_Rev34_(ZUJ)_22ago2026.docx")
d=Document(DOC)

mapping={
    '_Ref235633779': ('xref_ecuacion_15','ecuación (15)'),
    '_Ref235633852': ('xref_ecuacion_14','ecuación (14)'),
    '_Ref235634578': ('xref_ecuacion_13','ecuación (13)'),
    '_Ref235798613': ('xref_ecuacion_15','15'),
    '_Ref235798674': ('xref_ecuacion_14','14'),
    '_Ref235798729': ('xref_ecuacion_13','13'),
    '_Ref235634711': ('xref_ecuacion_11','ecuación (11)'),
}

def simple_ref(bookmark,result):
    f=OxmlElement('w:fldSimple'); f.set(qn('w:instr'),f' REF {bookmark} \\h ')
    r=OxmlElement('w:r'); t=OxmlElement('w:t'); t.text=result; r.append(t); f.append(r)
    return f

fixed=0
for p in d.paragraphs:
    children=list(p._p)
    i=0
    while i<len(children):
        node=children[i]
        begins=node.findall('.//'+qn('w:fldChar'))
        if not any(x.get(qn('w:fldCharType'))=='begin' for x in begins):
            i+=1; continue
        end=i; code=''
        while end<len(children):
            code+=''.join(x.text or '' for x in children[end].findall('.//'+qn('w:instrText')))
            if any(x.get(qn('w:fldCharType'))=='end' for x in children[end].findall('.//'+qn('w:fldChar'))):
                break
            end+=1
        target=next((old for old in mapping if old in code),None)
        if target is None:
            i=end+1; continue
        bookmark,result=mapping[target]
        insert_at=p._p.index(children[i])
        for old in children[i:end+1]: p._p.remove(old)
        p._p.insert(insert_at,simple_ref(bookmark,result))
        fixed+=1
        children=list(p._p); i=insert_at+1

d.save(DOC)
print(f'legacy_refs_fixed={fixed}')
