# Validación del libro de revisión

Fecha: 2026-09-19. Entrada activa: `revision_catalogo_cobertura_trazada.xlsx`, hojas `Catalogo` y `Cobertura`. Fuente: `Compras.xlsx`, hoja `Hoja1`, con los 12 duplicados conservados. Los libros anteriores se conservan como referencia.

Se asignó `insumo_id` a las 319 filas incluidas que carecían de él: 3 reutilizan IDs existentes, 29 siguen una normalización manual y 287 conservan un ID derivado de la descripción específica. El detalle y los criterios están en `asignaciones_insumo_id.json`. Las 470 filas `incluir` ya tienen ID. La hoja `Cobertura` y todas las demás columnas y hojas se conservaron iguales.

Se documentó la trazabilidad de las 319 asignaciones a las filas originales de `Compras.xlsx`, con hash de fuente, descripciones originales, recuentos, importes y criterio individual en `evidencias_catalogo.json`. Las 319 celdas de `Catalogo.evidencia` enlazan esa auditoría y dejan de tener texto provisional; sus banderas `pendiente` se actualizaron a `false`. El resto del catálogo y las hojas `Cobertura` e `Instrucciones` no cambiaron. Las equivalencias inferidas se declaran como tales; la fuente no certifica por sí sola identidad exacta de SKU ni cobertura semanal.

La corrida real `outputs/ejecucion_real_20260919/run_20260919T212455Z_f0255d/` finalizó con estado `completado`. El manifiesto registra 86 productos y cinco controles de salida aprobados. El panel conserva 165 semanas calendario: 129 observadas y 36 inciertas, sin objetivos semanales cero. La evaluación y H1 son retrospectivas y exploratorias.

| Campo | Filas por resolver |
| --- | ---: |
| `Catalogo.insumo_id` vacío en filas `incluir` | 0 |
| `Catalogo.evidencia` provisional | 0 |
| `Catalogo.pendiente` | 0 |
| `Cobertura.evidencia` vacía en semanas `observada` | 0 |
| `Cobertura.fecha_revision` vacía en semanas `observada` | 0 |

Hay 36 semanas `incierta` y 129 `observada`. Las semanas `observada` tienen el texto genérico `ticket` y fecha 2026-09-19; el libro no identifica el comprobante individual por semana, por lo que esa evidencia no se puede verificar desde aquí.

Por decisión del usuario, ningún cero se considera válido. La semana iniciada el 2023-08-28 contiene cinco renglones incluidos con importe cero en las filas originales 512, 516, 517, 518 y 519 y está `incierta`. La semana del 2024-01-01 sólo contiene el peaje excluido de la fila 250; también está `incierta` porque no hay compras de insumos incluidas que acrediten un objetivo cero. La fuente original permanece intacta. La configuración activa fija `zero_targets_valid: false`.

Los recuentos y montos del libro indican únicamente transacciones presentes en el Excel. No acreditan por sí solos cobertura completa de compras en una semana.
