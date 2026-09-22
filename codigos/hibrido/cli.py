"""Orquesta cada comando y deja evidencia auditable en una carpeta nueva."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import hashlib
import platform
import sys
import uuid
import importlib.metadata
import numpy as np
import pandas as pd
from .config import Config,load_config
from .data import load_purchases,templates,load_exogenous,load_sales,read_table,fingerprint
from .gaps import build_gap_panel

ROOT=Path(__file__).resolve().parents[2]
OUTPUT_DIR=Path(r'C:\Python\tesis\output')


def new_run_directory(command):
    """Crear un identificador único sin sobrescribir corridas anteriores."""
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    prefix='DEMO' if command=='demo' else command
    output=OUTPUT_DIR/(prefix+'_'+stamp+'_'+uuid.uuid4().hex[:6])
    output.mkdir(parents=True)
    return output


def create_demo(output):
    """Crear datos sintéticos aislados; DEMO nunca es evidencia de la tesis."""
    rng=np.random.default_rng(42);dates=pd.date_range('2021-01-04',periods=110,freq='W-MON');rows=[]
    for i,date in enumerate(dates):
        total=max(0,300+1.5*i+60*np.sin(i*2*np.pi/13)+rng.normal(0,12)) if i%13 else 0
        amounts=total*np.array([.45+.08*np.sin(i/8),.35-.08*np.sin(i/8),.2])
        if total == 0:
            continue
        for item,amount in zip(['HARINA','AZUCAR','MANTEQUILLA'],amounts):
            rows.append(dict(fecha=date,descripcion=item,importe_nominal=round(amount,2)))
    source=output/'compras_demo.csv';pd.DataFrame(rows).to_csv(source,index=False)
    coverage=pd.DataFrame({'semana_inicio':dates,'estado':['cero_confirmado' if i%13==0 else 'observada' for i in range(len(dates))],
        'evidencia':'fixture sintético de prueba','fecha_revision':'2026-09-12'})
    coverage.to_csv(output/'cobertura_demo.csv',index=False)
    catalog=pd.DataFrame({'descripcion_normalizada':['HARINA','AZUCAR','MANTEQUILLA'],
        'insumo_id':['harina','azucar','mantequilla'],'aprobado':True,
        'decision':'incluir','evidencia':'fixture sintético de prueba'})
    catalog.to_csv(output/'catalogo_demo.csv',index=False)
    return Config(source=str(source),source_sha256=fingerprint(source),source_approved=True,
        coverage=str(output/'cobertura_demo.csv'),catalog=str(output/'catalogo_demo.csv'),
        start=str(dates[0].date()),end=str(dates[-1].date()))


def manifest(output,cfg,status,files,error=None,demo=False):
    """Registrar estado, entorno, fuentes, código y huellas de cada producto."""
    versions={}
    for name in ['numpy','pandas','scikit-learn','statsmodels','matplotlib','openpyxl','scipy','joblib']:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]=None
    source_code=list(Path(__file__).parent.glob('*.py'))+[ROOT/'codigos/00_pipeline_hibrido.py',ROOT/'codigos/01_normalizacion.py']
    artifacts=[p for p in output.rglob('*') if p.is_file() and p.name!='manifiesto.json' and '.matplotlib' not in p.parts]
    value={'run_id':output.name,'estado':status,'demostracion':demo,'error':error,'config':cfg.dictionary() if cfg else None,
        'python':sys.version,'plataforma':platform.platform(),'versiones':versions,
        'fuentes':{str(p):fingerprint(p) for p in files if p.exists()},
        'codigo':{str(p.relative_to(ROOT)):fingerprint(p) for p in source_code},
        'productos':{str(p.relative_to(output)):fingerprint(p) for p in artifacts}}
    (output/'manifiesto.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def inventory_sources(output,source,sheet,files,cfg):
    """Comparar fuentes descriptivamente, sin cambiar la fuente canónica."""
    candidates=[(source,sheet)]+[(ROOT/'input'/name,'detalle') for name in ('compras_limpias.xlsx','compras_limpias_corregidas.xlsx')]
    rows=[]
    for candidate_number,(path,tab) in enumerate(candidates):
        if not path.exists():continue
        if path not in files:files.append(path)
        try:
            kwargs = dict(approved_duplicate_rows=cfg.approved_duplicate_rows) if candidate_number == 0 else {}
            valid,rejected=load_purchases(path,tab,**kwargs)
            rows.append(dict(archivo=str(path),sha256=fingerprint(path),estado='auditado',
                registros_validos=len(valid),pendientes=len(rejected),
                importe_nominal_valido=float(valid.importe_nominal.sum()),
                inicio=str(valid.fecha.min()),fin=str(valid.fecha.max()),
                observacion='Totales de registros sin incidencias; no equivalen a cobertura verificada.'))
        except Exception as exc:
            rows.append(dict(archivo=str(path),estado='requiere_revision',observacion=str(exc)))
    pd.DataFrame(rows).to_csv(output/'comparacion_fuentes.csv',index=False)


def execute(command,config_path=None):
    """Aplicar las puertas auditables: ingesta, aprobación, panel, modelos y salidas."""
    demo=command=='demo'
    output=new_run_directory(command)
    cfg=None;files=[]
    try:
        cfg=create_demo(output) if demo else load_config(config_path)
        cfg.validate()
        source=ROOT/cfg.source;files.append(source)
        # Primero se audita cada registro; incluso una corrida bloqueada conserva
        # sus diagnósticos y no se convierte silenciosamente en entrenamiento.
        purchases,rejected=load_purchases(
            source,cfg.source_sheet,demo,
            approved_duplicate_rows=cfg.approved_duplicate_rows,
        )
        purchases.to_csv(output/'compras_auditadas.csv',index=False)
        rejected.to_csv(output/'registros_pendientes.csv',index=False)
        coverage_template=templates(purchases,output)
        dates=pd.date_range(cfg.start,cfg.end,freq='W-MON')
        coverage_template=pd.DataFrame({'semana_inicio':dates,'estado':'desconocida','evidencia':'','fecha_revision':''})
        coverage_template['registros_detectados']=coverage_template.semana_inicio.map(purchases.groupby('semana_inicio').size()).fillna(0).astype(int)
        coverage_template.to_csv(output/'cobertura_PARA_REVISAR.csv',index=False)
        in_period=purchases.loc[purchases.semana_inicio.between(cfg.start,cfg.end)]
        cat=pd.DataFrame({'descripcion_normalizada':sorted(in_period.descripcion_normalizada.unique()),'insumo_id':'','aprobado':False,'decision':'revisar','evidencia':''})
        cat.to_csv(output/'catalogo_PARA_REVISAR.csv',index=False)
        (output/'auditoria.json').write_text(json.dumps({'fuente':str(source),'sha256':fingerprint(source),
            'registros_validos_para_revision':len(purchases),'pendientes':len(rejected),
            'cobertura':'Debe confirmarse documentalmente; transacciones no prueban integridad semanal.'},ensure_ascii=False,indent=2),encoding='utf-8')
        if not demo:inventory_sources(output,source,cfg.source_sheet,files,cfg)
        from .figures import generate_figures
        if command=='audit':
            # La auditoría termina aquí: no utiliza ni ajusta modelos.
            generate_figures(output,purchases,rejected,coverage_template,demo=demo)
            manifest(output,cfg,'auditoria_sin_entrenamiento',files,demo=demo)
            return output
        if not cfg.source_approved or not cfg.source_sha256 or fingerprint(source)!=cfg.source_sha256:
            # El hash impide reutilizar una aprobación con un archivo cambiado.
            raise ValueError('Fuente no aprobada o hash distinto. Revisar auditoría antes de entrenar.')
        if not rejected.empty:raise ValueError('Hay registros pendientes: corregir fuente o documentar decisión antes de entrenar.')
        if not cfg.start or not cfg.end:raise ValueError('Definir inicio y fin semanales del periodo auditado.')
        files.extend([ROOT/cfg.coverage,ROOT/cfg.catalog])
        panel,cov=build_gap_panel(
            purchases,
            read_table(ROOT/cfg.coverage,cfg.coverage_sheet),
            read_table(ROOT/cfg.catalog,cfg.catalog_sheet),
            cfg.start,cfg.end,cfg.zero_targets_valid,
        )
        panel.to_csv(output/'panel_semanal.csv');cov.to_csv(output/'cobertura.csv')
        if cfg.exogenous:files.append(ROOT/cfg.exogenous)
        if cfg.sales:files.append(ROOT/cfg.sales)
        exog=load_exogenous(ROOT/cfg.exogenous if cfg.exogenous else None)
        sales=load_sales(ROOT/cfg.sales if cfg.sales else None,panel.index)
        from .experiment import run_experiment
        from .reporting import export_results,quality_controls
        print('Entrenamiento y evaluación: selección interna, prueba final y persistencia.',flush=True)
        # La función experimental separa la elección de hiperparámetros del
        # periodo final, que solo sirve para evaluar las decisiones ya fijadas.
        result=run_experiment(panel,cfg,exog,output,sales,demo)
        controls=quality_controls(panel,result)
        pd.DataFrame(controls).to_csv(output/'controles.csv',index=False)
        if not all(x['aprobado'] for x in controls):raise ValueError('Fallaron controles de salida.')
        export_results(output,result,cfg,demo)
        print('Generando figuras y datos de respaldo.',flush=True)
        generate_figures(output,purchases,rejected,cov,panel,result,controls,demo)
        manifest(output,cfg,'completado_demo' if demo else 'completado',files,demo=demo)
        return output
    except Exception as exc:
        # No esconder errores: se registra el motivo y se devuelve código fallido.
        manifest(output,cfg,'bloqueado_o_fallido',files,error=str(exc),demo=demo)
        print(f'Corrida detenida. Auditoría: {output}\nMotivo: {exc}',file=sys.stderr)
        raise


def main(argv=None):
    """Interpretar los cuatro comandos públicos del pipeline."""
    parser=argparse.ArgumentParser(description='Pipeline híbrido Rev44: auditoría, demo, ejecución y reproducción de emisión.')
    parser.add_argument('command',choices=['audit','demo','run','forecast'])
    parser.add_argument('--config',default=str(ROOT/'codigos/02_config_hibrido.json'))
    parser.add_argument('--artifact',help='Modelo local de confianza generado por este pipeline. Joblib no es seguro para archivos desconocidos.')
    args=parser.parse_args(argv)
    if args.command=='forecast':
        # Solo reproduce el corte persistido. Para un corte nuevo se ejecuta run.
        if not args.artifact:parser.error('forecast requiere --artifact de confianza.')
        output=new_run_directory('forecast')
        artifact=Path(args.artifact).resolve()
        import joblib
        from .experiment import forecast_bundle
        try:
            result=forecast_bundle(joblib.load(artifact))
            result.to_csv(output/'pronostico_futuro.csv',index=False)
            manifest(output,None,'pronostico_reproducido',[artifact])
            print(f'Productos guardados en: {output}')
            return 0
        except Exception as exc:
            manifest(output,None,'bloqueado_o_fallido',[artifact],error=str(exc))
            print(f'Pronóstico detenido. Auditoría: {output}\nMotivo: {exc}',file=sys.stderr)
            return 2
    try:print(f'Productos guardados en: {execute(args.command,args.config)}');return 0
    except Exception:return 2


if __name__=='__main__':raise SystemExit(main())
