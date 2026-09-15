# Decisiones de alcance del catálogo

Fuente: aclaraciones del usuario en esta conversación y auditoría de Compras.xlsx correspondiente al periodo mayo de 2021 a junio de 2024. Se preserva el archivo original. Las decisiones de alcance no aprueban duplicados, ceros ni cobertura semanal.

## Decisiones aplicadas

- CASETAS: pagos de peaje; excluir.
- ADMINISTRACION: tarjetas, notas y publicidad según aclaración del usuario; excluir la categoría. Se conserva la descripción original incluso si difiere de estos ejemplos.
- OTROS: compras de una sola ocasión; excluir por indicación expresa, incluso si alguna descripción parece un ingrediente o empaque.
- NO DEFINIDO: excluir por indicación expresa.
- HORNEADO: incluir; identificar por descripción. Capacillos, fécula de maíz, vainilla y Carnation (leche evaporada) quedan dentro del alcance. El registro DMONTE ELOTE se conserva como ingrediente con identificador propio.
- CONSUMIBLES: incluir, con excepción de duyas. Las mangas se incluyen sin distinguir si son reutilizables, conforme a la última indicación del usuario. Se preservan los demás consumibles descritos en la fuente.
- DUYA/DUYAS: clasificar analíticamente como HERRAMIENTA y excluir, sin cambiar la clasificación en el Excel original.
- COMBUSTIBLE, MUEBLES y HERRAMIENTA: mantener exclusión previamente acordada.
- Registro 513: VARIOS ARTICULOS (DOMO, BASES, CAKETOPPER, SPRINKLES), importe 2000 MXN. Incluir como `compra_mixta_empaques_decoracion`; no repartir entre insumos. El 80% mencionado por el usuario es contextual y no constituye un desglose comprobado.

## Estado y límites

El catálogo contiene 563 descripciones del periodo, incluyendo las presentes en registros pendientes de la auditoría. Se guardaron 244 decisiones de alcance (151 inclusiones y 93 exclusiones). Otras 319 descripciones permanecen sin aprobar. La revisión autorizada de coincidencias claras resolvió 122 descripciones adicionales en 47 identificadores; no se aprobaron globalmente categorías completas.

La homologación conserva las descripciones originales y agrupa equivalencias textuales, errores evidentes de escritura o presentaciones identificables del mismo producto. Para ingredientes como Nutella y queso Philadelphia se agregan importes monetarios de distintas presentaciones; esto no normaliza cantidades físicas ni permite comparar precios unitarios. Se mantienen separados chocolate blanco y chips blancos, sabores de mezclas, bases dobles y sencillas, dimensiones explícitas y empaques sin capacidad identificada. Los registros genéricos conservan identificadores sin especificación: su agrupación no certifica identidad comercial de marca o formulación.

Ejemplos pendientes: BASE 33X3 no se corrigió a 33X33 sin confirmación; ROYAL ICING DEIMAN 50 no se interpretó como 500 g; PURATOS VAINILLA no se asignó a harina o relleno; MOLDE CUPCAKE (6 PZ) no se dio por desechable. La evidencia de esta etapa distingue la revisión del asistente autorizada por el usuario de una confirmación específica del negocio.

PLATO RIGIDO NEGRO RE aparece originalmente en OTROS y EMPAQUE. Por corrección expresa posterior del usuario, ambas apariciones se clasifican analíticamente como EMPAQUE y se incluyen bajo `plato_rigido_negro_re`. Esta corrección específica prevalece sobre la exclusión general de OTROS. Se conserva la vinculación por descripción, sin modificar la clasificación del Excel original.

La configuración ya apunta a `catalogo_alcance_revisado.csv`. `aprobado=True` solo acredita la decisión de alcance de esa descripción. La fuente continúa no aprobada; no se creó ni aprobó cobertura y no se ejecutó entrenamiento. No se modificó la tesis. El catálogo es parcial y el pipeline debe seguir bloqueando la ejecución real mientras existan decisiones pendientes.

SHA-256 de la fuente auditada: c47fab1d3545ecd309e9aebb4e7ae160da3fd2004ccca03c798c3c9cd8a41d57.
