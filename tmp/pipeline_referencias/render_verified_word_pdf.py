from pathlib import Path
import importlib.util, os, sys, json
from PIL import Image, ImageOps, ImageDraw
import pdfplumber

root=Path('C:/Python/tesis/tmp/pipeline_referencias')
runtime=Path('C:/Users/ramartinez/.cache/codex-runtimes/codex-primary-runtime')
os.environ['PATH']=str(runtime/'dependencies/native/poppler/Library/bin')+os.pathsep+os.environ['PATH']
skill=Path('C:/Users/ramartinez/.codex/plugins/cache/openai-primary-runtime/documents/26.904.11930/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('renderer',skill)
renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
pdf=root/'revision_verificada.pdf'
# Word is the native layout engine used for the PDF. Preserve the skill's
# canonical PNG rasterization pipeline while substituting that conversion.
renderer.convert_to_pdf=lambda *args,**kwargs:(str(pdf),'PDF exported by Microsoft Word; LibreOffice unavailable in the bundled runtime.')
renderer.rasterize('C:/Python/tesis/output/pipeline_fases_20260915/TESIS_Rev44_propuesta_pipeline_MLOps.docx',str(root/'render'),140,False,False)
pages=[]
with pdfplumber.open(pdf) as book:
    for i,p in enumerate(book.pages):
        txt=p.extract_text() or ''
        pages.append({'page':i+1,'text':txt})
(root/'pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print('PAGES',len(pages))
for p in pages:
    if any(s in p['text'] for s in ['Business Comprehension','Data Collection','Testing and Debugging','Monitoring','García Velasco, A.','Ordonez Bolanos, A.','Al 15 de septiembre']):
        print('REVIEW',p['page'],p['text'][:110].replace('\n',' '))
files=sorted((root/'render').glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
for offset in range(0,len(files),9):
    canvas=Image.new('RGB',(1530,2040),'#d5d5d5');draw=ImageDraw.Draw(canvas)
    for j,f in enumerate(files[offset:offset+9]):
        im=Image.open(f);im.thumbnail((500,640))
        x=(j%3)*510;y=(j//3)*680
        canvas.paste(im,(x+(500-im.width)//2,y+25))
        draw.text((x+10,y+5),f.stem,fill='black')
    canvas.save(root/f'contact-{offset//9+1:02d}.jpg')
