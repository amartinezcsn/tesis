# Informe de ejecución del pipeline híbrido

DEMOSTRACIÓN SINTÉTICA: NO ES EVIDENCIA DE CUP&CAKE. Evaluación rolling exploratoria de importes registrados utilizables, no del gasto real completo. Se excluyeron 6 objetivos inciertos de las métricas; no se imputaron ni sintetizaron. Calendario con huecos sin imputar. ultimo_valor significa último importe observado disponible, no necesariamente semana anterior. MASE usa solo diferencias entre semanas calendario consecutivas observadas. La cobertura no está certificada por la mera existencia de registros.

Corte de emisión: 2023-02-13 00:00:00. Moneda: MXN nominales.
Configuraciones elegidas únicamente en validación temporal interna.
Alcance de H1: demostracion_sintetica.

## Resumen por horizonte

```
             etapa  horizonte  folds  observados  excluidos  n_metricas       rmse       mae     mase
        evaluacion          1     16          16          0        16.0 123.770756 83.357069 1.126436
        evaluacion          2     16          15          1        15.0 115.799121 80.073584 1.087402
        evaluacion          3     16          14          2        14.0 117.698985 80.463506 1.096259
        evaluacion          4     16          13          3        13.0 137.299014 99.944492 1.374446
validacion_interna          1      8           8          0         NaN        NaN       NaN      NaN
validacion_interna          2      8           8          0         NaN        NaN       NaN      NaN
validacion_interna          3      8           8          0         NaN        NaN       NaN      NaN
validacion_interna          4      8           8          0         NaN        NaN       NaN      NaN
```

## Productos

resultados.xlsx; CSV por fase; modelos.joblib; seleccion.json; hipotesis.json; dss_hibrido.json; tablero.html; manifiesto_figuras.csv.

## Limitaciones

Participaciones exponenciales sin covariables, constantes entre horizontes para un origen. No hay intervalos de predicción futuros implementados; los intervalos de H1 describen diferencias de pérdidas.
El modo forecast reproduce el origen guardado. Para emitir desde un nuevo corte se requiere nueva ingesta y ejecución con datos y cobertura actualizados.
Las figuras no se insertan automáticamente en el DOCX ni se publican en servicios externos.