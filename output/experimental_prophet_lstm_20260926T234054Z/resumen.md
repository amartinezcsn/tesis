# Prueba aislada de Prophet y LSTM

Corrida base: `run_20260924T195600Z_86a6f5`.
Predicciones comparables: 24 por modelo.

| Modelo | RMSE global | MAE global | Cambio RMSE vs. híbrido |
|---|---:|---:|---:|
| hibrido_base | 687.294 | 464.257 | +0.00% |
| prophet | 592.366 | 342.903 | -13.81% |
| lstm | 653.377 | 380.541 | -4.93% |

Objetivos iguales a cero: 9 de 24.

| Modelo | RMSE sólo positivos | MAE sólo positivos | Victorias por error absoluto | Predicciones cero |
|---|---:|---:|---:|---:|
| hibrido_base | 857.295 | 662.499 | 10 | 0 |
| prophet | 747.364 | 525.228 | 9 | 12 |
| lstm | 826.457 | 606.962 | 5 | 1 |

Resultado exploratorio: el número de orígenes es pequeño; no constituye por sí solo evidencia suficiente para modificar la tesis.
Los modelos experimentales no se incorporaron al híbrido ni a sus artefactos.
