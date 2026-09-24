"""Construcción del panel semanal y predictores sin fuga temporal.

El calendario conserva todos los lunes. Una semana incierta permanece NaN;
no se comprime el tiempo ni se crea una compra ficticia de cero pesos.
"""
import numpy as np
import pandas as pd
from .data import clean_upper


def history(panel, origin, cfg):
    """Dar al modelo solo las semanas anteriores al origen de pronóstico."""
    start = 0 if cfg.training_window_weeks is None else max(0, origin-cfg.training_window_weeks)
    return panel.iloc[start:origin]


def validate_panel(panel):
    """Exigir lunes consecutivos, importes válidos y total reconciliado."""
    expected = pd.date_range(panel.index[0], periods=len(panel), freq='W-MON')
    if not panel.index.equals(expected):
        raise ValueError('Panel debe conservar cada lunes, sin comprimir huecos.')
    if not panel.columns.is_unique or 'total' not in panel:
        raise ValueError('Panel ambiguo.')
    values=panel.to_numpy(float)
    if np.isinf(values).any() or (values < 0).any():
        raise ValueError('Panel negativo o infinito.')
    missing=panel.total.isna()
    if not panel.loc[missing].isna().all().all() or panel.loc[~missing].isna().any().any():
        raise ValueError('Una semana incierta debe permanecer completamente ausente.')
    if not np.allclose(panel.loc[~missing].drop(columns='total').sum(axis=1),panel.loc[~missing,'total']):
        raise ValueError('Panel no reconciliado.')


def _category_column(frame):
    column=next((c for c in ('CLASIFICACION','clasificacion') if c in frame),None)
    if column is None and 'clasificacion_analitica' in frame:column='clasificacion_analitica'
    if column is None and 'insumo_id' in frame:column='insumo_id'
    return column


def excluded_purchase_summary(purchases, start, end, excluded_categories):
    """Auditar importes excluidos del objetivo monetario por semana y categoría."""
    frame=purchases.loc[purchases.semana_inicio.between(start,end)].copy()
    column=_category_column(frame)
    if column is None:raise ValueError('No se encontró categoría presupuestaria para auditar exclusiones.')
    frame['categoria_presupuestaria']=frame[column].map(clean_upper)
    excluded={str(value).strip().upper() for value in excluded_categories}
    frame=frame.loc[frame.categoria_presupuestaria.isin(excluded)]
    columns=['semana_inicio','categoria_presupuestaria','registros_excluidos','importe_nominal_excluido']
    if frame.empty:return pd.DataFrame(columns=columns)
    return (frame.groupby(['semana_inicio','categoria_presupuestaria'],as_index=False)
        .agg(registros_excluidos=('importe_nominal','size'),importe_nominal_excluido=('importe_nominal','sum')))


def zero_purchase_records(purchases, start, end):
    """Conservar y auditar renglones de cero sin tratarlos como huecos semanales."""
    frame=purchases.loc[purchases.semana_inicio.between(start,end) & purchases.importe_nominal.eq(0)].copy()
    columns=[name for name in ('fecha','semana_inicio','descripcion','descripcion_normalizada',
        'CLASIFICACION','clasificacion','importe_nominal') if name in frame]
    return frame[columns].reset_index(drop=True)


def composition_history(panel, origin, cfg):
    """Historia previa al origen para participaciones, independiente del total."""
    start=0 if cfg.composition_window_weeks is None else max(0,origin-cfg.composition_window_weeks)
    return panel.iloc[start:origin]


def build_gap_panel(purchases, coverage, catalog, start, end, zero_targets_valid=True,
                    excluded_categories=('COMBUSTIBLE','MUEBLES','HERRAMIENTA','IMPUTADO','IMPUTADOS','OTROS')):
    """Cruzar compras, catálogo y cobertura aprobados en un panel semanal.

El total representa registros utilizables, no el gasto real completo.
Las semanas sin evidencia suficiente permanecen enteramente ausentes.
"""
    if purchases.get('es_sintetico',pd.Series(False,index=purchases.index)).astype(bool).any():
        raise ValueError('Panel principal no admite registros sintéticos.')
    dates=pd.date_range(start,end,freq='W-MON')
    if not len(dates) or dates[0]!=pd.Timestamp(start) or dates[-1]!=pd.Timestamp(end):
        raise ValueError('Inicio y fin deben ser lunes inclusivos.')
    # La unidad pedida por la tesis es la categoría presupuestaria. Se conserva
    # cada registro válido de Compras.xlsx, sin filtrar por un catálogo de
    # descripciones que podría dejar fuera categorías presupuestarias enteras.
    source_rows=purchases.loc[purchases.semana_inicio.between(dates[0],dates[-1])].copy()
    selected=source_rows.copy()
    class_col=_category_column(selected)
    if class_col is None:
        # Compatibilidad limitada para fixtures/archivos antiguos. La fuente
        # canónica usa CLASIFICACION y no depende de este catálogo por artículo.
        required={'descripcion_normalizada','insumo_id','aprobado','decision','evidencia'}
        if not required.issubset(catalog.columns):
            raise ValueError('Catálogo pendiente: falta evidencia para mapear a categoría presupuestaria.')
        mapping=catalog.copy();mapping['descripcion_normalizada']=mapping.descripcion_normalizada.map(clean_upper)
        if not mapping.aprobado.astype(bool).all() or not mapping.decision.astype(str).str.lower().eq('incluir').all():
            raise ValueError('Catálogo pendiente: las decisiones de inclusión deben aprobarse.')
        evidence=mapping.evidencia.fillna('').astype(str).str.lower()
        if evidence.str.contains('pendiente|revisar|sin evidencia').any() or evidence.str.strip().eq('').any():
            raise ValueError('El catálogo requiere evidencia concreta para cada mapeo.')
        mapping=mapping.set_index('descripcion_normalizada').insumo_id
        selected['categoria_presupuestaria']=selected.descripcion_normalizada.map(clean_upper).map(mapping)
        if selected.categoria_presupuestaria.isna().any():
            raise ValueError('Catálogo pendiente: hay descripciones sin categoría aprobada.')
        selected['categoria_presupuestaria']=selected.categoria_presupuestaria.map(clean_upper)
        class_col='categoria_presupuestaria'
    else:
        selected['categoria_presupuestaria'] = selected[class_col].map(clean_upper)
    if selected.categoria_presupuestaria.isna().any():
        raise ValueError('Compra incluida sin categoria_presupuestaria.')
    # Exclusiones de alcance ya acordadas para el modelo de abastecimiento:
    # no son insumos presupuestarios relevantes para esta investigación.
    excluded={str(value).strip().upper() for value in excluded_categories}
    selected=selected.loc[~selected.categoria_presupuestaria.isin(excluded)].copy()
    if selected.empty:raise ValueError('Todos los registros fueron excluidos por categoría presupuestaria.')
    if not {'semana_inicio','estado','evidencia','fecha_revision'}.issubset(coverage):raise ValueError('Contrato de cobertura incompleto.')
    cov=coverage.copy();cov['semana_inicio']=pd.to_datetime(cov.semana_inicio)
    if cov.semana_inicio.duplicated().any() or cov.semana_inicio.dt.dayofweek.ne(0).any():raise ValueError('Cobertura con fechas ambiguas.')
    cov=cov.set_index('semana_inicio').reindex(dates)
    cov['estado']=cov.estado.fillna('desconocida')
    if not cov.estado.isin(['registrada','observada','cero_confirmado','incierta','desconocida','incompleta']).all():raise ValueError('Estado de cobertura no permitido; no se admite síntesis.')
    # La presencia de transacciones prueba captura en esa semana, no que la
    # captura esté completa. Ausencia de filas siempre significa NaN, nunca 0.
    selected['insumo_id'] = selected['categoria_presupuestaria']
    panel=selected.pivot_table(index='semana_inicio',columns='insumo_id',values='importe_nominal',aggfunc='sum',fill_value=0).reindex(dates,fill_value=0).astype(float)
    source_present=source_rows.groupby('semana_inicio').size().reindex(dates,fill_value=0).gt(0)
    declared=cov.estado.copy()
    if ((declared.eq('registrada')|declared.eq('observada')) & ~source_present).any():
        raise ValueError('Semana marcada como registrada/observada sin compras fuente.')
    confirmed_zero=declared.eq('cero_confirmado') & ~source_present
    if confirmed_zero.any() and not zero_targets_valid:
        raise ValueError('Ceros semanales no válidos para el entrenamiento; revisar política de cobertura.')
    if (declared.eq('cero_confirmado') & source_present).any():
        raise ValueError('Cobertura declara cero confirmado, pero existen transacciones fuente.')
    # Una semana con filas fuente, aunque todas sean categorías excluidas,
    # tiene cero MXN registrados dentro del universo elegible. Una semana
    # sin filas fuente sigue siendo ausencia de captura (NaN).
    uncertain=declared.isin(['incierta','incompleta'])
    captured=(source_present & ~uncertain) | confirmed_zero
    eligible_captured=selected.groupby('semana_inicio').size().reindex(dates,fill_value=0).gt(0)
    panel.loc[captured & ~eligible_captured,:]=0.
    panel.loc[~captured,:]=np.nan
    panel['total']=panel.sum(axis=1,min_count=1)
    cov.loc[source_present & ~uncertain,'estado']='observada'
    cov.loc[source_present & ~uncertain & eligible_captured,'evidencia']='Transacciones elegibles presentes; exhaustividad no certificada.'
    cov.loc[source_present & ~uncertain & ~eligible_captured,'evidencia']='Hay registros fuente, pero pertenecen solo a categorías excluidas; total elegible observado = 0 MXN.'
    cov.loc[confirmed_zero,'evidencia']='Cero elegible confirmado en la cobertura aprobada.'
    cov.loc[~source_present & ~confirmed_zero & cov.estado.isna(),'estado']='desconocida'
    cov['fecha_revision']=cov.fecha_revision.fillna('')
    panel.index.name='semana_inicio';cov.index.name='semana_inicio'
    validate_panel(panel)
    return panel,cov


def gap_features(panel, origin, horizon, cfg, exog, variables=(), sales=None):
    """Construir una fila de predictores conocidos en el origen.

Incluye último total observado, edad del dato, medias y conteos recientes,
calendario objetivo y, si existen, ventas/exógenas ya publicadas.
"""
    date=panel.index[0]+pd.Timedelta(weeks=origin)
    target=date+pd.Timedelta(weeks=horizon-1)
    y=panel.total.iloc[:origin];valid=y.dropna()
    if valid.empty:raise ValueError('No hay historia observada en este origen.')
    last=valid.index[-1]
    values={'ultimo_observado':float(valid.iloc[-1]),'edad_ultimo_semanas':float((date-last).days/7),
            'n_historia_observada':float(len(valid))}
    for window in (4,8,12):
        block=y.iloc[-window:]
        values[f'media_disponible_{window}']=float(block.mean())
        values[f'n_disponibles_{window}']=float(block.notna().sum())
    week=target.isocalendar().week
    values.update(cal_sin=np.sin(2*np.pi*week/52.1775),cal_cos=np.cos(2*np.pi*week/52.1775))
    if sales is not None:
        for lag in (1,4):
            r=sales.iloc[origin-lag]
            values[f'ventas_lag_{lag}']=float(r.importe_nominal) if pd.notna(r.available_at) and r.available_at<=date else np.nan
    # available_at es la barrera que evita introducir información futura.
    for variable in variables:
        eligible=exog.loc[(exog.variable==variable)&((exog.available_at<=date)|exog.tipo.eq('calendario'))]
        future=eligible.loc[eligible.tipo.isin(['pronostico','calendario']) & eligible.fecha_referencia.eq(target)]
        past=eligible.loc[eligible.tipo.eq('observada') & (eligible.fecha_referencia<date)]
        candidates=future if not future.empty else past
        values['exog_'+variable]=float(candidates.sort_values(['fecha_referencia','available_at']).iloc[-1].valor) if not candidates.empty else np.nan
    return pd.DataFrame([values])


def training_targets(panel,origin,horizon,cfg):
    """Elegir etiquetas observadas cuyo origen de pronóstico ya ocurrió."""
    start=max(cfg.lookback+horizon-1, 0 if cfg.training_window_weeks is None else origin-cfg.training_window_weeks)
    return [t for t in range(start,origin)
            if pd.notna(panel.total.iloc[t]) and panel.total.iloc[:t-horizon+1].notna().any()]


def gap_samples(panel,origin,horizon,cfg,exog,variables=(),sales=None):
    """Preparar entrenamiento ML y la fila que se debe pronosticar."""
    targets=training_targets(panel,origin,horizon,cfg)
    if len(targets)<cfg.min_training_observations:raise ValueError('Objetivos observados insuficientes para ML.')
    x=pd.concat([gap_features(panel,t-horizon+1,horizon,cfg,exog,variables,sales) for t in targets],ignore_index=True)
    return x,panel.total.iloc[targets].to_numpy(),gap_features(panel,origin,horizon,cfg,exog,variables,sales)


def gap_partitions(panel,cfg):
    """Separar validación interna y evaluación final por fechas de calendario."""
    validate_panel(panel)
    observed=np.flatnonzero(panel.total.notna().to_numpy())
    if not len(observed):raise ValueError('No hay semanas con compras capturadas.')
    last_label=int(observed[-1])
    # El holdout se cuenta hacia atrás desde la última etiqueta real, no desde
    # la cola del panel que puede extenderse por ventas/calendario.
    cutoff=max(0,last_label-cfg.holdout_weeks+1)
    def sufficient(o):return all(len(training_targets(panel,o,h,cfg))>=cfg.min_training_observations for h in cfg.horizons)
    if cfg.training_window_weeks is not None:
        # Orígenes equidistantes; el corte se purga por el horizonte máximo.
        last_origin=last_label-max(cfg.horizons)+1
        origin_start=cfg.rolling_origin_start or cfg.training_window_weeks
        if origin_start < cfg.training_window_weeks:
            raise ValueError('rolling_origin_start no puede preceder al inicio de la primera ventana de entrenamiento.')
        origins=list(range(origin_start,last_origin+1,cfg.rolling_step_weeks))
        tuning_candidates=[o for o in origins if o+max(cfg.horizons)-1 < cutoff and sufficient(o)]
        tuning=tuning_candidates[-cfg.tuning_origins:]
        evaluation=[o for o in origins if o>=cutoff and o<=last_origin and sufficient(o)]
    else:
        # Contrato anterior para las pruebas y corridas históricas.
        tuning_candidates=[o for o in range(cfg.lookback,cutoff-max(cfg.horizons)+1) if sufficient(o)]
        tuning=tuning_candidates[-cfg.tuning_origins:]
        evaluation=list(range(cutoff,min(cutoff+cfg.holdout_weeks,last_label+1)))
    if len(tuning)<cfg.tuning_origins or not evaluation:
        raise ValueError('Historia insuficiente para construir los folds rolling configurados.')
    # Los objetivos ausentes no se imputan ni bloquean la corrida exploratoria;
    # quedan trazados en ``particiones`` para que sus exclusiones sean visibles.
    rows=[]
    for stage,origins in [('validacion_interna',tuning),('evaluacion',evaluation)]:
        for o in origins:
            for h in cfg.horizons:
                target=o+h-1;available=target<len(panel) and pd.notna(panel.total.iloc[target])
                first_training=max(0, o-cfg.training_window_weeks) if cfg.training_window_weeks is not None else 0
                train_history=panel.total.iloc[first_training:o].dropna()
                rows.append(dict(etapa=stage,origen=panel.index[o],fecha_objetivo=panel.index[0]+pd.Timedelta(weeks=target),horizonte=h,
                    entrenamiento_inicio=panel.index[first_training],ultima_etiqueta_entrenamiento=train_history.index[-1],
                    n_entrenamiento_observado=len(training_targets(panel,o,h,cfg)),objetivo_observado=bool(available),
                    motivo='' if available else 'fuera_del_periodo' if target>=len(panel) else 'semana_incierta'))
    return cutoff,tuning,evaluation,pd.DataFrame(rows)
