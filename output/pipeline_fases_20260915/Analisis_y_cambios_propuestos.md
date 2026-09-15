# Análisis de las referencias y alineación del pipeline híbrido

## Resultado de la revisión

Se propone un ciclo de ocho fases para Cup&Cake, con trazabilidad transversal y retorno controlado al recibir nuevos datos o detectar degradación. La propuesta se incorporó en una copia de la tesis Rev44: procedimiento metodológico, Figura 27, estado de implementación, recomendaciones, trabajo futuro y referencias. El original se conserva. Las modificaciones al software descritas aquí son propuestas; no se modificó ni se volvió a entrenar el pipeline.

Las ocho fases son **Business Comprehension → Data Collection → EDA → Feature Engineering → Model Training → Testing and Debugging → Deployment → Monitoring**. Se emplea “Business Comprehension”, como en el artículo, para expresar comprensión del negocio. NaN significa dato ausente; EDA, análisis exploratorio; DSS, sistema de soporte a la decisión.

## Qué aportan los autores

### Ordonez Bolanos y colaboradores

La Figura 1 y la sección 3 presentan cinco etapas: Business Comprehension, Data Preparation, Data Analysis, Modeling y Deployment. La preparación incluye calidad, ingeniería de características, fundamentos de despliegue de código y versionado de datos. El modelado comprende entrenamiento, validación, prueba y selección. El despliegue incluye pruebas con datos reales, registro de versiones, monitoreo y retroalimentación (Ordonez Bolanos et al., 2023, pp. 92–99; páginas 6–13 del PDF).

Su contribución al caso es vincular necesidades del negocio, calidad de datos y operación del modelo. La revisión de calidad se trata como condición para avanzar, no como una actividad opcional. Su validación mediante un cuestionario aplicado a siete proyectos evalúa seguimiento de la metodología; no demuestra una mejora de precisión predictiva para Cup&Cake ni confirma H1 (pp. 100–102).

### García Velasco

El capítulo 5 enumera ocho fases: descripción del problema, análisis de datos, limpieza, realización y almacenamiento de experimentos, selección del modelo, puesta en producción, monitorización y reentrenamiento o sustitución. Destaca el registro de parámetros, métricas, artefactos y versiones, así como conservar modelos anteriores para poder recuperarlos (García Velasco, 2023, pp. 39–45; páginas 49–55 del PDF).

El trabajo aporta una secuencia operativa y un retorno explícito al reentrenamiento. Sus diagramas generales de niveles MLOps en el capítulo 1 remiten a otras fuentes; la adaptación se fundamenta principalmente en su metodología del capítulo 5 y no se atribuye al autor la creación de esos diagramas de terceros. El caso del capítulo 6 es una demostración técnica diferente del pronóstico semanal aquí estudiado.

## Correspondencia entre fuentes y diagrama nuevo

| Fase propuesta | Ordonez Bolanos et al. (2023) | García Velasco (2023) | Adaptación para Cup&Cake |
|---|---|---|---|
| Business Comprehension | §3.1, pp. 92–93 | §5.1, pp. 39–40 | Delimitar importe nominal registrado, insumos, responsable, cuatro horizontes y criterios de aceptación. |
| Data Collection | §3.2.1 y §3.2.4, pp. 93–94 | §5.1 y §5.3, pp. 39–41 | Separar extracción y auditoría; identificar fuente mediante hash y documentar alcance y cobertura. |
| EDA | §3.3, pp. 94–96 | §5.2, p. 40 | Explorar desarrollo sin comprimir semanas ni convertir ausencia en cero. |
| Feature Engineering | §3.2.2, p. 94 | §5.3–5.4, pp. 40–42 | Construir predictores disponibles en cada origen y conservar los objetivos ausentes. |
| Model Training | §3.4, pp. 96–97 | §5.4–5.5, pp. 41–43 | Entrenar componentes y seleccionar pesos por horizonte en validación interna; estimar composición. |
| Testing and Debugging | §3.4.1 y §3.5.2, pp. 96–97 | Validación de datos y evaluación de experimentos, pp. 41–43 | Hacer explícitas las pruebas de software y distinguirlas del contraste predictivo. |
| Deployment | §3.5.1–3.5.4, pp. 97–98 | §5.6, pp. 43–44 | Exportación local disponible; proponer aceptación y entrega semanal por lotes antes de operación. |
| Monitoring | §3.5.5, pp. 98–99 | §5.7–5.8, pp. 44–45 | Revisar calidad, antigüedad y errores observables; alertar y decidir una nueva versión. |

La coincidencia de ocho fases con el número de fases de García Velasco no significa equivalencia literal: el diagrama nuevo desagrega preparación y pruebas, integra selección en entrenamiento y representa reentrenamiento mediante el retorno del ciclo. Tampoco reproduce las cinco etapas del artículo. Es una síntesis metodológica original con atribución explícita.

## Decisiones que requieren adaptación

1. **Ubicar EDA antes de la ingeniería definitiva.** El artículo incluye Feature Engineering en Data Preparation, antes de Data Analysis. Para este caso se propone una auditoría inicial, EDA sobre desarrollo y construcción de características por origen. Puede haber iteración entre estas actividades; cada revisión debe quedar registrada.
2. **Conservar el calendario incompleto.** Las recomendaciones generales de limpieza no justifican borrar automáticamente duplicados, rellenar respuestas o unir semanas no consecutivas. La rama calendar_gaps mantiene las ausencias y exige decisiones documentadas sobre fuente, catálogo y cobertura. Esta es una adaptación del caso, no una regla temporal atribuida a los autores.
3. **Adaptar las particiones al tiempo.** No se traslada automáticamente el reparto orientativo 60–80 % de entrenamiento del artículo. Se mantiene validación cronológica interna y evaluación sobre objetivos observados. El protocolo vigente propone historia creciente, 26 semanas reservadas y al menos 24 etiquetas observadas por horizonte, sujetos a justificación.
4. **Separar pruebas de software y evaluación científica.** Pasar pruebas de contratos o persistencia no acredita precisión. Un fallo se depura y deja constancia de la repetición; un resultado predictivo desfavorable no autoriza reajustar retrospectivamente el método sobre el conjunto final.
5. **Ajustar MLOps a una microempresa.** No es necesario introducir MLflow, Docker, Kubernetes ni una nube para dibujar o iniciar el ciclo. El manifiesto por corrida ya aporta trazabilidad local. Se propone completar las responsabilidades, estados de versión y reglas de operación antes de ampliar infraestructura.
6. **Mantener el alcance exploratorio.** La configuración actual declara independent_holdout=false. La evaluación confirmatoria exigiría un diseño independiente futuro; las fuentes MLOps no sustituyen esa exigencia metodológica.

## Cambios concretos propuestos para el software

| Prioridad | Cambio | Ubicación sugerida | Criterio verificable |
|---|---|---|---|
| Inmediata | Resolver incidencias y documentar fuente, catálogo y cobertura. | `config_hibrido.json`, archivos de entrada y auditoría de `cli.py` | Fuente identificada y revisada; hash coincidente; decisiones trazables; calendario completo sin respuestas imputadas. |
| Alta | Hacer explícitos los estados de cada fase y registrar inicio, fin, fallo y productos. | Orquestación en `cli.py` y `manifiesto.json` | Una corrida interrumpida identifica la fase y conserva su auditoría. Los campos no afirman actividades no ejecutadas. |
| Alta | Mantener una verificación integral específica de calendar_gaps y del contrato del tablero. | `codigos/tests/test_hibrido_gaps.py`, pruebas de integración y constructor del DSS | Validar disponibilidad temporal, conservación de NaN, conteos por horizonte, conciliación y recarga. Reporte vinculado a versión de código y dependencias. |
| Alta | Definir la aceptación del modelo y la entrega semanal por lotes. | Nuevo contrato operativo junto a `reporting.py` y constructor del tablero | El responsable puede identificar corte, horizonte, versión, advertencias y vigencia; puede rechazar una corrida incompleta. |
| Media | Crear un registro de versiones candidatas, aceptadas y retiradas. | Nuevo registro local de modelos | Toda promoción documenta responsable, fecha y criterios; la versión anterior sigue disponible. No promover por el mejor error del conjunto final. |
| Media | Implementar Monitoring. | Nuevo módulo propuesto `monitoring.py` | Vincular predicciones archivadas con observaciones posteriores por origen, objetivo, horizonte y versión. Informar cobertura y errores solo cuando haya respuestas utilizables. |
| Media | Definir alertas y ciclo de reentrenamiento. | Configuración operativa y nuevo historial de incidencias | Frecuencia semanal propuesta; umbrales, mínimo muestral y responsable definidos antes del uso. Una alerta inicia revisión, sin sustitución silenciosa del modelo. |

La denominación `monitoring.py` es una propuesta de ampliación, no un módulo existente. Antes de fijar umbrales numéricos se necesitan datos revisados, una referencia de error y un acuerdo operativo. Ninguna de estas propuestas presupone respaldo de H1.

## Cambios incorporados en la copia de la tesis

| Sección | Modificación |
|---|---|
| Metodología y diseño evaluativo | Se describe historia creciente y evaluación retrospectiva exploratoria con calendario incompleto. |
| Procedimiento metodológico | Se explicitan las ocho fases y su fundamento bibliográfico; se añaden comprensión del negocio, pruebas y monitoreo. |
| EDA y características | Se ajustan las descripciones a calendar_gaps y a la disponibilidad temporal de las entradas. |
| Modelos y particiones | Se distinguen SARIMAX e HistGradientBoosting de ETS y Ridge de la rama histórica; se corrigen las referencias a 52 semanas, 16 semanas finales y 13 orígenes como protocolo vigente. |
| Desarrollo y Figura 27 | Se reemplaza el diagrama heredado por el nuevo ciclo, con fuente y estado del despliegue y monitoreo. |
| Estado de implementación | Se documenta la interrupción de la corrida del 15 de septiembre de 2026 y se distingue de las pruebas históricas. |
| Recomendaciones y trabajo futuro | Se propone aceptación del despliegue, monitoreo y reentrenamiento versionado. |
| Referencias | Se incorporan las dos entradas en orden alfabético. |

Las secciones señaladas expresamente como antecedentes históricos conservan sus resultados y técnicas anteriores; no se convierten en evidencia del protocolo vigente. La revisión se concentra en el pipeline y sus fuentes metodológicas, sin constituir una auditoría completa de todas las referencias de la tesis.

## Referencias

García Velasco, A. (2023). *MLOps: Administrando el diseño y ciclo de vida de los modelos de machine learning* [Trabajo de fin de grado, Universidad Politécnica de Madrid]. Archivo Digital UPM. https://oa.upm.es/74985/

Ordonez Bolanos, A. A., Rojas, J. S., Gómez Gómez, J., & Ramirez-Gonzalez, G. (2023). Metodología basada en MLOps (Machine Learning Operations) para apoyo a la gestión en proyectos de ciencia de datos. *Revista Colombiana de Tecnologías de Avanzada, 1*(41), 87–103. https://doi.org/10.24054/rcta.v1i41.2510

Nota bibliográfica: el artículo muestra distinto orden de autores en el encabezado y en su recuadro «Cómo citar». Se utiliza el orden del recuadro de citación publicado en la primera página. Las páginas citadas son las impresas: 39–45 del TFG corresponden a 49–55 del PDF y 92–99 del artículo a 6–13 del PDF.
