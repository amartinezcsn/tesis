# Informe de ejecución del pipeline híbrido

Evaluación retrospectiva; no garantiza precisión futura. Corte de emisión explícito. No es una orden de compra. Evaluación rolling exploratoria de importes registrados utilizables, no del gasto real completo. Se excluyeron 6 objetivos inciertos de las métricas; no se imputaron ni sintetizaron. Calendario con huecos sin imputar. ultimo_valor significa último importe observado disponible, no necesariamente semana anterior. MASE usa solo diferencias entre semanas calendario consecutivas observadas. La cobertura no está certificada por la mera existencia de registros.

Corte de emisión: 2024-07-01 00:00:00. Moneda: MXN nominales.
Configuraciones elegidas únicamente en validación temporal interna.
Alcance de H1: retrospectivo_exploratorio.

## Resumen por horizonte

```
             etapa  horizonte  folds  observados  excluidos  n_metricas       rmse        mae     mase
        evaluacion          1      2           1          1           1 271.186074 271.186074 0.392901
        evaluacion          2      2           1          1           1 495.250575 495.250575 0.717532
        evaluacion          3      2           0          2           0        NaN        NaN      NaN
        evaluacion          4      2           2          0           2 377.363225 334.107191 0.491926
validacion_interna          1      2           2          0           1 271.186074 271.186074 0.392901
validacion_interna          2      2           0          2           1 495.250575 495.250575 0.717532
validacion_interna          3      2           2          0           0        NaN        NaN      NaN
validacion_interna          4      2           2          0           2 377.363225 334.107191 0.491926
```

## Productos

resultados.xlsx; CSV por fase; modelos.joblib; seleccion.json; hipotesis.json; dss_hibrido.json; tablero.html; manifiesto_figuras.csv.

## Limitaciones

Participaciones exponenciales sin covariables, constantes entre horizontes para un origen. No hay intervalos de predicción futuros implementados; los intervalos de H1 describen diferencias de pérdidas.
El modo forecast reproduce el origen guardado. Para emitir desde un nuevo corte se requiere nueva ingesta y ejecución con datos y cobertura actualizados.
Las figuras no se insertan automáticamente en el DOCX ni se publican en servicios externos.