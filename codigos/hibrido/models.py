"""Modelos estadísticos y de aprendizaje automático del total semanal.

Cada componente devuelve su propio pronóstico. Una falla se registra: no se
sustituye por otro modelo bajo el nombre del componente fallido.
"""
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX
from .gaps import history
from threadpoolctl import threadpool_limits
from .features import samples


def stat_fit(y, name):
    """Ajustar SARIMAX AR(1) o ARIMA(1,1,1) a la historia disponible."""
    if name not in ('ss_ar1', 'ss_arima111'):
        raise ValueError(f'Componente estadístico no soportado: {name}')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        order=(1,0,0) if name=='ss_ar1' else (1,1,1)
        fit=SARIMAX(np.asarray(y),order=order,trend='c' if name=='ss_ar1' else 'n').fit(disp=False,maxiter=200)
    if any('converg' in str(w.message).lower() for w in caught):
        raise ValueError(f'{name}: convergencia no alcanzada.')
    return fit


def predict_stat(fit, h):
    """Obtener un total no negativo a ``h`` semanas del origen."""
    result = float(np.asarray(fit.forecast(h))[-1])
    if not np.isfinite(result): raise ValueError('Pronóstico estadístico no finito.')
    return max(result,0.)


def ml_fit(x,y,name,cfg):
    """Ajustar boosting o bosque aleatorio con semilla fija y un hilo."""
    if name not in ('hgb', 'rf'):
        raise ValueError(f'Componente ML no soportado: {name}')
    if not np.isfinite(y).all():raise ValueError('Objetivos de ML deben ser observados y finitos.')
    # No se inventan etiquetas; el boosting admite predictores ausentes.
    model=(HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=7,min_samples_leaf=5,early_stopping=False,random_state=cfg.seed)
           if name=='hgb' else RandomForestRegressor(n_estimators=100,max_depth=4,min_samples_leaf=3,random_state=cfg.seed,n_jobs=1))
    with threadpool_limits(limits=1):model.fit(x,y)
    return model


def candidates(cfg):
    """Enumerar las familias habilitadas antes de la validación interna."""
    return ['ss_ar1']+(['ss_arima111'] if cfg.use_arima else []),['hgb']+(['rf'] if cfg.use_rf else [])


def components(panel,origin,h,cfg,exog,variables,sales=None,selection=None):
    """Ajustar y pronosticar componentes con historia anterior al origen.

Sin ``selection`` se prueban candidatos. Con ella se usa exclusivamente la
pareja ya elegida durante desarrollo y se informan sus fallos.
"""
    stat_names,ml_names=candidates(cfg)
    if selection: stat_names,ml_names=[selection['stat']],[selection['ml']]
    predictions={}; fitted={}; errors=[]
    y=history(panel,origin,cfg).total.to_numpy()
    for name in stat_names:
        try:
            fitted[name]=stat_fit(y,name); predictions[name]=predict_stat(fitted[name],h)
        except Exception as exc:
            errors.append(dict(origen=str(panel.index[0]+pd.Timedelta(weeks=origin)),horizonte=h,modelo=name,error=str(exc)))
    x,y_train,test=samples(panel,origin,h,cfg,exog,variables,sales)
    for name in ml_names:
        try:
            fitted[name]=ml_fit(x,y_train,name,cfg)
            pred=float(fitted[name].predict(test)[0])
            if not np.isfinite(pred):raise ValueError('Pronóstico ML no finito.')
            predictions[name]=max(0.,pred)
        except Exception as exc:
            errors.append(dict(origen=str(panel.index[0]+pd.Timedelta(weeks=origin)),horizonte=h,modelo=name,error=str(exc)))
    return predictions,fitted,errors,test


def baselines(y,h,gaps=False):
    """Calcular referencias simples para interpretar la mejora del híbrido."""
    # Último observado, media reciente y valor estacional si hay 52 semanas.
    return {'ultimo_valor':float(y.dropna().iloc[-1]) if gaps and y.notna().any() else float(y.iloc[-1]),'promedio_4s':float(y.iloc[-4:].mean()),
        'estacional_52s':float(y.iloc[-52+h-1]) if len(y)>=52 else np.nan}
