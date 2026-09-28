# Revisión de dirección de tesis Rev57

## Alcance y dictamen ejecutivo

Se revisó el borrador completo `TESIS_AGO2026_Rev57_(ZUJ).docx`, de 106 páginas renderizadas. La revisión cubrió congruencia entre problema, pregunta, objetivos, hipótesis, metodología, resultados, discusión y conclusiones; suficiencia de la evidencia; redacción científica; referencias y presentación visual. No se verificaron externamente todos los DOI ni se reprodujo la corrida computacional, por lo que esos puntos permanecen fuera del dictamen.

**Dictamen:** el trabajo tiene un núcleo técnico defendible como estudio de desarrollo y evaluación exploratoria, pero **todavía no está listo para entrega ni para predefensa**. Hay tres hallazgos críticos: (1) la pregunta carece de delimitación temporal explícita y no identifica con suficiente precisión la unidad o población; (2) el objetivo general no se deriva de la pregunta y cambia el acto rector de “determinar la precisión” a “desarrollar”; y (3) el diseño descrito contiene especificaciones contradictorias, mientras que la evaluación efectiva —seis orígenes monetarios y entre tres y cinco observaciones composicionales— no permite sostener una validación confirmatoria.

La tesis no fracasa porque H1 no haya sido respaldada. Al contrario, el tratamiento prudente de ese resultado es una fortaleza. El problema es de **alineación y suficiencia de evidencia**, no de que el híbrido deba ganar.

## Fortalezas verificadas

- Los resultados distinguen entre consistencia computacional y precisión predictiva.
- Se informa que el híbrido solo obtuvo el menor RMSE en el horizonte de tres semanas y se evita presentarlo como superior en general.
- La discusión reconoce la muestra reducida, la cobertura no certificada, la imputación de 29 semanas y la ausencia de intervalos válidos.
- Las conclusiones responden con prudencia a H1 y no confunden falta de evidencia con equivalencia entre métodos.
- El procedimiento mantiene trazabilidad de categorías excluidas, `RESTO_ELEGIBLE`, huecos, folds y artefactos de ejecución.
- La comparación incluye líneas base y separa el error monetario del error de participación.

## Evaluación obligatoria de la pregunta de investigación

Pregunta actual:

> ¿Qué precisión ofrece un modelo híbrido que integra métodos estadísticos y aprendizaje automático, mediante evaluación temporal de su precisión frente a modelos de referencia, para estimar el importe total semanal de compras y su distribución porcentual entre los principales insumos, como apoyo a la planeación del presupuesto de abastecimiento en una microempresa de repostería creativa de Tizayuca, Hidalgo?

| Componente obligatorio | Estado | Observación |
|---|---|---|
| Expresión interrogativa | Presente | “¿Qué precisión ofrece...?” |
| Variable independiente X | Presente | Modelo híbrido estadístico y de aprendizaje automático. |
| Relación investigable | Presente | Comparación de precisión frente a modelos de referencia. |
| Variable dependiente Y | Presente | Error o precisión del importe semanal y de la composición porcentual. |
| Población o unidad de análisis | Parcial | Se menciona una microempresa, pero no las semanas/registros evaluados ni Cup&Cake por nombre. |
| Contexto institucional | Parcial | El caso se identifica de modo genérico, no como Cup&Cake. |
| Contexto geográfico | Presente | Tizayuca, Hidalgo. |
| Delimitación temporal | Ausente | No aparece el periodo ni la fecha de corte de la evaluación. |

La ausencia temporal es crítica. Además, el documento maneja al menos tres alcances temporales que deben conciliarse: fuentes 2022–2026 en Metodología, panel 2016–2026 en Resultados y emisión histórica con origen del 4 de agosto de 2025.

**Reformulación propuesta, condicionada a fijar primero el periodo efectivo:**

> ¿Qué precisión ofrece, frente a modelos de referencia y mediante validación temporal, un modelo híbrido de métodos estadísticos y aprendizaje automático para estimar el importe total semanal de compras y su distribución porcentual entre los principales insumos de Cup&Cake, microempresa de repostería creativa de Tizayuca, Hidalgo, con los registros disponibles y verificables del periodo **[fecha inicial efectiva–fecha de corte efectiva]**?

No debe sustituirse el marcador temporal hasta conciliar las fuentes, el panel y el bloque evaluado.

## Objetivo general propuesto

El objetivo actual empieza con “Desarrollar”, aunque la pregunta empieza con “¿Qué precisión ofrece...?”. Esto cambia el alcance rector. Conforme a la regla de derivación mínima, propongo:

> Determinar la precisión que ofrece, frente a modelos de referencia y mediante validación temporal, un modelo híbrido de métodos estadísticos y aprendizaje automático para estimar el importe total semanal de compras y su distribución porcentual entre los principales insumos de Cup&Cake, microempresa de repostería creativa de Tizayuca, Hidalgo, con los registros disponibles y verificables del periodo **[fecha inicial efectiva–fecha de corte efectiva]**.

El desarrollo del modelo debe conservarse como objetivo específico. Así, el resultado negativo o no confirmatorio no impide cumplir el objetivo general: determinar la precisión puede concluir que esta es inestable o insuficientemente demostrada.

## Matriz de trazabilidad

| Elemento rector | Método o evidencia | Resultado observado | Conclusión | Estado |
|---|---|---|---|---|
| Pregunta / precisión del híbrido y composición | Rolling window, comparadores y métricas monetarias y composicionales | Seis orígenes por horizonte; tres a cinco casos composicionales; desempeño dependiente del horizonte | No existe ventaja general ni evidencia confirmatoria | Parcial |
| OE1 Analizar y depurar registros | Auditoría, agregación semanal y panel | Panel construido; 29 semanas de compras imputadas; cobertura no certificada | Cumplimiento técnico condicionado por calidad de datos | Parcial |
| OE2 Desarrollar el híbrido | SES, ARIMA, Ridge, RF, HGB, MLP y combinaciones | Configuraciones seleccionadas por horizonte | Desarrollo realizado; estabilidad no demostrada | Verificado para desarrollo |
| OE3 Determinar distribución porcentual | Participación histórica y promedio temporal ponderado | El método ganador alterna entre horizontes | No hay método dominante; pocos casos válidos | Parcial |
| OE4 Contrastar precisión | Comparación temporal con referencias | Híbrido pierde en RMSE en h=1, h=2 y h=4; gana en h=3 | Contraste ejecutado, pero exploratorio | Parcial |
| H1 Superioridad conjunta | Diferencias de pérdidas pareadas | Seis pares monetarios y tres composicionales; sin intervalos válidos | H1 no respaldada; resultado no confirmatorio | No cumple como confirmación |

## Hallazgos consolidados

| ID | Severidad | Ubicación o evidencia | Hallazgo | Impacto | Acción correctiva | Verificación |
|---|---|---|---|---|---|---|
| H01 | Crítico | Pregunta, p. 16 | Falta delimitación temporal; población/unidad e institución son parciales. | Incumple la formulación obligatoria y deja ambiguo qué evidencia responde la pregunta. | Conciliar el periodo efectivo y reformular con Cup&Cake y los registros/semanas observados. | Los ocho componentes aparecen explícitos. |
| H02 | Crítico | Objetivo general, p. 17 | Cambia “determinar precisión” por “desarrollar” y no se deriva de la pregunta. | Rompe la cadena pregunta–objetivo–resultados. | Adoptar el objetivo propuesto y conservar “desarrollar” como OE. | Comparación textual pregunta/objetivo sin cambio de alcance. |
| H03 | Crítico | Metodología, pp. 39–47; Resultados, pp. 63–68 | El protocolo declara avance de una semana en una sección y de tres semanas en otras; también alterna entre trabajo futuro y corrida ya ejecutada. | Impide reproducir con certeza el diseño y distinguir protocolo planeado de efectivo. | Reescribir Metodología en pasado, declarar una única configuración final y separar decisiones previas de desviaciones ejecutadas. | Una tabla de protocolo único coincide con manifiesto y Resultados. |
| H04 | Crítico | Resultados y limitaciones, pp. 63–73 | Solo hay seis orígenes monetarios por horizonte y tres a cinco observaciones composicionales; 29 semanas de compras fueron imputadas y la captura no está certificada. | La pregunta no puede contestarse con fiabilidad confirmatoria ni sostener superioridad. | Reposicionar formalmente el alcance como exploratorio o ampliar y certificar datos antes de una pretensión confirmatoria. Añadir sensibilidad excluyendo semanas imputadas. | Resultados con análisis de sensibilidad y alcance explícito desde pregunta/resumen. |
| H05 | Importante | Resumen, p. 12; Abstract, p. 13 | Ambos están en futuro y omiten los resultados principales, aunque la tesis ya reporta una corrida completa. | El lector recibe un protocolo, no una síntesis de la tesis terminada. | Reescribir en pasado: objetivo, datos, diseño efectivo, n, métricas clave, hallazgo negativo y conclusión. | Coincidencia exacta con Resultados y Conclusiones. |
| H06 | Importante | Índice y listas, pp. 4–12 | Hay numerosos “¡Error! Marcador no definido.”, numeración obsoleta y enlaces de figuras/tablas antiguas. | Defecto formal evidente que compromete la entrega. | Reparar campos, títulos, marcadores y numeración; actualizar índice y lista completa. | Exportación limpia sin errores de campo. |
| H07 | Importante | pp. 16–32 y otras páginas | Permanece resaltado multicolor de edición en pregunta, objetivos, justificación y marco. | El archivo parece una copia de trabajo, no versión de entrega. | Retirar resaltado y aceptar o resolver revisiones pendientes después de estabilizar el contenido. | Revisión visual de las 106 páginas. |
| H08 | Importante | Metodología, pp. 39–45 | Abundan definiciones genéricas de “investigar”, “cuantitativa” y “deductiva”; algunas afirman generalización/causalidad que luego se niega para el caso. | Añade contradicciones y desplaza el procedimiento reproducible. | Reducir el contenido enciclopédico y describir decisiones reales: unidad, periodo, fuentes, limpieza, imputación, particiones, selección, métricas y controles. | Cada apartado metodológico responde “qué se hizo y por qué”. |
| H09 | Importante | Metodología y anexos | No se localiza una sección suficiente de ética, autorización de uso, confidencialidad y tratamiento de identificadores personales. | Riesgo documental por registros empresariales y campos administrativos/personales. | Añadir procedencia, autorización, minimización, exclusiones, almacenamiento, acceso y anonimización. | Evidencia institucional o declaración verificable incluida. |
| H10 | Importante | Referencias, pp. 77–86 | La lista presenta orden inconsistente y las dos obras Makridakis 2018 aparecen como 2018b antes de 2018a, mientras varias citas en texto usan solo 2018. Ordonez aparece después de Zhang. | Incumple correspondencia y orden APA 7; puede volver ambigua la fuente citada. | Hacer auditoría bidireccional, uniformar 2018a/2018b, autores corporativos y orden alfabético. | Cada cita tiene una referencia única y viceversa. |
| H11 | Menor | Portada, p. 1 | La fecha dice 28 de agosto de 2025, pero la corrida y el borrador son de septiembre de 2026. | Inconsistencia visible de versión. | Actualizar cuando la institución confirme fecha y formato. | Portada coincide con la versión de entrega. |
| H12 | Menor | Conclusiones, pp. 73–75 | La sección deja una página final casi vacía por un corte poco natural. | Afecta acabado editorial. | Ajustar saltos y mantener títulos con el texto siguiente. | Render sin páginas residuales innecesarias. |

## Trazabilidad de fuentes y APA 7

La bibliografía tiene buena presencia de fuentes de jerarquía muy alta y alta: Springer, Elsevier, *International Journal of Forecasting*, *European Journal of Operational Research*, *PLOS ONE*, *Science* y literatura metodológica clásica. Las obras clásicas están justificadas cuando sustentan combinación de pronósticos, datos composicionales, métricas y evaluación temporal.

Pendientes documentales:

- Verificar bidireccionalmente todas las citas y referencias; esta revisión no valida externamente todos los metadatos ni DOI.
- Corregir la desambiguación Makridakis et al. (2018a, 2018b) en el texto.
- Uniformar `OCDE`/`OECD` según el autor corporativo elegido en la referencia.
- Revisar entradas con títulos o atribuciones cercanas sobre desperdicio y pronóstico en panaderías para evitar confusión entre Hübner et al. y Martins-Turner et al.
- Ordenar alfabéticamente toda la lista y aplicar sangría francesa, cursivas, mayúsculas y rangos de páginas de forma consistente.

## Riesgos de defensa

1. **¿Cuál es exactamente el periodo de estudio?** Hoy el documento da tres respuestas diferentes.
2. **¿Por qué se imputaron 29 semanas por promedio simple y cómo cambia el ranking si se excluyen?** Falta un análisis de sensibilidad visible.
3. **¿Cómo puede sostenerse H1 con seis pares monetarios y tres composicionales?** La respuesta correcta es que no puede sostenerse confirmatoriamente con esta corrida.
4. **¿Por qué el objetivo general dice desarrollar si la pregunta pide precisión?** Debe corregirse antes de la defensa.
5. **¿Qué aporta el híbrido si pierde ante comparadores en tres de cuatro horizontes?** Aporta evidencia contextual, un procedimiento reproducible y un resultado negativo útil; no superioridad.
6. **¿Por qué usar MLP y no LSTM/RNN?** La tesis sí ofrece una defensa razonable: tamaño reducido y comparación homogénea, pero debe evitar que figuras o antecedentes obsoletos sugieran que se implementaron arquitecturas recurrentes.
7. **¿El pronóstico de agosto de 2025 puede apoyar decisiones en 2026?** No; el propio texto lo reconoce y debe mantener esa respuesta.

## Plan de corrección priorizado

| Orden | IDs | Acción | Dependencia | Esfuerzo | Estado | Criterio de cierre |
|---:|---|---|---|---|---|---|
| 1 | H01–H02 | Fijar periodo, pregunta y objetivo general. | Ninguna | Medio | Pendiente | Ocho componentes y derivación exacta. |
| 2 | H03–H04 | Congelar protocolo efectivo y decidir alcance exploratorio o nueva evaluación. | 1 | Alto | Pendiente | Metodología, resultados y manifiesto coinciden. |
| 3 | H04 | Ejecutar sensibilidad sin semanas imputadas o justificar formalmente su imposibilidad. | 2 | Alto | Pendiente | Tabla comparativa y conclusión proporcional. |
| 4 | H05, H08–H09 | Reescribir resumen, metodología y ética según lo realmente ejecutado. | 2–3 | Medio | Pendiente | Verbos en pasado y sin contradicciones. |
| 5 | H10 | Auditar citas y referencias APA 7. | Contenido estable | Medio | Pendiente | Correspondencia bidireccional completa. |
| 6 | H06–H07, H11–H12 | Limpiar campos, resaltados, portada y saltos. | Contenido estable | Bajo/medio | Pendiente | Render final limpio de 106 páginas o menos. |

## Condición para avanzar

Puede afirmarse que existe un procedimiento reproducible, que el híbrido no mostró una ventaja general y que la evidencia actual es exploratoria. No puede afirmarse todavía que la precisión sea estable, que H1 haya sido confirmada ni que el sistema esté validado para uso presupuestario operativo.

El siguiente cambio de mayor impacto es **fijar el periodo efectivo y corregir en una sola sesión la pregunta, el objetivo general y la configuración metodológica final**. Toda corrección editorial debe hacerse después de estabilizar esa cadena.
