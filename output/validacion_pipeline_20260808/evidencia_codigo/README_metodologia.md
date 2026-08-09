# Metodologia propuesta para analisis dimensional y modelado

## Contexto

El dataset `dataset_modelado_diario.xlsx` contiene 1,584 observaciones diarias y 276 columnas. Incluye variables calendarias, exogenas, rezagos, ventanas moviles, composicion de ventas, composicion de compras y cuatro variables objetivo.

Para la tesis, si es necesario reducir dimensionalidad, pero no debe hacerse a ciegas. La reduccion debe conservar tres criterios:

1. Capacidad predictiva para demanda, ingresos y compras.
2. Interpretabilidad financiera y operativa para Cup&Cake.
3. Validacion temporal sin fuga de informacion.

## Orden recomendado de ejecucion

0. `config_metodologia.py`
   - Centraliza rutas, objetivos, particiones temporales y reglas de clasificacion.

1. `01_perfil_dataset_y_dimensiones.py`
   - Describe cada variable.
   - Agrupa columnas por dimension.
   - Detecta variables constantes, nulos y concentracion de ceros.

2. `02_diagnostico_multicolinealidad.py`
   - Identifica redundancia entre variables.
   - Propone variables conservadas/eliminadas por correlacion alta.
   - Calcula VIF si esta instalado `statsmodels`.

3. `03_seleccion_caracteristicas_dataset_reducido.py`
   - Genera ranking de variables por objetivo.
   - Construye `dataset_reducido`.
   - Usa solo correlacion si no hay `scikit-learn`; usa metodos mas robustos si esta disponible.

4. `04_pca_reduccion_componentes.py`
   - Genera un dataset alternativo con componentes principales.
   - Util para comparar precision, aunque menos interpretable.

5. `05_modelos_estadisticos_ml_rolling_origin.py`
   - Compara metodo empirico, ARIMA/SARIMA, regresion lineal, arboles y random forest.
   - Ajusta hiperparametros por objetivo mediante origenes temporales anteriores.
   - Reserva los ultimos origenes para evaluar combinaciones no vistas durante el ajuste.
   - Usa validacion Rolling-Origin.
   - Reporta MAE, RMSE y MAPE.

La busqueda se ejecuta desde el pipeline maestro de forma predeterminada. Su costo
puede controlarse con `--origenes-ajuste 4 --origenes-evaluacion 3`, o puede
omitirse con `--sin-ajuste-hiperparametros`. Cada archivo de resultados agrega
las hojas `mejores_hiperparametros`, `resumen_ajuste` y `detalle_ajuste`.

6. `06_rnn_lstm_dataset_reducido.py`
   - Ajusta RNN y LSTM con un bloque de validacion temporal anterior a la prueba.
   - Reentrena cada configuracion ganadora con todo el historial de desarrollo.
   - Exporta resultados, detalle del ajuste, mejores hiperparametros, predicciones y la mejor configuracion.
   - Se recomienda usar el dataset reducido o PCA por el numero limitado de observaciones.

7. `09_generar_graficas_manifiesto_pca.py`
   - Genera la evidencia visual de limpieza, ingenieria, perfil, seleccion y PCA.

8. `10_generar_graficas_rolling_origin.py`
   - Consolida los tres datasets y genera 16 graficas de evaluacion temporal.

9. `11_generar_graficas_rnn_lstm.py`
   - Genera 16 graficas comparativas de RNN/LSTM.

El pipeline maestro ejecuta tambien estas tres etapas y guarda las graficas bajo
`graficas_metodologia`, `graficas_rolling_origin` y `graficas_rnn_lstm` dentro
del directorio de salida. Los archivos
`00_mejores_configuraciones_globales_modelos.xlsx` y
`00_mejores_configuraciones_globales_rnn_lstm.xlsx` identifican la mejor
combinacion de dataset, modelo e hiperparametros para cada objetivo.

## Recomendacion para la tesis

Compara tres versiones del dataset:

- Dataset completo: maxima informacion, mayor riesgo de redundancia.
- Dataset reducido: mejor equilibrio entre interpretabilidad y precision.
- Dataset PCA: menor dimensionalidad, menor interpretabilidad.

La seleccion final debe basarse en validacion temporal y no solo en el mejor ajuste interno. El resultado defendible sera el modelo/dataset que reduzca MAE, RMSE y MAPE frente al metodo empirico historico y mantenga estabilidad en varios origenes de pronostico.

## Dependencias sugeridas

```bash
pip install pandas numpy openpyxl scikit-learn statsmodels tensorflow
```

Si no se usaran redes neuronales, `tensorflow` puede omitirse.
