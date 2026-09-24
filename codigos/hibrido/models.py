"""Modelos estadísticos y de aprendizaje automático del total semanal.

Cada componente devuelve su propio pronóstico. Una falla se registra: no se
sustituye por otro modelo bajo el nombre del componente fallido.
"""
import warnings
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX
from scipy.optimize import minimize, minimize_scalar
from .gaps import history, training_targets, gap_features
from threadpoolctl import threadpool_limits
from .features import samples


@dataclass
class SeasonalNaiveFit:
    """Pronóstico anual semanal; un hueco no se convierte en cero."""
    history: np.ndarray

    def forecast(self, steps=1):
        if len(self.history)<52:
            raise ValueError('Naive estacional requiere 52 semanas de calendario.')
        values=np.asarray(self.history[-52:-52+steps],dtype=float)
        if len(values)<steps or not np.isfinite(values).all():
            raise ValueError('Naive estacional sin etiqueta observada para el rezago anual.')
        return values


@dataclass
class SimpleExpSmoothingFit:
    """Suavizamiento exponencial de nivel con estado congelado en semanas ausentes."""
    level: float
    alpha: float

    def forecast(self, steps=1):
        return np.repeat(self.level,steps)


@dataclass
class DampedHoltFit:
    """Holt amortiguado filtrado semana a semana sin imputar observaciones."""
    level: float
    trend: float
    phi: float

    def forecast(self, steps=1):
        return np.asarray([self.level+self.trend*sum(self.phi**i for i in range(1,h+1))
                           for h in range(1,steps+1)])


def _fit_ses(y):
    values=np.asarray(y,dtype=float);observed=np.flatnonzero(np.isfinite(values))
    if len(observed)<2:raise ValueError('SES requiere al menos dos semanas observadas.')
    initial=float(values[observed[0]])
    def loss(alpha):
        state=initial;errors=[]
        for value in values[observed[1:]]:
            errors.append((float(value)-state)**2)
            state=alpha*float(value)+(1-alpha)*state
        return float(np.mean(errors))
    fit=minimize_scalar(loss,bounds=(.001,.999),method='bounded')
    alpha=float(fit.x);state=initial
    for value in values[observed[1:]]:state=alpha*float(value)+(1-alpha)*state
    return SimpleExpSmoothingFit(state,alpha)


def _fit_damped_holt(y):
    values=np.asarray(y,dtype=float);observed=np.flatnonzero(np.isfinite(values))
    if len(observed)<3:raise ValueError('Holt amortiguado requiere al menos tres semanas observadas.')
    level=float(values[observed[0]])
    trend=float((values[observed[1]]-values[observed[0]])/(observed[1]-observed[0]))
    series=values[observed[0]:]
    def filter_state(params,return_state=False):
        alpha,beta,phi=map(float,params);state=level;slope=trend;errors=[]
        for value in series[1:]:
            previous=state;forecast=state+phi*slope
            if np.isfinite(value):
                errors.append((float(value)-forecast)**2)
                state=alpha*float(value)+(1-alpha)*forecast
                slope=beta*(state-previous)+(1-beta)*phi*slope
            else:
                state=forecast;slope=phi*slope
        return (state,slope,phi) if return_state else float(np.mean(errors)) if errors else np.inf
    fit=minimize(filter_state,[.3,.1,.8],method='L-BFGS-B',bounds=((.001,.999),(.001,.999),(.5,.99)))
    if not np.isfinite(fit.fun):raise ValueError('No fue posible ajustar Holt amortiguado.')
    return DampedHoltFit(*filter_state(fit.x,return_state=True))


def stat_fit(y, name):
    """Ajustar familias estadísticas sin convertir semanas ausentes en ceros."""
    if name=='seasonal_52s':return SeasonalNaiveFit(np.asarray(y,dtype=float))
    if name=='ses':return _fit_ses(y)
    if name=='holt_damped':return _fit_damped_holt(y)
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
    """Ajustar boosting, bosque, Ridge o red neuronal con escalamiento local."""
    if name not in ('hgb', 'rf','ridge','mlp'):
        raise ValueError(f'Componente ML no soportado: {name}')
    if not np.isfinite(y).all():raise ValueError('Objetivos de ML deben ser observados y finitos.')
    # No se inventan etiquetas; el boosting admite predictores ausentes.
    if name=='hgb':model=HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=7,min_samples_leaf=5,early_stopping=False,random_state=cfg.seed)
    elif name=='ridge':model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=10.0))
    elif name=='mlp':
        regressor=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
            MLPRegressor(hidden_layer_sizes=(4,),activation='tanh',solver='lbfgs',
                alpha=5.0,max_iter=2000,random_state=cfg.seed))
        model=TransformedTargetRegressor(regressor=regressor,transformer=StandardScaler())
    else:model=RandomForestRegressor(n_estimators=100,max_depth=4,min_samples_leaf=3,random_state=cfg.seed,n_jobs=1)
    with threadpool_limits(limits=1):model.fit(x,y)
    return model


def candidates(cfg):
    """Enumerar candidatos actuales y ampliados antes de la validación interna."""
    stats=['ss_ar1']+(['ss_arima111'] if cfg.use_arima else [])
    mls=['hgb']+(['rf'] if cfg.use_rf else [])
    if cfg.use_extended_statistical:stats+=['ses','holt_damped','seasonal_52s']
    if cfg.use_ridge:mls+=['ridge']
    if cfg.use_neural_network:mls+=['mlp']
    if cfg.use_residual_hybrid and cfg.use_arima:
        if cfg.use_rf:mls+=['rf_residual']
        if cfg.use_neural_network:mls+=['nn_residual']
    return stats,mls


def components(panel,origin,h,cfg,exog,variables,sales=None,selection=None):
    """Ajustar y pronosticar componentes con historia anterior al origen.

Sin ``selection`` se prueban candidatos. Con ella se usa exclusivamente la
pareja ya elegida durante desarrollo y se informan sus fallos.
"""
    stat_names,ml_names=candidates(cfg)
    if selection:
        stat_names=[selection['stat']]
        residual_names=('rf_residual','nn_residual')
        ml_names=[name for name in residual_names if selection['ml'].startswith(name+'__')] or [selection['ml']]
    predictions={}; fitted={}; errors=[]
    y=history(panel,origin,cfg).total.to_numpy()
    for name in stat_names:
        try:
            fitted[name]=stat_fit(y,name); predictions[name]=predict_stat(fitted[name],h)
        except Exception as exc:
            errors.append(dict(origen=str(panel.index[0]+pd.Timedelta(weeks=origin)),horizonte=h,modelo=name,error=str(exc)))
    x,y_train,test=samples(panel,origin,h,cfg,exog,variables,sales)
    for name in ml_names:
        if name in ('rf_residual','nn_residual'):
            for stat_name in stat_names:
                if stat_name!='ss_arima111' or stat_name not in predictions:continue
                key=f'{name}__{stat_name}'
                try:
                    targets=training_targets(panel,origin,h,cfg);residuals=[];residual_features=[]
                    for target,value in zip(targets,y_train):
                        inner_origin=target-h+1
                        base=stat_fit(history(panel,inner_origin,cfg).total.to_numpy(),stat_name)
                        residual_features.append(gap_features(panel,inner_origin,h,cfg,exog,variables,sales))
                        residuals.append(float(value)-predict_stat(base,h))
                    if len(residuals)<cfg.min_training_observations:
                        raise ValueError('Residuos ARIMA fuera de muestra insuficientes para el corrector ML.')
                    residual_model='mlp' if name=='nn_residual' else 'rf'
                    fitted[key]=ml_fit(pd.concat(residual_features,ignore_index=True),np.asarray(residuals),residual_model,cfg)
                    correction=float(fitted[key].predict(test)[0])
                    predictions[key]=max(0.,predictions[stat_name]+correction)
                except Exception as exc:
                    errors.append(dict(origen=str(panel.index[0]+pd.Timedelta(weeks=origin)),horizonte=h,modelo=key,error=str(exc)))
            continue
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
