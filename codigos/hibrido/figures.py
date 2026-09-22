"""Figuras de metodología y resultados, con CSV y omisiones trazables.

La visualización puede agrupar categorías para ser legible; sus CSV de
respaldo conservan el detalle usado para verificarla.
"""
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
TITLES += ['Convergencia del error rolling','Correlación de variables']
TITLES += ['Ventas semanales y semanas sin captura']


def generate_figures(output,purchases,rejected,coverage,panel=None,results=None,controls=None,demo=False,exog=None,sales=None):
    """Crear figuras metodológicas/resultados y registrar por qué faltan otras."""
    output=Path(output); directory=output/'figuras'; directory.mkdir(exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str(output/'.matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
    manifest=[]; generated=set()
    def readable_labels(index):
        """Acortar nombres solo en los ejes, sin modificar identificadores."""
        return [str(value).replace('_',' ')[:38] + ('…' if len(str(value))>38 else '') for value in index]

    def top_with_remainder(frame, limit, order):
        """Mostrar los principales y agregar los demás únicamente en la figura."""
        chosen=[item for item in order if item!='otros'][:limit]
        shown=frame.reindex(columns=chosen,fill_value=0).copy()
        shown['Resto de insumos']=frame.drop(columns=chosen,errors='ignore').sum(axis=1)
        return shown

    def save(number,figure,table,chapter='Desarrollo'):
        """Guardar PNG, SVG y CSV, y añadir sus rutas al manifiesto."""
        title=TITLES[number]; ident=f'F{number:02}'
        figure.suptitle(title,fontsize=14)
        note=('DEMOSTRACIÓN SINTÉTICA — NO ES EVIDENCIA DE TESIS' if demo else 'Importes registrados utilizables; huecos conservados; cobertura no certificada' if results and results.get('politica_faltantes')=='calendar_gaps' else 'Fuente: registros auditados de la ejecución')
        figure.text(.5,.015,note,ha='center',fontsize=8,color='#9d2525' if demo else '#444444')
        figure.tight_layout(rect=(0,.075,1,.92))
        for ext in ('png','svg'):figure.savefig(directory/f'{ident}.{ext}',dpi=300)
        table.to_csv(directory/f'{ident}_datos.csv',index=False)
        digest=hashlib.sha256((directory/f'{ident}_datos.csv').read_bytes()).hexdigest()
        manifest.append(dict(id=ident,titulo=title,estado='generada',archivo=f'figuras/{ident}.png',
            vector=f'figuras/{ident}.svg',datos=f'figuras/{ident}_datos.csv',sha256_datos=digest,
            run_id=output.name,capitulo=chapter,motivo='',demostracion=demo))
        generated.add(number);plt.close(figure)
    def diagram(number,labels):
        """Dibujar un esquema metodológico; no representa un resultado medido."""
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
    # F01–F02: calidad de registros y cobertura, disponibles incluso en audit.
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
        # F03–F13: describir desarrollo y mostrar la selección temporal.
        from .composition import shares
        cutoff=results['cutoff'];dev=panel.iloc[:cutoff];cats=results['categories']
        fig,(ax,coverage_ax)=plt.subplots(2,1,figsize=(11,5),sharex=True,gridspec_kw={'height_ratios':[4,0.55]})
        ax.plot(panel.index,panel.total,color='#345f7e',label='Compras registradas')
        ax.axvline(panel.index[cutoff],color='black',linestyle='--',label='Inicio evaluación')
        ax.set_ylabel('MXN nominales');ax.legend()
        coverage_ax.scatter(panel.index[panel.total.notna()],np.ones(panel.total.notna().sum()),s=7,color='#379166')
        coverage_ax.set_ylim(.5,1.5);coverage_ax.set_yticks([1],['Captura']);coverage_ax.set_xlabel('Semana; huecos en línea/franja = sin registros')
        save(3,fig,panel.reset_index())
        if sales is not None:
            weekly_sales=sales['importe_nominal'] if isinstance(sales,pd.DataFrame) else sales
            weekly_sales=weekly_sales.reindex(panel.index)
            fig,(ax,sales_ax)=plt.subplots(2,1,figsize=(11,5),sharex=True,gridspec_kw={'height_ratios':[4,0.55]})
            ax.plot(weekly_sales.index,weekly_sales,color='#a64b2a',label='Ventas registradas')
            ax.set_ylabel('MXN nominales');ax.legend()
            sales_ax.scatter(weekly_sales.index[weekly_sales.notna()],np.ones(weekly_sales.notna().sum()),s=7,color='#379166')
            sales_ax.set_ylim(.5,1.5);sales_ax.set_yticks([1],['Captura']);sales_ax.set_xlabel('Semana; huecos en línea/franja = sin registros')
            sales_table=pd.DataFrame({'semana_inicio':weekly_sales.index,'ventas_registradas':weekly_sales.to_numpy(),
                'captura_observada':weekly_sales.notna().to_numpy()})
            save(25,fig,sales_table)
            gap_rows=[]
            for nombre,series in [('compras',panel.total),('ventas',weekly_sales)]:
                missing=series.index[series.isna()]
                if len(missing):
                    groups=(missing.to_series().diff().dt.days.ne(7)).cumsum()
                    for _,group in missing.to_series().groupby(groups):
                        gap_rows.append(dict(fuente=nombre,inicio=group.iloc[0],fin=group.iloc[-1],
                            semanas_ausentes=len(group),clasificacion='sin_captura_en_archivo'))
            gap_table=pd.DataFrame(gap_rows,columns=['fuente','inicio','fin','semanas_ausentes','clasificacion'])
            if not gap_table.empty:gap_table=gap_table.sort_values(['fuente','inicio'])
            gap_table.to_csv(output/'periodos_ausentes.csv',index=False)
        pareto=dev.drop(columns='total').sum().sort_values(ascending=False)
        leading=pareto.head(15).iloc[::-1]
        fig,ax=plt.subplots(figsize=(12,7));ax.barh(readable_labels(leading.index),leading.values,
            color=['#346d96' if c in cats else '#b8c4cb' for c in leading.index])
        ax.set_xlabel('MXN nominales');ax.set_title(f'15 principales: {pareto.head(15).sum()/pareto.sum():.1%} del importe total',fontsize=10)
        save(4,fig,pd.DataFrame({'insumo':pareto.index,'importe':pareto.values,'acumulado_pct':(pareto.cumsum()/pareto.sum()*100).values}))
        comp=shares(dev,cats)
        heat=top_with_remainder(comp,15,pareto.index)
        fig,ax=plt.subplots(figsize=(12,7));im=ax.imshow(heat.T*100,aspect='auto',interpolation='nearest',vmin=0,vmax=100,cmap='Blues')
        ax.set_yticks(range(len(heat.columns)),readable_labels(heat.columns));ax.set_xlabel('Semana del conjunto de desarrollo')
        fig.colorbar(im,ax=ax,label='Participación (%)');save(5,fig,comp.reset_index())
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
        if {'horizonte','mse'}.issubset(score.columns):
            for h,g in score.groupby('horizonte'):
                axes[0].plot(range(len(g)),np.sqrt(g.mse),'.',label=f'h={h}')
        else:
            axes[0].text(.5,.5,'Sin etiquetas observadas para comparar configuraciones',ha='center',va='center',wrap=True,transform=axes[0].transAxes)
        axes[0].set_ylabel('RMSE de validación (MXN)');axes[0].set_xlabel('Configuración candidata')
        if {'horizonte','mse'}.issubset(score.columns):axes[0].legend()
        axes[1].bar(list(results['selection']),[s['peso'] for s in results['selection'].values()]);axes[1].set_ylim(0,1);axes[1].set_xlabel('Horizonte');axes[1].set_ylabel('Peso estadístico seleccionado');save(13,fig,score)
        # F14–F20: resultados congelados, errores y presupuesto por insumo.
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
            values=example.set_index('insumo_id')[['real','prediccion']]
            leading=values.max(axis=1).sort_values(ascending=False).head(10).index
            display=top_with_remainder(values.T,10,leading).T.iloc[::-1].mul(100)
            fig,ax=plt.subplots(figsize=(11,7));display.plot.barh(ax=ax,color=['#346d96','#b44828'],width=.75)
            ax.set_yticklabels(readable_labels(display.index));ax.set_xlabel('Participación (%)');ax.set_ylabel('')
            ax.legend(['Observada','Pronosticada'],loc='upper right',fontsize=9)
            ax.set_title('Primera semana válida; 10 participaciones principales y resto',fontsize=10)
            save(15,fig,example,'Resultados')
        assignments=results['asignaciones'];example=assignments[(assignments.horizonte==1)&(assignments.origen==assignments.origen.min())]
        ranked=example.set_index('insumo_id').importe.sort_values(ascending=False)
        shown=ranked.head(12).copy();shown.loc['Resto de insumos']=ranked.iloc[12:].sum();shown=shown.iloc[::-1]
        fig,ax=plt.subplots(figsize=(11,7));ax.barh(readable_labels(shown.index),shown.values,color='#346d96')
        ax.set_xlabel('MXN nominales asignados');ax.set_title('Primer origen, h=1; 12 insumos principales y resto',fontsize=10)
        save(16,fig,example,'Resultados')
        metrics=results['metricas'];fig,axes=plt.subplots(1,2,figsize=(12,5))
        for metric,ax in zip(['rmse','mae'],axes):metrics.pivot(index='modelo',columns='horizonte',values=metric).plot.barh(ax=ax);ax.set_xlabel(metric.upper()+' (MXN)')
        save(17,fig,metrics,'Resultados')
        cm=results['metricas_composicion'];errors=cm[cm.horizonte==1].pivot(index='insumo_id',columns='modelo',values='mae_pp')
        leaders=errors.drop(index='PROMEDIO_MACRO',errors='ignore').max(axis=1).nlargest(12).index.tolist()
        if 'PROMEDIO_MACRO' in errors.index:leaders.append('PROMEDIO_MACRO')
        shown=errors.loc[leaders].iloc[::-1]
        fig,ax=plt.subplots(figsize=(12,7));shown.plot.barh(ax=ax,color=['#346d96','#b44828'],width=.75)
        ax.set_yticklabels(readable_labels(shown.index));ax.set_xlabel('MAE de participación (puntos porcentuales), h=1');ax.set_ylabel('')
        ax.legend(['Ponderación temporal','Promedio histórico'],fontsize=9)
        ax.set_title('12 mayores errores por insumo y promedio macro',fontsize=10)
        save(18,fig,cm,'Resultados')
        loss=p[p.horizonte==1].pivot(index='origen',columns='modelo',values=['real','prediccion']);y=loss[('real','hibrido')]
        dif=(y-loss[('prediccion','ultimo_valor')])**2-(y-loss[('prediccion','hibrido')])**2
        cc=c[c.horizonte==1].copy();cc['error_pp']=(cc.real-cc.prediccion).abs()*100;cp=cc.groupby(['origen','modelo']).error_pp.mean().unstack();dp=cp.participacion_historica-cp.participacion_ewm
        fig,axes=plt.subplots(2,1,figsize=(10,6))
        for ax,s,label in zip(axes,[dif,dp],['Diferencia de pérdida monetaria (MXN²)','Diferencia de MAE de participación (pp)']):ax.plot(s.index,s.values,marker='o');ax.axhline(0,color='black',linestyle='--');ax.set_ylabel(label,fontsize=8)
        save(19,fig,pd.concat([dif.rename('diferencia_monetaria'),dp.rename('diferencia_pp')],axis=1).reset_index(),'Resultados')
        future=results['pronostico_futuro'];budget=future.pivot(index='horizonte',columns='insumo_id',values='importe').fillna(0)
        order=budget.sum().sort_values(ascending=False).index
        shown=top_with_remainder(budget,7,order)
        fig,ax=plt.subplots(figsize=(11,6));shown.plot.bar(stacked=True,ax=ax,width=.65,colormap='tab20')
        ax.set_ylabel('MXN nominales');ax.set_xlabel('Horizonte desde el corte guardado');ax.tick_params(axis='x',rotation=0)
        ax.legend(readable_labels(shown.columns),loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8,title='Insumos principales')
        save(20,fig,future)
    if controls:
        # F22 resume los invariantes de cierre; no convierte prueba en selección.
        tab=pd.DataFrame(controls);fig,ax=plt.subplots(figsize=(10,4));ax.barh(tab.control,tab.aprobado.astype(int),color='#367d59');ax.set_xlim(0,1.2);ax.set_xticks([0,1],['Falló','Aprobado']);save(22,fig,tab)
    if panel is not None and results is not None:
        # F23: convergencia descriptiva del error acumulado por fold rolling.
        # No pretende demostrar convergencia asintótica con muestras pequeñas.
        pred=results['predicciones'].copy()
        pred=pred.dropna(subset=['real','prediccion']).sort_values(['horizonte','fecha_objetivo','modelo'])
        if not pred.empty:
            pred['error_abs']=(pred['real']-pred['prediccion']).abs()
            pred['fold']=pred.groupby('horizonte')['fecha_objetivo'].rank(method='dense').astype(int)
            pred['mae_acumulado']=pred.groupby(['horizonte','modelo'])['error_abs'].expanding().mean().reset_index(level=[0,1],drop=True)
            fig,axes=plt.subplots(2,2,figsize=(12,7),sharey=False)
            for h,ax in zip(range(1,5),axes.flat):
                g=pred[pred.horizonte.eq(h)]
                for model in ['hibrido','ultimo_valor','promedio_4s','estacional_52s']:
                    q=g[g.modelo.eq(model)]
                    if not q.empty:ax.plot(q.fold,q.mae_acumulado,marker='o',label=model)
                ax.set_title(f'h={h}');ax.set_xlabel('Fold rolling acumulado');ax.set_ylabel('MAE acumulado (MXN)')
                if h==1:ax.legend(fontsize=8)
            save(23,fig,pred[['origen','fecha_objetivo','horizonte','modelo','fold','error_abs','mae_acumulado']],'Resultados')
        # F24: correlación descriptiva; no se interpreta como causalidad.
        corr_frame=panel[['total']].rename(columns={'total':'compras_total_mxn'}).copy()
        if sales is not None and 'importe_nominal' in sales:
            corr_frame['ventas_total_mxn']=pd.to_numeric(sales.importe_nominal,errors='coerce').reindex(corr_frame.index)
        if exog is not None and not exog.empty:
            ex=exog.pivot_table(index='fecha_referencia',columns='variable',values='valor',aggfunc='last')
            ex.index=pd.to_datetime(ex.index);corr_frame=corr_frame.join(ex.reindex(corr_frame.index),how='left')
        # Añadir calendario derivado como variables explicativas observables.
        week=corr_frame.index.isocalendar().week.astype(float).to_numpy()
        corr_frame['semana_sin']=np.sin(2*np.pi*week/52.1775)
        corr_frame['semana_cos']=np.cos(2*np.pi*week/52.1775)
        corr_frame=corr_frame.select_dtypes(include=[np.number]).dropna(axis=1,how='all')
        matrix=corr_frame.corr(min_periods=3)
        if not matrix.empty:
            fig,ax=plt.subplots(figsize=(10,8));im=ax.imshow(matrix.values,vmin=-1,vmax=1,cmap='coolwarm')
            labels=readable_labels(matrix.columns);ax.set_xticks(range(len(labels)),labels,rotation=45,ha='right');ax.set_yticks(range(len(labels)),labels)
            for i in range(len(matrix)):
                for j in range(len(matrix)):
                    value=matrix.iloc[i,j]
                    if pd.notna(value):ax.text(j,i,f'{value:.2f}',ha='center',va='center',fontsize=8)
            fig.colorbar(im,ax=ax,label='Correlación de Pearson');ax.set_title('Relación descriptiva; no implica causalidad',fontsize=10)
            save(24,fig,matrix.rename_axis('variable').reset_index(),'Resultados')
    for number,title in enumerate(TITLES):
        # Cada figura ausente conserva motivo explícito en el manifiesto.
        if number not in generated:
            reason='Sin ejecución empírica aprobada.'
            if number==6:reason='ACF/PACF requiere desarrollo continuo observado; no se comprimen ni imputan huecos.'
            if number==8:reason='STL requiere al menos 156 semanas de desarrollo sin huecos en esta configuración.'
            if number==11:reason='Esta versión usa un conjunto parsimonioso prefijado, sin selección por frecuencia; no se fabrican importancias.'
            if number==21:reason='Captura requiere inspeccionar el HTML de la ejecución en navegador; no se sustituye con una maqueta.'
            if number==23:reason='No hay predicciones observadas suficientes para construir la trayectoria de error rolling.'
            if number==24:reason='No hay al menos una variable numérica con observaciones suficientes para correlacionar.'
            manifest.append(dict(id=f'F{number:02}',titulo=title,estado='omitida',archivo='',datos='',run_id=output.name,capitulo='Desarrollo',motivo=reason,demostracion=demo))
    manifest=sorted(manifest,key=lambda r:r['id'])
    (output/'manifiesto_figuras.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame(manifest).to_csv(output/'manifiesto_figuras.csv',index=False)
    lines=['# Figuras para la tesis','', 'Paquete de demostración: no insertar como evidencia empírica.' if demo else 'Insertar únicamente después de revisar datos y contenido.','']
    for row in manifest:lines.extend([f"## {row['id']} {row['titulo']}",'',f"Estado: {row['estado']}. Capítulo sugerido: {row['capitulo']}.",f"Archivo: {row['archivo']}. Motivo: {row['motivo']}",''])
    (output/'guia_figuras.md').write_text('\n'.join(lines),encoding='utf-8')
    return manifest
