# Plan de ilustración y reorganización visual de la tesis

**Documento de trabajo para aprobación — 15 de octubre de 2026**

## 1. Alcance y regla de aprobación

Este plan sustituye la propuesta anterior de imágenes combinadas. Cada gráfica se generó como una pieza independiente, con tipografía, leyendas y proporciones aptas para lectura en una página de tesis. En esta etapa **no se modifica** `TESIS_SEP2026_Rev61_(ZUJ)_Final.docx`.

Después de la aprobación se creará una nueva revisión; la Rev61 permanecerá intacta. La numeración definitiva se asignará por posición con rótulos automáticos de Word, no con los identificadores internos I01–I16.

## 2. Criterio editorial y gráfico

- Una idea principal por figura.
- PNG de 300 ppp para inserción estable en Word; SVG como respaldo vectorial.
- Ancho objetivo: 15–16 cm para gráficas completas y 11–13 cm para diagramas simples.
- Texto mínimo equivalente a 9 puntos al tamaño final.
- Paleta consistente y distinguible en escala de grises; no depender sólo del color.
- Título analítico breve dentro de la figura; explicación, fuente y alcance en el pie.
- Leyendas fuera del área de datos cuando exista riesgo de cubrir información.
- Cero capturas de pantalla de tablas o resultados que puedan presentarse como tabla editable.
- Toda cifra deberá corresponder a la corrida validada `run_20261013T193604Z_157556` o indicar explícitamente la corrida de sensibilidad.
- La exposición seguirá una progresión académica: descripción básica de la serie, diagnóstico temporal, diseño de validación, comparación de modelos, evaluación composicional y aplicación presupuestaria.
- Ninguna tabla, figura, gráfica, ilustración o ecuación aparecerá sin ser anunciada mediante una referencia cruzada en el párrafo inmediatamente anterior o en el párrafo introductorio del mismo bloque.
- Después de cada elemento deberá existir un párrafo que interprete el resultado o explique su función; no bastará con repetir el título o describir colores y ejes.
- Las referencias cruzadas se crearán con campos automáticos de Word. No se escribirán manualmente números como “Figura 4” o “Tabla 7”.
- Cada ecuación se presentará de manera individual. No se agruparán dos o tres expresiones independientes bajo un mismo número ni se colocarán consecutivamente sin explicación intermedia.

## 3. Selección propuesta de figuras nuevas

### 3.1 Figuras esenciales para el cuerpo de la tesis

| ID | Archivo | Sección sugerida | Función narrativa | Pie propuesto, sujeto a edición |
|---|---|---|---|---|
| I01 | `I01_flujo_proceso.png` | Metodología / Procedimiento metodológico | Resume de extremo a extremo el proceso reproducible. | Flujo metodológico desde la integración de fuentes hasta la asignación presupuestaria y la validación. Fuente: elaboración propia. |
| I02 | `I02_validacion_temporal.png` | Metodología / Validación temporal rolling window | Explica visualmente entrenamiento, origen y horizonte sin fuga temporal. | Esquema de validación temporal con orígenes sucesivos y horizonte de cuatro semanas. Fuente: elaboración propia. |
| I03 | `I03_cobertura_semanal.png` | Desarrollo / Preparación de fuentes | Muestra qué fuentes están disponibles en cada semana y evita confundir ausencia con cero. | Cobertura semanal de las fuentes integradas en el panel analítico. Fuente: elaboración propia. |
| I04 | `I04_serie_semanal.png` | Desarrollo / Caracterización exploratoria | Presenta la dinámica del importe semanal y los puntos de evaluación. | Serie semanal del importe elegible y delimitación de los periodos de evaluación. Fuente: elaboración propia. |
| I05 | `I05_pareto_categorias.png` | Desarrollo / Definición de categorías | Justifica la concentración y la selección de categorías elegibles. | Concentración acumulada del gasto por categoría analítica. Fuente: elaboración propia. |
| I07 | `I07_observado_pronosticado.png` | Resultados / Rendimiento comparativo | Permite juzgar magnitud, dirección y error del pronóstico. | Valores observados y pronosticados del importe semanal en los horizontes evaluados. Fuente: elaboración propia. |
| I08 | `I08_rmse.png` | Resultados / Rendimiento comparativo | Compara modelos con una métrica monetaria principal. | RMSE por modelo y horizonte de pronóstico. Fuente: elaboración propia. |
| I10 | `I10_error_composicion_categoria.png` | Resultados / Distribución porcentual | Localiza en qué categorías se concentra el error de asignación. | Error absoluto de participación por categoría analítica. Fuente: elaboración propia. |
| I12 | `I12_H1_monetario.png` | Resultados / Contraste de hipótesis | Expone el contraste pareado de la componente monetaria. | Diferencias pareadas de pérdida monetaria entre el modelo propuesto y la línea base. Fuente: elaboración propia. |
| I13 | `I13_H1_composicion.png` | Resultados / Contraste de hipótesis | Expone por separado la evidencia composicional. | Diferencias pareadas de pérdida composicional entre el modelo propuesto y la línea base. Fuente: elaboración propia. |
| I16 | `I16_presupuesto_agregado.png` | Desarrollo o Resultados / Comunicación | Traduce el modelo a una salida operativa comprensible. | Asignación agregada del presupuesto pronosticado por categoría analítica. Fuente: elaboración propia. |

La selección central contiene once figuras. Si se requiere una versión más breve, I03 puede convertirse en tabla y sólo I04 permanecería como evidencia exploratoria; I12 e I13 pueden conservarse como figuras consecutivas, nunca como un panel ilegible.

### 3.2 Figuras recomendadas para anexos

| ID | Archivo | Anexo propuesto | Motivo |
|---|---|---|---|
| I06 | `I06_mapa_composicion.png` | Anexo C. Diagnóstico composicional | Es útil para auditoría, pero demasiado densa para interrumpir el argumento principal. |
| I09 | `I09_mae.png` | Anexo D. Métricas complementarias | Complementa RMSE; en el cuerpo bastaría una tabla que reporte ambas. |
| I11 | `I11_error_composicion_macro.png` | Anexo C | Agrega el diagnóstico por macrogrupo y complementa I10. |
| I14 | `I14_ablaciones.png` | Anexo E. Sensibilidad y ablaciones | Sustenta el aporte incremental de fuentes y componentes. |
| I15 | `I15_presupuesto_semanal.png` | Anexo F. Salida operativa detallada | Conserva el detalle semanal; I16 comunica mejor el resultado agregado en el cuerpo. |

### 3.3 Gráficas básicas de series de tiempo que deben incorporarse

Antes de presentar validación, modelos o métricas se añadirá un bloque de análisis exploratorio temporal. El propósito es conducir al lector de lo básico a lo complejo y justificar las decisiones metodológicas posteriores.

| ID provisional | Gráfica | Sección sugerida | Pregunta que responde | Decisión editorial |
|---|---|---|---|---|
| ST01 | Serie semanal completa del importe elegible | Desarrollo / Construcción del panel | ¿Cómo evoluciona la variable objetivo y dónde existen cambios visibles, picos o periodos atípicos? | I04 se ajustará para cumplir esta función, sin mezclar resultados de modelos. Es obligatoria en el cuerpo. |
| ST02 | Serie semanal con media y mediana móviles | Desarrollo / Caracterización exploratoria | ¿Existen cambios locales de nivel o variabilidad? | Nueva gráfica individual. La ventana deberá justificarse y se distinguirá de cualquier suavizamiento usado para pronosticar. |
| ST03 | Histograma y, por separado, diagrama de caja del importe semanal | Desarrollo / Caracterización exploratoria | ¿Cuál es la distribución marginal, su asimetría y la presencia de valores extremos? | Serán dos gráficas independientes si ambas aportan evidencia; no se combinarán en un panel pequeño. Una puede pasar al anexo. |
| ST04 | Gráfica de rezagos | Desarrollo / Caracterización exploratoria | ¿Qué relación visual existe entre \(Y_t\) y rezagos seleccionados? | Mostrar sólo rezagos relevantes y el tamaño de muestra. Puede ubicarse en anexo si la evidencia es débil. |
| ST05 | Función de autocorrelación | Marco teórico aplicado o Desarrollo | ¿Existe dependencia temporal aprovechable y hasta qué rezago? | Nueva gráfica individual con bandas de referencia e indicación expresa de que no prueban causalidad. |
| ST06 | Perfil estacional por semana del año o periodo disponible | Desarrollo / Caracterización exploratoria | ¿Hay un patrón calendario repetible? | Sólo se incorporará si hay suficientes ciclos comparables. Con historia corta se sustituirá por agrupaciones mensuales o por evento calendario y se declarará la limitación. |
| ST07 | Serie de ventas y compras normalizadas, en gráficas alineadas | Desarrollo / Integración de ventas | ¿Los movimientos entre fuentes son temporalmente comparables? | No usar doble eje. Si las escalas difieren, normalizar o presentar dos gráficas alineadas con la misma escala temporal. |
| ST08 | Descomposición tendencia–estacionalidad–residuo | Anexo de diagnóstico | ¿La descomposición aporta una estructura interpretable? | Condicionada a longitud y periodicidad suficientes. No se forzará una descomposición si sólo produce patrones inestables. |

#### Secuencia pedagógica recomendada

1. Definir la variable y la frecuencia mediante T01 y la ecuación de agregación semanal.
2. Presentar ST01 para reconocer nivel, continuidad, picos y posibles cambios de régimen.
3. Presentar ST02 y las gráficas de distribución para describir tendencia local, dispersión, asimetría y valores extremos.
4. Presentar ST04 y ST05 para discutir dependencia temporal.
5. Presentar ST06 y ST07 para evaluar calendario y predictores exógenos, sólo cuando los datos lo permitan.
6. Pasar entonces a I02, los modelos, la evaluación rolling window y las métricas comparativas.

No se interpretarán como “estacionalidad”, “tendencia” o “dependencia” simples rasgos visuales aislados. Cada afirmación se acompañará de la evidencia descriptiva o estadística correspondiente y de sus limitaciones por tamaño de muestra.

## 4. Reorganización de las figuras actuales

| Figura actual | Acción propuesta | Sustitución o destino |
|---|---|---|
| Cobertura de datos | Sustituir | I03, con mayor legibilidad. |
| Auditoría de datos | Convertir en tabla | Tabla de auditoría y trazabilidad, no imagen. |
| Serie semanal | Sustituir | I04. |
| Distribución y ceros | Separar o llevar a anexo | Tabla de intermitencia más histograma individual opcional. |
| Ventas | Integrar en evidencia de fuentes | Tabla descriptiva; gráfica sólo si aporta relación temporal comprobable. |
| Composición observada | Sustituir | I06 en anexo. |
| Categorías principales | Sustituir | I05. |
| Particiones temporales | Sustituir | I02. |
| Validación interna | Convertir en diagrama o tabla | I02 más tabla de tamaños de muestra. |
| Asignación de cuatro semanas | Separar | I15 en anexo e I16 en cuerpo. |
| Controles de calidad | Convertir en tabla | Lista verificable de controles, tolerancias y resultado. |
| Errores monetarios | Sustituir | I08; MAE pasa a I09/anexo. |
| Error de composición | Sustituir | I10; I11 como complemento en anexo. |
| Composición observada/estimada | Conservar sólo si no duplica I10 | Preferencia: tabla resumida o anexo. |
| Pérdida pareada H1 | Separar | I12 e I13, una figura por componente. |

## 5. Nuevas ilustraciones conceptuales sugeridas

Estas ilustraciones deberán ser diagramas propios y sencillos, no decorativos.

1. **Arquitectura conceptual del modelo híbrido.** Entradas de compras, ventas y calendario; módulo monetario; módulo composicional; reconciliación y presupuesto final. Ubicación: Marco teórico, “Fundamentos de integración del modelo híbrido”. Prioridad alta.
2. **Jerarquía de clasificación de insumos.** Registro original → clasificación analítica → macrogrupo → condición de elegibilidad. Ubicación: Desarrollo, “Definición de categorías”. Prioridad alta.
3. **Semántica de ausencia, cero e imputación.** Tres casos con ejemplos: semana cubierta sin compra, semana no cubierta y dato imputado. Ubicación: Marco teórico o Metodología. Prioridad alta.
4. **Disponibilidad temporal de predictores.** Línea de tiempo que muestre qué información puede conocerse al emitir cada pronóstico. Ubicación: Marco teórico, “Disponibilidad de variables exógenas”. Prioridad alta.
5. **Reconciliación total–participaciones.** Pronóstico total multiplicado por vector de participaciones, redondeo y ajuste del residuo para preservar la suma. Ubicación: Marco teórico. Prioridad alta.
6. **Ciclo de uso gerencial del presupuesto.** Pronosticar → revisar restricciones → aprobar → comprar → observar → retroalimentar. Ubicación: Discusión, implicaciones operativas. Prioridad media.
7. **Mapa de riesgos de validez.** Riesgos de historia corta, cambios de régimen, calidad de clasificación y disponibilidad de ventas, con mitigaciones. Ubicación: Discusión, validez y limitaciones. Prioridad media.
8. **Paquete de reproducibilidad.** Datos de entrada, configuración, código, identificador de corrida, métricas y artefactos. Ubicación: Desarrollo o Anexo B. Prioridad media.

## 6. Tablas adicionales recomendadas

| ID de trabajo | Tabla | Sección | Contenido mínimo |
|---|---|---|---|
| T01 | Diccionario operativo de variables | Metodología | Variable, definición, unidad, fuente, frecuencia, disponibilidad al origen y transformación. |
| T02 | Reglas de elegibilidad y exclusión | Desarrollo | Clasificación analítica, regla, justificación, tratamiento y ejemplo. |
| T03 | Cobertura de fuentes | Desarrollo | Fuente, primera/última fecha, semanas cubiertas, faltantes, duplicados y tratamiento. |
| T04 | Diseño de validación | Metodología | Origen, entrenamiento, horizonte, semanas evaluadas y observaciones útiles. |
| T05 | Modelos e hiperparámetros | Metodología | Modelo, entradas, configuración, regularización y criterio de selección. |
| T06 | Descriptivos del importe semanal | Desarrollo | n, media, mediana, desviación, mínimo, máximo, ceros e intermitencia. |
| T07 | Rendimiento por horizonte | Resultados | Modelo, h, RMSE, MAE, MASE si procede, rango o intervalo. |
| T08 | Precisión composicional | Resultados | Categoría, participación observada, estimada, error absoluto y contribución al total. |
| T09 | Ablaciones y sensibilidad | Resultados o anexo | Configuración, fuentes disponibles, RMSE, MAE y cambio frente al modelo completo. |
| T10 | Decisión de hipótesis | Resultados | Componente, pérdida propuesta, pérdida base, diferencia, intervalo, criterio y conclusión. |
| T11 | Controles de coherencia | Desarrollo | Control, tolerancia, resultado y evidencia: sumas, no negatividad, duplicados y reconciliación. |
| T12 | Manifiesto de reproducibilidad | Anexo B | Corrida, fecha, archivos, hash, versión de código y artefactos generados. |

Se revisarán las 42 tablas existentes antes de agregar nuevas: T01–T12 son funciones editoriales, no una instrucción para duplicar información ya presente.

### 6.1 Regla de introducción e interpretación de tablas

Cada tabla deberá quedar integrada mediante tres componentes:

1. **Párrafo previo:** plantea la pregunta, delimita el contenido y contiene la referencia cruzada automática, por ejemplo: “La Tabla X resume la cobertura temporal y los controles aplicados a cada fuente”.
2. **Tabla y nota:** presenta unidades, abreviaturas, fuente, periodo y aclaraciones necesarias.
3. **Párrafo posterior:** interpreta uno o dos hallazgos relevantes y explica su consecuencia metodológica u operativa. No repetirá celda por celda.

Durante la revisión de Rev62 se localizarán tablas existentes sin mención previa, tablas citadas sólo después de aparecer, referencias numéricas escritas manualmente y tablas sin interpretación. Todos esos casos deberán corregirse.

## 7. Ecuaciones que conviene incorporar o normalizar

Todas deberán insertarse como ecuaciones nativas de Word, con numeración consistente, referencia cruzada automática y definición inmediata de símbolos. La estructura obligatoria será: párrafo introductorio con referencia a la ecuación, una sola ecuación numerada y un párrafo posterior que explique su significado, unidades, supuestos y uso dentro del estudio.

Si la Rev61 contiene dos o tres ecuaciones consecutivas, se evaluará si son realmente una derivación inseparable. En caso contrario se separarán, se numerarán individualmente y se añadirá un párrafo explicativo entre ellas. No se permitirá una sucesión de fórmulas sin narrativa.

1. **Agregación semanal del importe elegible**

   \[Y_t=\sum_{i\in\mathcal{E}_t} x_i\]

   donde \(\mathcal{E}_t\) es el conjunto de registros elegibles de la semana \(t\).

2. **Participación observada por categoría**

   \[p_{k,t}=\frac{Y_{k,t}}{Y_t}\]

   El párrafo posterior explicará que la participación representa la fracción del importe semanal atribuible a la categoría \(k\), así como el tratamiento aplicado cuando el total semanal es cero.

3. **Restricción de cierre de las participaciones**

   \[\sum_{k=1}^{K}p_{k,t}=1\]

   Se explicará que esta restricción diferencia los datos composicionales de variables independientes y condiciona el método de evaluación.

4. **Pronóstico híbrido ponderado**

   \[\widehat{Y}_{t+h}=\sum_{m=1}^{M}w_m\widehat{Y}^{(m)}_{t+h}\]

   El texto posterior identificará los modelos participantes y cómo se estiman los pesos sin utilizar información futura.

5. **Restricción de no negatividad de los pesos**

   \[w_m\ge 0\]

   Se explicará que esta condición evita contribuciones negativas difíciles de interpretar en la combinación propuesta.

6. **Restricción de suma de los pesos**

   \[\sum_{m=1}^{M}w_m=1\]

   Se explicará que la combinación queda expresada como promedio ponderado y cómo se resuelve el redondeo numérico.

7. **Asignación presupuestaria por categoría**

   \[\widehat{B}_{k,t+h}=\widehat{Y}_{t+h}\widehat{p}_{k,t+h}\]

8. **Reconciliación del redondeo**

   \[r_{t+h}=\widehat{Y}_{t+h}-\sum_k\operatorname{round}(\widehat{B}_{k,t+h},2)\]

   Debe explicarse la regla transparente con la que el residuo se reasigna.

9. **RMSE por horizonte**

   \[\operatorname{RMSE}_h=\sqrt{\frac{1}{N_h}\sum_o(Y_{o,h}-\widehat{Y}_{o,h})^2}\]

   El párrafo posterior explicará sus unidades monetarias, su sensibilidad a errores grandes y el significado de \(N_h\).

10. **MAE por horizonte**

   \[\operatorname{MAE}_h=\frac{1}{N_h}\sum_o|Y_{o,h}-\widehat{Y}_{o,h}|\]

   Se explicará su interpretación como error absoluto medio en unidades monetarias y su papel complementario frente al RMSE.

11. **MASE, si se conserva en resultados**

   \[\operatorname{MASE}=\frac{\frac{1}{N}\sum_t|Y_t-\widehat{Y}_t|}{\frac{1}{T-s}\sum_{t=s+1}^{T}|Y_t-Y_{t-s}|}\]

12. **Error composicional absoluto**

   \[E_{\mathrm{comp},o,h}=\frac{1}{K}\sum_{k=1}^{K}|p_{k,o,h}-\widehat{p}_{k,o,h}|\]

13. **Pérdida conjunta normalizada**

   \[L_{o,h}=\alpha\,L^{\mathrm{mon}}_{o,h}+(1-\alpha)L^{\mathrm{comp}}_{o,h}\]

   La tesis deberá justificar \(\alpha\), no fijarlo sólo por conveniencia.

14. **Diferencia pareada para H1**

   \[d_{o,h}=L^{\mathrm{propuesto}}_{o,h}-L^{\mathrm{base}}_{o,h}\]

   Valores negativos favorecen al modelo propuesto; deben reportarse junto con intervalo de incertidumbre y tamaño de muestra.

15. **Restricción de información disponible**

   \[\mathcal{X}_{o,h}\subseteq\mathcal{I}_o\]

   Formaliza que ningún predictor del horizonte futuro puede utilizar información posterior al origen \(o\).

### 7.1 Auditoría específica de ecuaciones existentes

Antes de insertar ecuaciones nuevas se elaborará una matriz con: número actual, sección, propósito, símbolos definidos, referencia previa, explicación posterior, posible duplicidad y acción propuesta. Para cada uno de los 61 objetos matemáticos detectados en Rev61 se aplicarán estas reglas:

- Separar expresiones independientes que actualmente comparten línea, bloque o explicación.
- Mantener juntas únicamente expresiones que formen una sola identidad o definición inseparable; aun así, se justificará editorialmente.
- Añadir una frase previa del tipo “La Ecuación X define…” o “Como se muestra en la Ecuación X…”.
- Añadir después un párrafo que explique qué calcula, cómo se usa y qué representan sus símbolos.
- Definir cada símbolo en su primera aparición y conservar la misma notación en toda la tesis.
- Indicar unidades en el texto, especialmente para importes, errores y horizontes.
- Evitar que una ecuación quede al inicio o final de página separada del párrafo que la explica.
- Eliminar ecuaciones repetidas o meramente decorativas que no se utilicen en metodología o resultados.

### 7.2 Plantilla editorial para cada ecuación

**Párrafo previo:** “El error cuadrático medio utilizado para comparar los modelos en el horizonte \(h\) se define mediante la Ecuación X.”

**Ecuación X:** una única expresión matemática.

**Párrafo posterior:** “En esta expresión, \(Y_{o,h}\) representa… La métrica se expresa en… Un valor menor indica… En este estudio se calcula para…”.

## 8. Imágenes o tablas localizables en las referencias

No se propone copiar directamente estas piezas. Sirven para fundamentar o inspirar una adaptación propia, citando la fuente y comprobando las condiciones de uso. La página indicada es la **página PDF (1 basada)**, para que pueda localizarse sin ambigüedad.

| Referencia/archivo | Página PDF | Identificador localizable | Uso potencial |
|---|---:|---|---|
| Hübner et al., *Machine-learning-based demand forecasting against food waste* | 3 | **Figure 1 — Scope of the multi-dimensional assessment** | Ejemplo de delimitación visual del sistema; podría inspirar un diagrama propio del alcance de la tesis. |
| Mismo artículo | 8 | **Figure 2 — Direct machine learning pipeline results...** | Ejemplo de desglose de contribuciones; sólo sería pertinente como antecedente ambiental, no como resultado propio. |
| Mismo artículo | 8 | **Figure 3 — Life cycle contributions...** | Ejemplo de composición de impactos; posible referencia visual para discutir beneficios indirectos. |
| Mismo artículo | 9 | **Figure 4 — Observed return values of Baseline Approach 2...** | Ejemplo de comparación entre valores reales, virtuales y evitados. |
| Makridakis et al., *Statistical and Machine Learning forecasting* | 14 | **Fig. 1 — Three possible multi-step-ahead forecasting approaches** | Útil para adaptar un esquema propio que explique estrategia iterativa, directa y multi-salida. |
| Mismo artículo | 15 | **Fig. 2 — Forecasting performance (sMAPE)...** | Referencia de diseño para comparación global de métodos; no conviene copiar sus datos. |
| Mismo artículo | 18 | **Fig. 3 — Forecasting performance versus model fitting** | Útil para explicar ajuste frente a generalización. |
| Mismo artículo | 18 | **Fig. 4 — Forecasting performance versus computational complexity** | Útil en discusión sobre complejidad apropiada para una microempresa. |
| Mismo artículo | 14 | **Table 8 — Performance across various horizons** | Modelo de tabla para comparar desempeño por horizonte. |
| Mismo artículo | 15 | **Table 9 — MASE across various horizons** | Modelo de tabla para métrica escalada por horizonte. |
| INEGI, EAP/MIPYMES 2023 | 2 | **Cuadro 1** | Contextualización cuantitativa de microempresas; usar datos/cita, preferentemente rehacer tabla o gráfico propio. |
| Alonso García Velasco, TFG | 15 | **Figura 1.2 — Arquitectura MLOps** | Referencia conceptual para el diagrama de reproducibilidad, si se decide incorporar la perspectiva MLOps. |
| Mismo TFG | 31 | **Figura 3.1 — Ciclo de vida Vertex AI** | Sólo como antecedente de ciclo de vida; no trasladar arquitectura de plataforma al caso sin justificación. |
| Mismo TFG | 54 | **Figura 5.1 — Tipos de data drift** | Posible referencia para trabajo futuro sobre deriva de datos. |

## 9. Orden visual propuesto por capítulo

1. **Introducción:** ninguna figura técnica salvo que se apruebe un esquema mínimo del problema y contribución.
2. **Marco teórico:** arquitectura conceptual híbrida; disponibilidad temporal; reconciliación total–participaciones. Las figuras de artículos se citarán como antecedentes o se adaptarán, no se insertarán sin necesidad.
3. **Metodología:** I01, I02 y jerarquía de clasificación; T01, T02, T04 y T05.
4. **Desarrollo:** bloque básico ST01–ST07 según disponibilidad de datos; después I03, I05 y, si se requiere, I16; T03, T06 y T11.
5. **Resultados:** I07, I08, I10, I12 e I13; T07, T08 y T10.
6. **Discusión:** ciclo gerencial y mapa de riesgos sólo si mejoran la síntesis; evitar repetir resultados.
7. **Anexos:** I06, I09, I11, I14 e I15; T09 y T12.

## 10. Proceso de modificación después de la aprobación

1. Crear `TESIS_SEP2026_Rev62_(ZUJ)_Final.docx`; conservar Rev61 sin cambios.
2. Inventariar y eliminar únicamente las figuras que serán sustituidas, manteniendo su texto explicativo hasta reescribirlo.
3. Elaborar una matriz de auditoría de todas las tablas, figuras, ilustraciones, gráficas y ecuaciones existentes, indicando si poseen mención previa, campo de referencia cruzada, pie o número, fuente y párrafo interpretativo posterior.
4. Generar las gráficas básicas ST01–ST08 que resulten metodológicamente válidas y validar que sus conclusiones sean compatibles con la extensión de la serie.
5. Insertar cada imagen por separado, dimensionarla al ancho aprobado y aplicar el estilo de párrafo de figura.
6. Rehacer los pies con campos automáticos `SEQ`, marcadores y referencias cruzadas; actualizar la tabla de figuras.
7. Modificar los párrafos previos de todos los elementos visuales y tabulares para introducirlos mediante una referencia cruzada automática.
8. Añadir o corregir el párrafo posterior de cada elemento para interpretar el hallazgo, su función y su limitación cuando corresponda.
9. Convertir capturas de resultados a tablas editables donde corresponda.
10. Auditar los 61 objetos matemáticos existentes, separar ecuaciones independientes y agregar un párrafo previo y otro explicativo para cada ecuación conservada.
11. Incorporar sólo las nuevas tablas y ecuaciones aprobadas, eliminando duplicidad con las 42 tablas y los objetos matemáticos ya existentes.
12. Verificar que todas las cifras procedan de la corrida declarada y que ninguna referencia conserve el identificador de una corrida anterior.
13. Actualizar todos los campos de Word y comprobar que no existan referencias rotas, numeraciones manuales o elementos sin llamada en el texto.
14. Renderizar el documento completo a imágenes/PDF; revisar cortes, pies huérfanos, ecuaciones aisladas, tamaño de letra, referencias cruzadas y saltos de página.
15. Entregar Rev62, PDF de control visual, matriz de auditoría, carpeta final de figuras y manifiesto de trazabilidad.

## 11. Decisiones solicitadas para aprobación

La aprobación puede darse sobre el plan completo o con ajustes a estos puntos:

- Selección de once figuras para el cuerpo y cinco para anexos.
- Incorporación progresiva de las gráficas básicas ST01–ST07; ST08 queda condicionada a suficiencia temporal.
- Incorporación de las cinco ilustraciones conceptuales de prioridad alta.
- Conversión de auditoría, controles de calidad y parte de las métricas a tablas editables.
- Uso de I16 en el cuerpo e I15 en anexo.
- Empleo de referencias externas sólo como base para adaptaciones propias y citadas.
- Auditoría y corrección de las referencias cruzadas y de los párrafos previos y posteriores de todos los elementos académicos.
- Separación y explicación individual de las ecuaciones existentes y nuevas.
- Creación de Rev62 una vez aprobada la propuesta.

## 12. Artefactos ya disponibles para revisión

Las figuras individuales se encuentran en `documentacion/figuras_individuales_propuesta_20261015/`. Cada figura dispone de PNG, SVG y, cuando aplica, CSV de datos. `manifiesto_figuras.csv` y `manifiesto_figuras.json` documentan título, fuente, dimensiones y archivo asociado.
