import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { makeWorker, build } from '../scripts/build-hibrido.mjs';

test('Worker serves UTF-8 HTML, health and explicit 404 without network',async()=>{
  const code=makeWorker('<h1>Demostración México</h1>');
  const {default:worker}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
  const result=await worker.fetch(new Request('http://localhost/'));
  assert.match(await result.text(),/México/);
  assert.equal(result.headers.get('cache-control'),'no-store');
  assert.equal((await worker.fetch(new Request('http://localhost/unknown'))).status,404);
  assert.equal(await (await worker.fetch(new Request('http://localhost/health'))).text(),'ok');
});

test('Build rejects a failed scientific run',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'tesis-hibrido-'));
  await writeFile(join(dir,'dss_hibrido.json'),JSON.stringify({schema_version:1}));
  await writeFile(join(dir,'manifiesto.json'),JSON.stringify({estado:'bloqueado_o_fallido'}));
  await assert.rejects(build(dir,join(dir,'out')),/no completada/);
});

test('Demo build requires the synthetic warning and preserves it',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'tesis-hibrido-'));
  await writeFile(join(dir,'dss_hibrido.json'),JSON.stringify({schema_version:1,demostracion:true,run_id:'demo-test'}));
  await writeFile(join(dir,'manifiesto.json'),JSON.stringify({estado:'completado_demo'}));
  await writeFile(join(dir,'tablero.html'),'<h1>Presupuesto</h1>');
  await assert.rejects(build(dir,join(dir,'out')),/sin advertencia/);
  await writeFile(join(dir,'tablero.html'),'<h1>DEMOSTRACIÓN SINTÉTICA</h1>');
  const result=await build(dir,join(dir,'out'));
  assert.ok((await readFile(result,'utf8')).includes('content-security-policy'));
});
