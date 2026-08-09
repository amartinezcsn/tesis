# Manifiesto académico de gráficas: limpieza, ingeniería de características, perfil dimensional, multicolinealidad, selección de características y PCA

**Códigos metodológicos ilustrados:** `01_clean_eda.py`, `02_feature_engineering_profesional.py`, `03_perfil_dataset_y_dimensiones.py`, `04_diagnostico_multicolinealidad.py` y `05_seleccion_caracteristicas_dataset_reducido.py` y `06_pca_reduccion_componentes.py`  
**Fecha de generación:** 2026-08-08T11:27:13.478251-06:00  
**Número de figuras catalogadas:** 86

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

### Figura 39. Estructura general del dataset

- **Estado:** generada
- **Archivo:** `39_estructura_general_dataset_modelado.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `resumen_general`
- **Variables:** filas, columnas, predictores, objetivos
- **Objetivo académico:** Presentar simultáneamente el tamaño muestral y la complejidad dimensional del panel de modelado.
- **Interpretación:** El dataset contiene 1,584 observaciones y 271 predictores; la razón predictores/observaciones es 0.171.
- **Criterio de lectura:** Una razón elevada entre predictores y observaciones incrementa el riesgo de sobreajuste y justifica reducción dimensional.
- **Fundamento o ecuación:** R_{p/n}=\frac{p}{n}
- **Ubicación sugerida:** Inicio de la sección de perfil del dataset y diagnóstico de small data.
- **Limitaciones:** La razón p/n es un indicador estructural; no determina por sí sola el desempeño de los modelos.

### Figura 40. Variables por dimensión metodológica

- **Estado:** generada
- **Archivo:** `40_variables_por_dimension_metodologica.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `resumen_dimensiones`
- **Variables:** dimension, variables
- **Objetivo académico:** Cuantificar qué familias explican la dimensionalidad total.
- **Interpretación:** La dimensión dominante es 'rezagos historicos' con 126 variables.
- **Criterio de lectura:** Las dimensiones con más columnas son candidatas prioritarias para revisar redundancia y parsimonia.
- **Fundamento o ecuación:** p_g=\sum_{j=1}^{p}I(d_j=g)
- **Ubicación sugerida:** Descripción del dataset y justificación del análisis dimensional.
- **Limitaciones:** El conteo no equivale a relevancia predictiva.

### Figura 41. Esparsidad promedio por dimensión

- **Estado:** generada
- **Archivo:** `41_esparsidad_promedio_por_dimension.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `resumen_dimensiones`
- **Variables:** dimension, ceros_promedio
- **Objetivo académico:** Comparar la intermitencia y concentración de ceros entre familias de predictores.
- **Interpretación:** La mayor proporción promedio de ceros corresponde a 'rezagos historicos' con 92.2%.
- **Criterio de lectura:** Una dimensión muy esparsa puede ser informativa, pero exige métricas y modelos robustos a ceros.
- **Fundamento o ecuación:** Z_g=\frac{1}{p_g}\sum_{j\in g}\left[\frac{1}{n}\sum_{i=1}^{n}I(x_{ij}=0)\right]100
- **Ubicación sugerida:** Diagnóstico de intermitencia, small data y calidad de predictores.
- **Limitaciones:** Un cero puede representar ausencia real de actividad y no un error.

### Figura 42. Nulos promedio por dimensión

- **Estado:** generada
- **Archivo:** `42_nulos_promedio_por_dimension.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `resumen_dimensiones`
- **Variables:** dimension, nulos_promedio
- **Objetivo académico:** Auditar la completitud del panel por familia de variables.
- **Interpretación:** El promedio simple entre dimensiones es 0.000% de valores nulos.
- **Criterio de lectura:** Barras cercanas a cero indican que la fase de ingeniería produjo un panel completo.
- **Fundamento o ecuación:** M_g=\frac{1}{p_g}\sum_{j\in g}\frac{NA_j}{n}\times100
- **Ubicación sugerida:** Control de calidad previo a selección de características.
- **Limitaciones:** La ausencia de nulos no garantiza ausencia de imputaciones o errores semánticos.

### Figura 43. Variables constantes por dimensión

- **Estado:** generada
- **Archivo:** `43_variables_constantes_por_dimension.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `resumen_dimensiones`
- **Variables:** dimension, variables_constantes
- **Objetivo académico:** Identificar columnas sin variabilidad y, por tanto, sin capacidad discriminante.
- **Interpretación:** Se detectaron 0 variables constantes en el conjunto perfilado.
- **Criterio de lectura:** Una variable constante no puede explicar diferencias entre observaciones y normalmente debe excluirse.
- **Fundamento o ecuación:** Var(X_j)=0\Rightarrow X_j=c\;\forall i
- **Ubicación sugerida:** Auditoría de baja varianza y depuración previa al modelado.
- **Limitaciones:** Una variable constante en esta muestra podría variar en periodos futuros, aunque no aporta al ajuste actual.

### Figura 44. Cardinalidad frente a esparsidad

- **Estado:** generada
- **Archivo:** `44_cardinalidad_vs_esparsidad_variables.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `perfil_variables`
- **Variables:** valores_unicos, porcentaje_ceros, dimension
- **Objetivo académico:** Distinguir variables constantes, binarias, discretas y continuas según su cardinalidad y concentración de ceros.
- **Interpretación:** Los puntos en la zona superior izquierda representan variables con pocos estados y alta esparsidad.
- **Criterio de lectura:** La combinación de baja cardinalidad y muchos ceros puede indicar eventos raros o variables poco informativas.
- **Fundamento o ecuación:** K_j=|\{x_{1j},\ldots,x_{nj}\}|,\qquad Z_j=\frac{\sum_iI(x_{ij}=0)}{n}100
- **Ubicación sugerida:** Caracterización estructural de predictores y justificación de filtros de baja varianza.
- **Limitaciones:** La gráfica no evalúa relación con los objetivos.

### Figura 45. Variables con mayor concentración de ceros

- **Estado:** generada
- **Archivo:** `45_variables_mayor_concentracion_ceros.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `perfil_variables`
- **Variables:** variable, porcentaje_ceros
- **Objetivo académico:** Identificar predictores individuales dominados por ausencia de actividad.
- **Interpretación:** Las primeras posiciones corresponden a columnas donde la señal positiva aparece en pocos días.
- **Criterio de lectura:** Estas variables deben revisarse junto con su importancia predictiva antes de eliminarlas.
- **Fundamento o ecuación:** Z_j=\frac{1}{n}\sum_{i=1}^{n}I(x_{ij}=0)\times100
- **Ubicación sugerida:** Anexo de calidad del dataset y discusión sobre demanda intermitente.
- **Limitaciones:** Una alta tasa de ceros puede representar un evento raro valioso.

### Figura 46. Variabilidad relativa de las variables

- **Estado:** generada
- **Archivo:** `46_coeficiente_variacion_variables.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `perfil_variables`
- **Variables:** media, desviacion
- **Objetivo académico:** Comparar dispersión relativa entre variables con escalas diferentes.
- **Interpretación:** Valores altos indican que la desviación es grande respecto a la media y pueden señalar volatilidad o intermitencia.
- **Criterio de lectura:** El coeficiente es más interpretable cuando la media está alejada de cero.
- **Fundamento o ecuación:** CV_j=\frac{s_j}{|\bar{x}_j|}
- **Ubicación sugerida:** Diagnóstico de estabilidad y necesidad de escalamiento.
- **Limitaciones:** El CV es inestable para medias cercanas a cero y no se interpreta igual en variables binarias.

### Figura 47. Rango intercuartílico de las variables

- **Estado:** generada
- **Archivo:** `47_rango_intercuartil_variables.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `perfil_variables`
- **Variables:** p25, p75, variable
- **Objetivo académico:** Medir la dispersión robusta del 50% central de cada variable.
- **Interpretación:** Las barras grandes identifican variables con amplitud central elevada sin depender directamente de valores extremos.
- **Criterio de lectura:** El IQR complementa la desviación estándar en distribuciones asimétricas.
- **Fundamento o ecuación:** IQR_j=Q_{0.75,j}-Q_{0.25,j}
- **Ubicación sugerida:** Descripción estadística y detección preliminar de escalas heterogéneas.
- **Limitaciones:** No es comparable entre variables con unidades distintas sin normalización.

### Figura 48. Resumen distributivo de los objetivos

- **Estado:** generada
- **Archivo:** `48_boxplot_resumen_objetivos.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `objetivos`
- **Variables:** min, 25%, 50%, 75%, max
- **Objetivo académico:** Comparar posición central, dispersión y amplitud de los cuatro objetivos a partir de sus estadísticos descriptivos.
- **Interpretación:** La caja representa el rango intercuartílico, la línea central la mediana y los bigotes el mínimo y máximo observados.
- **Criterio de lectura:** Las escalas monetarias y de conteo son distintas; la figura describe forma y amplitud, no igualdad de unidades.
- **Fundamento o ecuación:** IQR=Q_{0.75}-Q_{0.25}
- **Ubicación sugerida:** Caracterización de las variables objetivo antes del modelado.
- **Limitaciones:** Los valores extremos pueden comprimir visualmente las cajas de objetivos con menor escala.

### Figura 49. Intermitencia de las variables objetivo

- **Estado:** generada
- **Archivo:** `49_intermitencia_variables_objetivo.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `perfil_variables`
- **Variables:** variable, porcentaje_ceros
- **Objetivo académico:** Cuantificar cuántos días presentan ausencia de ventas o compras en cada objetivo.
- **Interpretación:** Los objetivos con mayor proporción de ceros requieren especial cautela al usar MAPE y modelos continuos convencionales.
- **Criterio de lectura:** Las barras permiten distinguir demanda intermitente de variabilidad monetaria.
- **Fundamento o ecuación:** Z_y=\frac{1}{n}\sum_{t=1}^{n}I(y_t=0)\times100
- **Ubicación sugerida:** Justificación de métricas de error y dificultad diferencial entre objetivos.
- **Limitaciones:** El cero debe provenir de un calendario completo y una captura exhaustiva.

### Figura 50. Matriz de calidad por dimensión

- **Estado:** generada
- **Archivo:** `50_matriz_calidad_dimensiones.png`
- **Fuente y hoja:** `01_perfil_dataset_y_dimensiones.xlsx` / `resumen_dimensiones`
- **Variables:** variables, nulos_promedio, ceros_promedio, variables_constantes
- **Objetivo académico:** Integrar en una sola figura complejidad, nulos, esparsidad y variables constantes por dimensión.
- **Interpretación:** Las celdas intensas señalan dimensiones relativamente altas en cada indicador; los números conservan la escala original.
- **Criterio de lectura:** La normalización es por columna y permite comparar patrones, no magnitudes entre indicadores distintos.
- **Fundamento o ecuación:** z_{gk}=\frac{x_{gk}-\min_gx_{gk}}{\max_gx_{gk}-\min_gx_{gk}}
- **Ubicación sugerida:** Cierre del perfil dimensional y transición al diagnóstico de multicolinealidad.
- **Limitaciones:** Un indicador alto no implica eliminación automática; debe combinarse con relevancia predictiva e interpretabilidad.

### Figura 51. Distribución de correlaciones altas

- **Estado:** generada
- **Archivo:** `51_distribucion_correlaciones_altas.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `pares_correlacion_alta`
- **Variables:** correlacion_abs
- **Objetivo académico:** Mostrar la intensidad global de la redundancia lineal detectada.
- **Interpretación:** Se identificaron 60 pares; la mediana es 0.968.
- **Criterio de lectura:** Valores próximos a uno indican representaciones prácticamente equivalentes.
- **Fundamento o ecuación:** |r_jk| >= 0.92
- **Ubicación sugerida:** Apertura del diagnóstico de multicolinealidad.
- **Limitaciones:** Solo representa pares que superaron el umbral.

### Figura 52. Pares de mayor correlación

- **Estado:** generada
- **Archivo:** `52_pares_predictores_mayor_correlacion.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `pares_correlacion_alta`
- **Variables:** variable_1, variable_2, correlacion_abs
- **Objetivo académico:** Identificar transformaciones que contienen información casi duplicada.
- **Interpretación:** El par principal es ventas_registros_roll7_mean y ventas_registros_roll7_sum, con |r|=1.0000.
- **Criterio de lectura:** Los pares más cercanos a uno requieren revisión prioritaria.
- **Fundamento o ecuación:** r_jk = cov(X_j,X_k)/(s_j s_k)
- **Ubicación sugerida:** Evidencia empírica de redundancia entre características.
- **Limitaciones:** Correlación alta no implica que una variable sea incorrecta.

### Figura 53. Red de redundancia

- **Estado:** generada
- **Archivo:** `53_red_redundancia_predictores.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `pares_correlacion_alta`
- **Variables:** variable_1, variable_2, correlacion_abs
- **Objetivo académico:** Representar la multicolinealidad como una red de dependencias.
- **Interpretación:** La variable más conectada es ventas_importe_real_2026_05_roll7_mean, con 3 relaciones.
- **Criterio de lectura:** El tamaño del nodo representa frecuencia de conexiones y la arista representa correlación.
- **Fundamento o ecuación:** G=(V,E), E={(j,k): |r_jk|>=0.92}
- **Ubicación sugerida:** Síntesis visual de grupos redundantes.
- **Limitaciones:** Se muestran únicamente las variables más conectadas.

### Figura 54. Frecuencia de variables redundantes

- **Estado:** generada
- **Archivo:** `54_frecuencia_variables_redundantes.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `pares_correlacion_alta`
- **Variables:** variable_1, variable_2
- **Objetivo académico:** Priorizar variables que participan repetidamente en relaciones de alta correlación.
- **Interpretación:** ventas_importe_real_2026_05_roll7_mean aparece en 3 pares.
- **Criterio de lectura:** Una frecuencia alta señala familias de transformaciones similares.
- **Fundamento o ecuación:** d_j = suma I(|r_jk|>=0.92)
- **Ubicación sugerida:** Priorización de variables para depuración.
- **Limitaciones:** La frecuencia no mide relación con el objetivo.

### Figura 55. Conservadas y eliminadas por objetivo

- **Estado:** generada
- **Archivo:** `55_conservadas_eliminadas_por_objetivo.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `filtro_* y conservadas_*`
- **Variables:** variable_conservada, variable_eliminada
- **Objetivo académico:** Comparar el efecto de la depuración para cada objetivo.
- **Interpretación:** Cada objetivo conserva su propio conjunto porque la relevancia predictiva cambia.
- **Criterio de lectura:** Las barras comparan magnitud de conservación y eliminación.
- **Fundamento o ecuación:** S_y = GreedyFilter(X,y,0.92)
- **Ubicación sugerida:** Justificación de selección específica por objetivo.
- **Limitaciones:** El procedimiento codicioso depende del orden de evaluación.

### Figura 56. Dimensiones conservadas

- **Estado:** generada
- **Archivo:** `56_dimensiones_conservadas_por_objetivo.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `conservadas_*`
- **Variables:** variable, dimension
- **Objetivo académico:** Verificar que la reducción mantenga cobertura conceptual.
- **Interpretación:** Las celdas muestran variables sobrevivientes de cada dimensión.
- **Criterio de lectura:** Una dimensión pequeña puede seguir siendo predictivamente importante.
- **Fundamento o ecuación:** n_g,y = número de X_j conservadas en dimensión g
- **Ubicación sugerida:** Control de interpretabilidad tras la reducción.
- **Limitaciones:** El conteo no mide importancia individual.

### Figura 57. Relevancia conservada frente a eliminada

- **Estado:** generada
- **Archivo:** `57_relevancia_conservada_vs_eliminada.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `filtro_*`
- **Variables:** corr_objetivo_conservada, corr_objetivo_eliminada
- **Objetivo académico:** Comprobar la regla de conservación por asociación con el objetivo.
- **Interpretación:** Se representan 172 decisiones; los puntos deben ubicarse sobre o por encima de la diagonal.
- **Criterio de lectura:** La distancia respecto a la diagonal expresa la ventaja de la variable conservada.
- **Fundamento o ecuación:** keep = argmax |Corr(X_j,y)|
- **Ubicación sugerida:** Validación gráfica de la regla codiciosa.
- **Limitaciones:** La correlación marginal no captura interacciones.

### Figura 58. Ganancia de relevancia

- **Estado:** generada
- **Archivo:** `58_ganancia_relevancia_filtro.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `filtro_*`
- **Variables:** corr_objetivo_conservada, corr_objetivo_eliminada
- **Objetivo académico:** Cuantificar la ventaja de la variable conservada.
- **Interpretación:** Valores cercanos a cero corresponden a alternativas casi equivalentes.
- **Criterio de lectura:** La caja resume diferencias por objetivo.
- **Fundamento o ecuación:** Delta = |Corr(X_keep,y)| - |Corr(X_drop,y)|
- **Ubicación sugerida:** Evaluación cuantitativa de decisiones.
- **Limitaciones:** Una ventaja pequeña puede justificarse por interpretabilidad.

### Figura 59. Ranking de VIF

- **Estado:** generada
- **Archivo:** `59_ranking_vif_variables.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `vif_opcional`
- **Variables:** variable, vif
- **Objetivo académico:** Identificar dependencia multivariada entre predictores.
- **Interpretación:** Se detectaron 25 valores VIF infinitos.
- **Criterio de lectura:** VIF alto indica que una variable puede explicarse mediante otras.
- **Fundamento o ecuación:** VIF_j = 1/(1-R_j^2)
- **Ubicación sugerida:** Complemento al análisis de pares.
- **Limitaciones:** Se calcula solo sobre las 80 variables de mayor varianza.

### Figura 60. Clasificación por VIF

- **Estado:** generada
- **Archivo:** `60_clasificacion_variables_vif.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `vif_opcional`
- **Variables:** vif
- **Objetivo académico:** Resumir la gravedad de la multicolinealidad multivariada.
- **Interpretación:** Las categorías distinguen niveles bajos, moderados, altos e infinitos.
- **Criterio de lectura:** Una concentración alta respalda reducción dimensional.
- **Fundamento o ecuación:** VIF_j = 1/(1-R_j^2)
- **Ubicación sugerida:** Síntesis académica del VIF.
- **Limitaciones:** Los umbrales 5 y 10 son orientativos.

### Figura 61. Solapamiento de eliminaciones

- **Estado:** generada
- **Archivo:** `61_solapamiento_variables_eliminadas.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `filtro_*`
- **Variables:** variable_eliminada
- **Objetivo académico:** Evaluar si la redundancia es estable entre objetivos.
- **Interpretación:** 15 variables son eliminadas por los cuatro objetivos.
- **Criterio de lectura:** Las eliminadas consistentemente son candidatas a reducción global.
- **Fundamento o ecuación:** f_j = suma_y I(X_j eliminada)
- **Ubicación sugerida:** Definición de candidatos globales y específicos.
- **Limitaciones:** La coincidencia no sustituye validación fuera de muestra.

### Figura 62. Síntesis de multicolinealidad

- **Estado:** generada
- **Archivo:** `62_resumen_diagnostico_multicolinealidad.png`
- **Fuente y hoja:** `02_diagnostico_multicolinealidad.xlsx` / `Varias hojas`
- **Variables:** pares, variables, conservadas y eliminadas
- **Objetivo académico:** Cerrar la etapa con una visión cuantitativa de la redundancia.
- **Interpretación:** Integra pares detectados y magnitud de decisiones por objetivo.
- **Criterio de lectura:** Es evidencia diagnóstica previa a la selección definitiva.
- **Fundamento o ecuación:** Reducción_y = p - |S_y|
- **Ubicación sugerida:** Transición a selección de características.
- **Limitaciones:** Depende del umbral y del subconjunto VIF.

### Figura 63. Resultado global de la selección

- **Estado:** generada
- **Archivo:** `63_resultado_global_seleccion_caracteristicas.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `resumen`
- **Variables:** variables_originales, variables_reducidas, objetivos
- **Objetivo académico:** Cuantificar la magnitud real de la reducción obtenida.
- **Interpretación:** Se conservaron 80 de 271 predictores y se eliminaron 191, equivalente a 70.48%.
- **Criterio de lectura:** Una reducción pequeña indica que el criterio de unión entre objetivos fue permisivo.
- **Fundamento o ecuación:** Reducción(\%)=\frac{p_{original}-p_{reducido}}{p_{original}}\times100
- **Ubicación sugerida:** Apertura de la sección de selección de características.
- **Limitaciones:** La cantidad de variables no demuestra por sí misma mejora predictiva.

### Figura 64. Variables seleccionadas por objetivo

- **Estado:** generada
- **Archivo:** `64_variables_seleccionadas_por_objetivo.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `ranking_variables`
- **Variables:** target, seleccionada
- **Objetivo académico:** Comparar la amplitud del subconjunto relevante para cada problema predictivo.
- **Interpretación:** Cada objetivo puede seleccionar una combinación diferente de predictores.
- **Criterio de lectura:** Las barras distinguen la decisión binaria producida por el ranking compuesto.
- **Fundamento o ecuación:** I_{j,y}=I(rank_{j,y}\leq K\;\lor\;score_{j,y}\geq\tau)
- **Ubicación sugerida:** Justificación de selección específica por objetivo.
- **Limitaciones:** La unión final puede ser mucho mayor que cada subconjunto individual.

### Figura 65. Distribución del score compuesto

- **Estado:** generada
- **Archivo:** `65_distribucion_score_compuesto_seleccion.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `ranking_variables`
- **Variables:** score_compuesto, seleccionada
- **Objetivo académico:** Mostrar la separación entre variables retenidas y descartadas.
- **Interpretación:** La mediana del score de las seleccionadas es 0.359.
- **Criterio de lectura:** Una superposición amplia indica que parte de la selección depende del criterio Top-K y no solo de un umbral absoluto.
- **Fundamento o ecuación:** Score_{j,y}=\frac{1}{M}\sum_{m=1}^{M}Score^{norm}_{j,y,m}
- **Ubicación sugerida:** Explicación de la función de decisión multicriterio.
- **Limitaciones:** Los scores normalizados son relativos dentro de cada objetivo y método.

### Figura 66. Top de características por objetivo

- **Estado:** generada
- **Archivo:** `66_top_caracteristicas_score_compuesto.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `ranking_variables`
- **Variables:** target, variable, score_compuesto
- **Objetivo académico:** Identificar los predictores con mayor respaldo combinado para cada objetivo.
- **Interpretación:** Las variables superiores no necesariamente coinciden entre ventas, compras e indicadores operativos.
- **Criterio de lectura:** El score sintetiza evidencia lineal, no lineal, de ensamble y regularización.
- **Fundamento o ecuación:** Score_{comp}=media(\rho,MI,RF,|\beta_{Lasso}|)_{normalizados}
- **Ubicación sugerida:** Resultados de selección por objetivo.
- **Limitaciones:** El ranking no expresa causalidad ni garantiza estabilidad temporal.

### Figura 67. Matriz de scores por método

- **Estado:** generada
- **Archivo:** `67_matriz_scores_metodos_top_variables.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `scores_metodos`
- **Variables:** variable, metodo, score_norm
- **Objetivo académico:** Comparar cómo valoran los cuatro métodos a las variables más destacadas.
- **Interpretación:** Filas uniformemente altas muestran consenso; perfiles contrastantes revelan relaciones capturadas solo por ciertos métodos.
- **Criterio de lectura:** La intensidad se interpreta dentro de la normalización de cada método y objetivo.
- **Fundamento o ecuación:** s^{norm}=\frac{s-\min(s)}{\max(s)-\min(s)}
- **Ubicación sugerida:** Comparación metodológica de criterios de importancia.
- **Limitaciones:** Promediar objetivos puede ocultar relevancia específica.

### Figura 68. Concordancia entre métodos

- **Estado:** generada
- **Archivo:** `68_concordancia_metodos_seleccion.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `scores_metodos`
- **Variables:** metodo, score_norm
- **Objetivo académico:** Medir si los métodos ordenan las variables de manera semejante.
- **Interpretación:** Correlaciones altas indican consenso de ranking; valores bajos evidencian complementariedad metodológica.
- **Criterio de lectura:** Se emplea Spearman porque interesa el orden relativo y no la escala original.
- **Fundamento o ecuación:** \rho_s=Corr(rank(s_m),rank(s_{m'}))
- **Ubicación sugerida:** Rigor de la combinación multicriterio.
- **Limitaciones:** La concordancia puede variar entre objetivos aunque aquí se resume conjuntamente.

### Figura 69. Dimensiones seleccionadas por objetivo

- **Estado:** generada
- **Archivo:** `69_dimensiones_seleccionadas_por_objetivo.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `ranking_variables`
- **Variables:** dimension, target, seleccionada
- **Objetivo académico:** Verificar que la selección conserve diversidad conceptual.
- **Interpretación:** La matriz muestra qué dimensiones aportan más variables a cada objetivo.
- **Criterio de lectura:** Una dimensión con pocas variables puede seguir siendo estratégicamente relevante.
- **Fundamento o ecuación:** n_{g,y}=|\{X_j:d_j=g\land I_{j,y}=1\}|
- **Ubicación sugerida:** Análisis de interpretabilidad del dataset reducido.
- **Limitaciones:** Los conteos no equivalen a contribución predictiva acumulada.

### Figura 70. Solapamiento de selección entre objetivos

- **Estado:** generada
- **Archivo:** `70_solapamiento_seleccion_entre_objetivos.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `ranking_variables`
- **Variables:** variable, target, seleccionada
- **Objetivo académico:** Distinguir predictores globales de predictores específicos.
- **Interpretación:** 11 variables fueron seleccionadas por los cuatro objetivos.
- **Criterio de lectura:** Una frecuencia alta sugiere utilidad transversal; una frecuencia de uno indica especialización.
- **Fundamento o ecuación:** f_j=\sum_y I_{j,y}
- **Ubicación sugerida:** Definición del conjunto unido de predictores.
- **Limitaciones:** La estabilidad entre objetivos no equivale a estabilidad temporal.

### Figura 71. Curvas de score por ranking

- **Estado:** generada
- **Archivo:** `71_curvas_score_por_ranking.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `ranking_variables`
- **Variables:** rank_target, score_compuesto, target
- **Objetivo académico:** Visualizar qué tan rápido disminuye la evidencia al avanzar en el ranking.
- **Interpretación:** Una caída pronunciada sugiere una frontera natural; una curva plana indica dificultad para fijar un corte.
- **Criterio de lectura:** La línea vertical representa el criterio Top-K configurado.
- **Fundamento o ecuación:** rank_{j,y}=orden\ descendente(Score_{j,y})
- **Ubicación sugerida:** Justificación gráfica del número de variables retenidas.
- **Limitaciones:** El corte final también depende del umbral de score.

### Figura 72. Esparsidad de LassoCV

- **Estado:** generada
- **Archivo:** `72_esparsidad_coeficientes_lasso.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `scores_metodos`
- **Variables:** target, metodo, score
- **Objetivo académico:** Mostrar cuántos coeficientes son contraídos exactamente a cero.
- **Interpretación:** Una mayor proporción de ceros representa una selección más parsimoniosa dentro del modelo lineal regularizado.
- **Criterio de lectura:** Lasso reduce coeficientes mediante penalización L1.
- **Fundamento o ecuación:** \hat\beta=\arg\min_\beta\{RSS+\lambda\sum_j|\beta_j|\}
- **Ubicación sugerida:** Regularización y parsimonia metodológica.
- **Limitaciones:** Lasso puede elegir arbitrariamente entre predictores altamente correlacionados.

### Figura 73. Método dominante por variable-objetivo

- **Estado:** generada
- **Archivo:** `73_metodo_dominante_por_variable_objetivo.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `scores_metodos`
- **Variables:** target, variable, metodo, score_norm
- **Objetivo académico:** Mostrar qué criterio aporta con mayor frecuencia la evidencia principal.
- **Interpretación:** La distribución revela si la selección está dominada por relaciones lineales, no lineales, ensambles o regularización.
- **Criterio de lectura:** Se asigna como dominante el método con score normalizado máximo en cada combinación.
- **Fundamento o ecuación:** m^*_{j,y}=\arg\max_m s^{norm}_{j,y,m}
- **Ubicación sugerida:** Discusión de complementariedad entre métodos.
- **Limitaciones:** El máximo no refleja la magnitud de la diferencia frente al segundo método.

### Figura 74. Comparación del dataset completo y reducido

- **Estado:** generada
- **Archivo:** `74_comparacion_dataset_completo_reducido.png`
- **Fuente y hoja:** `03_dataset_reducido_por_seleccion.xlsx` / `ranking_variables`
- **Variables:** dimension, variable, seleccionada
- **Objetivo académico:** Evaluar cómo cambia la cobertura de dimensiones al construir el dataset reducido.
- **Interpretación:** El universo contiene 271 predictores y la unión seleccionada conserva 80.
- **Criterio de lectura:** Barras similares evidencian una reducción conservadora; diferencias amplias señalan dimensiones depuradas.
- **Fundamento o ecuación:** p^{sel}_g=|\{X_j:d_j=g\land\max_y I_{j,y}=1\}|
- **Ubicación sugerida:** Cierre de selección y transición a PCA/modelado.
- **Limitaciones:** El conteo dimensional no mide la información predictiva retenida.

### Figura 75. Reducción dimensional mediante PCA

- **Estado:** generada
- **Archivo:** `75_reduccion_dimensional_pca.png`
- **Fuente y hoja:** `dataset_modelado_diario.xlsx y 04_dataset_pca_componentes.xlsx` / `modelo / dataset_pca`
- **Variables:** número de predictores y componentes
- **Objetivo académico:** Cuantificar la compresión lograda conservando el umbral de varianza establecido.
- **Interpretación:** PCA transformó 271 predictores en 130 componentes, una reducción de 52.0%.
- **Criterio de lectura:** La reducción cuenta dimensiones; no implica una pérdida equivalente de información porque los componentes concentran varianza compartida.
- **Fundamento o ecuación:** Reducción(\%)=\frac{p-k}{p}\times100
- **Ubicación sugerida:** Apertura de la sección de reducción por componentes principales.
- **Limitaciones:** El número de componentes depende del escalamiento, del conjunto de entrenamiento y del umbral de varianza.

### Figura 76. Scree Plot

- **Estado:** generada
- **Archivo:** `76_scree_plot_pca.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `varianza_explicada`
- **Variables:** componente, varianza_explicada
- **Objetivo académico:** Mostrar cómo disminuye la contribución marginal de cada componente.
- **Interpretación:** La pendiente pronunciada inicial identifica componentes informativos; la zona plana refleja rendimientos decrecientes.
- **Criterio de lectura:** El punto de codo puede orientar una solución más parsimoniosa, aunque el código utiliza un criterio acumulado de 95%.
- **Fundamento o ecuación:** EVR_j=\frac{\lambda_j}{\sum_{h=1}^{p}\lambda_h}
- **Ubicación sugerida:** Justificación visual del número de componentes.
- **Limitaciones:** El codo es parcialmente subjetivo y no sustituye la validación predictiva.

### Figura 77. Varianza acumulada y umbral de retención

- **Estado:** generada
- **Archivo:** `77_varianza_acumulada_pca.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `varianza_explicada`
- **Variables:** componente, varianza_acumulada
- **Objetivo académico:** Demostrar el punto exacto en que se alcanza la proporción de información definida.
- **Interpretación:** El umbral de 95% se alcanza con 130 componentes.
- **Criterio de lectura:** La curva suma la contribución ordenada de los componentes; el cruce con 95% define la dimensión final.
- **Fundamento o ecuación:** VEA_k=\sum_{j=1}^{k}EVR_j\geq0.95
- **Ubicación sugerida:** Fundamento cuantitativo de la retención de componentes.
- **Limitaciones:** Conservar varianza no garantiza conservar toda la información relevante para cada objetivo.

### Figura 78. Contribución de los primeros componentes

- **Estado:** generada
- **Archivo:** `78_contribucion_primeros_componentes.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `varianza_explicada`
- **Variables:** varianza_explicada
- **Objetivo académico:** Comparar la concentración de información en la parte inicial de la solución PCA.
- **Interpretación:** Los primeros 12 componentes concentran 41.6% de la varianza total.
- **Criterio de lectura:** Barras altas representan ejes latentes que resumen una mayor proporción de variabilidad original.
- **Fundamento o ecuación:** VE_{1:q}=\sum_{j=1}^{q}EVR_j
- **Ubicación sugerida:** Discusión de concentración y rendimientos decrecientes.
- **Limitaciones:** Una alta varianza explicada no equivale necesariamente a mayor relación con las variables objetivo.

### Figura 79. Componentes requeridos por umbral

- **Estado:** generada
- **Archivo:** `79_componentes_por_umbral_varianza.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `varianza_explicada`
- **Variables:** varianza_acumulada
- **Objetivo académico:** Mostrar la relación de compromiso entre compacidad y conservación de varianza.
- **Interpretación:** Cada barra indica la dimensión mínima necesaria para alcanzar un nivel acumulado específico.
- **Criterio de lectura:** Umbrales más altos conservan más variabilidad, pero reducen menos la dimensionalidad.
- **Fundamento o ecuación:** k_\alpha=\min\{k:VEA_k\geq\alpha\}
- **Ubicación sugerida:** Análisis de sensibilidad del umbral de 95%.
- **Limitaciones:** La elección final debe contrastarse con desempeño fuera de muestra e interpretabilidad.

### Figura 80. Mapa de cargas de los primeros componentes

- **Estado:** generada
- **Archivo:** `80_mapa_cargas_primeros_componentes.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `cargas_componentes`
- **Variables:** variable y cargas pca_01 a pca_06
- **Objetivo académico:** Interpretar qué variables originales definen los ejes latentes iniciales.
- **Interpretación:** Valores absolutos altos indican contribución fuerte; el signo representa dirección dentro del eje y puede invertirse sin cambiar la solución.
- **Criterio de lectura:** Patrones semejantes por filas permiten reconocer familias de variables que participan conjuntamente.
- **Fundamento o ecuación:** PC_j=\sum_{i=1}^{p}w_{ij}Z_i
- **Ubicación sugerida:** Interpretación sustantiva de componentes principales.
- **Limitaciones:** Las cargas no son coeficientes causales y su signo es arbitrario.

### Figura 81. Cargas del primer componente

- **Estado:** generada
- **Archivo:** `81_cargas_primer_componente.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `cargas_componentes`
- **Variables:** variable, pca_01
- **Objetivo académico:** Identificar el significado estadístico del eje que concentra la mayor varianza.
- **Interpretación:** Las variables con mayor magnitud son las que más definen PCA 1; signos opuestos representan contrastes dentro del mismo patrón.
- **Criterio de lectura:** La interpretación debe centrarse en magnitudes y familias conceptuales, no solo en el signo.
- **Fundamento o ecuación:** PC_1=w_{11}Z_1+\cdots+w_{p1}Z_p
- **Ubicación sugerida:** Explicación narrativa del primer componente.
- **Limitaciones:** Una etiqueta sustantiva del componente requiere revisar conjuntamente todas las cargas dominantes.

### Figura 82. Contribución acumulada de variables

- **Estado:** generada
- **Archivo:** `82_contribucion_variables_primeros_componentes.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `cargas_componentes`
- **Variables:** cargas de los primeros diez componentes
- **Objetivo académico:** Detectar variables cuya información se distribuye de manera relevante entre varios componentes iniciales.
- **Interpretación:** Una barra alta indica que la variable está bien representada dentro del subespacio inicial.
- **Criterio de lectura:** Se suman las cargas al cuadrado para evitar cancelación entre signos.
- **Fundamento o ecuación:** h_i^2(q)=\sum_{j=1}^{q}w_{ij}^2
- **Ubicación sugerida:** Evaluación de representación de variables originales.
- **Limitaciones:** La medida depende del número de componentes considerado y no incorpora directamente la varianza de cada componente.

### Figura 83. Trayectoria temporal de componentes

- **Estado:** generada
- **Archivo:** `83_series_temporales_componentes_pca.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `dataset_pca`
- **Variables:** fecha, pca_01, pca_02, pca_03
- **Objetivo académico:** Examinar cambios estructurales y patrones temporales dentro del espacio reducido.
- **Interpretación:** Picos o cambios persistentes señalan fechas en las que múltiples variables originales se desplazaron conjuntamente.
- **Criterio de lectura:** Cada serie es una combinación lineal estandarizada y no conserva unidades económicas originales.
- **Fundamento o ecuación:** t_{rj}=Z_r w_j
- **Ubicación sugerida:** Análisis temporal del dataset PCA y transición al modelado.
- **Limitaciones:** Las puntuaciones no deben interpretarse como ventas, compras o utilidad directa.

### Figura 84. Plano factorial PCA 1-PCA 2

- **Estado:** generada
- **Archivo:** `84_plano_factorial_pca1_pca2.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `dataset_pca`
- **Variables:** pca_01, pca_02 y orden temporal
- **Objetivo académico:** Visualizar agrupamientos, trayectorias y observaciones atípicas en las dos direcciones principales.
- **Interpretación:** Puntos alejados del centro representan días con configuraciones multivariadas inusuales; el gradiente temporal permite detectar desplazamientos estructurales.
- **Criterio de lectura:** La distancia en el plano aproxima similitud solo respecto a los dos primeros componentes.
- **Fundamento o ecuación:** d_{rs}^{(2)}=\sqrt{(t_{r1}-t_{s1})^2+(t_{r2}-t_{s2})^2}
- **Ubicación sugerida:** Exploración del espacio latente y detección visual de periodos atípicos.
- **Limitaciones:** Dos componentes pueden explicar una fracción limitada de la varianza total.

### Figura 85. Correlación entre componentes y objetivos

- **Estado:** generada
- **Archivo:** `85_correlacion_componentes_objetivos.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `dataset_pca`
- **Variables:** primeros componentes y cuatro objetivos
- **Objetivo académico:** Examinar qué ejes latentes presentan asociación lineal inicial con cada problema predictivo.
- **Interpretación:** Componentes con correlación elevada pueden ser útiles para un objetivo, aunque PCA fue construido sin utilizar las variables objetivo.
- **Criterio de lectura:** PCA maximiza varianza de predictores y no relevancia supervisada.
- **Fundamento o ecuación:** r_{PC_j,y}=Corr(t_j,y)
- **Ubicación sugerida:** Puente entre reducción no supervisada y evaluación predictiva.
- **Limitaciones:** Una correlación baja no descarta relaciones no lineales o interacciones entre componentes.

### Figura 86. Ortogonalidad de componentes

- **Estado:** generada
- **Archivo:** `86_ortogonalidad_componentes_pca.png`
- **Fuente y hoja:** `04_dataset_pca_componentes.xlsx` / `dataset_pca`
- **Variables:** primeros quince componentes
- **Objetivo académico:** Verificar que los componentes resultantes sean linealmente no correlacionados.
- **Interpretación:** La mayor correlación absoluta fuera de la diagonal es 0.0446; valores próximos a cero evidencian ortogonalidad numérica.
- **Criterio de lectura:** La diagonal vale uno y las celdas externas deberían aproximarse a cero.
- **Fundamento o ecuación:** Cov(PC_j,PC_k)=0\quad j\neq k
- **Ubicación sugerida:** Cierre del PCA y justificación de su utilidad frente a multicolinealidad.
- **Limitaciones:** La ortogonalidad se refiere a relaciones lineales; no implica independencia estadística completa.

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
10. Exponer la estructura general, la razón predictores/observaciones y la distribución por dimensiones.
11. Analizar nulos, ceros, constantes, cardinalidad y dispersión de las variables.
12. Caracterizar la distribución e intermitencia de los cuatro objetivos y cerrar con la matriz de calidad dimensional.
13. Presentar la distribución de correlaciones altas, los pares principales y la red de redundancia.
14. Explicar las decisiones de conservación y eliminación específicas para cada objetivo.
15. Complementar el análisis por pares con VIF y cerrar con la síntesis de reducción potencial.
16. Presentar la magnitud de reducción y la selección específica para cada objetivo.
17. Comparar scores, concordancia de métodos, cobertura dimensional y solapamiento entre objetivos.
18. Explicar la contracción Lasso, el método dominante y cerrar comparando dataset completo y reducido.
19. Cuantificar la reducción PCA y presentar el Scree Plot, la varianza acumulada y los umbrales alternativos.
20. Interpretar las cargas, la contribución de variables y las trayectorias temporales de los componentes.
21. Cerrar con el plano factorial, la relación con objetivos y la verificación de ortogonalidad.

## Nota de rigor

Las figuras son descriptivas. Ninguna asociación visual prueba causalidad ni desempeño predictivo. La capacidad de pronóstico debe establecerse posteriormente mediante partición temporal, validación Rolling-Origin y métricas fuera de muestra.