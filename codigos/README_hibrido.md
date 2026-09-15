# Pipeline híbrido Rev44

Implementación inicial ejecutable del plan `documentacion/PLAN_PIPELINE_HIBRIDO_Rev44.md`. Predice el total semanal nominal, estima participaciones y distribuye el presupuesto entre insumos. El resultado científico puede ser desfavorable a H1; no se reajusta el procedimiento para forzar una mejora.

## Ejecución

Desde la raíz del proyecto, con Python 3.12 y un entorno aislado:

```powershell
python -m venv .venv_hibrido
.\.venv_hibrido\Scripts\python.exe -m pip install -r codigos\requirements_hibrido.txt
.\.venv_hibrido\Scripts\python.exe codigos\00_pipeline_hibrido.py audit
.\.venv_hibrido\Scripts\python.exe codigos\00_pipeline_hibrido.py demo
.\.venv_hibrido\Scripts\python.exe -m unittest discover -s codigos\tests -p test_hibrido.py -v
```

El entorno `.venv_hibrido` de esta entrega ya fue instalado para las pruebas. El comando `audit` no entrena. `demo` crea sus propios datos sintéticos en una carpeta DEMO y marca todas las figuras, artefactos, reportes y predicciones; nunca los trata como evidencia de Cup&Cake.

Para entrenar con registros reales:

```powershell
.\.venv_hibrido\Scripts\python.exe codigos\00_pipeline_hibrido.py run --config codigos\config_hibrido.json
```

La corrida real se bloquea deliberadamente hasta completar la aprobación de fuente, el catálogo y la cobertura. La configuración inicial usa `datasets/xlsx/Compras.xlsx` solo como fuente de auditoría: no decide que sea preferible a la fuente corregida.

## Preparación de datos reales

1. Ejecutar `audit` y revisar `auditoria.json`, `compras_auditadas.csv` y `registros_pendientes.csv`. Los duplicados, fechas inválidas, importes negativos o faltantes no se eliminan silenciosamente. Resolverlos en una fuente corregida trazable, conservando el original.
2. Elegir la fuente definitiva en `source`, indicar la hoja en `source_sheet` y registrar su SHA-256 auditado en `source_sha256`. Cambiar `source_approved` a `true` solo tras revisarla. Un cambio posterior del archivo invalida el hash.
3. Completar `catalogo_PARA_REVISAR.csv`: homologar descripciones a `insumo_id` y aprobar cada correspondencia. `otros` y `total` son nombres reservados. No confundir clasificación comercial con insumo sin revisarlo.
4. Completar `cobertura_PARA_REVISAR.csv`: cada lunes requiere estado `observada` o `cero_confirmado`, evidencia y fecha de revisión. `desconocida` o `incompleta` bloquean el entrenamiento dentro del periodo elegido. Siete filas de calendario no prueban cobertura.
5. Guardar los archivos revisados en las rutas `catalog` y `coverage`; pueden estar en `input/hibrido/`. Definir `start` y `end` como lunes inclusivos del periodo aprobado. No usar la selección del periodo para buscar resultados favorables.
6. Revisar el umbral de selección (80% propuesto), ventana, holdout y protocolo inferencial. La opción `independent_holdout` debe permanecer falsa si las fechas ya fueron usadas para orientar el desarrollo. `protocol_approved` no significa que la prueba estadística sea automáticamente adecuada: requiere revisión metodológica.

Las rutas relativas se resuelven desde la raíz del proyecto, no desde el directorio de ejecución. Las fuentes brutas, tesis y salidas anteriores no se sobrescriben.

## Contratos opcionales

Exógenas: CSV/XLSX con `variable`, `fecha_referencia`, `available_at`, `valor`, `fuente`, `version`, `tipo`. Los tipos son `observada`, `pronostico` o `calendario`. Para una variable se usa una previsión/calendario de la semana objetivo que ya existía en origen; en su defecto, la última observación disponible anterior al origen. Sin registro válido queda ausente, no se convierte en cero observado. Las fechas deben ser coherentes, sin mezclar zonas horarias.

Ventas: tabla semanal `semana_inicio`, `importe_nominal`, `available_at`, con un lunes único por semana y publicación no anterior al cierre. Se agregan como rezagos opcionales; ventas no es una variable objetivo. No se usa el maestro diario con importes reales como sustituto nominal.

Si no se proporcionan estas fuentes, el modelo funciona con compras históricas y calendario. No inventa clima futuro ni obliga a generar exógenas artificiales.

## Modelado y separación temporal

- Reutiliza las funciones de normalización de `01_clean_eda.py`, no sus imputaciones o deflactores. Adapta los rezagos, medias desplazadas, referencias y componentes semanales en módulos nuevos con contratos más estrictos.
- Ventana predeterminada: 52 etiquetas semanales por horizonte; 12 semanas de historia adicional para características. La rama estadística usa 52 importes consecutivos. No requiere lag 52 para todos los modelos.
- Reserva las últimas 16 semanas calendario como evaluación. Para comparar h=1..4 desde orígenes comunes y con los cuatro objetivos observables se obtienen 13 orígenes de prueba. No etiqueta 16 orígenes como si fueran 16 semanas objetivo. Se exige historia suficiente y la configuración queda registrada.
- Ajuste interno: ocho orígenes anteriores y purgados, cuya última etiqueta h=4 precede al primer origen final. Transformaciones de ML se ajustan por ventana.
- Componentes: ETS aditivo sin estacionalidad y ARIMA(1,1,1); Ridge con tres valores de regularización y Random Forest parsimonioso. Predictores históricos prefijados y calendario; sin búsqueda masiva de variables.
- Selección de componente estadístico, componente ML y peso por horizonte en validación interna. Pesos candidatos 0.25, 0.50 y 0.75; no se llama híbrido a un componente puro. Los fallos invalidan la configuración durante selección y detienen la evaluación si afectan al modelo fijado; no se ocultan con un promedio bajo otro nombre.
- Categorías seleccionadas en desarrollo y congeladas en prueba; durante ajuste interno se seleccionan nuevamente solo con entrenamiento. Referencia de composición: promedio histórico de participaciones. Candidato: promedio exponencial con alfa seleccionado internamente. La composición es constante entre horizontes en esta primera versión.
- Los ceros observados se mantienen en métricas monetarias; en composición son indefinidos. El remuestreo conserva su posición temporal en lugar de unir semanas distantes.
- RMSE y MAE monetarios, MASE con escala del entrenamiento y MAE porcentual por insumo y macro. H1 compara dos pérdidas en h=1. Intervalos exploratorios de diferencia por bootstrap circular pareado con bloque fijo y corrección Bonferroni para dos componentes; sin garantía inferencial con pocas observaciones. El test final no elige el modelo operativo.

## Productos por ejecución

Cada corrida se guarda bajo `output/hibrido/<run_id>/` y contiene lo que haya alcanzado a generar, incluso si se bloquea:

- Auditoría, pendientes, plantillas de cobertura/catálogo y panel reconciliado.
- Particiones, selección interna, métricas, predicciones, participaciones y asignaciones en CSV y Excel.
- `seleccion.json`, `hipotesis.json`, `modelos.joblib`, `pronostico_futuro.csv`.
- `dss_hibrido.json`, `tablero.html`, `informe.md`.
- Figuras PNG 300 dpi y SVG, CSV de respaldo, guía de inserción y manifiesto F00–F22.
- `manifiesto.json`: configuración, hashes de fuentes y código, versiones, productos y estado de corrida.

Los artefactos joblib solo deben cargarse si son de confianza: no abrir modelos enviados por terceros desconocidos.

```powershell
.\.venv_hibrido\Scripts\python.exe codigos\00_pipeline_hibrido.py forecast --artifact output\hibrido\<run_id>\modelos.joblib
```

Este comando reproduce la emisión del corte guardado, comprobada contra el modelo en memoria. No pretende actualizar un modelo con datos que no recibió. Para un nuevo corte, actualizar fuentes y cobertura y ejecutar una nueva corrida. Su origen es el lunes siguiente al último dato auditado, no necesariamente la fecha actual del equipo.

## Gráficas y Word

El catálogo registra 23 figuras potenciales. Las omisiones son explícitas: F08 exige tres ciclos anuales en desarrollo; F11 no se fabrica cuando no existe selección de variables por frecuencia; F21 requiere captura de navegador de la interfaz real. F00, F10 y F12 son esquemas del procedimiento, no evidencia de entrenamiento. Los demás gráficos se producen únicamente cuando existe información válida.

`guia_figuras.md` y los manifiestos señalan archivos y capítulos sugeridos. No se inserta contenido automáticamente en la tesis. Debe revisarse legibilidad y procedencia antes de la edición controlada del DOCX más reciente. No utilizar figuras DEMO como resultados de investigación.

## Tablero existente

Se añadió un constructor compatible con el nuevo contrato, sin sustituir ni publicar el tablero heredado:

```powershell
cd dashboard
npm run build:hibrido -- ..\output\hibrido\<run_id>
node --test tests/hibrido.test.mjs
```

Produce un Worker estático local en `dashboard/dist/hibrido/`; no lo despliega. También puede abrirse directamente el `tablero.html` de la ejecución. El build solo acepta corridas completadas y preserva las advertencias de demostración.

## Legado y alcance de la migración

La entrada científica nueva es `00_pipeline_hibrido.py`. No requiere ejecutar el maestro diario ni los experimentos de PCA/RNN. Los scripts anteriores se conservan como antecedentes; no deben usarse para evaluar la H1 de Rev44. La lista de retiro condicionado está en el plan técnico. No se han borrado fuentes, imágenes, resultados ni código documental.

Por compatibilidad, ejecutar `00_pipeline_semanal.py` delega ahora en el pipeline Rev44 (sin argumentos realiza auditoría). Su antigua función interna queda como antecedente, no como entrada activa.

Pendientes de ampliación: modelos de composición con covariables por horizonte, intervalos de predicción futuros, captura automatizada F21, inserción editorial en Word y actualización incremental con configuración congelada. No se prometen como funciones implementadas en esta versión inicial.
