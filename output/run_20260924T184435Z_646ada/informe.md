# Informe de ejecución del pipeline híbrido

Evaluación retrospectiva; no garantiza precisión futura. Corte de emisión explícito. No es una orden de compra. Evaluación rolling exploratoria de importes registrados utilizables, no del gasto real completo. Se excluyeron 0 objetivos inciertos de las métricas; no se imputaron ni sintetizaron. Calendario con huecos sin imputar. ultimo_valor significa último importe observado disponible, no necesariamente semana anterior. MASE usa solo diferencias entre semanas calendario consecutivas observadas. La cobertura no está certificada por la mera existencia de registros.

Corte de emisión: 2025-08-04 00:00:00. Moneda: MXN nominales.
Configuraciones elegidas únicamente en validación temporal interna.
Alcance de H1: retrospectivo_exploratorio.

## Resumen por horizonte

```
             etapa  horizonte  folds  observados  excluidos  n_metricas        rmse        mae      mase
        evaluacion          1      6           6          0         6.0  609.463724 456.033397 13.460456
        evaluacion          2      6           6          0         6.0  887.763960 661.371977 15.469433
        evaluacion          3      6           6          0         6.0 1020.967296 665.024371 13.040679
        evaluacion          4      6           6          0         6.0  976.035439 729.566477 13.136436
validacion_interna          1      5           5          0         NaN         NaN        NaN       NaN
validacion_interna          2      5           5          0         NaN         NaN        NaN       NaN
validacion_interna          3      5           5          0         NaN         NaN        NaN       NaN
validacion_interna          4      5           5          0         NaN         NaN        NaN       NaN
```

## Productos

resultados.xlsx; CSV por fase; modelos.joblib; seleccion.json; hipotesis.json; dss_hibrido.json; tablero.html; manifiesto_figuras.csv.

## Limitaciones

Participaciones exponenciales sin covariables, constantes entre horizontes para un origen. No hay intervalos de predicción futuros implementados; los intervalos de H1 describen diferencias de pérdidas.
El modo forecast reproduce el origen guardado. Para emitir desde un nuevo corte se requiere nueva ingesta y ejecución con datos y cobertura actualizados.
Las figuras no se insertan automáticamente en el DOCX ni se publican en servicios externos.