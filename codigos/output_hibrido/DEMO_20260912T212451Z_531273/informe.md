# Informe de ejecución del pipeline híbrido

DEMOSTRACIÓN SINTÉTICA: NO ES EVIDENCIA DE CUP&CAKE.

Corte de emisión: 2023-02-13 00:00:00. Moneda: MXN nominales.
Configuraciones elegidas únicamente en validación temporal interna.
Alcance de H1: demostracion_sintetica.

## Productos

resultados.xlsx; CSV por fase; modelos.joblib; seleccion.json; hipotesis.json; dss_hibrido.json; tablero.html; manifiesto_figuras.csv.

## Limitaciones

Participaciones exponenciales sin covariables, constantes entre horizontes para un origen. No hay intervalos de predicción futuros implementados; los intervalos de H1 describen diferencias de pérdidas.
El modo forecast reproduce el origen guardado. Para emitir desde un nuevo corte se requiere nueva ingesta y ejecución con datos y cobertura actualizados.
Las figuras no se insertan automáticamente en el DOCX ni se publican en servicios externos.