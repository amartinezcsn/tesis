# Reejecución con la clasificación analítica actualizada

Fecha de ejecución: 13 de octubre de 2026.

## Alcance

Se repitió el ejercicio completo después de los cambios realizados en la columna `clasificacion_analitica` de `revision_catalogo_cobertura_trazada.xlsx`. Se conservaron las corridas anteriores y se generaron nuevas carpetas para:

- referencia rolling-origin con paso 3;
- sensibilidad rolling-origin con paso 1;
- control step 1 sin parámetros de imputación;
- ablación con compras solamente;
- ablación con compras y ventas;
- ablación con compras y calendario.

## Corrección necesaria en el flujo

La implementación anterior tomaba `CLASIFICACION` directamente de `Compras.xlsx`. Por tanto, una reejecución sin cambios de código habría ignorado la columna modificada en el catálogo.

Se modificó `codigos/hibrido/gaps.py` para aplicar `Catalogo.clasificacion_analitica` como reclasificación aprobada por `descripcion_normalizada`. Para descripciones que aún no figuran en el catálogo se conserva la clasificación original de `Compras.xlsx`. El proceso bloquea catálogos con categorías vacías, descripciones duplicadas o clasificaciones no aprobadas.

Se agregó una prueba de regresión que comprueba que la clasificación analítica aprobada prevalece sobre la clasificación transaccional. La suite completa terminó con 68 pruebas aprobadas.

## Trazabilidad del libro

- SHA-256 anterior: `c96e3564d7b7ce5a55a18e0b667b0f57947bd9f891d913682daf88b0367454ca`.
- SHA-256 actualizado: `4d85afa01d89ac90a3df026a93ed307d2e3331f6539e43d939c019c567ffec23`.
- Filas del catálogo: 563.
- Reclasificaciones respecto de la versión anterior: 15.
- Todas las filas conservan `aprobado=True`, categoría no vacía y descripción única.

Las 15 modificaciones eliminan clasificaciones compuestas y asignan una categoría única. Entre ellas se encuentran `HARINA | CHOCOLATE` a `HARINA`, `QUESO CREMA | RELLENO` a `QUESO CREMA`, `TRANSFER | DECORACION` a `DECORACION` y variantes de capacillos a `CAPACILLOS`.

Al aplicar la versión anterior del catálogo se obtenían 44 categorías elegibles; con el catálogo actualizado se obtienen 34. El importe total se conserva al comparar ambos catálogos con la misma lógica, con una diferencia máxima semanal de redondeo inferior a `5e-13` MXN.

## Corridas nuevas

| Escenario | Carpeta | Estado | Categorías del panel |
|---|---|---:|---:|
| Step 3 | `output/run_20261013T193239Z_29f48e` | completado | 34 |
| Step 1 | `output/run_20261013T193604Z_157556` | completado | 34 |
| Step 1 sin imputación | `output/run_20261013T194232Z_d0a239` | completado | 34 |
| Solo compras | `output/run_20261013T194927Z_fe8b96` | completado | 34 |
| Compras y ventas | `output/run_20261013T195442Z_5fed8f` | completado | 34 |
| Compras y calendario | `output/run_20261013T195837Z_713fcd` | completado | 34 |

Todos los manifiestos registran el nuevo SHA-256 y todos los controles son verdaderos. Las cinco corridas step 1 tienen particiones idénticas, con SHA-256 `ac32427be2ae442565ad0c0f26446321825d365ebbfa24d53852d644796479ff`.

## Selección Pareto actualizada

La selección al 80 % quedó en diez categorías y cubre 80.44 % del importe elegible:

1. HARINA
2. CHOCOLATE
3. FONDANT
4. EMPAQUE
5. CHANTILLY
6. RELLENO
7. DECORACION
8. AMBIANTE
9. HUEVO
10. CAPACILLOS

`BASES`, que antes era la categoría número 11 del conjunto explícito, ahora queda dentro de `RESTO_ELEGIBLE`.

## Resultados monetarios

### Referencia step 3

| Horizonte | n | RMSE híbrido | MAE híbrido |
|---:|---:|---:|---:|
| 1 | 6 | 521.60 | 386.43 |
| 2 | 6 | 695.41 | 439.26 |
| 3 | 6 | 801.62 | 458.80 |
| 4 | 6 | 700.88 | 572.54 |

H1 monetaria tiene muestra insuficiente en step 3: `n=6`, diferencia media de error cuadrático de 161,798.64 MXN².

### Sensibilidad step 1

| Horizonte | n | RMSE híbrido | MAE híbrido |
|---:|---:|---:|---:|
| 1 | 17 | 903.90 | 528.11 |
| 2 | 17 | 1,001.94 | 544.58 |
| 3 | 17 | 1,252.90 | 639.21 |
| 4 | 17 | 1,349.96 | 720.06 |

La parte monetaria no cambia frente al ejercicio step 1 anterior. En H1, la diferencia se define como error cuadrático de último valor menos error cuadrático del híbrido. El resultado es:

- `n=17`;
- media: -432,255.66 MXN²;
- intervalo simultáneo: [-1,047,433.38; 62,131.74] MXN².

El signo negativo favorece a la referencia histórica y el intervalo incluye cero. No existe respaldo confirmatorio para superioridad monetaria del método híbrido.

## Resultado de composición

La reclasificación sí modifica el componente de composición:

- antes: diferencia media H1 de 0.4066 puntos porcentuales;
- ahora: diferencia media H1 de 0.1688 puntos porcentuales;
- muestra disponible: `n=9`, insuficiente para el intervalo exigido.

El signo positivo favorece ligeramente la participación EWM frente a la participación histórica, pero el tamaño de muestra impide una conclusión inferencial. H1 conjunta sigue sin respaldo confirmatorio.

## Control de imputación

Los artefactos científicos de step 1 y step 1 sin imputación son idénticos por SHA-256: métricas, selección, predicciones, particiones, composición, métricas de composición e hipótesis. Los parámetros de imputación siguen siendo de reporte y no alteran el entrenamiento ni la evaluación.

## Ablaciones de predictores

RMSE del híbrido y diferencia respecto de solo compras, en MXN:

| Escenario | H1 | H2 | H3 | H4 |
|---|---:|---:|---:|---:|
| Solo compras | 902.500 | 1,003.536 | 1,253.772 | 1,350.210 |
| Compras + ventas | 902.821 (+0.322) | 1,003.286 (-0.250) | 1,253.201 (-0.571) | 1,349.478 (-0.732) |
| Compras + calendario | 902.492 (-0.008) | 1,003.630 (+0.094) | 1,253.230 (-0.543) | 1,350.568 (+0.358) |
| Modelo completo | 903.898 (+1.399) | 1,001.942 (-1.593) | 1,252.903 (-0.869) | 1,349.963 (-0.247) |

Las diferencias son pequeñas y no muestran una contribución uniforme de ventas o calendario en los cuatro horizontes. La conclusión del ejercicio anterior se mantiene.

## Conclusión

Los cambios de `clasificacion_analitica` se incorporaron correctamente. La consecuencia principal es una taxonomía más compacta: diez categorías explícitas en lugar de once y `BASES` dentro de `RESTO_ELEGIBLE`. Las métricas monetarias y la conclusión de H1 no cambian. El resultado descriptivo de composición se reduce de 0.4066 a 0.1688 puntos porcentuales y permanece inconcluso por muestra insuficiente.

No se modificó ningún documento de tesis. Cualquier actualización de una revisión formal debe hacerse después de aprobación explícita.
