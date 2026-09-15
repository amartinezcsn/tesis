"""Reemplazo acotado del marco, matemáticas OMML y bibliografía verificada."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile
from datetime import datetime
import hashlib, json, re, unicodedata
from lxml import etree as E

ROOT=Path(r'C:\Python\tesis')
SOURCE=ROOT/'documentacion/TESIS_AGO2026_Rev42_(ZUJ)_11sep2026.docx'
OUT=ROOT/'output/revision42_marco_teorico'
MD=OUT/'marco_nuevo.md'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
NS={'w':W,'m':M}
def el(tag, **attrs):
    prefix,name=tag.split(':'); n=E.Element('{'+{'w':W,'m':M}[prefix]+'}'+name)
    for k,v in attrs.items(): n.set('{'+{'w':W,'m':M}[prefix]+'}'+k,str(v))
    return n
def wrap(tag, nodes):
    n=el(tag)
    n.extend(nodes if isinstance(nodes,list) else [nodes]); return n
def run(s,italic=False):
    r=el('w:r'); pr=el('w:rPr'); pr.append(el('w:color',val='000000'))
    if italic: pr.append(el('w:i'))
    r.append(pr); t=el('w:t'); t.text=s; t.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); r.append(t); return r
def mr(s,plain=False):
    r=el('m:r')
    if plain: r.append(wrap('m:rPr',el('m:sty',val='p')))
    pr=el('w:rPr'); pr.append(el('w:rFonts',ascii='Cambria Math',hAnsi='Cambria Math')); pr.append(el('w:sz',val='23')); r.append(pr)
    t=el('m:t'); t.text=s; r.append(t); return r

class MathParser:
    """Subset required by this chapter, with true fractions, limits and scripts."""
    symbols={'alpha':'α','beta':'β','gamma':'γ','sigma':'σ','theta':'θ','phi':'φ','lambda':'λ','nu':'ν','rho':'ρ','varepsilon':'ε','Delta':'Δ','pi':'π','ell':'ℓ','mid':'|','geq':'≥','leq':'≤','in':'∈','pm':'±','ldots':'…','quad':'  ','arg':'arg','min':'min','sin':'sin','cos':'cos','log':'log'}
    def __init__(self,s): self.s=s; self.i=0
    def skip(self):
        while self.i<len(self.s) and self.s[self.i].isspace(): self.i+=1
    def group(self):
        self.skip()
        if self.i<len(self.s) and self.s[self.i]=='{':
            self.i+=1; out=self.sequence('}'); self.i+=1; return out
        return [self.atom()]
    def scripts(self):
        sub=sup=None; self.skip()
        while self.i<len(self.s) and self.s[self.i] in '_^':
            c=self.s[self.i]; self.i+=1; v=self.group()
            if c=='_': sub=v
            else: sup=v
            self.skip()
        return sub,sup
    def atom(self):
        self.skip()
        if self.s[self.i]=='{': return wrap('m:box',wrap('m:e',self.group()))
        if self.s[self.i]!='\\':
            c=self.s[self.i]; self.i+=1; return mr(c)
        self.i+=1; m=re.match('[A-Za-z]+',self.s[self.i:]); assert m,self.s[self.i:]
        cmd=m.group(); self.i+=len(cmd)
        if cmd in ['left','right']: return self.atom()
        if cmd=='frac': return wrap('m:f',[wrap('m:num',self.group()),wrap('m:den',self.group())])
        if cmd=='sqrt': return wrap('m:rad',[wrap('m:radPr',el('m:degHide',val='1')),el('m:deg'),wrap('m:e',self.group())])
        if cmd in ['hat','bar']:
            return wrap('m:acc',[wrap('m:accPr',el('m:chr',val='̂' if cmd=='hat' else '̄')),wrap('m:e',self.group())])
        if cmd=='mathrm':
            self.skip(); assert self.s[self.i]=='{'; end=self.s.index('}',self.i); text=self.s[self.i+1:end]; self.i=end+1; return mr(text,True)
        if cmd=='sum':
            sub,sup=self.scripts(); pr=el('m:naryPr'); pr.append(el('m:chr',val='∑')); pr.append(el('m:limLoc',val='undOvr'))
            if sub is None: pr.append(el('m:subHide',val='1'))
            if sup is None: pr.append(el('m:supHide',val='1'))
            body=self.scripted() if self.i<len(self.s) and self.s[self.i]!='}' else mr('')
            return wrap('m:nary',[pr,wrap('m:sub',sub or []),wrap('m:sup',sup or []),wrap('m:e',body)])
        assert cmd in self.symbols,cmd
        return mr(self.symbols[cmd],cmd in ['arg','min','sin','cos','log'])
    def scripted(self):
        base=self.atom(); sub,sup=self.scripts()
        if sub is not None and sup is not None: return wrap('m:sSubSup',[wrap('m:e',base),wrap('m:sub',sub),wrap('m:sup',sup)])
        if sub is not None: return wrap('m:sSub',[wrap('m:e',base),wrap('m:sub',sub)])
        if sup is not None: return wrap('m:sSup',[wrap('m:e',base),wrap('m:sup',sup)])
        return base
    def sequence(self,end=None):
        out=[]; self.skip()
        while self.i<len(self.s) and self.s[self.i]!=end:
            out.append(self.scripted()); self.skip()
        return out

# author/date, APA text; * segments receive real Word italics.
REFS={
'FPP':('Hyndman & Athanasopoulos, 2021','Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.). OTexts. https://otexts.com/fpp3/','Hyndman, R. J., & Athanasopoulos, G. (2021).'),
'SHM':('Shmueli, 2010','Shmueli, G. (2010). To explain or to predict? *Statistical Science, 25*(3), 289–310. https://doi.org/10.1214/10-STS330','Shmueli, G. (2010).'),
'OECD':('OECD, 2021','OECD. (2021). *The digital transformation of SMEs*. OECD Publishing. https://doi.org/10.1787/bdb9256a-en','OECD. (2021).'),
'ESL':('Hastie et al., 2009','Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The elements of statistical learning: Data mining, inference, and prediction* (2nd ed.). Springer. https://doi.org/10.1007/978-0-387-84858-7','Hastie, T., Tibshirani, R., & Friedman, J. (2009).'),
'POWER':('Power, 2002','Power, D. J. (2002). *Decision support systems: Concepts and resources for managers*. Quorum Books.','Power, D. J. (2002).'),
'HIER':('Hyndman et al., 2011','Hyndman, R. J., Ahmed, R. A., Athanasopoulos, G., & Shang, H. L. (2011). Optimal combination forecasts for hierarchical time series. *Computational Statistics & Data Analysis, 55*(9), 2579–2589. https://doi.org/10.1016/j.csda.2011.03.006','Hyndman, R. J., Ahmed, R. A.,'),
'KUHN':('Kuhn & Johnson, 2013','Kuhn, M., & Johnson, K. (2013). *Applied predictive modeling*. Springer. https://doi.org/10.1007/978-1-4614-6849-3','Kuhn, M., & Johnson, K. (2013).'),
'RF':('Breiman, 2001','Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32. https://doi.org/10.1023/A:1010933404324','Breiman, L. (2001).'),
'GB':('Friedman, 2001','Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *The Annals of Statistics, 29*(5), 1189–1232. https://doi.org/10.1214/aos/1013203451','Friedman, J. H. (2001).'),
'BG':('Bates & Granger, 1969','Bates, J. M., & Granger, C. W. J. (1969). The combination of forecasts. *Operational Research Quarterly, 20*(4), 451–468. https://doi.org/10.2307/3008764','Bates, J. M., & Granger,'),
'ZHANG':('Zhang, 2003','Zhang, G. P. (2003). Time series forecasting using a hybrid ARIMA and neural network model. *Neurocomputing, 50*, 159–175. https://doi.org/10.1016/S0925-2312(01)00702-0','Zhang, G. P. (2003).'),
'AITCH':('Aitchison, 1982','Aitchison, J. (1982). The statistical analysis of compositional data. *Journal of the Royal Statistical Society: Series B (Methodological), 44*(2), 139–160. https://doi.org/10.1111/j.2517-6161.1982.tb01195.x','Aitchison, J. (1982).'),
'TIB':('Tibshirani, 1996','Tibshirani, R. (1996). Regression shrinkage and selection via the lasso. *Journal of the Royal Statistical Society: Series B (Methodological), 58*(1), 267–288. https://doi.org/10.1111/j.2517-6161.1996.tb02080.x','Tibshirani, R. (1996).'),
'TASH':('Tashman, 2000','Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: An analysis and review. *International Journal of Forecasting, 16*(4), 437–450. https://doi.org/10.1016/S0169-2070(00)00065-0','Tashman, L. J. (2000).'),
'HK':('Hyndman & Koehler, 2006','Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting, 22*(4), 679–688. https://doi.org/10.1016/j.ijforecast.2006.03.001','Hyndman, R. J., & Koehler, A. B. (2006).'),
}

def text(n): return ''.join(n.xpath('.//w:t/text()',namespaces=NS)).strip()
def ppr(p):
    n=p.find('w:pPr',NS)
    if n is None: n=el('w:pPr'); p.insert(0,n)
    return n
def paragraph(s,heading=0,bib=False):
    p=el('w:p'); pr=ppr(p)
    if heading:
        pr.append(el('w:pStyle',val={1:'Ttulo2',2:'Ttulo3'}[heading])); num=el('w:numPr'); num.extend([el('w:ilvl',val=str(heading)),el('w:numId',val='19')]); pr.append(num); pr.append(el('w:keepNext'))
        pr.append(el('w:spacing',before='240',after='120',line='300',lineRule='auto')); pr.append(el('w:jc',val='left'))
    else:
        pr.append(el('w:spacing',before='0',after='120',line='360',lineRule='auto')); pr.append(el('w:widowControl'))
    if bib:
        pr.append(el('w:ind',left='720',hanging='720')); pr.append(el('w:jc',val='left'))
        pr.find('w:spacing',NS).set('{'+W+'}line','480')
    for i,part in enumerate(s.split('*')): p.append(run(part,i%2==1))
    return p

def bookmark(p,name,bid):
    p.insert(1,el('w:bookmarkStart',id=bid,name=name)); p.append(el('w:bookmarkEnd',id=bid))

def equation(latex,key,number):
    table=el('w:tbl'); pr=el('w:tblPr'); pr.append(el('w:tblW',w='9962',type='dxa')); pr.append(el('w:tblLayout',type='fixed'))
    borders=el('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']: borders.append(el('w:'+side,val='nil'))
    pr.append(borders); table.append(pr); grid=el('w:tblGrid')
    for width in [753,8456,753]: grid.append(el('w:gridCol',w=width))
    table.append(grid); row=el('w:tr'); row.append(wrap('w:trPr',el('w:cantSplit'))); table.append(row)
    for i,width in enumerate([753,8456,753]):
        cell=el('w:tc'); cell.append(wrap('w:tcPr',el('w:tcW',w=width,type='dxa'))); row.append(cell)
        p=el('w:p'); pp=ppr(p); pp.append(el('w:spacing',before='80',after='80',line='240',lineRule='auto')); pp.append(el('w:jc',val='center' if i<2 else 'right')); pp.append(el('w:keepNext')); cell.append(p)
        if i==1:
            tree=MathParser(latex).sequence(); p.append(wrap('m:oMathPara',wrap('m:oMath',tree)))
        if i==2:
            bookmark(p,'MT_'+key,20000+number); p.append(run('(2.'))
            fld=el('w:fldSimple',instr='SEQ EcuacionMT \\* ARABIC'); fld.append(run(str(number))); p.append(fld); p.append(run(')'))
    return table

def main():
    with ZipFile(SOURCE) as z: entries=[(i,z.read(i.filename)) for i in z.infolist()]
    contents=dict((i.filename,b) for i,b in entries)
    root=E.fromstring(contents['word/document.xml']); body=root.find('w:body',NS)
    start=next(i for i,c in enumerate(body) if c.tag=='{'+W+'}p' and text(c)=='MARCO TEÓRICO')
    end=next(i for i,c in enumerate(body) if c.tag=='{'+W+'}p' and text(c)=='METODOLOGÍA')
    refidx=next(i for i,c in enumerate(body) if c.tag=='{'+W+'}p' and text(c)=='REFERENCIAS')
    before=[E.tostring(c) for c in list(body)[:start+1]]
    middle=[E.tostring(c) for c in list(body)[end:refidx+1]]
    removed=list(body)[start+1:end]
    assert not any(c.xpath('.//w:sectPr',namespaces=NS) for c in removed),'Section break in replacement'
    for c in removed: body.remove(c)
    chunks=[s.strip() for s in MD.read_text(encoding='utf-8').split('\n\n') if s.strip()]
    nodes=[]; keys=set(); number=0; equations=[]; paragraph_count=0; headings=[]
    for chunk in chunks:
        if chunk.startswith('@@eq|'):
            _,key,latex=chunk.split('|',2); number+=1; nodes.append(equation(latex,key,number)); equations.append({'number':f'2.{number}','key':key,'latex':latex}); continue
        if chunk.startswith('## '): nodes.append(paragraph(chunk[3:],1)); headings.append(chunk[3:]); continue
        if chunk.startswith('### '): nodes.append(paragraph(chunk[4:],2)); continue
        assert re.search(r'\[\[[A-Z; ]+\]\]$',chunk),chunk[:80]
        def cite(match):
            ks=[k.strip() for k in match.group(1).split(';')]; keys.update(ks)
            return '('+'; '.join(sorted(REFS[k][0] for k in ks))+')'
        s=re.sub(r'\[\[([A-Z; ]+)\]\]',cite,chunk)
        # APA parenthetical citation precedes the paragraph's final full stop.
        s=re.sub(r'\. (\([^()]+\))$',r' \1.',s)
        nodes.append(paragraph(s)); paragraph_count+=1
    assert number==29 and len(headings)==10
    for offset,n in enumerate(nodes): body.insert(start+1+offset,n)
    refhead=next(c for c in body if c.tag=='{'+W+'}p' and text(c)=='REFERENCIAS')
    refs=list(body)[list(body).index(refhead)+1:]
    refnodes=[p for p in refs if p.tag=='{'+W+'}p' and text(p)]
    added=[]; updated=[]
    for key in sorted(keys):
        _,bib,prefix=REFS[key]; matches=[p for p in refnodes if text(p).startswith(prefix)]
        assert len(matches)<=1,(key,len(matches))
        new=paragraph(bib,bib=True)
        if matches:
            pos=refnodes.index(matches[0]); body.replace(matches[0],new); refnodes[pos]=new; updated.append(key)
        else: refnodes.append(new); added.append(key)
    # Preserve all other entries; insert additions into alphabetic bibliography.
    for n in refnodes:
        if n.getparent() is body: body.remove(n)
    idx=list(body).index(refhead)+1
    order=lambda p:unicodedata.normalize('NFKD',text(p)).casefold()
    for i,n in enumerate(sorted(refnodes,key=order)): body.insert(idx+i,n)
    assert all(sum(text(p).startswith(REFS[k][2]) for p in refnodes)==1 for k in keys)
    newend=next(i for i,c in enumerate(body) if c is not None and c.tag=='{'+W+'}p' and text(c)=='METODOLOGÍA')
    newref=list(body).index(refhead)
    assert before==[E.tostring(c) for c in list(body)[:start+1]]
    assert middle==[E.tostring(c) for c in list(body)[newend:newref+1]]
    # Chapter equations use their own sequence to preserve equations elsewhere.
    settings=E.fromstring(contents['word/settings.xml'])
    up=settings.find('w:updateFields',NS)
    if up is None: up=el('w:updateFields'); settings.append(up)
    up.set('{'+W+'}val','true')
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); backup=OUT/f'respaldo_antes_marco_{stamp}.docx'
    backup.write_bytes(SOURCE.read_bytes())
    candidate=OUT/'TESIS_Rev42_marco_actualizado.docx'
    changes={'word/document.xml':E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True),'word/settings.xml':E.tostring(settings,encoding='UTF-8',xml_declaration=True,standalone=True)}
    with ZipFile(candidate,'w') as z:
        for info,data in entries: z.writestr(info,changes.get(info.filename,data))
    with ZipFile(candidate) as z:
        assert z.testzip() is None
        assert all(z.read(name)==data for name,data in contents.items() if name not in changes)
    # Old TOC/figure caches are refreshed in Word, not treated as valid page locators.
    audit={'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'candidate':str(candidate),'backup':str(backup),'sections':headings,'paragraphs':paragraph_count,'equations':equations,'cited_reference_keys':sorted(keys),'references_added':added,'references_updated':updated,'other_chapters_preserved':True}
    (OUT/'validacion_marco.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='equations'},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
