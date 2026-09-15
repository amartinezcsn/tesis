"""Ingesta nominal; reutiliza normalización de 01_clean_eda sin su imputación."""
from pathlib import Path
import hashlib
import importlib
import re
import numpy as np
import pandas as pd

clean_upper = importlib.import_module('01_clean_eda').clean_upper


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_table(path, sheet=0):
    path = Path(path)
    return pd.read_excel(path, sheet_name=sheet) if path.suffix.lower() == '.xlsx' else pd.read_csv(path)


def load_purchases(path, sheet=0, demo=False, approved_duplicate_rows=(),
                   synthetic_training_approved=False, synthetic_before=None):
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
            synthetic |= ~frame[col].fillna(0).astype(str).str.lower().isin(['0','0.0','false','no',''])
    if synthetic.any() and not demo:
        if not synthetic_training_approved or synthetic_before is None:
            raise ValueError('Datos sintéticos prohibidos sin aprobación y corte de entrenamiento.')
        cutoff = pd.Timestamp(synthetic_before).normalize()
        if frame.loc[synthetic, 'fecha'].isna().any() or frame.loc[synthetic, 'fecha'].ge(cutoff).any():
            raise ValueError('Datos sintéticos dentro del holdout/evaluación.')
        if 'metodo_sintesis' not in frame or frame.loc[synthetic, 'metodo_sintesis'].fillna('').astype(str).str.strip().eq('').any():
            raise ValueError('Cada registro sintético requiere metodo_sintesis.')
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


def build_panel(purchases, coverage, catalog, start, end, synthetic_before=None):
    for col in ('semana_inicio', 'estado', 'evidencia', 'fecha_revision'):
        if col not in coverage:
            raise ValueError(f'Cobertura sin columna {col}')
    coverage = coverage.copy()
    coverage['semana_inicio'] = pd.to_datetime(coverage.semana_inicio, errors='raise').dt.normalize()
    if coverage.semana_inicio.duplicated().any() or coverage.semana_inicio.dt.dayofweek.ne(0).any():
        raise ValueError('Cobertura duplicada o semana que no inicia en lunes.')
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if start.dayofweek != 0 or end.dayofweek != 0 or end < start:
        raise ValueError('Inicio y fin deben ser lunes ordenados e inclusivos.')
    dates = pd.date_range(start, end, freq='W-MON')
    cov = coverage.set_index('semana_inicio').reindex(dates)
    if not cov.estado.isin(['observada','cero_confirmado','sintetica_entrenamiento']).all():
        raise ValueError('Cobertura pendiente/incompleta: no se entrenará ni se comprimirán semanas.')
    if cov.evidencia.fillna('').astype(str).str.strip().eq('').any() or pd.to_datetime(cov.fecha_revision, errors='coerce').isna().any():
        raise ValueError('Cada semana necesita evidencia y fecha de revisión.')
    cat = catalog.copy()
    for col in ('descripcion_normalizada','insumo_id','aprobado'):
        if col not in cat: raise ValueError(f'Catálogo sin columna {col}')
    cat['descripcion_normalizada'] = cat.descripcion_normalizada.map(clean_upper)
    if cat.descripcion_normalizada.duplicated().any():
        raise ValueError('Catálogo ambiguo: descripción duplicada.')
    if not cat.aprobado.astype(str).str.lower().isin(['true','1']).all():
        raise ValueError('Catálogo requiere aprobación explícita.')
    if cat.insumo_id.fillna('').astype(str).str.strip().eq('').any() or cat.insumo_id.isin(['otros','total']).any():
        raise ValueError('IDs vacíos o reservados (otros/total) en catálogo.')
    selected = purchases.loc[purchases.semana_inicio.between(start,end)].copy()
    selected = selected.merge(cat[['descripcion_normalizada','insumo_id']],on='descripcion_normalizada',how='left',validate='many_to_one')
    if selected.insumo_id.isna().any():
        raise ValueError('Compras sin homologación de insumo.')
    panel = selected.pivot_table(index='semana_inicio',columns='insumo_id',values='importe_nominal',aggfunc='sum',fill_value=0)
    panel = panel.reindex(dates, fill_value=0).astype(float).sort_index(axis=1)
    panel.index.name = 'semana_inicio'
    panel['total'] = panel.sum(axis=1)
    count = selected.groupby('semana_inicio').size().reindex(dates,fill_value=0)
    synthetic = selected.get('es_sintetico', pd.Series(False,index=selected.index)).astype(bool)
    synthetic_count = selected.loc[synthetic].groupby('semana_inicio').size().reindex(dates,fill_value=0)
    synthetic_state = cov.estado.eq('sintetica_entrenamiento')
    if synthetic_state.any():
        if synthetic_before is None or synthetic_state.loc[pd.Timestamp(synthetic_before):].any():
            raise ValueError('Cobertura sintética dentro del holdout/evaluación.')
        if ((synthetic_state & count.eq(0)) | (synthetic_state & synthetic_count.ne(count))).any():
            raise ValueError('Semana sintética sin filas exclusivamente sintéticas.')
    if (cov.estado.eq('observada') & synthetic_count.gt(0)).any():
        raise ValueError('Una semana con filas sintéticas no puede marcarse observada.')
    if ((cov.estado.eq('cero_confirmado')) & panel.total.gt(0)).any():
        raise ValueError('Cero confirmado contradice compras positivas.')
    if (cov.estado.eq('observada') & count.eq(0)).any():
        raise ValueError('Semana sin registros necesita estado cero_confirmado, no observada.')
    if not np.isclose(panel.total.sum(), selected.importe_nominal.sum()):
        raise ValueError('Fallo de reconciliación de compras.')
    return panel, cov


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


def load_sales(path, index, synthetic_training_approved=False, synthetic_before=None):
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
    synthetic = sales.get('es_sintetico', pd.Series(False,index=sales.index)).fillna(False).astype(bool)
    if synthetic.any():
        if not synthetic_training_approved or synthetic_before is None:
            raise ValueError('Ventas sintéticas prohibidas sin aprobación y corte de entrenamiento.')
        if sales.loc[synthetic,'semana_inicio'].ge(pd.Timestamp(synthetic_before)).any():
            raise ValueError('Ventas sintéticas dentro del holdout/evaluación.')
    return sales.set_index('semana_inicio').reindex(index)
