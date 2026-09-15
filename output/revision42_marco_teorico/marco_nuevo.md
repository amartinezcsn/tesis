El presente marco teórico desarrolla los fundamentos conceptuales y matemáticos para el pronóstico del importe total semanal de compras y su distribución porcentual entre los principales insumos de una microempresa de repostería. Se examinan las series temporales semanales, los métodos estadísticos y de aprendizaje automático, y las estrategias para integrarlos en un modelo híbrido. Posteriormente, se abordan la desagregación presupuestaria, el tratamiento de datos limitados y la evaluación temporal mediante métricas de error monetario y de participación. Finalmente, se analiza el uso de inteligencia de negocios como apoyo a la planeación del presupuesto de abastecimiento. [[FPP; POWER]]

## Microempresa y planeación del presupuesto de abastecimiento

### Recursos de información y conocimiento del negocio

Las empresas pequeñas presentan condiciones heterogéneas de digitalización. La disponibilidad de registros, las competencias del personal y los recursos para integrar herramientas condicionan el uso de analítica. Estas restricciones justifican procedimientos proporcionales a la información disponible, pero no permiten asumir que toda microempresa carece de registros o que una solución tecnológica tendrá beneficios automáticos. En Cup&Cake, la pertinencia del procedimiento se evaluará respecto de la necesidad de anticipar el presupuesto de compras. [[OECD]]

La experiencia del responsable del negocio puede aportar información sobre celebraciones, cambios de proveedores o adquisiciones extraordinarias que no aparece explícitamente en una serie. Ese conocimiento permite interpretar registros y proponer variables, mientras que las reglas de pronóstico hacen reproducible la estimación. La complementariedad requiere distinguir hechos documentados de expectativas y conservar el momento en que cada dato estuvo disponible. [[FPP]]

### Pronóstico como información para decidir

Un pronóstico puntual resume una distribución de resultados posibles. Bajo pérdida cuadrática, el valor que minimiza el error esperado es la media condicional. La ecuación (2.1) adapta esta propiedad al importe de compras: la estimación depende de la información existente en el origen del pronóstico, sin utilizar datos posteriores. [[ESL]]

@@eq|media|\hat{y}_{t+h|t}=E(y_{t+h}\mid I_t)

En esta notación, y representa el importe semanal observado, t es la última semana conocida, h es el horizonte e I representa la información disponible. El sombrero distingue el pronóstico del valor observado y la barra vertical separa el periodo pronosticado del origen de información. Una estimación puntual ayuda a formular expectativas, pero no determina por sí sola la decisión presupuestaria del responsable. [[ESL; POWER]]

La planeación del presupuesto utilizará esa estimación como un insumo para revisar recursos destinados al abastecimiento. Un sistema de soporte a la decisión organiza datos y modelos para facilitar la valoración de alternativas; la decisión final también puede incorporar restricciones que el modelo no observa. Por ello, el estudio evaluará precisión predictiva y no supondrá que un menor error produce necesariamente un retorno financiero positivo. [[POWER]]

## Compras monetarias y contexto de la repostería

### Delimitación de la variable objetivo

Pronosticar requiere definir con precisión qué se observa, con qué frecuencia y para qué horizonte. En esta investigación, la respuesta principal será el importe total semanal registrado de compras. Las ventas, el consumo de ingredientes y las existencias son magnitudes diferentes: pueden aportar contexto, pero no sustituyen la variable definida. La comparación entre modelos deberá mantener la misma respuesta y las mismas unidades monetarias. [[FPP]]

El importe de una adquisición puede variar por cantidad, precio y composición de insumos. Además, la fecha de compra puede diferir de la fecha de consumo o pago. Por tanto, la interpretación prevista será presupuestaria: se intentará anticipar el registro monetario de compras, sin identificarlo con una cantidad óptima de abastecimiento. Esta delimitación mantiene separado el objetivo de predicción de las inferencias explicativas o causales. [[SHM]]

### Agregación del importe y niveles de análisis

Los pronósticos jerárquicos representan series relacionadas mediante sumas. Adaptada al caso, la identidad de agregación expresa el importe semanal total como suma de los importes de las categorías de insumos. La ecuación (2.2) es una aplicación de esa estructura aditiva, no un modelo causal de costos. [[HIER]]

@@eq|total|y_t=\sum_{j=1}^{J}b_{j,t}

Aquí, b es el importe del insumo o categoría j y J es el número de categorías mutuamente excluyentes que cubren el total. Si solo se presentan los principales insumos, será necesario conservar una categoría residual para las demás compras o declarar que se trabaja con un subtotal. La suma evita que las asignaciones se interpreten como un total cuando omiten parte de sus componentes. [[HIER]]

La perecibilidad aporta contexto a la periodicidad de las compras, pero no hace equivalentes el pronóstico monetario y la planificación de inventarios. La frecuencia y el nivel de agregación deben responder a la decisión analizada. En el caso propuesto, la escala semanal facilitará la revisión del presupuesto; la traducción de importes a unidades físicas requeriría precios, recetas, existencias y condiciones de suministro que exceden ese pronóstico. [[FPP]]

## Series temporales semanales y calidad de los registros

### Frecuencia y continuidad

Una serie temporal es una secuencia ordenada de observaciones. La agregación semanal debe conservar un calendario consistente y distinguir ausencia de compra de ausencia de registro. Rellenar automáticamente huecos con ceros cambiaría el fenómeno observado. La continuidad de las fuentes y la identificación de semanas incompletas deberán examinarse antes de interpretar patrones o entrenar modelos. [[FPP]]

### Nivel tendencia y estacionalidad

La descomposición aditiva representa una serie mediante tendencia-ciclo, estacionalidad y residuo. Es útil cuando las oscilaciones estacionales se interpretan en la escala original; si aumentan proporcionalmente al nivel, pueden considerarse transformaciones u otras representaciones. La ecuación (2.3) presenta la descomposición con notación adaptada al importe semanal. [[FPP]]

@@eq|descomp|y_t=T_t+S_t+R_t

T representa el componente de tendencia-ciclo, S el patrón estacional y R la variación restante. El residuo no debe interpretarse automáticamente como error de captura: puede contener acontecimientos legítimos o estructura no representada. La descomposición sirve para explorar el comportamiento de la serie, sin demostrar que los componentes conservarán la misma forma en periodos futuros. [[FPP]]

La estacionalidad implica repetición asociada al calendario. Para compras semanales, un patrón anual debe examinarse con la cobertura disponible y con atención a festividades móviles. Contar con un ciclo no permite observar su repetición entre años. La incorporación de componentes estacionales dependerá de evidencia histórica y de su utilidad predictiva, no solo de la existencia de fechas comerciales relevantes. [[FPP]]

### Estacionariedad y dependencia temporal

La diferenciación transforma la serie mediante cambios entre observaciones sucesivas, como muestra la ecuación (2.4). Puede ayudar a tratar variaciones persistentes de nivel; la estabilización de varianza, en cambio, puede requerir transformaciones de escala. ADF y KPSS examinan hipótesis distintas sobre estacionariedad, y su interpretación debe considerar el tamaño de muestra y los componentes incluidos en la prueba. [[FPP]]

@@eq|diff|\Delta y_t=y_t-y_{t-1}

La autocorrelación describe asociación lineal entre observaciones separadas por un rezago. En la ecuación (2.5), k identifica la separación temporal, N el número de semanas y la barra el promedio de la serie. La función ayuda a explorar memoria temporal, sin constituir por sí sola una regla de selección del modelo. [[FPP]]

@@eq|acf|r_k=\frac{\sum_{t=k+1}^{N}(y_t-\bar{y})(y_{t-k}-\bar{y})}{\sum_{t=1}^{N}(y_t-\bar{y})^2}

La autocorrelación parcial y las pruebas de dependencia conjunta pueden complementar el diagnóstico. Las decisiones sobre rezagos deben respetar el origen temporal: analizar toda la serie para escoger características y luego evaluar sobre una parte de ella puede incorporar información de los periodos reservados. En la evaluación propuesta, los diagnósticos que determinen ajustes se restringirán al historial disponible. [[FPP]]

### Intermitencia y valores extremos

Cuando existen periodos con valor cero, resulta útil distinguir tamaño de los eventos positivos y tiempo entre eventos. El método de Croston mantiene estimaciones suavizadas de ambas cantidades y obtiene una tasa por periodo mediante su cociente, representado en la ecuación (2.6). Su traslado de demanda a compras monetarias deberá justificarse por el patrón observado. [[FPP]]

@@eq|croston|\hat{y}_{t+h|t}=\frac{\hat{z}_t}{\hat{a}_t}

La estimación z corresponde al tamaño de los eventos positivos y a al intervalo entre ellos. El procedimiento es una alternativa de referencia para intermitencia, no una garantía de superioridad. Los picos también deberán distinguirse entre errores de registro y compras extraordinarias; eliminarlos por su magnitud podría retirar información legítima del proceso que se desea pronosticar. [[FPP; KUHN]]

## Métodos estadísticos y de aprendizaje automático

### Referencias simples

Una referencia establece qué precisión puede obtenerse con una regla reproducible. El método ingenuo conserva el último valor conocido para los horizontes futuros, como muestra la ecuación (2.7). Una referencia estacional utiliza el periodo comparable de un ciclo anterior cuando existe historial suficiente. Ninguna de estas reglas representa por sí misma el juicio del propietario. [[FPP]]

@@eq|naive|\hat{y}_{t+h|t}=y_t

La utilidad de estas referencias es contextualizar el error: una arquitectura compleja puede reducir el error de entrenamiento sin mejorar el de semanas futuras. El estudio deberá comparar al híbrido con referencias previamente definidas para el importe y para la composición, de modo que la mejora se mida respecto de alternativas pertinentes. [[FPP]]

### Suavizamiento exponencial y ARIMA

El suavizamiento exponencial simple actualiza una estimación del nivel mediante una combinación de la observación reciente y el nivel previo. En la ecuación (2.8), alfa controla el peso de la información reciente y toma valores entre cero y uno. Su pronóstico no incorpora por sí mismo tendencia o estacionalidad, por lo que funciona como una representación básica. [[FPP]]

@@eq|ses|\ell_t=\alpha y_t+(1-\alpha)\ell_{t-1},\quad \hat{y}_{t+h|t}=\ell_t

Los modelos de suavizamiento con tendencia y estacionalidad amplían esta representación. Su pertinencia dependerá de la estructura temporal y de la cantidad de observaciones. No será suficiente seleccionar una variante más compleja: deberá verificarse si sus componentes ayudan a estimar las semanas reservadas para evaluación. [[FPP]]

Un ARIMA combina términos autorregresivos, diferenciación y medias móviles de innovaciones. La ecuación (2.9) usa el operador de rezago B, de modo que B aplicado a y en t devuelve el valor anterior. Los polinomios phi y theta representan los órdenes autorregresivo y de medias móviles; d es el orden de diferenciación y épsilon la innovación. [[FPP]]

@@eq|arima|\phi(B)(1-B)^d y_t=c+\theta(B)\varepsilon_t

El componente de medias móviles de ARIMA opera sobre innovaciones y no equivale a promediar compras de semanas anteriores. Las variantes estacionales añaden operadores a una periodicidad definida. La selección debe considerar longitud del historial y diagnóstico de residuos; los modelos estadísticos no son inadecuados por definición ante una microempresa. [[FPP]]

### Bosques aleatorios y potenciación de gradiente

Random Forest combina árboles construidos con aleatoriedad en muestras y predictores. En regresión, la salida es el promedio de las predicciones, representado en la ecuación (2.10). B es el número de árboles, T identifica cada árbol y x reúne los predictores disponibles. La agregación busca reducir variabilidad respecto de un árbol individual. [[RF]]

@@eq|rf|\hat{f}(x)=\frac{1}{B}\sum_{b=1}^{B}T_b(x)

Los árboles permiten representar interacciones y relaciones no lineales. Para series semanales necesitan entradas temporales adecuadas, como rezagos y calendario; no deducen automáticamente qué información estará disponible en el futuro. Su comportamiento depende de profundidad, tamaño de nodos y diversidad de árboles, y no puede describirse como inmunidad a errores de captura o datos faltantes. [[RF]]

La potenciación de gradiente construye una función de manera aditiva. La ecuación (2.11) expresa una actualización con un aprendiz base g, un coeficiente rho y una tasa de aprendizaje nu. La dirección de actualización depende del gradiente negativo de la pérdida; con pérdida cuadrática se relaciona con los residuales. [[GB]]

@@eq|gb|F_m(x)=F_{m-1}(x)+\nu\rho_m g_m(x)

La tasa de aprendizaje y el número de etapas controlan la magnitud de la adaptación. Estas técnicas pueden aprovechar interacciones entre calendario e historial, pero requieren ajuste temporal. Evaluar más etapas sobre los mismos datos finales usados para reportar precisión introduciría optimismo en la comparación. [[GB]]

### Redes neuronales y alcance de los comparadores

Una red autorregresiva aproxima una relación entre rezagos mediante una función no lineal. Las arquitecturas recurrentes añaden estados internos y mecanismos de memoria, pero también parámetros y decisiones de ajuste. En escenarios con pocas observaciones, su inclusión debe justificarse por información suficiente y comparación con métodos más sencillos; no define por sí misma el carácter híbrido del estudio. [[FPP]]

La selección de familias tendrá sentido si permite examinar representaciones distintas del mismo objetivo. Un comparador adicional deberá aportar una pregunta pertinente, como la utilidad de no linealidad o memoria, y no solo ampliar una lista de algoritmos. La configuración final pertenecerá a metodología y se fijará mediante información anterior a las semanas de evaluación. [[KUHN]]

## Fundamentos de integración del modelo híbrido

### Combinación de pronósticos

La combinación de pronósticos parte de que métodos distintos pueden contener información complementaria. Para dos modelos, la ecuación (2.12) pondera un pronóstico estadístico y uno de aprendizaje automático. La notación adapta el principio de combinación al caso; el peso w determina la contribución del primero. Restringirlo entre cero y uno produce una combinación convexa. [[BG]]

@@eq|hybrid|\hat{y}_{t+h|t}^{H}=w\hat{y}_{t+h|t}^{E}+(1-w)\hat{y}_{t+h|t}^{A}

Los superíndices H, E y A identifican híbrido, estadístico y aprendizaje automático. Bajo errores insesgados con varianzas finitas, la varianza del error combinado depende de las varianzas individuales y de su covarianza. La ecuación (2.13) explica por qué el grado de dependencia entre errores importa para la combinación. [[BG]]

@@eq|variance|\sigma_H^2=w^2\sigma_E^2+(1-w)^2\sigma_A^2+2w(1-w)\sigma_{EA}

Cuando los errores se parecen mucho, combinar puede aportar poco. Si el denominador es positivo, el peso que minimiza esa varianza sin imponer la restricción convexa se expresa en la ecuación (2.14). Su uso exige estimar varianzas y covarianza sin información futura; la estimación puede ser inestable con pocos errores disponibles. [[BG]]

@@eq|weight|w^{*}=\frac{\sigma_A^2-\sigma_{EA}}{\sigma_E^2+\sigma_A^2-2\sigma_{EA}}

La combinación simple también debe considerarse como referencia, pues estimar pesos no garantiza mejorar un promedio. En el estudio propuesto, el interés será contrastar si integrar representaciones distintas produce menores errores. La evaluación deberá distinguir esa combinación de la mera selección del algoritmo ganador. [[FPP]]

### Integración mediante componentes

Otra estrategia híbrida representa la serie como suma de componentes lineal y no lineal. Un antecedente integra ARIMA y una red neuronal para modelar estructura complementaria. La ecuación (2.15) resume esa formulación; sus componentes no son observables independientes, sino representaciones estimadas mediante un procedimiento de modelado. [[ZHANG]]

@@eq|residual|y_t=L_t+N_t,\quad \hat{y}_{t+h|t}=\hat{L}_{t+h|t}+\hat{N}_{t+h|t}

Si el segundo componente se entrena con errores del primero, debe cuidarse cómo se generan esos errores. Los residuales de entrenamiento pueden presentar un comportamiento distinto del error predictivo. Por ello, cualquier adaptación a Cup&Cake deberá construir y ajustar sus componentes respetando el orden temporal y evaluar la suma sobre semanas no utilizadas para configurar el procedimiento. [[ZHANG; FPP]]

Estas alternativas ofrecen mecanismos plausibles para H1, sin anticipar cuál resultará más preciso. Una combinación puede fallar si los componentes comparten errores, si los pesos se estiman con poca información o si la estructura cambia. La selección de una arquitectura concreta requerirá especificar qué componentes se integran y cómo se contrastará el conjunto. [[FPP]]

## Distribución porcentual y coherencia de las asignaciones

### Participaciones como datos composicionales

Las participaciones describen partes de un total y están sujetas a una restricción de suma. Por ello, no se interpretan como variables completamente independientes: aumentar una participación requiere disminuir alguna otra. La ecuación (2.16) adapta la representación composicional a importes no negativos de compras, incluyendo la condición de total positivo. [[AITCH]]

@@eq|shares|p_{j,t}=\frac{b_{j,t}}{y_t},\quad p_{j,t}\geq0,\quad \sum_{j=1}^{J}p_{j,t}=1,\quad y_t>0

Las proporciones se expresan entre cero y uno; su multiplicación por cien produce porcentajes. Si el total observado es cero, las participaciones no quedan definidas por el cociente. Una regla de tratamiento deberá distinguir ese caso de una participación cero dentro de una semana con compras. Las transformaciones logarítmicas requieren además componentes estrictamente positivos. [[AITCH]]

### Desagregación del pronóstico total

El enfoque descendente pronostica un agregado y lo distribuye mediante proporciones. La ecuación (2.17) adapta esa relación a importes por insumo: cada asignación es el producto del total pronosticado y la participación estimada para el mismo horizonte. Las proporciones deben cumplir las restricciones de suma y no negatividad. [[FPP]]

@@eq|allocation|\hat{b}_{j,t+h|t}=\hat{p}_{j,t+h|t}\hat{y}_{t+h|t}

El procedimiento preserva la suma cuando todas las categorías están representadas. Esa coherencia es aritmética y no demuestra precisión: un total correcto puede repartirse incorrectamente. Por esa razón, la evaluación deberá revisar tanto el importe agregado como las participaciones y, cuando resulte pertinente, las asignaciones monetarias resultantes. [[HIER]]

Como referencia, el promedio de proporciones históricas asigna a cada categoría su participación media en las semanas de entrenamiento con total positivo. La ecuación (2.18) adapta el promedio histórico de proporciones a ese conjunto válido V, cuyo tamaño es n. No es equivalente al cociente de sumas, que otorga más peso a las semanas de mayor importe. [[FPP]]

@@eq|histshare|\bar{p}_{j}=\frac{1}{n}\sum_{t\in V}\frac{b_{j,t}}{y_t}

Una distribución histórica fija puede ser insuficiente si la mezcla cambia. Las proporciones pronosticadas ofrecen una alternativa, aunque requieren información y evaluación propias. Debe mantenerse el mismo conjunto de categorías a lo largo del contraste o documentar sus cambios. Este principio permite diferenciar la mejora de la composición de la mejora del total. [[FPP]]

### Representación relativa de las participaciones

El análisis composicional utiliza cocientes para representar información relativa. La transformación logarítmica de una participación respecto de una categoría de referencia aparece en la ecuación (2.19). Su utilidad es mostrar que la información relevante puede expresarse como relación entre partes, en lugar de tratar porcentajes como respuestas independientes sin restricciones. [[AITCH]]

@@eq|alr|z_{j,t}=\log\left(\frac{p_{j,t}}{p_{J,t}}\right),\quad j=1,\ldots,J-1

Esta transformación es una alternativa teórica y no obliga a seleccionarla para el estudio. Los ceros requieren un tratamiento explícito que no distorsione la composición; no deberán sustituirse de manera arbitraria solo para permitir un logaritmo. Una estrategia más simple también podrá ser pertinente si conserva coherencia y obtiene precisión comparable fuera de muestra. [[AITCH]]

## Datos limitados e ingeniería de características

### Complejidad y capacidad de generalización

La cantidad de observaciones debe valorarse en relación con la complejidad del modelo y la dependencia de los datos. Para pérdida cuadrática, la descomposición sesgo–varianza expresa el error esperado como suma de sesgo al cuadrado, varianza del estimador y ruido irreducible. La ecuación (2.20) resume esa relación para una entrada x. [[ESL]]

@@eq|biasvar|E[(Y-\hat{f}(x))^2]=\mathrm{Sesgo}^2[\hat{f}(x)]+\mathrm{Var}[\hat{f}(x)]+\sigma^2

Un ajuste flexible puede reducir error de entrenamiento y ser sensible a cambios de muestra. Regularizar busca controlar esa sensibilidad, aunque no elimina toda incertidumbre. La estabilidad deberá examinarse con datos posteriores, especialmente cuando la agregación semanal reduzca el número de observaciones disponibles para estimar parámetros. [[ESL]]

### Penalizaciones y selección de variables

Ridge añade una penalización cuadrática sobre coeficientes y Lasso una penalización absoluta. Las ecuaciones (2.21) y (2.22) presentan sus objetivos en notación común: SSE es la suma de errores cuadrados y beta reúne los coeficientes, excluyendo el intercepto de la penalización. Lambda controla la intensidad de contracción. [[ESL; TIB]]

@@eq|ridge|\hat{\beta}^{R}=\arg\min_{\beta}\left(\mathrm{SSE}(\beta)+\lambda\sum_{j=1}^{K}\beta_j^2\right)

@@eq|lasso|\hat{\beta}^{L}=\arg\min_{\beta}\left(\mathrm{SSE}(\beta)+\lambda\sum_{j=1}^{K}|\beta_j|\right)

Lasso puede llevar coeficientes a cero y producir una representación más reducida. Eso no demuestra que una variable carezca de importancia económica; su selección depende de los datos, la penalización y los demás predictores. La comparación deberá ajustar lambda dentro de entrenamiento y considerar el escalado, pues las unidades de las variables influyen en la penalización. [[TIB]]

### Predictores temporales y calendario

Los rezagos y resúmenes móviles expresan información histórica en una forma utilizable por algoritmos de regresión. Deben construirse únicamente con observaciones conocidas en cada origen. Imputación, escalado y selección de variables forman parte del procedimiento de entrenamiento y no deben estimarse con las semanas finales de evaluación. [[KUHN]]

Las bases armónicas representan ciclos mediante funciones seno y coseno. La ecuación (2.23) presenta un par de términos con periodicidad m y armónico k. La codificación permite representar continuidad entre el final y el inicio de un ciclo, sin asignar una distancia artificialmente grande a posiciones próximas. [[FPP]]

@@eq|fourier|s_{k,t}=\sin\left(\frac{2\pi kt}{m}\right),\quad c_{k,t}=\cos\left(\frac{2\pi kt}{m}\right)

La periodicidad debe corresponder al índice temporal. En semanas completas, el número de lunes o domingos no varía entre observaciones; un calendario diario tendrá que convertirse en información semanal pertinente, como presencia o proximidad de festividades. El número de armónicos y las interacciones deberá ser compatible con el tamaño del historial. [[FPP]]

### Disponibilidad de variables exógenas

Las variables de calendario pueden conocerse anticipadamente, mientras que clima observado, ventas futuras o indicadores publicados con retraso pueden ser desconocidos al pronosticar. Un modelo con regresores necesita sus valores futuros o un procedimiento explícito para estimarlos. Utilizar realizaciones futuras como si estuvieran disponibles produciría una evaluación que no representa el uso previsto. [[FPP]]

En horizontes de varias semanas, tampoco puede incorporarse como rezago una compra futura todavía no observada. La metodología deberá indicar si se generan pronósticos directos por horizonte o se utilizan predicciones recursivas. El análisis de variables exógenas podrá complementar el contraste principal, sin constituir una segunda hipótesis independiente. [[FPP]]

## Evaluación temporal y métricas de precisión

### Origen del pronóstico y ventana de entrenamiento

La evaluación fuera de muestra compara pronósticos con observaciones que no participaron en su ajuste. Una ventana deslizante mantiene un historial de tamaño fijo y actualiza su posición; una ventana expansiva conserva el historial previo y añade observaciones. La elección afecta recencia, tamaño de muestra y cantidad de evaluaciones posibles. [[TASH]]

La comparación requiere suficientes orígenes y resultados por horizonte, evitando que un único periodo determine la conclusión. Los modelos deberán enfrentar las mismas semanas y condiciones de información. El error de la ecuación (2.24) distingue el valor observado en t+h del pronóstico emitido en t. [[TASH; FPP]]

@@eq|error|e_{t,h}=y_{t+h}-\hat{y}_{t+h|t}

El ajuste de configuraciones deberá separarse de su evaluación final. Si los pesos híbridos, las variables o el modelo se eligen observando los resultados finales, esos resultados dejan de ser una estimación independiente de la selección. El protocolo temporal permitirá comparar alternativas sin dar por comprobada la hipótesis antes de obtener evidencia. [[FPP]]

### Error monetario del importe total

MAE y RMSE resumen el error en las unidades de la respuesta. MAE promedia magnitudes absolutas; RMSE extrae la raíz del promedio de cuadrados y es más sensible a errores grandes. Las ecuaciones (2.25) y (2.26) se expresan para un horizonte h y un conjunto O de n orígenes evaluados. [[FPP]]

@@eq|mae|\mathrm{MAE}_h=\frac{1}{n}\sum_{t\in O}|e_{t,h}|

@@eq|rmse|\mathrm{RMSE}_h=\sqrt{\frac{1}{n}\sum_{t\in O}e_{t,h}^2}

Las medidas se interpretarán en moneda y deberán reportarse por horizonte. Menor RMSE significa menor media de errores cuadrados, no necesariamente menor cantidad de errores extremos. Para dar transparencia a H1, el criterio principal de comparación deberá fijarse antes del análisis final, manteniendo las demás métricas como información complementaria. [[FPP]]

### Escalamiento y límites de errores porcentuales

MASE divide el error absoluto por una escala obtenida de diferencias históricas de entrenamiento. La ecuación (2.27) muestra su forma para una partición con N observaciones de entrenamiento, n de prueba y rezago de referencia m. Permite comparar escalas sin dividir cada error por la compra observada de su semana. [[HK]]

@@eq|mase|\mathrm{MASE}=\frac{\frac{1}{n}\sum_{i=1}^{n}|e_i|}{\frac{1}{N-m}\sum_{t=m+1}^{N}|y_t-y_{t-m}|}

El denominador debe ser positivo y calcularse sin datos de prueba. Al desplazar la ventana, la regla de escalamiento deberá mantenerse explícita; un historial constante puede hacer indefinida la medida. MASE complementa el contraste directo con referencias y no reemplaza la interpretación de pesos monetarios. [[HK]]

MAPE divide cada error por el valor observado. Aunque produce porcentajes, resulta indefinido con ceros e inestable con importes pequeños. Por ello, no se utilizará como criterio central de contraste de una serie con esas condiciones. Su eventual reporte deberá identificar los casos válidos sin ocultar las semanas excluidas. [[HK]]

### Error de participaciones y evaluación conjunta

La precisión de la composición debe medirse separadamente. La ecuación (2.28) adapta MAE a participaciones entre cero y uno y multiplica por cien para expresar el error en puntos porcentuales. O con subíndice positivo representa los orígenes cuyo total observado en el horizonte es positivo y n con el mismo subíndice es su cantidad. Esta adaptación no se presenta como una métrica composicional nueva atribuida a los autores. [[HK; AITCH]]

@@eq|maepp|\mathrm{MAE}_{p,h}=\frac{100}{n_{+}J}\sum_{t\in O_{+}}\sum_{j=1}^{J}|p_{j,t+h}-\hat{p}_{j,t+h|t}|

La ponderación uniforme ofrece igual importancia a las categorías. Si se adoptan otros pesos, deberán justificarse y fijarse antes de evaluar. Además de la medida agregada, revisar errores por insumo permite identificar si una mejora promedio oculta deterioro en categorías concretas. Se informarán por separado las semanas cuyo total cero impida definir una composición observada. [[FPP]]

El contraste de H1 tendrá dos componentes: precisión del importe total y de su distribución. Mejorar solo uno constituirá evidencia parcial respecto de su formulación conjunta. La comparación no se resolverá escogiendo retrospectivamente el horizonte favorable ni interpretando una diferencia de error como efecto financiero. La metodología deberá precisar el criterio de decisión y el tratamiento de incertidumbre de las diferencias observadas. [[SHM; TASH]]

## Inteligencia de negocios y comunicación del pronóstico

### Presentación del presupuesto y su incertidumbre

Un tablero puede reunir el total esperado, las participaciones y las asignaciones monetarias para que el responsable revise el presupuesto. La presentación deberá identificar origen, horizonte, unidades y referencia comparativa. Esta función corresponde al soporte de decisiones; no transforma automáticamente una asignación monetaria en una orden de compra. [[POWER]]

Los intervalos de predicción comunican incertidumbre adicional al valor puntual. Bajo una aproximación normal de los errores, la ecuación (2.29) utiliza un cuantil z y una estimación de la desviación del error correspondiente al horizonte. Esa aproximación depende de supuestos que deberán verificarse antes de su uso. [[FPP]]

@@eq|interval|\hat{y}_{t+h|t}\pm z_{1-\alpha/2}\hat{\sigma}_h

Alfa expresa la probabilidad nominal fuera del intervalo y sigma la escala de incertidumbre predictiva. No debe confundirse este intervalo con uno de confianza para una media estimada ni calcularse su amplitud sumando errores sin considerar el horizonte. En series asimétricas o con ceros, otras aproximaciones podrían resultar más pertinentes. [[FPP]]

### Adopción y límites operativos

La viabilidad de una herramienta depende también de integración, mantenimiento, competencias y recursos. La digitalización de empresas pequeñas enfrenta barreras diversas, por lo que una solución debe adecuarse a sus capacidades y no justificarse únicamente por sofisticación. El tablero propuesto buscará facilitar interpretación y trazabilidad; no se asumirá que su disponibilidad demuestra adopción efectiva. [[OECD]]

La evaluación de costos de implementación y beneficios organizacionales es distinta de medir precisión. En consecuencia, la reducción de MAE o RMSE no se denominará retorno de inversión. La comunicación de resultados deberá mantener visible esa diferencia para que el responsable pueda utilizar el pronóstico junto con la información operativa que posea. [[POWER]]

## Síntesis de fundamentos y relación con la hipótesis

Los fundamentos revisados permiten plantear una integración de métodos que representen señales diferentes y una desagregación que conserve la relación entre total e insumos. La combinación ofrece una razón teórica para esperar mejoras, mientras que la estimación de pesos y la dependencia entre errores explican por qué esa mejora no está asegurada. [[FPP]]

La composición añade un problema propio: conservar proporciones válidas y anticipar su variación. Por tanto, el procedimiento deberá evaluar el importe y las participaciones frente a sus respectivas referencias. La coherencia de suma es una condición de la representación, mientras que la precisión requiere evidencia de semanas posteriores no utilizadas en el ajuste. [[HIER; FPP]]

La investigación se desarrollará como una evaluación predictiva del presupuesto semanal de abastecimiento. El capítulo sustenta la elección de variables, métodos y criterios de contraste, sin anticipar resultados de Cup&Cake. H1 podrá recibir respaldo completo, parcial o no recibirlo según el comportamiento de sus dos componentes bajo el protocolo temporal definido. [[SHM]]
