# Informe de ejecución del pipeline híbrido

DEMOSTRACIÓN SINTÉTICA: NO ES EVIDENCIA DE CUP&CAKE. Evaluación rolling exploratoria de importes registrados utilizables, no del gasto real completo. Se excluyeron 0 objetivos inciertos de las métricas; no se imputaron ni sintetizaron. Calendario con huecos sin imputar. ultimo_valor significa último importe observado disponible, no necesariamente semana anterior. MASE usa solo diferencias entre semanas calendario consecutivas observadas. La cobertura no está certificada por la mera existencia de registros.

Corte de emisión: 2023-02-13 00:00:00. Moneda: MXN nominales.
Configuraciones elegidas únicamente en validación temporal interna.
Alcance de H1: demostracion_sintetica.

## Resumen por horizonte

```
             etapa  horizonte  folds  observados  excluidos  n_metricas       rmse        mae     mase
        evaluacion          1      6           6          0         6.0 166.814934 117.307505 1.573642
        evaluacion          2      6           6          0         6.0 172.357226 118.796273 1.509114
        evaluacion          3      6           6          0         6.0  71.045631  55.202430 0.727322
        evaluacion          4      6           6          0         6.0  96.578074  81.067025 1.057107
validacion_interna          1      5           5          0         NaN        NaN        NaN      NaN
validacion_interna          2      5           5          0         NaN        NaN        NaN      NaN
validacion_interna          3      5           5          0         NaN        NaN        NaN      NaN
validacion_interna          4      5           5          0         NaN        NaN        NaN      NaN
```

## Productos

resultados.xlsx; CSV por fase; modelos.joblib; seleccion.json; hipotesis.json; dss_hibrido.json; tablero.html; manifiesto_figuras.csv.

## Limitaciones

Participaciones exponenciales sin covariables, constantes entre horizontes para un origen. No hay intervalos de predicción futuros implementados; los intervalos de H1 describen diferencias de pérdidas.
El modo forecast reproduce el origen guardado. Para emitir desde un nuevo corte se requiere nueva ingesta y ejecución con datos y cobertura actualizados.
Las figuras no se insertan automáticamente en el DOCX ni se publican en servicios externos.