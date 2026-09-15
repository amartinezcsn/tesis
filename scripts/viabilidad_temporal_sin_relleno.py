"""Counts candidate calendar-aligned samples, not approved scientific data."""
from openpyxl import load_workbook
from datetime import datetime,timedelta
from collections import Counter
import json
w=load_workbook('datasets/xlsx/Compras.xlsx',read_only=True,data_only=True)
rows=list(w.active.values)[1:];w.close()
dates=[datetime(2021,5,3)+timedelta(weeks=i) for i in range(165)]
exclude={'COMBUSTIBLE','MUEBLES','HERRAMIENTA'}
ambiguous={'CONSUMIBLES','OTROS','NO DEFINIDO','CASETAS','ADMINISTRACION','HORNEADO'}
counts=Counter()
for r in rows:
    if isinstance(r[1],datetime) and dates[0]<=r[1]<=datetime(2024,6,30) and r[8] not in exclude|ambiguous and isinstance(r[6],(int,float)) and r[6]>0:
        d=r[1].replace(hour=0,minute=0,second=0,microsecond=0)
        counts[d-timedelta(days=d.weekday())]+=1
seen=[counts[d]>0 for d in dates]
out={'advertencia':'Disponibilidad candidata por presencia de registros; no certifica completitud, clasificación ni importes.', 'n':len(dates)}
cut=dates.index(datetime(2024,1,1));out['corte_ilustrativo']='2024-01-01'
out['objetivos_finales_con_registro']=sum(seen[cut:])
out['bloque_final_semanas']=len(dates)-cut
out['por_lookback']={}
for lookback in (4,8,12):
    byh={}
    for h in (1,2,3,4):
        train=[];test=[]
        for origin in range(lookback,len(dates)-h+1):
            target=origin+h-1
            if all(seen[origin-lookback:origin]) and seen[target]:
                (train if target<cut else test).append(origin)
        byh[h]={'pares_previos_al_corte':len(train),'origenes_finales':len([o for o in test if o>=cut])}
    out['por_lookback'][lookback]=byh
out['pares_h1_a_historia_52_completa']=sum(all(seen[o-52:o+1]) for o in range(52,len(dates)))
out['ventana52_calendario_observaciones_antes_corte']=sum(seen[cut-52:cut])
print(json.dumps(out,ensure_ascii=False,indent=2))
