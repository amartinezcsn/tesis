# Sensibilidad retrospectiva rolling semanal y plan de actualización Rev62

Fecha de cierre: 2026-10-13.

## Conclusión principal

La reproducción del protocolo con avance de tres semanas fue exacta. Al ampliar
la evaluación a orígenes semanales, la muestra monetaria pasó de 6 a 17 pares
por horizonte, pero el resultado no respalda H1: el híbrido seleccionado solo
con validación interna presentó mayor RMSE que `ultimo_valor` en los cuatro
horizontes de la evaluación ampliada. La composición aportó 9 pares válidos en
`h=1`, menos que el mínimo inferencial de 12. Esta ejecución es una sensibilidad
retrospectiva ampliada, no una confirmación independiente.

No se modificó `TESIS_SEP2026_Rev61_(ZUJ)_Final.docx`.

## Corridas y trazabilidad

| Propósito | Corrida | Avance | Resultado |
| --- | --- | ---: | --- |
| Referencia histórica | `run_20260924T195600Z_86a6f5` | 3 semanas | Corrida original preservada |
| Reproducción | `run_20261013T171831Z_8f6f09` | 3 semanas | Coincidencia exacta |
| Sensibilidad semanal | `run_20261013T172443Z_49188a` | 1 semana | Evaluación ampliada |
| Sensibilidad semanal sin imputación | `run_20261013T173039Z_ab4e3e` | 1 semana | Resultados científicos idénticos |
| Ablación compras | `run_20261013T174714Z_ebc291` | 1 semana | Sin ventas ni banderas opcionales |
| Ablación compras y ventas | `run_20261013T175259Z_516e8e` | 1 semana | Ventas, sin banderas opcionales |
| Ablación compras y calendario | `run_20261013T175656Z_0a73e7` | 1 semana | Banderas opcionales, sin ventas |

El entorno reproducido usa Python 3.10.0rc2, NumPy 2.2.6, pandas 2.3.3,
scikit-learn 1.7.2, statsmodels 0.14.6, matplotlib 3.10.8, openpyxl 3.1.5,
SciPy 1.15.3 y joblib 1.5.2. Se corrigió `requirements_hibrido.txt` para fijar
`joblib==1.5.2`, versión registrada por el manifiesto histórico.

La reproducción `8f6f09` coincidió exactamente con `86a6f5` en:

- 24 filas de métricas monetarias;
- 96 filas de métricas de composición;
- 216 filas de selección interna y la selección final por horizonte;
- selección de composición;
- 144 predicciones;
- 44 filas de particiones;
- 528 filas de composición;
- `seleccion.json` e `hipotesis.json`.

## Calendario, particiones y ausencia de fuga

El panel conserva 493 lunes consecutivos. Contiene 416 objetivos observados y
el último corresponde al 2025-07-28. La ventana de entrenamiento es móvil de 52
semanas, el holdout abarca 20 semanas calendario, se mantienen cinco orígenes
internos y cuatro horizontes.

| Avance | Orígenes de evaluación | Objetivos monetarios válidos | Filas origen por horizonte |
| ---: | ---: | ---: | ---: |
| 3 semanas | 6 | 24 | 24 |
| 1 semana | 17 | 68 | 68 |

Las pruebas confirman que la última etiqueta de entrenamiento es anterior al
origen, la fecha objetivo es `origen + horizonte - 1`, los orígenes internos
quedan purgados antes del corte y las cuatro ablaciones conservan particiones
idénticas. El hash común de `particiones.csv` para las ablaciones es
`ac32427be2ae442565ad0c0f26446321825d365ebbfa24d53852d644796479ff`.

## Selección operativa basada solo en validación interna

La selección cambió al cambiar la cuadrícula de orígenes internos, pero en
ambos protocolos se realizó antes de abrir la evaluación final.

| Horizonte | Step 3 | Step 1 | Peso estadístico |
| ---: | --- | --- | ---: |
| 1 | SES + RF | ARIMA de espacio de estados + corrector residual MLP | 0.75 |
| 2 | SES + HGB | ARIMA de espacio de estados + corrector residual MLP | 0.75 |
| 3 | ARIMA de espacio de estados + corrector residual MLP | ARIMA de espacio de estados + corrector residual MLP | 0.75 |
| 4 | ARIMA de espacio de estados + corrector residual RF | ARIMA de espacio de estados + corrector residual MLP | 0.75 |

El parámetro de composición permaneció en `alpha=0.1`; también permanecieron
las 11 categorías individuales. Ningún dato del bloque final se usó para
reconfigurar estos modelos.

## Métricas del híbrido step 3 frente a step 1

| Horizonte | n step 3 | RMSE step 3 | MAE step 3 | n step 1 | RMSE step 1 | MAE step 1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 6 | 521.60 | 386.43 | 17 | 903.90 | 528.11 |
| 2 | 6 | 695.41 | 439.26 | 17 | 1001.94 | 544.58 |
| 3 | 6 | 801.62 | 458.80 | 17 | 1252.90 | 639.21 |
| 4 | 6 | 700.88 | 572.54 | 17 | 1349.96 | 720.06 |

La diferencia de métricas no debe interpretarse como deterioro causado solo por
el tamaño de paso: `step=1` incorpora once orígenes adicionales y modifica los
cinco orígenes internos que determinan la selección. Es una evaluación más
densa del mismo periodo, no una repetición de la misma muestra.

## Menor error observado por horizonte

La tabla siguiente usa únicamente la comparación principal sobre fechas
comunes. Describe el menor RMSE observado; no reemplaza la selección operativa.

| Protocolo | Horizonte | Modelo con menor RMSE observado | n | RMSE |
| --- | ---: | --- | ---: | ---: |
| Step 3 | 1 | RF | 6 | 446.21 |
| Step 3 | 2 | HGB | 6 | 596.17 |
| Step 3 | 3 | Híbrido seleccionado | 6 | 801.62 |
| Step 3 | 4 | Corrector residual RF sobre ARIMA | 6 | 578.95 |
| Step 1 | 1 | Último valor observado | 17 | 620.30 |
| Step 1 | 2 | Último valor observado | 17 | 779.36 |
| Step 1 | 3 | Último valor observado | 17 | 804.04 |
| Step 1 | 4 | Último valor observado | 17 | 863.30 |

`promedio_4s` obtuvo RMSE descriptivamente menor en `step=1` para los cuatro
horizontes, pero el pipeline lo clasifica como referencia complementaria de
disponibilidad propia, no como candidato de selección. No se adopta a partir del
bloque final.

## H1 y lectura correcta del signo

Las diferencias están definidas como pérdida de la referencia histórica menos
pérdida del método propuesto:

- importe: error cuadrático de `ultimo_valor` menos error cuadrático del híbrido;
- composición: MAE porcentual de `participacion_historica` menos MAE porcentual
  de `participacion_ewm`.

Por tanto, un valor positivo favorece al método propuesto y un valor negativo
favorece a la referencia histórica.

| Componente | Step 3 | Step 1 | Lectura step 1 |
| --- | --- | --- | --- |
| Importe h=1 | n=6; media 161798.64; muestra insuficiente | n=17; media -432255.66; IC simultáneo [-1047433.38, 62131.74] | Media favorable a `ultimo_valor`; intervalo incluye cero |
| Composición h=1 | n=3; media -1.3880 pp; muestra insuficiente | n=9; media 0.4066 pp; muestra insuficiente | Media descriptiva favorable a EWM, sin intervalo admisible |

H1 no tiene evidencia favorable simultánea y no posee respaldo confirmatorio.

El bootstrap conserva el protocolo: circular, pareado, bloque de cuatro
semanas, 2000 remuestreos, mínimo 12 y cuantiles Bonferroni 1.25% y 98.75% para
dos componentes. En `h=1` los 17 objetivos monetarios son semanas distintas,
pero las ventanas de entrenamiento consecutivas se solapan intensamente; el
bloque de cuatro conserva dependencia local, sin demostrar que capture toda la
dependencia serial. Los horizontes 2 a 4 comparten fechas objetivo entre
orígenes, pero no intervienen en el contraste H1, que está fijado en `h=1`. Los
9 pares composicionales quedan por debajo del mínimo 12 y no se debe fabricar
un intervalo con ellos.

## Composición

En `step=1`, los errores macro fueron:

| Horizonte | EWM MAE pp | Histórico MAE pp | Pares válidos |
| ---: | ---: | ---: | ---: |
| 1 | 9.3370 | 9.7437 | 9 |
| 2 | 9.5505 | 9.3378 | 10 |
| 3 | 10.0711 | 9.6684 | 11 |
| 4 | 10.5247 | 10.2217 | 12 |

El candidato EWM fue descriptivamente mejor solo en `h=1`; el histórico tuvo
menor MAE macro en `h=2`, `h=3` y `h=4`. Esto tampoco autoriza seleccionar por
el bloque final.

## Verificación de las copias de promedio simple

Las corridas `49188a` y `ab4e3e` difieren en la configuración únicamente por
`imputation_start` e `imputation_end`. Son idénticos, incluyendo sus hashes:

- panel original, particiones y selección interna;
- predicciones y métricas monetarias;
- composición y métricas de composición;
- H1;
- pronóstico semanal y consolidado de cuatro semanas.

El archivo `modelos.joblib` tiene un hash de archivo distinto porque el paquete
serializa la configuración. Después de cargar ambos artefactos locales de
confianza, todas las claves salvo `config` tienen el mismo hash de contenido,
incluidos modelos ajustados, selección, categorías, variables, participaciones
y origen de emisión. Los cuatro archivos de promedio simple solo existen en la
corrida que los solicita. Esto demuestra que esas copias no participan en el
entrenamiento ni en la evaluación.

## Ablaciones con particiones idénticas

Todos los modelos conservan la codificación cíclica básica de semana. En esta
tabla, calendario significa las banderas opcionales `es_fecha_pago_semana` y
`es_festivo_semana`.

| Predictores | RMSE h1 | RMSE h2 | RMSE h3 | RMSE h4 |
| --- | ---: | ---: | ---: | ---: |
| Compras | 902.50 | 1003.54 | 1253.77 | 1350.21 |
| Compras + ventas | 902.82 | 1003.29 | 1253.20 | 1349.48 |
| Compras + calendario | 902.49 | 1003.63 | 1253.23 | 1350.57 |
| Compras + ventas + calendario | 903.90 | 1001.94 | 1252.90 | 1349.96 |

Las diferencias son pequeñas, cambian de signo por horizonte y no establecen un
aporte general de ventas o calendario. La familia y el peso elegidos
internamente fueron iguales en las cuatro ablaciones. La composición y sus
métricas también fueron idénticas por hash, porque esas fuentes opcionales solo
alimentan el modelo monetario actual. No se atribuyen aportes causales.

## Auditoría de categorías 15 a 11 más RESTO ELEGIBLE

El panel contiene 35 categorías elegibles después de las seis exclusiones. La
Figura 4 muestra descriptivamente las 15 de mayor importe, que acumulan 90.02%
del importe de desarrollo. Ese número 15 es un límite de visualización, no la
regla de selección composicional.

La regla fija categorías individuales hasta rebasar el umbral de 80%. Las once
seleccionadas son HARINA, CHOCOLATE, FONDANT, EMPAQUE, CHANTILLY, RELLENO,
DECORACION, AMBIENTE, HUEVO, CAPACILLOS y BASES. Con BASES, la acumulación
alcanza 82.29%. Las otras cuatro categorías del top 15 —QUESO CREMA,
MANTEQUILLA, ADMINISTRACION y NO DEFINIDO— se integran en `RESTO_ELEGIBLE`
junto con las 20 categorías elegibles menores restantes.

La transición es, por tanto, de una vista exploratoria top 15 a once categorías
modeladas individualmente más un residual reconciliador. `RESTO_ELEGIBLE` no es
la categoría fuente `OTROS`, que se excluye antes de construir el objetivo.

## Limitaciones y recomendación

- La ampliación aumenta pares monetarios, pero reutiliza el mismo periodo final;
  no constituye evidencia independiente.
- La cobertura registra importes utilizables, no certifica exhaustividad del
  gasto semanal.
- La composición sigue por debajo del mínimo inferencial en `h=1`.
- Las ventanas rolling consecutivas y los horizontes superpuestos generan
  dependencia; el bootstrap por bloques la mitiga parcialmente.
- Las ablaciones son comparaciones predictivas asociativas, no estimaciones
  causales del aporte de cada fuente.
- No debe describirse ningún resultado como óptimo o mejor posible.

Se recomienda usar `step=1` como análisis de sensibilidad ampliado y conservar
la conclusión negativa de H1. Si se desea sostener inferencia, se necesita una
evaluación prospectiva o un bloque temporal nuevo, con protocolo congelado y
mayor cantidad de pares composicionales válidos.

## Mapa propuesto de cambios para Rev62

Este mapa requiere aprobación antes de editar Rev61.

### Metodología

Explicitar la sensibilidad `step=1`, los 17 orígenes, la diferencia entre
evaluación ampliada y confirmación independiente, el solapamiento de ventanas,
el signo de las diferencias de pérdidas y el papel complementario de las
ablaciones. Mantener la selección exclusivamente en validación interna.

### Desarrollo

Actualizar el contrato de entorno a `joblib==1.5.2`; describir las dos
configuraciones rolling sin reemplazar la original; explicar que las copias de
promedio simple son productos de auditoría; distinguir calendario cíclico común
de las banderas opcionales de pago y festivo.

### Resultados

Añadir una tabla `step=3` contra `step=1`, la selección interna por horizonte,
el menor RMSE observado en la comparación principal, H1 con sus pares e
intervalos, la tabla de ablaciones y la auditoría top 15 a 11 más
`RESTO_ELEGIBLE`. Identificar las corridas por ID.

### Discusión

Explicar por qué la evaluación más densa cambia la lectura respecto de seis
orígenes, por qué el resultado final no reconfigura el modelo, por qué no se
puede atribuir un aporte general a ventas/calendario y por qué el solapamiento
limita la inferencia.

### Conclusiones

Mantener que H1 no recibe respaldo; indicar que `ultimo_valor` tuvo el menor
RMSE principal observado en los cuatro horizontes de `step=1`; evitar
“óptimo”, “mejor posible” y cualquier afirmación confirmatoria.

### Resumen y Abstract

Actualizar conteos, alcance retrospectivo, resultado negativo de H1 y
limitación composicional. Mantener equivalencia exacta entre ambos idiomas.

### Referencias

Revisar si las afirmaciones nuevas sobre validación temporal dependiente y
bootstrap por bloques requieren una fuente metodológica adicional. No añadir
referencias solo para adornar; cada cita debe respaldar una afirmación concreta.

### Anexo B

Incluir las configuraciones `step=1`, la tabla de hashes de reproducción y sin
imputación, IDs de las cuatro ablaciones, definición del signo, conteos de pares
y reglas de categorías. Conservar `step=3` para trazabilidad histórica.

## Punto de aprobación

No se editará Rev61 hasta recibir aprobación explícita del usuario para crear
Rev62 a partir de este mapa.
