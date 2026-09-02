/**
 * Construye una extensión sintética, trazable y separada de la serie observada.
 *
 * No altera dataset_maestro_semanal.xlsx ni debe usarse para evaluar H1/H2.
 * Los valores sintéticos sólo sirven para análisis de sensibilidad, demostración
 * del DSS o pruebas técnicas mientras se recuperan los comprobantes faltantes.
 */

import fs from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const INPUT = join(ROOT, "input", "dataset_maestro_semanal.xlsx");
const OUTPUT_DIR = join(ROOT, "output", "semanal");
const OUTPUT = join(OUTPUT_DIR, "05_extension_sintetica_compras.xlsx");
const SEED = 20260826;
const TAIL_WEEKS = 43;
const SALES_MEDIAN_FLOOR = 250;

function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function asDate(value) {
  if (value instanceof Date) return value;
  if (typeof value === "number") return new Date(Date.UTC(1899, 11, 30 + value));
  return new Date(value);
}

function isoDate(value) {
  return asDate(value).toISOString().slice(0, 10);
}

function numeric(value) {
  return Number.isFinite(Number(value)) ? Number(value) : 0;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function loadRows(values) {
  const [headers, ...data] = values;
  return data.map((row) => Object.fromEntries(headers.map((header, index) => [header, row[index]])));
}

function chooseSyntheticDonor(target, observed, random, salesMedian) {
  const week = numeric(target.semana_anio);
  const sameSeason = observed.filter((row) => Math.abs(numeric(row.semana_anio) - week) <= 2);
  const pool = sameSeason.length >= 4 ? sameSeason : observed;
  const donor = pool[Math.floor(random() * pool.length)];
  const targetSales = numeric(target.ventas_importe_real_2026_05);
  const donorSales = numeric(donor.ventas_importe_real_2026_05);
  const ratio = (targetSales + salesMedian) / (donorSales + salesMedian);
  const boundedRatio = Math.max(0.5, Math.min(2.0, ratio));
  return { donor, adjustment: boundedRatio, synthetic: Math.max(0, numeric(donor.compras_importe_semanal) * boundedRatio) };
}

async function sourceRows() {
  const input = await FileBlob.load(INPUT);
  const workbook = await SpreadsheetFile.importXlsx(input);
  const sheet = workbook.worksheets.getItemAt(0);
  const used = sheet.getUsedRange(true);
  return loadRows(used.values);
}

async function inspect() {
  const rows = await sourceRows();
  const values = rows.map((row) => numeric(row.compras_importe_semanal));
  let zeroTail = 0;
  for (let index = values.length - 1; index >= 0 && values[index] === 0; index -= 1) zeroTail += 1;
  console.log(JSON.stringify({ rows: rows.length, firstWeek: isoDate(rows[0].semana_inicio), lastWeek: isoDate(rows.at(-1).semana_inicio), zeroTail }, null, 2));
}

function columnName(index) {
  let number = index + 1;
  let output = "";
  while (number > 0) {
    const remainder = (number - 1) % 26;
    output = String.fromCharCode(65 + remainder) + output;
    number = Math.floor((number - 1) / 26);
  }
  return output;
}

async function build() {
  const rows = await sourceRows();
  const sourceTail = rows.slice(-TAIL_WEEKS);
  if (sourceTail.length !== TAIL_WEEKS || sourceTail.some((row) => numeric(row.compras_importe_semanal) !== 0)) {
    throw new Error(`Se esperaba una cola de exactamente ${TAIL_WEEKS} semanas sin cobertura de compras.`);
  }
  const observed = rows.slice(0, -TAIL_WEEKS);
  const salesMedian = Math.max(median(observed.map((row) => numeric(row.ventas_importe_real_2026_05))), SALES_MEDIAN_FLOOR);
  const random = seededRandom(SEED);
  const syntheticRows = sourceTail.map((row) => {
    const { donor, adjustment, synthetic } = chooseSyntheticDonor(row, observed, random, salesMedian);
    return { ...row, importe_sintetico: synthetic, semana_donante: isoDate(donor.semana_inicio), compra_donante: numeric(donor.compras_importe_semanal), factor_ajuste_ventas: adjustment };
  });

  const extendedHeaders = [
    "semana_inicio", "compras_importe_observado_original", "compras_importe_sensibilidad",
    "origen_objetivo", "es_sintetico", "metodo_sintetico", "semana_donante",
    "factor_ajuste_ventas", "ventas_importe_semana", "semana_anio", "eventos_festivos_semana",
    "eventos_pago_semana", "es_san_valentin", "es_dia_nino", "es_dia_madre",
  ];
  const extended = rows.map((row, index) => {
    const synthetic = index >= rows.length - TAIL_WEEKS ? syntheticRows[index - (rows.length - TAIL_WEEKS)] : null;
    return [
      asDate(row.semana_inicio), numeric(row.compras_importe_semanal),
      synthetic ? synthetic.importe_sintetico : numeric(row.compras_importe_semanal),
      synthetic ? "sintetico" : "observado", synthetic ? 1 : 0,
      synthetic ? "bootstrap estacional con ajuste por ventas" : "no aplica",
      synthetic ? synthetic.semana_donante : "", synthetic ? synthetic.factor_ajuste_ventas : null,
      numeric(row.ventas_importe_real_2026_05), numeric(row.semana_anio),
      numeric(row.eventos_festivos_semana), numeric(row.eventos_pago_semana),
      numeric(row.es_san_valentin), numeric(row.es_dia_nino), numeric(row.es_dia_madre),
    ];
  });
  const syntheticHeaders = [
    "semana_inicio", "importe_compras_sintetico", "semana_donante", "importe_compra_donante",
    "factor_ajuste_ventas", "ventas_semana_objetivo", "metodo", "semilla",
  ];
  const syntheticTable = syntheticRows.map((row) => [
    asDate(row.semana_inicio), row.importe_sintetico, row.semana_donante, row.compra_donante,
    row.factor_ajuste_ventas, numeric(row.ventas_importe_real_2026_05),
    "bootstrap estacional ±2 semanas, ajuste ventas acotado [0.5, 2.0]", SEED,
  ]);
  const metadata = [
    ["campo", "valor"],
    ["propósito", "Análisis de sensibilidad y demostración técnica; no evidencia observada."],
    ["semanas sintéticas", TAIL_WEEKS],
    ["periodo sintético", `${isoDate(sourceTail[0].semana_inicio)} a ${isoDate(sourceTail.at(-1).semana_inicio)}`],
    ["método", "Bootstrap estacional de una semana donante observada con semana del año ±2; ajuste por razón de ventas acotada."],
    ["semilla", SEED],
    ["serie original", "input/dataset_maestro_semanal.xlsx"],
    ["regla de uso", "Excluir filas es_sintetico=1 de ajuste, selección de modelos, evaluación y contraste de hipótesis."],
    ["limitación", "Los importes no sustituyen comprobantes reales ni permiten aceptar o rechazar H1/H2."],
  ];

  const workbook = Workbook.create();
  const extendedSheet = workbook.worksheets.add("serie_extendida");
  const syntheticSheet = workbook.worksheets.add("sinteticas_43");
  const metadataSheet = workbook.worksheets.add("metadatos");
  extendedSheet.showGridLines = false;
  syntheticSheet.showGridLines = false;
  metadataSheet.showGridLines = false;

  extendedSheet.getRange(`A1:${columnName(extendedHeaders.length - 1)}${extended.length + 1}`).values = [extendedHeaders, ...extended];
  syntheticSheet.getRange(`A1:${columnName(syntheticHeaders.length - 1)}${syntheticTable.length + 1}`).values = [syntheticHeaders, ...syntheticTable];
  metadataSheet.getRange(`A1:B${metadata.length}`).values = metadata;
  for (const [sheet, headerEnd, lastRow] of [[extendedSheet, columnName(extendedHeaders.length - 1), extended.length + 1], [syntheticSheet, columnName(syntheticHeaders.length - 1), syntheticTable.length + 1]]) {
    sheet.getRange(`A1:${headerEnd}1`).format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" }, wrapText: true };
    sheet.getRange(`A1:${headerEnd}${lastRow}`).format.borders = { preset: "outside", style: "thin", color: "#D9E2F3" };
    sheet.freezePanes.freezeRows(1);
    sheet.getRange(`A1:${headerEnd}${lastRow}`).format.autofitColumns();
  }
  metadataSheet.getRange("A1:B1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" } };
  metadataSheet.getRange("A1:B9").format.wrapText = true;
  metadataSheet.getRange("A1:B9").format.autofitColumns();
  metadataSheet.getRange("B2").format.columnWidth = 75;
  extendedSheet.getRange("A:A").format.columnWidth = 15;
  extendedSheet.getRange("B:C").format.columnWidth = 20;
  extendedSheet.getRange("D:F").format.columnWidth = 18;
  extendedSheet.getRange("G:G").format.columnWidth = 15;
  extendedSheet.getRange("H:H").format.columnWidth = 16;
  extendedSheet.getRange("I:I").format.columnWidth = 19;
  extendedSheet.getRange("J:O").format.columnWidth = 14;
  extendedSheet.getRange("A1:O1").format.rowHeight = 32;
  syntheticSheet.getRange("A:A").format.columnWidth = 15;
  syntheticSheet.getRange("B:B").format.columnWidth = 21;
  syntheticSheet.getRange("C:C").format.columnWidth = 15;
  syntheticSheet.getRange("D:D").format.columnWidth = 21;
  syntheticSheet.getRange("E:E").format.columnWidth = 18;
  syntheticSheet.getRange("F:F").format.columnWidth = 21;
  syntheticSheet.getRange("G:G").format.columnWidth = 52;
  syntheticSheet.getRange("H:H").format.columnWidth = 13;
  syntheticSheet.getRange("A1:H1").format.rowHeight = 32;
  extendedSheet.getRange(`A2:A${extended.length + 1}`).format.numberFormat = "yyyy-mm-dd";
  extendedSheet.getRange(`B2:C${extended.length + 1}`).format.numberFormat = '"$"#,##0.00';
  extendedSheet.getRange(`H2:H${extended.length + 1}`).format.numberFormat = "0.000";
  syntheticSheet.getRange(`A2:A${syntheticTable.length + 1}`).format.numberFormat = "yyyy-mm-dd";
  syntheticSheet.getRange(`B2:B${syntheticTable.length + 1}`).format.numberFormat = '"$"#,##0.00';
  syntheticSheet.getRange(`D2:D${syntheticTable.length + 1}`).format.numberFormat = '"$"#,##0.00';
  syntheticSheet.getRange(`E2:E${syntheticTable.length + 1}`).format.numberFormat = "0.000";
  extendedSheet.getRange(`D2:D${extended.length + 1}`).conditionalFormats.add("containsText", { text: "sintetico", format: { fill: "#FFF2CC", font: { bold: true, color: "#7F6000" } } });

  const preview = await workbook.render({ sheetName: "sinteticas_43", range: "A1:H20", scale: 1.5, format: "png" });
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  await fs.writeFile(join(OUTPUT_DIR, "05_extension_sintetica_previa.png"), new Uint8Array(await preview.arrayBuffer()));
  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  await xlsx.save(OUTPUT);
  console.log(JSON.stringify({ output: OUTPUT, rowsSynthetic: syntheticRows.length, meanSynthetic: syntheticRows.reduce((sum, row) => sum + row.importe_sintetico, 0) / syntheticRows.length }, null, 2));
}

if (process.argv.includes("--inspect")) await inspect();
else await build();
