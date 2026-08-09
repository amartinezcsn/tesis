# Alineación con la investigación

## Pregunta de investigación

¿En qué medida un sistema de inteligencia de negocios basado en modelos de aprendizaje automático optimiza la precisión del pronóstico de demanda y fortalece la planeación de abastecimiento y financiera de una microempresa de repostería creativa en Tizayuca, Hidalgo, frente al método empírico utilizado históricamente?

## Objetivo general

Evaluar en qué medida un sistema de inteligencia de negocios basado en modelos de aprendizaje automático optimiza la precisión del pronóstico de demanda y fortalece la planeación de abastecimiento y financiera de la microempresa.

## Alineación del pipeline con los objetivos específicos

1. Registro histórico de ventas, compras y planeación empírica: la etapa de limpieza y el dataset maestro permiten describir y validar la información disponible del negocio.
2. Dataset maestro y variables exógenas: la ingeniería de características y el perfilado del dataset consolidan variables calendáricas, comerciales y de negocio para el modelado.
3. Pronóstico de demanda, ingresos y abastecimiento: los modelos estadísticos, de machine learning y recurrentes se orientan a anticipar ventas, ingresos y compras.
4. Comparación temporal y estabilidad: la validación Rolling-Origin permite evaluar precisión, robustez y generalización bajo particiones temporales.
5. Selección y ajuste de modelos: las etapas de selección, PCA y ajuste de hiperparámetros fortalecen la calidad del modelo final.
6. Comparación frente al método empírico: MAE, RMSE y MAPE se reportan para justificar la mejora predictiva frente a la línea base histórica.
7. Integración a inteligencia de negocios: los resultados se consolidan en reportes y gráficos para la toma de decisiones.
8. Impacto financiero y operativo: los hallazgos alimentan la interpretación de planeación financiera y abastecimiento.
9. Escenarios de planeación: el pipeline genera bases reproducibles para futuras simulaciones de compras, inventarios y expansión comercial.

## Evidencia de la ejecución actual

- Etapas ejecutadas: limpieza, ingenieria, perfil, multicolinealidad, seleccion, pca, modelos_rolling_origin, modelos_rolling_origin, modelos_rolling_origin, rnn_lstm, rnn_lstm, graficas_metodologia, graficas_modelos, graficas_rnn
- Variantes de modelos evaluadas: completo, reducido, pca
- RNN/LSTM: activado
- Ruta de salida: C:\Python\tesis\output\analisis_dimensional

Este archivo complementa el manifiesto y el resumen de ejecución para que la tesis quede trazable desde la pregunta inicial hasta la evidencia analítica.