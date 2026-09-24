"""Experimento temporal: selección interna, prueba final y emisión futura."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from .features import partitions
from .models import components, candidates, baselines, predict_stat
from .composition import select_categories, shares, predict_shares, with_eligible_remainder, allocate
from .evaluation import total_metrics, composition_metrics, hypothesis
from .gaps import history as training_history, composition_history


def select_models(panel,cfg,exog,sales=None):
    """Elegir componentes, peso, alfa y categorías usando solo desarrollo.

Cada horizonte tiene su propia pareja estadístico/ML y su peso. La prueba
final aún no participa en ninguna elección.
"""
    cutoff,tuning,evaluation,folds=partitions(panel,cfg)
    # Fijar nombres de exógenas en desarrollo; gap_features aún comprueba
    # available_at para cada origen y evita usar valores publicados después.
    variables=sorted(exog.loc[exog.available_at <= panel.index[tuning[0]],'variable'].unique())
    selections={}; scores=[]; failures=[]; comp_scores=[]; composition_exclusions=[]
    for h in cfg.horizons:
        # Simular pronósticos retrospectivos solo en orígenes internos.
        inner=[]
        for origin in tuning:
            if pd.isna(panel.total.iloc[origin+h-1]):continue
            pred,_,errors,_=components(panel,origin,h,cfg,exog,variables,sales)
            failures.extend(errors)
            inner.append((pred,float(panel.total.iloc[origin+h-1])))
        stats,mls=candidates(cfg)
        if not inner:
            if not stats or not mls:
                raise ValueError(f'Sin componentes para h={h}; fallos: {failures}')
            selections[h]=dict(horizonte=h,stat=stats[0],ml=mls[0],peso=float(cfg.weights[len(cfg.weights)//2]),
                mse=None,n=0,seleccion='sin_validacion_interna')
            continue
        for stat in stats:
            # Probar parejas y pesos declarados; gana el menor MSE interno.
            for ml in mls:
                if ml in ('rf_residual','nn_residual') and stat!='ss_arima111':
                    continue
                ml_key=f'{ml}__{stat}' if ml in ('rf_residual','nn_residual') else ml
                for weight in cfg.weights:
                    if any(stat not in pred or ml_key not in pred for pred,_ in inner):continue
                    mse=float(np.mean([(y-weight*p[stat]-(1-weight)*p[ml_key])**2 for p,y in inner]))
                    scores.append(dict(horizonte=h,stat=stat,ml=ml_key,peso=weight,mse=mse,n=len(inner)))
        available=[r for r in scores if r['horizonte']==h]
        if available:
            selections[h]=min(available,key=lambda r:r['mse'])
        else:
            # En la evaluación exploratoria puede no existir una etiqueta
            # observada para un horizonte dentro de los folds internos. Se
            # conserva una configuración base y se marca explícitamente.
            stats,mls=candidates(cfg)
            if not stats or not mls:
                raise ValueError(f'Sin componentes para h={h}; fallos: {failures}')
            selections[h]=dict(horizonte=h,stat=stats[0],ml=mls[0],peso=float(cfg.weights[len(cfg.weights)//2]),
                mse=None,n=0,seleccion='sin_validacion_interna')
    # Evaluar la mezcla de insumos con categorías aprendidas en cada historia.
    composition_origins=tuning
    if not any(pd.notna(panel.total.iloc[o+h-1]) for o in composition_origins for h in cfg.horizons if o+h-1<len(panel)):
        # En datos dispersos, los cinco orígenes de ajuste del total pueden
        # caer todos en semanas sin captura. Calibrar alpha en una cuadrícula
        # rolling más amplia, siempre anterior al holdout y con historia 52w.
        start=cfg.rolling_origin_start or cfg.training_window_weeks or cfg.lookback
        composition_origins=list(range(start,max(start,cutoff-max(cfg.horizons)+2),cfg.rolling_step_weeks))
    for alpha in cfg.alphas:
        losses=[]
        for origin in composition_origins:
            history=composition_history(panel,origin,cfg)
            positive_weeks=int((history.total>0).sum())
            if positive_weeks<cfg.min_composition_weeks:
                composition_exclusions.append(dict(origen=panel.index[origin],alpha=alpha,
                    semanas_composicion_positiva=positive_weeks,motivo='historia_elegible_insuficiente'))
                continue
            try:
                categories=select_categories(history,cfg.threshold,cfg.excluded_budget_categories)
                pred=predict_shares(history,categories,alpha,calendar=True)
            except ValueError as exc:
                composition_exclusions.append(dict(origen=panel.index[origin],alpha=alpha,
                    semanas_composicion_positiva=positive_weeks,motivo=str(exc)))
                continue
            for horizon in cfg.horizons:
                target=origin+horizon-1
                if target>=len(panel) or pd.isna(panel.total.iloc[target]):
                    continue
                real=shares(panel.iloc[[target]],categories).iloc[0]
                if real.notna().all():
                    losses.append(float((real-pred).abs().mean()*100))
        if losses:comp_scores.append(dict(alpha=alpha,mae_pp=float(np.mean(losses)),n=len(losses)))
    if not comp_scores:
        # Si las semanas de validación contienen únicamente etiquetas
        # excluidas, no se inventa una categoría residual. Se conserva una
        # configuración determinista y se deja constancia de que no hubo
        # soporte para comparar alphas.
        alpha=cfg.alphas[0]
        comp_scores.append(dict(alpha=alpha,mae_pp=np.nan,n=0,
            seleccion='sin_validacion_composicion'))
    else:
        alpha=min(comp_scores,key=lambda r:r['mae_pp'])['alpha']
    categories=select_categories(panel.iloc[:cutoff],cfg.threshold,cfg.excluded_budget_categories)
    return selections,alpha,categories,variables,cutoff,tuning,evaluation,folds,pd.DataFrame(scores),pd.DataFrame(comp_scores),failures,pd.DataFrame(composition_exclusions)


def run_experiment(panel,cfg,exog,output,sales=None,demo=False):
    """Ejecutar la evaluación congelada y guardar un modelo de emisión.

Devuelve las tablas necesarias para métricas, reportes y figuras; las
predicciones finales nunca retroalimentan la selección de candidatos.
"""
    cfg.validate()
    output=Path(output)
    (selected,alpha,categories,variables,cutoff,tuning,evaluation,folds,scores,comp_scores,failures,composition_exclusions)=select_models(panel,cfg,exog,sales)
    rows=[]; composition=[]; allocations=[]
    for origin in evaluation:
        # Ventana creciente: en cada origen entra solo la historia anterior.
        history=training_history(panel,origin,cfg)
        share_history=composition_history(panel,origin,cfg)
        prop=predict_shares(share_history,categories,alpha,calendar=True)
        ref=predict_shares(share_history,categories)
        scale=float(history.total.diff().abs().mean())
        for h in cfg.horizons:
            # El total híbrido es peso * estadístico + (1-peso) * ML.
            if origin+h-1>=len(panel):continue
            selection=selected[h]
            pred,_,errors,_=components(panel,origin,h,cfg,exog,variables,sales,selection)
            if errors:raise ValueError(f'Fallo del modelo fijado en evaluación: {errors}')
            pred['hibrido']=selection['peso']*pred[selection['stat']]+(1-selection['peso'])*pred[selection['ml']]
            pred.update(baselines(history.total,h,gaps=True))
            target=origin+h-1
            for name,value in pred.items():
                rows.append(dict(origen=panel.index[origin],fecha_objetivo=panel.index[target],horizonte=h,modelo=name,
                    real=float(panel.total.iloc[target]),prediccion=value,escala_mase=scale))
            if pd.isna(panel.total.iloc[target]):
                # La fila queda trazada para auditar el fold; las métricas la
                # excluyen porque real es NaN y no se fabrican composiciones.
                continue
            real=shares(panel.iloc[[target]],categories).iloc[0]
            for name,values in [('participacion_historica',ref),('participacion_ewm',prop)]:
                for item,value in values.items():
                    composition.append(dict(origen=panel.index[origin],fecha_objetivo=panel.index[target],horizonte=h,
                        modelo=name,insumo_id=item,real=float(real[item]),prediccion=float(value)))
            allocation_shares=with_eligible_remainder(prop)
            budget=allocate(pred['hibrido'],allocation_shares)
            # RESTO_ELEGIBLE conserva categorías elegibles menores; no es la
            # categoría presupuestaria excluida OTROS.
            for item,value in budget.items():
                allocations.append(dict(origen=panel.index[origin],fecha_objetivo=panel.index[target],horizonte=h,
                    insumo_id=item,participacion=float(allocation_shares[item]),importe=value,total_redondeado=float(budget.sum())))
    predictions=pd.DataFrame(rows); composition=pd.DataFrame(composition); allocations=pd.DataFrame(allocations)
    metrics=total_metrics(predictions,common=True); percentages=composition_metrics(composition)
    result=hypothesis(predictions,composition,cfg,demo)
    # Reajuste final con toda la historia, pero configuración elegida antes.
    origin=int(np.flatnonzero(panel.total.notna().to_numpy())[-1])+1
    origin_date=panel.index[origin] if origin<len(panel) else panel.index[-1]+pd.Timedelta(weeks=1)
    bundle={'version':1,'moneda':'MXN nominales','demostracion':demo,
        'origen':str(origin_date),'config':cfg.dictionary(),
        'seleccion':selected,'alpha_composicion':alpha,'categorias':categories,'variables_exogenas':variables,'modelos':{}}
    prop=predict_shares(composition_history(panel,origin,cfg),categories,alpha,calendar=True)
    bundle['participaciones']=with_eligible_remainder(prop)
    for h in cfg.horizons:
        pred,fitted,errors,test=components(panel,origin,h,cfg,exog,variables,sales,selected[h])
        if errors:raise ValueError(f'Fallo de entrenamiento final: {errors}')
        bundle['modelos'][h]={'stat':fitted[selected[h]['stat']],'ml':fitted[selected[h]['ml']],'x_emision':test}
    joblib.dump(bundle,output/'modelos.joblib')
    future=forecast_bundle(bundle)
    reloaded=forecast_bundle(joblib.load(output/'modelos.joblib'))
    # La recarga debe reproducir exactamente la emisión en memoria.
    pd.testing.assert_frame_equal(future,reloaded)
    four_week=aggregate_four_week_forecast(future)
    datasets={'predicciones':predictions,'composicion':composition,'asignaciones':allocations,'metricas':metrics,
        'metricas_composicion':percentages,'particiones':folds,'seleccion_interna':scores,
        'seleccion_composicion':comp_scores,'exclusiones_composicion':composition_exclusions,
        'pronostico_futuro':future,'pronostico_4_semanas':four_week,'fallos_componentes':pd.DataFrame(failures)}
    for name,table in datasets.items():table.to_csv(output/(name+'.csv'),index=False)
    with pd.ExcelWriter(output/'resultados.xlsx',engine='openpyxl') as writer:
        for name,table in datasets.items():table.to_excel(writer,sheet_name=name[:31],index=False)
    (output/'hipotesis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'seleccion.json').write_text(json.dumps({'modelos':selected,'alpha':alpha,'categorias':categories,'variables':variables,
        'corte_desarrollo':str(panel.index[cutoff]),'criterio':'validacion temporal interna, no ranking de evaluación'},ensure_ascii=False,indent=2),encoding='utf-8')
    datasets.update(cutoff=cutoff,categories=categories,selection=selected,hypothesis=result)
    excluded=int((folds['objetivo_observado']==False).sum())
    datasets['advertencia']=f'Evaluación rolling exploratoria de importes registrados utilizables, no del gasto real completo. Se excluyeron {excluded} objetivos inciertos de las métricas; no se imputaron ni sintetizaron. Calendario con huecos sin imputar. ultimo_valor significa último importe observado disponible, no necesariamente semana anterior. MASE usa solo diferencias entre semanas calendario consecutivas observadas. La cobertura no está certificada por la mera existencia de registros.'
    datasets['politica_faltantes']='calendar_gaps'
    return datasets


def forecast_bundle(bundle):
    """Reproducir cuatro semanas desde el corte guardado en ``modelos.joblib``.

No incorpora datos nuevos: para otro corte se actualizan fuentes y se corre
otra vez el pipeline completo.
"""
    rows=[]; prop=bundle['participaciones']
    for h,models in bundle['modelos'].items():
        stat=predict_stat(models['stat'],int(h))
        ml_value=float(models['ml'].predict(models['x_emision'])[0])
        residual=bundle['seleccion'][h]['ml'].startswith(('rf_residual__','nn_residual__'))
        ml=max(0.,stat+ml_value) if residual else max(0.,ml_value)
        weight=bundle['seleccion'][h]['peso']
        total=weight*stat+(1-weight)*ml
        if not np.isfinite(total):raise ValueError('Inferencia no finita.')
        allocation=allocate(total,prop)
        for item,amount in allocation.items():
            rows.append(dict(origen=bundle['origen'],fecha_objetivo=str(pd.Timestamp(bundle['origen'])+pd.Timedelta(weeks=int(h)-1)),
                horizonte=int(h),insumo_id=item,participacion=float(prop[item]),importe=float(amount),
                total=float(allocation.sum()),unidad='MXN nominales',demostracion=bundle['demostracion']))
    return pd.DataFrame(rows)


def aggregate_four_week_forecast(future):
    """Consolidar cuatro pronósticos semanales en presupuesto de 28 días."""
    horizons=set(pd.to_numeric(future.horizonte,errors='coerce').dropna().astype(int))
    if horizons!={1,2,3,4}:
        raise ValueError('El consolidado requiere los cuatro horizontes semanales.')
    grouped=future.groupby('insumo_id',as_index=False).importe.sum().rename(columns={'importe':'importe_4_semanas'})
    total=float(grouped.importe_4_semanas.sum())
    if not np.isfinite(total) or total<0:raise ValueError('Total de cuatro semanas inválido.')
    grouped['participacion_4_semanas']=grouped.importe_4_semanas/total if total else 0.
    grouped['total_4_semanas']=total
    grouped['unidad']='MXN nominales'
    grouped['periodo']='próximas 4 semanas (28 días)'
    return grouped.sort_values('importe_4_semanas',ascending=False,kind='stable').reset_index(drop=True)
