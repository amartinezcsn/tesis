"""Componentes adaptados de 06_modelos_rolling_window, sin fallback encubierto."""
import warnings
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX
from .gaps import history
from threadpoolctl import threadpool_limits
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from .features import samples


def stat_fit(y, name):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        if name.startswith('ss_'):
            order=(1,0,0) if name=='ss_ar1' else (1,1,1)
            fit=SARIMAX(np.asarray(y),order=order,trend='c' if name=='ss_ar1' else 'n').fit(disp=False,maxiter=200)
        else:
            fit = ExponentialSmoothing(np.asarray(y),trend='add',seasonal=None).fit() if name=='ets' else ARIMA(np.asarray(y),order=(1,1,1)).fit()
    if any('converg' in str(w.message).lower() for w in caught):
        raise ValueError(f'{name}: convergencia no alcanzada.')
    return fit


def predict_stat(fit, h):
    result = float(np.asarray(fit.forecast(h))[-1])
    if not np.isfinite(result): raise ValueError('Pronóstico estadístico no finito.')
    return max(result,0.)


def ml_fit(x,y,name,cfg):
    if not np.isfinite(y).all():raise ValueError('Objetivos de ML deben ser observados y finitos.')
    if cfg.missing_policy=='calendar_gaps':
        # Native missing-feature support: no synthetic target or median replacement.
        model=(HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=7,min_samples_leaf=5,early_stopping=False,random_state=cfg.seed)
               if name=='hgb' else RandomForestRegressor(n_estimators=100,max_depth=4,min_samples_leaf=3,random_state=cfg.seed,n_jobs=1))
        with threadpool_limits(limits=1):model.fit(x,y)
        return model
    regressor = RandomForestRegressor(n_estimators=100,max_depth=4,min_samples_leaf=3,random_state=cfg.seed,n_jobs=1) if name=='rf' else Ridge(alpha=float(name.split('_')[1]))
    model = Pipeline([('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),
        ('scale',StandardScaler()),('model',regressor)])
    model.fit(x,y)
    return model


def candidates(cfg):
    if cfg.missing_policy=='calendar_gaps':
        return ['ss_ar1']+(['ss_arima111'] if cfg.use_arima else []),['hgb']+(['rf'] if cfg.use_rf else [])
    return ['ets']+(['arima'] if cfg.use_arima else []), ['ridge_0.1','ridge_1','ridge_10']+(['rf'] if cfg.use_rf else [])


def components(panel,origin,h,cfg,exog,variables,sales=None,selection=None):
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
    # Reused last-value, trailing mean and seasonal logic, explicit unavailable status.
    return {'ultimo_valor':float(y.dropna().iloc[-1]) if gaps and y.notna().any() else float(y.iloc[-1]),'promedio_4s':float(y.iloc[-4:].mean()),
        'estacional_52s':float(y.iloc[-52+h-1]) if len(y)>=52 else np.nan}
