# Manifiesto académico de gráficas Rolling-Origin

Fecha de generación: 2026-08-08T12:43:32

## Propósito metodológico

Documentar la comparación de métodos empíricos, modelos estadísticos y algoritmos de aprendizaje automático mediante particiones temporales expansivas. Las figuras deben interpretarse por objetivo y complementarse entre sí: precisión promedio, estabilidad, frecuencia de victorias y mejora frente a la línea base.

## Ecuaciones centrales

- $MAE=\frac{1}{n}\sum_{i=1}^{n}|y_i-\hat y_i|$
- $RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}$
- $MAPE=\frac{100}{n}\sum_{i=1}^{n}|(y_i-\hat y_i)/y_i|$
- $Train_o=\{1,\ldots,t_o\}$ y $Test_o=\{t_o+1,\ldots,t_o+h\}$

## Figura 1. Esquema de validación Rolling-Origin

- **Archivo:** `01_esquema_validacion_rolling_origin.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** resultados_por_origen
- **Variables:** fecha_inicio_prueba, fecha_fin_prueba
- **Objetivo académico:** Representar la expansión secuencial del entrenamiento y la evaluación sobre bloques futuros de 30 días.
- **Interpretación:** Cada fila corresponde a un origen distinto. La región de entrenamiento utiliza únicamente el pasado y la región de prueba contiene observaciones posteriores.
- **Criterio de lectura:** Las ventanas se desplazan cronológicamente; nunca se mezclan aleatoriamente observaciones pasadas y futuras.
- **Ecuación o fundamento:** `Train_o=\{1,\ldots,t_o\},\qquad Test_o=\{t_o+1,\ldots,t_o+h\}`
- **Uso sugerido en la tesis:** Sección de validación temporal estricta y diseño experimental.
- **Limitaciones:** La figura muestra solamente los primeros orígenes para conservar legibilidad; el archivo contiene todas las ventanas.

## Figura 2. Cobertura de orígenes por objetivo

- **Archivo:** `02_cobertura_origenes_por_objetivo.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** resultados_por_origen
- **Variables:** dataset, target, fecha_inicio_prueba
- **Objetivo académico:** Verificar que todos los objetivos y variantes se evaluaron con la misma cantidad de ventanas temporales.
- **Interpretación:** Barras iguales indican un diseño balanceado y hacen comparable el promedio de errores entre variantes.
- **Criterio de lectura:** Una diferencia en el número de orígenes debe investigarse antes de comparar métricas promedio.
- **Ecuación o fundamento:** `O_{d,y}=\left|\{o:(d,y,o)\text{ fue evaluado}\}\right|`
- **Uso sugerido en la tesis:** Auditoría del diseño experimental y reproducibilidad.
- **Limitaciones:** La igualdad en el número de ventanas no garantiza igualdad de dificultad entre objetivos.

## Figura 3. Ranking por RMSE promedio

- **Archivo:** `03_ranking_rmse_por_objetivo.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** ranking_modelos
- **Variables:** dataset, target, modelo, rmse_promedio
- **Objetivo académico:** Comparar el desempeño promedio de todos los modelos y representaciones para cada variable objetivo.
- **Interpretación:** Las barras más cortas corresponden a menor penalización cuadrática de errores y, por tanto, mejor desempeño bajo RMSE.
- **Criterio de lectura:** La comparación debe realizarse dentro de cada objetivo porque las escalas monetarias y operativas son diferentes.
- **Ecuación o fundamento:** `RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}`
- **Uso sugerido en la tesis:** Resultados comparativos de modelos y selección del candidato principal.
- **Limitaciones:** RMSE es sensible a errores extremos y no expresa por sí solo estabilidad temporal.

## Figura 4. Mejor modelo por dataset y objetivo

- **Archivo:** `04_mejor_modelo_por_dataset_objetivo.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** ranking_modelos
- **Variables:** dataset, target, modelo, rmse_promedio
- **Objetivo académico:** Resumir qué algoritmo obtiene el menor RMSE para cada combinación de representación y objetivo.
- **Interpretación:** Cada celda muestra el nombre del ganador y su RMSE. La intensidad se normaliza por objetivo para evitar comparar escalas incompatibles.
- **Criterio de lectura:** Debe observarse tanto la repetición del modelo ganador como la sensibilidad a la representación completa, reducida o PCA.
- **Ecuación o fundamento:** `m^*_{d,y}=\arg\min_m RMSE_{d,y,m}`
- **Uso sugerido en la tesis:** Síntesis ejecutiva de resultados predictivos.
- **Limitaciones:** Un ganador por promedio puede no ser el más estable en todas las ventanas.

## Figura 5. Mejora frente a la línea base empírica

- **Archivo:** `05_mejora_frente_linea_base_empirica.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** ranking_modelos
- **Variables:** rmse_promedio del modelo y del promedio empírico de 7 días
- **Objetivo académico:** Cuantificar si los modelos avanzados aportan una mejora real respecto al método empírico de referencia.
- **Interpretación:** Valores positivos indican reducción del error; valores negativos significan que la línea base empírica fue superior.
- **Criterio de lectura:** La magnitud relativa facilita comparar objetivos con escalas distintas.
- **Ecuación o fundamento:** `Mejora(\%)=\frac{RMSE_{base}-RMSE_m}{RMSE_{base}}\times100`
- **Uso sugerido en la tesis:** Contraste entre posprueba analítica y método de control.
- **Limitaciones:** La mejora porcentual puede ser inestable cuando el error base es muy pequeño.

## Figura 6. Relación MAE–RMSE

- **Archivo:** `06_relacion_mae_rmse_modelos.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** ranking_modelos
- **Variables:** mae_promedio, rmse_promedio
- **Objetivo académico:** Evaluar si el desempeño está condicionado por errores extremos además del error absoluto típico.
- **Interpretación:** Cuanto mayor sea la separación vertical respecto a la diagonal MAE=RMSE, mayor es el efecto de errores grandes.
- **Criterio de lectura:** Modelos cercanos al origen presentan menor error en ambas métricas.
- **Ecuación o fundamento:** `MAE=\frac{1}{n}\sum|e_i|,\qquad RMSE=\sqrt{\frac{1}{n}\sum e_i^2}`
- **Uso sugerido en la tesis:** Discusión de métricas y costo de errores extremos.
- **Limitaciones:** MAE y RMSE mantienen las unidades del objetivo, por lo que no deben compararse entre objetivos distintos.

## Figura 7. Concordancia entre métricas

- **Archivo:** `07_concordancia_rankings_metricas.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** ranking_modelos
- **Variables:** rankings de MAE, RMSE y MAPE
- **Objetivo académico:** Determinar si las métricas conducen a conclusiones semejantes sobre el orden de los modelos.
- **Interpretación:** Valores altos indican que dos métricas ordenan de forma parecida; valores bajos revelan criterios de evaluación diferentes.
- **Criterio de lectura:** Una baja concordancia con MAPE puede asociarse con objetivos que contienen ceros o valores pequeños.
- **Ecuación o fundamento:** `\rho_s=Corr(rank(M_a),rank(M_b))`
- **Uso sugerido en la tesis:** Justificación de una evaluación multicriterio.
- **Limitaciones:** El promedio resume múltiples objetivos y datasets, por lo que puede ocultar desacuerdos particulares.

## Figura 8. Evolución temporal del RMSE

- **Archivo:** `08_evolucion_temporal_rmse_ganadores.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** resultados_por_origen y ranking_modelos
- **Variables:** fecha_inicio_prueba, rmse del modelo ganador
- **Objetivo académico:** Evaluar la estabilidad del modelo ganador a través de diferentes periodos futuros.
- **Interpretación:** Picos de RMSE identifican ventanas difíciles, cambios de régimen o eventos no capturados por el modelo.
- **Criterio de lectura:** Una línea baja y estable es preferible a un promedio bajo acompañado de episodios extremos.
- **Ecuación o fundamento:** `RMSE_o=\sqrt{\frac{1}{h}\sum_{i=1}^{h}(y_{o,i}-\hat y_{o,i})^2}`
- **Uso sugerido en la tesis:** Análisis de robustez temporal y riesgo predictivo.
- **Limitaciones:** La figura sigue al ganador promedio; otro modelo podría superar al ganador en ventanas específicas.

## Figura 9. Distribución del RMSE por modelo

- **Archivo:** `09_distribucion_rmse_por_modelo.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** resultados_por_origen
- **Variables:** modelo, rmse
- **Objetivo académico:** Comparar mediana, dispersión y asimetría del error a lo largo de todos los orígenes.
- **Interpretación:** La línea central es la mediana; la caja representa el 50 % central de errores. Cajas más compactas indican mayor estabilidad.
- **Criterio de lectura:** La comparación global mezcla objetivos de distintas escalas y debe complementarse con las figuras por objetivo.
- **Ecuación o fundamento:** `IQR_{RMSE}=Q_{0.75}(RMSE)-Q_{0.25}(RMSE)`
- **Uso sugerido en la tesis:** Discusión de estabilidad y variabilidad del desempeño.
- **Limitaciones:** Al mezclar escalas, los objetivos monetarios tienen mayor peso visual que los objetivos de conteo.

## Figura 10. Estabilidad mediante coeficiente de variación

- **Archivo:** `10_estabilidad_modelos_cv_rmse.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** resultados_por_origen
- **Variables:** media y desviación estándar del RMSE
- **Objetivo académico:** Identificar el modelo con menor variabilidad relativa del error en cada problema.
- **Interpretación:** Valores pequeños indican que el error cambia menos entre ventanas respecto a su nivel promedio.
- **Criterio de lectura:** Debe analizarse junto con el RMSE medio, porque un modelo estable puede ser consistentemente impreciso.
- **Ecuación o fundamento:** `CV_{RMSE}=\frac{s(RMSE_o)}{\overline{RMSE}_o}`
- **Uso sugerido en la tesis:** Evaluación de robustez y riesgo operativo.
- **Limitaciones:** El CV puede ser inestable cuando el RMSE medio se aproxima a cero.

## Figura 11. Ventanas ganadas por modelo

- **Archivo:** `11_ventanas_ganadas_por_modelo.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** resultados_por_origen
- **Variables:** modelo y RMSE mínimo por origen
- **Objetivo académico:** Medir con qué frecuencia cada modelo fue el mejor en una ventana temporal concreta.
- **Interpretación:** Un alto número de victorias indica capacidad de adaptación a distintos periodos, aunque no considera la magnitud de las derrotas.
- **Criterio de lectura:** Debe contrastarse con el RMSE promedio y la estabilidad.
- **Ecuación o fundamento:** `W_m=\sum_o I\left(m=\arg\min_j RMSE_{j,o}\right)`
- **Uso sugerido en la tesis:** Comparación dinámica de modelos.
- **Limitaciones:** Los empates numéricos se asignan al primer mínimo encontrado.

## Figura 12. Sensibilidad a la representación del dataset

- **Archivo:** `12_sensibilidad_modelos_dataset.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** ranking_modelos
- **Variables:** modelo, dataset, rmse_promedio normalizado
- **Objetivo académico:** Evaluar si un modelo mejora o empeora al utilizar predictores completos, seleccionados o componentes PCA.
- **Interpretación:** Valores cercanos a uno indican proximidad al mejor resultado del objetivo; valores mayores representan pérdida relativa de desempeño.
- **Criterio de lectura:** Las líneas base y modelos univariados pueden mostrar resultados idénticos porque no usan los predictores exógenos.
- **Ecuación o fundamento:** `RMSE^{rel}_{d,y,m}=\frac{RMSE_{d,y,m}}{\min_{d,m}RMSE_{d,y,m}}`
- **Uso sugerido en la tesis:** Comparación entre dataset completo, reducido y PCA.
- **Limitaciones:** El promedio entre objetivos resume escalas después de normalizar, pero puede ocultar efectos específicos.

## Figura 13. Método empírico frente a modelos avanzados

- **Archivo:** `13_empirico_vs_modelos_avanzados.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** ranking_modelos
- **Variables:** mejor rmse_promedio por familia
- **Objetivo académico:** Contrastar directamente la línea base operativa con el mejor enfoque estadístico o de aprendizaje automático.
- **Interpretación:** El punto más cercano a cero identifica la familia superior. Segmentos cortos indican que la complejidad adicional produce poca ganancia.
- **Criterio de lectura:** La comparación se realiza por objetivo y dataset para mantener la escala.
- **Ecuación o fundamento:** `\Delta RMSE=RMSE^*_{empírico}-RMSE^*_{avanzado}`
- **Uso sugerido en la tesis:** Contraste del grupo de control frente a la intervención analítica.
- **Limitaciones:** La categoría avanzada agrupa modelos con supuestos y complejidad muy diferentes.

## Figura 14. Diagnóstico del MAPE

- **Archivo:** `14_diagnostico_mape_por_objetivo.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** resultados_por_origen
- **Variables:** target, modelo, mape
- **Objetivo académico:** Mostrar la sensibilidad del error porcentual ante objetivos con ceros o valores pequeños.
- **Interpretación:** MAPE elevado o no finito puede reflejar denominadores cercanos a cero más que un deterioro proporcional ordinario.
- **Criterio de lectura:** Para series intermitentes deben priorizarse MAE y RMSE y considerar métricas complementarias como WAPE, sMAPE o MASE.
- **Ecuación o fundamento:** `MAPE=\frac{100}{n}\sum_i\left|\frac{y_i-\hat y_i}{y_i}\right|`
- **Uso sugerido en la tesis:** Discusión crítica de métricas de evaluación.
- **Limitaciones:** La implementación excluye denominadores cercanos a cero; aun así, valores pequeños pueden inflar el porcentaje.

## Figura 15. Orígenes temporales más difíciles

- **Archivo:** `15_origenes_temporales_mas_dificiles.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** resultados_por_origen
- **Variables:** mínimo RMSE por dataset, objetivo y fecha de inicio
- **Objetivo académico:** Detectar periodos donde todos los modelos enfrentaron mayor dificultad predictiva.
- **Interpretación:** Una barra extensa indica que incluso el mejor algoritmo disponible cometió errores elevados en esa ventana.
- **Criterio de lectura:** Estas fechas deben contrastarse con eventos comerciales, cambios operativos, datos atípicos o rupturas estructurales.
- **Ecuación o fundamento:** `D_o=\min_m RMSE_{m,o}`
- **Uso sugerido en la tesis:** Análisis de errores, eventos atípicos y limitaciones del modelo.
- **Limitaciones:** Los valores monetarios dominan por escala; la interpretación debe realizarse dentro del objetivo correspondiente.

## Figura 16. Score multicriterio de modelos

- **Archivo:** `16_score_multicriterio_modelos.png`
- **Fuente:** 05_modelos_rolling_origin_completo/reducido/pca.xlsx
- **Hoja:** ranking_modelos
- **Variables:** MAE, RMSE y MAPE normalizados
- **Objetivo académico:** Integrar las tres métricas en una síntesis comparable dentro de cada objetivo y dataset.
- **Interpretación:** Un score menor indica un balance más favorable entre error absoluto, penalización cuadrática y error relativo.
- **Criterio de lectura:** El resultado debe contrastarse con estabilidad temporal y mejora frente a la línea base.
- **Ecuación o fundamento:** `S_m=\frac{1}{3}\left(MAE_m^{norm}+RMSE_m^{norm}+MAPE_m^{norm}\right)`
- **Uso sugerido en la tesis:** Selección multicriterio del modelo candidato.
- **Limitaciones:** La ponderación es uniforme y MAPE puede ser poco fiable en series con ceros; el score es una síntesis exploratoria.
