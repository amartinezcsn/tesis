// Publishable local build only: this script does not deploy or upload anything.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

export function makeWorker(html) {
  const encoded = Buffer.from(html, 'utf8').toString('base64');
  return `const html = new TextDecoder().decode(Uint8Array.from(atob(${JSON.stringify(encoded)}), c => c.charCodeAt(0)));
export default { async fetch(request) {
  const path = new URL(request.url).pathname;
  if (path === '/health') return new Response('ok');
  if (path !== '/') return new Response('Not found', {status:404});
  return new Response(html, {headers:{'content-type':'text/html; charset=utf-8','x-content-type-options':'nosniff','cache-control':'no-store','content-security-policy':"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"}});
}};`;
}

export async function build(runDirectory, outputDirectory) {
  const run = resolve(runDirectory);
  const payload = JSON.parse(await readFile(resolve(run, 'dss_hibrido.json'), 'utf8'));
  const manifest = JSON.parse(await readFile(resolve(run, 'manifiesto.json'), 'utf8'));
  if (payload.schema_version !== 1 || !['completado', 'completado_demo'].includes(manifest.estado)) {
    throw new Error('Contrato incompatible o corrida no completada.');
  }
  const html = await readFile(resolve(run, 'tablero.html'), 'utf8');
  if (payload.demostracion && !html.includes('DEMOSTRACIÓN SINTÉTICA')) throw new Error('Demostración sin advertencia.');
  const out = resolve(outputDirectory);
  await mkdir(out, {recursive:true});
  await writeFile(resolve(out, 'index.js'), makeWorker(html), 'utf8');
  await writeFile(resolve(out, 'run.json'), JSON.stringify({run_id:payload.run_id, demostracion:payload.demostracion}), 'utf8');
  return resolve(out, 'index.js');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (!process.argv[2]) throw new Error('Uso: node scripts/build-hibrido.mjs <directorio corrida> [salida]');
  const out = process.argv[3] || resolve(dirname(fileURLToPath(import.meta.url)), '../dist/hibrido');
  console.log(await build(process.argv[2], out));
}
