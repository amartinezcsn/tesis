import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(new Request("http://localhost/"));
}

test("server-renders the interactive purchasing dashboard", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /Dashboard de abastecimiento Cup&amp;Cake/);
  assert.match(html, /id="horizon"/);
  assert.match(html, /Distribución presupuestaria/);
  assert.match(html, /Trazabilidad de la emisión/);
  assert.match(html, /28 días; no equivale necesariamente a un mes calendario/);
  assert.match(html, /calcula cantidades físicas/);
  assert.match(html, /run_20261019T162504Z_f60a2f/);
  assert.doesNotMatch(html, /__DASHBOARD_DATA__/);
});

test("static build is sourced from the synchronized hybrid dashboard", async () => {
  const source = await readFile(new URL("../scripts/build-static.mjs", import.meta.url), "utf8");
  assert.match(source, /public.*index\.html/s);
  assert.match(source, /makeWorker\(html\)/);
  assert.doesNotMatch(source, /04_dss_semanal\.json/);
});
