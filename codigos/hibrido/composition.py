"""Segundo componente del sistema: participaciones y reparto del presupuesto."""
import numpy as np
import pandas as pd

EXCLUDED_BUDGET_CATEGORIES = {'COMBUSTIBLE','MUEBLES','HERRAMIENTA','IMPUTADO','IMPUTADOS','OTROS'}


def select_categories(history, threshold, excluded_categories=EXCLUDED_BUDGET_CATEGORIES):
    """Fijar insumos principales según su importe acumulado en desarrollo."""
    sums=history.drop(columns='total').sum().sort_values(ascending=False,kind='stable')
    normalized=sums.index.astype(str).str.strip().str.upper()
    excluded={str(value).strip().upper() for value in excluded_categories}
    sums=sums[~normalized.isin(excluded)]
    sums=sums[sums>0]
    if sums.empty: raise ValueError('Sin historia positiva para composición.')
    count=min(len(sums),int(np.searchsorted(sums.cumsum()/sums.sum(),threshold))+1)
    return sums.index[:count].tolist()


def amounts(panel,categories):
    """Importes de categorías elegidas, sin redistribuirles las categorías omitidas."""
    return panel.reindex(columns=categories,fill_value=0.).copy()


def shares(panel,categories):
    """Convertir importes observados en proporciones del total semanal."""
    return amounts(panel,categories).div(panel.total.where(panel.total>0),axis=0)


def predict_shares(history,categories,alpha=None,calendar=False):
    """Estimar participaciones de categorías respecto al total elegible.

Las categorías no seleccionadas conservan su remanente; no se reasignan a
los insumos principales.
"""
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
    result=np.clip(prediction.to_numpy(float),0.,1.)
    result=pd.Series(result,index=valid.columns)
    if result.sum()>1+1e-8:
        raise ValueError('Las participaciones principales exceden el total elegible.')
    return result


def with_eligible_remainder(participation):
    """Completar el vector con el remanente de categorías elegibles no listadas."""
    result=participation.astype(float).clip(lower=0.).copy()
    if 'RESTO_ELEGIBLE' in result.index:
        raise ValueError('RESTO_ELEGIBLE es una etiqueta reservada de salida.')
    remainder=1.-float(result.sum())
    if remainder < -1e-8:
        raise ValueError('Las participaciones principales exceden el total elegible.')
    result.loc['RESTO_ELEGIBLE']=max(0.,remainder)
    # Mitiga solo el error de redondeo flotante; no redistribuye masa omitida.
    result/=result.sum()
    return result


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
