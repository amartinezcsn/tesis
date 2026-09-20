"""Propone IDs conservadores para descripciones incluidas sin homologar."""

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


SOURCE = Path('outputs/revision_datos_20260919/revision_catalogo_cobertura.xlsx')
OUTPUT = Path('outputs/revision_datos_20260919/asignaciones_insumo_id.json')

MANUAL = {
    'FOUNDANT': 'fondant_sin_especificacion',
    'CREMA PARA BATIR AMBIANTE 1 LT': 'crema_batir_ambiente_1_l',
    'TEGRAL SATIN CREME CA': 'tegral_satin_creme_cake_sabor_no_especificado',
    'TEGRAL SATIN CREME CAKE PURATOS': 'tegral_satin_creme_cake_sabor_no_especificado',
    'CHANTILLY DULCE': 'chantilly_dulce',
    'CHANTILLI DULL': 'chantilly_dull',
    'CHANT DULL': 'chantilly_dull',
    'EASY PASTEL TRES LECHES': 'easy_pastel_tres_leches_sabor_no_especificado',
    'TRANSFER': 'transfer_sin_especificacion',
    'HUEVO': 'huevo_sin_especificacion',
    'CAPACILLOS': 'capacillos',
    'CHOCOLATE': 'chocolate_sin_especificacion',
    'ACEITE': 'aceite_sin_especificacion',
    'GLORIA MAN': 'mantequilla_gloria_presentacion_no_especificada',
    'ROYAL ICING': 'royal_icing_sin_especificacion',
    'OREO': 'oreo_sin_especificacion',
    'FERRERO': 'ferrero_sin_especificacion',
    'FERRERO ROCHER': 'ferrero_rocher',
    'FERRERO ROCHER T-16': 'ferrero_rocher_t16',
    'HUEVO BLANCO SAN JUAN': 'huevo_san_juan',
    'INIX CONTENEDOR MANTECADAS 25 PZ': 'contenedor_mantecadas_inix_25_pz',
    '2 PAQ INIX CONTENEDOR MANTECADA 25 PZ': 'contenedor_mantecadas_inix_25_pz',
    'DOMO 1/2 PLANCHA INI': 'domo_media_plancha_inix',
    'DOMO 1/2 DE PLANCHA INIX': 'domo_media_plancha_inix',
    'KISSES LECHE': 'kisses_leche',
    'KISS LECHE': 'kisses_leche',
    'BASE 26 CM': 'base_26_cm',
    'BASE 30 CM': 'base_30_cm',
    'PERLAS': 'perlas_sin_especificacion',
    'CAKETOPPER': 'caketopper_sin_especificacion',
    'ROYAL ICING DEIMAN 50': 'royal_icing_deiman_50_sin_unidad',
    'BASE 33X3': 'base_33x3_medida_sin_confirmar',
}


def canonical(value):
    text = unicodedata.normalize('NFKD', str(value).upper())
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace('FOUNDANT', 'FONDANT').replace('CHANTILLI', 'CHANTILLY')
    text = re.sub(r'(?<=\d)\s*[X*]\s*(?=\d)', ' X ', text)
    text = re.sub(r'(?<=\d)(CM|KG|GR|G|ML|LT|PZ)\b', r' \1', text)
    text = re.sub(r'\b(PIEZAS|PIEZA|PZA|PZS)\b', 'PZ', text)
    text = re.sub(r'[^A-Z0-9]+', ' ', text)
    return ' '.join(text.split())


def specific_id(description, classification):
    words = canonical(description).lower().split()
    slug = '_'.join(words)
    if not slug:
        raise ValueError(f'Descripción vacía: {description!r}')
    if slug[0].isdigit():
        category = canonical(classification.split(',')[0]).lower().replace(' ', '_')
        slug = f'{category}_{slug}'
    if slug in {'otros', 'total'}:
        slug = f'insumo_{slug}'
    if len(slug) > 64:
        digest = hashlib.sha256(slug.encode()).hexdigest()[:8]
        slug = f'{slug[:55].rstrip("_")}_{digest}'
    return slug


def main():
    catalog = pd.read_excel(SOURCE, sheet_name='Catalogo')
    existing = catalog.loc[catalog.insumo_id.notna()]
    existing_ids = set(existing.insumo_id.astype(str))
    known = defaultdict(set)
    for row in existing.itertuples():
        known[canonical(row.descripcion_normalizada)].add(str(row.insumo_id))
    assignments = []
    for index, row in catalog.iterrows():
        if row['decision'] != 'incluir' or pd.notna(row['insumo_id']):
            continue
        name = str(row['descripcion_normalizada'])
        if name in MANUAL:
            item_id = MANUAL[name]
            method = 'id_preexistente' if item_id in existing_ids else 'normalizacion_manual'
        elif len(known[canonical(name)]) == 1:
            item_id, method = next(iter(known[canonical(name)])), 'equivalencia_textual'
        else:
            item_id, method = specific_id(name, str(row['clasificacion_original'])), 'descripcion_especifica'
        assignments.append({
            'fila_excel': int(index + 2),
            'descripcion_normalizada': name,
            'insumo_id': item_id,
            'metodo': method,
            'importe_nominal_MXN': float(row['importe_nominal_MXN']),
        })
    if len(assignments) != 319:
        raise ValueError(f'Se esperaban 319 IDs nuevos, se propusieron {len(assignments)}.')
    ids = [row['insumo_id'] for row in assignments]
    if any(not item or item in {'total', 'otros'} for item in ids):
        raise ValueError('ID vacío o reservado.')
    by_id = defaultdict(list)
    for row in assignments:
        by_id[row['insumo_id']].append(row['descripcion_normalizada'])
    shared = {key: value for key, value in by_id.items() if len(value) > 1}
    OUTPUT.write_text(json.dumps({
        'origen': SOURCE.name,
        'criterio': 'Propuesta conservadora: se reutilizan IDs existentes cuando la equivalencia es clara; las demás descripciones conservan un ID específico. La evidencia de catálogo requiere revisión independiente.',
        'asignaciones': assignments,
        'ids_compartidos_nuevos': shared,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print('metodos', dict(Counter(row['metodo'] for row in assignments)))
    print('ids_nuevos_distintos', len(set(ids)))
    print('ids_compartidos_nuevos', shared)
    print('primeros', assignments[:12])


if __name__ == '__main__':
    main()
