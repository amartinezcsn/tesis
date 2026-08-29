# Pipeline semanal de presupuesto de abastecimiento

## Propósito

Pronosticar semanalmente el importe de compras de Cup&Cake con modelos
estadísticos y de aprendizaje automático, comparados mediante rolling-window
(ventana deslizante).

## Parámetros metodológicos

- Unidad de análisis: semana completa, lunes a domingo.
- Ventana de entrenamiento: 52 semanas.
- Horizonte principal: una semana (`h=1`).
- Horizonte complementario: cuatro semanas directas (`h=4`), reportado por
  separado de `h=1`.
- Consolidado mensual: suma de los pronósticos directos `h=1+h=2+h=3+h=4`;
  no se interpreta como un modelo mensual independiente.
- Desplazamiento de la ventana: una semana.
- Evaluación final: 16 semanas no usadas para ajustar hiperparámetros.
- H1: comparación con persistencia del último valor semanal observado.
- H2: comparación de variables históricas frente a históricas más exógenas.
- Contraste H1: Diebold-Mariano unilateral sobre pérdida cuadrática, con
  corrección de muestra finita y ajuste Holm para las comparaciones múltiples.
- Intermitencia: Croston-SBA y TSB; variantes Ridge, Random Forest y
  HistGradientBoosting con `log1p`; y modelo hurdle de dos etapas.

## Trazabilidad y disponibilidad de información

Las rutas se resuelven desde la carpeta del proyecto, por lo que el pipeline
no depende de una ubicación fija en el equipo. Al finalizar una ejecución se
genera `output/semanal/00_trazabilidad_ejecucion.json`, que registra la huella
SHA-256 de las fuentes y scripts, versiones de paquetes, semilla y parámetros.

El diccionario dentro de `dataset_modelado_semanal.xlsx` identifica la fuente,
el rezago y la disponibilidad de cada predictor. Los calendarios se usan en la
misma semana porque se conocen de antemano; INPC, temperatura y el índice de
nacimientos se desplazan una semana para representar el último valor publicado
u observado disponible al momento de pronosticar.

La referencia primaria de H1 es `empirico_ultimo_valor`: para cada semana de
prueba pronostica el importe de la semana observada inmediatamente anterior.
El promedio móvil de cuatro semanas y el ingenuo estacional de 52 semanas se
mantienen como comparadores obligatorios, no como referencias sustitutas.

## Ejecución

Instala las dependencias en un entorno aislado del proyecto. En PowerShell,
desde `C:\Python\tesis`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\codigos\requirements_pipeline_semanal.txt
```

Después ejecuta:

```powershell
.\.venv\Scripts\python.exe .\codigos\00_pipeline_semanal.py
```

Para comprobar los controles estructurales antes de una corrida completa:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\codigos\tests -v
```

## Archivos generados

| Archivo | Contenido |
|---|---|
| `input/dataset_maestro_semanal.xlsx` | Datos diarios agregados por semana. |
| `input/dataset_modelado_semanal.xlsx` | Objetivo y predictores sin fuga de información. |
| `output/semanal/01_perfil_semanal.xlsx` | Cobertura, ceros y calidad. |
| `output/semanal/02_modelos_rolling_window.xlsx` | Predicciones y métricas por horizonte, H1/H2 y consolidado de cuatro semanas. |
| `output/semanal/03_resumen_resultados_semanales.md` | Síntesis legible. |
| `output/semanal/04_dss_semanal.json` | Datos de evaluación para el DSS. |

## Límites de interpretación

El pipeline evalúa precisión del importe semanal de compras para `h=1` y,
como análisis complementario, para `h=4`. El consolidado mensual agrega cuatro
pronósticos semanales directos; no estima una serie mensual independiente. No calcula
inventario, cantidades por insumo, merma, costos de faltante ni órdenes de
compra. Una predicción futura requiere variables exógenas conocidas antes de la
semana pronosticada.

La extensión `05_extension_sintetica_compras.xlsx` se conserva fuera de las
entradas operativas. Sus filas sólo sirven para análisis de sensibilidad o
pruebas del DSS: el módulo de modelos se detiene si detecta indicadores de
origen sintético, por lo que esos valores no pueden intervenir en ajuste,
selección, evaluación ni contraste de H1/H2.

## Código heredado

Los archivos diarios previos, incluidos los que usan `rolling_origin`, PCA o
RNN/LSTM, se conservan como antecedente reproducible y no forman parte de la
ejecución semanal. La única entrada operativa es `00_pipeline_semanal.py`.
