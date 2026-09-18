import numpy as np
import pandas as pd


def total_metrics(predictions,common=False):
    rows=[]
    eligible={}
    if common:
        for h,g in predictions.groupby('horizonte'):
            wide=g.pivot(index='origen',columns='modelo',values='prediccion')
            # Main comparison: hybrid, selected components and last observed.
            primary=[c for c in wide if c not in ('promedio_4s','estacional_52s')]
            valid=g.groupby('origen').real.first().notna() & wide[primary].notna().all(axis=1)
            eligible[h]=set(wide.index[valid])
    for (h,model),group in predictions.groupby(['horizonte','modelo']):
        g=group.dropna(subset=['prediccion','real'])
        primary=model not in ('promedio_4s','estacional_52s')
        if common and primary:
            g=g.loc[g.origen.isin(eligible[h])]
        e=g.real-g.prediccion
        scaled=e.abs()/g.escala_mase.replace(0,np.nan)
        rows.append(dict(horizonte=h,modelo=model,n=len(g),rmse=float(np.sqrt(np.mean(e**2))) if len(g) else np.nan,
            mae=float(e.abs().mean()),mase=float(scaled.mean()),n_mase=int(scaled.notna().sum()),
            excluidas=len(group)-len(g),comparacion='principal_fechas_comunes' if common and primary else 'complementaria_disponibilidad_propia' if common else 'fechas_comunes'))
    return pd.DataFrame(rows)


def composition_metrics(frame):
    rows=[]
    for (h,model,item),g in frame.groupby(['horizonte','modelo','insumo_id']):
        error=(g.real-g.prediccion).abs()*100
        rows.append(dict(horizonte=h,modelo=model,insumo_id=item,mae_pp=float(error.mean()),n=int(error.notna().sum()),excluidas=int(error.isna().sum())))
    result=pd.DataFrame(rows)
    macro=result.groupby(['horizonte','modelo'],as_index=False).agg(mae_pp=('mae_pp','mean'),n=('n','min'),excluidas=('excluidas','max'))
    macro['insumo_id']='PROMEDIO_MACRO'
    return pd.concat([result,macro],ignore_index=True)


def paired_interval(differences,cfg):
    """Exploratory paired circular block bootstrap; positive favors proposed model."""
    d=np.asarray(differences,float)
    n=int(np.isfinite(d).sum())
    if np.isinf(d).any() or n<cfg.min_inference_weeks or len(d)<2*cfg.bootstrap_block:
        return {'estado':'muestra_insuficiente','n':n,'media':float(np.nanmean(d)) if n else None,'limite_inferior':None,'limite_superior':None}
    rng=np.random.default_rng(cfg.seed)
    starts=rng.integers(0,len(d),size=(cfg.bootstrap_samples,int(np.ceil(len(d)/cfg.bootstrap_block))))
    idx=(starts[:,:,None]+np.arange(cfg.bootstrap_block))%len(d)
    samples=d[idx.reshape(cfg.bootstrap_samples,-1)[:,:len(d)]]
    # Keep undefined composition weeks in the calendar; never join distant weeks.
    valid_counts=np.isfinite(samples).sum(axis=1)
    means=np.nansum(samples,axis=1)[valid_counts>0]/valid_counts[valid_counts>0]
    # Bonferroni simultaneous 95% intervals for the two predeclared H1 endpoints.
    low,high=np.quantile(means,[0.0125,0.9875])
    return {'estado':'estimado','n':n,'media':float(np.nanmean(d)),'limite_inferior':float(low),'limite_superior':float(high)}


def hypothesis(predictions,composition,cfg,demo=False):
    p=predictions[predictions.horizonte==1].pivot(index='origen',columns='modelo',values=['real','prediccion'])
    y=p[('real','hibrido')]
    money=(y-p[('prediccion','ultimo_valor')])**2-(y-p[('prediccion','hibrido')])**2
    c=composition[(composition.horizonte==1)].copy()
    c['loss']=(c.real-c.prediccion).abs()*100
    c=c.groupby(['origen','modelo']).loss.mean().unstack()
    percent=(c['participacion_historica']-c['participacion_ewm']).reindex(money.index)
    a,b=paired_interval(money,cfg),paired_interval(percent,cfg)
    favorable=all(x['limite_inferior'] is not None and x['limite_inferior']>0 for x in (a,b))
    confirmatory=False
    return {'hipotesis':'H1','horizonte_principal':1,'importe':a,'composicion':b,
        'evidencia_favorable_ambos_componentes':favorable,
        'respaldo_confirmatorio':bool(favorable and confirmatory),
        'alcance':'demostracion_sintetica' if demo else ('confirmatorio_condicionado_al_protocolo' if confirmatory else 'retrospectivo_exploratorio'),
        'metodo':'Bootstrap circular pareado por semanas; bloques fijados en configuración; intervalos simultáneos Bonferroni para dos componentes de H1.',
        'advertencia':'No garantiza validez inferencial con muestras pequeñas. No reusar test explorado como confirmación independiente.'}
