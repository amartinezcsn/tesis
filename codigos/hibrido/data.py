"""Lectura y auditoría de fuentes, sin inventar observaciones.

Las compras son importes nominales registrados. Catálogo y cobertura se
aprueban por separado; una transacción no demuestra que una semana esté
completa.
"""
from pathlib import Path
import hashlib
import importlib
import re
import numpy as np
import pandas as pd

clean_upper = importlib.import_module('01_normalizacion').clean_upper


def boolean_flags(values):
    """Interpretar banderas explícitas sin confundir cualquier texto con True."""
    normalized=values.fillna(False).astype(str).str.strip().str.lower()
    allowed={'','0','0.0','1','1.0','false','true','no','si','sí'}
    invalid=~normalized.isin(allowed)
    if invalid.any():
        raise ValueError(f'Bandera booleana inválida: {sorted(normalized[invalid].unique())}')
    return normalized.isin({'1','1.0','true','si','sí'})


def fingerprint(path):
    """Calcular SHA-256 para detectar cambios en un archivo aprobado."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_table(path, sheet=0):
    """Leer CSV o una hoja XLSX con la misma interfaz."""
    path = Path(path)
    return pd.read_excel(path, sheet_name=sheet) if path.suffix.lower() == '.xlsx' else pd.read_csv(path)


def load_purchases(path, sheet=0, demo=False, approved_duplicate_rows=()):
    """Auditar filas y separar compras utilizables de registros pendientes.

Conserva el número de fila original y no elimina duplicados autorizados.
Devuelve dos tablas: ``valid`` y ``rejected`` con un motivo por rechazo.
"""
    raw = read_table(path, sheet)
    # Homologar nombres de columnas conocidos, sin decidir cuál fuente es oficial.
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
    # Una causa principal por fila; los duplicados nunca se descartan en silencio.
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
    """Crear plantillas de revisión, no aprobaciones automáticas."""
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
    """Validar variables externas y su fecha real de disponibilidad.

    ``Dataset_Tizayuca_2022_2026.xlsx`` se acepta como fuente diaria y se
    transforma aquí a variables calendáricas semanales conocidas en el origen
    del pronóstico. Temperatura, clima e índices no se convierten
    automáticamente: sin una fecha de publicación no es posible demostrar que
    eran conocidos antes del pronóstico.
    """
    columns = ['variable','fecha_referencia','available_at','valor','fuente','version','tipo']
    if path is None: return pd.DataFrame(columns=columns)
    frame = read_table(path)
    if {'Fecha','EsFestivoMexicano','EsFechaPago'}.issubset(frame):
        fecha = pd.to_datetime(frame['Fecha'], errors='raise', format='%Y-%m-%d')
        daily = pd.DataFrame({'fecha': fecha, 'festivo': pd.to_numeric(frame['EsFestivoMexicano'], errors='raise'),
            'pago': pd.to_numeric(frame['EsFechaPago'], errors='raise')})
        daily['semana_inicio'] = daily['fecha'] - pd.to_timedelta(daily['fecha'].dt.dayofweek, unit='D')
        weekly = daily.groupby('semana_inicio', as_index=False)[['festivo','pago']].max()
        rows = []
        for _, row in weekly.iterrows():
            for variable, value in [('es_festivo_semana', row['festivo']), ('es_fecha_pago_semana', row['pago'])]:
                rows.append(dict(variable=variable, fecha_referencia=row['semana_inicio'],
                    available_at=row['semana_inicio'], valor=float(value), fuente=Path(path).name,
                    version='1', tipo='calendario'))
        return pd.DataFrame(rows, columns=columns)
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
    # Una observación futura no puede presentarse como conocida en el origen.
    if ((frame.tipo=='observada') & (frame.fecha_referencia>frame.available_at)).any():
        raise ValueError('Una observación no puede estar disponible antes de su fecha de referencia.')
    return frame


def load_sales(path, index):
    """Validar ventas semanales opcionales, publicadas después de su cierre."""
    if path is None: return None
    sales = read_table(path)
    if {'Fecha','Importe'}.issubset(sales):
        # Exportación transaccional: las filas antiguas pueden ser conceptos
        # separados del mismo pedido, por lo que no se deduplican por número.
        fecha = pd.to_datetime(sales['Fecha'], errors='coerce', format='%d/%m/%Y')
        importe = pd.to_numeric(sales['Importe'], errors='coerce')
        valid = fecha.notna() & importe.notna()
        if not valid.any():
            raise ValueError('Ventas transaccionales sin fecha e importe utilizables.')
        clean = pd.DataFrame({'fecha': fecha[valid], 'importe_nominal': importe[valid]})
        if (clean['importe_nominal'] < 0).any():
            raise ValueError('Ventas negativas requieren una regla documentada de devoluciones.')
        clean['semana_inicio'] = clean['fecha'] - pd.to_timedelta(clean['fecha'].dt.dayofweek, unit='D')
        weekly = clean.groupby('semana_inicio', as_index=False)['importe_nominal'].sum()
        # No hay evidencia de que la bitácora sea exhaustiva: una semana sin
        # transacciones es falta de captura, no ventas cero.
        full_weeks = pd.date_range(weekly['semana_inicio'].min(), weekly['semana_inicio'].max(), freq='W-MON')
        weekly = weekly.set_index('semana_inicio').reindex(full_weeks).rename_axis('semana_inicio').reset_index()
        weekly['available_at'] = weekly['semana_inicio'] + pd.Timedelta(weeks=1)
        weekly['es_sintetico'] = False
        sales = weekly
    if not {'semana_inicio','importe_nominal','available_at'}.issubset(sales):
        raise ValueError('Ventas requieren semana_inicio, importe_nominal, available_at.')
    sales['semana_inicio'] = pd.to_datetime(sales.semana_inicio)
    sales['available_at'] = pd.to_datetime(sales.available_at)
    sales['importe_nominal'] = pd.to_numeric(sales.importe_nominal,errors='raise')
    if sales.semana_inicio.duplicated().any() or not np.isfinite(sales.importe_nominal.dropna()).all():
        raise ValueError('Ventas semanales duplicadas o no finitas.')
    if sales.semana_inicio.dt.dayofweek.ne(0).any() or (sales.available_at.dropna() < sales.semana_inicio[sales.available_at.notna()]+pd.Timedelta(weeks=1)).any():
        raise ValueError('Ventas semanales deben publicarse después del cierre lunes-domingo.')
    synthetic = boolean_flags(sales.get('es_sintetico', pd.Series(False,index=sales.index)))
    if synthetic.any():
        raise ValueError('Ventas sintéticas prohibidas en el protocolo de tesis.')
    return sales.set_index('semana_inicio').reindex(index)


def complete_purchase_panel_simple_mean(panel, start, end):
    """Completar solo semanas ausentes del alcance indicado con medias por categoría.

    Devuelve una copia (nunca altera el panel observado) y una tabla larga de
    valores generados para que cada imputación conserve trazabilidad.
    """
    result=panel.copy();scope=result.index.to_series().between(pd.Timestamp(start),pd.Timestamp(end)).to_numpy()
    observed=scope & result.total.notna().to_numpy();missing=scope & result.total.isna().to_numpy()
    if not observed.any():raise ValueError('Sin semanas observadas para calcular promedio de compras.')
    categories=[column for column in result.columns if column!='total']
    rows=[]
    for category in categories:
        average=float(result.loc[observed,category].mean())
        result.loc[missing,category]=average
        for date in result.index[missing]:
            rows.append(dict(fuente='compras',semana_inicio=date,serie=category,importe_observado=np.nan,
                importe_estimado=average,estado='estimado_promedio_simple',metodo='media_aritmetica_categoria'))
    # La suma de las medias por categoría equivale al promedio de los totales
    # de las semanas observadas y mantiene la reconciliación presupuestaria.
    result.loc[missing,'total']=result.loc[missing,categories].sum(axis=1)
    for date in result.index[missing]:
        rows.append(dict(fuente='compras',semana_inicio=date,serie='TOTAL',importe_observado=np.nan,
            importe_estimado=float(result.loc[date,'total']),estado='estimado_promedio_simple',
            metodo='suma_de_medias_aritmeticas_por_categoria'))
    result['estado_dato']=np.where(result.total.notna(),'observado','ausente_fuera_de_alcance')
    result.loc[missing,'estado_dato']='estimado_promedio_simple'
    return result,pd.DataFrame(rows)


def complete_sales_simple_mean(sales, start, end):
    """Completar las semanas de ventas faltantes dentro del periodo autorizado."""
    result=sales.copy();scope=result.index.to_series().between(pd.Timestamp(start),pd.Timestamp(end))
    observed=scope & result.importe_nominal.notna();missing=scope & result.importe_nominal.isna()
    if not observed.any():raise ValueError('Sin semanas observadas para calcular promedio de ventas.')
    average=float(result.loc[observed,'importe_nominal'].mean())
    result.loc[missing,'importe_nominal']=average
    result.loc[missing,'available_at']=pd.Timestamp.now().normalize()
    result['estado_dato']=np.where(result.importe_nominal.notna(),'observado','ausente_fuera_de_alcance')
    result.loc[missing,'estado_dato']='estimado_promedio_simple'
    audit=pd.DataFrame([dict(fuente='ventas',semana_inicio=date,serie='TOTAL',importe_observado=np.nan,
        importe_estimado=average,estado='estimado_promedio_simple',metodo='media_aritmetica_semanal')
        for date in result.index[missing]])
    return result,audit
