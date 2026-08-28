# Resultados del pronóstico semanal

## Configuración de referencia
- Horizontes evaluados: H=1, H=4; el principal es H=1.
- Línea base primaria para H1: `empirico_promedio_4s`.
- Modelo con menor RMSE: `empirico_ultimo_valor` (referencia).
- RMSE: 608.0819; MAE: 452.8732; MASE: 8.5443.
- Contrastes H1 con apoyo estadístico y umbral de 20% en H=1: 0.
- Contrastes H2 con apoyo estadístico y mejora direccional en H=1: 0.

## Interpretación
- H1 y H2 se interpretan con las tablas de contraste y no sólo con el ranking.
- MAPE es diagnóstico: no se usa para seleccionar el modelo ni aceptar hipótesis.
- Las conclusiones se limitan a precisión del presupuesto semanal.