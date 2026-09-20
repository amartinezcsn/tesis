# Decisión sobre registros duplicados

Fecha: 2026-09-19. El usuario indicó conservar los 12 registros idénticos del archivo original `Compras.xlsx`, hoja `Hoja1`. Se conservan las filas de Excel 190, 191, 294, 296, 297, 298, 792, 798, 893, 895, 1417 y 1418. La decisión está registrada en `02_config_hibrido.json` como `approved_duplicate_rows`.

SHA-256 de la fuente auditada: `c47fab1d3545ecd309e9aebb4e7ae160da3fd2004ccca03c798c3c9cd8a41d57`. Se fijó este hash para que un cambio posterior en el Excel invalide la aprobación. El cargador conservó 1 682 filas y reportó cero registros pendientes.

Esta decisión cubre la fuente y sus duplicados. La inclusión de cada descripción y la cobertura de cada semana requieren las revisiones separadas indicadas en `revision_catalogo_cobertura.xlsx`.
