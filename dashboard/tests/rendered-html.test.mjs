import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(new Request("http://localhost/"));
}

test("server-renders the weekly purchasing dashboard", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /Cupcake Dashboard Resultados/);
  assert.match(html, /Compras · importe semanal/);
  assert.match(html, /Promedio móvil de 4 semanas/);
  assert.match(html, /H=4 · consolidación mensual/);
  assert.match(html, /DSS semanal reproducible/);
  assert.doesNotMatch(html, /Ventas · importe real|Promedio móvil de 7 días/);
  assert.doesNotMatch(html, /__DSS_DATA__/);
});

test("static build is sourced from the generated DSS artifact", async () => {
  const source = await readFile(new URL("../scripts/build-static.mjs", import.meta.url), "utf8");
  assert.match(source, /04_dss_semanal\.json/);
  assert.match(source, /JSON\.stringify\(dashboardData\)/);
});
