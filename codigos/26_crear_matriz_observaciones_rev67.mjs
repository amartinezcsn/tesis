import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "C:/Python/tesis/outputs/revision_observaciones_rev67";
const outputPath = `${outputDir}/Matriz_consolidada_observaciones_revisores_Rev67.xlsx`;

const rows = [
  ["R1-01","Capítulo II","Suficiencia bibliográfica","Revisor 1 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Incorporar más referentes; la versión revisada tenía apenas 20.","Referentes y estado del arte","Corregida","La revisión de evidencia y la bibliografía fueron ampliadas y depuradas.","pp. 9-18 y 87-90","Sección 2.1 con antecedentes nacionales e internacionales; lista de referencias ampliada."],
  ["R1-02","Capítulo III","Definición del modelo","Revisor 1 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Explicar con exactitud qué modelo se utilizó y por qué.","Arquitectura y justificación del modelo","Corregida","Se describen familias, arquitectura híbrida, función de cada componente y alcance de la MLP.","pp. 43-46 y 61-64","Secciones 3.8.4, 3.8.5 y 3.9.6; Tablas 3 y 6; ecuaciones 37-39."],
  ["R1-03","Capítulo III","Selección de configuración","Revisor 1 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Explicar la comparación y decisión para elegir el modelo de entrenamiento.","Selección interna y comparadores","Corregida","La selección se separa de la evaluación final y se documenta por horizonte.","pp. 39, 43-46 y 61-65","Diseño evaluativo, validación interna, comparadores y configuración seleccionada por horizonte."],
  ["R1-04","Capítulo III","Datos de entrenamiento","Revisor 1 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Precisar cuáles fueron los datos de entrenamiento.","Datos, periodo y ventana de entrenamiento","Corregida","Se especifican fuentes, unidad semanal, periodo disponible, predictores y ventana fija de 52 semanas.","pp. 37, 40-44, 46 y 49-51","Secciones 3.3, 3.7, 3.8.1-3.8.5 y Tabla 2."],
  ["R1-05","Capítulos III-IV","Pruebas con otros modelos","Revisor 1 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Indicar si se realizaron pruebas con otros modelos para corroborar resultados.","Comparación de modelos","Corregida","Se comparan referencias, modelos estadísticos, aprendizaje automático, combinaciones y correcciones residuales.","pp. 43-45, 61-64 y 72-75","Tabla 3, Figura 9, Tabla 6, Figura 11 y resultados por horizonte."],
  ["R1-06","Capítulo IV-V","Interpretación de H1","Revisor 1 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Aclarar la hipótesis y si se realizó otra corrida al no confirmarse H1.","Contraste y sensibilidad de H1","Corregida","Se informa que H1 es no confirmatoria y se documenta una corrida de sensibilidad sin parámetros de imputación; no se fuerza un resultado favorable.","pp. 70, 76-77, 80-82","Secciones 4.2, 4.6, 4.8.4 y 5.1; diferencias pareadas y limitaciones."],

  ["R2-01","Estructura general","Organización capitular","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Ajustar la estructura a la organización institucional de cinco capítulos.","Estructura institucional","Corregida","El documento se reorganizó en cinco capítulos: Introducción, Marco teórico, Metodología, Resultados y discusión, Conclusiones y recomendaciones.","Índice, pp. iii-viii","Índice general y encabezados de los capítulos I-V."],
  ["R2-02","Estructura general","Títulos de capítulos","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Agregar la palabra capítulo al nombre de cada capítulo.","Encabezados capitulares","Corregida","Todos los encabezados principales incluyen la palabra CAPÍTULO.","pp. 1, 9, 36, 70 y 81","Encabezados CAPÍTULO I a CAPÍTULO V."],
  ["R2-03","Preliminares","Agradecimientos","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Terminar la sección de agradecimientos.","Secciones preliminares","Corregida","La sección contiene texto completo y ya no aparece como pendiente.","p. ii","Apartado AGRADECIMIENTOS en preliminares."],
  ["R2-04","Estructura general","Numeración de capítulos","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Usar numeración romana para los capítulos.","Numeración capitular","Corregida","Los capítulos están identificados con números romanos I-V.","pp. 1, 9, 36, 70 y 81","Encabezados de cada capítulo."],
  ["R2-05","Estructura general","Numeración de temas y subtemas","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Numerar temas y subtemas de acuerdo con el capítulo.","Jerarquía de secciones","Corregida","La numeración sigue el patrón 1.1, 1.2, 2.1, 3.8.5, etc.","Índice, pp. iii-viii; cuerpo completo","Índice general y encabezados jerárquicos de los cinco capítulos."],
  ["R2-06","Preliminares","Índice de figuras","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Cambiar el título a Índice de Figuras.","Listas preliminares","Corregida","La lista aparece como ÍNDICE DE FIGURAS.","pp. ix-x","Encabezado de la lista de figuras."],
  ["R2-07","Preliminares","Paginación romana","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Numerar con romanos minúsculos las secciones anteriores al capítulo I, excepto portada.","Paginación preliminar","Corregida","Las páginas preliminares usan numeración romana minúscula y la portada no exhibe número.","pp. i-xii","Pies de página de preliminares."],
  ["R2-08","Cuerpo de la tesis","Paginación arábiga","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Usar numeración arábiga a partir del capítulo I.","Paginación del cuerpo","Corregida","El cuerpo reinicia en página 1 con numeración arábiga.","p. 1 en adelante","Pie de página desde CAPÍTULO I."],
  ["R2-09","Capítulo III","Diagrama metodológico","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Agregar un diagrama metodológico con proceso, etapas o fases.","Flujo metodológico","Corregida","Se incorporó un flujo reproducible desde fuentes y cobertura hasta presupuesto, validación y comunicación.","p. 52","Figura 2 y párrafos previo y posterior."],
  ["R2-10","Documento completo","Formato de figuras","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Colocar pie de figura centrado y no encabezado.","Formato de figuras","Corregida","Las figuras tienen imagen, pie centrado, fuente y explicación asociada.","pp. 51-77 y 98-100","Figuras 1-21; ejemplo visible en Figura 8, p. 63."],
  ["R2-11","Documento completo","Encabezados de tablas","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Centrar los encabezados de las tablas.","Formato de tablas","Corregida","Los encabezados y títulos de tablas fueron homologados y centrados.","pp. 15-17, 44-45, 64-71 y anexos","Tablas 1-9 y tablas de anexos."],
  ["R2-12","Documento completo","Secciones sin numeración","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Numerar las secciones internas que carecían de tema o subtema.","Jerarquía documental","Corregida","Los apartados del cuerpo tienen numeración jerárquica; sólo preliminares, referencias, glosario y anexos conservan encabezado no decimal.","Índice, pp. iii-viii","Correspondencia entre índice y encabezados del cuerpo."],
  ["R2-13","Capítulo I","Extensión de la pregunta","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Simplificar la pregunta sin perder variables, caso y criterio de evaluación.","Pregunta de investigación","Atendida con limitación","La pregunta se reformuló para hacer explícitos modelo, comparación, variable, caso, ubicación y periodos. No se redujo de forma drástica porque la regla de trazabilidad exige conservar esos ocho componentes.","p. 4","Sección 1.2.2; correspondencia con el objetivo general de la p. 5."],
  ["R2-14","Capítulos II-III","Aportación técnica original","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Destacar la aportación técnica original más allá de integrar componentes existentes.","Contribución técnica","Corregida","La contribución se presenta como procedimiento reproducible y evaluativo para small data, no como algoritmo nuevo ni superioridad general.","pp. 18, 35, 39, 68 y 78-81","Síntesis del vacío, alcance evaluativo, trazabilidad, discusión y conclusiones."],
  ["R2-15","Capítulo III","Hiperparámetros y criterios de selección","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Precisar reglas de selección de hiperparámetros y criterios para elegir configuraciones.","Selección interna","Corregida","Se documentan candidatos, selección por horizonte, separación temporal y configuración final.","pp. 43-46 y 61-65","Secciones 3.8.4-3.8.6, 3.9.6; Tablas 3 y 6."],
  ["R2-16","Documento completo","Lineamientos UPMH","Revisor 2 (nombre no consignado)","OBSERVACIONES 1 y 2.docx","Ajustar estructura y presentación a los lineamientos de tesis de maestría de la UPMH.","Cumplimiento estructural general","Corregida","Se homologaron capítulos, numeración, preliminares, índices, figuras, tablas y paginación.","Documento completo; índice pp. iii-x","Estructura final de cinco capítulos y listas preliminares actualizadas."],

  ["D-01","Capítulo I","Pregunta: población, institución y tiempo","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H01","La pregunta carecía de delimitación temporal explícita y presentaba de forma parcial la unidad y el caso institucional.","Trazabilidad de la pregunta","Corregida","La pregunta identifica Cup&Cake, Tizayuca, los registros disponibles 2016-2026 y el bloque final de evaluación de 2025.","p. 4","Sección 1.2.2."],
  ["D-02","Capítulo I","Derivación del objetivo general","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H02","El objetivo general cambiaba determinar precisión por desarrollar y rompía la derivación de la pregunta.","Pregunta-objetivo","Corregida","El objetivo general ahora inicia con Determinar y conserva variables, relación, caso y periodos de la pregunta.","p. 5","Sección 1.4.1 y comparación directa con 1.2.2."],
  ["D-03","Capítulo III","Protocolo temporal contradictorio","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H03","El diseño alternaba avance de una y tres semanas y mezclaba protocolo planeado con corrida ejecutada.","Rolling Window","Corregida","El documento y el código se alinearon a ventana fija de 52 semanas con desplazamiento semanal.","pp. 46 y 61-63","Tabla 2, Ecuación 39 y Figura 8; explicación de Rolling Window."],
  ["D-04","Capítulos III-V","Muestra, imputación y cobertura","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H04","La muestra efectiva era reducida, existían 29 semanas estimadas y la captura no estaba certificada.","Alcance exploratorio y sensibilidad","Atendida con limitación","Se ejecutó sensibilidad sin parámetros de imputación y se explicitaron seis folds monetarios y tres a cinco composicionales. La cobertura histórica no puede corregirse retroactivamente y permanece como limitación.","pp. 70-71, 76, 80-82","Secciones 4.2, 4.3, 4.6, 4.8.4 y 5.1-5.3."],
  ["D-05","Resumen y Abstract","Síntesis en pasado y resultados","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H05","Resumen y abstract estaban en futuro y omitían resultados principales.","Resumen ejecutivo","Corregida","Ambos se reescribieron en pasado con datos, diseño, tamaños efectivos, RMSE, resultado de H1 y alcance.","pp. xi-xii","RESUMEN y ABSTRACT."],
  ["D-06","Preliminares","Campos e índices rotos","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H06","Existían errores de marcador, numeración obsoleta y referencias antiguas.","Índices y referencias cruzadas","Corregida","Los índices general, de tablas y de figuras se reconstruyeron con páginas actualizadas; no quedan mensajes de error de campo.","pp. iii-x","Índices y listas; auditoría final sin Error ni Reference source not found."],
  ["D-07","Documento completo","Resaltados y marcas de edición","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H07","Persistía resaltado multicolor de edición.","Limpieza editorial","Corregida","La versión final está limpia, sin resaltados de revisión visibles.","Documento completo","Revisión visual de las 113 páginas de la Rev67."],
  ["D-08","Capítulo III","Metodología genérica y contradictoria","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H08","La metodología contenía definiciones genéricas y afirmaciones de generalización o causalidad incompatibles con el estudio.","Metodología efectiva","Corregida","Se reestructuró alrededor del diseño evaluativo, fuentes, unidad semanal, particiones, modelos, métricas, controles y límites de inferencia.","pp. 36-48","Capítulo III, secciones 3.1-3.8.8."],
  ["D-09","Capítulo III","Ética y tratamiento de datos","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H09","Faltaba una sección suficiente sobre autorización, confidencialidad, acceso e identificadores.","Consideraciones éticas","Corregida","Se añadió el tratamiento de registros, acceso restringido, minimización y uso académico.","p. 48","Sección 3.8.8."],
  ["D-10","Referencias","Consistencia APA 7","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H10","La lista tenía orden inconsistente y ambigüedades de desambiguación y autores corporativos.","Referencias y citas","Atendida con limitación","La bibliografía fue ordenada y depurada. No se realizó verificación externa exhaustiva de todos los DOI ni puede afirmarse una auditoría bibliométrica total.","pp. 87-90","Lista de REFERENCIAS ordenada; la limitación se mantiene documentada."],
  ["D-11","Portada","Fecha de versión","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H11","La portada mostraba 2025 mientras la revisión y corrida correspondían a 2026.","Portada","Corregida","La portada indica septiembre de 2026.","Portada","Fecha visible en la parte inferior."],
  ["D-12","Capítulo V","Página residual y saltos","Dirección de tesis (nombre no consignado)","REVISION_DIRECCION_REV57.md, H12","Las conclusiones dejaban una página casi vacía por cortes poco naturales.","Maquetación final","Corregida","Se ajustaron saltos y continuidad de Conclusiones, Recomendaciones y Trabajo futuro.","pp. 81-83","Capítulo V sin página residual independiente."],

  ["T-01","Capítulos III-V","Delimitación del total modelado","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","Aclarar que el total modelado no equivale a todas las compras y que se excluyen categorías.","Importe elegible y exclusiones","Corregida","Se define el importe elegible y se enumeran categorías excluidas; las conclusiones se limitan a registros utilizables.","pp. 43, 58-60, 73 y 80-82","Secciones 3.8.4, 3.9.5, 4.5, 4.8.4 y 5.1-5.2."],
  ["T-02","Capítulos III-IV","Enlace entre categorías","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","Explicar el paso de categorías principales mostradas a los 11 insumos y RESTO_ELEGIBLE.","Trazabilidad de categorías","Corregida","Se incorporó una tabla de trazabilidad y se definió RESTO_ELEGIBLE como conciliación distinta de OTROS.","pp. 45, 58-60, 67 y 73","Tabla 4, Figuras 6-7, Tabla 7 y resultados composicionales."],
  ["T-03","Capítulos III-V","Aporte de ventas y calendario","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","Integrar predictores no demuestra cuánto aportan; faltaba comparación controlada con y sin ellos.","Ablación de predictores","Atendida con limitación","Se presenta sensibilidad por grupos de fuentes, pero la tesis reconoce que no aisló causalmente el aporte de cada predictor individual.","pp. 64, 79 y 81-82","Figura 9; discusión y conclusiones mantienen explícita la limitación."],
  ["T-04","Capítulo V","Actividades futuras","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","No contar como realizado actualizar registros, estimar intervalos futuros o validar el tablero.","Separación entre resultados y trabajo futuro","Corregida","Las acciones no ejecutadas se ubican en recomendaciones y trabajo futuro, sin presentarse como resultados logrados.","pp. 79 y 81-83","Implicaciones, conclusiones, recomendaciones y trabajo futuro."],
  ["T-05","Capítulos III-V","Vigencia del pronóstico","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","Aclarar que el pronóstico con origen de agosto de 2025 no es presupuesto vigente.","Alcance operativo","Corregida","La tesis señala expresamente que la emisión es histórica y que una aplicación requiere actualizar datos y reejecutar el flujo.","pp. 67, 79 y 81-82","Tabla 7; sección 4.8.3; conclusiones y recomendaciones."],
  ["T-06","Capítulo IV-V","Dictamen de H1","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","La hipótesis no queda confirmada y no debe presentarse como superioridad conjunta.","Resultado no confirmatorio","Corregida","El contraste se declara no confirmatorio y se distingue falta de evidencia de equivalencia o rechazo definitivo.","pp. 76-77, 80-81","Secciones 4.6, 4.8.4 y 5.1."],
  ["T-07","Capítulo IV","Interpretación del signo composicional","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","Corregir la lectura de histórico menos ponderado = -1.39 pp; el signo favorece al histórico.","Diferencia pareada composicional","Corregida","La interpretación se alineó con la resta y ya no atribuye la diferencia negativa al método ponderado.","pp. 76-77","Sección 4.6 y Figura 17."],
  ["T-08","Capítulo IV","Tamaño efectivo y cobertura","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","Seis orígenes monetarios y tres a cinco observaciones composicionales no permiten una conclusión fuerte; la cobertura no está certificada.","Limitaciones de validez","Atendida con limitación","Los tamaños efectivos y la cobertura se reportan explícitamente y restringen las conclusiones. Los datos faltantes originales no pueden reconstruirse sin nuevas fuentes.","pp. 71, 76 y 80","Secciones 4.3, 4.6 y 4.8.4."],
  ["T-09","Capítulos III-IV","Parámetros inferenciales","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","Explicitar mínimo inferencial, nivel de confianza, regla de decisión y comparaciones múltiples.","Protocolo inferencial","Parcial","Se documentan regla no confirmatoria, bootstrap insuficiente y tratamiento del horizonte principal; el nivel de confianza y todos los parámetros del remuestreo no quedan desarrollados con detalle suficiente en el cuerpo.","pp. 40, 76, 80 y 96","Delimitación temporal, evaluación de H1, limitaciones y Anexo B."],
  ["T-10","Anexo B","Archivos de reproducibilidad","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","El anexo remitía a archivos no incluidos dentro de la tesis.","Paquete de reproducibilidad","Atendida con limitación","El Anexo B identifica rutas, funciones y criterios de reproducción, pero los archivos siguen siendo artefactos externos al DOCX.","pp. 96-97","Tabla del paquete de reproducibilidad y restricciones de acceso."],
  ["T-11","Capítulos IV-V","Contribución defendible","Revisor técnico (nombre no consignado)","Analisis__tesis_RODRIGO.docx","Presentar como aportación el procedimiento evaluado y sus límites, sin convertirlo en superioridad predictiva o beneficio operativo demostrado.","Alcance de la contribución","Corregida","La discusión y las conclusiones describen una aportación reproducible y exploratoria, no una ventaja general ni una orden automática de compra.","pp. 78-83","Secciones 4.8.1-4.8.4 y Capítulo V."],
];

const headers = ["ID","Capítulo","Subtema","Observador","Fuente de observación","Observación consolidada","Tema consolidado","Estado Rev67","Razón del estado","Página(s) Rev67","Dónde se observa el ajuste"];
const statusOrder = ["Corregida","Atendida con limitación","Parcial","Pendiente"];
const chapterOrder = ["Preliminares","Portada","Estructura general","Documento completo","Cuerpo de la tesis","Resumen y Abstract","Capítulo I","Capítulo II","Capítulos II-III","Capítulo III","Capítulos III-IV","Capítulo IV","Capítulo IV-V","Capítulos III-V","Capítulos IV-V","Capítulo V","Referencias","Anexo B"];
const sortedRows = [...rows].sort((a,b) => {
  const rankA = chapterOrder.indexOf(a[1]);
  const rankB = chapterOrder.indexOf(b[1]);
  return (rankA - rankB) || a[2].localeCompare(b[2], "es") || a[0].localeCompare(b[0]);
});
const chapters = [...new Set(sortedRows.map(r => r[1]))];
const statusCounts = Object.fromEntries(statusOrder.map(s => [s, rows.filter(r => r[7] === s).length]));

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Resumen");
const detail = workbook.worksheets.add("Matriz completa");
const sources = workbook.worksheets.add("Fuentes y criterio");
summary.showGridLines = false; detail.showGridLines = false; sources.showGridLines = false;
summary.tabColor = "#1F4E78"; detail.tabColor = "#5B9BD5"; sources.tabColor = "#A5A5A5";

summary.getRange("A2:H2").merge();
summary.getRange("A2").values = [["Matriz consolidada de observaciones de revisores"]];
summary.getRange("A3:H3").merge();
summary.getRange("A3").values = [["Contraste contra TESIS_OCT2026_Rev67_(ZUJ)_Glosario_Complementado.docx"]];
summary.getRange("A5:B5").values = [["Estado","Observaciones"]];
summary.getRange("A6:B9").values = statusOrder.map(s => [s,statusCounts[s]]);
summary.getRange("D5:E5").values = [["Fuente / observador","Observaciones"]];
const observers = [...new Set(rows.map(r => r[3]))];
summary.getRangeByIndexes(5,3,observers.length,2).values = observers.map(o => [o,rows.filter(r=>r[3]===o).length]);
summary.getRange("A12:C12").values = [["Capítulo o bloque","Observaciones","Con seguimiento"]];
summary.getRangeByIndexes(12,0,chapters.length,3).values = chapters.map(c => [c,rows.filter(r=>r[1]===c).length,rows.filter(r=>r[1]===c && ["Parcial","Pendiente","Atendida con limitación"].includes(r[7])).length]);
summary.getRange("G5:H5").values = [["Indicador","Valor"]];
summary.getRange("G6:H9").values = [["Total de observaciones",rows.length],["Revisores o conjuntos",observers.length],["Corregidas",statusCounts["Corregida"]],["Con seguimiento",rows.length-statusCounts["Corregida"]]];

detail.getRange("A2:K2").merge();
detail.getRange("A2").values = [["Observaciones consolidadas y evidencia de corrección en la versión 67"]];
detail.getRange("A4:K4").values = [headers];
detail.getRangeByIndexes(4,0,sortedRows.length,headers.length).values = sortedRows;
const table = detail.tables.add(`A4:K${4+rows.length}`, true, "ObservacionesRev67");
table.style = "TableStyleMedium2";
detail.freezePanes.freezeRows(4);
detail.freezePanes.freezeColumns(3);

sources.getRange("A2:D2").merge();
sources.getRange("A2").values = [["Fuentes revisadas y criterio de clasificación"]];
sources.getRange("A4:D4").values = [["Fuente","Observador consignado","Uso en la matriz","Limitación"]];
sources.getRange("A5:D9").values = [
  ["OBSERVACIONES 1 y 2.docx - bloque 1","No consignado","Seis observaciones técnicas y de evidencia","No contiene firma ni nombre del revisor."],
  ["OBSERVACIONES 1 y 2.docx - bloque 2","No consignado","Dieciséis observaciones estructurales, metodológicas y formales","No contiene firma ni nombre del revisor."],
  ["REVISION_DIRECCION_REV57.md","No consignado","Doce hallazgos H01-H12 de la revisión integral","Revisión contra Rev57; el estado se verificó nuevamente en Rev67."],
  ["Analisis__tesis_RODRIGO.docx","No consignado","Once observaciones sobre objetivos, H1, categorías y reproducibilidad","El documento declara que no reprodujo las ejecuciones computacionales."],
  ["TESIS_OCT2026_Rev67_(ZUJ)_Glosario_Complementado.docx","No aplica","Documento usado para comprobar correcciones y páginas","Las páginas indicadas son las impresas en Rev67, no el número físico del archivo."],
];
sources.getRange("A12:D12").values = [["Estado","Criterio","Interpretación","Acción"]];
sources.getRange("A13:D16").values = [
  ["Corregida","La evidencia requerida aparece de manera verificable en Rev67.","No queda un incumplimiento material del punto observado.","Sin acción adicional, salvo revisión del comité."],
  ["Atendida con limitación","La tesis reconoce y trata el punto, pero la condición de origen no puede eliminarse.","Ejemplos: cobertura histórica o tamaño muestral.","Mantener la limitación y ampliar datos en trabajo futuro."],
  ["Parcial","Existe avance verificable, pero falta un elemento solicitado.","El punto no está cerrado por completo.","Completar antes de entrega si el comité lo exige."],
  ["Pendiente","No se encontró evidencia suficiente de corrección.","La observación sigue abierta.","Corregir y volver a verificar."],
];

for (const sheet of [summary, detail, sources]) {
  const used = sheet.getUsedRange();
  used.format.font = {name:"Arial",size:10,color:"#1F1F1F"};
  used.format.verticalAlignment = "center";
}
for (const sheet of [summary, detail, sources]) {
  sheet.getRange("A2:K2").format.font = {name:"Arial",size:15,bold:true,color:"#1F1F1F"};
}
summary.getRange("A3:H3").format.font = {name:"Arial",size:10,italic:true,color:"#666666"};
for (const r of ["A5:B5","D5:E5","G5:H5","A12:C12"]) summary.getRange(r).format = {fill:"#1F4E78",font:{name:"Arial",size:10,bold:true,color:"#FFFFFF"},horizontalAlignment:"center",verticalAlignment:"center"};
summary.getRange("A5:H30").format.borders = {preset:"all",style:"thin",color:"#D9E2F3"};
summary.getRange("A6:A9").format.font = {name:"Arial",size:10,bold:true};
summary.getRange("A1:H30").format.wrapText = true;
summary.getRange("A:A").format.columnWidth = 31; summary.getRange("B:B").format.columnWidth = 15; summary.getRange("C:C").format.columnWidth = 18;
summary.getRange("D:D").format.columnWidth = 44; summary.getRange("E:E").format.columnWidth = 15; summary.getRange("F:F").format.columnWidth = 3; summary.getRange("G:G").format.columnWidth = 25; summary.getRange("H:H").format.columnWidth = 15;

detail.getRange("A4:K4").format = {fill:"#1F4E78",font:{name:"Arial",size:10,bold:true,color:"#FFFFFF"},horizontalAlignment:"center",verticalAlignment:"center",wrapText:true};
detail.getRange(`A5:K${4+rows.length}`).format.wrapText = true;
detail.getRange(`A5:K${4+rows.length}`).format.verticalAlignment = "top";
const widths = [10,20,25,34,31,52,29,23,52,22,52];
"ABCDEFGHIJK".split("").forEach((c,i)=>detail.getRange(`${c}:${c}`).format.columnWidth=widths[i]);
detail.getRange(`A5:A${4+rows.length}`).format.horizontalAlignment = "center";
detail.getRange(`H5:H${4+rows.length}`).format.font = {name:"Arial",size:10,bold:true};
detail.getRange(`A4:K${4+rows.length}`).format.borders = {preset:"all",style:"thin",color:"#D9D9D9"};

sources.getRange("A4:D4").format = {fill:"#1F4E78",font:{name:"Arial",size:10,bold:true,color:"#FFFFFF"},horizontalAlignment:"center",verticalAlignment:"center",wrapText:true};
sources.getRange("A12:D12").format = {fill:"#5B9BD5",font:{name:"Arial",size:10,bold:true,color:"#FFFFFF"},horizontalAlignment:"center",verticalAlignment:"center",wrapText:true};
sources.getRange("A4:D16").format.borders = {preset:"all",style:"thin",color:"#D9D9D9"};
sources.getRange("A4:D16").format.wrapText = true; sources.getRange("A4:D16").format.verticalAlignment = "top";
sources.getRange("A:A").format.columnWidth = 45; sources.getRange("B:B").format.columnWidth = 28; sources.getRange("C:C").format.columnWidth = 46; sources.getRange("D:D").format.columnWidth = 48;

detail.getRange(`H5:H${4+rows.length}`).conditionalFormats.add("containsText", {text:"Corregida",format:{fill:"#E2F0D9",font:{color:"#375623",bold:true}}});
detail.getRange(`H5:H${4+rows.length}`).conditionalFormats.add("containsText", {text:"Atendida con limitación",format:{fill:"#FFF2CC",font:{color:"#7F6000",bold:true}}});
detail.getRange(`H5:H${4+rows.length}`).conditionalFormats.add("containsText", {text:"Parcial",format:{fill:"#FCE4D6",font:{color:"#843C0C",bold:true}}});
detail.getRange(`H5:H${4+rows.length}`).conditionalFormats.add("containsText", {text:"Pendiente",format:{fill:"#F4CCCC",font:{color:"#9C0006",bold:true}}});

summary.freezePanes.freezeRows(4); sources.freezePanes.freezeRows(4);
workbook.recalculate();
await fs.mkdir(outputDir,{recursive:true});
const preview1 = await workbook.render({sheetName:"Resumen",range:"A1:H30",scale:1.4,format:"png"});
await fs.writeFile(`${outputDir}/preview_resumen.png`,new Uint8Array(await preview1.arrayBuffer()));
const preview2 = await workbook.render({sheetName:"Matriz completa",range:"A1:K18",scale:1.0,format:"png"});
await fs.writeFile(`${outputDir}/preview_matriz.png`,new Uint8Array(await preview2.arrayBuffer()));
const preview2b = await workbook.render({sheetName:"Matriz completa",range:"A30:K49",scale:1.0,format:"png"});
await fs.writeFile(`${outputDir}/preview_matriz_final.png`,new Uint8Array(await preview2b.arrayBuffer()));
const preview3 = await workbook.render({sheetName:"Fuentes y criterio",range:"A1:D16",scale:1.2,format:"png"});
await fs.writeFile(`${outputDir}/preview_fuentes.png`,new Uint8Array(await preview3.arrayBuffer()));
const check = await workbook.inspect({kind:"table",range:"Matriz completa!A4:K12",include:"values,formulas",tableMaxRows:12,tableMaxCols:11,maxChars:12000});
console.log(check.ndjson);
const errors = await workbook.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",options:{useRegex:true,maxResults:100},summary:"formula error scan"});
console.log(errors.ndjson);
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
console.log(JSON.stringify({rows:rows.length,statusCounts,observers:observers.length,chapters:chapters.length}));
