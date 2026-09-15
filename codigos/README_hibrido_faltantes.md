# Pipeline exploratorio con calendario incompleto

## Alcance y estado

Adaptación del 14 de septiembre de 2026. Periodo propuesto: mayo de 2021 a junio de 2024; calendario semanal completo del lunes 3 de mayo de 2021 al lunes 24 de junio de 2024 (165 semanas completas). La semana parcial iniciada en abril no se incluye. Se estudian importes nominales registrados utilizables, no demanda, consumo de inventario ni gasto real completo del negocio. La existencia de registros no certifica integridad semanal.

Se incluyen ingredientes, empaques y materiales de decoración recurrentes; se excluyen combustible, herramientas, muebles y otras adquisiciones duraderas. Cada descripción requiere decisión documentada en el catálogo; no se infiere automáticamente su inclusión por la categoría comercial. Los originales no se modifican y los duplicados no se eliminan automáticamente.

La configuración real continúa bloqueada: faltan aprobación de fuente y hash, revisión de incidencias, catálogo y cobertura. Esta implementación no constituye resultados empíricos de Cup&Cake ni confirmación de H1. No se modificó la tesis.

## Secuencia implementada

1. Auditar fuente y conservar trazabilidad. La ejecución principal rechaza la autorización de entrenamiento sintético.
2. Revisar el catálogo (`incluir`/`excluir`, identificador de insumo, aprobación y evidencia). Las categorías COMBUSTIBLE, MUEBLES y HERRAMIENTA no pueden incluirse.
3. Construir calendario completo y aplicar cobertura. `registrada` indica una semana cuyo importe registrado se acepta para este análisis limitado; no certifica todas las compras. `observada` y `cero_confirmado` también requieren evidencia y fecha de revisión. `incierta`, `desconocida` e `incompleta` permanecen como NaN en toda la fila. Una semana sin compras incluidas no se convierte en cero por defecto. Los importes cero por artículo requieren revisión antes de aceptar la semana.
4. Expandir el historial en cada origen temporal, sin comprimir los huecos. El componente estadístico usa SARIMAX en espacio de estados (AR(1), opcionalmente ARIMA(1,1,1)), que admite respuestas faltantes. Sus estimaciones internas no se incorporan como compras observadas ni etiquetas de entrenamiento.
5. Entrenar modelos directos por horizonte solo con objetivos observados: HistGradientBoosting y, opcionalmente, RandomForest con soporte nativo de predictores NaN. Predictores: último importe disponible y antigüedad, medias y conteos observados en ventanas calendario de 4/8/12 semanas y calendario. Las ventanas sin observaciones conservan media NaN. No hay relleno de objetivos ni datos sintéticos.
6. Seleccionar componentes y peso de la combinación dentro del desarrollo temporal. Estimar participaciones con historia disponible; la ponderación exponencial usa edad calendario, incluidos los huecos. Distribuir el total entre insumos y reconciliar importes.
7. Evaluar únicamente objetivos observados, conservando todas las fechas de origen en los archivos. Comparación principal por horizonte sobre fechas comunes de híbrido, estadístico seleccionado, ML seleccionado y último valor disponible. Los referentes suplementarios pueden tener menos casos; no deben ordenarse como si su muestra fuera idéntica. MASE usa diferencias entre semanas calendario consecutivas observadas.
8. Guardar selección, particiones, predicciones, controles, modelos y figuras. La evaluación es retrospectiva exploratoria: `independent_holdout=false`. H1 puede no recibir respaldo; no se garantiza mejor desempeño.

## Parámetros que aún requieren revisión metodológica

`holdout_weeks=26` propone un corte en enero de 2024, pero no equivale a 26 objetivos observados. `min_training_observations=24` es un umbral operativo, no una garantía de suficiencia estadística. `tuning_origins=8` y el resto de hiperparámetros son propuestas de implementación. `window=52` no limita la historia en `calendar_gaps`. La validación interna exige objetivos suficientes por horizonte; si no los hay, se detiene. No se debe cambiar el corte para favorecer H1.

## Ejecución y pruebas

Desde la raíz del proyecto:

```powershell
.\.venv_hibrido\Scripts\python.exe codigos\00_pipeline_hibrido.py audit --config codigos\config_hibrido.json
$env:OMP_NUM_THREADS='1'
.\.venv_hibrido\Scripts\python.exe -m unittest discover -s codigos\tests -p 'test_hibrido*.py'
.\.venv_hibrido\Scripts\python.exe codigos\00_pipeline_hibrido.py run --config codigos\config_hibrido.json
```

`audit` genera plantillas nuevas sin aprobar datos ni entrenar. Completar catálogo y cobertura en las rutas configuradas, resolver incidencias y aprobar explícitamente el hash antes de `run`. El bloqueo actual es intencional. Las demostraciones sintéticas se aíslan y marcan como pruebas técnicas, nunca como evidencia de la investigación.

La prueba integral automatizada usa AR(1) y HistGradientBoosting. En una prueba adicional con los candidatos opcionales, ARIMA(1,1,1) no convergió en un origen de evaluación de la serie artificial: la corrida se detuvo, como corresponde. No se sustituye el modelo seleccionado ni se oculta ese origen para mejorar métricas. Habilitar candidatos opcionales no garantiza completar cualquier serie; la configuración real no se cambió para favorecer el resultado de la demostración.

## Figuras

Se conservan las fases del flujo, auditoría, cobertura, evolución semanal, particiones temporales, selección, comparación, errores, composición y asignación. Las curvas observadas conservan discontinuidades. ACF, PACF y STL se omiten si el desarrollo contiene faltantes: no se rellenan ni se eliminan fechas para producir esos gráficos. Los motivos quedan registrados en el inventario de figuras. Las gráficas de auditoría no certifican cobertura.

## Soporte técnico

- [Statsmodels: SARIMAX con datos faltantes](https://www.statsmodels.org/stable/examples/notebooks/generated/statespace_sarimax_internet.html).
- [Scikit-learn: HistGradientBoostingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html).
- [Scikit-learn: RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).
- [Forecasting: Principles and Practice, validación temporal](https://otexts.com/fpp3/tscv.html).
