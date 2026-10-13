# Decisión de reproducibilidad: versión de `joblib`

Fecha de decisión: 2026-10-13.

## Discrepancia observada

La corrida histórica `run_20260924T195600Z_86a6f5` registra `joblib==1.5.2` en
`manifiesto.json`, mientras que `codigos/requirements_hibrido.txt` declaraba
`joblib==1.5.3`. Las demás versiones registradas en el manifiesto coinciden con
el entorno disponible en `C:\Python310\python.exe`.

## Decisión

Se fija `joblib==1.5.2` en `requirements_hibrido.txt`. Para reproducir la corrida
histórica se considera canónico el entorno capturado por su manifiesto, porque
ese archivo registra el software que efectivamente produjo los artefactos. No se
atribuye equivalencia numérica a `joblib==1.5.3` sin una comparación separada.

## Comprobaciones requeridas

1. Verificar que las versiones de Python y dependencias coincidan con el
   manifiesto histórico.
2. Verificar que los hashes de las fuentes y de los 14 archivos de código
   coincidan con el manifiesto.
3. Ejecutar la configuración histórica sin sobrescribir la corrida original.
4. Comparar métricas, selección interna, predicciones, particiones e H1; los
   artefactos de presentación o serialización no se consideran sustitutos de
   esas comparaciones científicas.

## Alcance

Esta decisión corrige el contrato de instalación reproducible. No modifica la
tesis ni reinterpreta los resultados históricos.
