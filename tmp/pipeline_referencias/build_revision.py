from pathlib import Path
import copy, hashlib, json, html
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path('C:/Python/tesis')
OUT=ROOT/'output/pipeline_fases_20260915'
OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'tmp/pipeline_referencias/fuente_rev44_congelada.docx'
digest=hashlib.sha256(source.read_bytes()).hexdigest()

# Original vector diagram, also exported at high resolution for Word.
W,H,S=1500,1780,2
im=Image.new('RGB',(W*S,H*S),'white'); dr=ImageDraw.Draw(im)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="white"/>']
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size*S)
def text(x,y,t,size=27,bold=False,color='#172B43'):
    dr.text((x*S,y*S),t,font=font(size,bold),fill=color)
    svg.append(f'<text x="{x}" y="{y+size}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(t)}</text>')
def line(points,color='#52677E',width=3):
    dr.line([(x*S,y*S) for x,y in points],fill=color,width=width*S)
    svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{color}" stroke-width="{width}"/>')
def arrow(x,y,d='down'):
    pts=[(x,y),(x-9,y-13),(x+9,y-13)] if d=='down' else [(x,y),(x-13,y-9),(x-13,y+9)]
    dr.polygon([(a*S,b*S) for a,b in pts],fill='#52677E')
    svg.append(f'<polygon points="{" ".join(f"{a},{b}" for a,b in pts)}" fill="#52677E"/>')
text(190,15,'Pipeline híbrido semanal de Cup&Cake',41,True)
text(190,68,'Ciclo propuesto de desarrollo y operación con enfoque MLOps',27)
stages=[
('01','Business Comprehension','Definir el problema, alcance, usuario y criterios de aceptación.','Salida: objetivo semanal, horizontes h=1 a h=4 y protocolo.'),
('02','Data Collection','Auditar fuente, hash, duplicados, catálogo y cobertura semanal.','Salida: calendario íntegro; semanas inciertas como NaN.'),
('03','EDA','Explorar importes, cobertura, ceros y patrones en desarrollo.','Salida: diagnóstico y límites de suficiencia de los registros.'),
('04','Feature Engineering','Construir historia disponible, antigüedad, medias y calendario.','Salida: predictores disponibles en cada origen; objetivos sin imputar.'),
('05','Model Training','Ajustar componentes estadístico y ML; combinar por horizonte.','Salida: selección interna, participaciones y asignaciones reconciliadas.'),
('06','Testing and Debugging','Verificar software y evaluar predicciones sobre objetivos observados.','Salida: controles, métricas y fallos; evaluación retrospectiva exploratoria.'),
('07','Deployment','Empaquetar modelo, versión y salida DSS; validar el uso con el responsable.','Estado: exportación local disponible; operación productiva pendiente.'),
('08','Monitoring','Vigilar cobertura, antigüedad y errores cuando lleguen datos observados.','Propuesta: alertas, revisión humana y reentrenamiento versionado.')]
for i,(num,title,a,b) in enumerate(stages):
    y=124+i*174; x=190; right=1390; height=140
    fill='#EEF4FA' if i<6 else '#FFF6E8'; border='#486B8F' if i<6 else '#AA782A'
    dr.rounded_rectangle((x*S,y*S,right*S,(y+height)*S),radius=12*S,fill=fill,outline=border,width=2*S)
    svg.append(f'<rect x="{x}" y="{y}" width="{right-x}" height="{height}" rx="12" fill="{fill}" stroke="{border}" stroke-width="2"/>')
    text(x+20,y+14,num,32,True,border);text(x+95,y+12,title,34,True)
    text(x+25,y+61,a,27);text(x+25,y+99,b,26)
    if i<7:line([(790,y+height),(790,y+174)]);arrow(790,y+174)
line([(190,1412),(105,1412),(105,368),(184,368)])
arrow(184,368,'right')
text(22,1510,'Retorno controlado: nuevos datos o degradación → revisión → nueva versión',29,True)
text(22,1560,'Fallos técnicos: corregir y repetir las etapas afectadas, conservando el registro.',27)
text(22,1602,'Evaluación final: no ajustar el método para mejorar retrospectivamente sus errores.',27)
text(22,1658,'Trazabilidad transversal: fuentes · código · configuración · pruebas · modelos · métricas',26)
text(22,1710,'Fuente: elaboración propia con base en Ordonez Bolanos et al. (2023, fig. 1, pp. 92–99)',24)
text(22,1743,'y García Velasco (2023, cap. 5, pp. 39–45).',24)
svg.append('</svg>')
(OUT/'diagrama_pipeline_hibrido.svg').write_text('\n'.join(svg),encoding='utf-8')
im.save(OUT/'diagrama_pipeline_hibrido.png',dpi=(440,440))

doc=Document(source); current=list(doc.paragraphs)
# Resolve original anchors by text, preserving changes made to the live source
# during the review. Only the old image and its caption use structural anchors.
initial={int(line.split(': ',1)[0]):line.split(': ',1)[1] for line in (ROOT/'tmp/pipeline_referencias/tesis.txt').read_text(encoding='utf-8').splitlines() if ': ' in line and line.split(': ',1)[0].isdigit()}
p={i:para for i,para in enumerate(current)}
by_text={}
for para in current:by_text.setdefault(para.text,[]).append(para)
for i,t in initial.items():
    matches=by_text.get(t,[])
    if len(matches)==1:p[i]=matches[0]
caption=next(para for para in current if para.text.startswith('Figura 27 - Trazabilidad') and 'Antecedente' in para.text)
ci=current.index(caption)
p[398]=caption;p[397]=current[ci-1];p[399]=current[ci+1]
for i in [312,316,330,331,335,336,338,341,343,344,346,347,352,354,355,356,357,360,362,363,364,366,396,564,566,567,593,663,665,704,731]:
    assert p[i].text==initial[i],(i,p[i].text[:80],initial[i][:80])
changes=[]
def replace(i,new):
    old=p[i].text
    # Retain paragraph properties and bookmarks for existing cross references.
    for child in list(p[i]._p):
        if child.tag not in (qn('w:pPr'),qn('w:bookmarkStart'),qn('w:bookmarkEnd')):p[i]._p.remove(child)
    p[i].add_run(new)
    changes.append({'paragraph_original':i,'before':old,'after':new})
def before(i,t,style=None):
    return p[i].insert_paragraph_before(t,style=style or p[i].style)

replace(312,'El rigor del estudio se sustentará en la separación cronológica, la validación con orígenes sucesivos y una ventana de historia creciente, conservando todas las semanas del calendario. La comparación se realizará sobre objetivos observados comunes a los métodos de cada contraste. La evaluación será retrospectiva y exploratoria; no permitirá inferir causalidad ni generalizar a otras microempresas.')
replace(316,'El protocolo calendar_gaps utiliza historia creciente desde el inicio del periodo hasta cada origen de pronóstico. La configuración vigente propone del 3 de mayo de 2021 al 24 de junio de 2024, con 165 semanas calendario y 26 semanas finales reservadas. El número de objetivos evaluables dependerá de la cobertura aprobada y del horizonte; 26 semanas reservadas no equivalen a 26 observaciones válidas. Se emitirán pronósticos para h=1 a h=4, con h=1 como horizonte principal. El consolidado de cuatro semanas no se denominará mes calendario. Estos parámetros deben justificarse antes de la ejecución real.')
replace(330,'El procedimiento se organizará en ocho fases: Business Comprehension, Data Collection, EDA, Feature Engineering, Model Training, Testing and Debugging, Deployment y Monitoring. Se adopta como marco la metodología de cinco etapas de Ordonez Bolanos et al. (2023, fig. 1, pp. 92–99) y se integra la secuencia de experimentación, selección, puesta en producción, monitorización y reentrenamiento de García Velasco (2023, cap. 5, pp. 39–45). La Figura 27 presenta una adaptación propia para el pronóstico semanal de Cup&Cake, no una reproducción literal de los esquemas de los autores. La disponibilidad del software y las pruebas técnicas se distinguirán de la evaluación con datos reales y de la operación productiva.')
before(331,'Business Comprehension',style='Heading 3')
before(331,'Se delimitará la necesidad de información del responsable de Cup&Cake, el alcance de las adquisiciones incluidas y los criterios técnicos de aceptación. La variable objetivo será el importe nominal registrado utilizable de compras por semana, con una distribución monetaria por insumo. No se equiparará este registro con la demanda, el consumo físico ni el gasto completo del negocio. La comprensión del problema deberá precisar fuentes disponibles, factibilidad, destinatario, forma de uso y responsable del mantenimiento (Ordonez Bolanos et al., 2023, pp. 92–93; García Velasco, 2023, pp. 39–40).',style='Normal')
replace(331,'Data Collection y control de calidad')
replace(335,'Se conservarán las fuentes originales y se registrarán su huella SHA-256, hoja, fecha de extracción y decisiones de revisión. Se homologarán fechas, insumos e importes, documentando duplicados y registros incompletos sin eliminarlos automáticamente. El catálogo delimitará ingredientes, empaques y decoración recurrente y excluirá combustible, muebles y herramientas. El panel mantendrá todas las semanas del periodo; los estados incierta, desconocida e incompleta se representarán como NaN, mientras que los ceros requerirán confirmación. La calidad y el versionado de los datos constituyen condiciones de entrada al modelado (Ordonez Bolanos et al., 2023, pp. 93–94; García Velasco, 2023, pp. 40–41).')
replace(336,'EDA de la serie temporal semanal')
replace(338,'El calendario se dividirá cronológicamente en desarrollo y evaluación final. La configuración calendar_gaps reserva 26 semanas calendario y propone ocho orígenes internos de ajuste; el número de etiquetas observadas se informará por horizonte. El EDA describirá cobertura, distribución de importes, frecuencia de ceros confirmados y evolución temporal utilizando desarrollo para las decisiones de modelado. ACF, PACF y STL se omitirán cuando existan huecos en desarrollo, sin rellenar respuestas ni comprimir fechas para producir esas figuras. Los diagnósticos adicionales deberán justificarse según su pertinencia. Esta separación adapta el análisis de datos de los autores al carácter temporal e incompleto del caso (García Velasco, 2023, p. 40; Ordonez Bolanos et al., 2023, pp. 94–96).')
replace(341,'Feature Engineering y disponibilidad temporal')
replace(343,'La rama calendar_gaps construye el último importe observado y su antigüedad, el número de observaciones históricas, medias y conteos disponibles en ventanas calendario de 4, 8 y 12 semanas, y componentes calendáricos. Las ventanas sin datos conservan sus valores ausentes. Las respuestas de entrenamiento no se imputan y cada ejemplo utiliza únicamente predictores disponibles en su origen. Las ventas y exógenas son opcionales, con fuente y disponibilidad documentadas; la configuración principal no las incorpora actualmente. La selección y transformación de variables descrita por Ordonez Bolanos et al. (2023, p. 94) se adapta a este control temporal y no autoriza rellenar compras desconocidas.')
replace(344,'Model Training y selección de componentes')
replace(346,'Modelos estadísticos: la rama calendar_gaps implementa AR(1) en espacio de estados mediante SARIMAX y permite ARIMA(1,1,1) como candidato adicional. Ambos conservan el calendario y admiten respuestas faltantes en el ajuste estadístico; sus estimaciones internas no se incorporan como compras observadas. ETS corresponde a la rama histórica strict y no al protocolo vigente con faltantes.')
replace(347,'Modelos de aprendizaje automático: la rama calendar_gaps implementa HistGradientBoosting y permite Random Forest con soporte nativo de predictores faltantes. Los modelos directos por horizonte se entrenan únicamente con objetivos observados. La configuración propone al menos 24 etiquetas utilizables por horizonte como umbral operativo; su cumplimiento no demuestra suficiencia estadística. Ridge pertenece a la rama strict. Cada experimento conservará parámetros, métricas y artefactos conforme al principio de trazabilidad de García Velasco (2023, pp. 41–43).')
replace(352,'La referencia de distribución será el promedio de participaciones históricas de semanas observadas con importe total positivo. El candidato exponencial tendrá en cuenta la edad calendario, incluidos los huecos. Ambos usarán solo la historia previa al origen. Si no existen semanas válidas, el procedimiento informará insuficiencia y no generará una composición arbitraria.')
replace(354,'En calendar_gaps se utiliza una ventana creciente; window=52 no limita esta rama. Ocho orígenes internos, sujetos a suficiencia por horizonte, seleccionarán componentes y pesos. Todas sus fechas objetivo deberán preceder al comienzo de la evaluación final. La configuración independent_holdout=false identifica una evaluación retrospectiva exploratoria; no se presentará como una prueba confirmatoria independiente. Las decisiones se registrarán antes de ejecutar la comparación real y no se modificarán para favorecer H1.')
replace(355,'En cada origen se ajustarán los modelos con la historia previa disponible. La rama ML emitirá pronósticos directos por horizonte y la rama estadística pronósticos de varios pasos; ninguna utilizará las respuestas futuras. La combinación se seleccionará en validación interna y permanecerá fijada durante la evaluación. Las nuevas observaciones ya transcurridas podrán incorporarse mediante la regla de historia creciente, sin usar los errores finales para rediseñar el método. Se conservarán todos los orígenes y se evaluarán únicamente objetivos observados comunes a cada contraste.')
replace(356,'Testing and Debugging')
before(357,'Esta fase distinguirá dos verificaciones. Las pruebas de software comprobarán contratos de entrada, fechas, tratamiento de NaN, ausencia de fuga temporal, convergencia, reconciliación monetaria y reproducción al recargar el artefacto. La evaluación predictiva comparará el híbrido, sus componentes y el último valor disponible sobre objetivos observados comunes por horizonte. Los referentes suplementarios podrán disponer de menos casos y deberán informar su propia muestra. Un fallo técnico exigirá corrección documentada y repetición de las etapas afectadas; los errores de la evaluación final no se usarán para reajustar la selección. La separación entre entrenamiento, validación y prueba, y las comprobaciones previas al despliegue, se apoyan en Ordonez Bolanos et al. (2023, pp. 96–97); esta adaptación hace explícita la depuración del software.',style='Normal')
replace(360,'MASE complementará las métricas monetarias cuando exista una escala válida. En calendar_gaps su denominador se obtendrá de diferencias absolutas entre pares de semanas calendario consecutivas observadas del entrenamiento. No se unirán artificialmente semanas separadas por huecos. Si la escala es cero o no puede calcularse, se informará como no definida. MAPE no será un criterio de selección.')
replace(362,'El análisis de H1 examinará por separado las diferencias de pérdida del importe total y de las participaciones en h=1. El código dispone de remuestreo circular pareado por bloques de cuatro semanas, con 2000 réplicas y ajuste de Bonferroni para dos componentes, conservando las posiciones temporales de los faltantes. Su interpretación será exploratoria y dependerá de la cantidad y distribución de objetivos observados. La configuración actual no habilita una confirmación independiente de H1; mejorar métricas descriptivas o aprobar pruebas de software no equivale a confirmarla.')
replace(363,'Deployment y comunicación del presupuesto')
replace(364,'La implementación exporta modelos, pronósticos y una salida local DSS con importes por horizonte, participaciones, asignaciones, métricas y advertencias. La exportación local constituye el prototipo disponible. El uso productivo requerirá una ejecución real validada, versión identificada, prueba de aceptación con el responsable y mecanismo de recuperación de la versión anterior. Se propone una entrega semanal por lotes, coherente con el horizonte del estudio. El despliegue debe elegirse según el destinatario y la forma de consumo de las predicciones (Ordonez Bolanos et al., 2023, pp. 97–98; García Velasco, 2023, p. 43).')
before(366,'Monitoring y reentrenamiento controlado',style='Heading 3')
before(366,'Se propone revisar semanalmente la cobertura de los registros, la antigüedad del último dato y el cumplimiento de los contratos. Cuando estén disponibles los importes observados se calcularán errores por horizonte frente a las referencias y se registrará la cantidad de objetivos evaluables. La falta de una respuesta se informará como evaluación pendiente. El responsable revisará alertas y cambios relevantes en los datos antes de iniciar una nueva versión del experimento. La monitorización, el versionado y el retorno al reentrenamiento se fundamentan en García Velasco (2023, pp. 44–45) y Ordonez Bolanos et al. (2023, pp. 98–99).',style='Normal')
before(366,'Esta fase permanece como ampliación propuesta. Deberán definirse responsable, frecuencia, umbrales de alerta, tamaño mínimo de muestra, registro de incidencias y criterios de promoción o reversión antes del uso operativo. Una alerta no cambiará automáticamente el modelo: abrirá una revisión que podrá retornar a Data Collection, Feature Engineering o Business Comprehension, según el problema. El reentrenamiento conservará la versión anterior y exigirá repetir las verificaciones. No se atribuyen al prototipo actual monitoreo continuo, despliegue automático ni un nivel completo de madurez MLOps.',style='Normal')

replace(396,'Fases del pipeline híbrido con enfoque MLOps')
p[396].paragraph_format.page_break_before=False
replace(397,'')
p[397].alignment=1
p[397].paragraph_format.space_before=Pt(0);p[397].paragraph_format.space_after=Pt(0)
p[397].paragraph_format.line_spacing=1
p[397].paragraph_format.keep_with_next=True
p[397].paragraph_format.page_break_before=True
pic=p[397].add_run().add_picture(str(OUT/'diagrama_pipeline_hibrido.png'),width=Inches(6.5))
pic._inline.docPr.set('descr','Ocho fases del pipeline híbrido: comprensión del negocio, colección, EDA, ingeniería de características, entrenamiento, pruebas, despliegue y monitoreo; retorno controlado a datos y nueva versión. El despliegue productivo y el monitoreo permanecen pendientes.')
replace(398,'Figura 27 - Fases del pipeline híbrido semanal con enfoque MLOps. Fuente: elaboración propia con base en Ordonez Bolanos et al. (2023, fig. 1, pp. 92–99) y García Velasco (2023, cap. 5, pp. 39–45). Las fases operativas indicadas no acreditan un despliegue productivo completado.')
p[398].paragraph_format.line_spacing=1
for run in p[398].runs:run.font.size=Pt(10)
p[399].paragraph_format.page_break_before=True
replace(564,'Al 15 de septiembre de 2026 se dispone de una implementación modular con entrada 00_pipeline_hibrido.py. La configuración principal utiliza calendar_gaps, actualizada el 14 de septiembre, y conserva las ramas strict y demo como antecedentes y pruebas técnicas. La corrida real del 15 de septiembre se detuvo en la validación de fuente, antes del entrenamiento. Su auditoría identificó 1670 registros válidos para revisión y 12 pendientes; este recuento no certifica cobertura ni suficiencia del conjunto analítico.')
replace(566,'La rama monetaria vigente selecciona internamente AR(1) o ARIMA(1,1,1) en espacio de estados y un componente HistGradientBoosting o Random Forest, según los candidatos habilitados. La historia crece conservando los huecos del calendario. La composición se estima con participaciones históricas y un promedio exponencial sensible a la edad calendario. Las categorías se fijan sin consultar los errores finales y las asignaciones conservan el total al redondear a centavos.')
replace(567,'Los conteos de 57 pruebas de Python y tres del constructor del tablero, así como las 20 figuras de demostración, corresponden a la revisión técnica previa de la implementación inicial. No certifican por sí solos la cobertura de pruebas de la rama calendar_gaps ni resultados predictivos sobre Cup&Cake. La verificación de esta rama deberá conservar su propio reporte de ejecución, incluidos fallos, omisiones y versiones de dependencias.')
replace(593,'La evaluación heredada utilizó una ventana de 52 semanas y reportó 16 orígenes para h=1 y h=4. Se conserva exclusivamente como antecedente. La configuración principal actual utiliza historia creciente y reserva 26 semanas calendario; los objetivos observados se contabilizarán por horizonte. Las cifras de 16 semanas y 13 orígenes de la rama strict no describen calendar_gaps, cuya corrida real todavía no ha completado entrenamiento y evaluación.')
replace(663,'Se recomienda resolver las incidencias de fuente, aprobar el catálogo y documentar la cobertura antes de entrenar con registros reales. Deberán fijarse y justificar el periodo y el protocolo exploratorio de calendar_gaps; una futura evaluación confirmatoria requerirá un diseño independiente adicional. Para alinear el ciclo con MLOps, se propone explicitar la aceptación del despliegue, el registro de versiones, la vigilancia de datos y errores y el retorno controlado al reentrenamiento (García Velasco, 2023, pp. 43–45; Ordonez Bolanos et al., 2023, pp. 97–99).')
replace(665,'El trabajo inmediato consiste en completar la revisión de datos y la evaluación retrospectiva, y generar las figuras empíricas correspondientes. Las ampliaciones comprenden comparación controlada con y sin exógenas, intervalos futuros validados y un ciclo operativo de entrega semanal, monitorización y reentrenamiento versionado. Los umbrales de alerta y las reglas de sustitución del modelo deberán fijarse antes del uso productivo; no se presuponen mejoras de precisión ni beneficios financieros.')

# Insert bibliographic records in the existing alphabetic References section.
ref1='García Velasco, A. (2023). MLOps: Administrando el diseño y ciclo de vida de los modelos de machine learning [Trabajo de fin de grado, Universidad Politécnica de Madrid]. Archivo Digital UPM. https://oa.upm.es/74985/'
ref2='Ordonez Bolanos, A. A., Rojas, J. S., Gómez Gómez, J., & Ramirez-Gonzalez, G. (2023). Metodología basada en MLOps (Machine Learning Operations) para apoyo a la gestión en proyectos de ciencia de datos. Revista Colombiana de Tecnologías de Avanzada, 1(41), 87–103. https://doi.org/10.24054/rcta.v1i41.2510'
for anchor,t in [(704,ref1),(731,ref2)]:
    prefix='García Velasco, A.' if anchor==704 else 'Ordonez Bolanos, A.'
    for existing in list(doc.paragraphs):
        if existing.text.startswith(prefix):existing._p.getparent().remove(existing._p)
    new=before(anchor,t)
    if p[anchor]._p.pPr is not None:
        new._p.remove(new._p.pPr) if new._p.pPr is not None else None
        new._p.insert(0,copy.deepcopy(p[anchor]._p.pPr))
# Refresh the cached figure entry wording; Word updates page fields during QA.
old_title='Trazabilidad del pipeline analítico de la investigación.'
new_title='Fases del pipeline híbrido semanal con enfoque MLOps.'
for para in doc.paragraphs:
    nodes=para._p.xpath('.//w:t');visible=''.join(n.text or '' for n in nodes)
    start=visible.find(old_title)
    if start<0:continue
    end=start+len(old_title);pos=0;inserted=False
    for node in nodes:
        value=node.text or '';stop=pos+len(value)
        if stop>start and pos<end:
            prefix=value[:max(0,start-pos)]
            suffix=value[max(0,end-pos):] if stop>end else ''
            node.text=prefix+('' if inserted else new_title)+suffix
            inserted=True
        pos=stop
doc.core_properties.comments='Propuesta de revisión metodológica y diagrama basada en dos referencias MLOps. Original preservado.'
target=OUT/'TESIS_Rev44_propuesta_pipeline_MLOps.docx'
doc.save(target)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(OUT/'registro_cambios.json').write_text(json.dumps({'source':str(source),'sha256_original':digest,'changes':changes,'references_added':[ref1,ref2]},ensure_ascii=False,indent=2),encoding='utf-8')
print(target)
