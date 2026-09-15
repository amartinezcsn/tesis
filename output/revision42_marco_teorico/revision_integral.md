# Revisión del marco teórico de la versión 42

Documento fuente: `C:\Python\tesis\documentacion\TESIS_AGO2026_Rev42_(ZUJ)_11sep2026.docx`.

Revisión de coherencia, secuencia, pertinencia y precisión conceptual respecto del enfoque propuesto: modelo híbrido estadístico y de aprendizaje automático, importe total semanal de compras, distribución porcentual por insumo y evaluación temporal frente a referencias. Se respeta que la investigación aún no se ha desarrollado. No se modificó la tesis.

Los localizadores P170–P481 corresponden a la posición de los párrafos de cuerpo del DOCX, contada desde uno en la versión leída; no son números de página ni la numeración visible de Word. Los fragmentos permiten encontrarlos mediante Buscar. Las filas que agrupan párrafos comparten una misma recomendación. Se revisaron los 312 párrafos de ese tramo, incluidos encabezados, y el contenido matemático de cuatro tablas de ecuaciones. La revisión es textual y estructural; no valida la paginación. Se contrastaron conceptos técnicos seleccionados con las fuentes indicadas al final, sin realizar una auditoría bibliográfica completa.

## Dictamen

El marco aún no es coherente en su totalidad con el nuevo enfoque. Hay fundamentos aprovechables de series temporales, aprendizaje estadístico, regularización y evaluación temporal, pero conviven con afirmaciones del enfoque previo sobre pronóstico de ventas, inventarios físicos, merma, flujo de caja y expansión comercial. Algunos párrafos prometen resultados, atribuyen conductas no acreditadas al propietario o presentan una implementación ya realizada. Faltan fundamentos desarrollados de hibridación y desagregación porcentual.

La revisión debe priorizar el contenido conceptual antes de corregir el estilo. Una hipótesis de superioridad predictiva requiere una explicación plausible de por qué combinar modelos podría ayudar, y condiciones claras bajo las cuales la comparación podría no respaldarla.

## Criterios de ajuste

- El objeto pronosticado es el importe registrado de compras, que no equivale automáticamente a demanda, consumo de insumos, cantidades óptimas ni pagos efectivos.
- La distribución porcentual describe la composición monetaria de las compras. No determina recetas, existencias o necesidades físicas.
- Comparar métodos o elegir el ganador no constituye por sí mismo un modelo híbrido: debe existir una integración definida de componentes.
- La literatura puede redactarse en presente o pasado según corresponda. Las actividades del estudio deben expresarse como propuestas; los beneficios deben quedar condicionados a resultados y aplicación posterior.
- El conocimiento del propietario aporta contexto y posibles variables. Un pronóstico ingenuo no mide directamente su capacidad ni sus sesgos.
- La prueba de H1 debe distinguir el desempeño del importe total y el de las participaciones. Una mejora en el primero no demuestra una mejora en el segundo.

## Revisión de todos los bloques de párrafos

### Apertura y conocimiento tácito

| Localizador | Fragmento o tema | Dictamen y ajuste |
|---|---|---|
| P170 | MARCO TEÓRICO | Conservar como título del capítulo. |
| P171 | El presente marco teórico establece | Reescribir el mapa del capítulo para incorporar importe de compras, modelo híbrido, composición porcentual y validación; hoy describe principalmente una transición de intuición a IA. |
| P172–P173 | Microempresa; Caracterización Estructural y Ontología | Conservar el tema contextual y simplificar el segundo título a «Características de la microempresa y restricciones de información». |
| P174 | deconstrucción ontológica | Reducir a una explicación concreta de escala, centralización y disponibilidad de datos. El vocabulario ontológico no aporta aquí un marco filosófico desarrollado. |
| P175 | 95%… 41.8% | Verificar fuente, año, universo y denominador de ambas cifras antes de conservarlas; no calificarlas de falsas sin cotejo. Eliminar «alarmantes» si no se presenta un indicador definido. |
| P176–P178 | restricciones; centralización absoluta; inmediatez | Conservar el argumento contextual, acortar y evitar universales como «absoluta» o «de manera indefinida». Explicar cómo esas condiciones afectan captura de datos y planeación semanal. |
| P179 | crecimiento de unidades como Cup&Cake | Trasladar hechos acreditados del caso a su contexto; retirar afirmaciones sobre expansión y choques macroeconómicos que no sustentan la variable objetivo. |
| P180 | Conocimiento Tácito | Conservar con título breve. |
| P181 | activo estratégico más valioso | Conservar definición y referencias del conocimiento tácito. Corregir «quien se manifiesta»: lo que se manifiesta es el conocimiento. No asumir ausencia de registros ni jerarquizarlo como el activo más valioso sin evidencia. |
| P182–P183 | socialización; patrones regulares | Conservar con menor extensión. Vincular experiencia con selección de fechas y eventos que podrían aportar información predictiva. |
| P184 | lo convierte en una referencia contrastable | Precisar que una regla reproducible no equivale al juicio del propietario. Para comparar directamente ambos se necesitarían pronósticos del propietario registrados antes de conocer los resultados. |
| P185–P188 | Sistema 1 y Sistema 2 | Resumir en uno o dos párrafos como contexto de decisiones bajo incertidumbre. Eliminar elogios a autores y fórmulas de autoridad; evitar equiparar análisis únicamente con cálculo matemático. |
| P189–P190 | predominio del Sistema 1; viabilidad económica | Matizar las generalizaciones y separar racionalidad limitada de diagnóstico del propietario. No afirmar consecuencias financieras demostradas en el caso. |
| P191–P192 | sesgos más dañinos y recurrentes | Reducir el bloque; presentar sesgos posibles de la literatura, no como resultados de una evaluación psicológica de Cup&Cake. |
| P193 | Sesgo de Sobreconfianza | Retirar atribución personal y ejemplo de nuevas sucursales. Si se conserva, usar un ejemplo hipotético de estimación del presupuesto semanal. |
| P194 | Heurística de Disponibilidad | Conservar definición; formular el ejemplo como hipotético. Eliminar la cadena automática entre recuerdo, sobreabastecimiento y merma. |
| P195 | Anclaje y Ajuste | Conservar definición y un ejemplo presupuestario acotado. No afirmar que el propietario omite todas las variables relevantes. |
| P196 | intensidad matemática que duplica | Evitar una constante psicológica universal y la inferencia de sobreproducción sistemática en Cup&Cake. Suprimir si no contribuye al argumento de pronóstico presupuestario. |
| P197–P198 | límite epistemológico absoluto | Sustituir por «Limitaciones de las estimaciones informales». Eliminar afirmaciones absolutas y el razonamiento basado en expansión comercial. |
| P199 | estacionalidades cruzadas y exógenas | Conservar como motivación posible; separar hipótesis de patrones de hallazgos. No incorporar redes sociales, competencia o clima como datos disponibles sin acreditarlo. |
| P200–P201 | gestión reactiva; efecto látigo | No atribuir una regla de compra o efectos de inventario al caso sin evidencia. El efecto látigo no se demuestra por variabilidad de una sola serie de importes; retirar o delimitar como antecedente de cadena de suministro. |
| P202–P204 | sustituir el instinto; colapsa | Suprimir las conclusiones repetidas y descalificaciones. Contradicen P184 y P205, que reconocen complementariedad del juicio y la analítica. |
| P205 | complementarlo… mitigar sesgos | Conservar el enlace hacia herramientas analíticas. Sustituir beneficios asegurados por el propósito de aportar pronósticos contrastables; no se medirá mitigación de sesgos. |

### Inteligencia de negocios y presupuesto

| Localizador | Fragmento o tema | Dictamen y ajuste |
|---|---|---|
| P206 | Inteligencia de Negocios… Planeación Financiera | Delimitar el título a apoyo a la planeación del presupuesto de abastecimiento. |
| P207 | datos como activo estratégico | Conservar definición breve de BI/DDDM sin presentarlos como respuesta garantizada a limitaciones cognitivas. |
| P208 | ingresos, flujos y costos de inventario | Conservar definición de analítica predictiva; sustituir aplicación por estimación de importes de compra. Los otros usos pueden quedar como antecedentes diferenciados. |
| P209–P211 | Evolución… DSS | Reducir historia tecnológica a definiciones de BI y DSS, su relación y función de comunicación de resultados. |
| P212 | acceso vedado… democratizado | Matizar generalizaciones históricas; enlazar accesibilidad con recursos y mantenimiento requeridos. |
| P213 | expansión; mermas; series de ingresos | Corregir objetivo a compras; no asumir registros de merma. Trasladar descripción de integración concreta a metodología. |
| P214–P215 | DDDM como activo | Fusionar con P207. Eliminar «reducción drástica» y beneficios competitivos garantizados. |
| P216–P217 | productividad y difusión de DDDM | Conservar como antecedentes si se verifican población y alcance de las fuentes. No transferir asociaciones de otras organizaciones a resultados causales esperados en Cup&Cake. |
| P218 | inventario mínimo óptimo; datos purificados de sesgos | Reescribir por completo: preguntas sobre importe semanal y composición; los datos también pueden contener sesgos. Evitar atribuir decisiones al estado de ánimo. |
| P219–P220 | Taxonomía Analítica | Conservar una clasificación breve con límites entre descripción, diagnóstico, predicción y prescripción. |
| P221 | valor predictivo nulo | Corregir: la descripción no produce por sí misma un pronóstico, pero sirve para detectar patrones y construir variables. |
| P222 | técnicas correlacionales… causas | Corregir: asociación y exploración diagnóstica no establecen causalidad por sí solas. |
| P223 | predictivo frente a explicativo | Conservar distinción, sin equiparar todo análisis descriptivo con modelado causal ni limitar toda predicción estadística exclusivamente al futuro. En este estudio sí interesa el futuro temporal. |
| P224 | ventas se duplicaron | Usar ejemplo hipotético monetario de compras. No introducir una cifra histórica del caso sin soporte. Cerrar explicando qué añade un pronóstico al reporte histórico. |
| P225–P228 | optimización del flujo de efectivo | Reorientar al presupuesto de compras. Distinguir importe comprado, egreso pagado y saldo de caja; un pronóstico de compras aislado no es un modelo de liquidez. |
| P229–P232 | alta precisión; optimizar ciclos de caja | Retirar promesas y lista de resultados fuera de alcance. Sustituir por un párrafo sobre reserva y revisión del presupuesto sujeto a incertidumbre. |
| P233 | En esta investigación… corto plazo | Conservar el límite y pasar «se emplean» a «se propone emplear». Añadir distribución presupuestaria por insumo. |
| P234–P236 | S&OP y perecederos | Reducir a antecedente operativo o mover al contexto de compras. No presentar S&OP como intervención que se implementará. |
| P237–P238 | Hübner; beneficios de doble dígito | Verificar autores, estudio y cifras. Distinguir demanda física y políticas de inventario del pronóstico monetario. No generalizar caducidad homogénea a todos los insumos. |
| P239 | optimizador de recursos… maximiza | Sustituir íntegramente: no se pronostican cantidades físicas ni se optimiza producción o inventario. |
| P240–P242 | binomio indiscutible; escudo; blindar | Suprimir cierres redundantes. Reemplazar por transición a la construcción de series semanales del importe de compras. |

### Series temporales y modelos

| Localizador | Fragmento o tema | Dictamen y ajuste |
|---|---|---|
| P243–P245 | series temporales; frecuencia | Conservar: es fundamento directamente pertinente. |
| P246 | semana lunes a domingo; ceros | Conservar distinción cero/dato faltante. Cambiar «demanda igual a cero» por «importe de compras igual a cero». Llevar definición operativa del calendario a metodología. |
| P247–P248 | STL y tres ciclos | Conservar conceptos; justificar o retirar el umbral de tres ciclos como regla universal. Evitar presentarlo como criterio teórico automático. |
| P249 | ADF, KPSS, log1p y diferenciación | Conservar pruebas y cautela con muestra pequeña. Separar estabilización de varianza de tratamiento de cambios de nivel; diferenciar ambas transformaciones. |
| P250–P251 | ACF, PACF y Ljung-Box | Conservar; aclarar que son diagnósticos, no garantía de pronosticabilidad. |
| P252–P253 | ADI y CV² | Conservar con definición, cita precisa y cautela al trasladar una clasificación de demanda a importes monetarios de compras. |
| P254 | atípicos y MAD | Conservar principios; el procedimiento concreto de identificación pertenece a metodología. |
| P255–P256 | relación con IA | Conservar como transición y conectar también con la integración híbrida. |
| P257 | Modelos estadísticos y aprendizaje automático | Añadir un apartado específico posterior de modelos híbridos; el título actual organiza familias pero no explica su integración. |
| P258 | estadísticos lineales; ML superior | Corregir generalización de ambas familias. Contradice P259, P269 y P292. |
| P259 | competencias M4/M5 | Conservar con citas específicas para cada competencia y límites de extrapolación. Evitar atribuir ambos resultados a una única referencia que no los cubra. |
| P260–P262 | Fundamentos y ARIMA | Conservar definición, acortar introducción y limitar supuestos a ARIMA, no a todos los métodos estadísticos. |
| P263 | variable actual | Revisar ecuación nativa: el símbolo actual extraído aparece como Y(t−1), igual que un rezago; debe corresponder a Y(t). |
| P264 | diferenciación… estabilizar varianza | Corregir: la diferenciación trata cambios del nivel; la estabilización de varianza puede requerir otra transformación. |
| P265 | componente MA | Conservar; revisar delimitadores y notación nativa. Distinguir término MA de ARIMA de un promedio móvil usado como referencia. |
| P266 | SARIMA y ETS | Conservar, separando familias y evitando «ciclos rígidos». Definir periodicidad semanal sin confundir ciclo anual y mes. |
| P267 | hurdle | Conservar concepto de ocurrencia e importe condicional, con referencia. Mover modelos candidatos y decisiones de evaluación a metodología; no confundir esta descomposición con hibridación estadística–ML. |
| P268–P270 | referencias e intermitencia | Conservar y delimitar aplicación a compras monetarias. Mover lista definitiva de candidatos a metodología. |
| P271–P272 | aprendizaje automático y candidatos | Renombrar a pronóstico del importe de compras. Conservar fundamentos; selección final de algoritmos corresponde a metodología. |
| P273 | ML no paramétrico y aprendizaje autónomo | Corregir: ML también incluye modelos paramétricos; dependencia temporal y entradas deben representarse adecuadamente. |
| P274–P275 | ensambles y Random Forest | Conservar explicación del promedio y aleatoriedad; matizar independencia de árboles y reducción «drástica» de varianza. |
| P276 | boosting y pérdida de gradiente | Explicar corrección en dirección del gradiente negativo de la pérdida; residuales es el caso de pérdida cuadrática, no una identidad universal. |
| P277 | inmunidad casi total | Retirar: no existe inmunidad general a atípicos o faltantes; capacidades dependen del algoritmo y su implementación. |
| P278 | ingresos y requerimientos físicos | Reorientar a asociaciones predictivas con el importe de compras; evitar atribuir determinación causal o cálculo de cantidades. |
| P279–P282 | RNN y LSTM | Reducir si son comparadores secundarios. Cambiar «colapsan», «erradicar» y «patología» por limitaciones y mecanismos concretos; incluir referencia original de LSTM. |
| P283–P285 | compuertas | Conservar solo si las redes se mantienen justificadas. La compuerta no evalúa relevancia económica explícita; el estado oculto no es necesariamente el pronóstico final. |
| P286 | comparación secundaria | Conservar cautela y coherencia con datos limitados. |
| P287 | el modelo incorpora XAI | Eliminar afirmación de implementación. Incluir XAI solo si está previsto y justificado; atribuciones de variables no equivalen a efectos causales. |
| P288–P289 | confrontación empírica | Conservar tema con título simple; retirar afirmaciones sobre lo que toda la comunidad «asumió». |
| P290 | M4 y superioridad estadística | Verificar cifra exacta, año y fuente; corregir «parsimonia e igualaron». Incorporar el papel de las combinaciones y modelos híbridos en el antecedente, sin extrapolar superioridad general. |
| P291 | M5 | Conservar como contraste de escala y estructura, verificando resultados y cita; no trasladar automáticamente evidencia de Walmart a una microempresa. |
| P292 | superioridad no debe asumirse | Conservar; debe regir todo el capítulo. |
| P293 | actualización en tiempo real | Reducir o retirar si no se desarrollará actualización en tiempo real. Diferenciar reentrenamiento semanal de flujo continuo. |
| P294–P297 | validación, regularización, características | Conservar un resumen y remitir al bloque correspondiente para evitar reiteración. Usar «evaluación comparativa» en lugar de sugerir intervención experimental. |
| P298–P301 | aplicación a perecederos | Fusionar con P308–P313. Delimitar estudios ajenos, evitar jerarquía universal entre costo de exceso y defecto, y supuestos de vida útil de pocas horas para todos los insumos. |
| P302 | transformación implementada | Pasar a propuesta; sustituir intervalos de confianza del pronóstico por intervalos de predicción cuando ese sea el objeto. No garantizar precisión. |
| P303 | se requiere ML y LSTM | Retirar necesidad demostrada de esas arquitecturas; deben ser opciones justificadas y contrastables. Cambiar variable objetivo a compras. |
| P304 | órdenes exactas y flujo de efectivo | Sustituir íntegramente por apoyo al presupuesto. Un tablero comunica métricas y pronósticos; no optimiza métricas por sí mismo. |
| P305–P307 | arsenal; eficiencia; sincronización | Suprimir cierres retóricos y reemplazar por fundamento de combinación híbrida con alcances y riesgos. |

### Perecederos

| Localizador | Fragmento o tema | Dictamen y ajuste |
|---|---|---|
| P308–P309 | Pronóstico en productos perecederos | Reubicar como contexto temprano y reducir duplicidad con P234–P239 y P298–P301. Separar demanda física y compras monetarias. |
| P310–P312 | ontología; almacenamiento indefinido | Simplificar definición; corregir equiparación de FMCG con bienes duraderos y almacenamiento indefinido. Matizar vidas útiles, recuperación y costos de disposición. |
| P313 | insumos específicos de Cup&Cake | No afirmar uso de lácteos no pasteurizados ni otros insumos sin registro. Sustituir imposibilidades universales de almacenamiento por restricciones que dependen de cada producto. |
| P314–P317 | Newsvendor | Reducir a antecedente que distingue decisiones óptimas de pronóstico. No es necesario desarrollarlo como modelo central porque no se estimarán cantidades ni costos de exceso/defecto. |
| P318 | función objetivo de la microempresa | No presentar minimizar costos de inventario como objetivo de esta tesis. Identificarlo como función del modelo Newsvendor citado. |
| P319–P321 | costos y ecuación 1 | Si se conserva, explicar supuestos y unidades del modelo externo. Retirar si solo prolonga un tema que no se aplicará. |
| P322 | distribución E[D]; incapacidad del administrador | E[D] es una esperanza, no una distribución. Eliminar diagnóstico personal y supuestos resultados de inventario/merma. |
| P323–P325 | microestacionalidad | Conservar como posible mecanismo de variación, sin afirmar que BI optimizará Newsvendor ni generalizar elasticidad y varianza de otros productos. |
| P326 | demanda puede triplicar | Aportar fuente o retirar magnitud. Para calendario semanal, explicar exposición de cada semana a eventos. |
| P327 | fines de semana | Explicar agregación: en semanas completas la composición de días se repite; un indicador diario debe transformarse en información que varíe entre semanas. |
| P328 | ciclos de nómina | Conservar como posible predictor conocido anticipadamente; no declarar correlación fuerte en Cup&Cake sin análisis. |
| P329 | clima reduce drásticamente | Matizar y distinguir clima observado futuro de información climática disponible al emitir pronóstico. |
| P330 | elección empírica | Conservar como cierre breve. |
| P331–P332 | impacto financiero y ambiental | Convertir en antecedentes acotados o retirar por redundancia. Verificar identidad de Hübner, que cambia dentro del documento. |
| P333 | núcleo rector; mitigar Newsvendor | Reorientar al alcance presupuestario; no confundir MAE de importes con diferencia producción–demanda. |
| P334 | incremento del 18% | Eliminar o marcar como ejemplo hipotético ajeno al estudio. No permite deducir cantidad exacta ni constituye resultado. |
| P335 | merma 10–15%; utilidad neta | Verificar cifras y condiciones de fuente. No asegurar que una reducción de merma se traslada íntegramente a utilidad neta. |
| P336 | erradicación de sobreproducción | Retirar efecto ambiental garantizado; no se medirá ni se optimizará producción. |
| P337–P338 | integración y bajo error | Conservar distinción entre precisión y utilización; matizar «condición necesaria» y eliminar garantía de éxito. |
| P339–P340 | 42.5 pasteles; explosión de materiales | Sustituir por ejemplo monetario de total y participaciones. No se contemplan recetas, kilos ni órdenes automáticas; corregir además «como Un tablero» y «analéticamente». |
| P341 | tablero y juicio humano | Conservar: establece adecuadamente límites de interpretación. |
| P342 | entornos hostiles; invalida | Suprimir cierre exagerado y repetido. |
| P343 | mejora estable y estadísticamente defendible | Conservar como cautela, sin convertirlo en garantía. Distinguir error observado de significancia formal si se define un contraste. |
| P344 | apoyo al presupuesto y efectos adicionales | Conservar, incorporar distribución por insumo y evitar repetir el mismo límite en numerosos cierres. |

### Datos limitados e ingeniería de características

| Localizador | Fragmento o tema | Dictamen y ajuste |
|---|---|---|
| P345–P348 | Small Data; sobreajuste; características | Conservar apertura breve; fusionar definiciones repetidas con los apartados siguientes. |
| P349–P350 | Small Data frente a Big Data | Simplificar. Verificar atribución de definición a Alekseeva y no tratar tamaño pequeño, fragmentación y mala calidad como sinónimos necesarios. |
| P351–P352 | dimensionalidad; incapacidad matemática | Conservar dispersión del espacio de variables; retirar imposibilidad universal y ejemplos de fuentes no disponibles. |
| P353–P355 | sesgo–varianza; ecuación 2 | Conservar y delimitar la descomposición a error cuadrático bajo los supuestos pertinentes, no a cualquier métrica. |
| P356 | sesgo y problema necesariamente no lineal | Corregir: sesgo es una propiedad de la estimación; no todo fenómeno real requiere no linealidad ni toda regresión lineal subajusta. |
| P357 | Varianza | Conservar explicación de sensibilidad al conjunto de entrenamiento. |
| P358 | error irreducible y ruido blanco | Definirlo respecto de información y modelo disponibles; no identificar todo error impredecible con ruido blanco del mercado. |
| P359–P360 | sesgo cero; fracaso estrepitoso | Conservar riesgo de sobreajuste, retirar inevitabilidad y ejemplo de desabasto como hecho del caso. |
| P361–P363 | regularización | Conservar y explicar que las penalizaciones son algunas formas de controlar complejidad, no la totalidad de métodos. |
| P364 | Ridge y multicolinealidad | Aclarar que la multicolinealidad se refiere a correlación entre predictores, no entre predictor y variable objetivo. |
| P365 | Lasso; ecuación 3 | Conservar, revisar distinción tipográfica entre observado y estimado en la ecuación nativa y escalado de variables dentro del entrenamiento. |
| P366 | parámetro estocástico; variables irrelevantes | Lambda es un hiperparámetro de regularización, no necesariamente estocástico. Lasso puede anular coeficientes, pero ello no prueba irrelevancia económica ni causal. |
| P367 | inmune al ruido; seguro | Sustituir por reducción potencial de sobreajuste, verificable temporalmente; no garantizar estabilidad o flujo de caja. |
| P368–P370 | ingeniería y conocimiento tácito | Conservar vínculo y cambiar ventas por compras. Evitar «precisión estrictamente determinada» por variables: también intervienen datos, método y evaluación. |
| P371–P372 | rezagos y ventanas | Mantener teoría; mover longitudes concretas a metodología. No afirmar autocorrelación ya establecida. Revisar fórmula nativa y_(t−7), residuo de la escala diaria. |
| P373–P375 | seno/coseno | Conservar ecuación 4; adaptar periodo al índice elegido en datos semanales. Un ciclo de siete días no varía entre semanas completas si se usa el mismo día de referencia. |
| P376–P377 | exógenas conocidas | Conservar y ampliar a disponibilidad real, retrasos de publicación y predictores de cada horizonte. |
| P378–P379 | validación temporal | Conservar principio. Evitar prohibición universal de k-fold para cualquier serie; justificar el esquema temporal por el objetivo operativo de este estudio. |
| P380 | ventana fija, semana posterior | Conservar definición y cubrir también horizontes de dos a cuatro semanas si forman parte del alcance. |
| P381–P385 | mecanismo iterativo | Mover pasos a metodología y fusionar con P423–P431. Cambiar ingresos/demanda por compras. En ventana fija, el conocimiento se actualiza, no se expande en tamaño. |
| P386 | ventana expansiva | Conservar como alternativa teórica; distinguirla de la fija elegida. |
| P387 | MAE/MAPE aseguran robustez y expansión | Sustituir: evaluar no garantiza robustez. Usar métricas coherentes con H1, incluir participación y retirar expansión. |
| P388–P390 | sobreajuste inevitable; certidumbre de IA | Fusionar con introducción; conservar cautela de P389 y eliminar extremos de fracaso inevitable o certidumbre. |

### Evaluación y referencias

| Localizador | Fragmento o tema | Dictamen y ajuste |
|---|---|---|
| P391–P392 | métricas y método intuitivo | Conservar. Reemplazar equivalencia intuición–línea base por referencias reproducibles y separar errores de total y composición. |
| P393–P395 | definiciones de MAE/RMSE/MAPE | Fusionar con desarrollo posterior. Usar pesos monetarios, no pasteles; revisar referencias a ecuaciones 15,14,13, sin asumir que son correctas por sus campos almacenados. |
| P396–P397 | minimizar varianza del error | Simplificar: objetivo es evaluar pérdida predictiva; minimizar varianza aislada puede ignorar sesgo. |
| P398 | AIC premia complejidad | Corregir: AIC incorpora una penalización por número de parámetros. Distinguirlo de R² y de evaluación temporal. |
| P399 | evaluación fuera de muestra | Conservar y añadir que esos datos no deben usarse para ajustar hiperparámetros, pesos de combinación o transformaciones. |
| P400 | una configuración y aporte exógeno | Alinear con H1 única: modelo híbrido y distribución. Aporte exógeno queda complementario, no segunda condición principal. |
| P401–P402 | MAE | Conservar definición; simplificar título y revisar referencia duplicada «((15))». |
| P403–P406 | linealidad e interpretación de MAE | Conservar; ejemplos en moneda. Condensar el rótulo aislado de implicaciones. |
| P407–P408 | errores catastróficos; guardián | Sustituir por «RMSE y sensibilidad a errores grandes». Conservar fórmula, eliminar atribuciones financieras. |
| P409 | penalización exponencial, cuatro veces | Corregir: los términos se elevan al cuadrado, no exponencialmente; el factor cuatro se refiere a la contribución cuadrática, no al RMSE final. |
| P410–P411 | implicaciones del RMSE | Conservar argumento de sensibilidad y límite de interpretación; fusionar rótulo con párrafo. |
| P412 | menos desviaciones grandes | Matizar: menor RMSE indica menor media de errores cuadrados; no demuestra necesariamente menor cantidad de errores grandes. |
| P413–P419 | MAPE, ceros y escaladas | Conservar límites y reducir siete párrafos a dos o tres. Definir MASE/RMSSE y denominador calculado con entrenamiento; contemplar denominador cero. Añadir métricas de participaciones: MAPE no mide por sí mismo calidad de composición. |
| P420–P422 | repetición de validación | Fusionar con P378–P386; conservar una única explicación teórica. |
| P423 | rolling-window fijo | Conservar definición en el apartado único de validación. |
| P424–P428 | 52 semanas y pasos | Mover a metodología. Precisar si se evalúan los horizontes 1,2,3,4 o solo 1 y 4. Cuatro semanas no equivalen siempre a un mes calendario. |
| P429–P431 | fija frente a expansiva | Reducir repetición; justificar elección como decisión de diseño, no superioridad universal. Revisar compatibilidad de 52 semanas de entrenamiento con un rezago 52 y pérdidas iniciales por características. |
| P432 | desempeño esperado | Conservar como estimación histórica de desempeño; no implica estabilidad futura garantizada. |
| P433–P434 | fusión multicriterio | Cambiar a «Comparación con modelos de referencia». Varias métricas no constituyen una fusión si no se define agregación; fijar criterio primario antes del contraste. |
| P435 | MAPE 15% carece de valor | Sustituir exageración por necesidad de contextualizar la mejora mediante referencias; MAPE ya fue relegado a diagnóstico. |
| P436 | investigación realizada; siete días | Pasar a propuesta y definir referencias semanales. Evitar equivalencia entre último observado e intuición del dueño. Incorporar referencia de participaciones históricas. |
| P437 | ROI calculado con delta de error | Corregir prioritariamente: diferencia de error predictivo no es retorno de inversión. Quitar esa equivalencia y revisar ecuación 11 referenciada. |
| P438 | H1 significativa; MAPE; expansión | Sustituir íntegramente: no corresponde a H1 actual ni permite deducir merma, liquidez o rentabilidad. |
| P439 | marco experimental | Conservar evaluación comparativa temporal; evitar sugerir un experimento de efectos empresariales. |
| P440–P442 | validación, generalización y métricas | Condensar en un cierre y añadir desempeño de participación. La ventana cronológica no basta si hay filtraciones en preprocesamiento. |
| P443 | expansión y blindaje | Eliminar por contradicción directa con P442 y con delimitación del estudio. |

### Adopción y conclusión

| Localizador | Fragmento o tema | Dictamen y ajuste |
|---|---|---|
| P444–P449 | barreras tecnológicas, financieras, humanas | Conservar en forma breve; no duplicar extensamente cada eje. Vincular con viabilidad prevista del procedimiento y tablero. |
| P450–P451 | menos del 25% | Simplificar título y comprobar porcentaje, población y fuente antes de conservarlo. |
| P452 | capacidad de absorción | Conservar marco conceptual con referencia completa; eliminar «patologías» y bloqueos inevitables. |
| P453–P454 | ausencia absoluta de infraestructura | Matizar. No todas las microempresas carecen de infraestructura ni el caso carece de registros digitales. |
| P455 | antes de la intervención | Pasar a descripción del estado inicial acreditado. Cotejar autoría de Alekseeva, diferente de otras entradas del capítulo. |
| P456 | dependiente ventas; independientes compras | Invertir la formulación conforme al nuevo objetivo: compras y participaciones son respuestas; ventas históricas pueden ser predictoras conocidas. Eliminar imposibilidad universal y objetivo de optimizar caja. |
| P457–P458 | TCO prohibitivo | Conservar concepto de costo total; matizar inviabilidad no calculada. |
| P459 | componentes de costo hundido | Corregir: costos previstos, recurrentes y recuperables no son todos costos hundidos. |
| P460 | licencias | Conservar como componente posible, reconociendo opciones abiertas o de bajo costo. |
| P461 | LSTM exige GPU | Matizar: necesidad depende del tamaño y carga. Revisar referencia interna «Sección 2.3» conforme a numeración final. |
| P462 | consultoría y nuevas sucursales | No asumir contratación obligatoria ni expansión. Explicar necesidades posibles de integración y mantenimiento. |
| P463–P464 | alfabetización y perfiles | Conservar con lenguaje no estigmatizante: «Capacidades para interpretar datos y pronósticos». |
| P465 | tecnología y capacidades humanas | Conservar, distinguiendo evidencia de otras organizaciones de implementación futura en el caso. |
| P466–P467 | propietario carece; abandonará | Cambiar diagnóstico no acreditado por barreras posibles. Un usuario no necesita dominar RMSE internamente para utilizar una presentación adecuada. |
| P468–P470 | Lean Data Science e hibridación | Reducir, verificar atribuciones y definir enfoque. Llamar «integración tecnológica» a BI+herramientas; reservar modelo híbrido para la combinación predictiva. |
| P471 | AutoML | Retirar como propuesta si no se utilizará, o delimitar antecedente. No garantiza selección óptima ni control de fuga temporal. |
| P472 | fracciones de segundo; anula nube | Conservar parsimonia como criterio, sin prometer tiempo de ejecución o costo no medidos. |
| P473 | semáforos de caja y alertas automáticas | Reorientar al tablero previsto de importe, participaciones y errores. Corregir «como Un tablero». |
| P474 | viable; blinda; dinamiza | Pasar a beneficio potencial dependiente de datos, evaluación y uso; eliminar conclusión de viabilidad ya demostrada. |
| P475 | Conclusión | Conservar título y reconstruir síntesis. |
| P476–P477 | intuición condena; IA imperativa | Sustituir: la literatura no demuestra incapacidad del propietario ni superioridad necesaria del modelo propuesto. |
| P478 | parsimonia y validación | Conservar como fundamento de diseño; añadir mecanismo híbrido y coherencia de participaciones. |
| P479 | MAE/RMSE/MAPE garantizan máxima estabilidad | Corregir a evaluación futura con métricas monetarias y de participación; retirar ingresos, garantía y MAPE como prueba central. |
| P480 | DSS implementado | Sustituir por tablero previsto y criterios de interpretación. No afirmar barreras ya superadas. |
| P481 | certidumbre; expansión | Reescribir el cierre para explicar cómo los fundamentos permitirán contrastar H1, con posibilidad de respaldo parcial o ausencia de mejora. |

## Contenido teórico que falta desarrollar

### Importe de compras como variable objetivo

Definir la suma semanal de importes y distinguirla de ventas, demanda, consumo, pago efectivo y presupuesto óptimo. Explicar que el gasto puede cambiar por precios, cantidades, mezcla de insumos, descuentos y periodicidad de adquisición. Pronosticar el registro histórico no determina automáticamente cuánto debería comprarse.

### Modelo híbrido

Definir la integración prevista o sus alternativas justificadas: combinación de pronósticos estadísticos y de aprendizaje automático, o modelado complementario de componentes. Explicar por qué errores parcialmente distintos podrían hacer útil la combinación, pero también por qué estimar pesos con pocos datos puede sobreajustar. Una comparación entre métodos sin integración no satisface por sí sola el objetivo de un modelo híbrido. La selección final y sus parámetros pertenecen a metodología. Ver [combinación de pronósticos](https://otexts.com/fpp3/combinations.html).

### Composición y desagregación presupuestaria

Definir participación monetaria de un insumo como su importe dividido por el total, cuando este sea positivo. Explicar restricciones de no negatividad y suma. Si se distribuye todo el total entre «principales insumos», aclarar si se añade «otros» o si el denominador se restringe al subconjunto; no normalizar silenciosamente una parte como si fuera el total. Tratar semanas de importe cero sin convertir 0/0 en participación observada.

Relacionar pronóstico total, proporciones y asignación monetaria por insumo; distinguir proporciones históricas fijas de proporciones variables. Explicar que las restricciones aritméticas no garantizan precisión. Los enfoques de desagregación descendente y su coherencia agregada ofrecen una base pertinente: [pronósticos por niveles](https://otexts.com/fpp3/single-level.html).

### Evaluación de H1

Separar error monetario del total y error de participaciones, por ejemplo en puntos porcentuales. Definir referencia para cada uno, tratamiento de ceros y criterio primario antes de observar resultados. No elegir retrospectivamente la métrica o el horizonte que favorezca al híbrido. Explicar en metodología cómo se concluirá si mejora el total y empeora la composición. Las métricas monetarias actuales cubren solo parte de la hipótesis.

### Información disponible y ajuste temporal

Separar variables conocidas anticipadamente, como calendario, de variables futuras desconocidas, como clima observado o inflación aún no publicada. Explicar ajuste de transformaciones, selección de variables y pesos híbridos con entrenamiento, sin usar los datos finales para decidir esas configuraciones. Para horizontes de varias semanas, aclarar qué información existe en cada origen del pronóstico.

## Secuencia propuesta

1. Microempresa, conocimiento del negocio y planeación del presupuesto de abastecimiento.
2. Compras en repostería y diferencia entre importe monetario, demanda y cantidades físicas.
3. Series temporales semanales, calidad, continuidad, estacionalidad e intermitencia.
4. Métodos estadísticos y de aprendizaje automático pertinentes para datos limitados.
5. Fundamentos de integración de modelos híbridos.
6. Distribución porcentual y coherencia entre total y asignaciones por insumo.
7. Ingeniería de características, regularización y disponibilidad temporal de predictores.
8. Evaluación fuera de muestra y métricas monetarias y de participación.
9. BI, comunicación del pronóstico y barreras de adopción.
10. Síntesis de fundamentos y relación con la hipótesis propuesta.

La amplitud de RNN/LSTM, Newsvendor, psicología de decisiones y S&OP debería corresponder a su papel real. El capítulo dedica actualmente más desarrollo a algunos de esos antecedentes que a los dos componentes nuevos del objetivo.

## Puntos técnicos contrastados

- Diferenciación y estabilización de varianza son tratamientos distintos: [estacionariedad y diferenciación](https://otexts.com/fpp3/stationarity.html).
- AIC incorpora penalización por parámetros; no simplemente premia complejidad: [selección de predictores](https://otexts.com/fpp3/selecting-predictors.html).
- RMSE usa raíz de la media de cuadrados; MAPE presenta problemas con ceros y valores próximos a cero: [evaluación de precisión](https://otexts.com/fpp3/accuracy.html).

No se verificaron una por una las referencias, porcentajes ni citas textuales del capítulo. Las observaciones de autoría y cifras son solicitudes de cotejo, no dictámenes de falsedad. Tampoco se atribuyen al documento defectos visuales basados solo en extracción: las expresiones nativas de Word se inspeccionaron en su estructura, pero requieren comprobación visual al editar.
