import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const projectRoot = resolve(import.meta.dirname, "..");
const sourcePath = resolve(projectRoot, "public", "index.html");
const dssPath = resolve(projectRoot, "..", "output", "semanal", "04_dss_semanal.json");
const outputDir = resolve(projectRoot, "dist", "server");
const outputPath = resolve(outputDir, "index.js");

const dss = JSON.parse(await readFile(dssPath, "utf8"));

const MODEL_LABELS = {
  arima: "ARIMA",
  croston_sba: "Croston SBA",
  empirico_estacional_52s: "Estacional 52 semanas",
  empirico_promedio_4s: "Promedio móvil 4 semanas",
  empirico_ultimo_valor: "Último valor observado",
  ets: "ETS",
  hist_gradient: "HistGradientBoosting",
  lasso: "Lasso",
  random_forest: "Random Forest",
  ridge: "Ridge",
  sarima: "SARIMA",
};
const FEATURE_LABELS = {
  historico: "Histórico",
  historico_exogeno: "Histórico + exógenas",
  univariado: "Univariado",
  referencia: "Referencia empírica",
};

const finite = (value, fallback = 0) => Number.isFinite(Number(value)) ? Number(value) : fallback;
const byHorizon = (rows, horizon) => rows.filter((row) => Number(row.horizonte) === horizon);
const metric = (rows, horizon, model, featureSet = undefined) => rows.find((row) =>
  Number(row.horizonte) === horizon && row.modelo === model &&
  (featureSet === undefined || row.feature_set === featureSet));
const labelModel = (row) => `${MODEL_LABELS[row.modelo] ?? row.modelo} · ${FEATURE_LABELS[row.feature_set] ?? row.feature_set}`;

function originRmse(rows, horizon, model, featureSet, origins) {
  return origins.map((origin) => {
    const values = rows.filter((row) => Number(row.horizonte) === horizon &&
      row.modelo === model && row.feature_set === featureSet && row.origen_pronostico === origin);
    if (!values.length) return 0;
    return Math.sqrt(values.reduce((sum, row) => sum + finite(row.error_cuadrado), 0) / values.length);
  });
}

function buildDashboardData() {
  const metrics = dss.metricas ?? [];
  const predictions = dss.predicciones_validacion ?? [];
  const h1 = dss.contraste_h1 ?? [];
  const coverageRows = dss.cobertura ?? [];
  const horizons = dss.horizontes_evaluados_semanas ?? [1, 4];
  const result = { purchasesAmount: {} };

  for (const horizon of horizons) {
    const horizonMetrics = byHorizon(metrics, horizon);
    const winner = [...horizonMetrics].sort((a, b) => finite(a.rmse) - finite(b.rmse))[0];
    const base = metric(metrics, horizon, dss.linea_base_primaria) ?? {};
    const last = metric(metrics, horizon, "empirico_ultimo_valor") ?? {};
    const winnerContrast = h1.find((row) => Number(row.horizonte) === horizon &&
      winner && row.hipotesis?.includes(`${winner.modelo}/${winner.feature_set}`));
    const rows = predictions.filter((row) => Number(row.horizonte) === horizon);
    const origins = [...new Set(rows.map((row) => row.origen_pronostico))].sort().slice(-3);
    const coverage = coverageRows.find((row) => Number(row.horizonte) === horizon) ?? {};
    const firstDate = rows.map((row) => row.semana_prueba).sort()[0] ?? "sin datos";
    const lastDate = rows.map((row) => row.semana_prueba).sort().at(-1) ?? "sin datos";
    const winnerFeature = winner?.feature_set ?? "referencia";
    const winnerModel = winner?.modelo ?? dss.linea_base_primaria;
    const winnerRmse = finite(winner?.rmse);
    const baselineRmse = finite(base.rmse);
    const improvement = baselineRmse ? 100 * (baselineRmse - winnerRmse) / baselineRmse : 0;
    const supported = Boolean(winnerContrast?.apoya_hipotesis);
    const h2Supported = dss.contraste_h2?.filter((row) => Number(row.horizonte) === horizon && row.apoya_hipotesis).length ?? 0;

    result.purchasesAmount[String(horizon)] = {
      model: labelModel(winner ?? { modelo: dss.linea_base_primaria, feature_set: "referencia" }),
      dataset: `H=${horizon} · ${finite(coverage.origenes_evaluacion)} orígenes de evaluación`,
      rmse: winnerRmse,
      mae: finite(winner?.mae),
      mape: finite(winner?.mape_diagnostico),
      unit: "MXN por semana",
      coverage: `${firstDate} — ${lastDate}`,
      excluded: `${finite(coverage.semanas_cola_excluidas)} semanas de cola excluidas`,
      periods: origins,
      modelWindows: originRmse(predictions, horizon, winnerModel, winnerFeature, origins),
      avg4: {
        rmse: baselineRmse,
        windows: originRmse(predictions, horizon, dss.linea_base_primaria, "referencia", origins),
      },
      last: {
        rmse: finite(last.rmse),
        windows: originRmse(predictions, horizon, "empirico_ultimo_valor", "referencia", origins),
      },
      improvement,
      hypothesisSupported: supported,
      insight: supported
        ? `${labelModel(winner)} apoya H1 para H=${horizon}, con una reducción estimada de ${improvement.toFixed(1)}% frente al promedio móvil de cuatro semanas.`
        : `${labelModel(winner)} no aporta evidencia suficiente para aceptar H1 en H=${horizon}; la decisión debe conservar la referencia empírica hasta contar con nueva validación.`,
      note: `H1 exige significancia unilateral (α=0.05) y una reducción mínima de 20% en RMSE. Contrastes H2 con apoyo: ${h2Supported}. MAPE se muestra sólo como diagnóstico.`,
    };
  }
  return result;
}

const dashboardData = buildDashboardData();
const html = (await readFile(sourcePath, "utf8"))
  .replace("const data = __DSS_DATA__;", `const data = ${JSON.stringify(dashboardData)};`);
const encoded = Buffer.from(html, "utf8").toString("base64");

const worker = `const HTML_BASE64 = ${JSON.stringify(encoded)};

function decodeHtml() {
  return Uint8Array.from(atob(HTML_BASE64), (character) => character.charCodeAt(0));
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return new Response("ok", {
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    return new Response(decodeHtml(), {
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "public, max-age=300",
        "content-security-policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        "referrer-policy": "strict-origin-when-cross-origin",
        "x-content-type-options": "nosniff",
      },
    });
  },
};
`;

await mkdir(outputDir, { recursive: true });
await writeFile(outputPath, worker, "utf8");
console.log(`Built ${outputPath}`);
