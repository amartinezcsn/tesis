# Plan de desarrollo del pipeline híbrido de Cup&Cake

Fecha de revisión: 12 de septiembre de 2026.
Base metodológica: TESIS_AGO2026_Rev44_(ZUJ)_12sep2026.docx, capítulo de Metodología y H1.
Estado: plan técnico basado en inspección del código y comprobaciones diagnósticas. No constituye una implementación ni una validación del modelo. No se eliminaron archivos ni se ejecutó entrenamiento completo.

## Resultado esperado

Una ejecución reproducible debe generar pronósticos del importe total de compras para las cuatro semanas siguientes, sus participaciones por insumo y sus asignaciones monetarias. Debe separar la evaluación histórica de la emisión futura, mantener una sola H1 y permitir que el híbrido no supere las referencias sin alterar el protocolo para favorecerlo.

No se incluyen optimización de inventarios, cantidades físicas, rentabilidad, ventas como objetivo, merma ni expansión comercial. Las ventas históricas podrán ser predictores.

## Diagnóstico del código

1. **Existe una base semanal útil, no un híbrido implementado.** `00_pipeline_semanal.py` ejecuta agregación, características, perfil, diagnóstico, modelos individuales y reportes. `06_modelos_rolling_window.py` no contiene una etapa que combine un componente estadístico con uno de aprendizaje automático. El modelo hurdle existente combina probabilidad e importe positivo; no equivale a la integración estadística y ML definida para esta investigación.
2. **Se pierde el detalle por insumo.** `02_agregar_semanal.py`, función `aggregate_daily_to_weekly`, suma ventas y un único total de compras. La limpieza sí conserva descripción, clasificación y subclasificación. En `input/compras_limpias.xlsx`, hoja `detalle`, se verificaron 1,333 filas, 38 clasificaciones y 560 descripciones, entre 2022-01-01 y 2025-07-30. Esto no demuestra cobertura continua ni que las clasificaciones correspondan a insumos homogéneos.
3. **Hay dos fuentes derivadas que deben reconciliarse.** Existe `compras_limpias_corregidas.xlsx`, con hojas `detalle`, `diario_completo` y `resumen`. No debe elegirse por su nombre: se requiere comparación contra el archivo bruto y documentación del origen de las correcciones.
4. **Ceros y ausencias se confunden.** `01_clean_eda.py:build_compras` crea un calendario completo y rellena importes ausentes con cero. `config_semanal.py:primary_coverage_block` luego excluye automáticamente ciertas rachas. La Rev44 exige verificar cobertura, no inferirla solo por una racha o por ventas positivas. Contar siete filas generadas tampoco prueba siete días de registro observado.
5. **Exógenas futuras pueden entrar en h>1.** `direct_ml_samples` toma todas las columnas `exog_` de la fila objetivo. Para temperatura e indicadores rezagados respecto a esa fila, esto puede usar información posterior al origen. Comprobación con índices: origen 60, h=4, último dato cerrado 59; la función devolvió una exógena cuyo valor representaba la observación 62. El calendario futuro sí puede conocerse; una observación meteorológica futura no.
6. **Separar orígenes no basta para separar etiquetas.** `split_tuning_evaluation` no impone que las fechas objetivo utilizadas en ajuste precedan al primer origen de prueba. En una comprobación de 90 filas y h=4: último origen de ajuste 70, última etiqueta 73 y primer origen de evaluación 71. Debe aplicarse una separación por fecha de disponibilidad de la etiqueta, no únicamente por índice de origen.
7. **La unidad monetaria requiere una decisión explícita.** `config_semanal.py` usa `compras_total_real_2026_05`; la limpieza ajusta con un índice base de mayo de 2026 y sustituye factores faltantes por 1. Para presupuesto operativo se propone MXN nominales. Los importes reales pueden conservarse como análisis separado, pero no deben presentarse como moneda nominal ni usar indicadores aún no publicados como predictores históricos.
8. **Los errores de modelos se ocultan.** `forecast_statistical` devuelve un promedio de cuatro semanas ante cualquier excepción, manteniendo la etiqueta de ARIMA o ETS. Debe registrarse el fallo y, si existe respaldo operativo, identificarlo como modelo distinto.
9. **El código conserva H2.** Configuración, características, evaluación, trazabilidad, reportes, JSON y constructor del tablero todavía incluyen esa hipótesis. La comparación con/sin exógenas puede permanecer como análisis complementario, no como H2.
10. **Hay detalles que revisar en las transformaciones.** Ridge no estandariza sus predictores; las variantes log1p limitan el pronóstico al máximo de entrenamiento. El hurdle describe su inversa logarítmica como esperanza del importe, sin justificar corrección de retrans formación. Se propone empezar en escala monetaria y evaluar transformaciones como variantes documentadas, no conservar límites implícitos.
11. **La salida futura no está implementada.** `08_exportar_dss_semanal.py` exporta evaluación y fija el pronóstico futuro como no disponible. No existe allí entrenamiento final persistido ni inferencia para fechas aún no observadas.
12. **El tablero sí tiene una conexión reutilizable.** `dashboard/scripts/build-static.mjs` lee el JSON semanal y lo inserta al construir la página. No requiere reconstrucción completa, pero actualmente selecciona ganadores por RMSE de evaluación, interpreta H1 solo sobre importe y convierte ciertos faltantes a cero. Se deben separar ganador descriptivo, modelo fijado en desarrollo y modelo usado para emisión.

### Alcance de las comprobaciones

Se inspeccionaron los puntos de entrada, limpieza de compras, configuración, agregación, características, particiones, entrenamiento/evaluación, reportes, trazabilidad, exportación y constructor del tablero. Los módulos diarios se revisaron para determinar su papel y dependencias, no para validar íntegramente sus algoritmos.

La suite `python -m unittest discover -s codigos/tests -v` no llegó a ejecutar pruebas: el entorno disponible carece de `matplotlib`. La carpeta `.venv` no contiene el ejecutable Windows esperado. Dos comprobaciones pequeñas de alineación temporal sí se ejecutaron sin entrenamiento y produjeron los resultados indicados arriba. No se certifica el pipeline actual como funcional.

## Arquitectura propuesta

Fuentes brutas → auditoría y cobertura → panel semanal por insumo → particiones temporales → características disponibles en origen → componentes estadístico y ML → combinación híbrida del total → participaciones → asignaciones → evaluación H1 → entrenamiento final e inferencia → JSON y tablero.

### Contratos de datos

- Compras: `registro_id`, `fecha`, `insumo_id`, `importe_nominal`, `fuente`, `estado_validacion`. Conservar descripción original y catálogo de homologación; no sumar cantidades de unidades incompatibles.
- Cobertura: `semana_inicio`, `estado` (observada, cero confirmado, incompleta, desconocida), `evidencia`, `fecha_revision`. Separar estado del valor monetario.
- Exógenas: `variable`, `fecha_referencia`, `available_at`, `valor`, `fuente`, `version`. Admitir cada registro solo si estaba disponible en el origen de emisión.
- Predicciones: `run_id`, `origen`, `fecha_objetivo`, `horizonte`, `modelo`, `insumo_id` cuando corresponda, `prediccion`, `unidad`, `estado`. El observado pertenece a la evaluación, no es requisito de inferencia futura.
- Conservar un calendario completo; no comprimir semanas ausentes y luego tratarlas como contiguas al aplicar `shift`.

### Modelo inicial propuesto

Para el total, seleccionar dentro del desarrollo un componente ETS o ARIMA y un componente Ridge estandarizado o Random Forest. Mantener HistGradientBoosting como alternativa posterior si la cobertura lo permite. Comparar con último valor, promedio de cuatro semanas e ingenuo estacional cuando sea válido.

La integración inicial será una combinación convexa por horizonte:

`pronostico_hibrido = w_h × pronostico_estadistico + (1 − w_h) × pronostico_ml`.

Propuesta de rejilla inicial: pesos 0.25, 0.50 y 0.75; los componentes puros se reportan aparte. Elegir componentes y pesos con predicciones temporales internas fuera de muestra, nunca con residuos de entrenamiento ni con el test final. Si la muestra es insuficiente para ajustar pesos, predefinir 0.50 y declarar la limitación. No llamar híbrido a un componente puro seleccionado como respaldo.

La combinación simple tiene respaldo como punto de partida en [Hyndman y Athanasopoulos, Forecast combinations](https://otexts.com/fpp3/combinations.html); su superioridad en este caso sigue siendo una pregunta empírica.

Para participaciones, usar como referencia el promedio histórico de participaciones en semanas con total positivo, conforme a la Rev44. Como primer candidato distinto de la referencia, proponer un promedio exponencialmente ponderado de las composiciones válidas, con su parámetro seleccionado en validación interna. Produce una distribución no negativa y normalizada sin exigir un modelo grande por cada insumo. Registrar que esta versión mantiene la composición pronosticada entre horizontes; una regresión regularizada por horizonte será una extensión condicionada a datos suficientes y evaluación interna.

Seleccionar insumos por participación monetaria acumulada solo en desarrollo y agregar `otros`. Proponer inicialmente 80% como umbral a confirmar antes del experimento; no fijarlo usando el test. Congelar las categorías para la evaluación. En validación interna, cualquier selección aprendida debe usar únicamente el entrenamiento correspondiente.

`asignacion_insumo = participacion_pronosticada × total_hibrido`.

En semanas observadas con total cero, la composición real es indefinida: no imputarla como vector cero. Excluir esas semanas solo del error porcentual, contar exclusiones y mantener la evaluación monetaria. Si no existe historia válida de composición, bloquear esa salida. Documentar el tratamiento de devoluciones antes de imponer no negatividad; no recortar silenciosamente transacciones negativas.

## Plan de trabajo y criterios de aceptación

Las duraciones son estimaciones de esfuerzo de una persona, no compromisos de fecha; excluyen espera por aclaraciones del negocio y ejecuciones extensas.

| Fase | Trabajo y reutilización | Entregable verificable | Esfuerzo |
| --- | --- | --- | --- |
| 0 | Resolver fuente de compras, moneda, definición de insumo y cobertura; congelar alcance Rev44 y H1 | Configuración del experimento y registro de decisiones; no entrenar sin fuente canónica | 1–2 días |
| 1 | Recuperar normalizadores de `01_clean_eda.py`; separar ingesta de modelado; parametrizar rutas y fechas | Compras trazables, catálogo, rechazos y cobertura; totales reconciliados contra fuente | 2–3 días |
| 2 | Adaptar `02_agregar_semanal.py` y diagnóstico temporal | Panel total/insumo, participaciones y residual; sumas reconciliadas y ceros auditados | 1–2 días |
| 3 | Corregir `config_semanal.py`, `03_features_semanales.py` y particiones de `06_modelos_rolling_window.py` | Un generador origen–horizonte; etiquetas disponibles antes de ajuste; exógenas as-of; test temporal reservado | 2–3 días |
| 4 | Extraer funciones de referencias y componentes de `06_modelos_rolling_window.py`; agregar escalado local de Ridge y fallos explícitos | Predicciones internas reproducibles y modelo híbrido con pesos/configuración registrados | 2–3 días |
| 5 | Crear módulo de composición y asignación | Referencia histórica y candidato; porcentajes suman 100%; asignaciones suman total | 1–2 días |
| 6 | Separar métricas, contraste H1 y reportes del monolito | RMSE/MAE/MASE monetarios, MAE porcentual por insumo y macro, cobertura común y evidencia H1 | 2–3 días |
| 7 | Crear entrenamiento final, persistencia e inferencia; reutilizar trazabilidad y exportador | Artefacto versionado recargable; pronósticos futuros h=1..4 sin etiquetas futuras | 2–3 días |
| 8 | Adaptar constructor y visualización del dashboard | Total, porcentajes, importes por insumo, cuatro semanas y advertencias; ausencia distinta de cero | 1–2 días |
| 9 | Ejecutar regresión, corrida reproducible y retiro controlado de legado | Comando único desde fuentes, pruebas aprobadas, documentación y listado final de dependencias | 1–2 días |

Total orientativo: 15–25 jornadas. La ruta crítica pasa por cobertura, temporalidad y separación de evaluación; no por aumentar el número de algoritmos.

### Protocolo de evaluación

- Mantener 52 semanas de entrenamiento y 16 semanas finales como propuesta, verificando primero viabilidad. El código actual reserva 16 orígenes comunes compatibles con h=4, lo cual no equivale exactamente a 16 fechas objetivo finales para todos los horizontes. Elegir y documentar una sola interpretación coherente con la tesis.
- Fijar cortes por fechas y disponibilidad: para cada partición, la última etiqueta usada en ajuste debe estar disponible antes del origen evaluado. Aplicar purga multihorizonte donde sea necesaria.
- Separar historial necesario para rezagos de filas efectivas de entrenamiento: imponer lag 52 a todos los modelos pierde datos innecesariamente. Eliminar ese requisito global y justificar rezagos dentro de desarrollo.
- No cambiar modelos, pesos, categorías o umbrales después de mirar la evaluación final. Se permite actualización secuencial de parámetros con observaciones que ya hayan llegado, bajo regla fijada previamente.
- La evaluación temporal debe usar únicamente observaciones anteriores al origen, también al ajustar transformaciones y seleccionar modelos; véase [Hyndman y Athanasopoulos, Time series cross-validation](https://otexts.com/fpp3/tscv.html).
- H1 exige evaluar ambos componentes. Proponer h=1 como contraste principal; h=2..4 complementarios. Definir antes del test la pérdida monetaria, la pérdida de composición, la prueba de incertidumbre y la familia de comparaciones. No trasladar automáticamente el DM sobre pérdida cuadrática a la composición.
- Si se emplea remuestreo temporal, remuestrear semanas completas, con sus categorías juntas, y fijar el tamaño de bloque sin consultar test. Con pocos casos, declarar evidencia insuficiente en vez de garantizar significancia.
- Si el test heredado ya se utilizó reiteradamente para rediseñar el pipeline, tratarlo como retrospectivo exploratorio. Una confirmación independiente requerirá datos no examinados o evaluación prospectiva; volver a reservar las mismas fechas no borra su uso previo.
- No escoger el modelo operativo por el menor RMSE del test. Fijarlo mediante desarrollo; reportar cualquier ranking final como descriptivo.

## Qué reutilizar y cómo adaptarlo

| Archivo o grupo actual | Decisión |
| --- | --- |
| `01_clean_eda.py` | Reutilizar normalización e ingesta del detalle. Separar INPC, no imputar ausencia como cero, parametrizar fechas, conservar nominales y auditar deduplicación. No eliminar todavía. |
| `00_pipeline_semanal.py` | Convertir en único punto de entrada completo, incluyendo ingesta y nuevos módulos; quitar dependencia manual del maestro diario heredado. |
| `config_semanal.py` | Conservar configuración central, sustituir cobertura heurística y rezagos exógenos fijos por contratos explícitos. Eliminar H2 y nombres mensuales ambiguos. |
| `02_agregar_semanal.py` | Reutilizar calendario, validaciones y agregación, incorporando importes por insumo y estado de cobertura. |
| `03_features_semanales.py` | Conservar rezagos/resúmenes desplazados; separar calendario conocido de datos observados con fecha de disponibilidad. |
| `04_perfil_semanal.py`, `04_analisis_series_temporales_semanal.py` | Reutilizar tablas y diagnósticos pertinentes; ejecutarlos antes de selección de características y sin test; unificar la política de cobertura. |
| `06_modelos_rolling_window.py` | Dividir en particiones, componentes, híbrido y evaluación; reutilizar funciones verificadas, no copiar el monolito sin corregir fugas. |
| `07_reportes_semanales.py`, `08_exportar_dss_semanal.py` | Ampliar a total/composición/asignaciones, H1 única, metadatos de moneda, estado de modelos y pronóstico futuro separado. |
| `trazabilidad.py` | Conservar hashes/semillas/versiones; incluir fuentes brutas, catálogo, cobertura, configuración, artefactos, horizontes y estado de fallo por ejecución. |
| `tests/test_pipeline_semanal.py` | Conservar calendario y controles útiles; reemplazar pruebas que exigen excluir ceros por heurística. Agregar fuga multihorizonte, disponibilidad de etiquetas y composición. |
| `dashboard/scripts/build-static.mjs`, `dashboard/public/index.html` | Reutilizar publicación estática y presentación; actualizar contrato JSON y retirar aceptación automática de H1, H2 y conversión de faltantes a cero. |

### Organización objetivo

Mantener un solo ejecutor y módulos con responsabilidades claras: `ingesta`, `cobertura`, `agregacion`, `particiones`, `features`, `modelos_base`, `modelo_hibrido`, `composicion`, `evaluacion`, `entrenamiento_final`, `inferencia` y `exportacion`. Separar código científico de scripts de edición de tesis. Es una estructura propuesta; migrar funciones conservando pruebas, no duplicarlas permanentemente.

Guardar cada corrida bajo un identificador propio, con configuración, tablas de auditoría, predicciones, métricas y manifiesto. Los artefactos de modelo deben incluir transformaciones, columnas, catálogo, moneda, corte temporal y versiones. La recarga debe reproducir las predicciones del mismo origen antes de habilitar el modo futuro.

## Qué retirar de la solución activa

No hay autorización de borrado en este plan. La recomendación es archivar antes de eliminar y hacerlo después de una corrida completa independiente del legado.

### Candidato redundante

`codigos/feature_engineering.py`: antecedente diario con ruta a otro equipo; no se encontró referencia desde los ejecutores revisados. Retirarlo del código activo después de confirmar que no existe ejecución externa manual. La versión usada por el maestro diario es `02_feature_engineering_profesional.py`.

### Legado diario que no debe entrar al nuevo pipeline

- `02_feature_engineering_profesional.py`
- `03_perfil_dataset_y_dimensiones.py`
- `04_diagnostico_multicolinealidad.py`
- `05_seleccion_caracteristicas_dataset_reducido.py`
- `06_pca_reduccion_componentes.py`
- `07_modelos_estadisticos_ml_rolling_origin.py`
- `08_rnn_lstm_dataset_reducido.py`
- `09_generar_graficas_manifiesto_pca.py`
- `10_generar_graficas_rolling_origin.py`
- `11_generar_graficas_rnn_lstm.py`
- `config_metodologia.py`, `README_metodologia.md`, `requirements_pipeline_tesis.txt`

Archivarlos en conjunto con un manifiesto de sus productos y referencias. No se afirma que sus funciones sean incorrectas: corresponden al enfoque diario/multiobjetivo o a experimentos no necesarios para la primera versión semanal. RNN/LSTM permanecen como posibilidad secundaria en la tesis, por lo que se archivan como experimentos, no se exige borrarlas definitivamente.

`00_pipeline_maestro_tesis.py` solo podrá retirarse del flujo activo cuando la ingesta reutilizada de `01_clean_eda.py` funcione desde el nuevo ejecutor. El pipeline semanal actual todavía necesita su maestro diario. No eliminar `01_clean_eda.py` ni los archivos fuente para simplificar prematuramente.

### No borrar por considerarlos código sobrante

- `datasets/`: fuentes y evidencia original.
- `input/compras_limpias*.xlsx`: conservar hasta reconciliar procedencia y contenido.
- `scripts/`: scripts de edición de Word, no parte del entrenamiento; separar organizativamente, no borrar sin revisar dependencia documental.
- `imagenes/`, `resultados/`, `output/`: pueden respaldar figuras y versiones previas de la tesis. Archivar por experimento, no eliminar globalmente.
- Dependencias de dashboard: no retirar herramientas de publicación, autenticación o base de datos por una lectura parcial; no son el cuello de botella del pipeline científico.

Los entornos y dependencias se depurarán al final mediante un entorno nuevo con requisitos mínimos probados; no borrar `node_modules` o entornos amplios como primer paso.

## Pruebas obligatorias antes de usar resultados

1. Total semanal igual a suma por insumo más residual; nominal/real nunca mezclados.
2. Ausencia distinta de cero; semanas parciales e inciertas identificadas.
3. Cambiar datos posteriores al origen no altera la predicción emitida en ese origen.
4. Etiquetas de validación interna disponibles antes del corte externo, en h=1..4.
5. Imputación, escalado, selección de variables, catálogo aprendido y pesos ajustados sin test.
6. Híbrido calculado con componentes declarados y pesos válidos; excepciones no ocultas.
7. Participaciones no negativas y suma uno; total cero real excluido solo de la métrica porcentual.
8. Asignaciones suman total, incluso después de redondear a centavos con regla reproducible.
9. Rechazo de datos sintéticos preservado desde fuente hasta evaluación; etiquetas de procedencia no perdidas durante agregación.
10. Inferencia futura sin columna de resultados futuros, modelo recargable y salidas idénticas con el mismo corte.
11. Reportes sin H2; H1 no favorable si solo mejora una de sus dos partes.
12. Tablero distingue cero, no disponible, fallo, evaluación histórica y pronóstico futuro.

## Decisiones pendientes antes del primer entrenamiento

Confirmar fuente canónica y correcciones de compras; catálogo de insumos; cobertura auditada; moneda nominal propuesta; umbral de principales insumos; fechas de desarrollo/test; disponibilidad histórica de exógenas y criterio inferencial de H1. No todas bloquean el diseño de módulos, pero sí una corrida científica interpretable.

El éxito del desarrollo será entregar un procedimiento reproducible y evaluable. No se condicionará la finalización a obtener una H1 favorable.

## Plan de figuras para documentar cada fase

La generación de figuras será un entregable obligatorio del pipeline, no una actividad manual posterior. Cada fase deberá exportar sus datos de respaldo y producir las figuras pertinentes cuando existan observaciones suficientes. Si una figura no puede calcularse, el manifiesto registrará el motivo; no se inventarán valores ni se rellenarán resultados faltantes con cero.

Se distinguirán dos clases de figuras: diagramas del procedimiento propuesto, que pueden incorporarse ahora a Metodología, y gráficas empíricas, que se incorporarán a Desarrollo o Resultados después de ejecutar y verificar el pipeline. Ningún diagrama conceptual presentará como realizado un procedimiento pendiente.

### Catálogo de figuras por fase

Los identificadores siguientes son internos del pipeline. La numeración final de figuras se asignará según su posición en Word, sin sustituir por anticipado la numeración existente.

| Fase | Identificador y figura | Datos de respaldo | Mensaje y ubicación propuesta |
| --- | --- | --- | --- |
| 0. Alcance y arquitectura | F00 Diagrama general del pipeline, con ramas de total y composición | Configuración y dependencias de etapas | Explicar cómo las fuentes llegan al presupuesto y al contraste de H1. Metodología; diagrama propuesto. |
| 1. Ingesta y depuración | F01 Flujo de registros recibidos, aceptados, rechazados y pendientes | Auditoría de ingesta con motivos excluyentes | Mostrar trazabilidad sin presentar eliminación de registros como mejora automática. Desarrollo. |
| 1. Cobertura | F02 Calendario de cobertura semanal de compras y ventas | Tabla de cobertura validada y evidencia | Distinguir observación, cero confirmado, periodo incompleto y cobertura desconocida. Desarrollo. |
| 2. Agregación | F03 Serie del importe total semanal, con marcas de cobertura | Panel semanal y estado de observación | Mostrar evolución monetaria; dejar huecos en periodos desconocidos. Desarrollo. |
| 2. Selección de insumos | F04 Pareto de participación monetaria acumulada | Compras del conjunto de desarrollo y catálogo congelado | Justificar insumos principales, umbral y categoría residual sin usar test. Desarrollo. |
| 2. Composición | F05 Mapa de calor de participaciones por insumo y semana | Panel de participaciones en semanas válidas | Mostrar estabilidad y cambios de composición; representar total cero como no definido. Desarrollo. |
| 2. Diagnóstico temporal | F06 ACF y PACF; F07 distribución del importe y frecuencia de ceros | Serie de desarrollo y tablas de diagnósticos | Examinar dependencia temporal, asimetría e intermitencia sin anticipar resultados de las pruebas. Desarrollo. |
| 2. Diagnóstico condicional | F08 Descomposición temporal, solo si cumple los requisitos de longitud y continuidad | Componentes estimados exclusivamente en desarrollo | Ilustrar patrones exploratorios y sus limitaciones; omitir con motivo cuando no proceda. Desarrollo. |
| 3. Validación | F09 Línea temporal de entrenamiento, validación interna, separación de etiquetas y evaluación final | Tabla explícita de particiones y fechas objetivo | Demostrar qué datos están disponibles en cada origen y horizonte. Metodología como esquema; Desarrollo con fechas reales. |
| 3. Variables predictivas | F10 Diagrama de disponibilidad y alineación origen–horizonte | Diccionario de variables, `available_at` y ejemplos auditados | Distinguir calendario conocido de indicadores y clima observados. Metodología/Desarrollo. |
| 3. Selección de características | F11 Frecuencia de selección de variables en particiones internas | Registro de variables seleccionadas por partición | Mostrar estabilidad de selección, sin interpretar frecuencia como causalidad ni importancia universal. Desarrollo. |
| 4. Integración híbrida | F12 Diagrama de componentes y combinación; F13 pesos por horizonte y error de validación interna | Configuración elegida y predicciones internas fuera de muestra | Explicar arquitectura y justificar pesos sin consultar evaluación final. Metodología para el diagrama; Desarrollo para valores estimados. |
| 4 y 6. Pronóstico del total | F14 Observado frente a pronosticado del híbrido y referencia, con paneles por horizonte | Predicciones finales con origen, fecha objetivo, modelo y observado | Evaluar comportamiento fuera de muestra sobre fechas comparables. Resultados. |
| 5. Distribución | F15 Participaciones observadas y pronosticadas en semanas seleccionadas por regla previa | Predicciones de composición y referencia histórica | Comparar composición sin escoger únicamente semanas favorables; usar pares de barras apiladas al 100%. Resultados. |
| 5. Asignación | F16 Importe pronosticado por insumo y comprobación del total | Asignaciones, total híbrido y diferencia de reconciliación | Mostrar cómo el total se distribuye y verificar que las asignaciones sumen el total. Desarrollo/Resultados. |
| 6. Error monetario | F17 Comparación de RMSE y MAE por modelo y horizonte | Tabla de métricas sobre fechas comunes | Comparar híbrido, componentes y referencias; usar paneles separados por métrica. Resultados. |
| 6. Error de composición | F18 MAE en puntos porcentuales por insumo y promedio macro | Métricas porcentuales, número de semanas válidas y exclusiones | Mostrar qué insumos presentan mayor dificultad y comparar contra la referencia. Resultados. |
| 6. Estabilidad y H1 | F19 Diferencia de pérdidas frente a las referencias a lo largo del tiempo; intervalos solo cuando el procedimiento esté definido y ejecutado | Pérdidas pareadas y salida del contraste, separadas para total y composición | Distinguir mejora descriptiva, incertidumbre y respaldo de ambas partes de H1. Resultados. |
| 7. Inferencia futura | F20 Pronóstico de las próximas cuatro semanas y asignaciones por insumo | Artefacto recargado y predicciones emitidas con fecha de corte | Separar claramente observados históricos de futuro; no mostrar valores reales futuros inexistentes. Desarrollo como ejemplo de salida, solo después de implementarla. |
| 8. Tablero | F21 Captura de la interfaz usando el JSON validado de una ejecución | Versión de interfaz, JSON y `run_id` | Ilustrar consulta del presupuesto, porcentajes, cobertura y estado del modelo. Desarrollo. |
| 9. Verificación | F22 Resumen de controles de calidad aprobados, fallidos y no ejecutados | Reporte real de pruebas y controles por fase | Mostrar evidencia de verificación; no confundir controles aprobados con H1 favorable. Desarrollo o anexo técnico. |

No todas las figuras deben ocupar el cuerpo principal. F00, F02, F04, F09, F12 y F14–F20 son candidatas prioritarias; diagnósticos extensos y controles técnicos pueden ubicarse en anexos. F08 es condicional. La selección editorial final evitará figuras redundantes.

### Implementación y reutilización de gráficas

1. Extraer y adaptar `save_figures` de `04_analisis_series_temporales_semanal.py` para los diagnósticos semanales. Preservar las tablas numéricas que alimentan cada gráfico y corregir primero su política de cobertura.
2. Adaptar la comparación de errores de `07_reportes_semanales.py` para distinguir total, composición, horizontes y conjuntos de evaluación. No limitar la nueva salida a h=1 y h=4 si se reportan los cuatro horizontes.
3. Revisar funciones concretas de `09_generar_graficas_manifiesto_pca.py`, `10_generar_graficas_rolling_origin.py` y `11_generar_graficas_rnn_lstm.py` para recuperar utilidades de estilo o exportación. No trasladar automáticamente figuras de PCA, ventas diarias o redes neuronales al nuevo enfoque. Archivar los generadores heredados solo después de extraer y probar las utilidades realmente necesarias.
4. Crear un módulo compartido de visualización y un catálogo de figuras. Cada etapa entregará tablas normalizadas; el generador leerá esas tablas y no volverá a entrenar modelos para dibujar resultados.
5. Separar la construcción de diagramas conceptuales, las gráficas empíricas y las capturas del tablero. Las capturas deberán corresponder a una interfaz ejecutada con el JSON identificado, no a una maqueta presentada como implementación.

### Estándar de exportación y trazabilidad

- Guardar por ejecución en `output/<run_id>/figuras/`, sin sobrescribir figuras de experimentos anteriores.
- Exportar gráficas como PNG de al menos 300 dpi al tamaño previsto de inserción y, cuando sea posible, también SVG o PDF vectorial. Conservar CSV de datos de respaldo; el pipeline puede seguir exportando Excel como presentación adicional.
- Producir `manifiesto_figuras.csv` o JSON con: identificador, archivo, título, descripción, fase, capítulo sugerido, `run_id`, fuente y hash, corte temporal, conjunto utilizado, unidades, horizontes, código generador, estado y motivo de omisión.
- Usar etiquetas en español, tipografía legible al tamaño de Word y colores consistentes: híbrido, componente estadístico, componente ML y referencia deben conservar su identidad entre figuras. No depender únicamente del color; combinar líneas, símbolos o patrones.
- Rotular siempre MXN nominales o la base real correspondiente; expresar errores de participación en puntos porcentuales. No usar el rótulo mensual para una suma de cuatro semanas.
- Identificar desarrollo, evaluación y pronóstico futuro. Evitar conectar líneas a través de semanas desconocidas, usar ejes engañosos o mezclar porcentajes y moneda en una sola escala.
- Añadir barras o bandas de incertidumbre solo si fueron calculadas mediante un procedimiento documentado. No convertir desviaciones de errores en intervalos de predicción sin justificación.

### Integración en Word

La generación del paquete de figuras no modificará automáticamente la tesis. La inserción se realizará como una etapa editorial controlada sobre el DOCX más reciente identificado y confirmado al momento de trabajar, con respaldo previo.

Cada figura llevará título descriptivo, explicación en el texto, referencia cruzada y nota de procedencia. Para diagramas adaptados de autores se conservará la atribución y se verificará la referencia bibliográfica; para resultados propios se identificará la fuente de datos y la ejecución. Los identificadores F00–F22 no sustituirán los campos de numeración de Word.

Después de insertar se actualizarán referencias cruzadas e índice de figuras y se verificará visualmente legibilidad, resolución, recortes, saltos de página y correspondencia entre figura y explicación. Las definiciones protegidas del director no se alterarán para acomodar imágenes.

### Criterios de aceptación y esfuerzo adicional

- Cada fase dispone de una figura pertinente o de un motivo documentado para no generarla.
- Los valores representados coinciden con sus tablas de respaldo y la misma ejecución de modelos.
- Las figuras de evaluación no participan en selección posterior de hiperparámetros ni permiten escoger retrospectivamente ejemplos favorables.
- La regeneración con los mismos datos y configuración conserva valores, etiquetas y correspondencia con el manifiesto.
- Las pruebas verifican existencia, dimensiones, datos no vacíos, unidades y ausencia de valores no finitos no tratados; la inspección visual comprueba el diseño final.

Integrar el trabajo gráfico desde las fases 1–8. Añadir una estimación inicial de 3–5 jornadas para catálogo, nuevos gráficos, pruebas e integración editorial, además del esfuerzo base de 15–25 jornadas. El total orientativo pasa a 18–30 jornadas; dependerá del número de figuras finalmente insertadas y de la disponibilidad de renderizado de Word. Estas cifras son de planificación, no una fecha de entrega garantizada.
