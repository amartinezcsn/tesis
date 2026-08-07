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
   - Entrena RNN y LSTM con ventanas temporales.
   - Se recomienda usar el dataset reducido o PCA por el numero limitado de observaciones.

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
