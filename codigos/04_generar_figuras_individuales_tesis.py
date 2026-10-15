"""Paquete de figuras individuales para revisión previa a integrar la tesis."""
from pathlib import Path
import hashlib, json
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'output/run_20261013T193604Z_157556'
OUT=ROOT/'documentacion/figuras_individuales_propuesta_20261015'
ABL={
 'Solo compras':ROOT/'output/run_20261013T194927Z_fe8b96',
 'Compras + ventas':ROOT/'output/run_20261013T195442Z_5fed8f',
 'Compras + calendario':ROOT/'output/run_20261013T195837Z_713fcd',
 'Modelo completo':ROOT/'output/run_20261013T194232Z_d0a239'}
C={'azul':'#0072B2','naranja':'#D55E00','verde':'#009E73','rosa':'#CC79A7','gris':'#666666'}
MAN=[]

def style():
 OUT.mkdir(parents=True,exist_ok=True)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,
  'axes.labelsize':11,'legend.fontsize':10,'figure.titlesize':15,
  'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,
  'grid.alpha':.22,'grid.linewidth':.7})

def save(fig,stem,title,chapter,sources,data=None,note=''):
 fig.tight_layout()
 for ext in ('png','svg'):
  fig.savefig(OUT/f'{stem}.{ext}',dpi=300 if ext=='png' else None,bbox_inches='tight',facecolor='white')
 plt.close(fig)
 if data is not None:data.to_csv(OUT/f'{stem}_datos.csv',index=False)
 item={'id':stem,'titulo':title,'capitulo_sugerido':chapter,'fuentes':'; '.join(sources),'nota':note}
 for ext in ('png','svg'):
  item[f'sha256_{ext}']=hashlib.sha256((OUT/f'{stem}.{ext}').read_bytes()).hexdigest()
 MAN.append(item)

def process_flow():
 fig,ax=plt.subplots(figsize=(11,4.6));ax.axis('off')
 labels=['Fuentes\nauditadas','Cobertura y\ncatálogo','Panel semanal\ncon huecos','Selección\ninterna','Pronóstico\ndel total','Composición y\nasignación']
 xs=np.linspace(.075,.925,len(labels))
 for i,(x,label) in enumerate(zip(xs,labels)):
  box=patches.FancyBboxPatch((x-.07,.42),.14,.25,boxstyle='round,pad=.012',
   fc='#EAF2F8' if i<4 else '#D6EAF8',ec='#356A8A',lw=1.4,transform=ax.transAxes)
  ax.add_patch(box);ax.text(x,.545,label,ha='center',va='center',transform=ax.transAxes,
   weight='bold' if i>=3 else 'normal')
  if i<len(labels)-1:ax.annotate('',xy=(xs[i+1]-.075,.545),xytext=(x+.075,.545),
   xycoords=ax.transAxes,arrowprops=dict(arrowstyle='->',color='#356A8A',lw=1.5))
 ax.text(.5,.22,'La evaluación final permanece separada de la selección de modelos y categorías.',
  ha='center',transform=ax.transAxes,color=C['gris'])
 ax.set_title('Flujo reproducible del sistema híbrido',pad=14)
 save(fig,'I01_flujo_proceso','Flujo reproducible del sistema híbrido','Metodología',
  ['configuración y manifiesto de la corrida'],note='Diagrama metodológico; no representa magnitudes.')

def validation_timeline():
 d=pd.read_csv(RUN/'particiones.csv',parse_dates=['origen','fecha_objetivo'])
 q=d[d.etapa.eq('evaluacion')]
 fig,ax=plt.subplots(figsize=(10.5,5.2))
 markers={1:'o',2:'s',3:'^',4:'D'}
 for h,g in q.groupby('horizonte'):
  ax.scatter(g.fecha_objetivo,[h]*len(g),s=46,marker=markers[h],label=f'H{h}')
 for origin in sorted(q.origen.unique()):ax.axvline(origin,color='#B8B8B8',lw=.5,alpha=.3)
 ax.set_yticks([1,2,3,4],['H1','H2','H3','H4']);ax.set_ylabel('Horizonte')
 ax.set_xlabel('Fecha objetivo');ax.set_title('Evaluación rolling-origin con paso semanal y 17 orígenes')
 ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
 ax.legend(frameon=False,ncol=4)
 save(fig,'I02_validacion_temporal','Evaluación rolling-origin con paso semanal y 17 orígenes',
  'Metodología',['particiones.csv'],q)

def coverage_state():
 d=pd.read_csv(RUN/'cobertura.csv',parse_dates=['semana_inicio'])
 states=['observada','cero_confirmado','incierta','incompleta','desconocida']
 pal={'observada':'#56B4E9','cero_confirmado':'#009E73','incierta':'#E69F00','incompleta':'#F0E442','desconocida':'#999999'}
 fig,ax=plt.subplots(figsize=(11,3.8))
 for state in states:
  x=d.loc[d.estado.eq(state),'semana_inicio'];ax.scatter(x,np.zeros(len(x)),marker='s',s=26,color=pal[state],label=state)
 ax.set_yticks([]);ax.set_xlabel('Semana de inicio');ax.set_title('Estado documentado de la cobertura semanal')
 ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
 ax.legend(frameon=False,ncol=3,loc='upper center')
 save(fig,'I03_cobertura_semanal','Estado documentado de la cobertura semanal','Desarrollo',['cobertura.csv'],d)

def weekly_series():
 d=pd.read_csv(RUN/'panel_semanal.csv',parse_dates=['semana_inicio'])
 fig,ax=plt.subplots(figsize=(11,5.4));obs=d.total.notna()
 ax.plot(d.semana_inicio,d.total.where(obs),color=C['azul'],lw=1.35,label='Importe observado')
 z=obs&d.total.eq(0);ax.scatter(d.loc[z,'semana_inicio'],d.loc[z,'total'],s=16,color=C['naranja'],label='Cero elegible observado')
 ax.set_ylabel('Importe elegible semanal (MXN nominales)');ax.set_xlabel('Semana de inicio')
 ax.set_title('Serie semanal del gasto elegible conservando huecos de captura');ax.legend(frameon=False)
 ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
 save(fig,'I04_serie_semanal','Serie semanal del gasto elegible conservando huecos de captura','Desarrollo',['panel_semanal.csv'],d[['semana_inicio','total']])

def category_data():
 panel=pd.read_csv(RUN/'panel_semanal.csv',parse_dates=['semana_inicio']).set_index('semana_inicio')
 sel=json.loads((RUN/'seleccion.json').read_text(encoding='utf-8'));cut=pd.Timestamp(sel['corte_desarrollo'])
 sums=panel.loc[panel.index<cut].drop(columns='total').sum().sort_values(ascending=False);sums=sums[sums.gt(0)]
 cum=sums.cumsum()/sums.sum()*100
 return panel,sel,cut,sums,cum

def pareto():
 panel,sel,cut,sums,cum=category_data();top=sums.head(15);chosen=set(sel['categorias'])
 fig,ax=plt.subplots(figsize=(11,5.8));x=np.arange(len(top))
 ax.bar(x,top.values,color=[C['azul'] if k in chosen else '#AAB7B8' for k in top.index])
 ax.set_xticks(x,top.index,rotation=38,ha='right');ax.set_ylabel('Importe acumulado (MXN)')
 ax.set_title('Pareto de categorías calculado en el conjunto de desarrollo')
 ax2=ax.twinx();ax2.grid(False);ax2.plot(x,cum.loc[top.index],color=C['naranja'],marker='o',lw=1.6)
 ax2.axhline(80,color=C['gris'],ls='--',lw=1);ax2.set_ylabel('Participación acumulada (%)')
 out=pd.DataFrame({'categoria':sums.index,'importe':sums.values,'participacion_acumulada_pct':cum.values,'seleccionada':sums.index.isin(chosen)})
 save(fig,'I05_pareto_categorias','Pareto de categorías calculado en el conjunto de desarrollo','Desarrollo',['panel_semanal.csv','seleccion.json'],out)

def composition_heatmap():
 panel,sel,cut,_,_=category_data();cats=sel['categorias']
 pos=panel.loc[(panel.index<cut)&panel.total.gt(0),cats];sh=pos.div(panel.loc[pos.index,'total'],axis=0)*100;recent=sh.tail(60).T
 fig,ax=plt.subplots(figsize=(11,5.8));v=max(10,np.nanpercentile(recent.values,95))
 im=ax.imshow(recent,aspect='auto',interpolation='nearest',cmap='Blues',vmin=0,vmax=v)
 ax.set_yticks(range(len(recent.index)),recent.index);ticks=np.linspace(0,len(recent.columns)-1,7).astype(int)
 ax.set_xticks(ticks,[recent.columns[i].strftime('%Y-%m-%d') for i in ticks],rotation=28,ha='right')
 ax.set_xlabel('Semana');ax.set_ylabel('Categoría');ax.set_title('Participación observada en las últimas 60 semanas con total positivo')
 fig.colorbar(im,ax=ax,label='Participación del total semanal (%)',fraction=.03,pad=.02)
 save(fig,'I06_mapa_composicion','Participación observada en las últimas 60 semanas con total positivo','Desarrollo',['panel_semanal.csv','seleccion.json'],recent.T.reset_index())

def predictions():
 d=pd.read_csv(RUN/'predicciones.csv',parse_dates=['fecha_objetivo']);q=d[(d.horizonte.eq(1))&d.modelo.isin(['hibrido','ultimo_valor'])]
 w=q.pivot(index='fecha_objetivo',columns='modelo',values='prediccion');real=q.groupby('fecha_objetivo').real.first()
 fig,ax=plt.subplots(figsize=(11,5.5));ax.plot(real.index,real,color='black',marker='o',lw=1.6,label='Observado')
 ax.plot(w.index,w.hibrido,color=C['azul'],marker='s',lw=1.5,label='Híbrido')
 ax.plot(w.index,w.ultimo_valor,color=C['naranja'],marker='^',ls='--',lw=1.4,label='Último valor')
 ax.set_ylabel('Importe semanal (MXN nominales)');ax.set_xlabel('Fecha objetivo');ax.set_title('Pronóstico fuera de muestra en el horizonte principal')
 ax.legend(frameon=False,ncol=3);ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
 save(fig,'I07_observado_pronosticado','Pronóstico fuera de muestra en el horizonte principal','Resultados',['predicciones.csv'],w.join(real.rename('real')).reset_index())

def monetary_metric(metric):
 d=pd.read_csv(RUN/'metricas.csv');mods=['hibrido','ultimo_valor','ss_arima111','nn_residual__ss_arima111']
 lab={'hibrido':'Híbrido','ultimo_valor':'Último valor','ss_arima111':'Estado espacial ARIMA','nn_residual__ss_arima111':'Red residual'}
 pal=[C['azul'],C['naranja'],C['verde'],C['rosa']];q=d[d.modelo.isin(mods)&d.comparacion.eq('principal_fechas_comunes')]
 fig,ax=plt.subplots(figsize=(9.2,5.6));x=np.arange(1,5);width=.19
 for j,m in enumerate(mods):
  z=q[q.modelo.eq(m)].set_index('horizonte')[metric].reindex(x);ax.bar(x+(j-1.5)*width,z,width,color=pal[j],label=lab[m])
 ax.set_xticks(x,[f'H{i}' for i in x]);ax.set_xlabel('Horizonte semanal');ax.set_ylabel(f'{metric.upper()} (MXN)')
 ax.set_title(f'{metric.upper()} por modelo y horizonte');ax.legend(frameon=False,ncol=2)
 save(fig,f'I0{8 if metric=="rmse" else 9}_{metric}',f'{metric.upper()} por modelo y horizonte','Resultados',['metricas.csv'],q[['horizonte','modelo',metric,'n']])

def composition_metrics():
 d=pd.read_csv(RUN/'metricas_composicion.csv');h1=d[(d.horizonte.eq(1))&~d.insumo_id.eq('PROMEDIO_MACRO')]
 cats=h1.groupby('insumo_id').mae_pp.mean().sort_values().index;y=np.arange(len(cats));height=.36
 fig,ax=plt.subplots(figsize=(9.5,6.2))
 for off,m,color,label in [(-height/2,'participacion_historica',C['naranja'],'Histórica'),(height/2,'participacion_ewm',C['azul'],'EWM')]:
  q=h1[h1.modelo.eq(m)].set_index('insumo_id').reindex(cats);ax.barh(y+off,q.mae_pp,height,color=color,label=label)
 ax.set_yticks(y,cats);ax.set_xlabel('MAE (puntos porcentuales)');ax.set_title('Error de composición por categoría en H1');ax.legend(frameon=False)
 save(fig,'I10_error_composicion_categoria','Error de composición por categoría en H1','Resultados',['metricas_composicion.csv'],h1)
 macro=d[d.insumo_id.eq('PROMEDIO_MACRO')];fig,ax=plt.subplots(figsize=(8.5,5.4))
 for m,color,label,mark in [('participacion_historica',C['naranja'],'Histórica','^'),('participacion_ewm',C['azul'],'EWM','o')]:
  q=macro[macro.modelo.eq(m)].sort_values('horizonte');ax.plot(q.horizonte,q.mae_pp,color=color,marker=mark,lw=1.7,label=label)
 ax.set_xticks([1,2,3,4],['H1','H2','H3','H4']);ax.set_xlabel('Horizonte semanal');ax.set_ylabel('MAE macro (puntos porcentuales)')
 ax.set_title('Error macro de composición por horizonte');ax.legend(frameon=False)
 save(fig,'I11_error_composicion_macro','Error macro de composición por horizonte','Resultados',['metricas_composicion.csv'],macro)

def hypothesis():
 pred=pd.read_csv(RUN/'predicciones.csv',parse_dates=['fecha_objetivo']);p=pred[(pred.horizonte.eq(1))&pred.modelo.isin(['hibrido','ultimo_valor'])]
 w=p.pivot(index='fecha_objetivo',columns='modelo',values=['real','prediccion']);real=w['real'].hibrido
 money=(real-w['prediccion'].ultimo_valor)**2-(real-w['prediccion'].hibrido)**2
 hyp=json.loads((RUN/'hipotesis.json').read_text(encoding='utf-8'))
 fig,ax=plt.subplots(figsize=(11,5.4));ax.axhline(0,color='black',lw=.8);ax.plot(money.index,money,marker='o',color=C['azul'],lw=1.2)
 ax.axhline(hyp['importe']['media'],color=C['naranja'],ls='--',label='Media pareada')
 ax.set_ylabel('Diferencia de error cuadrático (MXN²)');ax.set_xlabel('Fecha objetivo');ax.set_title('Contraste H1 del componente monetario')
 ax.text(.01,.03,'Positivo favorece al híbrido; negativo favorece a último valor.',transform=ax.transAxes,color=C['gris']);ax.legend(frameon=False)
 save(fig,'I12_H1_monetario','Contraste H1 del componente monetario','Resultados',['predicciones.csv','hipotesis.json'],money.rename('diferencia_monetaria_mxn2').reset_index())
 comp=pd.read_csv(RUN/'composicion.csv',parse_dates=['fecha_objetivo']);c=comp[(comp.horizonte.eq(1))&comp.modelo.isin(['participacion_historica','participacion_ewm'])].copy()
 c['ae_pp']=(c.real-c.prediccion).abs()*100;cm=c.groupby(['fecha_objetivo','modelo']).ae_pp.mean().unstack();diff=cm.participacion_historica-cm.participacion_ewm
 fig,ax=plt.subplots(figsize=(10,5.3));ax.axhline(0,color='black',lw=.8);ax.plot(diff.index,diff,marker='s',color=C['verde'],lw=1.2)
 ax.axhline(hyp['composicion']['media'],color=C['naranja'],ls='--',label='Media pareada')
 ax.set_ylabel('Diferencia de MAE (puntos porcentuales)');ax.set_xlabel('Fecha objetivo');ax.set_title('Contraste H1 del componente de composición')
 ax.text(.01,.03,'Positivo favorece EWM; n=9, muestra insuficiente para inferencia.',transform=ax.transAxes,color=C['gris']);ax.legend(frameon=False)
 save(fig,'I13_H1_composicion','Contraste H1 del componente de composición','Resultados',['composicion.csv','hipotesis.json'],diff.rename('diferencia_composicion_pp').reset_index())

def ablations():
 rows=[]
 for name,path in ABL.items():
  d=pd.read_csv(path/'metricas.csv');d=d[d.modelo.eq('hibrido')&d.comparacion.eq('principal_fechas_comunes')]
  rows += [{'escenario':name,'horizonte':r.horizonte,'rmse':r.rmse} for _,r in d.iterrows()]
 data=pd.DataFrame(rows);base=data[data.escenario.eq('Solo compras')].set_index('horizonte').rmse
 data['delta']=data.apply(lambda r:r.rmse-base.loc[r.horizonte],axis=1)
 fig,ax=plt.subplots(figsize=(9.5,5.5));ax.axhline(0,color='black',lw=.8)
 specs=[('Compras + ventas','#56B4E9','s'),('Compras + calendario',C['verde'],'^'),('Modelo completo',C['azul'],'D')]
 for name,color,mark in specs:
  q=data[data.escenario.eq(name)];ax.plot(q.horizonte,q.delta,color=color,marker=mark,lw=1.7,label=name)
 ax.set_xticks([1,2,3,4],['H1','H2','H3','H4']);ax.set_xlabel('Horizonte semanal');ax.set_ylabel('Cambio de RMSE frente a solo compras (MXN)')
 ax.set_title('Ablación de ventas y variables de calendario');ax.text(.01,.03,'Valores negativos indican menor error.',transform=ax.transAxes,color=C['gris']);ax.legend(frameon=False)
 save(fig,'I14_ablaciones','Ablación de ventas y variables de calendario','Discusión',[p.name+'/metricas.csv' for p in ABL.values()],data)

def budgets():
 f=pd.read_csv(RUN/'pronostico_futuro.csv');a=pd.read_csv(RUN/'pronostico_4_semanas.csv').sort_values('importe_4_semanas')
 piv=f.pivot(index='horizonte',columns='insumo_id',values='importe').fillna(0);order=a.sort_values('importe_4_semanas',ascending=False).insumo_id.tolist();piv=piv.reindex(columns=order)
 fig,ax=plt.subplots(figsize=(9.2,6));bottom=np.zeros(len(piv));cmap=plt.get_cmap('tab20')
 for i,col in enumerate(piv.columns):ax.bar(piv.index,piv[col],bottom=bottom,label=col,color=cmap(i%20));bottom+=piv[col].values
 ax.set_xticks([1,2,3,4],['H1','H2','H3','H4']);ax.set_xlabel('Semana futura');ax.set_ylabel('Importe asignado (MXN)');ax.set_title('Asignación presupuestaria por semana futura')
 ax.legend(frameon=False,ncol=2,bbox_to_anchor=(1.02,1),loc='upper left')
 save(fig,'I15_presupuesto_semanal','Asignación presupuestaria por semana futura','Resultados',['pronostico_futuro.csv'],f)
 fig,ax=plt.subplots(figsize=(9,6));ax.barh(np.arange(len(a)),a.importe_4_semanas,color=C['azul']);ax.set_yticks(np.arange(len(a)),a.insumo_id)
 ax.set_xlabel('Importe de cuatro semanas (MXN)');ax.set_title('Presupuesto agregado de cuatro semanas por categoría')
 for i,v in enumerate(a.importe_4_semanas):ax.text(v+8,i,f'${v:,.2f}',va='center',fontsize=9)
 save(fig,'I16_presupuesto_agregado','Presupuesto agregado de cuatro semanas por categoría','Resultados',['pronostico_4_semanas.csv'],a)

def main():
 style();process_flow();validation_timeline();coverage_state();weekly_series();pareto();composition_heatmap();predictions();monetary_metric('rmse');monetary_metric('mae');composition_metrics();hypothesis();ablations();budgets()
 pd.DataFrame(MAN).to_csv(OUT/'manifiesto_figuras.csv',index=False)
 (OUT/'manifiesto_figuras.json').write_text(json.dumps(MAN,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'{len(MAN)} figuras guardadas en {OUT}')
if __name__=='__main__':main()
