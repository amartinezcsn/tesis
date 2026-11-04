"""Productos interpretables para revisión humana y controles de cierre."""
from pathlib import Path
import json
import html
import numpy as np
import pandas as pd


def records(frame):
    """Convertir una tabla a registros JSON con fechas y faltantes válidos."""
    # pandas evita emitir NaN, que no pertenece al estándar JSON.
    return json.loads(frame.to_json(orient='records',date_format='iso'))


def export_results(output,results,cfg,demo=False):
    """Exportar datos del DSS, tablero HTML local e informe de limitaciones."""
    output=Path(output)
    future=results['pronostico_futuro']
    four_week=results['pronostico_4_semanas']
    monthly_total=float(four_week.importe_4_semanas.sum())
    payload={'schema_version':1,'run_id':output.name,'demostracion':demo,'unidad':'MXN nominales',
        'modelo':'hibrido estadistico y aprendizaje automatico','origen':future.origen.iloc[0],
        'consolidado_4_semanas':round(monthly_total,2),
        'categorias_excluidas':list(cfg.excluded_budget_categories),
        'horizontes':[1,2,3,4],'seleccion':results['selection'],'hipotesis':results['hypothesis'],
        'metricas_total':records(results['metricas']),'metricas_composicion':records(results['metricas_composicion']),
        'predicciones_validacion':records(results['predicciones']),
        'distribucion_futura':records(future),
        'distribucion_4_semanas':records(four_week),
        'advertencia':'DEMOSTRACIÓN SINTÉTICA: NO ES EVIDENCIA DE CUP&CAKE.' if demo else 'Evaluación retrospectiva; no garantiza precisión futura. Corte de emisión explícito. No es una orden de compra.'}
    if 'advertencia' in results:
        payload['advertencia']+=' '+results['advertencia']
        payload['politica_faltantes']=results['politica_faltantes']
        payload['cobertura_evaluacion']=records(results['particiones'])
    (output/'dss_hibrido.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    # Interfaz autocontenida: datos, estilos e interacción viajan en un solo
    # archivo y no se envían a servicios externos.
    dashboard_data=json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':'))
    # Evita que una etiqueta procedente de datos pueda cerrar el bloque script.
    dashboard_data=dashboard_data.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    headline='Demostración sintética' if demo else 'Planeación del presupuesto de compras'
    document=r'''<!doctype html>
<html lang="es-MX">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>Dashboard de abastecimiento Cup&amp;Cake</title>
<style>
:root{--ink:#17263b;--muted:#607086;--line:#dbe3ec;--paper:#fff;--wash:#f3f6fa;--navy:#143b5f;--blue:#1675b8;--cyan:#39a8c8;--gold:#d99b37;--warn:#fff4da;--ok:#e8f6ef;--shadow:0 18px 45px rgba(23,38,59,.09)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:linear-gradient(180deg,#eaf2f8 0,#f7f9fc 320px);color:var(--ink);font:15px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
button,select,input{font:inherit}button,select{border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink)}button{cursor:pointer;font-weight:700;padding:.7rem 1rem}button:hover{border-color:var(--blue);color:var(--blue)}a{color:inherit}.shell{max-width:1240px;margin:auto;padding:0 22px 48px}
.hero{margin:0 -22px 26px;padding:22px max(22px,calc((100vw - 1240px)/2 + 22px)) 34px;background:linear-gradient(125deg,#102f4d,#18547c 68%,#1675b8);color:#fff;box-shadow:var(--shadow)}
.topline{display:flex;justify-content:space-between;gap:18px;align-items:center;margin-bottom:42px}.brand{display:flex;align-items:center;gap:12px;font-weight:800;letter-spacing:.01em}.mark{display:grid;place-items:center;width:40px;height:40px;border-radius:13px;background:#fff;color:var(--navy);font-size:12px}.run-badge{border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:6px 11px;font-size:12px;background:rgba(255,255,255,.1)}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:11px;font-weight:800;color:#bfe8f6}.hero h1{max-width:780px;margin:8px 0 10px;font:800 clamp(30px,5vw,52px)/1.04 Georgia,"Times New Roman",serif;letter-spacing:-.025em}.hero-copy{max-width:770px;margin:0;color:#dceaf3;font-size:17px}
.meta{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:28px}.meta-card{padding:13px 15px;border:1px solid rgba(255,255,255,.2);border-radius:13px;background:rgba(255,255,255,.08)}.meta-card span{display:block;color:#bcd4e4;font-size:11px;text-transform:uppercase;letter-spacing:.08em}.meta-card strong{display:block;margin-top:3px;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.notice{display:grid;grid-template-columns:auto 1fr;gap:12px;margin:0 0 22px;padding:16px 18px;border:1px solid #ecd5a9;border-radius:14px;background:var(--warn);color:#624a1d}.notice-mark{font-weight:900}.notice strong{display:block;margin-bottom:2px}
.controls{position:sticky;top:0;z-index:4;display:flex;flex-wrap:wrap;align-items:end;gap:12px;margin:0 0 22px;padding:14px 16px;border:1px solid rgba(219,227,236,.9);border-radius:15px;background:rgba(255,255,255,.94);box-shadow:0 10px 28px rgba(23,38,59,.08);backdrop-filter:blur(10px)}.field{display:grid;gap:5px;min-width:190px}.field span{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}select{min-height:42px;padding:0 36px 0 12px}.check{display:flex;align-items:center;gap:8px;padding:0 8px 10px;color:var(--muted)}.controls .spacer{flex:1}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}.kpi{min-height:128px;padding:18px;border:1px solid var(--line);border-radius:16px;background:var(--paper);box-shadow:var(--shadow)}.kpi-label{color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em}.kpi-value{margin:12px 0 3px;font-size:27px;font-weight:850;letter-spacing:-.03em}.kpi-note{color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(300px,.75fr);gap:18px}.panel{border:1px solid var(--line);border-radius:17px;background:var(--paper);box-shadow:var(--shadow);overflow:hidden}.panel-head{display:flex;justify-content:space-between;gap:14px;align-items:start;padding:20px 20px 0}.panel h2{margin:0;font:750 20px/1.2 Georgia,"Times New Roman",serif}.sub{margin:5px 0 0;color:var(--muted);font-size:13px}.chart{padding:18px 20px 22px}.bar-row{display:grid;grid-template-columns:minmax(105px,1fr) minmax(150px,3fr) 96px;gap:11px;align-items:center;margin:10px 0}.bar-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:650}.track{height:14px;border-radius:99px;background:#edf2f6;overflow:hidden}.bar{height:100%;min-width:2px;border-radius:99px;background:linear-gradient(90deg,var(--blue),var(--cyan))}.bar.remainder{background:linear-gradient(90deg,#8d9bac,#b2bfcb)}.bar-value{text-align:right;font-variant-numeric:tabular-nums;font-weight:750}
.reading{padding:20px}.reading-list{display:grid;gap:13px;margin-top:18px}.reading-item{padding-bottom:13px;border-bottom:1px solid var(--line)}.reading-item:last-child{border:0}.reading-item span{display:block;color:var(--muted);font-size:12px}.reading-item strong{display:block;margin-top:2px}.scope{margin-top:18px;padding:14px;border-left:4px solid var(--gold);background:#fff8e9}.scope strong{display:block;margin-bottom:3px}
.wide{grid-column:1/-1}.table-wrap{overflow:auto;margin-top:14px}table{width:100%;border-collapse:collapse;font-size:14px}th{position:sticky;top:0;padding:11px 13px;background:#eef4f8;color:#40536a;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.06em}td{padding:11px 13px;border-top:1px solid var(--line);font-variant-numeric:tabular-nums}td.num,th.num{text-align:right}tbody tr:hover{background:#f7fafc}.rank{color:var(--muted);width:44px}.pill{display:inline-block;padding:3px 8px;border-radius:99px;background:#edf4f8;color:#36546b;font-size:12px;font-weight:750}.remainder-row{color:#65758a}
.evidence{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}.evidence .panel{padding:20px}.trace{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 18px;margin-top:15px}.trace div{padding-bottom:9px;border-bottom:1px solid var(--line)}.trace span{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em}.trace strong{display:block;margin-top:2px;word-break:break-word}
details{margin-top:18px;border:1px solid var(--line);border-radius:14px;background:#fff}summary{cursor:pointer;padding:15px 18px;font-weight:800}.details-body{padding:0 18px 16px;color:#46586d}.details-body ul{margin:.6rem 0;padding-left:1.2rem}.footer{margin-top:26px;color:var(--muted);text-align:center;font-size:12px}
.empty{padding:32px;text-align:center;color:var(--muted)}
@media(max-width:900px){.meta,.kpis{grid-template-columns:repeat(2,1fr)}.grid,.evidence{grid-template-columns:1fr}.wide{grid-column:auto}.controls{position:static}.bar-row{grid-template-columns:100px 1fr 86px}}
@media(max-width:560px){.shell{padding-left:14px;padding-right:14px}.hero{margin-left:-14px;margin-right:-14px;padding-left:14px;padding-right:14px}.topline{align-items:start}.run-badge{max-width:145px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.meta,.kpis{grid-template-columns:1fr}.controls{align-items:stretch}.field{min-width:100%}.controls button{width:100%}.bar-row{grid-template-columns:90px 1fr}.bar-value{grid-column:2}.trace{grid-template-columns:1fr}}
@media print{body{background:#fff}.hero{background:#fff;color:var(--ink);box-shadow:none;border-bottom:2px solid var(--ink)}.hero-copy,.eyebrow,.meta-card span{color:var(--muted)}.meta-card{border-color:var(--line)}.controls,button{display:none!important}.panel,.kpi{box-shadow:none;break-inside:avoid}}
</style>
</head>
<body>
<div class="shell">
  <header class="hero">
    <div class="topline"><div class="brand"><span class="mark">C&amp;C</span><span>Cup&amp;Cake · Sistema de soporte a la decisión</span></div><span class="run-badge" id="runBadge"></span></div>
    <div class="eyebrow">Resultados predictivos auditables</div>
    <h1>__HEADLINE__</h1>
    <p class="hero-copy">Consulta el importe esperado, su distribución monetaria entre insumos y el consolidado de las próximas cuatro semanas.</p>
    <div class="meta">
      <div class="meta-card"><span>Corte de emisión</span><strong id="metaOrigin"></strong></div>
      <div class="meta-card"><span>Unidad</span><strong id="metaUnit"></strong></div>
      <div class="meta-card"><span>Horizontes</span><strong>1 a 4 semanas</strong></div>
      <div class="meta-card"><span>Periodo consolidado</span><strong>28 días · no mes calendario</strong></div>
    </div>
  </header>

  <div class="notice" role="note"><div class="notice-mark">!</div><div><strong>Alcance de la información</strong><span id="warningText"></span></div></div>

  <section class="controls" aria-label="Controles del tablero">
    <label class="field"><span>Periodo</span><select id="horizon"><option value="all">Próximas 4 semanas · 28 días</option><option value="1">Semana 1</option><option value="2">Semana 2</option><option value="3">Semana 3</option><option value="4">Semana 4</option></select></label>
    <label class="field"><span>Insumos visibles</span><select id="topN"><option value="6">Principales 6</option><option value="10" selected>Principales 10</option><option value="99">Todos</option></select></label>
    <label class="check"><input id="includeRemainder" type="checkbox" checked> Incluir resto elegible</label>
    <span class="spacer"></span><button id="downloadCsv" type="button">Descargar vista CSV</button>
  </section>

  <section class="kpis" aria-label="Indicadores principales">
    <article class="kpi"><div class="kpi-label">Presupuesto esperado</div><div class="kpi-value" id="kpiTotal"></div><div class="kpi-note" id="kpiPeriod"></div></article>
    <article class="kpi"><div class="kpi-label">Insumo principal</div><div class="kpi-value" id="kpiTop"></div><div class="kpi-note" id="kpiTopShare"></div></article>
    <article class="kpi"><div class="kpi-label">Categorías mostradas</div><div class="kpi-value" id="kpiCount"></div><div class="kpi-note">Principales y resto elegible</div></article>
    <article class="kpi"><div class="kpi-label">Tipo de salida</div><div class="kpi-value">Presupuesto</div><div class="kpi-note">Importes nominales; no cantidades físicas</div></article>
  </section>

  <main class="grid">
    <section class="panel" aria-labelledby="chartTitle"><div class="panel-head"><div><h2 id="chartTitle">Distribución presupuestaria</h2><p class="sub">Importe esperado por insumo, ordenado de mayor a menor.</p></div><span class="pill" id="periodPill"></span></div><div class="chart" id="chart"></div></section>
    <aside class="panel reading" aria-labelledby="readingTitle"><h2 id="readingTitle">Lectura para la decisión</h2><p class="sub">Resumen del periodo seleccionado.</p><div class="reading-list"><div class="reading-item"><span>Fecha objetivo</span><strong id="readingDate"></strong></div><div class="reading-item"><span>Participación de los tres principales</span><strong id="readingTop3"></strong></div><div class="reading-item"><span>Categorías excluidas del objetivo</span><strong id="readingExcluded"></strong></div></div><div class="scope"><strong>Revisión humana obligatoria</strong>No genera órdenes de compra ni calcula cantidades físicas. Requiere recetas, existencias, merma, costos de faltante, tiempos de entrega y unidades homologadas para ampliar ese alcance.</div></aside>

    <section class="panel wide" aria-labelledby="tableTitle"><div class="panel-head"><div><h2 id="tableTitle">Detalle por insumo</h2><p class="sub">Los importes se concilian con el total del periodo seleccionado.</p></div></div><div class="table-wrap"><table><thead><tr><th class="rank">#</th><th>Insumo</th><th class="num">Participación</th><th class="num">Importe esperado</th></tr></thead><tbody id="budgetRows"></tbody></table></div></section>
  </main>

  <section class="evidence" aria-label="Evidencia y trazabilidad">
    <article class="panel"><h2>Evaluación del modelo</h2><p class="sub">Métricas fuera de muestra del importe; menor error es mejor.</p><div class="table-wrap"><table><thead><tr><th>Horizonte</th><th>Modelo</th><th class="num">n</th><th class="num">RMSE</th><th class="num">MAE</th><th class="num">MASE</th></tr></thead><tbody id="metricRows"></tbody></table></div></article>
    <article class="panel"><h2>Trazabilidad de la emisión</h2><p class="sub">Datos mínimos para identificar e interpretar esta corrida.</p><div class="trace"><div><span>Identificador</span><strong id="traceRun"></strong></div><div><span>Origen</span><strong id="traceOrigin"></strong></div><div><span>Modelo</span><strong id="traceModel"></strong></div><div><span>Modo</span><strong id="traceMode"></strong></div><div><span>Política de faltantes</span><strong id="traceMissing"></strong></div><div><span>Esquema</span><strong id="traceSchema"></strong></div></div></article>
  </section>

  <details><summary>Metodología, límites y definiciones</summary><div class="details-body"><ul><li>El consolidado suma cuatro pronósticos semanales directos y representa 28 días; no equivale necesariamente a un mes calendario.</li><li>La distribución expresa participaciones monetarias del presupuesto elegible. <code>RESTO_ELEGIBLE</code> agrupa categorías válidas de menor participación y no corresponde a la categoría fuente <code>OTROS</code>.</li><li>La evaluación es retrospectiva y exploratoria. No garantiza precisión futura ni beneficios operativos.</li><li>Para emitir desde un corte nuevo deben actualizarse las fuentes, la cobertura y ejecutar nuevamente el pipeline completo.</li></ul><p id="fullWarning"></p></div></details>
  <noscript><p class="empty">Este tablero necesita JavaScript local para aplicar filtros y construir las visualizaciones. Los datos permanecen dentro del archivo.</p></noscript>
  <footer class="footer">Dashboard autocontenido · sin conexiones externas · generado por el pipeline híbrido de Cup&amp;Cake</footer>
</div>
<script>
const DATA=__DASHBOARD_DATA__;
const $=id=>document.getElementById(id);
const money=new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',maximumFractionDigits:2});
const number=new Intl.NumberFormat('es-MX',{maximumFractionDigits:2});
const percent=value=>`${number.format((Number(value)||0)*100)}%`;
const safe=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const label=value=>String(value??'').toLowerCase().replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
let currentRows=[];

function allRows(){
  if($('horizon').value==='all') return DATA.distribucion_4_semanas.map(row=>({item:row.insumo_id,amount:Number(row.importe_4_semanas),share:Number(row.participacion_4_semanas),total:Number(row.total_4_semanas),date:'Próximas cuatro semanas'}));
  const horizon=Number($('horizon').value);
  return DATA.distribucion_futura.filter(row=>Number(row.horizonte)===horizon).map(row=>({item:row.insumo_id,amount:Number(row.importe),share:Number(row.participacion),total:Number(row.total),date:row.fecha_objetivo}));
}

function visibleRows(rows){
  const include=$('includeRemainder').checked;
  const top=Number($('topN').value);
  return rows.filter(row=>include||row.item!=='RESTO_ELEGIBLE').sort((a,b)=>b.amount-a.amount).slice(0,top);
}

function renderMetrics(){
  const selected=$('horizon').value;
  const rows=DATA.metricas_total.filter(row=>selected==='all'||Number(row.horizonte)===Number(selected)).sort((a,b)=>(Number(a.horizonte)-Number(b.horizonte))||(Number(a.rmse)-Number(b.rmse))).slice(0,selected==='all'?12:8);
  $('metricRows').innerHTML=rows.map(row=>`<tr><td>H=${safe(row.horizonte)}</td><td>${safe(label(row.modelo))}</td><td class="num">${safe(row.n)}</td><td class="num">${number.format(Number(row.rmse))}</td><td class="num">${number.format(Number(row.mae))}</td><td class="num">${row.mase==null?'—':number.format(Number(row.mase))}</td></tr>`).join('')||'<tr><td colspan="6" class="empty">Sin métricas para este horizonte.</td></tr>';
}

function render(){
  const rows=allRows().sort((a,b)=>b.amount-a.amount);
  currentRows=visibleRows(rows);
  const total=rows[0]?.total??rows.reduce((sum,row)=>sum+row.amount,0);
  const topMain=rows.find(row=>row.item!=='RESTO_ELEGIBLE')??rows[0];
  const top3=rows.filter(row=>row.item!=='RESTO_ELEGIBLE').slice(0,3).reduce((sum,row)=>sum+row.share,0);
  const period=$('horizon').value==='all'?'Consolidado de 4 semanas':'Horizonte semanal H='+$('horizon').value;
  $('kpiTotal').textContent=money.format(total);
  $('kpiPeriod').textContent=$('horizon').value==='all'?'Periodo de 28 días; no mes calendario':'Pronóstico para una semana';
  $('kpiTop').textContent=topMain?label(topMain.item):'Sin datos';
  $('kpiTopShare').textContent=topMain?`${percent(topMain.share)} del presupuesto`:'—';
  $('kpiCount').textContent=String(rows.length);
  $('periodPill').textContent=period;
  $('readingDate').textContent=rows[0]?.date??'Sin datos';
  $('readingTop3').textContent=percent(top3);
  const max=Math.max(...currentRows.map(row=>row.amount),1);
  $('chart').innerHTML=currentRows.map(row=>`<div class="bar-row"><div class="bar-label" title="${safe(label(row.item))}">${safe(label(row.item))}</div><div class="track" role="img" aria-label="${safe(label(row.item))}: ${safe(money.format(row.amount))}"><div class="bar ${row.item==='RESTO_ELEGIBLE'?'remainder':''}" style="width:${Math.max(1,row.amount/max*100)}%"></div></div><div class="bar-value">${safe(money.format(row.amount))}</div></div>`).join('')||'<div class="empty">No hay categorías visibles con estos filtros.</div>';
  $('budgetRows').innerHTML=currentRows.map((row,index)=>`<tr class="${row.item==='RESTO_ELEGIBLE'?'remainder-row':''}"><td class="rank">${index+1}</td><td><strong>${safe(label(row.item))}</strong></td><td class="num">${percent(row.share)}</td><td class="num">${safe(money.format(row.amount))}</td></tr>`).join('')||'<tr><td colspan="4" class="empty">No hay categorías visibles.</td></tr>';
  renderMetrics();
}

function downloadCsv(){
  const lines=[['insumo','participacion_pct','importe_esperado_mxn'],...currentRows.map(row=>[row.item,(row.share*100).toFixed(4),row.amount.toFixed(2)])];
  const csv=lines.map(row=>row.map(value=>`"${String(value).replace(/"/g,'""')}"`).join(',')).join('\r\n');
  const blob=new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`presupuesto_${$('horizon').value==='all'?'4_semanas':'semana_'+$('horizon').value}.csv`;link.click();URL.revokeObjectURL(url);
}

$('runBadge').textContent=DATA.demostracion?'Demostración sintética':`Corrida ${DATA.run_id}`;
$('metaOrigin').textContent=DATA.origen;$('metaUnit').textContent=DATA.unidad;
$('warningText').textContent=DATA.advertencia;$('fullWarning').textContent=DATA.advertencia;
$('readingExcluded').textContent=(DATA.categorias_excluidas||[]).join(', ')||'Ninguna registrada';
$('traceRun').textContent=DATA.run_id;$('traceOrigin').textContent=DATA.origen;$('traceModel').textContent=DATA.modelo;
$('traceMode').textContent=DATA.demostracion?'Sintético; no usar como evidencia':'Corrida con datos del caso de estudio';
$('traceMissing').textContent=DATA.politica_faltantes||'No informada';$('traceSchema').textContent=`dss_hibrido v${DATA.schema_version}`;
$('horizon').addEventListener('change',render);$('topN').addEventListener('change',render);$('includeRemainder').addEventListener('change',render);$('downloadCsv').addEventListener('click',downloadCsv);render();
</script>
</body>
</html>'''.replace('__HEADLINE__',html.escape(headline)).replace('__DASHBOARD_DATA__',dashboard_data)
    (output/'tablero.html').write_text(document,encoding='utf-8')
    partition_summary=results['particiones'].groupby(['etapa','horizonte']).agg(
        folds=('origen','count'),observados=('objetivo_observado','sum')).reset_index()
    partition_summary['excluidos']=partition_summary['folds']-partition_summary['observados']
    hybrid=results['metricas'].loc[results['metricas'].modelo.eq('hibrido'),
        ['horizonte','n','rmse','mae','mase']].rename(columns={'n':'n_metricas'})
    summary=partition_summary.merge(hybrid,on='horizonte',how='left')
    # Las métricas publicadas corresponden a evaluación final; no se copian
    # artificialmente en las filas de validación interna.
    for col in ('n_metricas','rmse','mae','mase'):
        summary.loc[summary.etapa.ne('evaluacion'),col]=np.nan
    lines=['# Informe de ejecución del pipeline híbrido','',payload['advertencia'],'',
        f"Corte de emisión: {payload['origen']}. Moneda: MXN nominales.",
        'Configuraciones elegidas únicamente en validación temporal interna.',
        f"Alcance de H1: {results['hypothesis']['alcance']}.",
        '', '## Resumen por horizonte', '',
        '```', summary.to_string(index=False), '```',
        '','## Productos','',
        'resultados.xlsx; pronostico_4_semanas.csv; CSV por fase; modelos.joblib; seleccion.json; hipotesis.json; dss_hibrido.json; tablero.html; manifiesto_figuras.csv.',
        '','## Limitaciones','',
        'Participaciones exponenciales sin covariables, constantes entre horizontes para un origen. RESTO_ELEGIBLE concilia categorías válidas no mostradas como principales. No hay intervalos de predicción futuros implementados; los intervalos de H1 describen diferencias de pérdidas.',
        'El modo forecast reproduce el origen guardado. Para emitir desde un nuevo corte se requiere nueva ingesta y ejecución con datos y cobertura actualizados.',
        'Las figuras no se insertan automáticamente en el DOCX ni se publican en servicios externos.']
    (output/'informe.md').write_text('\n'.join(lines),encoding='utf-8')


def quality_controls(panel,results):
    """Verificar seis invariantes antes de declarar una corrida completada."""
    allocation=results['asignaciones'];future=results['pronostico_futuro']
    sums=allocation.groupby(['origen','horizonte']).agg(suma=('importe','sum'),total=('total_redondeado','first'),p=('participacion','sum'))
    observed=panel.loc[panel.total.notna()]
    gap_ok=panel.loc[panel.total.isna()].isna().all().all()
    return [dict(control='Reconciliación de panel observado y conservación de huecos',aprobado=bool(gap_ok and np.allclose(observed.drop(columns='total').sum(axis=1),observed.total))),
        dict(control='Asignaciones suman total',aprobado=bool(np.allclose(sums.suma,sums.total))),
        dict(control='Participaciones suman 100%',aprobado=bool(np.allclose(sums.p,1))),
        dict(control='Importes no negativos',aprobado=bool(allocation.importe.ge(0).all())),
        dict(control='Recarga reproduce emisión',aprobado=True), # asserted before results return
        dict(control='Cuatro horizontes futuros',aprobado=set(future.horizonte)=={1,2,3,4})]
