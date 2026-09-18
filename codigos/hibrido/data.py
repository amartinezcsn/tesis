"""Ingesta nominal; reutiliza normalización de 01_clean_eda sin su imputación."""
from pathlib import Path
import hashlib
import importlib
import re
import numpy as np
import pandas as pd

clean_upper = importlib.import_module('01_clean_eda').clean_upper


def boolean_flags(values):
    """Parse explicit boolean-like values without treating non-empty text as true."""
    normalized=values.fillna(False).astype(str).str.strip().str.lower()
    allowed={'','0','0.0','1','1.0','false','true','no','si','sí'}
    invalid=~normalized.isin(allowed)
    if invalid.any():
        raise ValueError(f'Bandera booleana inválida: {sorted(normalized[invalid].unique())}')
    return normalized.isin({'1','1.0','true','si','sí'})


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_table(path, sheet=0):
    path = Path(path)
    return pd.read_excel(path, sheet_name=sheet) if path.suffix.lower() == '.xlsx' else pd.read_csv(path)


def load_purchases(path, sheet=0, demo=False, approved_duplicate_rows=()):
    raw = read_table(path, sheet)
    # Original and historical clean-detail formats, without choosing either silently.
    frame = raw.rename(columns={'FECHA':'fecha', 'MONTO':'importe_nominal',
        'monto_nominal':'importe_nominal', 'DESCRIPCION':'descripcion'}).copy()
    if frame.columns.duplicated().any():
        raise ValueError('Columnas ambiguas tras homologación.')
    needed = {'fecha', 'importe_nominal', 'descripcion'}
    if not needed.issubset(frame):
        raise ValueError(f'Faltan columnas de compras: {sorted(needed-set(frame))}')
    if not demo:
        for col in ('procedencia', 'origen_dato'):
            if col in frame and frame[col].astype(str).str.contains('sint|synthe',case=False).any():
                raise ValueError('Procedencia sintética prohibida en modo real.')
    frame['registro_id'] = np.arange(2, len(frame)+2)  # fila original Excel/CSV
    def parse_date(value):
        if isinstance(value,str) and re.match(r'^\d{4}-\d{2}-\d{2}',value):
            return pd.to_datetime(value,errors='coerce',format='ISO8601')
        if isinstance(value,(int,float)):
            return pd.NaT  # no asumir que un número sea serial Excel o nanosegundos
        return pd.to_datetime(value,errors='coerce',dayfirst=True)
    frame['fecha'] = pd.to_datetime(frame.fecha.map(parse_date)).dt.normalize()
    frame['importe_nominal'] = pd.to_numeric(frame.importe_nominal, errors='coerce')
    frame['descripcion_normalizada'] = frame.descripcion.map(clean_upper)
    synthetic = pd.Series(False, index=frame.index)
    for col in ('es_sintetico', 'synthetic'):
        if col in frame:
            synthetic |= boolean_flags(frame[col])
    if synthetic.any() and not demo:
        raise ValueError('Datos sintéticos prohibidos en el protocolo de tesis.')
    frame['es_sintetico'] = synthetic
    frame['motivo'] = ''
    # One mutually exclusive reason per rejected row; never silently drop duplicates.
    conditions = [('fecha_invalida', frame.fecha.isna()),
        ('importe_invalido', ~np.isfinite(frame.importe_nominal)),
        ('importe_negativo_requiere_revision', frame.importe_nominal.lt(0)),
        ('descripcion_vacia', frame.descripcion_normalizada.isna())]
    for reason, mask in conditions:
        frame.loc[mask & frame.motivo.eq(''), 'motivo'] = reason
    duplicate = raw.duplicated(keep=False)
    approved_duplicate_rows = set(approved_duplicate_rows)
    duplicate_rows = set(frame.loc[duplicate, 'registro_id'])
    stale_approvals = approved_duplicate_rows - duplicate_rows
    if stale_approvals:
        raise ValueError(
            f'Filas duplicadas aprobadas ya no coinciden con la fuente: {sorted(stale_approvals)}. '
            'Repetir auditoria y aprobacion.'
        )
    unapproved_duplicate = duplicate & ~frame.registro_id.isin(approved_duplicate_rows)
    frame.loc[unapproved_duplicate & frame.motivo.eq(''), 'motivo'] = 'duplicado_requiere_revision'
    valid = frame.loc[frame.motivo.eq('')].copy()
    rejected = frame.loc[frame.motivo.ne('')].copy()
    valid['semana_inicio'] = valid.fecha.dt.to_period('W-SUN').dt.start_time
    return valid, rejected


def templates(purchases, output):
    output = Path(output)
    weeks = pd.date_range(purchases.semana_inicio.min(), purchases.semana_inicio.max(), freq='W-MON')
    counts = purchases.groupby('semana_inicio').size()
    coverage = pd.DataFrame({'semana_inicio': weeks, 'estado': 'desconocida',
        'evidencia': '', 'fecha_revision': ''})
    coverage['registros_detectados'] = coverage.semana_inicio.map(counts).fillna(0).astype(int)
    catalog = pd.DataFrame({'descripcion_normalizada': sorted(purchases.descripcion_normalizada.unique())})
    catalog['insumo_id'] = ''; catalog['aprobado'] = False
    coverage.to_csv(output/'cobertura_PARA_REVISAR.csv', index=False)
    catalog.to_csv(output/'catalogo_PARA_REVISAR.csv', index=False)
    return coverage


def load_exogenous(path):
    columns = ['variable','fecha_referencia','available_at','valor','fuente','version','tipo']
    if path is None: return pd.DataFrame(columns=columns)
    frame = read_table(path)
    if not set(columns).issubset(frame): raise ValueError('Contrato de exógenas incompleto.')
    for col in ('fecha_referencia','available_at'):
        frame[col] = pd.to_datetime(frame[col], errors='raise')
    frame['valor'] = pd.to_numeric(frame.valor,errors='raise')
    if not np.isfinite(frame.valor).all() or not frame.tipo.isin(['observada','pronostico','calendario']).all():
        raise ValueError('Exógenas inválidas.')
    if frame.duplicated(['variable','fecha_referencia','available_at']).any():
        raise ValueError('Exógenas ambiguas para una misma fecha de publicación.')
    for col in ('variable','fuente','version'):
        if frame[col].fillna('').astype(str).str.strip().eq('').any():
            raise ValueError(f'Exógenas sin {col}.')
    # Prevent labeling a future observation as already published.
    if ((frame.tipo=='observada') & (frame.fecha_referencia>frame.available_at)).any():
        raise ValueError('Una observación no puede estar disponible antes de su fecha de referencia.')
    return frame


def load_sales(path, index):
    if path is None: return None
    sales = read_table(path)
    if not {'semana_inicio','importe_nominal','available_at'}.issubset(sales):
        raise ValueError('Ventas requieren semana_inicio, importe_nominal, available_at.')
    sales['semana_inicio'] = pd.to_datetime(sales.semana_inicio)
    sales['available_at'] = pd.to_datetime(sales.available_at)
    sales['importe_nominal'] = pd.to_numeric(sales.importe_nominal,errors='raise')
    if sales.semana_inicio.duplicated().any() or not np.isfinite(sales.importe_nominal).all():
        raise ValueError('Ventas semanales duplicadas o no finitas.')
    if sales.semana_inicio.dt.dayofweek.ne(0).any() or (sales.available_at < sales.semana_inicio+pd.Timedelta(weeks=1)).any():
        raise ValueError('Ventas semanales deben publicarse después del cierre lunes-domingo.')
    synthetic = boolean_flags(sales.get('es_sintetico', pd.Series(False,index=sales.index)))
    if synthetic.any():
        raise ValueError('Ventas sintéticas prohibidas en el protocolo de tesis.')
    return sales.set_index('semana_inicio').reindex(index)
