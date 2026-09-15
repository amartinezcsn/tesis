from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from copy import deepcopy
from datetime import datetime
import hashlib,json

path=Path(r'C:\Python\tesis\documentacion\TESIS_AGO2026_Rev44_(ZUJ)_12sep2026.docx')
out=Path(r'C:\Python\tesis\output\revision44_metodologia')
out.mkdir(exist_ok=True)
raw=path.read_bytes()
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+ns['w']+'}'
with ZipFile(path) as z: entries=[(i,z.read(i.filename)) for i in z.infolist()]
root=E.fromstring(dict((i.filename,b) for i,b in entries)['word/document.xml'])
body=root.find('w:body',ns); ps=body.findall('w:p',ns)
txt=lambda p: ''.join(p.xpath('.//w:t/text()',namespaces=ns))
assert txt(ps[282])=='METODOLOGÍA' and txt(ps[360])=='DESARROLLO'
protected=[283,284,285,292,295,300,302,307,309,318,320,321]
preserved={i:E.tostring(ps[i]) for i in protected}
outside=[E.tostring(n) for n in body if n not in ps[283:360]]
replacements={
289:'En Cup&Cake, la investigación tendrá como propósito desarrollar un modelo híbrido que integre métodos estadísticos y aprendizaje automático para pronosticar el importe total semanal de compras, junto con un procedimiento para estimar su distribución porcentual entre los principales insumos. Su precisión se contrastará frente a modelos de referencia como apoyo a la planeación del presupuesto de abastecimiento.',
290:'La aplicación se delimitará al caso de Cup&Cake. Se prevé comunicar los pronósticos mediante un tablero de inteligencia de negocios, sin sustituir el juicio del responsable ni presuponer mejoras en rentabilidad, inventarios o merma. Los resultados no se generalizarán automáticamente a otras microempresas.',
293:'Se documentará el contexto de planeación de compras de Cup&Cake para interpretar las necesidades de información del responsable. La evaluación cuantitativa se realizará frente a referencias reproducibles. Solo se incluirán estimaciones del propietario como comparador si existen registros fechados antes de conocer los importes observados y compatibles con los mismos horizontes de pronóstico.',
296:'Para el caso de Cup&Cake no se adoptará el alcance causal descrito en la definición precedente. La aplicación tendrá carácter evaluativo y comparativo: se contrastarán alternativas de pronóstico bajo las mismas condiciones temporales para examinar su precisión fuera de muestra, sin atribuir relaciones de causa y efecto sobre la operación del negocio.',
297:'La investigación describirá el comportamiento histórico de ventas y compras y comparará la precisión del modelo híbrido y del procedimiento de distribución porcentual con sus respectivas referencias. La evaluación considerará por separado el importe total semanal y la participación de los principales insumos. Su inferencia se limitará al desempeño predictivo del caso de estudio.',
303:'La semana calendario constituirá la unidad temporal de análisis. Se calcularán el importe total de compras, el importe correspondiente a cada insumo seleccionado y su participación porcentual. Los registros históricos de ventas podrán utilizarse como predictores únicamente cuando su información esté disponible antes de cada origen de pronóstico.',
304:'Se integrarán los registros históricos de ventas y compras de Cup&Cake y se agregarán por semana calendario. Las variables exógenas se incorporarán según su pertinencia y disponibilidad documentada. Los eventos de calendario conocidos podrán utilizarse para la semana objetivo; los indicadores económicos y meteorológicos deberán representar la información efectivamente disponible antes del pronóstico.',
305:'Las matrices semanales permitirán ajustar y comparar los componentes estadístico y de aprendizaje automático, su integración híbrida y el procedimiento de distribución porcentual. Se evaluará el error monetario del total y el error de participación por insumo. El carácter cuantitativo no implicará generalización estadística a otras empresas: las conclusiones se circunscribirán a los registros y condiciones del caso estudiado.',
310:'Se adoptará un diseño no experimental basado en el análisis retrospectivo de registros históricos de Cup&Cake. No se introducirán intervenciones deliberadas en la operación ni se asignarán grupos experimentales. La evaluación reproducirá situaciones de pronóstico mediante cortes cronológicos y utilizará exclusivamente información disponible hasta cada origen.',
311:'Se evaluarán la precisión del importe total semanal y la de su distribución porcentual. Para el importe total, la referencia primaria será el último valor semanal observado; se conservarán como comparadores el promedio móvil de cuatro semanas y, cuando exista cobertura suficiente, el ingenuo estacional de 52 semanas. Para la distribución se utilizará una referencia de participaciones históricas. Todos los métodos se evaluarán sobre fechas objetivo comunes; los ceros observados se distinguirán de la ausencia de registros.',
314:'El diseño cuantitativo, aplicado, no experimental y evaluativo se concretará mediante un estudio de caso longitudinal-retrospectivo. Los registros se organizarán cronológicamente y las decisiones de modelado se documentarán antes de examinar la evaluación final.',
315:'La comparación contrastará el modelo híbrido con las referencias monetarias y con sus componentes individuales; el procedimiento de distribución porcentual se contrastará con su propia referencia histórica. Se utilizarán las mismas fechas objetivo y horizontes para cada comparación. No se emplearán preprueba, posprueba ni grupos de control experimentales.',
316:'Se propone una validación de ventana deslizante con 52 semanas de entrenamiento y avance de una semana. Su viabilidad se verificará según la cobertura efectiva, los rezagos y el número de observaciones utilizables; cualquier ajuste se justificará en la etapa de desarrollo. Se generarán pronósticos directos para h=1, h=2, h=3 y h=4, con h=1 como horizonte principal. Las métricas se reportarán por horizonte. La suma de los cuatro pronósticos será un consolidado de cuatro semanas y no equivaldrá necesariamente a un mes calendario.',
325:'El estudio será longitudinal y retrospectivo porque analizará registros históricos en su secuencia temporal. Se revisarán las fuentes disponibles del periodo 2022–2026 y se documentarán las fechas efectivas de inicio y corte para ventas y compras, sin asumir cobertura completa. El modelado se limitará a los periodos cuya disponibilidad y continuidad puedan verificarse.',
330:'El procedimiento comprenderá recolección y depuración de registros, agregación semanal, diagnóstico temporal, ingeniería de características, selección de componentes e integración del modelo híbrido, estimación de la distribución porcentual, evaluación fuera de muestra y comunicación de resultados. Estas fases se ejecutarán preservando la separación entre desarrollo y evaluación final.',
332:'Se recopilarán y estructurarán los registros históricos disponibles de Cup&Cake. Se verificará su integridad antes de asumir su utilidad para el modelado. La consolidación contemplará principalmente las siguientes fuentes:',
335:'Se homologarán fechas, identificadores de insumos e importes, documentando duplicados, devoluciones y registros incompletos. Las observaciones se agregarán por semana calendario con una regla uniforme de inicio y cierre. Se obtendrán la serie del importe total, las series monetarias por insumo y sus participaciones, además de predictores compatibles con la frecuencia semanal.',
337:'Antes del modelado se auditará la cobertura mediante el calendario semanal y la revisión de las fuentes. Las rachas de compras iguales a cero, su coincidencia con ventas positivas o su ubicación al final del registro motivarán una verificación, pero no bastarán para clasificarlas automáticamente como ausencia de observación. Se distinguirán semanas sin compras confirmadas, semanas con registros y semanas de cobertura incierta. La decisión y su evidencia se documentarán; no se imputarán ceros a periodos sin cobertura comprobada.',
338:'El periodo con cobertura verificable se dividirá cronológicamente en desarrollo y evaluación final. Se propone reservar las últimas 16 semanas, sujeto a justificar su viabilidad y el número de fechas evaluables por horizonte antes de ajustar modelos. Los diagnósticos ADF, KPSS, ACF, PACF, Ljung-Box, ADI, CV² y de atípicos se aplicarán al conjunto de desarrollo según su pertinencia y requisitos. La descomposición STL con periodo 52 se utilizará únicamente si la longitud y continuidad permiten su cálculo e interpretación, explicitando las limitaciones de disponer de pocos ciclos.',
342:'Se examinará si los registros de compras de Cup&Cake presentan patrones temporales o asociaciones con eventos comerciales que puedan aportar información predictiva. Estas relaciones no se asumirán de antemano ni se equiparará el importe de compras con la demanda de productos. Las características candidatas se evaluarán dentro del conjunto de desarrollo.',
343:'Se construirán rezagos, resúmenes móviles y variables calendáricas con información anterior al pronóstico. Para indicadores económicos se registrará la fecha de publicación; para datos meteorológicos futuros solo se admitirán pronósticos archivados y disponibles en el origen correspondiente. Si no existe esa evidencia de disponibilidad, se emplearán observaciones rezagadas o se excluirá la variable. Las transformaciones y la selección de características se ajustarán dentro de cada partición de entrenamiento.',
350:'Se respetará el orden cronológico mediante una ventana deslizante. La longitud inicial propuesta será de 52 semanas y deberá justificarse considerando la cobertura, los rezagos y las observaciones efectivas para cada modelo. Se distinguirá la validación interna, destinada a configurar el procedimiento, de la evaluación final fuera de muestra.',
351:'En cada origen se entrenarán los modelos con la ventana histórica disponible y se generarán pronósticos directos para las cuatro semanas siguientes, sin utilizar sus valores observados. La configuración, los hiperparámetros, las transformaciones y el mecanismo de integración se seleccionarán mediante particiones temporales internas. Durante la evaluación final podrán incorporarse observaciones de semanas ya transcurridas mediante una regla de actualización previamente fijada, pero sus errores no se usarán para rediseñar el procedimiento. Solo se evaluarán fechas objetivo observables y comunes a los métodos comparados.',
355:'RMSE (Raíz del Error Cuadrático Medio): se utilizará como criterio principal para el importe total semanal; MAE será una medida complementaria. La evaluación de participaciones utilizará un criterio propio y no se combinarán directamente errores monetarios con errores porcentuales.',
356:'Se propone utilizar MASE como medida monetaria complementaria, con el denominador calculado exclusivamente en el conjunto de entrenamiento y una referencia ingenua explícita. Si el denominador es cero, se reportará como no definido. MAPE no será un criterio de selección y, si se presenta como diagnóstico, se indicarán las observaciones excluidas por importe cero.',
358:'Se prevé comunicar los resultados mediante un tablero de inteligencia de negocios. Se mostrarán el importe total pronosticado para cada horizonte, las participaciones estimadas y las asignaciones monetarias por insumo, junto con el modelo utilizado, las métricas y las advertencias de cobertura. La suma de los cuatro horizontes se identificará como consolidado de cuatro semanas; una presentación por mes calendario requerirá una regla de agregación explícita.'
}
additions={
348:[
'La integración híbrida se definirá como una fase específica del desarrollo. Se seleccionarán un componente estadístico y uno de aprendizaje automático, y se establecerá el mecanismo mediante el cual sus estimaciones producirán el pronóstico conjunto. La elección y configuración se realizarán exclusivamente mediante validación temporal interna. Antes de la evaluación final se documentarán los componentes, la regla de integración, el tratamiento de pronósticos negativos y las condiciones de actualización, de forma que el procedimiento pueda reproducirse.',
'Para la distribución porcentual, los principales insumos se seleccionarán con un criterio explícito de participación monetaria acumulada aplicado al conjunto de desarrollo. El umbral y la regla de selección se fijarán antes de la evaluación final. Las compras no incluidas en los insumos seleccionados se agruparán en una categoría residual para conservar la correspondencia con el importe total.',
'En semanas con importe total positivo, la participación de cada insumo se obtendrá dividiendo su importe entre el total semanal. Se definirá y ajustará con datos de desarrollo un procedimiento para pronosticar dichas participaciones, con restricciones de no negatividad y suma igual a uno. Las asignaciones monetarias se calcularán multiplicando las participaciones pronosticadas por el total pronosticado; su suma deberá coincidir con este total.',
'La referencia de distribución será el promedio de las participaciones semanales observadas en la ventana de entrenamiento, calculado únicamente en semanas de importe total positivo y actualizado con información previa a cada origen. El procedimiento propuesto deberá diferenciarse de esta referencia y documentarse antes de la evaluación final. Si no existen semanas válidas para estimar participaciones, se reportará falta de información y no se generará una distribución arbitraria.'
],
356:[
'La precisión de la distribución se evaluará mediante el error absoluto medio de las participaciones, expresado en puntos porcentuales. Se calculará por insumo y se presentará un promedio no ponderado entre las categorías previamente definidas. Las semanas con importe total observado igual a cero no tendrán una composición porcentual definida y se excluirán únicamente de esta métrica, informando su número; permanecerán en la evaluación monetaria cuando correspondan a ceros confirmados.',
'El contraste de H1 considerará conjuntamente la comparación del importe total y la comparación de participaciones frente a sus respectivas referencias. Antes de examinar la evaluación final se fijarán los criterios de evidencia, el procedimiento para cuantificar la incertidumbre y el tratamiento de comparaciones múltiples, atendiendo a la dependencia temporal y al tamaño de la muestra. Se distinguirá una reducción descriptiva del error del respaldo inferencial de la hipótesis; no se declarará respaldo de H1 a partir de una mejora aislada en uno de sus componentes.'
]}
def settext(p,s):
    ts=p.xpath('.//w:t',namespaces=ns)
    assert ts
    ts[0].text=s
    for t in ts[1:]:t.text=''
def newparagraph(s):
    p=E.Element(W+'p')
    pr=ps[335].find('w:pPr',ns)
    if pr is not None:p.append(deepcopy(pr))
    r=E.SubElement(p,W+'r'); rp=ps[335].find('w:r/w:rPr',ns)
    if rp is not None:r.append(deepcopy(rp))
    E.SubElement(r,W+'t').text=s
    return p
changes=[]
for i,s in replacements.items():
    assert 283<=i<360 and i not in protected
    changes.append({'paragraph_index':i,'before':txt(ps[i]),'after':s});settext(ps[i],s)
inserted=[]
for i,strings in additions.items():
    index=list(body).index(ps[i])+1
    for offset,s in enumerate(strings):
        p=newparagraph(s);body.insert(index+offset,p);inserted.append(p)
assert all(E.tostring(ps[i])==v for i,v in preserved.items())
assert outside==[E.tostring(n) for n in body if n not in ps[283:360] and n not in inserted]
backup=out/('Rev44_antes_metodologia_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.docx')
backup.write_bytes(raw)
candidate=out/'Rev44_metodologia_verificada.docx'
xml=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(candidate,'w') as z:
    for i,b in entries:z.writestr(i,xml if i.filename=='word/document.xml' else b)
with ZipFile(candidate) as z:
    assert z.testzip() is None
    assert all(z.read(i.filename)==b for i,b in entries if i.filename!='word/document.xml')
assert path.read_bytes()==raw,'El archivo cambió durante la edición'
path.write_bytes(candidate.read_bytes())
audit={'source':str(path),'backup':str(backup),'paragraphs_modified':len(changes),'paragraphs_added':len(inserted),'protected_definitions_unchanged':True,'other_chapters_unchanged':True,'changes':changes}
(out/'auditoria.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='changes'},ensure_ascii=False))
