"""Intermedio JSON para el libro de revisión; no aprueba datos."""

import json
from pathlib import Path

import pandas as pd

from hibrido.cli import ROOT
from hibrido.config import load_config
from hibrido.data import load_purchases


def main():
    cfg = load_config('02_config_hibrido.json')
    valid, rejected = load_purchases(
        ROOT / cfg.source,
        cfg.source_sheet,
        approved_duplicate_rows=cfg.approved_duplicate_rows,
    )
    if not rejected.empty:
        raise ValueError('La fuente conserva incidencias sin resolver.')
    valid = valid.loc[valid.semana_inicio.between(cfg.start, cfg.end)].copy()
    catalog = pd.read_csv(ROOT / cfg.catalog).copy()
    stats = valid.groupby('descripcion_normalizada', dropna=False).agg(
        registros=('registro_id', 'size'),
        importe_nominal=('importe_nominal', 'sum'),
        clasificacion_original=('CLASIFICACION', lambda x: ', '.join(sorted(set(x.dropna().astype(str))))),
    )
    catalog = catalog.join(stats, on='descripcion_normalizada')
    if catalog.registros.isna().any():
        raise ValueError('El catálogo contiene descripciones fuera del periodo auditado.')
    catalog['pendiente'] = catalog.decision.eq('revisar') | ~catalog.aprobado.astype(bool)
    catalog = catalog.sort_values(
        ['pendiente', 'importe_nominal', 'descripcion_normalizada'],
        ascending=[False, False, True],
    )
    dates = pd.date_range(cfg.start, cfg.end, freq='W-MON')
    weekly = valid.groupby('semana_inicio').agg(
        registros_detectados=('registro_id', 'size'),
        importe_registrado=('importe_nominal', 'sum'),
        articulos_con_cero=('importe_nominal', lambda x: int(x.eq(0).sum())),
    ).reindex(dates, fill_value=0)
    weekly.index.name = 'semana_inicio'
    coverage = weekly.reset_index()
    coverage.insert(1, 'estado', 'desconocida')
    coverage.insert(2, 'evidencia', '')
    coverage.insert(3, 'fecha_revision', '')
    output = Path('outputs/revision_datos_20260919')
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        'source_sha256': cfg.source_sha256,
        'catalog': catalog.fillna('').to_dict(orient='records'),
        'coverage': coverage.assign(semana_inicio=lambda x: x.semana_inicio.dt.strftime('%Y-%m-%d')).to_dict(orient='records'),
        'summary': {
            'catalog_rows': len(catalog),
            'pending': int(catalog.pendiente.sum()),
            'weeks': len(coverage),
            'weeks_without_records': int(coverage.registros_detectados.eq(0).sum()),
            'weeks_with_zero_items': int(coverage.articulos_con_cero.gt(0).sum()),
        },
    }
    (output / '_datos_revision.json').write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding='utf-8')
    print(payload['summary'])


if __name__ == '__main__':
    main()
