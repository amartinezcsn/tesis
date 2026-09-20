"""Documenta la procedencia de cada asignación nueva del catálogo."""

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hibrido.data import fingerprint, load_purchases


ROOT = Path('C:/Python/tesis')
BASE = Path('outputs/revision_datos_20260919')
SOURCE = ROOT / 'datasets/xlsx/Compras.xlsx'
WORKBOOK = BASE / 'revision_catalogo_cobertura_sin_ceros.xlsx'
ASSIGNMENTS = BASE / 'asignaciones_insumo_id.json'
OUTPUT = BASE / 'evidencias_catalogo.json'
CONFIG = json.loads(Path('02_config_hibrido.json').read_text(encoding='utf-8'))

SPECIAL = {
    'FOUNDANT': 'Se corrige la grafía FOUNDANT a fondant; la presentación no consta.',
    'CREMA PARA BATIR AMBIANTE 1 LT': 'Se normaliza la grafía AMBIANTE a ambiente y se conserva 1 L.',
    'TEGRAL SATIN CREME CA': 'Se interpreta CA como abreviatura de CAKE; se conserva sabor no especificado.',
    'TEGRAL SATIN CREME CAKE PURATOS': 'Misma denominación base TEGRAL SATIN CREME CAKE; marca Puratos explícita sólo aquí.',
    'CHANTILLI DULL': 'Se normaliza CHANTILLI a chantilly; DULL se conserva literalmente.',
    'CHANT DULL': 'Se interpreta CHANT como abreviatura de chantilly; DULL se conserva literalmente.',
    'INIX CONTENEDOR MANTECADAS 25 PZ': 'Se conserva contenedor INIX de 25 piezas.',
    '2 PAQ INIX CONTENEDOR MANTECADA 25 PZ': 'Se conserva contenedor INIX de 25 piezas; 2 PAQ describe cantidad comprada.',
    'DOMO 1/2 PLANCHA INI': 'Se interpreta INI como truncamiento de INIX; se conserva media plancha.',
    'DOMO 1/2 DE PLANCHA INIX': 'Se conserva domo INIX de media plancha.',
    'KISSES LECHE': 'Se conserva denominación KISSES LECHE.',
    'KISS LECHE': 'Se interpreta KISS como forma singular de KISSES LECHE.',
    'ROYAL ICING DEIMAN 50': 'Se conserva el número 50 sin atribuirle unidad.',
    'BASE 33X3': 'Se conserva literalmente 33X3; la segunda medida no se corrige ni infiere.',
    'FERRERO ROCHER T-16': 'Se conserva T-16 como presentación distinta de la denominación genérica.',
}


def main():
    if fingerprint(SOURCE) != CONFIG['source_sha256']:
        raise ValueError('La fuente original no coincide con el hash aprobado.')
    purchases, rejected = load_purchases(
        SOURCE, CONFIG['source_sheet'],
        approved_duplicate_rows=CONFIG['approved_duplicate_rows'],
    )
    if not rejected.empty:
        raise ValueError('La fuente tiene registros rechazados inesperados.')
    purchases = purchases.loc[purchases.semana_inicio.between(CONFIG['start'], CONFIG['end'])]
    catalog = pd.read_excel(WORKBOOK, sheet_name='Catalogo')
    assignments = json.loads(ASSIGNMENTS.read_text(encoding='utf-8'))['asignaciones']
    pending_names = {item['descripcion_normalizada'] for item in assignments}
    original_ids = defaultdict(set)
    for row in catalog.itertuples():
        if row.descripcion_normalizada not in pending_names and pd.notna(row.insumo_id):
            original_ids[str(row.insumo_id)].add(str(row.descripcion_normalizada))
    evidence = []
    for item in assignments:
        excel_row = item['fila_excel']
        name = item['descripcion_normalizada']
        cat = catalog.iloc[excel_row - 2]
        source_rows = purchases.loc[purchases.descripcion_normalizada.eq(name)].sort_values('registro_id')
        if cat.descripcion_normalizada != name or cat.insumo_id != item['insumo_id']:
            raise ValueError(f'La asignación no coincide con el catálogo en fila {excel_row}.')
        if not str(cat.evidencia).startswith('Pendiente de homolog'):
            raise ValueError(f'La evidencia ya no es provisional en fila {excel_row}.')
        if len(source_rows) != int(cat.registros) or abs(source_rows.importe_nominal.sum() - float(cat.importe_nominal_MXN)) > 0.01:
            raise ValueError(f'Los totales no reconcilian con la fuente en fila {excel_row}.')
        method = item['metodo']
        if name in SPECIAL:
            reason = SPECIAL[name]
        elif method == 'descripcion_especifica':
            reason = 'ID específico derivado de la descripción; no se fusiona con otra denominación.'
        elif method == 'id_preexistente':
            prior = ', '.join(sorted(original_ids[item['insumo_id']]))
            reason = f'Se reutiliza el ID ya presente en el catálogo para: {prior}.'
        else:
            reason = 'ID normalizado desde la denominación; no se supone marca, tamaño ni presentación ausente.'
        zero_only = bool(source_rows.importe_nominal.eq(0).all())
        if zero_only:
            reason += ' Las únicas filas tienen importe cero y no son objetivos válidos.'
        row_ids = [int(value) for value in source_rows.registro_id]
        sample = ','.join(map(str, row_ids[:3])) + ('…' if len(row_ids) > 3 else '')
        short = (
            f'Compras.xlsx/Hoja1 filas {sample} ({len(row_ids)} registros). '
            f'ID {item["insumo_id"]}. {reason} '
            f'Detalle: evidencias_catalogo.json, fila {excel_row}.'
        )
        evidence.append({
            'fila_catalogo': excel_row,
            'descripcion_normalizada': name,
            'insumo_id': item['insumo_id'],
            'metodo': method,
            'criterio': reason,
            'filas_fuente': row_ids,
            'descripciones_fuente': sorted(source_rows.descripcion.astype(str).unique().tolist()),
            'registros': len(row_ids),
            'importe_nominal_MXN': round(float(source_rows.importe_nominal.sum()), 2),
            'importe_cero_no_valido': zero_only,
            'evidencia_catalogo': short,
        })
    if len(evidence) != 319:
        raise ValueError(f'Se esperaban 319 evidencias, no {len(evidence)}.')
    OUTPUT.write_text(json.dumps({
        'fuente': str(SOURCE),
        'hoja': CONFIG['source_sheet'],
        'sha256': CONFIG['source_sha256'],
        'periodo': [CONFIG['start'], CONFIG['end']],
        'criterio_general': 'La descripción original y sus filas prueban la trazabilidad de la asignación; las inferencias de equivalencia se declaran expresamente. No sustituyen comprobantes de cobertura semanal.',
        'evidencias': evidence,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Evidencias:', len(evidence), 'cero-only:', sum(row['importe_cero_no_valido'] for row in evidence))
    print('Ejemplos:', [(row['fila_catalogo'], row['evidencia_catalogo']) for row in evidence[:3]])


if __name__ == '__main__':
    main()
