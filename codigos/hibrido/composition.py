"""Segundo componente del sistema: participaciones y reparto del presupuesto."""
import numpy as np
import pandas as pd

EXCLUDED_BUDGET_CATEGORIES = {'IMPUTADO', 'OTROS'}


def select_categories(history, threshold):
    """Fijar insumos principales según su importe acumulado en desarrollo."""
    sums=history.drop(columns='total').sum().sort_values(ascending=False,kind='stable')
    normalized=sums.index.astype(str).str.strip().str.upper()
    sums=sums[~normalized.isin(EXCLUDED_BUDGET_CATEGORIES)]
    sums=sums[sums>0]
    if sums.empty: raise ValueError('Sin historia positiva para composición.')
    count=min(len(sums),int(np.searchsorted(sums.cumsum()/sums.sum(),threshold))+1)
    return sums.index[:count].tolist()


def amounts(panel,categories):
    """Repartir el total únicamente entre las categorías presupuestarias elegidas."""
    result=panel.reindex(columns=categories,fill_value=0.).copy()
    selected_total=result.sum(axis=1)
    return result.div(selected_total.where(selected_total>0),axis=0).mul(panel.total,axis=0)


def shares(panel,categories):
    """Convertir importes observados en proporciones del total semanal."""
    return amounts(panel,categories).div(panel.total.where(panel.total>0),axis=0)


def predict_shares(history,categories,alpha=None,calendar=False):
    """Estimar mezcla histórica o mezcla reciente ponderada por edad real."""
    valid=shares(history,categories).dropna()
    if valid.empty:raise ValueError('Sin semanas de composición definida.')
    if calendar and alpha is not None:
        # La antigüedad se mide en semanas reales, sin acercar huecos ausentes.
        ages=(history.index[-1]-valid.index).days.to_numpy()/7
        weights=(1-alpha)**ages
        if not weights.sum():raise ValueError('Pesos de composición sin soporte.')
        prediction=valid.mul(weights,axis=0).sum()/weights.sum()
    else:
        prediction=valid.mean() if alpha is None else valid.ewm(alpha=alpha,adjust=False).mean().iloc[-1]
    result=np.maximum(prediction.to_numpy(float),0.)
    return pd.Series(result/result.sum(),index=valid.columns)


def allocate(total,participation):
    """Asignar centavos por resto mayor para reconciliar exactamente el total.

Los empates siguen el orden estable del catálogo: la salida es determinista.
"""
    if total<0 or not np.isfinite(total) or (participation<0).any() or not np.isclose(participation.sum(),1):
        raise ValueError('Total o composición inválidos.')
    cents=int(np.floor(total*100+0.5))
    raw=participation.to_numpy()*cents
    rounded=np.floor(raw).astype('int64')
    remaining=cents-int(rounded.sum())
    order=np.argsort(-(raw-rounded),kind='stable')
    rounded[order[:remaining]]+=1
    return pd.Series(rounded/100,index=participation.index)
