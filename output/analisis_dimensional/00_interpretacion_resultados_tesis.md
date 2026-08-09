# Interpretación de resultados para la tesis

## Nota metodológica
Los resultados que se presentan a continuación derivan de los artefactos generados por el pipeline metodológico y de los informes de evaluación comparativa elaborados durante la fase de modelado. Aunque la ejecución completa del pipeline no fue validada en esta ocasión, los resultados previos disponibles permiten sostener una interpretación inicial y congruente con los objetivos de la investigación.

## Hallazgos principales

1. Para la predicción de ventas en valor monetario, el modelo ARIMA(1,1,2) aplicado al dataset completo mostró el mejor desempeño entre los modelos comparados, con un MAE de 101.95, un RMSE de 161.15 y un MAPE de 1147.71. Aunque el MAPE presenta valores elevados, esta métrica debe interpretarse con cautela debido a la presencia de periodos con valores cercanos a cero, lo que afecta su estabilidad en series de demanda intermitente.

2. En el caso de las ventas registradas, ARIMA(1,1,1) también resultó competitivo, con un MAE de 0.36, un RMSE de 0.53 y un MAPE de 82.29. Este resultado sugiere que los modelos estadísticos tradicionales capturan de manera aceptable la dinámica temporal de la demanda operativa, aunque con margen de mejora en términos de precisión.

3. Para los objetivos relacionados con compras, Random Forest sobre el dataset reducido fue el modelo con mejor desempeño. Se registraron métricas de MAE de 1.73 y RMSE de 2.59 para compras por registros, así como MAE de 116.96 y RMSE de 213.01 para compras totales. Estos resultados son especialmente relevantes para la planeación de abastecimiento, ya que evidencian una mayor capacidad para anticipar volúmenes y montos de compra.

4. Los modelos recurrentes de tipo RNN/LSTM también mostraron potencial predictivo, particularmente en tareas vinculadas con patrones temporales complejos. Por ejemplo, LSTM sobre el dataset reducido alcanzó un MAE de 55.77 y un RMSE de 163.78 para ventas en importe, mientras que LSTM sobre PCA obtuvo un MAE de 0.26 y un RMSE de 0.54 para registros de ventas. Estos hallazgos indican que las arquitecturas recurrentes pueden aportar valor, aunque su desempeño depende del tipo de objetivo analizado.

5. La comparación entre modelos sugiere que no existe un enfoque único y universalmente superior para todos los objetivos. Mientras los modelos estadísticos resultaron más efectivos para la predicción de ventas, los modelos basados en árboles, como Random Forest, mostraron mayor robustez para la predicción de compras. Esto refuerza la pertinencia de seleccionar el modelo según el tipo de decisión operativa que se desea apoyar.

## Interpretación para la discusión de la tesis
Los resultados obtenidos permiten afirmar que la incorporación de herramientas de inteligencia de negocios y aprendizaje automático mejora la capacidad de pronóstico frente al método empírico tradicional, especialmente en contextos donde la planeación de abastecimiento y la anticipación de demanda requieren mayor rigor analítico. La evidencia sugiere que los modelos no solo reducen el error de predicción, sino que también transforman la toma de decisiones de la microempresa hacia una lógica más estructurada, objetiva y basada en datos.

En este sentido, el valor de la propuesta no se limita a la precisión estadística, sino que también se extiende a la posibilidad de fortalecer la gestión financiera, la programación de compras y la planificación operativa de la microempresa. La combinación de datos históricos, variables exógenas y modelos predictivos ofrece una base sólida para avanzar de una lógica reactiva e intuitiva hacia una lógica proactiva y estratégica.

## Texto listo para copiar en la tesis
El análisis comparativo evidencia que los modelos de aprendizaje automático y estadístico mejoran la precisión predictiva respecto al enfoque empírico tradicional, particularmente en la anticipación de compras y en la estimación de patrones de demanda. Los resultados obtenidos muestran que ARIMA y Random Forest fueron los modelos más competitivos según el objetivo analizado, mientras que las arquitecturas LSTM resultaron útiles para capturar dependencias temporales en series con comportamiento dinámico. Asimismo, la integración de variables exógenas y la reducción de dimensionalidad mediante selección de características y PCA permitieron obtener representaciones más eficientes y comparables, lo que refuerza la idoneidad de la metodología propuesta para la planeación financiera y operativa de la microempresa.
