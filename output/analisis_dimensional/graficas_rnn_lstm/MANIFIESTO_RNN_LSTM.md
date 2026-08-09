# Manifiesto académico de gráficas RNN/LSTM

Generado: 2026-08-08 11:28

## Alcance metodológico

Este módulo documenta la preparación de secuencias, la arquitectura base y la comparación de RNN simple y LSTM sobre los datasets reducido y PCA.
Los resultados proceden de una única partición temporal final de 90 días; no son directamente equivalentes a la evaluación Rolling-Origin de los modelos tradicionales.

## Figura 1. Partición temporal de entrenamiento y prueba

- **Archivo:** `01_particion_temporal_rnn_lstm.png`
- **Fuente:** Datasets reducido/PCA y configuración de 08_rnn_lstm_dataset_reducido.py
- **Hoja:** Varias
- **Variables:** fecha, LOOKBACK_DAYS, TEST_DAYS
- **Objetivo:** Documentar que la prueba corresponde a los últimos 90 días y no a una muestra aleatoria.
- **Interpretación:** El bloque final se reserva íntegramente para evaluación; los 28 días previos aportan contexto para formar la primera secuencia de prueba.
- **Criterio de lectura:** La separación cronológica evita entrenar con observaciones posteriores al periodo pronosticado.
- **Ecuación o fundamento:** `Train=\{1,\ldots,N-90\},\quad Test=\{N-89,\ldots,N\}`
- **Uso sugerido en tesis:** Metodología de partición temporal para redes recurrentes.
- **Limitaciones:** Es una sola partición final, no una validación Rolling-Origin; por ello su incertidumbre temporal está menos caracterizada.

## Figura 2. Ventanas supervisadas de 14 y 28 días

- **Archivo:** `02_ventana_supervisada_28_dias.png`
- **Fuente:** 08_rnn_lstm_dataset_reducido.py
- **Hoja:** make_sequences
- **Variables:** x[i-L:i], y[i], L en {14, 28}
- **Objetivo:** Ilustrar cómo cada ejemplo utiliza la ventana candidata ganadora para estimar el valor del día siguiente.
- **Interpretación:** La red recibe un tensor temporal y aprende dependencias entre posiciones consecutivas.
- **Criterio de lectura:** Cada ventana termina en t-1; el objetivo corresponde a t, evitando incluir el valor futuro dentro de la entrada.
- **Ecuación o fundamento:** `X_t=[x_{t-L},\ldots,x_{t-1}],\quad L\in\{14,28\}`
- **Uso sugerido en tesis:** Explicación de la preparación supervisada de datos para RNN y LSTM.
- **Limitaciones:** El horizonte efectivo es de un día; el código evalúa 90 predicciones de un paso construidas sobre el contexto final.

## Figura 3. Arquitectura de las redes recurrentes

- **Archivo:** `03_arquitectura_rnn_lstm.png`
- **Fuente:** 08_rnn_lstm_dataset_reducido.py
- **Hoja:** Sequential
- **Variables:** entrada, capa recurrente, capa densa, Dense(1)
- **Objetivo:** Representar las arquitecturas candidatas utilizadas para comparar RNN simple y LSTM.
- **Interpretación:** La única diferencia estructural entre modelos es el tipo de capa recurrente; las capas densas y la salida son equivalentes.
- **Criterio de lectura:** La comparación es más controlada porque mantiene constante el resto de la arquitectura.
- **Ecuación o fundamento:** `\hat y_t=W_2\,ReLU(W_1h_t+b_1)+b_2`
- **Uso sugerido en tesis:** Configuración del experimento de aprendizaje profundo.
- **Limitaciones:** La rejilla es compacta y no constituye una búsqueda exhaustiva.

## Figura 4. Dimensionalidad de entrada de las redes

- **Archivo:** `04_dimensionalidad_entrada_recurrente.png`
- **Fuente:** 03_dataset_reducido... / 04_dataset_pca...
- **Hoja:** dataset_reducido / dataset_pca
- **Variables:** número de predictores y 28×p
- **Objetivo:** Comparar la carga informativa que recibe cada secuencia según la representación del dataset.
- **Interpretación:** PCA reduce el número de canales de entrada frente al dataset reducido; cada ejemplo contiene 28 veces el número de predictores.
- **Criterio de lectura:** La escala logarítmica permite comparar predictores y valores totales de una secuencia.
- **Ecuación o fundamento:** `Dim(X)=N_{seq}\times 28\times p`
- **Uso sugerido en tesis:** Justificación del control de dimensionalidad antes del aprendizaje profundo.
- **Limitaciones:** Menos entradas reducen complejidad, pero PCA disminuye interpretabilidad de los canales.

## Figura 5. Comparación de RMSE

- **Archivo:** `05_comparacion_rmse_rnn_lstm.png`
- **Fuente:** 06_rnn_lstm_reducido.xlsx y 06_rnn_lstm_pca.xlsx
- **Hoja:** resultados
- **Variables:** dataset, target, modelo, rmse
- **Objetivo:** Comparar la penalización de errores grandes entre arquitecturas y representaciones.
- **Interpretación:** Una barra menor representa mejor ajuste predictivo para el objetivo correspondiente.
- **Criterio de lectura:** La comparación debe hacerse dentro de cada objetivo, no entre unidades monetarias y conteos.
- **Ecuación o fundamento:** `RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}`
- **Uso sugerido en tesis:** Resultados de desempeño predictivo de redes recurrentes.
- **Limitaciones:** Cada métrica proviene de una única partición final de 90 días.

## Figura 6. Comparación de MAE

- **Archivo:** `06_comparacion_mae_rnn_lstm.png`
- **Fuente:** 06_rnn_lstm_reducido.xlsx y 06_rnn_lstm_pca.xlsx
- **Hoja:** resultados
- **Variables:** dataset, target, modelo, mae
- **Objetivo:** Comparar la magnitud promedio de los errores en las unidades originales.
- **Interpretación:** MAE resume el error típico sin penalizar cuadráticamente los valores extremos.
- **Criterio de lectura:** Una menor barra significa menor desviación absoluta promedio.
- **Ecuación o fundamento:** `MAE=\frac{1}{n}\sum_{i=1}^{n}|y_i-\hat y_i|`
- **Uso sugerido en tesis:** Evaluación de precisión media de las redes.
- **Limitaciones:** No muestra la dirección del sesgo ni la distribución temporal de los errores.

## Figura 7. Diagnóstico del MAPE

- **Archivo:** `07_diagnostico_mape_rnn_lstm.png`
- **Fuente:** 06_rnn_lstm_reducido.xlsx y 06_rnn_lstm_pca.xlsx
- **Hoja:** resultados
- **Variables:** dataset, target, modelo, mape
- **Objetivo:** Mostrar la inestabilidad del error porcentual cuando existen valores reales pequeños o iguales a cero.
- **Interpretación:** MAPE muy elevado no necesariamente implica el mismo deterioro observado en MAE o RMSE; puede estar dominado por denominadores pequeños.
- **Criterio de lectura:** Debe interpretarse junto con la tasa de ceros de cada objetivo.
- **Ecuación o fundamento:** `MAPE=\frac{100}{n}\sum_i\left|\frac{y_i-\hat y_i}{y_i}\right|`
- **Uso sugerido en tesis:** Discusión crítica de métricas para series intermitentes.
- **Limitaciones:** El código excluye denominadores cercanos a cero, pero los valores pequeños siguen amplificando el porcentaje.

## Figura 8. Arquitectura ganadora por objetivo

- **Archivo:** `08_arquitectura_ganadora_por_objetivo.png`
- **Fuente:** 06_rnn_lstm_*.xlsx
- **Hoja:** resultados
- **Variables:** dataset, target, modelo, rmse
- **Objetivo:** Identificar si RNN simple o LSTM obtiene el menor RMSE en cada combinación.
- **Interpretación:** La etiqueta muestra el modelo ganador y su error absoluto.
- **Criterio de lectura:** El ganador se determina de forma independiente para cada dataset y objetivo.
- **Ecuación o fundamento:** `m^*_{d,y}=\arg\min_m RMSE_{d,y,m}`
- **Uso sugerido en tesis:** Síntesis de comparación arquitectónica.
- **Limitaciones:** Una diferencia pequeña no demuestra superioridad estadística; no hay repeticiones con distintas semillas.

## Figura 9. Mejora relativa de LSTM

- **Archivo:** `09_mejora_lstm_vs_rnn.png`
- **Fuente:** 06_rnn_lstm_*.xlsx
- **Hoja:** resultados
- **Variables:** rmse de rnn_simple y lstm
- **Objetivo:** Cuantificar si la memoria controlada de LSTM produce una mejora práctica frente a una RNN simple.
- **Interpretación:** Valores positivos favorecen LSTM; valores negativos favorecen RNN simple.
- **Criterio de lectura:** La magnitud porcentual permite comparar objetivos con escalas distintas.
- **Ecuación o fundamento:** `Mejora_{LSTM}=\frac{RMSE_{RNN}-RMSE_{LSTM}}{RMSE_{RNN}}\times100`
- **Uso sugerido en tesis:** Discusión de la contribución de las compuertas LSTM.
- **Limitaciones:** No incorpora costo computacional ni incertidumbre por inicialización aleatoria.

## Figura 10. Efecto del dataset reducido frente a PCA

- **Archivo:** `10_efecto_dataset_reducido_vs_pca.png`
- **Fuente:** 06_rnn_lstm_reducido.xlsx y 06_rnn_lstm_pca.xlsx
- **Hoja:** resultados
- **Variables:** dataset, modelo, target, rmse
- **Objetivo:** Evaluar si la compacidad PCA mejora o deteriora el desempeño respecto a variables seleccionadas interpretables.
- **Interpretación:** Valores negativos indican que PCA reduce el RMSE; positivos indican que el dataset reducido fue mejor.
- **Criterio de lectura:** La comparación se realiza para la misma arquitectura y objetivo.
- **Ecuación o fundamento:** `\Delta_{PCA}=\frac{RMSE_{PCA}-RMSE_{red}}{RMSE_{red}}\times100`
- **Uso sugerido en tesis:** Comparación de estrategias de reducción dimensional para deep learning.
- **Limitaciones:** PCA puede mejorar estabilidad numérica, pero sacrifica interpretabilidad.

## Figura 11. Relación entre MAE y RMSE

- **Archivo:** `11_relacion_mae_rmse_redes.png`
- **Fuente:** 06_rnn_lstm_*.xlsx
- **Hoja:** resultados
- **Variables:** mae, rmse
- **Objetivo:** Detectar combinaciones donde algunos errores grandes elevan sustancialmente el RMSE.
- **Interpretación:** Cuanto más alejado se encuentre un punto por encima de la diagonal, mayor es la influencia de errores extremos.
- **Criterio de lectura:** La diagonal representa igualdad teórica entre ambas métricas.
- **Ecuación o fundamento:** `RMSE\geq MAE`
- **Uso sugerido en tesis:** Análisis de severidad y heterogeneidad del error.
- **Limitaciones:** Las métricas agregadas no permiten localizar temporalmente los errores extremos.

## Figura 12. Score multicriterio

- **Archivo:** `12_score_multicriterio_rnn_lstm.png`
- **Fuente:** 06_rnn_lstm_*.xlsx
- **Hoja:** resultados
- **Variables:** mae, rmse, mape
- **Objetivo:** Sintetizar el desempeño conjunto de las tres métricas después de normalizarlas por objetivo.
- **Interpretación:** Un score menor representa mejor equilibrio relativo.
- **Criterio de lectura:** La normalización evita mezclar escalas monetarias y de conteo.
- **Ecuación o fundamento:** `S=\frac{MAE^{norm}+RMSE^{norm}+MAPE^{norm}}{3}`
- **Uso sugerido en tesis:** Síntesis complementaria del rendimiento de las redes.
- **Limitaciones:** El peso uniforme es una decisión analítica y MAPE puede distorsionar el score en series con ceros.

## Figura 13. Configuración de entrenamiento

- **Archivo:** `13_configuracion_entrenamiento_redes.png`
- **Fuente:** 08_rnn_lstm_dataset_reducido.py
- **Hoja:** Constantes y model.fit
- **Variables:** LOOKBACK_DAYS, TEST_DAYS, EPOCHS, BATCH_SIZE, unidades, paciencia
- **Objetivo:** Resumir los principales hiperparámetros que controlan la capacidad y el proceso de ajuste.
- **Interpretación:** La figura documenta los límites superiores de la rejilla reproducible.
- **Criterio de lectura:** EarlyStopping puede detener el ajuste antes de las 60 épocas; la mejor época queda registrada en el Excel.
- **Ecuación o fundamento:** `\theta^*=\arg\min_\theta MAE_{val}(\theta)`
- **Uso sugerido en tesis:** Tabla o figura de configuración experimental.
- **Limitaciones:** El detalle conserva la mejor época, pero no la historia completa de pérdida.

## Figura 14. Complejidad paramétrica frente a la muestra

- **Archivo:** `14_complejidad_parametros_vs_muestra.png`
- **Fuente:** Datasets de entrada y arquitectura del código 08
- **Hoja:** Varias
- **Variables:** predictores, secuencias, parámetros estimados
- **Objetivo:** Ilustrar el riesgo de sobreajuste al relacionar la capacidad de la red con el número de secuencias disponibles.
- **Interpretación:** LSTM posee aproximadamente cuatro veces más parámetros recurrentes que una RNN simple con igual número de unidades.
- **Criterio de lectura:** Una razón elevada señala alta capacidad relativa frente a una muestra pequeña.
- **Ecuación o fundamento:** `Params_{RNN}=u(p+u+1),\quad Params_{LSTM}=4u(p+u+1)`
- **Uso sugerido en tesis:** Discusión de Small Data y complejidad de aprendizaje profundo.
- **Limitaciones:** Es una estimación estructural; no sustituye una curva de aprendizaje ni validación con múltiples semillas.

## Figura 15. Intermitencia en el periodo de prueba

- **Archivo:** `15_intermitencia_objetivos_periodo_prueba.png`
- **Fuente:** 03_dataset_reducido... / 04_dataset_pca...
- **Hoja:** últimos 90 días
- **Variables:** targets y porcentaje de ceros
- **Objetivo:** Relacionar la frecuencia de ceros con la inestabilidad del MAPE y la dificultad predictiva.
- **Interpretación:** Los objetivos con más ceros suelen presentar errores porcentuales extremos y mayor dificultad para redes entrenadas con pérdidas continuas.
- **Criterio de lectura:** La tasa se calcula únicamente sobre el bloque final de prueba.
- **Ecuación o fundamento:** `Z_y=\frac{1}{90}\sum_{t\in Test}I(y_t=0)\times100`
- **Uso sugerido en tesis:** Análisis crítico de los resultados RNN/LSTM.
- **Limitaciones:** Cero puede ser una observación operativa legítima; no debe tratarse automáticamente como dato faltante.

## Figura 16. Resumen del experimento RNN/LSTM

- **Archivo:** `16_resumen_experimento_rnn_lstm.png`
- **Fuente:** 06_rnn_lstm_*.xlsx
- **Hoja:** resultados
- **Variables:** combinaciones, datasets, objetivos, arquitecturas y ganadores
- **Objetivo:** Cerrar la etapa con una síntesis de alcance experimental.
- **Interpretación:** El número de victorias muestra qué arquitectura obtuvo menor RMSE en más combinaciones.
- **Criterio de lectura:** Debe leerse junto con la magnitud de las diferencias, no solo con el conteo de ganadores.
- **Ecuación o fundamento:** `W_m=\sum_{d,y}I\left(m=\arg\min_j RMSE_{d,y,j}\right)`
- **Uso sugerido en tesis:** Cierre de la sección de redes recurrentes.
- **Limitaciones:** El experimento no registra múltiples ejecuciones, intervalos de confianza ni curvas de entrenamiento.
