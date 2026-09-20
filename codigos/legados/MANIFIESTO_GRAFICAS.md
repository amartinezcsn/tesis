# Manifiesto explicativo de gráficas del flujo metodológico

**Fecha de generación:** 2026-08-02T05:14:24
**Directorio de datos intermedios:** `/mnt/data`
**Directorio de resultados:** `/mnt/data`
**Gráficas generadas:** 12

## Propósito

Este manifiesto documenta la relación entre cada gráfica, el archivo Excel del que proviene y la interpretación que puede incorporarse al capítulo metodológico o de resultados de la tesis. Las imágenes no sustituyen las tablas completas; funcionan como evidencia visual sintetizada.

## Reglas generales de lectura

1. Las gráficas descriptivas muestran estructura, concentración y calidad, pero no demuestran capacidad predictiva.
2. Correlación y VIF se utilizan para detectar redundancia; la eliminación debe considerar también relevancia financiera y desempeño fuera de muestra.
3. PCA conserva varianza, pero transforma las variables en componentes menos interpretables.
4. MAE y RMSE deben compararse únicamente dentro del mismo objetivo y unidad.
5. Rolling-Origin y la prueba final de RNN/LSTM son esquemas de evaluación diferentes; no deben compararse sin aclararlo.
6. MAPE puede ser inestable o no calculable cuando los valores reales contienen ceros.

## Catálogo de gráficas

### 1. Distribución de variables por dimensión

- **Etapa:** Perfil del dataset
- **Estado:** generada
- **Imagen:** `01_distribucion_variables_por_dimension.png`
- **Fuente:** `01_perfil_dataset_y_dimensiones.xlsx`
- **Hoja:** `resumen_dimensiones`
- **Variables utilizadas:** dimension, variables
- **Objetivo visual:** Mostrar cómo se distribuye la dimensionalidad entre calendario, rezagos, ventanas móviles y otras familias.
- **Interpretación principal:** La dimensión con más variables es 'rezagos historicos' con 126 columnas. Las barras largas identifican las familias que más incrementan la complejidad del dataset.
- **Criterio de lectura:** Una concentración alta en rezagos o ventanas móviles justifica aplicar diagnóstico de redundancia y reducción dimensional.
- **Limitaciones:** La gráfica cuenta columnas; no mide por sí sola la calidad predictiva de cada dimensión.

### 2. Concentración de ceros y nulos

- **Etapa:** Perfil del dataset
- **Estado:** generada
- **Imagen:** `02_calidad_variables_ceros_nulos.png`
- **Fuente:** `01_perfil_dataset_y_dimensiones.xlsx`
- **Hoja:** `perfil_variables`
- **Variables utilizadas:** variable, porcentaje_ceros, porcentaje_nulos
- **Objetivo visual:** Detectar variables escasas, incompletas o dominadas por ceros que podrían aportar poca información estable.
- **Interpretación principal:** La primera variable del ranking es 'compras_administracion_real_2026_05_lag1'. Una barra extensa significa que gran parte de sus registros no presenta actividad o información disponible.
- **Criterio de lectura:** Las variables con muchos ceros deben evaluarse junto con su relevancia predictiva; no deben eliminarse automáticamente.
- **Limitaciones:** Un cero puede ser un valor real de ausencia de operación y no necesariamente un problema de calidad.

### 3. Pares con mayor correlación absoluta

- **Etapa:** Diagnóstico de multicolinealidad
- **Estado:** generada
- **Imagen:** `03_pares_mayor_multicolinealidad.png`
- **Fuente:** `02_diagnostico_multicolinealidad.xlsx`
- **Hoja:** `pares_correlacion_alta`
- **Variables utilizadas:** variable_1, variable_2, correlacion_abs
- **Objetivo visual:** Evidenciar qué predictores contienen información lineal muy similar y podrían ser redundantes.
- **Interpretación principal:** El par más relacionado es 'ventas_registros_roll7_mean' y 'ventas_registros_roll7_sum', con correlación absoluta de 1.0000.
- **Criterio de lectura:** Los pares por encima de 0.92 deben revisarse para conservar la variable más relacionada con el objetivo o la más interpretable.
- **Limitaciones:** La correlación solamente identifica relaciones lineales entre pares y no sustituye al análisis VIF o a la validación predictiva.

### 4. Variables con mayor VIF

- **Etapa:** Diagnóstico de multicolinealidad
- **Estado:** generada
- **Imagen:** `04_variables_mayor_vif.png`
- **Fuente:** `02_diagnostico_multicolinealidad.xlsx`
- **Hoja:** `vif_opcional`
- **Variables utilizadas:** variable, vif
- **Objetivo visual:** Complementar el análisis de correlación mediante una medida de redundancia de cada variable respecto al conjunto de predictores.
- **Interpretación principal:** La variable con mayor VIF es 'ventas_ganancia_real_2026_05_roll14_std' con 63.76. Valores altos indican que puede explicarse ampliamente mediante otras variables.
- **Criterio de lectura:** VIF superiores a 5 requieren revisión y valores superiores a 10 suelen considerarse evidencia fuerte de multicolinealidad.
- **Limitaciones:** Los umbrales son referencias prácticas y deben combinarse con interpretabilidad y desempeño fuera de muestra.

### 5. Ranking de características seleccionadas

- **Etapa:** Selección de características
- **Estado:** generada
- **Imagen:** `05_ranking_caracteristicas_seleccionadas.png`
- **Fuente:** `03_dataset_reducido_por_seleccion.xlsx`
- **Hoja:** `ranking_variables`
- **Variables utilizadas:** variable, score_compuesto, seleccionada, target
- **Objetivo visual:** Mostrar las variables que concentran mayor evidencia combinada de correlación, información mutua, Random Forest y Lasso.
- **Interpretación principal:** La variable con mayor puntuación media es 'compras_total_real_2026_05_roll28_mean' con score 0.5279, considerando su aparición en 4 objetivo(s).
- **Criterio de lectura:** Una puntuación alta significa consistencia entre los métodos de selección, pero no garantiza por sí sola causalidad ni estabilidad futura.
- **Limitaciones:** El score es relativo a los métodos y umbrales configurados; puede cambiar al modificar el periodo o los hiperparámetros.

### 6. Comparación de dimensionalidad

- **Etapa:** Reducción dimensional
- **Estado:** generada
- **Imagen:** `06_comparacion_reduccion_dimensional.png`
- **Fuente:** `01_perfil_dataset_y_dimensiones.xlsx; 03_dataset_reducido_por_seleccion.xlsx; 04_dataset_pca_componentes.xlsx`
- **Hoja:** `resumen_general; resumen; varianza_explicada`
- **Variables utilizadas:** predictores, variables_reducidas, número de componentes
- **Objetivo visual:** Comparar de forma directa el tamaño del dataset completo, la selección de variables y la representación PCA.
- **Interpretación principal:** La selección reduce aproximadamente 2.6% y PCA reduce 52.0% respecto a 271 predictores originales.
- **Criterio de lectura:** Una mayor reducción mejora compacidad, pero puede disminuir interpretabilidad o perder información predictiva.
- **Limitaciones:** El número de componentes PCA no equivale a variables interpretables de negocio.

### 7. Varianza acumulada de los componentes

- **Etapa:** PCA
- **Estado:** generada
- **Imagen:** `07_varianza_acumulada_pca.png`
- **Fuente:** `04_dataset_pca_componentes.xlsx`
- **Hoja:** `varianza_explicada`
- **Variables utilizadas:** componente, varianza_explicada, varianza_acumulada
- **Objetivo visual:** Justificar cuántos componentes son necesarios para conservar al menos 95 % de la información estadística.
- **Interpretación principal:** El umbral de 95 % se alcanza en el componente 130; el dataset PCA termina con 130 componentes y conserva 95.08% de varianza.
- **Criterio de lectura:** El punto donde la curva cruza 95 % define la dimensionalidad necesaria bajo el criterio configurado.
- **Limitaciones:** La varianza explicada mide conservación estadística, no garantiza el menor error de pronóstico.

### 8. Cargas del primer componente principal

- **Etapa:** PCA
- **Estado:** generada
- **Imagen:** `08_cargas_primer_componente_pca.png`
- **Fuente:** `04_dataset_pca_componentes.xlsx`
- **Hoja:** `cargas_componentes`
- **Variables utilizadas:** variable, pca_01
- **Objetivo visual:** Facilitar una interpretación parcial del componente principal mediante las variables originales con mayor peso absoluto.
- **Interpretación principal:** La mayor carga absoluta en pca_01 corresponde a 'compras_total_real_2026_05_roll14_sum' con valor 0.1300.
- **Criterio de lectura:** Las cargas positivas y negativas indican direcciones opuestas dentro del componente; la magnitud expresa contribución relativa.
- **Limitaciones:** Un componente combina muchas variables, por lo que no debe nombrarse únicamente con base en una sola carga.

### 9. Mejor modelo por dataset y objetivo

- **Etapa:** Modelado Rolling-Origin
- **Estado:** generada
- **Imagen:** `09_mejores_modelos_rolling_origin.png`
- **Fuente:** `05_modelos_rolling_origin_completo.xlsx; 05_modelos_rolling_origin_pca.xlsx; 05_modelos_rolling_origin_reducido.xlsx`
- **Hoja:** `ranking_modelos`
- **Variables utilizadas:** dataset, target, modelo, rmse_promedio
- **Objetivo visual:** Comparar los modelos con validación temporal repetida y mostrar el menor RMSE para cada combinación de dataset y objetivo.
- **Interpretación principal:** El menor RMSE mostrado corresponde a Promedio 7 días para Registros de compras en el dataset completo, con 0.8242.
- **Criterio de lectura:** En cada barra, menor longitud significa mejor desempeño promedio fuera de muestra dentro de su objetivo.
- **Limitaciones:** No deben compararse directamente magnitudes de RMSE entre objetivos expresados en unidades distintas.

### 10. Estabilidad temporal del error

- **Etapa:** Modelado Rolling-Origin
- **Estado:** generada
- **Imagen:** `10_estabilidad_rmse_rolling_origin_ventas.png`
- **Fuente:** `05_modelos_rolling_origin_completo.xlsx; 05_modelos_rolling_origin_reducido.xlsx; 05_modelos_rolling_origin_pca.xlsx`
- **Hoja:** `resultados_por_origen`
- **Variables utilizadas:** fecha_inicio_prueba, dataset, modelo, target, rmse
- **Objetivo visual:** Mostrar si los modelos mantienen un error estable a través de diferentes periodos de validación y no solamente un buen promedio global.
- **Interpretación principal:** Las líneas con valores bajos y poca variación representan modelos más precisos y estables en diferentes orígenes de pronóstico.
- **Criterio de lectura:** Picos aislados revelan periodos difíciles o sensibilidad del modelo a cambios operativos.
- **Limitaciones:** La gráfica se centra en el importe de ventas y en los cuatro mejores pares dataset-modelo por RMSE promedio.

### 11. Comparación RNN y LSTM

- **Etapa:** Redes neuronales recurrentes
- **Estado:** generada
- **Imagen:** `11_comparacion_rnn_lstm_rmse.png`
- **Fuente:** `06_rnn_lstm_pca.xlsx; 06_rnn_lstm_reducido.xlsx`
- **Hoja:** `primera hoja`
- **Variables utilizadas:** dataset, target, modelo, rmse
- **Objetivo visual:** Comparar el error de RNN simple y LSTM usando las versiones reducida y PCA del dataset.
- **Interpretación principal:** El menor RMSE dentro de esta prueba corresponde a LSTM, dataset reducido, objetivo Registros de compras, con 0.0404.
- **Criterio de lectura:** Para cada objetivo deben compararse las barras de RNN y LSTM dentro de la misma escala y versión del dataset.
- **Limitaciones:** Estos resultados proceden de una prueba final de 90 días y no son directamente equivalentes a la validación Rolling-Origin.

### 12. Indicadores cuantitativos del flujo

- **Etapa:** Síntesis metodológica
- **Estado:** generada
- **Imagen:** `12_resumen_cuantitativo_metodologia.png`
- **Fuente:** `01_perfil_dataset_y_dimensiones.xlsx; 02_diagnostico_multicolinealidad.xlsx; 03_dataset_reducido_por_seleccion.xlsx; 04_dataset_pca_componentes.xlsx`
- **Hoja:** `resúmenes metodológicos`
- **Variables utilizadas:** predictores, pares correlacionados, variables seleccionadas, componentes PCA
- **Objetivo visual:** Presentar en una sola figura los principales tamaños y resultados intermedios del análisis dimensional.
- **Interpretación principal:** El proceso parte de 271 predictores, identifica 60 pares altamente correlacionados, conserva 264 variables por selección y representa la información mediante 130 componentes PCA.
- **Criterio de lectura:** La figura permite explicar el tránsito desde el dataset original hacia dos estrategias alternativas de reducción.
- **Limitaciones:** Las barras representan conceptos diferentes; se comparan como conteos metodológicos, no como métricas de desempeño.

## Uso recomendado en la tesis

Las gráficas 1 y 2 pueden colocarse en la caracterización del dataset. Las gráficas 3 y 4 respaldan el diagnóstico de multicolinealidad. Las gráficas 5 a 8 documentan las estrategias de reducción dimensional. Las gráficas 9 y 10 corresponden a la validación temporal Rolling-Origin. La gráfica 11 presenta los resultados de redes recurrentes bajo prueba final. La gráfica 12 puede emplearse como cierre visual del flujo metodológico.

## Reproducibilidad

Todas las imágenes se generan directamente desde los archivos Excel producidos por los scripts metodológicos. Para reproducirlas se debe ejecutar este código después de completar las etapas de perfil, multicolinealidad, selección, PCA, Rolling-Origin y RNN/LSTM.