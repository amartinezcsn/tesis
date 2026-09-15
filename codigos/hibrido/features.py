"""Rezagos y medias desplazadas del pipeline semanal, ahora por origen explícito."""
import numpy as np
import pandas as pd


def row_features(panel, origin, horizon, cfg, exog, variables=(), sales=None):
    if origin < cfg.lookback or origin > len(panel):
        raise ValueError('Historia insuficiente para características.')
    date = panel.index[0] + pd.Timedelta(weeks=origin)
    target = date + pd.Timedelta(weeks=horizon-1)
    y = panel.total.iloc[:origin]
    values = {f'lag_{lag}':float(y.iloc[-lag]) for lag in cfg.lags}
    for window in cfg.rolling:
        values[f'media_{window}'] = float(y.iloc[-window:].mean())
        values[f'desv_{window}'] = float(y.iloc[-window:].std())
    week = target.isocalendar().week
    values.update(cal_sin=np.sin(2*np.pi*week/52.1775),cal_cos=np.cos(2*np.pi*week/52.1775))
    if sales is not None:
        for lag in (1,4):
            record = sales.iloc[origin-lag]
            values[f'ventas_lag_{lag}'] = float(record.importe_nominal) if pd.notna(record.available_at) and record.available_at <= date else np.nan
    for variable in variables:
        eligible = exog.loc[(exog.variable==variable)&(exog.available_at<=date)].copy()
        observed = eligible.loc[(eligible.tipo=='observada')&(eligible.fecha_referencia<date)]
        future = eligible.loc[(eligible.tipo.isin(['pronostico','calendario']))&(eligible.fecha_referencia==target)]
        candidates = future if not future.empty else observed
        values['exog_'+variable] = np.nan if candidates.empty else float(candidates.sort_values(['fecha_referencia','available_at']).iloc[-1].valor)
    return pd.DataFrame([values])


def samples(panel, origin, horizon, cfg, exog, variables=(), sales=None):
    # Labels end at origin-1. Context dates may precede the training target window.
    targets = range(origin-cfg.window, origin)
    contexts = [t-horizon+1 for t in targets]
    if min(contexts) < cfg.lookback:
        raise ValueError('No hay 52 (o ventana configurada) pares temporales completos.')
    x = pd.concat([row_features(panel,c,horizon,cfg,exog,variables,sales) for c in contexts],ignore_index=True)
    y = panel.total.iloc[list(targets)].to_numpy()
    test = row_features(panel,origin,horizon,cfg,exog,variables,sales)
    return x, y, test


def partitions(panel, cfg):
    cutoff = len(panel)-cfg.holdout_weeks
    first = cfg.lookback+cfg.window+max(cfg.horizons)-1
    # Every tuning label must be observed strictly before the first test origin.
    eligible = list(range(first,cutoff-max(cfg.horizons)+1))
    tuning = eligible[-cfg.tuning_origins:]
    evaluation = list(range(cutoff,len(panel)-max(cfg.horizons)+1))
    if len(tuning)<cfg.tuning_origins or not evaluation:
        raise ValueError(f'Historia insuficiente: {len(panel)} semanas; requiere al menos {first+cfg.tuning_origins+max(cfg.horizons)-1+cfg.holdout_weeks}.')
    rows=[]
    for stage,origins in [('validacion_interna',tuning),('evaluacion',evaluation)]:
        for origin in origins:
            for h in cfg.horizons:
                rows.append(dict(etapa=stage,origen=panel.index[origin],fecha_objetivo=panel.index[origin+h-1],horizonte=h,
                    entrenamiento_inicio=panel.index[origin-cfg.window],ultima_etiqueta_entrenamiento=panel.index[origin-1]))
    return cutoff,tuning,evaluation,pd.DataFrame(rows)
