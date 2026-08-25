# Pipeline semanal de presupuesto de abastecimiento

## Propósito

Pronosticar semanalmente el importe de compras de Cup&Cake con modelos
estadísticos y de aprendizaje automático, comparados mediante rolling-window
(ventana deslizante).

## Parámetros metodológicos

- Unidad de análisis: semana completa, lunes a domingo.
- Ventana de entrenamiento: 52 semanas.
- Horizonte principal: una semana.
- Desplazamiento de la ventana: una semana.
- Evaluación final: 16 semanas no usadas para ajustar hiperparámetros.
- H1: comparación con promedio móvil de cuatro semanas.
- H2: comparación de variables históricas frente a históricas más exógenas.

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
| `output/semanal/02_modelos_rolling_window.xlsx` | Predicciones, métricas y H1/H2. |
| `output/semanal/03_resumen_resultados_semanales.md` | Síntesis legible. |
| `output/semanal/04_dss_semanal.json` | Datos de evaluación para el DSS. |

## Límites de interpretación

El pipeline evalúa precisión del importe semanal de compras. No calcula
inventario, cantidades por insumo, merma, costos de faltante ni órdenes de
compra. Una predicción futura requiere variables exógenas conocidas antes de la
semana pronosticada.

## Código heredado

Los archivos diarios previos, incluidos los que usan `rolling_origin`, PCA o
RNN/LSTM, se conservan como antecedente reproducible y no forman parte de la
ejecución semanal. La única entrada operativa es `00_pipeline_semanal.py`.
