from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from .features import partitions
from .models import components, candidates, baselines, predict_stat
from .composition import select_categories, shares, predict_shares, allocate
from .evaluation import total_metrics, composition_metrics, hypothesis


def select_models(panel,cfg,exog,sales=None):
    cutoff,tuning,evaluation,folds=partitions(panel,cfg)
    # Vocabulary is fixed by available sources in development, not future rows.
    variables=sorted(exog.loc[exog.available_at <= panel.index[tuning[0]-cfg.window-max(cfg.horizons)+1],'variable'].unique())
    selections={}; scores=[]; failures=[]; comp_scores=[]
    for h in cfg.horizons:
        inner=[]
        for origin in tuning:
            pred,_,errors,_=components(panel,origin,h,cfg,exog,variables,sales)
            failures.extend(errors)
            inner.append((pred,float(panel.total.iloc[origin+h-1])))
        stats,mls=candidates(cfg)
        for stat in stats:
            for ml in mls:
                for weight in cfg.weights:
                    if any(stat not in pred or ml not in pred for pred,_ in inner):continue
                    mse=float(np.mean([(y-weight*p[stat]-(1-weight)*p[ml])**2 for p,y in inner]))
                    scores.append(dict(horizonte=h,stat=stat,ml=ml,peso=weight,mse=mse,n=len(inner)))
        available=[r for r in scores if r['horizonte']==h]
        if not available:raise ValueError(f'Sin combinación válida para h={h}; fallos: {failures}')
        selections[h]=min(available,key=lambda r:r['mse'])
    # Categories are learned afresh on each inner training window.
    for alpha in cfg.alphas:
        losses=[]
        for origin in tuning:
            history=panel.iloc[origin-cfg.window:origin]
            categories=select_categories(history,cfg.threshold)
            real=shares(panel.iloc[[origin]],categories).iloc[0]
            if real.notna().all():
                pred=predict_shares(history,categories,alpha)
                losses.append(float((real-pred).abs().mean()*100))
        if losses:comp_scores.append(dict(alpha=alpha,mae_pp=float(np.mean(losses)),n=len(losses)))
    if not comp_scores:raise ValueError('Sin semanas positivas para validar composición.')
    alpha=min(comp_scores,key=lambda r:r['mae_pp'])['alpha']
    categories=select_categories(panel.iloc[:cutoff],cfg.threshold)
    return selections,alpha,categories,variables,cutoff,tuning,evaluation,folds,pd.DataFrame(scores),pd.DataFrame(comp_scores),failures


def run_experiment(panel,cfg,exog,output,sales=None,demo=False):
    output=Path(output)
    (selected,alpha,categories,variables,cutoff,tuning,evaluation,folds,scores,comp_scores,failures)=select_models(panel,cfg,exog,sales)
    rows=[]; composition=[]; allocations=[]
    for origin in evaluation:
        history=panel.iloc[origin-cfg.window:origin]
        prop=predict_shares(history,categories,alpha)
        ref=predict_shares(history,categories)
        scale=float(history.total.diff().abs().mean())
        for h in cfg.horizons:
            selection=selected[h]
            pred,_,errors,_=components(panel,origin,h,cfg,exog,variables,sales,selection)
            if errors:raise ValueError(f'Fallo del modelo fijado en evaluación: {errors}')
            pred['hibrido']=selection['peso']*pred[selection['stat']]+(1-selection['peso'])*pred[selection['ml']]
            pred.update(baselines(history.total,h))
            target=origin+h-1
            for name,value in pred.items():
                rows.append(dict(origen=panel.index[origin],fecha_objetivo=panel.index[target],horizonte=h,modelo=name,
                    real=float(panel.total.iloc[target]),prediccion=value,escala_mase=scale))
            real=shares(panel.iloc[[target]],categories).iloc[0]
            for name,values in [('participacion_historica',ref),('participacion_ewm',prop)]:
                for item,value in values.items():
                    composition.append(dict(origen=panel.index[origin],fecha_objetivo=panel.index[target],horizonte=h,
                        modelo=name,insumo_id=item,real=float(real[item]),prediccion=float(value)))
            budget=allocate(pred['hibrido'],prop)
            for item,value in budget.items():
                allocations.append(dict(origen=panel.index[origin],fecha_objetivo=panel.index[target],horizonte=h,
                    insumo_id=item,participacion=float(prop[item]),importe=value,total_redondeado=float(budget.sum())))
    predictions=pd.DataFrame(rows); composition=pd.DataFrame(composition); allocations=pd.DataFrame(allocations)
    metrics=total_metrics(predictions); percentages=composition_metrics(composition)
    result=hypothesis(predictions,composition,cfg,demo)
    # Final fit is selected in development, never from the final ranking.
    origin=len(panel); bundle={'version':1,'moneda':'MXN nominales','demostracion':demo,
        'origen':str(panel.index[-1]+pd.Timedelta(weeks=1)),'config':cfg.dictionary(),
        'seleccion':selected,'alpha_composicion':alpha,'categorias':categories,'variables_exogenas':variables,'modelos':{}}
    prop=predict_shares(panel.iloc[-cfg.window:],categories,alpha)
    bundle['participaciones']=prop
    for h in cfg.horizons:
        pred,fitted,errors,test=components(panel,origin,h,cfg,exog,variables,sales,selected[h])
        if errors:raise ValueError(f'Fallo de entrenamiento final: {errors}')
        bundle['modelos'][h]={'stat':fitted[selected[h]['stat']],'ml':fitted[selected[h]['ml']],'x_emision':test}
    joblib.dump(bundle,output/'modelos.joblib')
    future=forecast_bundle(bundle)
    reloaded=forecast_bundle(joblib.load(output/'modelos.joblib'))
    pd.testing.assert_frame_equal(future,reloaded)
    datasets={'predicciones':predictions,'composicion':composition,'asignaciones':allocations,'metricas':metrics,
        'metricas_composicion':percentages,'particiones':folds,'seleccion_interna':scores,
        'seleccion_composicion':comp_scores,'pronostico_futuro':future,'fallos_componentes':pd.DataFrame(failures)}
    for name,table in datasets.items():table.to_csv(output/(name+'.csv'),index=False)
    with pd.ExcelWriter(output/'resultados.xlsx',engine='openpyxl') as writer:
        for name,table in datasets.items():table.to_excel(writer,sheet_name=name[:31],index=False)
    (output/'hipotesis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'seleccion.json').write_text(json.dumps({'modelos':selected,'alpha':alpha,'categorias':categories,'variables':variables,
        'corte_desarrollo':str(panel.index[cutoff]),'criterio':'validacion temporal interna, no ranking de evaluación'},ensure_ascii=False,indent=2),encoding='utf-8')
    datasets.update(cutoff=cutoff,categories=categories,selection=selected,hypothesis=result)
    return datasets


def forecast_bundle(bundle):
    """Reproduce la emisión del corte guardado; un nuevo corte requiere reentrenar."""
    rows=[]; prop=bundle['participaciones']
    for h,models in bundle['modelos'].items():
        stat=predict_stat(models['stat'],int(h))
        ml=max(0.,float(models['ml'].predict(models['x_emision'])[0]))
        weight=bundle['seleccion'][h]['peso']
        total=weight*stat+(1-weight)*ml
        if not np.isfinite(total):raise ValueError('Inferencia no finita.')
        allocation=allocate(total,prop)
        for item,amount in allocation.items():
            rows.append(dict(origen=bundle['origen'],fecha_objetivo=str(pd.Timestamp(bundle['origen'])+pd.Timedelta(weeks=int(h)-1)),
                horizonte=int(h),insumo_id=item,participacion=float(prop[item]),importe=float(amount),
                total=float(allocation.sum()),unidad='MXN nominales',demostracion=bundle['demostracion']))
    return pd.DataFrame(rows)
