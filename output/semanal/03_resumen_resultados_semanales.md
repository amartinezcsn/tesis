# Resultados del pronóstico semanal

## Configuración de referencia
- Línea base primaria para H1: `empirico_ultimo_valor`.
- Mejor h=1: `ridge` (historico); RMSE 502.1078; MAE 325.9802.
- Mejor h=4: `empirico_promedio_4s` (referencia); RMSE 652.5237; MAE 427.6304.
- Consolidado mensual: 336 presupuestos históricos de cuatro semanas, cada uno como suma de h=1+h=2+h=3+h=4.

## Interpretación
- H1 y H2 se interpretan con las tablas de contraste y no sólo con el ranking.
- MAPE es diagnóstico: no se usa para seleccionar el modelo ni aceptar hipótesis.
- H1 se interpreta principalmente en h=1; h=4 se reporta como evidencia complementaria de planeación.
- El consolidado mensual no equivale a un modelo mensual independiente.