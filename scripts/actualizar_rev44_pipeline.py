from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from copy import deepcopy
from datetime import datetime
import json

path = Path('documentacion/TESIS_AGO2026_Rev44_(ZUJ)_12sep2026.docx')
out = Path('output/revision44_pipeline'); out.mkdir(parents=True, exist_ok=True)
raw = path.read_bytes()
with ZipFile(path) as z:
    entries = [(i, z.read(i.filename)) for i in z.infolist()]
root = E.fromstring(dict((i.filename,b) for i,b in entries)['word/document.xml'])
ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W = '{'+ns['w']+'}'
body = root.find('w:body',ns); ps = body.findall('w:p',ns)
def text(p): return ''.join(p.xpath('.//w:t/text()',namespaces=ns))
assert text(ps[282]) == 'METODOLOGÍA' and text(ps[366]) == 'DESARROLLO' and text(ps[758]) == 'REFERENCIAS'
protected = [283,284,285,292,295,300,302,307,309,318,320,321]
protected_xml = [E.tostring(ps[i]) for i in protected]
equations = [E.tostring(e) for e in root.xpath('//m:oMath',namespaces=ns)]
references = [E.tostring(p) for p in ps[758:]]
changes = {
281: 'La investigación se desarrollará como una evaluación predictiva del presupuesto semanal de abastecimiento. El capítulo sustenta la elección de variables, métodos y criterios de contraste, sin anticipar resultados de Cup&Cake. El respaldo de H1 requerirá evidencia favorable en el importe total y en las participaciones; una mejora aislada se describirá como un resultado de ese componente y no como confirmación de la hipótesis conjunta (Shmueli, 2010).',
289: 'En Cup&Cake, la investigación tiene como propósito desarrollar y evaluar un modelo híbrido que integre métodos estadísticos y aprendizaje automático para pronosticar el importe total semanal de compras, junto con un procedimiento para estimar su distribución porcentual entre los principales insumos. Se dispone de una implementación computacional inicial; su precisión con datos reales todavía deberá contrastarse frente a modelos de referencia como apoyo a la planeación del presupuesto de abastecimiento.',
330: 'El procedimiento comprende recolección y depuración de registros, agregación semanal, diagnóstico temporal, ingeniería de características, selección de componentes e integración del modelo híbrido, estimación de la distribución porcentual, evaluación fuera de muestra y comunicación de resultados. El pipeline implementa una versión inicial de este flujo. La verificación técnica del software se distingue de la ejecución científica con datos reales, que permanece pendiente de aprobar fuentes, cobertura, catálogo y protocolo de evaluación.',
338: 'El periodo con cobertura verificable se dividirá cronológicamente en desarrollo y evaluación final. La configuración inicial reserva las últimas 16 semanas calendario; al exigir que los cuatro horizontes tengan valores observables, se obtienen 13 orígenes finales comunes. Esta configuración deberá justificarse con la cobertura real antes del experimento. La versión actual genera ACF, PACF, distribución de importes y frecuencia de ceros sobre desarrollo. STL, con periodo 52, requiere al menos tres ciclos anuales y continuidad. ADF, KPSS, Ljung-Box, ADI, CV² y el diagnóstico formal de atípicos quedan como ampliaciones por implementar y revisar según su pertinencia.',
340: 'El pipeline exporta tablas de respaldo, figuras y un manifiesto por ejecución. Los diagnósticos disponibles se identifican por su conjunto temporal y las omisiones incluyen un motivo. El libro de diagnósticos de la implementación anterior se conserva como antecedente y no se considera un producto verificado del pipeline híbrido actual.',
343: 'La versión inicial construye rezagos de 1, 2, 4, 8 y 12 semanas, resúmenes móviles de 4, 8 y 12 semanas y variables calendáricas. Emplea predictores prefijados, sin selección por frecuencia. La imputación y el escalado de los modelos que los requieren se ajustan dentro de cada ventana. Las exógenas son opcionales y requieren fuente, versión y fecha de disponibilidad; para semanas futuras solo se admiten calendarios conocidos o pronósticos archivados disponibles en el origen. En su ausencia se utilizan observaciones previas admisibles o se registra información faltante.',
346: 'Modelos estadísticos: la implementación inicial incluye ETS aditivo sin componente estacional y ARIMA(1,1,1). Croston-SBA y TSB quedan fuera de esta versión; su eventual incorporación requerirá justificación en desarrollo y pruebas antes de consultar la evaluación final.',
347: 'Modelos de aprendizaje automático: la implementación inicial incluye Ridge con estandarización y tres valores candidatos de regularización, así como Random Forest con complejidad acotada. El ajuste utiliza importes nominales. HistGradientBoosting y las variantes log1p o hurdle del código anterior no forman parte del experimento híbrido implementado.',
348: 'RNN y LSTM no forman parte de la implementación actual. Su eventual evaluación será una ampliación secundaria, condicionada a la disponibilidad de observaciones suficientes y sin modificar retrospectivamente el protocolo del experimento principal.',
349: 'La integración implementada combina un componente estadístico y uno de aprendizaje automático mediante un promedio ponderado. La pareja de componentes y el peso se seleccionan por horizonte en validación temporal interna, con pesos candidatos de 0.25, 0.50 y 0.75 para el componente estadístico y el peso complementario para el componente de aprendizaje automático. Los pronósticos se restringen a valores no negativos. Los fallos se registran y no se sustituyen silenciosamente por otro método bajo el mismo nombre.',
350: 'La configuración inicial propone seleccionar los principales insumos hasta alcanzar el 80 % de participación monetaria acumulada en desarrollo y reunir el resto en una categoría residual. El umbral deberá aprobarse antes del experimento. Durante la validación interna, la selección utiliza únicamente el entrenamiento de cada partición; las categorías quedan congeladas antes de la evaluación final.',
351: 'En semanas con importe total positivo, la participación de cada insumo se obtiene dividiendo su importe entre el total semanal. El procedimiento implementado estima participaciones mediante un promedio exponencial, con parámetro seleccionado internamente entre 0.1, 0.3 y 0.6 en el horizonte principal. Esta primera versión mantiene la misma composición pronosticada para los cuatro horizontes. Las participaciones son no negativas y suman uno; las asignaciones se calculan a partir del total híbrido y se reconcilian a centavos mediante la regla de mayores restos.',
352: 'La referencia de distribución es el promedio de las participaciones semanales observadas en la ventana de entrenamiento, calculado solo en semanas de importe total positivo y actualizado con información previa a cada origen. El promedio exponencial se contrasta con esta referencia. Si no existen semanas válidas para estimar participaciones, el pipeline informa falta de datos y no genera una distribución arbitraria.',
354: 'La configuración inicial utiliza ventanas de 52 etiquetas semanales por horizonte y requiere historia adicional para construir rezagos y resúmenes móviles. Ocho orígenes internos permiten seleccionar los componentes y sus parámetros. Las etiquetas de los cuatro horizontes de la última partición interna deben preceder al primer origen de evaluación final. La longitud de las ventanas y el número de orígenes deberán revisarse con la cobertura real, sin consultar los errores finales para elegirlos.',
357: 'La evaluación comparativa calculará la discrepancia entre valores observados y pronosticados del importe total semanal y de las participaciones. H1 se contrastará frente a las respectivas referencias. La comparación equivalente con y sin variables exógenas permanece como análisis complementario pendiente; admitir estas variables como entrada no equivale a haber ejecutado dicha comparación.',
362: 'El contraste de H1 exige evidencia favorable tanto para el importe total como para las participaciones en h=1. La implementación dispone de un remuestreo circular pareado por bloques de cuatro semanas, con 2000 réplicas y ajuste de Bonferroni para dos componentes, aplicado a diferencias de pérdidas monetarias cuadráticas y porcentuales absolutas. Conserva la posición temporal de las semanas con composición no definida. Este procedimiento se considera exploratorio hasta revisar su adecuación al tamaño muestral y aprobar el protocolo antes de examinar una evaluación independiente. Las mejoras descriptivas, las pruebas de software o una ejecución demostrativa no confirman H1.',
364: 'Se implementó una salida local de inteligencia de negocios que muestra el importe total pronosticado por horizonte, las participaciones y asignaciones por insumo, las métricas y las advertencias de ejecución. Su uso con resultados de Cup&Cake permanece pendiente de la validación con datos reales. La suma de los cuatro horizontes se identificará como consolidado de cuatro semanas y no como mes calendario.',
367: 'Antecedentes del repositorio y de la preparación de datos',
368: 'Se construyó un repositorio en GITHUB para conservar los archivos de la investigación. La Imagen 1 identifica este antecedente. Las descripciones, tablas y figuras heredadas que siguen documentan etapas previas de exploración; no acreditan cobertura, ausencia de fuga de información ni precisión del pipeline híbrido actual. Su reutilización científica requiere una nueva auditoría conforme al procedimiento vigente.',
678: 'La evaluación heredada utilizó una ventana de 52 semanas y reportó 16 orígenes para h=1 y h=4. Se conserva como antecedente, no como evaluación del híbrido. El pipeline actual distingue 16 semanas objetivo reservadas de los 13 orígenes comunes que permiten observar h=1 a h=4; sus resultados reales todavía no se han generado.',
687: 'El archivo 04_dss_semanal.json corresponde a la integración heredada y no debe utilizarse para respaldar la H1 actual. El pipeline híbrido genera dss_hibrido.json y tablero.html dentro de una carpeta identificada por ejecución, con una separación explícita entre demostración y evaluación real.',
691: 'En la versión actual, los indicadores monetarios son RMSE, MAE y MASE; las participaciones se evalúan mediante MAE en puntos porcentuales. El procedimiento Diebold-Mariano con ajuste Holm de la versión anterior no constituye el protocolo vigente para la H1 conjunta. La adecuación del procedimiento inferencial implementado deberá aprobarse antes de la evaluación real independiente.',
695: 'Las métricas incorporadas en versiones anteriores del DSS pertenecen a experimentos heredados. No representan resultados del híbrido actual ni permiten seleccionar sus componentes. El tablero nuevo solo dispone, hasta este punto, de una ejecución demostrativa identificada como tal.',
698: 'El DSS está destinado a facilitar la revisión humana del presupuesto. No se dispone todavía de evidencia real para recomendar el híbrido por encima de sus referencias. La versión inicial tampoco genera intervalos de predicción para los importes futuros; no deben interpretarse bandas o variaciones descriptivas como tales intervalos.',
703: 'La interfaz heredada y sus capturas se conservan como antecedentes. Para el pipeline actual se añadió un constructor independiente, build-hibrido.mjs, que consume los productos de una ejecución completada y preserva las advertencias de demostración. La salida es una instantánea local; no se ha publicado ni se conecta automáticamente con los registros operativos.',
704: 'La actualización incremental con configuración congelada, la captura verificada de la nueva interfaz y su uso operativo permanecen pendientes. La recarga del artefacto actual reproduce el pronóstico del corte guardado; un nuevo corte requiere incorporar fuentes y cobertura aprobadas y ejecutar nuevamente el pipeline. La configuración no debe elegirse por el mejor resultado del conjunto final.',
711: 'La auditoría preliminar de Compras.xlsx identificó 1670 registros sin las incidencias examinadas y 13 pendientes de revisión: 12 marcados por duplicidad y uno por importe inválido. Estos conteos no establecen cobertura semanal ni constituyen una muestra final aprobada. La fuente definitiva, las correcciones, el catálogo de insumos y el periodo continuo de análisis siguen pendientes de validación.',
713: 'La versión inicial emplea características históricas y calendáricas prefijadas, con exógenas opcionales sujetas a disponibilidad documentada. No se ha ejecutado una selección dimensional del nuevo experimento con datos reales. Los análisis de reducción dimensional anteriores no se presentan como resultados del híbrido.',
715: 'No se dispone todavía de métricas reales del modelo híbrido ni de su procedimiento de distribución porcentual. RMSE, MAE, MASE y MAE de participaciones se reportarán después de ejecutar el protocolo aprobado sobre fechas comparables. Los rankings y valores de versiones anteriores no permiten concluir qué modelo será más preciso en este experimento.',
716: 'La ejecución demostrativa verificó que el software puede producir pronósticos para cuatro horizontes y distribuir cada total entre insumos. Sus importes y errores son datos de prueba y se excluyen de los resultados empíricos de la investigación. Las figuras heredadas siguientes se mantienen identificadas como antecedentes, pendientes de sustitución por evidencia real del procedimiento actual.',
722: 'RNN y LSTM no se incluyen en la implementación inicial. Por tanto, no se presentan resultados de redes recurrentes como evidencia del experimento actual.',
724: 'H1 permanece pendiente de contraste con datos reales. Se reportarán por separado los errores del importe total y de las participaciones frente a sus referencias, junto con la incertidumbre y las limitaciones del procedimiento. Hasta completar esa evaluación no corresponde afirmar respaldo ni rechazo de la hipótesis.',
726: 'Se verificó técnicamente la generación del JSON y de la interfaz local con una ejecución demostrativa. No se ha validado su utilidad operativa con la persona responsable de Cup&Cake. Las expresiones de error conservadas a continuación son definiciones matemáticas y no constituyen resultados; los indicadores complementarios no implementados no se atribuyen a la salida actual.',
732: 'La tabla heredada de modelos ganadores no corresponde al experimento híbrido y no se utilizará para concluir sobre H1. La tabla de resultados vigente se elaborará únicamente después de la evaluación con datos reales y distinguirá el importe total, las participaciones y cada horizonte.',
736: 'La discusión empírica permanece pendiente de evaluar el híbrido y la distribución porcentual con datos reales. La implementación permite efectuar comparaciones separadas por horizonte, pero su funcionamiento técnico no demuestra una mejora de precisión.',
737: 'El conjunto inicial acotado de componentes responde a una decisión de diseño parsimonioso. Su conveniencia deberá examinarse con el protocolo temporal definido; no se deduce superioridad de una familia de modelos a partir de su complejidad ni de los resultados demostrativos.',
739: 'La evaluación monetaria conservará los ceros confirmados. Las semanas cuyo importe observado sea cero no tienen participaciones definidas y se excluirán únicamente de la métrica porcentual, informando su número. La frecuencia real de estos casos quedará establecida después de aprobar la cobertura.',
741: 'El uso previsto es apoyar la revisión del presupuesto semanal mediante importes y participaciones pronosticados. No se han medido beneficios financieros u operativos, ni reducciones de faltantes, sobreabastecimiento o merma. La interfaz no autoriza compras automáticas y mantiene la decisión bajo responsabilidad humana.',
743: 'Las pruebas técnicas verifican controles de separación temporal, reconciliación y trazabilidad, pero no sustituyen una evaluación independiente con datos reales. La elección de la fuente, la cobertura, el tamaño muestral y el protocolo inferencial siguen condicionando la validez del estudio. La eventual generalización se limitará al caso y a las condiciones observadas.',
745: 'Se implementó una versión inicial del pipeline para combinar pronósticos estadísticos y de aprendizaje automático del importe semanal de compras, estimar participaciones y generar asignaciones monetarias reconciliadas. La verificación técnica comprende pruebas automatizadas y una ejecución demostrativa; este avance no equivale a concluir la investigación.',
746: 'H1 todavía no ha sido contrastada con el modelo híbrido actual sobre datos reales aprobados. No se afirma su respaldo ni su rechazo. Las conclusiones de experimentos anteriores y los resultados sintéticos no se transfieren a la hipótesis conjunta sobre importe total y distribución porcentual.',
747: 'La conclusión en esta etapa se limita a la disponibilidad de una implementación inicial verificable. Determinar su precisión y su pertinencia para Cup&Cake exige completar la auditoría de datos y la evaluación prevista, sin condicionar el cierre del estudio a obtener una hipótesis favorable.',
749: 'Se recomienda resolver las incidencias de la fuente, aprobar el catálogo y documentar la cobertura semanal antes de entrenar con registros reales. También deberán fijarse el periodo final independiente y el protocolo de contraste. Durante la evaluación se conservarán las referencias, se informarán los cuatro horizontes y se mantendrá la revisión humana de las salidas.',
751: 'El trabajo inmediato consiste en completar la validación con datos reales, revisar los diagnósticos pendientes y generar las figuras empíricas del experimento. Las ampliaciones posibles incluyen una comparación controlada con y sin exógenas, actualización incremental con configuración congelada e intervalos futuros debidamente validados. La captura del tablero y la inserción editorial de figuras reales se realizarán después de verificar su procedencia y legibilidad.'
}
def settext(p, s):
    ts = p.xpath('.//w:t',namespaces=ns); assert ts
    ts[0].text = s
    for t in ts[1:]: t.text = ''
audit=[]
for i,s in changes.items():
    assert i not in protected
    audit.append({'index':i,'before':text(ps[i]),'after':s}); settext(ps[i],s)
# Mark the legacy sections without repeatedly interrupting every paragraph.
for i in [371,375,435,494,635,658,661,664,669,674,679]:
    s=text(ps[i]); new='Antecedentes de '+s[0].lower()+s[1:]
    audit.append({'index':i,'before':s,'after':new});settext(ps[i],new)
for i in range(366,734):
    s=text(ps[i])
    if s.startswith(('Figura ', 'Imagen ', 'Tabla ')):
        new=s+' [Antecedente de la versión anterior; no es evidencia del híbrido actual]'
        audit.append({'index':i,'before':s,'after':new});settext(ps[i],new)

intro = [
('Estado de la implementación del pipeline híbrido', True),
('Al 12 de septiembre de 2026 se dispone de una implementación inicial en Python, con entrada 00_pipeline_hibrido.py y módulos separados de auditoría, preparación semanal, características, modelos, composición, evaluación y comunicación. El software se ha ejecutado con datos de demostración para comprobar su funcionamiento; el entrenamiento y la evaluación científica con registros reales aprobados de Cup&Cake siguen pendientes.',False),
('La auditoría exige una fuente identificada mediante una huella SHA-256, un catálogo de insumos aprobado y evidencia de cobertura para cada semana. Las ausencias no se convierten automáticamente en compras cero. El importe se expresa en pesos mexicanos nominales y se reconcilia con los importes por insumo. Los registros sintéticos se reservan para pruebas técnicas independientes y se excluyen del experimento real.',False),
('La rama monetaria selecciona internamente un componente ETS o ARIMA y uno Ridge o Random Forest, junto con el peso de su combinación por horizonte. La rama de composición utiliza participaciones históricas ponderadas exponencialmente y se compara con un promedio histórico. Las categorías se fijan sin consultar la evaluación final y las asignaciones conservan el total después del redondeo a centavos.',False),
('La revisión técnica aprobó 57 pruebas de Python y tres del constructor del tablero. Estas verifican, entre otros aspectos, disponibilidad temporal, particiones, registros inválidos, composición, reconciliación y recarga del artefacto. La ejecución demostrativa produjo 20 figuras de un catálogo de 23; las omisiones se documentaron. Estos conteos acreditan pruebas de software, no precisión predictiva ni respaldo de H1.',False),
('Cada ejecución conserva configuración, huellas de fuentes y código, versiones, métricas y predicciones cuando procede. Las figuras se exportan con datos de respaldo y manifiesto. La descomposición temporal requiere suficiente historia; no se genera una frecuencia de selección cuando los predictores son prefijados. La captura de la nueva interfaz está pendiente. Ninguna figura de demostración se incorpora como resultado empírico de la tesis.',False),
('Antes del experimento real deberán confirmarse la fuente definitiva, las correcciones de registros, el catálogo, la cobertura, las fechas de evaluación y la adecuación del contraste inferencial. La comparación con y sin exógenas, los diagnósticos adicionales y la actualización incremental no se presentan como funciones completadas. Los antecedentes conservados en las secciones siguientes no sustituyen estas validaciones.',False)
]
pos=list(body).index(ps[366])+1
for offset,(s,heading) in enumerate(intro):
    p=E.Element(W+'p'); template=ps[367] if heading else ps[335]
    pr=template.find('w:pPr',ns)
    if pr is not None:p.append(deepcopy(pr))
    r=E.SubElement(p,W+'r'); rp=template.find('w:r/w:rPr',ns)
    if rp is not None:r.append(deepcopy(rp))
    E.SubElement(r,W+'t').text=s;body.insert(pos+offset,p)

assert protected_xml == [E.tostring(ps[i]) for i in protected]
assert equations == [E.tostring(e) for e in root.xpath('//m:oMath',namespaces=ns)]
assert references == [E.tostring(p) for p in ps[758:]]
stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
backup=out/f'Rev44_antes_pipeline_{stamp}.docx';backup.write_bytes(raw)
candidate=out/'Rev44_pipeline_actualizada.docx'
with ZipFile(candidate,'w') as z:
    for i,b in entries:z.writestr(i,E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True) if i.filename=='word/document.xml' else b)
with ZipFile(candidate) as z:
    assert z.testzip() is None
    assert all(z.read(i.filename)==b for i,b in entries if i.filename!='word/document.xml')
assert path.read_bytes()==raw, 'La tesis cambió durante la edición'
path.write_bytes(candidate.read_bytes())
(out/'auditoria.json').write_text(json.dumps({'backup':str(backup),'modified':len(audit),'added':len(intro),'definitions_preserved':True,'equations_preserved':len(equations),'references_preserved':True,'visual_review':'pending_renderer_unavailable','changes':audit},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'path':str(path),'backup':str(backup),'modified':len(audit),'added':len(intro),'equations_preserved':len(equations)},ensure_ascii=False))
