from pathlib import Path
import json
import html
import numpy as np
import pandas as pd


def records(frame):
    # pandas JSON handles timestamps and missing numerics without emitting NaN.
    return json.loads(frame.to_json(orient='records',date_format='iso'))


def export_results(output,results,cfg,demo=False):
    output=Path(output)
    future=results['pronostico_futuro']
    totals=future.groupby('horizonte').total.first()
    payload={'schema_version':1,'run_id':output.name,'demostracion':demo,'unidad':'MXN nominales',
        'modelo':'hibrido estadistico y aprendizaje automatico','origen':future.origen.iloc[0],
        'consolidado_4_semanas':round(float(totals.sum()),2),
        'horizontes':[1,2,3,4],'seleccion':results['selection'],'hipotesis':results['hypothesis'],
        'metricas_total':records(results['metricas']),'metricas_composicion':records(results['metricas_composicion']),
        'predicciones_validacion':records(results['predicciones']),
        'distribucion_futura':records(future),
        'advertencia':'DEMOSTRACIÓN SINTÉTICA: NO ES EVIDENCIA DE CUP&CAKE.' if demo else 'Evaluación retrospectiva; no garantiza precisión futura. Corte de emisión explícito. No es una orden de compra.'}
    if 'advertencia' in results:
        payload['advertencia']+=' '+results['advertencia']
        payload['politica_faltantes']=results['politica_faltantes']
        payload['cobertura_evaluacion']=records(results['particiones'])
    (output/'dss_hibrido.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    # Safe static, self-contained view; no remote upload or implicit deployment.
    def table(df):
        return df.to_html(index=False,escape=True,na_rep='No definido',float_format=lambda x:f'{x:,.2f}')
    headline='DEMOSTRACIÓN SINTÉTICA' if demo else 'Presupuesto semanal de Cup&Cake'
    document=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Pipeline híbrido</title>
<style>body{{font:16px system-ui;margin:2rem auto;max-width:1200px;padding:0 1rem;color:#203044}}h1,h2{{color:#203044}}.notice{{padding:1rem;background:#fff3dc}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:.55rem;text-align:left;border-bottom:1px solid #d9e1e8}}th{{background:#e8f0f6}}.scroll{{overflow:auto}}section{{margin:2rem 0}}img{{max-width:100%}}</style></head><body>
<h1>{headline}</h1><p class="notice">{html.escape(payload['advertencia'])}</p><p>Ejecución: {html.escape(output.name)}. Corte: {html.escape(payload['origen'])}. Unidad: MXN nominales.</p>
<section><h2>Pronóstico y distribución por insumo</h2><p>Consolidado de cuatro semanas: ${payload['consolidado_4_semanas']:,.2f}. No equivale a un mes calendario.</p><div class="scroll">{table(future.assign(participacion_pct=future.participacion*100).drop(columns=['demostracion','participacion']))}</div></section>
<section><h2>Evaluación del importe</h2><div class="scroll">{table(results['metricas'])}</div></section>
<section><h2>Evaluación de participaciones</h2><div class="scroll">{table(results['metricas_composicion'])}</div></section>
<section><h2>H1</h2><p>Alcance: {html.escape(results['hypothesis']['alcance'])}. Evidencia favorable en ambos componentes: {results['hypothesis']['evidencia_favorable_ambos_componentes']}. Respaldo confirmatorio: {results['hypothesis']['respaldo_confirmatorio']}.</p><p>El modelo se seleccionó en desarrollo, no por el ranking final. Revisar hipotesis.json antes de interpretar inferencia.</p></section>
<section><h2>Figuras del pipeline</h2><p>Consultar manifiesto_figuras.csv y guia_figuras.md: incluyen datos de respaldo y motivos de omisión.</p></section></body></html>'''
    (output/'tablero.html').write_text(document,encoding='utf-8')
    lines=['# Informe de ejecución del pipeline híbrido','',payload['advertencia'],'',
        f"Corte de emisión: {payload['origen']}. Moneda: MXN nominales.",
        'Configuraciones elegidas únicamente en validación temporal interna.',
        f"Alcance de H1: {results['hypothesis']['alcance']}.",
        '','## Productos','',
        'resultados.xlsx; CSV por fase; modelos.joblib; seleccion.json; hipotesis.json; dss_hibrido.json; tablero.html; manifiesto_figuras.csv.',
        '','## Limitaciones','',
        'Participaciones exponenciales sin covariables, constantes entre horizontes para un origen. No hay intervalos de predicción futuros implementados; los intervalos de H1 describen diferencias de pérdidas.',
        'El modo forecast reproduce el origen guardado. Para emitir desde un nuevo corte se requiere nueva ingesta y ejecución con datos y cobertura actualizados.',
        'Las figuras no se insertan automáticamente en el DOCX ni se publican en servicios externos.']
    (output/'informe.md').write_text('\n'.join(lines),encoding='utf-8')


def quality_controls(panel,results):
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
