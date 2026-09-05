# Resultados del pronóstico semanal

## Configuración de referencia
- Línea base primaria para H1: `empirico_ultimo_valor`.
- Mejor h=1: `empirico_estacional_52s` (referencia); RMSE 695.1872; MAE 438.1884.
- Mejor h=4: `hurdle_hist_gradient` (historico_exogeno); RMSE 399.5604; MAE 318.5170.
- Consolidado mensual: 336 presupuestos históricos de cuatro semanas, cada uno como suma de h=1+h=2+h=3+h=4.

## Interpretación
- H1 y H2 se interpretan con las tablas de contraste y no sólo con el ranking.
- MAPE es diagnóstico: no se usa para seleccionar el modelo ni aceptar hipótesis.
- H1 se interpreta principalmente en h=1; h=4 se reporta como evidencia complementaria de planeación.
- El consolidado mensual no equivale a un modelo mensual independiente.