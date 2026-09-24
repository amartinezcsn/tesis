# Pipeline híbrido Rev44

Para explicar el recorrido completo en la predefensa, consultar
[FLUJO_PIPELINE_HIBRIDO_PREDEFENSA.md](FLUJO_PIPELINE_HIBRIDO_PREDEFENSA.md).

El diagnóstico del 12 de septiembre describía el flujo anterior, archivado en `legados/`. La integración estadística y ML está en `hibrido/models.py` y `hibrido/experiment.py`. `00_pipeline_hibrido.py` es la única entrada operativa, `01_normalizacion.py` normaliza descripciones y `02_config_hibrido.json` fija el experimento. Los módulos internos de `hibrido/` conservan nombres importables.

| Orden | Archivo activo | Función |
| --- | --- | --- |
| 00 | `00_pipeline_hibrido.py` | CLI principal: auditoría, demostración, entrenamiento y pronóstico |
| 01 | `01_normalizacion.py` | Limpieza de descripciones al leer compras |
| 02 | `02_config_hibrido.json` | Fuentes y parámetros de la corrida real |

`hibrido/` contiene funciones importadas por la CLI; `tests/test_hibrido*.py` verifica la ejecución. Las versiones de dependencias están en `requirements_hibrido.txt`.

> El protocolo de tesis conserva el calendario semanal completo y representa las semanas inciertas como valores ausentes. Consultar [protocolo de calendario con faltantes](README_hibrido_faltantes.md). La implementación anterior de ventana continua fue retirada del camino ejecutable.

Implementación inicial ejecutable del plan `documentacion/PLAN_PIPELINE_HIBRIDO_Rev44.md`. Predice el total semanal nominal, estima participaciones y distribuye el presupuesto entre insumos. El resultado científico puede ser desfavorable a H1; no se reajusta el procedimiento para forzar una mejora.

## Ejecución

Desde `codigos/`, con Python 3.10 y un entorno aislado:

```powershell
py -3.10 -m venv .venv_hibrido
.\.venv_hibrido\Scripts\python.exe -m pip install -r requirements_hibrido.txt
.\.venv_hibrido\Scripts\python.exe 00_pipeline_hibrido.py audit
.\.venv_hibrido\Scripts\python.exe 00_pipeline_hibrido.py demo
.\.venv_hibrido\Scripts\python.exe -m unittest discover -s tests -p "test_hibrido*.py" -v
```

Instalar `requirements_hibrido.txt` en el entorno antes de ejecutar. El comando `audit` no entrena. `demo` crea sus propios datos sintéticos en una carpeta DEMO y marca todas las figuras, artefactos, reportes y predicciones; nunca los trata como evidencia de Cup&Cake.

Para entrenar con registros reales:

```powershell
.\.venv_hibrido\Scripts\python.exe 00_pipeline_hibrido.py run --config 02_config_hibrido.json
```

La fuente original `datasets/xlsx/Compras.xlsx` quedó fijada por SHA-256 y sus 12 filas duplicadas se conservan por decisión del usuario del 19 de septiembre de 2026. La corrida real completada está en `outputs/ejecucion_real_20260919/run_20260919T212455Z_f0255d/`. La decisión sobre duplicados está documentada en `outputs/revision_datos_20260919/decision_duplicados.md`.

## Preparación de datos reales

1. Ejecutar `audit` y revisar `auditoria.json`, `compras_auditadas.csv` y `registros_pendientes.csv`. Las 12 filas duplicadas del archivo actual ya están autorizadas y permanecen en el cálculo. Cualquier nueva incidencia exige una decisión documentada.
2. La fuente y hoja actuales constan en `02_config_hibrido.json`, con su SHA-256. Un cambio posterior del archivo invalida el hash y requiere una auditoría nueva.
3. Completar `catalogo_PARA_REVISAR.csv`: homologar descripciones a `insumo_id` y aprobar cada correspondencia. `otros` y `total` son nombres reservados. No confundir clasificación comercial con insumo sin revisarlo.
4. Completar `cobertura_PARA_REVISAR.csv`: cada lunes requiere estado, evidencia y fecha de revisión. La configuración real no admite `cero_confirmado` como objetivo válido; las semanas inciertas permanecen ausentes. Siete filas de calendario no prueban cobertura.
5. Guardar los archivos revisados en las rutas `catalog` y `coverage`; pueden estar en `input/hibrido/`. Definir `start` y `end` como lunes inclusivos del periodo aprobado. No usar la selección del periodo para buscar resultados favorables.
6. Revisar el umbral de selección (80% propuesto), el holdout y el protocolo inferencial. La evaluación implementada es retrospectiva y exploratoria; no se presenta como confirmación independiente.

El archivo `outputs/revision_datos_20260919/revision_catalogo_cobertura_trazada.xlsx` contiene las hojas `Catalogo` y `Cobertura`, usadas directamente por la configuración actual. Las 470 filas incluidas tienen `insumo_id`; 319 asignaciones nuevas se documentan en `asignaciones_insumo_id.json` y su trazabilidad completa a la fuente en `evidencias_catalogo.json`. Las semanas del 2023-08-28 (cinco importes cero) y 2024-01-01 (sin compras de insumos incluidas) están marcadas `incierta` conforme a la decisión de no considerar válidos los ceros. Las inferencias de equivalencia entre descripciones se declaran en el archivo de trazabilidad.

Las rutas relativas se resuelven desde la raíz del proyecto, no desde el directorio de ejecución. Las fuentes brutas, tesis y salidas anteriores no se sobrescriben.

## Contratos opcionales

Exógenas: CSV/XLSX con `variable`, `fecha_referencia`, `available_at`, `valor`, `fuente`, `version`, `tipo`. Los tipos son `observada`, `pronostico` o `calendario`. Para una variable se usa una previsión/calendario de la semana objetivo que ya existía en origen; en su defecto, la última observación disponible anterior al origen. Sin registro válido queda ausente, no se convierte en cero observado. Las fechas deben ser coherentes, sin mezclar zonas horarias.

Ventas: tabla semanal `semana_inicio`, `importe_nominal`, `available_at`, con un lunes único por semana y publicación no anterior al cierre. Se agregan como rezagos opcionales; ventas no es una variable objetivo. No se usa el maestro diario con importes reales como sustituto nominal.

Si no se proporcionan estas fuentes, el modelo funciona con compras históricas y calendario. No inventa clima futuro ni obliga a generar exógenas artificiales.

## Modelado y separación temporal

- `01_normalizacion.py` conserva la normalización de descripciones del código histórico sin sus imputaciones o deflactores. Los rezagos, referencias y componentes semanales tienen contratos temporales explícitos en `hibrido/`.
- Historia creciente por origen, sin comprimir semanas ni imputar objetivos. Los modelos ML exigen un mínimo configurable de etiquetas observadas.
- La configuración principal usa ventana móvil de 52 semanas, avance de 3 semanas y reserva de 20 semanas objetivo. El ajuste usa cinco orígenes internos purgados; la cantidad utilizable se informa por horizonte.
- El total se forma después de excluir las categorías configuradas (incluidas IMPUTADO/IMPUTADOS y OTROS); `exclusiones_compras.csv` conserva el importe y conteo excluidos. Una semana con transacciones solo excluidas es cero MXN elegible; sin transacciones fuente permanece ausente.
- Componentes estadísticos: SARIMAX AR(1), ARIMA(1,1,1), SES, Holt amortiguado y naive estacional. Componentes ML: HistGradientBoosting, Random Forest, Ridge y MLP pequeña regularizada. También se evalúan correctores residuales RF y MLP sobre ARIMA mediante pronósticos de origen móvil fuera de muestra.
- Los predictores son historia disponible, antigüedad, resúmenes de 4/8/12 semanas, calendario, rezagos de ventas y fuentes opcionales disponibles en cada origen. Las variables futuras se usan únicamente si estaban disponibles en el origen.
- Selección de componente estadístico, componente ML y peso por horizonte en validación interna. Pesos candidatos 0.25, 0.50 y 0.75; no se llama híbrido a un componente puro. Los fallos invalidan la configuración durante selección y detienen la evaluación si afectan al modelo fijado; no se ocultan con un promedio bajo otro nombre.
- Categorías principales se fijan solo con desarrollo. La ventana de composición es independiente de la ventana del total y, por defecto, creciente; requiere ocho semanas positivas elegibles para puntuar un fold. Referencia: promedio histórico; candidato: promedio exponencial con alfa seleccionado internamente. Las participaciones principales se calculan sobre el total elegible y el remanente se informa como `RESTO_ELEGIBLE`, no como categoría fuente OTROS.
- La configuración real no acepta importes cero como objetivos válidos (`zero_targets_valid: false`). Las semanas afectadas quedan `incierta` y mantienen su posición temporal ausente; los importes originales permanecen en la auditoría.
- RMSE y MAE monetarios, MASE con escala del entrenamiento y MAE porcentual por insumo y macro. H1 compara dos pérdidas en h=1. Intervalos exploratorios de diferencia por bootstrap circular pareado con bloque fijo y corrección Bonferroni para dos componentes; sin garantía inferencial con pocas observaciones. El test final no elige el modelo operativo.

## Productos por ejecución

Cada corrida `audit`, `demo`, `run` o `forecast` se guarda en una carpeta nueva bajo `C:\Python\tesis\output\<run_id>\`, incluso si se bloquea. La ruta de salida es fija: `--output` ya no se admite. `forecast` guarda `pronostico_futuro.csv` y su manifiesto en lugar de imprimir el CSV. Las corridas anteriores no se mueven ni sobrescriben.

- Auditoría, pendientes, plantillas de cobertura/catálogo y panel reconciliado.
- Particiones, selección interna, métricas, predicciones, participaciones y asignaciones en CSV y Excel.
- `seleccion.json`, `hipotesis.json`, `modelos.joblib`, `pronostico_futuro.csv`, `pronostico_4_semanas.csv`.
- `dss_hibrido.json`, `tablero.html`, `informe.md`.
- Figuras PNG 300 dpi y SVG, CSV de respaldo, guía de inserción y manifiesto F00–F22.
- `manifiesto.json`: configuración, hashes de fuentes y código, versiones, productos y estado de corrida.

Los artefactos joblib solo deben cargarse si son de confianza: no abrir modelos enviados por terceros desconocidos.

```powershell
.\.venv_hibrido\Scripts\python.exe 00_pipeline_hibrido.py forecast --artifact ..\output\<run_id>\modelos.joblib
```

Este comando reproduce la emisión del corte guardado, comprobada contra el modelo en memoria. No pretende actualizar un modelo con datos que no recibió. Para un nuevo corte, actualizar fuentes y cobertura y ejecutar una nueva corrida. Su origen es el lunes siguiente al último dato auditado, no necesariamente la fecha actual del equipo.

## Gráficas y Word

El catálogo registra 23 figuras potenciales. Las omisiones son explícitas: F08 exige tres ciclos anuales en desarrollo; F11 no se fabrica cuando no existe selección de variables por frecuencia; F21 requiere captura de navegador de la interfaz real. F00, F10 y F12 son esquemas del procedimiento, no evidencia de entrenamiento. Los demás gráficos se producen únicamente cuando existe información válida.

`guia_figuras.md` y los manifiestos señalan archivos y capítulos sugeridos. No se inserta contenido automáticamente en la tesis. Debe revisarse legibilidad y procedencia antes de la edición controlada del DOCX más reciente. No utilizar figuras DEMO como resultados de investigación.

## Tablero existente

Se añadió un constructor compatible con el nuevo contrato, sin sustituir ni publicar el tablero heredado:

```powershell
cd dashboard
npm run build:hibrido -- ..\output\<run_id>
node --test tests/hibrido.test.mjs
```

Produce un Worker estático local en `dashboard/dist/hibrido/`; no lo despliega. También puede abrirse directamente el `tablero.html` de la ejecución. El build solo acepta corridas completadas y preserva las advertencias de demostración.

## Legado y alcance de la migración

La entrada científica es `00_pipeline_hibrido.py`. No requiere ejecutar el maestro diario ni los experimentos de PCA/RNN. Los scripts anteriores se conservan en `legados/` como antecedentes y no deben usarse para evaluar H1 de Rev44. Las fuentes, imágenes y resultados históricos permanecen en sus rutas.

Pendientes de ampliación: modelos de composición con covariables por horizonte, intervalos de predicción futuros, captura automatizada F21, inserción editorial en Word y actualización incremental con configuración congelada. No se prometen como funciones implementadas en esta versión inicial.
