# Revision tecnica del pipeline de tesis

Fecha de validacion: 2026-08-08

## Resultado

El flujo fue ejecutado desde seleccion de caracteristicas hasta la generacion
de graficas con cero errores de etapa. Tambien se ejecuto previamente desde
perfil para validar la integracion de los codigos 03 a 11.

## Correcciones verificadas

- El pipeline maestro integra los generadores 09, 10 y 11.
- LassoCV usa `TimeSeriesSplit` y no particiones aleatorias.
- Los candidatos tradicionales deben cubrir todos los origenes de ajuste.
- Los tres origenes finales quedan fuera del ajuste de hiperparametros.
- Cada libro 05 incluye `mejor_configuracion` y `cobertura_objetivos`.
- RNN/LSTM usa validacion temporal interna, seleccion por RMSE, reentrenamiento
  con el historial de desarrollo y prueba final intacta.
- Cada libro 06 incluye resultados, hiperparametros, detalle de ajuste, ganador
  por objetivo y 90 predicciones de prueba por modelo/objetivo.
- El dataset reducido conserva 80 de 271 predictores (reduccion de 70.5%).
- PCA conserva 130 componentes para alcanzar el 95% de varianza configurado.
- Los objetivos de compras excluyen 305 dias terminales sin cobertura; su fecha
  efectiva final es 2025-07-30. Ventas conserva la fecha final 2026-05-31.

## Integridad de salidas

- 3 libros Rolling-Origin: 84 resultados, 76 candidatos resumidos y 304
  evaluaciones de candidato por libro.
- 2 libros RNN/LSTM: 8 resultados, 16 candidatos y 720 predicciones por libro.
- 86 PNG metodologicos, 16 PNG Rolling-Origin y 16 PNG RNN/LSTM.
- Todos los PNG abren correctamente y superan 1000 x 700 pixeles.
- Las matrices de ganadores fueron verificadas visualmente y ajustadas para
  mantener contraste legible.

## Mejores configuraciones tradicionales por objetivo

| Objetivo | Dataset | Modelo | Hiperparametros | RMSE promedio |
|---|---|---|---|---:|
| Registros de compras | reducido | Random Forest | n_estimators=150, max_depth=None, min_samples_leaf=5, max_features=sqrt | 2.593218 |
| Importe de compras | reducido | Random Forest | n_estimators=150, max_depth=None, min_samples_leaf=5, max_features=sqrt | 213.014385 |
| Importe de ventas | completo | ARIMA | order=(1,1,2) | 161.149341 |
| Registros de ventas | completo | ARIMA | order=(1,1,1) | 0.525051 |

## Mejores configuraciones RNN/LSTM por objetivo

| Objetivo | Dataset | Modelo | Configuracion | Mejor epoca | RMSE |
|---|---|---|---|---:|---:|
| Registros de compras | PCA | RNN simple | lookback=28, units=32, dense=16, lr=0.001, batch=16 | 12 | 2.747907 |
| Importe de compras | PCA | RNN simple | lookback=14, units=24, dense=12, lr=0.001, batch=16 | 13 | 239.714050 |
| Importe de ventas | reducido | LSTM | lookback=28, units=32, dense=16, lr=0.001, batch=16 | 23 | 163.776916 |
| Registros de ventas | PCA | LSTM | lookback=28, units=32, dense=16, lr=0.001, batch=16 | 7 | 0.544629 |

## Conclusion comparativa

Los modelos tradicionales obtienen menor RMSE que RNN/LSTM en los cuatro
objetivos. Con la evidencia disponible, Random Forest es la mejor opcion para
compras y ARIMA para ventas. Las redes recurrentes no justifican sustituir esas
configuraciones en esta muestra; quedan como comparacion metodologica.

Las advertencias de convergencia de Lasso, VIF infinito, retracing de TensorFlow
y localizacion automatica de fechas no detuvieron etapas ni produjeron valores
no finitos en las metricas finales. Deben conservarse en la bitacora como
limitaciones numericas y de rendimiento, no como errores de salida.
