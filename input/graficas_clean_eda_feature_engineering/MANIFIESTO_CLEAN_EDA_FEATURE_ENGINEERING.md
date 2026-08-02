# Manifiesto académico de gráficas: limpieza, EDA e ingeniería de características

**Códigos metodológicos ilustrados:** `01_clean_eda.py` y `02_feature_engineering_profesional.py`  
**Fecha de generación:** 2026-08-02T10:08:20.504951-06:00  
**Número de figuras catalogadas:** 38

## Propósito metodológico

Este conjunto de figuras documenta la transformación de fuentes heterogéneas en un panel diario, numérico y monetariamente comparable, y posteriormente la construcción de variables temporales, exógenas, rezagadas, móviles y derivadas para el modelado predictivo. Las gráficas se organizan desde la trazabilidad de las fuentes hasta la auditoría del dataset maestro. Cada figura incluye su fundamento matemático, criterio de lectura, limitaciones y ubicación sugerida dentro de la tesis.

## Ecuaciones de transformación principales

1. **Factor de actualización:** $F_t=\frac{INPC_{base}}{INPC_t}$.
2. **Conversión a moneda constante:** $Valor^{real}_t=Valor^{nominal}_t\times F_t$.
3. **Agregación diaria:** $X_d=\sum_{i\in d}x_i$.
4. **Media móvil descriptiva:** $MA_{w,t}=\frac{1}{w}\sum_{i=0}^{w-1}y_{t-i}$.
5. **Participación por categoría:** $p_k=\frac{X_k}{\sum_jX_j}\times100$.
6. **Correlación de Pearson:** $r_{xy}=\frac{\sum_i(x_i-\bar{x})(y_i-\bar{y})}{\sqrt{\sum_i(x_i-\bar{x})^2\sum_i(y_i-\bar{y})^2}}$.

7. **Rezago:** $x_t^{(k)}=y_{t-k}$.
8. **Ventana móvil sin fuga:** $MA_{w,t}=rac{1}{w}\sum_{i=1}^{w}y_{t-i}$.
9. **Codificación cíclica:** $z_{sin}=\sin(2\pi x/P)$ y $z_{cos}=\cos(2\pi x/P)$.

## Catálogo de figuras

### Figura 1. Cobertura temporal de las fuentes

- **Estado:** generada
- **Archivo:** `01_cobertura_temporal_fuentes.png`
- **Fuente y hoja:** `Seis archivos generados por 01_clean_eda.py` / `Varias`
- **Variables:** fecha y número de registros
- **Objetivo académico:** Demostrar que las fuentes poseen cobertura temporal compatible antes de la integración.
- **Interpretación:** Las barras muestran que las series convergen en el intervalo analítico; el número al final indica registros disponibles.
- **Criterio de lectura:** La intersección temporal define el dominio válido del dataset maestro.
- **Fundamento o ecuación:** D = \bigcap_{j=1}^{m}[t_{inicio,j},t_{fin,j}]
- **Ubicación sugerida:** Sección 4.2, construcción del dataset maestro y trazabilidad de fuentes.
- **Limitaciones:** La cantidad de registros no implica igual granularidad: INPC y temperatura pueden ser mensuales, mientras ventas y compras son transaccionales.

### Figura 2. Evolución del INPC

- **Estado:** generada
- **Archivo:** `02_evolucion_inpc.png`
- **Fuente y hoja:** `inpc_limpio.xlsx` / `limpio`
- **Variables:** fecha, inpc_valor
- **Objetivo académico:** Documentar la variable macroeconómica empleada para eliminar el efecto de inflación.
- **Interpretación:** Una trayectoria ascendente implica que una unidad monetaria histórica no es directamente comparable con una unidad del periodo base.
- **Criterio de lectura:** El índice se usa como denominador del factor de actualización.
- **Fundamento o ecuación:** F_t=\frac{INPC_{base}}{INPC_t}
- **Ubicación sugerida:** Sección de depuración monetaria y Tabla de inflación histórica.
- **Limitaciones:** El INPC mensual homogeneiza poder adquisitivo, pero no modela cambios específicos de precios de insumos de repostería.

### Figura 3. Factor de ajuste inflacionario

- **Estado:** generada
- **Archivo:** `03_factor_ajuste_inflacion.png`
- **Fuente y hoja:** `inpc_limpio.xlsx` / `limpio`
- **Variables:** fecha, factor_ajuste_a_2026_05
- **Objetivo académico:** Mostrar la magnitud de la corrección aplicada a cada importe nominal.
- **Interpretación:** El primer factor observado es 0.557; valores mayores que uno elevan importes históricos para expresarlos en moneda constante.
- **Criterio de lectura:** La línea horizontal representa el periodo base, donde nominal y real coinciden.
- **Fundamento o ecuación:** Valor^{real}_t=Valor^{nominal}_t\times F_t
- **Ubicación sugerida:** Justificación de la deflactación de ventas, compras, ganancias, descuentos y envíos.
- **Limitaciones:** El factor depende de la fecha y calidad de la serie INPC; los meses faltantes deben revisarse antes de llenar con 1.0.

### Figura 4. Temperatura promedio mensual

- **Estado:** generada
- **Archivo:** `04_temperatura_promedio_hidalgo.png`
- **Fuente y hoja:** `temperatura_hidalgo_limpia.xlsx` / `limpio`
- **Variables:** fecha, temperatura_promedio_mensual
- **Objetivo académico:** Representar una variable exógena potencialmente asociada con patrones de consumo y conservación de insumos.
- **Interpretación:** Los máximos y mínimos recurrentes permiten identificar estacionalidad climática.
- **Criterio de lectura:** La periodicidad debe interpretarse como contexto, no como causalidad directa sobre ventas.
- **Fundamento o ecuación:** \bar{T}_m=\frac{1}{n_m}\sum_{i=1}^{n_m}T_{i,m}
- **Ubicación sugerida:** Sección 4.1.2, conjuntos de datos de variables exógenas.
- **Limitaciones:** La temperatura agregada estatal puede no representar las condiciones exactas del establecimiento.

### Figura 5. Distribución del clima

- **Estado:** generada
- **Archivo:** `05_distribucion_categorias_clima.png`
- **Fuente y hoja:** `dataset_tizayuca_limpio.xlsx` / `limpio`
- **Variables:** clima
- **Objetivo académico:** Verificar la frecuencia y el balance de las categorías climáticas antes de codificarlas.
- **Interpretación:** La categoría más frecuente es 'SOLEADO'. Categorías muy escasas pueden generar variables dummy con baja variabilidad.
- **Criterio de lectura:** Las barras comparan la frecuencia absoluta de cada estado del clima.
- **Fundamento o ecuación:** p(c_k)=\frac{n(c_k)}{N}
- **Ubicación sugerida:** EDA de variables categóricas y justificación de la codificación one-hot.
- **Limitaciones:** La categoría describe condiciones registradas y puede contener simplificaciones o datos imputados.

### Figura 6. Eventos comerciales y calendáricos

- **Estado:** generada
- **Archivo:** `06_eventos_festivos_fechas_pago.png`
- **Fuente y hoja:** `dataset_tizayuca_limpio.xlsx` / `limpio`
- **Variables:** es_festivo_mexicano, es_fecha_pago
- **Objetivo académico:** Mostrar la distribución temporal de festivos y fechas de pago que podrían modificar la demanda.
- **Interpretación:** Los picos indican meses con mayor concentración de eventos; sirven para justificar variables de proximidad y ventanas de eventos.
- **Criterio de lectura:** La coincidencia temporal con ventas debe analizarse después, sin asumir causalidad.
- **Fundamento o ecuación:** E_{m,k}=\sum_{t\in m}I(evento_{t,k}=1)
- **Ubicación sugerida:** Ingeniería de características: festivos, quincenas y proximidad a eventos.
- **Limitaciones:** El indicador binario mide presencia, no intensidad económica del evento.

### Figura 7. Serie diaria de ventas

- **Estado:** generada
- **Archivo:** `07_serie_diaria_ventas_reales.png`
- **Fuente y hoja:** `ventas_limpias.xlsx` / `diario_completo`
- **Variables:** fecha, ventas_importe_real_2026_05
- **Objetivo académico:** Visualizar nivel, variabilidad, picos, ceros y tendencia de la variable financiera principal.
- **Interpretación:** La línea fina conserva la volatilidad diaria; la media móvil revela cambios persistentes del nivel de ventas.
- **Criterio de lectura:** Los picos no deben eliminarse automáticamente: pueden corresponder a eventos reales o pedidos extraordinarios.
- **Fundamento o ecuación:** MA_{30,t}=\frac{1}{30}\sum_{i=0}^{29}y_{t-i}
- **Ubicación sugerida:** Sección 4.2.1, EDA de ventas; base para discutir no estacionariedad y volatilidad.
- **Limitaciones:** La media móvil es descriptiva y utiliza información contemporánea; no debe confundirse con una característica predictiva sin desplazamiento.

### Figura 8. Ventas nominales frente a reales

- **Estado:** generada
- **Archivo:** `08_ventas_nominales_vs_reales.png`
- **Fuente y hoja:** `ventas_limpias.xlsx` / `detalle`
- **Variables:** fecha, importe_nominal, importe_real_2026_05
- **Objetivo académico:** Evidenciar el efecto práctico de la corrección inflacionaria sobre la serie de ingresos.
- **Interpretación:** La separación promedio absoluta entre ambas series mensuales es de 1,597.44 pesos; las diferencias son mayores en periodos alejados del mes base.
- **Criterio de lectura:** La serie real es la adecuada para comparar desempeño financiero a través del tiempo.
- **Fundamento o ecuación:** Ingreso^{real}_{t}=Ingreso^{nominal}_{t}\frac{INPC_{base}}{INPC_t}
- **Ubicación sugerida:** Justificación de la variable objetivo monetaria a precios constantes.
- **Limitaciones:** Los importes reales dependen del índice general de precios y no de un deflactor específico del giro comercial.

### Figura 9. Distribución de ventas diarias

- **Estado:** generada
- **Archivo:** `09_distribucion_ventas_diarias.png`
- **Fuente y hoja:** `ventas_limpias.xlsx` / `diario_completo`
- **Variables:** ventas_importe_real_2026_05
- **Objetivo académico:** Evaluar asimetría, dispersión y presencia de días de venta extraordinaria.
- **Interpretación:** La asimetría muestral es 3.20. Una cola derecha prolongada evidencia pocos días con importes mucho mayores que el nivel habitual.
- **Criterio de lectura:** La diferencia entre media y mediana permite identificar falta de simetría.
- **Fundamento o ecuación:** g_1=\frac{\frac{1}{N}\sum(y_i-\bar y)^3}{s^3}
- **Ubicación sugerida:** Caracterización estadística de la variable objetivo de ventas.
- **Limitaciones:** Se excluyen ceros para describir la magnitud condicional de días con venta; la tasa de días sin venta se documenta por separado.

### Figura 10. Ventas por día de la semana

- **Estado:** generada
- **Archivo:** `10_ventas_por_dia_semana.png`
- **Fuente y hoja:** `ventas_limpias.xlsx` / `diario_completo`
- **Variables:** fecha, ventas_importe_real_2026_05
- **Objetivo académico:** Identificar microestacionalidad semanal y diferencias en dispersión entre días.
- **Interpretación:** El día con mayor mediana es Lun. La caja representa el 50 % central y los bigotes la dispersión sin valores extremos.
- **Criterio de lectura:** Las medianas distintas respaldan la incorporación del día de la semana y su codificación cíclica.
- **Fundamento o ecuación:** IQR=Q_{0.75}-Q_{0.25}
- **Ubicación sugerida:** EDA de estacionalidad semanal e ingeniería de características de calendario.
- **Limitaciones:** La gráfica es descriptiva; las diferencias pueden estar condicionadas por festivos, promociones o crecimiento del negocio.

### Figura 11. Mapa de calor de ventas mensuales

- **Estado:** generada
- **Archivo:** `11_mapa_calor_ventas_mes_anio.png`
- **Fuente y hoja:** `ventas_limpias.xlsx` / `diario_completo`
- **Variables:** fecha, ventas_importe_real_2026_05
- **Objetivo académico:** Comparar simultáneamente estacionalidad mensual y evolución interanual.
- **Interpretación:** Las celdas de mayor intensidad representan meses con mayor facturación real; patrones verticales repetidos sugieren estacionalidad.
- **Criterio de lectura:** Debe distinguirse entre estacionalidad y crecimiento estructural del negocio.
- **Fundamento o ecuación:** Y_{a,m}=\sum_{t\in(a,m)}y_t
- **Ubicación sugerida:** EDA temporal; figura central para discutir estacionalidad y tendencia.
- **Limitaciones:** Los años incompletos contienen menos meses y no deben compararse mediante totales anuales sin normalización.

### Figura 12. Composición de productos vendidos

- **Estado:** generada
- **Archivo:** `12_composicion_productos_vendidos.png`
- **Fuente y hoja:** `ventas_limpias.xlsx` / `detalle`
- **Variables:** pastel, galletas, otros, cupcakes
- **Objetivo académico:** Describir la estructura de la demanda por familia de producto.
- **Interpretación:** La categoría dominante representa aproximadamente 41.2% de las unidades clasificadas.
- **Criterio de lectura:** Una mezcla concentrada implica que la demanda total puede estar impulsada por una familia específica.
- **Fundamento o ecuación:** Participación_k=\frac{\sum_t q_{k,t}}{\sum_j\sum_t q_{j,t}}\times100
- **Ubicación sugerida:** Contexto del negocio y caracterización de ventas por tipo de producto.
- **Limitaciones:** Las categorías dependen de la calidad y exhaustividad del registro comercial.

### Figura 13. Margen de ganancia mensual

- **Estado:** generada
- **Archivo:** `13_margen_ganancia_mensual.png`
- **Fuente y hoja:** `ventas_limpias.xlsx` / `detalle`
- **Variables:** importe_real_2026_05, ganancia_real_2026_05
- **Objetivo académico:** Relacionar ingresos con rentabilidad y evidenciar variaciones financieras no visibles en las ventas brutas.
- **Interpretación:** Un mes puede mostrar ventas elevadas y margen reducido; por ello ingreso y ganancia no deben tratarse como equivalentes.
- **Criterio de lectura:** La línea representa la proporción de ganancia registrada respecto al importe real mensual.
- **Fundamento o ecuación:** Margen_m=\frac{Ganancia^{real}_m}{Ventas^{real}_m}\times100
- **Ubicación sugerida:** Planeación financiera y análisis de rentabilidad histórica.
- **Limitaciones:** La interpretación depende de cómo el sistema fuente define y calcula la columna Ganancia.

### Figura 14. Serie diaria de compras

- **Estado:** generada
- **Archivo:** `14_serie_diaria_compras_reales.png`
- **Fuente y hoja:** `compras_limpias.xlsx` / `pivot_diario`
- **Variables:** fecha, compras_total_real_2026_05
- **Objetivo académico:** Visualizar periodicidad, intermitencia y magnitud de los egresos por abastecimiento.
- **Interpretación:** Los periodos prolongados en cero y los picos aislados son característicos de compras intermitentes.
- **Criterio de lectura:** La intermitencia explica por qué métricas porcentuales como MAPE pueden ser inestables.
- **Fundamento o ecuación:** MA_{30,t}=\frac{1}{30}\sum_{i=0}^{29}c_{t-i}
- **Ubicación sugerida:** EDA de compras y justificación de modelos para demanda intermitente.
- **Limitaciones:** Los ceros pueden representar ausencia real de compra, no datos faltantes.

### Figura 15. Compras por clasificación

- **Estado:** generada
- **Archivo:** `15_compras_por_clasificacion.png`
- **Fuente y hoja:** `compras_limpias.xlsx` / `detalle`
- **Variables:** clasificacion, monto_real_2026_05
- **Objetivo académico:** Identificar los grupos de insumo que concentran el mayor desembolso.
- **Interpretación:** Las barras superiores representan categorías con mayor impacto financiero acumulado y potencial prioridad de pronóstico.
- **Criterio de lectura:** La clasificación debe revisarse por consistencia semántica antes de interpretar diferencias.
- **Fundamento o ecuación:** C_k=\sum_{i:clasificacion_i=k}Monto^{real}_i
- **Ubicación sugerida:** Caracterización del abastecimiento y selección de categorías operativamente relevantes.
- **Limitaciones:** Los importes no consideran necesariamente frecuencia, perecibilidad ni criticidad del insumo.

### Figura 16. Concentración del gasto por proveedor

- **Estado:** generada
- **Archivo:** `16_pareto_proveedores.png`
- **Fuente y hoja:** `compras_limpias.xlsx` / `detalle`
- **Variables:** proveedor, monto_real_2026_05
- **Objetivo académico:** Evaluar dependencia de abastecimiento y concentración financiera mediante un diagrama de Pareto.
- **Interpretación:** Los 12 proveedores mostrados concentran 93.7% del gasto total registrado.
- **Criterio de lectura:** Las barras representan gasto individual y la curva el porcentaje acumulado.
- **Fundamento o ecuación:** P_k=\frac{\sum_{j=1}^{k}C_{(j)}}{\sum_{j=1}^{J}C_j}\times100
- **Ubicación sugerida:** Análisis de proveedores, riesgo de concentración y gestión de abastecimiento.
- **Limitaciones:** El gasto histórico no mide desempeño, calidad, plazo de entrega ni posibilidad de sustitución.

### Figura 17. Unidades de medida normalizadas

- **Estado:** generada
- **Archivo:** `17_unidades_medida_normalizadas.png`
- **Fuente y hoja:** `compras_limpias.xlsx` / `detalle`
- **Variables:** unidad
- **Objetivo académico:** Evidenciar el resultado de la homologación de abreviaturas y unidades de compra.
- **Interpretación:** Una lista reducida de categorías confirma que variantes como pza, pzs y pz fueron consolidadas.
- **Criterio de lectura:** La normalización evita crear categorías artificialmente distintas para la misma unidad.
- **Fundamento o ecuación:** u^{*}=f(u),\quad f(\{pza,pzs,pz\})=pz
- **Ubicación sugerida:** Auditoría de limpieza semántica de datos de compras.
- **Limitaciones:** La homologación textual no convierte magnitudes entre unidades físicamente distintas.

### Figura 18. Ventas y compras integradas

- **Estado:** generada
- **Archivo:** `18_ventas_compras_mensuales.png`
- **Fuente y hoja:** `dataset_maestro_diario.xlsx` / `maestro`
- **Variables:** ventas_importe_real_2026_05, compras_total_real_2026_05
- **Objetivo académico:** Demostrar la integración de ingresos y egresos dentro de una misma escala temporal y monetaria.
- **Interpretación:** La separación entre ambas curvas aproxima la holgura bruta disponible, aunque no constituye flujo de efectivo completo.
- **Criterio de lectura:** Los desfases entre compra y venta pueden revelar anticipación de inventario o rezagos operativos.
- **Fundamento o ecuación:** Saldo^{operativo}_m=Ventas^{real}_m-Compras^{real}_m
- **Ubicación sugerida:** Construcción del dataset maestro y vínculo con planeación financiera.
- **Limitaciones:** No incluye todos los costos, impuestos, cuentas por cobrar ni momento exacto de pago.

### Figura 19. Saldo operativo mensual aproximado

- **Estado:** generada
- **Archivo:** `19_saldo_operativo_mensual.png`
- **Fuente y hoja:** `dataset_maestro_diario.xlsx` / `maestro`
- **Variables:** ventas_importe_real_2026_05, compras_total_real_2026_05
- **Objetivo académico:** Ilustrar la relación financiera básica entre entradas por ventas y desembolsos de compra.
- **Interpretación:** Se observan 2 meses con saldo negativo bajo esta aproximación; deben investigarse como posibles periodos de acumulación de inventario o baja demanda.
- **Criterio de lectura:** Las barras bajo cero indican que las compras superaron las ventas del mes.
- **Fundamento o ecuación:** S_m=\sum_{t\in m}Ventas_t-\sum_{t\in m}Compras_t
- **Ubicación sugerida:** Puente entre EDA y simulación financiera.
- **Limitaciones:** No es utilidad neta ni flujo de efectivo contable; es un indicador exploratorio limitado a dos componentes.

### Figura 20. Días sin actividad

- **Estado:** generada
- **Archivo:** `20_dias_sin_actividad.png`
- **Fuente y hoja:** `dataset_maestro_diario.xlsx` / `maestro`
- **Variables:** ventas_importe_real_2026_05, compras_total_real_2026_05, ventas_registros, compras_registros
- **Objetivo académico:** Cuantificar la intermitencia de las series operativas después de completar el calendario diario.
- **Interpretación:** Un porcentaje alto de ceros indica una serie intermitente y condiciona la elección de métricas y modelos.
- **Criterio de lectura:** Cero es una observación válida cuando el calendario está completo; no debe confundirse con un dato ausente.
- **Fundamento o ecuación:** Z_x=\frac{1}{N}\sum_{t=1}^{N}I(x_t=0)\times100
- **Ubicación sugerida:** Calidad del dataset, small data e implicaciones para MAPE y modelado.
- **Limitaciones:** La validez del cero depende de que la fuente original haya sido exhaustiva en ese día.

### Figura 21. Completitud del dataset maestro

- **Estado:** generada
- **Archivo:** `21_valores_faltantes_dataset_maestro.png`
- **Fuente y hoja:** `dataset_maestro_diario.xlsx` / `maestro`
- **Variables:** todas las columnas
- **Objetivo académico:** Auditar la completitud después de uniones, codificación y relleno de fechas.
- **Interpretación:** El dataset contiene 0 celdas nulas. Barras iguales a cero documentan que la integración produjo un panel completo.
- **Criterio de lectura:** Los valores faltantes deben distinguirse de ceros operativos legítimos.
- **Fundamento o ecuación:** M_j=\frac{\sum_{t=1}^{N}I(x_{t,j}\;es\;NA)}{N}\times100
- **Ubicación sugerida:** Auditoría de calidad antes de la ingeniería de características.
- **Limitaciones:** Ausencia de nulos no garantiza corrección semántica ni ausencia de imputaciones discutibles.

### Figura 22. Correlación exploratoria del maestro

- **Estado:** generada
- **Archivo:** `22_correlacion_variables_clave_maestro.png`
- **Fuente y hoja:** `dataset_maestro_diario.xlsx` / `maestro`
- **Variables:** ventas_importe_real_2026_05, ventas_ganancia_real_2026_05, ventas_registros, compras_total_real_2026_05, compras_registros, es_festivo_mexicano, es_fecha_pago, nacimientos_indice, temperatura_promedio_mensual_hidalgo, inpc_valor_mensual
- **Objetivo académico:** Explorar relaciones lineales iniciales entre variables financieras, operativas y exógenas.
- **Interpretación:** Valores cercanos a 1 o -1 indican asociación lineal fuerte; valores cercanos a cero no descartan relaciones no lineales.
- **Criterio de lectura:** La matriz orienta análisis posteriores, pero no debe utilizarse para establecer causalidad.
- **Fundamento o ecuación:** r_{xy}=\frac{\sum_i(x_i-\bar{x})(y_i-\bar{y})}{\sqrt{\sum_i(x_i-\bar{x})^2\sum_i(y_i-\bar{y})^2}}
- **Ubicación sugerida:** Cierre del EDA y transición al diagnóstico de multicolinealidad e ingeniería de características.
- **Limitaciones:** La correlación puede estar afectada por tendencia, estacionalidad, ceros e inflación.

### Figura 23. Familias de características construidas

- **Estado:** generada
- **Archivo:** `23_familias_ingenieria_caracteristicas.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `diccionario`
- **Variables:** grupo, variable
- **Objetivo académico:** Cuantificar la expansión dimensional producida por calendario, rezagos, ventanas móviles, clima y objetivos.
- **Interpretación:** La familia dominante es 'Rezago' con 126 variables; esto evidencia que la representación histórica concentra gran parte de la dimensionalidad.
- **Criterio de lectura:** Las barras representan conteos de columnas, no importancia predictiva.
- **Fundamento o ecuación:** p_g=\frac{n_g}{\sum_{h=1}^{G}n_h}\times100
- **Ubicación sugerida:** Sección 4.2.2, descripción del resultado de la ingeniería de características.
- **Limitaciones:** Una familia numerosa puede contener redundancia y requiere diagnóstico posterior.

### Figura 24. Expansión dimensional del panel

- **Estado:** generada
- **Archivo:** `24_expansion_dimensional_feature_engineering.png`
- **Fuente y hoja:** `dataset_maestro_diario.xlsx y dataset_modelado_diario.xlsx` / `maestro / modelo`
- **Variables:** número de columnas
- **Objetivo académico:** Mostrar cuánto aumenta la representación analítica al transformar datos operativos en predictores.
- **Interpretación:** El proceso incorporó 211 columnas netas. El aumento responde a la creación sistemática de información temporal y no a nuevas observaciones.
- **Criterio de lectura:** La comparación debe leerse como enriquecimiento representacional, no como aumento del tamaño muestral.
- **Fundamento o ecuación:** p_{final}=p_{base}+p_{cal}+p_{exo}+p_{lags}+p_{roll}+p_{derivadas}
- **Ubicación sugerida:** Apertura de la sección de ingeniería de características.
- **Limitaciones:** Una relación alta entre columnas y filas incrementa el riesgo de sobreajuste.

### Figura 25. Historial mínimo y pérdida controlada de filas

- **Estado:** generada
- **Archivo:** `25_historial_minimo_y_observaciones.png`
- **Fuente y hoja:** `dataset_maestro_diario.xlsx y dataset_modelado_diario.xlsx` / `maestro / modelo`
- **Variables:** fecha y conteo de filas
- **Objetivo académico:** Documentar la eliminación de observaciones iniciales sin historial suficiente para rezagos de 28 días.
- **Interpretación:** Se eliminaron 28 filas iniciales; esta decisión garantiza que cada observación modelada disponga del mismo historial máximo.
- **Criterio de lectura:** La pérdida ocurre al inicio de la serie y no es una eliminación aleatoria.
- **Fundamento o ecuación:** N_{modelo}=N_{maestro}-L_{max},\qquad L_{max}=28
- **Ubicación sugerida:** Justificación del periodo efectivo de modelado y del tamaño muestral final.
- **Limitaciones:** Reducir filas es metodológicamente necesario, pero disminuye aún más el tamaño de una muestra pequeña.

### Figura 26. Codificación cíclica del mes

- **Estado:** generada
- **Archivo:** `26_codificacion_ciclica_mes.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** mes, mes_sin, mes_cos
- **Objetivo académico:** Demostrar que diciembre y enero permanecen próximos en el espacio transformado.
- **Interpretación:** Los doce meses se distribuyen sobre una circunferencia; la distancia geométrica conserva la continuidad del ciclo anual.
- **Criterio de lectura:** Meses consecutivos aparecen cercanos y los opuestos del año se ubican en extremos contrarios.
- **Fundamento o ecuación:** mes_{sin}=\sin\left(2\pi\frac{mes}{12}\right),\quad mes_{cos}=\cos\left(2\pi\frac{mes}{12}\right)
- **Ubicación sugerida:** Justificación matemática de la codificación de estacionalidad anual.
- **Limitaciones:** La transformación representa periodicidad, pero no prueba que exista un efecto mensual sobre la demanda.

### Figura 27. Codificación cíclica semanal

- **Estado:** generada
- **Archivo:** `27_codificacion_ciclica_dia_semana.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** dia_semana, dia_semana_sin, dia_semana_cos
- **Objetivo académico:** Representar la continuidad entre domingo y lunes evitando una discontinuidad numérica artificial.
- **Interpretación:** La estructura circular conserva la vecindad semanal y permite a los modelos aprender patrones periódicos.
- **Criterio de lectura:** La posición angular, no el número entero original, expresa la relación temporal.
- **Fundamento o ecuación:** d_{sin}=\sin\left(2\pi\frac{d}{7}\right),\quad d_{cos}=\cos\left(2\pi\frac{d}{7}\right)
- **Ubicación sugerida:** Ingeniería de variables calendáricas y microestacionalidad semanal.
- **Limitaciones:** No sustituye otros efectos de calendario como festivos, quincenas o fin de mes.

### Figura 28. Alineación de un rezago semanal

- **Estado:** generada
- **Archivo:** `28_alineacion_rezago_7_dias.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** target_ventas_importe_real_2026_05, ventas_importe_real_2026_05_lag7
- **Objetivo académico:** Ilustrar cómo una observación histórica se desplaza para convertirse en predictor disponible.
- **Interpretación:** La segunda curva reproduce el comportamiento de la serie con siete días de desplazamiento; en la fecha t contiene el valor conocido en t−7.
- **Criterio de lectura:** Una coincidencia visual recurrente sugiere persistencia semanal, pero debe confirmarse fuera de muestra.
- **Fundamento o ecuación:** x^{(7)}_t=y_{t-7}
- **Ubicación sugerida:** Explicación visual de predictores rezagados y prevención de fuga de información.
- **Limitaciones:** La ventana de 180 días es ilustrativa y no resume toda la serie.

### Figura 29. Relación del objetivo con sus rezagos

- **Estado:** generada
- **Archivo:** `29_correlacion_objetivo_rezagos.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** target de ventas y lag1, lag2, lag3, lag7, lag14, lag28
- **Objetivo académico:** Comparar la memoria lineal de corto, mediano y ciclo semanal/mensual aproximado.
- **Interpretación:** El rezago con mayor asociación absoluta es 1 días, con r=0.089.
- **Criterio de lectura:** Barras altas sugieren mayor persistencia lineal, no necesariamente mayor importancia multivariada.
- **Fundamento o ecuación:** r_k=Corr(y_t,y_{t-k})
- **Ubicación sugerida:** Justificación empírica de las longitudes de rezago elegidas.
- **Limitaciones:** La correlación puede estar influida por tendencia, estacionalidad y exceso de ceros.

### Figura 30. Ventanas móviles multiescala

- **Estado:** generada
- **Archivo:** `30_comparacion_ventanas_moviles.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** target_ventas_importe_real_2026_05, ventas_importe_real_2026_05_roll7_mean, ventas_importe_real_2026_05_roll14_mean, ventas_importe_real_2026_05_roll28_mean
- **Objetivo académico:** Mostrar el compromiso entre sensibilidad y suavizado al ampliar la ventana histórica.
- **Interpretación:** La ventana de 7 días responde con rapidez; la de 28 días ofrece una tendencia más estable pero reacciona con mayor retraso.
- **Criterio de lectura:** Las curvas fueron calculadas con información anterior al día de predicción.
- **Fundamento o ecuación:** \bar y^{(w)}_t=\frac{1}{w}\sum_{i=1}^{w}y_{t-i},\quad w\in\{7,14,28\}
- **Ubicación sugerida:** Justificación de estadísticas móviles para captar nivel reciente y tendencia.
- **Limitaciones:** El suavizado puede ocultar picos comercialmente relevantes.

### Figura 31. Estadísticos móviles de 28 días

- **Estado:** generada
- **Archivo:** `31_estadisticos_moviles_28_dias.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** ventas_importe_real_2026_05_roll28_mean, ventas_importe_real_2026_05_roll28_std, ventas_importe_real_2026_05_roll28_sum
- **Objetivo académico:** Distinguir tres propiedades históricas: nivel promedio, variabilidad y volumen acumulado.
- **Interpretación:** La media representa nivel local; la desviación mide inestabilidad; la suma expresa volumen del periodo.
- **Criterio de lectura:** Cada panel utiliza la misma ventana, pero responde a una propiedad estadística distinta.
- **Fundamento o ecuación:** \mu_{w,t}=\frac{1}{w}\sum y_{t-i},\quad s_{w,t}=\sqrt{\frac{1}{w-1}\sum(y_{t-i}-\mu_{w,t})^2},\quad S_{w,t}=\sum y_{t-i}
- **Ubicación sugerida:** Descripción académica de ventanas móviles múltiples.
- **Limitaciones:** Media y suma pueden resultar casi redundantes si la ventana es fija.

### Figura 32. Proximidad a eventos comerciales

- **Estado:** generada
- **Archivo:** `32_proximidad_fechas_pago.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** es_fecha_pago, dias_desde_pago, dias_hasta_pago
- **Objetivo académico:** Mostrar cómo una bandera binaria se transforma en distancias temporales más informativas.
- **Interpretación:** Las trayectorias en forma de diente de sierra miden recencia y anticipación; los marcadores identifican el evento.
- **Criterio de lectura:** La distancia permite diferenciar días previos y posteriores aunque ambos tengan bandera cero.
- **Fundamento o ecuación:** d^-_t=t-\max\{s<t:I_s=1\},\qquad d^+_t=\min\{s>t:I_s=1\}-t
- **Ubicación sugerida:** Ingeniería de características de festivos, quincenas y eventos.
- **Limitaciones:** La variable indica cercanía temporal, no intensidad del efecto comercial.

### Figura 33. Ventanas históricas de eventos

- **Estado:** generada
- **Archivo:** `33_ventanas_eventos_7_30_dias.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** festivos_7d, festivos_30d, pagos_7d, pagos_30d
- **Objetivo académico:** Representar la densidad reciente de festivos y fechas de pago en distintos horizontes.
- **Interpretación:** Una ventana corta captura concentración inmediata; una ventana larga resume el contexto mensual reciente.
- **Criterio de lectura:** El desplazamiento de un día impide incorporar el evento del día objetivo como historia ya observada.
- **Fundamento o ecuación:** E^{(w)}_t=\sum_{i=1}^{w}I_{t-i}
- **Ubicación sugerida:** Justificación de acumuladores de eventos y control de fuga temporal.
- **Limitaciones:** Eventos distintos reciben el mismo peso dentro de la ventana.

### Figura 34. Recencia de actividad

- **Estado:** generada
- **Archivo:** `34_recencia_ventas_compras.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** dias_desde_ultima_venta, dias_desde_ultima_compra
- **Objetivo académico:** Cuantificar periodos de inactividad y comportamiento intermitente de ventas y compras.
- **Interpretación:** Los incrementos continuos representan rachas sin operación; el retorno a valores bajos ocurre después de una nueva actividad.
- **Criterio de lectura:** La recencia resume información diferente al importe o al número de operaciones.
- **Fundamento o ecuación:** R_t=t-\max\{s<t:x_s>0\}
- **Ubicación sugerida:** Variables derivadas para small data y series intermitentes.
- **Limitaciones:** Al inicio de la serie la recencia depende del tratamiento adoptado cuando no existe evento previo.

### Figura 35. Indicadores derivados de estabilidad financiera

- **Estado:** generada
- **Archivo:** `35_indicadores_financieros_derivados_7d.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** ventas_vs_compras_ratio_7d, ventas_minus_compras_7d
- **Objetivo académico:** Integrar ventas y compras recientes en medidas relativas y absolutas de equilibrio operativo.
- **Interpretación:** Una razón superior a uno y una diferencia positiva indican que el promedio reciente de ventas supera al de compras.
- **Criterio de lectura:** La razón y la diferencia responden a escalas distintas y son complementarias.
- **Fundamento o ecuación:** Q_t=\frac{\bar V^{(7)}_t}{\bar C^{(7)}_t},\qquad D_t=\bar V^{(7)}_t-\bar C^{(7)}_t
- **Ubicación sugerida:** Vínculo entre ingeniería de características y planeación financiera.
- **Limitaciones:** La razón se vuelve inestable cuando las compras promedio son cero; el código reemplaza esos casos por cero.

### Figura 36. Relación predictor histórico–objetivo

- **Estado:** generada
- **Archivo:** `36_relacion_media7_objetivo_ventas.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** ventas_importe_real_2026_05_roll7_mean, target_ventas_importe_real_2026_05
- **Objetivo académico:** Ilustrar la capacidad descriptiva de una característica histórica frente al objetivo contemporáneo.
- **Interpretación:** La correlación lineal observada es r=0.099; la dispersión alrededor de la tendencia evidencia variabilidad no explicada por un único predictor.
- **Criterio de lectura:** Cada punto es un día; la línea solo resume tendencia lineal.
- **Fundamento o ecuación:** y_t=\beta_0+\beta_1\bar y^{(7)}_t+\varepsilon_t
- **Ubicación sugerida:** Transición entre feature engineering y modelado predictivo.
- **Limitaciones:** La asociación dentro de muestra no equivale a desempeño fuera de muestra.

### Figura 37. Correlación entre objetivos y features representativos

- **Estado:** generada
- **Archivo:** `37_correlacion_features_objetivos.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** target_ventas_importe_real_2026_05, target_compras_total_real_2026_05, target_ventas_registros, target_compras_registros, ventas_importe_real_2026_05_lag1, ventas_importe_real_2026_05_lag7, ventas_importe_real_2026_05_roll7_mean, ventas_importe_real_2026_05_roll28_std, compras_total_real_2026_05_lag1, compras_total_real_2026_05_lag7, compras_total_real_2026_05_roll7_mean, dias_desde_ultima_venta, dias_desde_ultima_compra, es_fecha_pago, es_festivo_mexicano, ventas_vs_compras_ratio_7d, ventas_minus_compras_7d
- **Objetivo académico:** Examinar relaciones lineales, redundancia potencial y diferencias entre objetivos monetarios y operativos.
- **Interpretación:** Los bloques de alta correlación entre rezagos y ventanas anticipan la necesidad de selección de características y PCA.
- **Criterio de lectura:** La escala va de −1 a 1; asociaciones cercanas a cero pueden ocultar relaciones no lineales.
- **Fundamento o ecuación:** r_{jk}=Corr(x_j,x_k)
- **Ubicación sugerida:** Cierre de ingeniería de características y transición a multicolinealidad.
- **Limitaciones:** La matriz es exploratoria y no controla autocorrelación, tendencia ni múltiples comparaciones.

### Figura 38. Completitud y esparsidad del dataset modelado

- **Estado:** generada
- **Archivo:** `38_esparsidad_features_modelado.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx` / `modelo`
- **Variables:** todas las características
- **Objetivo académico:** Verificar que el tratamiento final elimina nulos e identificar variables dominadas por ceros.
- **Interpretación:** La ausencia de nulos confirma un panel numéricamente completo; porcentajes altos de cero evidencian intermitencia o categorías poco frecuentes.
- **Criterio de lectura:** Los ceros se interpretan como valores válidos únicamente cuando proceden de ausencia real de actividad.
- **Fundamento o ecuación:** Z_j=\frac{1}{N}\sum_{t=1}^{N}I(x_{t,j}=0)\times100,\qquad M_j=\frac{1}{N}\sum I(x_{t,j}=NA)\times100
- **Ubicación sugerida:** Auditoría final antes del diagnóstico dimensional y entrenamiento.
- **Limitaciones:** La completitud sintáctica no garantiza validez semántica ni utilidad predictiva.

## Secuencia narrativa recomendada para el capítulo de desarrollo

1. Iniciar con la cobertura temporal para justificar la compatibilidad de las fuentes.
2. Explicar la deflactación mediante INPC y demostrar visualmente su efecto.
3. Caracterizar variables exógenas: clima, temperatura, festivos y fechas de pago.
4. Describir ventas desde cuatro perspectivas: tiempo, distribución, estacionalidad y mezcla de productos.
5. Describir compras desde intermitencia, clasificación, proveedores y unidades normalizadas.
6. Cerrar el EDA con la integración ventas-compras, la auditoría de ceros/nulos y la correlación exploratoria.
7. Introducir la expansión dimensional y el historial mínimo requerido.
8. Explicar codificaciones cíclicas, rezagos, ventanas móviles y proximidad a eventos.
9. Presentar indicadores financieros derivados, relaciones con objetivos y auditoría final del dataset modelado.

## Nota de rigor

Las figuras son descriptivas. Ninguna asociación visual prueba causalidad ni desempeño predictivo. La capacidad de pronóstico debe establecerse posteriormente mediante partición temporal, validación Rolling-Origin y métricas fuera de muestra.