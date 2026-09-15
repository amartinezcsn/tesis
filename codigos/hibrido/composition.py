import numpy as np
import pandas as pd


def select_categories(history, threshold):
    sums=history.drop(columns='total').sum().sort_values(ascending=False,kind='stable')
    sums=sums[sums>0]
    if sums.empty: raise ValueError('Sin historia positiva para composición.')
    count=min(len(sums),int(np.searchsorted(sums.cumsum()/sums.sum(),threshold))+1)
    return sums.index[:count].tolist()


def amounts(panel,categories):
    result=panel.reindex(columns=categories,fill_value=0.).copy()
    result['otros']=panel.drop(columns=['total',*categories],errors='ignore').sum(axis=1)
    return result


def shares(panel,categories):
    return amounts(panel,categories).div(panel.total.where(panel.total>0),axis=0)


def predict_shares(history,categories,alpha=None,calendar=False):
    valid=shares(history,categories).dropna()
    if valid.empty:raise ValueError('Sin semanas de composición definida.')
    if calendar and alpha is not None:
        # Time decay uses actual calendar age, never rank after dropping gaps.
        ages=(history.index[-1]-valid.index).days.to_numpy()/7
        weights=(1-alpha)**ages
        if not weights.sum():raise ValueError('Pesos de composición sin soporte.')
        prediction=valid.mul(weights,axis=0).sum()/weights.sum()
    else:
        prediction=valid.mean() if alpha is None else valid.ewm(alpha=alpha,adjust=False).mean().iloc[-1]
    result=np.maximum(prediction.to_numpy(float),0.)
    return pd.Series(result/result.sum(),index=valid.columns)


def allocate(total,participation):
    """Largest remainder: exact budget in cents, deterministic ties by catalog order."""
    if total<0 or not np.isfinite(total) or (participation<0).any() or not np.isclose(participation.sum(),1):
        raise ValueError('Total o composición inválidos.')
    cents=int(np.floor(total*100+0.5))
    raw=participation.to_numpy()*cents
    rounded=np.floor(raw).astype('int64')
    remaining=cents-int(rounded.sum())
    order=np.argsort(-(raw-rounded),kind='stable')
    rounded[order[:remaining]]+=1
    return pd.Series(rounded/100,index=participation.index)
