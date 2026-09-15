"""Calendario intacto, objetivos sin imputar, alcance explícito y ventana creciente."""
import numpy as np
import pandas as pd
from .data import clean_upper


def history(panel, origin, cfg):
    return panel.iloc[:origin] if cfg.missing_policy == 'calendar_gaps' else panel.iloc[origin-cfg.window:origin]


def validate_panel(panel):
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


def build_gap_panel(purchases, coverage, catalog, start, end):
    """Only approved recorded totals are usable; no assertion of actual total spend."""
    if purchases.get('es_sintetico',pd.Series(False,index=purchases.index)).astype(bool).any():
        raise ValueError('Panel principal no admite registros sintéticos.')
    dates=pd.date_range(start,end,freq='W-MON')
    if not len(dates) or dates[0]!=pd.Timestamp(start) or dates[-1]!=pd.Timestamp(end):
        raise ValueError('Inicio y fin deben ser lunes inclusivos.')
    required={'descripcion_normalizada','insumo_id','aprobado','decision','evidencia'}
    if not required.issubset(catalog):raise ValueError('Catálogo requiere decision y evidencia además de homologación.')
    cat=catalog.copy();cat['descripcion_normalizada']=cat.descripcion_normalizada.map(clean_upper)
    if cat.descripcion_normalizada.isna().any() or cat.descripcion_normalizada.duplicated().any():
        raise ValueError('Catálogo ambiguo.')
    if not cat.aprobado.astype(str).str.lower().isin(['true','1']).all() or not cat.decision.isin(['incluir','excluir']).all():
        raise ValueError('Catálogo pendiente: aprobar alcance por descripción.')
    if cat.evidencia.fillna('').astype(str).str.strip().eq('').any():raise ValueError('Decisión sin evidencia.')
    inc=cat.decision.eq('incluir')
    if cat.loc[inc,'insumo_id'].fillna('').astype(str).str.strip().eq('').any() or cat.loc[inc,'insumo_id'].isin(['total','otros']).any():
        raise ValueError('Identificador de insumo vacío o reservado.')
    selected=purchases.loc[purchases.semana_inicio.between(dates[0],dates[-1])].merge(cat,on='descripcion_normalizada',how='left',validate='many_to_one')
    if selected.decision.isna().any():raise ValueError('Registro sin decisión de alcance.')
    class_col=next((c for c in ('CLASIFICACION','clasificacion') if c in selected),None)
    if class_col and (selected[class_col].astype(str).str.upper().isin(['COMBUSTIBLE','MUEBLES','HERRAMIENTA']) & selected.decision.eq('incluir')).any():
        raise ValueError('Combustible, muebles y herramientas están excluidos por protocolo.')
    selected=selected.loc[selected.decision.eq('incluir')]
    if selected.empty:raise ValueError('Sin adquisiciones incluidas.')
    if not {'semana_inicio','estado','evidencia','fecha_revision'}.issubset(coverage):raise ValueError('Contrato de cobertura incompleto.')
    cov=coverage.copy();cov['semana_inicio']=pd.to_datetime(cov.semana_inicio)
    if cov.semana_inicio.duplicated().any() or cov.semana_inicio.dt.dayofweek.ne(0).any():raise ValueError('Cobertura con fechas ambiguas.')
    cov=cov.set_index('semana_inicio').reindex(dates)
    cov['estado']=cov.estado.fillna('desconocida')
    if not cov.estado.isin(['registrada','observada','cero_confirmado','incierta','desconocida','incompleta']).all():raise ValueError('Estado de cobertura no permitido; no se admite síntesis.')
    usable=cov.estado.isin(['registrada','observada','cero_confirmado'])
    if cov.loc[usable,'evidencia'].fillna('').astype(str).str.strip().eq('').any() or pd.to_datetime(cov.loc[usable,'fecha_revision'],errors='coerce').isna().any():
        raise ValueError('Semanas utilizables requieren revisión documentada.')
    # Raw zero line items require their own adjudication, not a blanket weekly approval.
    zero_weeks=selected.loc[selected.importe_nominal.eq(0),'semana_inicio']
    if usable.reindex(zero_weeks,fill_value=False).any():
        raise ValueError('Importes cero por artículo pendientes: marcar semana incierta o resolver fuente documentadamente.')
    panel=selected.pivot_table(index='semana_inicio',columns='insumo_id',values='importe_nominal',aggfunc='sum',fill_value=0).reindex(dates,fill_value=0).astype(float)
    panel['total']=panel.sum(axis=1)
    counts=selected.groupby('semana_inicio').size().reindex(dates,fill_value=0)
    if (cov.estado.isin(['registrada','observada']) & counts.eq(0)).any():raise ValueError('Semana sin compras incluidas no es cero confirmado.')
    if (cov.estado.eq('cero_confirmado') & panel.total.gt(0)).any():raise ValueError('Cero confirmado contradice importes.')
    panel.loc[~usable,:]=np.nan
    panel.index.name='semana_inicio';cov.index.name='semana_inicio'
    validate_panel(panel)
    return panel,cov


def gap_features(panel, origin, horizon, cfg, exog, variables=(), sales=None):
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
    for variable in variables:
        eligible=exog.loc[(exog.variable==variable)&(exog.available_at<=date)]
        future=eligible.loc[eligible.tipo.isin(['pronostico','calendario']) & eligible.fecha_referencia.eq(target)]
        past=eligible.loc[eligible.tipo.eq('observada') & (eligible.fecha_referencia<date)]
        candidates=future if not future.empty else past
        values['exog_'+variable]=float(candidates.sort_values(['fecha_referencia','available_at']).iloc[-1].valor) if not candidates.empty else np.nan
    return pd.DataFrame([values])


def training_targets(panel,origin,horizon,cfg):
    return [t for t in range(cfg.lookback+horizon-1,origin)
            if pd.notna(panel.total.iloc[t]) and panel.total.iloc[:t-horizon+1].notna().any()]


def gap_samples(panel,origin,horizon,cfg,exog,variables=(),sales=None):
    targets=training_targets(panel,origin,horizon,cfg)
    if len(targets)<cfg.min_training_observations:raise ValueError('Objetivos observados insuficientes para ML.')
    x=pd.concat([gap_features(panel,t-horizon+1,horizon,cfg,exog,variables,sales) for t in targets],ignore_index=True)
    return x,panel.total.iloc[targets].to_numpy(),gap_features(panel,origin,horizon,cfg,exog,variables,sales)


def gap_partitions(panel,cfg):
    validate_panel(panel);cutoff=len(panel)-cfg.holdout_weeks
    def sufficient(o):return all(len(training_targets(panel,o,h,cfg))>=cfg.min_training_observations for h in cfg.horizons)
    # All inner h=1..4 labels must precede the cutoff, including unavailable labels.
    eligible=[o for o in range(cfg.lookback,cutoff-max(cfg.horizons)+1) if sufficient(o)]
    tuning=eligible[-cfg.tuning_origins:]
    evaluation=list(range(cutoff,len(panel)))
    if len(tuning)<cfg.tuning_origins or not evaluation or not sufficient(cutoff):raise ValueError('Historia observada insuficiente para separar validación y evaluación.')
    for h in cfg.horizons:
        if sum(pd.notna(panel.total.iloc[o+h-1]) for o in tuning)<2:raise ValueError(f'Menos de dos objetivos internos observados para h={h}.')
        if not any(o+h-1<len(panel) and pd.notna(panel.total.iloc[o+h-1]) for o in evaluation):raise ValueError(f'Sin objetivos finales observados para h={h}.')
    rows=[]
    for stage,origins in [('validacion_interna',tuning),('evaluacion',evaluation)]:
        for o in origins:
            for h in cfg.horizons:
                target=o+h-1;available=target<len(panel) and pd.notna(panel.total.iloc[target])
                rows.append(dict(etapa=stage,origen=panel.index[o],fecha_objetivo=panel.index[0]+pd.Timedelta(weeks=target),horizonte=h,
                    entrenamiento_inicio=panel.index[0],ultima_etiqueta_entrenamiento=panel.total.iloc[:o].dropna().index[-1],
                    n_entrenamiento_observado=len(training_targets(panel,o,h,cfg)),objetivo_observado=bool(available),
                    motivo='' if available else 'fuera_del_periodo' if target>=len(panel) else 'semana_incierta'))
    return cutoff,tuning,evaluation,pd.DataFrame(rows)
