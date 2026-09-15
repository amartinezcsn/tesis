"""Figuras trazables por fase; datos de respaldo y omisiones explícitas."""
from pathlib import Path
import hashlib
import json
import os
import numpy as np
import pandas as pd

TITLES=[
'Arquitectura del pipeline','Auditoría de registros','Cobertura semanal','Importe semanal de compras',
'Selección de insumos en desarrollo','Composición semanal en desarrollo','Dependencia temporal en desarrollo',
'Distribución del importe y ceros','Descomposición temporal exploratoria','Particiones temporales',
'Disponibilidad de información','Selección de características','Integración híbrida',
'Pesos y validación interna','Pronósticos fuera de muestra','Composición observada y pronosticada',
'Asignación y reconciliación','Errores monetarios','Errores de participación',
'Diferencias de pérdidas para H1','Presupuesto de las cuatro semanas siguientes','Interfaz del tablero','Controles de calidad']


def generate_figures(output,purchases,rejected,coverage,panel=None,results=None,controls=None,demo=False):
    output=Path(output); directory=output/'figuras'; directory.mkdir(exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str(output/'.matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
    manifest=[]; generated=set()
    def save(number,figure,table,chapter='Desarrollo'):
        title=TITLES[number]; ident=f'F{number:02}'
        figure.suptitle(title,fontsize=14)
        note=('DEMOSTRACIÓN SINTÉTICA — NO ES EVIDENCIA DE TESIS' if demo else 'Importes registrados utilizables; huecos conservados; cobertura no certificada' if results and results.get('politica_faltantes')=='calendar_gaps' else 'Fuente: registros auditados de la ejecución')
        figure.text(.5,.005,note,ha='center',fontsize=8,color='#9d2525' if demo else '#444444')
        figure.tight_layout(rect=(0,.035,1,.94))
        for ext in ('png','svg'):figure.savefig(directory/f'{ident}.{ext}',dpi=300)
        table.to_csv(directory/f'{ident}_datos.csv',index=False)
        digest=hashlib.sha256((directory/f'{ident}_datos.csv').read_bytes()).hexdigest()
        manifest.append(dict(id=ident,titulo=title,estado='generada',archivo=f'figuras/{ident}.png',
            vector=f'figuras/{ident}.svg',datos=f'figuras/{ident}_datos.csv',sha256_datos=digest,
            run_id=output.name,capitulo=chapter,motivo='',demostracion=demo))
        generated.add(number);plt.close(figure)
    def diagram(number,labels):
        fig,ax=plt.subplots(figsize=(10,3));ax.axis('off')
        for i,label in enumerate(labels):
            x=(i+.5)/len(labels)
            ax.text(x,.5,label,ha='center',va='center',transform=ax.transAxes,
                bbox=dict(boxstyle='round,pad=.7',facecolor='#e9f1f7',edgecolor='#345f7e'),fontsize=9)
            if i:ax.annotate('',xy=(x-.07,.5),xytext=(x-1/len(labels)+.07,.5),xycoords='axes fraction',arrowprops={'arrowstyle':'->'})
        save(number,fig,pd.DataFrame({'etapa':labels}),'Metodología')
    diagram(0,['Fuentes y\ncobertura','Panel\nsemanal','Validación\ntemporal','Total híbrido\ny composición','Evaluación\ny presupuesto'])
    diagram(10,['Historia cerrada\nantes de origen','Exógena con\navailable_at ≤ origen','Calendario\nde semana objetivo','Pronóstico\nh = 1, 2, 3, 4'])
    diagram(12,['Componente\nestadístico','Peso w por\nhorizonte','Componente ML\npeso (1 − w)','Pronóstico\nhíbrido'])
    counts=pd.concat([pd.Series({'aceptados_para_revision':len(purchases)}),rejected.motivo.value_counts()])
    fig,ax=plt.subplots(figsize=(9,4));ax.barh(counts.index,counts.values,color='#3c708c');ax.set_xlabel('Registros')
    save(1,fig,counts.rename_axis('estado').reset_index(name='registros'))
    cov=coverage.reset_index() if 'semana_inicio' not in coverage else coverage.copy()
    if 'semana_inicio' not in cov:cov=cov.rename(columns={cov.columns[0]:'semana_inicio'})
    states={'observada':0,'registrada':1,'cero_confirmado':2,'incompleta':3,'incierta':4,'desconocida':5}
    fig,ax=plt.subplots(figsize=(11,3));x=pd.to_datetime(cov.semana_inicio)
    for state,value in states.items():
        mask=cov.estado.eq(state);ax.scatter(x[mask],np.repeat(value,mask.sum()),label=state,s=18)
    ax.set_yticks(list(states.values()),list(states));ax.set_xlabel('Semana');save(2,fig,cov)
    if panel is not None and results is not None:
        from .composition import shares
        cutoff=results['cutoff'];dev=panel.iloc[:cutoff];cats=results['categories']
        fig,ax=plt.subplots(figsize=(10,4));ax.plot(panel.index,panel.total,color='#345f7e');ax.axvline(panel.index[cutoff],color='black',linestyle='--',label='Inicio evaluación');ax.set_ylabel('MXN nominales');ax.legend()
        save(3,fig,panel.reset_index())
        pareto=dev.drop(columns='total').sum().sort_values(ascending=False)
        fig,ax=plt.subplots(figsize=(10,5));pareto.plot.bar(ax=ax,color=['#346d96' if c in cats else '#b8c4cb' for c in pareto.index]);ax.set_ylabel('MXN nominales');ax.tick_params(axis='x',rotation=70,labelsize=8)
        ax2=ax.twinx();ax2.plot(range(len(pareto)),pareto.cumsum()/pareto.sum()*100,color='#a24722',marker='o');ax2.set_ylabel('Participación acumulada (%)');ax2.set_ylim(0,105)
        save(4,fig,pd.DataFrame({'insumo':pareto.index,'importe':pareto.values,'acumulado_pct':(pareto.cumsum()/pareto.sum()*100).values}))
        comp=shares(dev,cats)
        fig,ax=plt.subplots(figsize=(11,max(3,len(comp.columns)*.35)));im=ax.imshow(comp.T*100,aspect='auto',interpolation='nearest',vmin=0,vmax=100,cmap='Blues');ax.set_yticks(range(len(comp.columns)),comp.columns);ax.set_xlabel('Semana del conjunto de desarrollo');fig.colorbar(im,ax=ax,label='Participación (%)');save(5,fig,comp.reset_index())
        from statsmodels.tsa.stattools import acf,pacf
        if len(dev)>=10 and dev.total.notna().all() and dev.total.std()>0:
            lags=min(26,len(dev)//2-1);ac=acf(dev.total,nlags=lags);pc=pacf(dev.total,nlags=lags)
            fig,axes=plt.subplots(1,2,figsize=(10,4))
            for ax,values,label in zip(axes,[ac,pc],['ACF','PACF']):ax.stem(range(len(values)),values);ax.set_title(label);ax.set_xlabel('Rezago semanal')
            save(6,fig,pd.DataFrame({'rezago':range(lags+1),'acf':ac,'pacf':pc}))
        fig,axes=plt.subplots(1,2,figsize=(10,4));axes[0].hist(dev.total,bins=20,color='#346d96');axes[0].set_xlabel('MXN nominales');axes[1].bar(['Cero','Positivo'],[(dev.total==0).sum(),(dev.total>0).sum()],color=['#aaa','#346d96']);axes[1].set_ylabel('Semanas');save(7,fig,dev[['total']].reset_index())
        if len(dev)>=156 and dev.total.notna().all():
            from statsmodels.tsa.seasonal import STL
            stl=STL(dev.total,period=52,robust=True).fit();tab=pd.DataFrame({'fecha':dev.index,'tendencia':stl.trend,'estacional':stl.seasonal,'residuo':stl.resid})
            fig,axes=plt.subplots(3,1,figsize=(10,7))
            for ax,col in zip(axes,tab.columns[1:]):ax.plot(tab.fecha,tab[col]);ax.set_ylabel(col)
            save(8,fig,tab)
        folds=results['particiones'];fig,ax=plt.subplots(figsize=(11,5))
        subset=folds[folds.horizonte==4]
        for i,r in enumerate(subset.itertuples()):
            ax.plot([r.entrenamiento_inicio,r.ultima_etiqueta_entrenamiento],[i,i],color='#346d96',linewidth=3)
            ax.scatter(r.fecha_objetivo,i,color='#b44828' if r.etapa=='evaluacion' else '#379166',s=15)
        ax.set_ylabel('Origen (h=4)');ax.set_xlabel('Fecha; azul: entrenamiento, punto: objetivo');save(9,fig,folds)
        score=results['seleccion_interna'];fig,axes=plt.subplots(1,2,figsize=(10,4))
        for h,g in score.groupby('horizonte'):axes[0].plot(range(len(g)),np.sqrt(g.mse),'.',label=f'h={h}')
        axes[0].set_ylabel('RMSE de validación (MXN)');axes[0].set_xlabel('Configuración candidata');axes[0].legend()
        axes[1].bar(list(results['selection']),[s['peso'] for s in results['selection'].values()]);axes[1].set_ylim(0,1);axes[1].set_xlabel('Horizonte');axes[1].set_ylabel('Peso estadístico seleccionado');save(13,fig,score)
        p=results['predicciones'];fig,axes=plt.subplots(2,2,figsize=(12,7))
        for h,ax in zip(range(1,5),axes.flat):
            for model,color in [('hibrido','#346d96'),('ultimo_valor','#b44828')]:
                g=p[(p.horizonte==h)&(p.modelo==model)];ax.plot(g.fecha_objetivo,g.prediccion,label=model,color=color)
                if model=='hibrido':ax.plot(g.fecha_objetivo,g.real,label='Observado',color='black',linestyle=':')
            ax.set_title(f'h={h}');ax.tick_params(axis='x',labelrotation=30,labelsize=7);ax.set_ylabel('MXN');ax.legend(fontsize=8)
        save(14,fig,p,'Resultados')
        c=results['composicion'];first=c[(c.horizonte==1)&(c.modelo=='participacion_ewm')&c.real.notna()].origen.min()
        if pd.notna(first):
            example=c[(c.horizonte==1)&(c.origen==first)&(c.modelo=='participacion_ewm')]
            fig,ax=plt.subplots(figsize=(9,4));example.set_index('insumo_id')[['real','prediccion']].T.mul(100).plot.bar(stacked=True,ax=ax);ax.set_ylabel('Participación (%)');ax.legend(bbox_to_anchor=(1,1),fontsize=8);ax.set_xlabel('Primera semana válida, regla predefinida');save(15,fig,example,'Resultados')
        assignments=results['asignaciones'];example=assignments[(assignments.horizonte==1)&(assignments.origen==assignments.origen.min())]
        fig,ax=plt.subplots(figsize=(10,4));ax.barh(example.insumo_id,example.importe,color='#346d96');ax.set_xlabel('MXN nominales asignados');save(16,fig,example,'Resultados')
        metrics=results['metricas'];fig,axes=plt.subplots(1,2,figsize=(12,5))
        for metric,ax in zip(['rmse','mae'],axes):metrics.pivot(index='modelo',columns='horizonte',values=metric).plot.barh(ax=ax);ax.set_xlabel(metric.upper()+' (MXN)')
        save(17,fig,metrics,'Resultados')
        cm=results['metricas_composicion'];fig,ax=plt.subplots(figsize=(10,5));cm[cm.horizonte==1].pivot(index='insumo_id',columns='modelo',values='mae_pp').plot.barh(ax=ax);ax.set_xlabel('MAE de participación (puntos porcentuales), h=1');save(18,fig,cm,'Resultados')
        loss=p[p.horizonte==1].pivot(index='origen',columns='modelo',values=['real','prediccion']);y=loss[('real','hibrido')]
        dif=(y-loss[('prediccion','ultimo_valor')])**2-(y-loss[('prediccion','hibrido')])**2
        cc=c[c.horizonte==1].copy();cc['error_pp']=(cc.real-cc.prediccion).abs()*100;cp=cc.groupby(['origen','modelo']).error_pp.mean().unstack();dp=cp.participacion_historica-cp.participacion_ewm
        fig,axes=plt.subplots(2,1,figsize=(10,6))
        for ax,s,label in zip(axes,[dif,dp],['Diferencia de pérdida monetaria (MXN²)','Diferencia de MAE de participación (pp)']):ax.plot(s.index,s.values,marker='o');ax.axhline(0,color='black',linestyle='--');ax.set_ylabel(label,fontsize=8)
        save(19,fig,pd.concat([dif.rename('diferencia_monetaria'),dp.rename('diferencia_pp')],axis=1).reset_index(),'Resultados')
        future=results['pronostico_futuro'];fig,ax=plt.subplots(figsize=(10,5));future.pivot(index='horizonte',columns='insumo_id',values='importe').plot.bar(stacked=True,ax=ax);ax.set_ylabel('MXN nominales');ax.set_xlabel('Horizonte desde el corte guardado');ax.legend(bbox_to_anchor=(1,1),fontsize=8);save(20,fig,future)
    if controls:
        tab=pd.DataFrame(controls);fig,ax=plt.subplots(figsize=(10,4));ax.barh(tab.control,tab.aprobado.astype(int),color='#367d59');ax.set_xlim(0,1.2);ax.set_xticks([0,1],['Falló','Aprobado']);save(22,fig,tab)
    for number,title in enumerate(TITLES):
        if number not in generated:
            reason='Sin ejecución empírica aprobada.'
            if number==6:reason='ACF/PACF requiere desarrollo continuo observado; no se comprimen ni imputan huecos.'
            if number==8:reason='STL requiere al menos 156 semanas de desarrollo sin huecos en esta configuración.'
            if number==11:reason='Esta versión usa un conjunto parsimonioso prefijado, sin selección por frecuencia; no se fabrican importancias.'
            if number==21:reason='Captura requiere inspeccionar el HTML de la ejecución en navegador; no se sustituye con una maqueta.'
            manifest.append(dict(id=f'F{number:02}',titulo=title,estado='omitida',archivo='',datos='',run_id=output.name,capitulo='Desarrollo',motivo=reason,demostracion=demo))
    manifest=sorted(manifest,key=lambda r:r['id'])
    (output/'manifiesto_figuras.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame(manifest).to_csv(output/'manifiesto_figuras.csv',index=False)
    lines=['# Figuras para la tesis','', 'Paquete de demostración: no insertar como evidencia empírica.' if demo else 'Insertar únicamente después de revisar datos y contenido.','']
    for row in manifest:lines.extend([f"## {row['id']} {row['titulo']}",'',f"Estado: {row['estado']}. Capítulo sugerido: {row['capitulo']}.",f"Archivo: {row['archivo']}. Motivo: {row['motivo']}",''])
    (output/'guia_figuras.md').write_text('\n'.join(lines),encoding='utf-8')
    return manifest
