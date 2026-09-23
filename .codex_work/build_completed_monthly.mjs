import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workspace = "C:/Python/tesis";
const sourceDir = path.join(workspace, "datasets/xlsx/originales");
const outputDir = path.join(workspace, "outputs/01a0cc5d-ecb9-7661-9180-6b901b0b049d");
const previewDir = path.join(workspace, ".codex_work/previews");
const mode = process.argv[2] || "inspect";

function asDate(value) {
  if (value instanceof Date && !Number.isNaN(value.valueOf())) return value;
  if (typeof value === "number") {
    const d = new Date(Date.UTC(1899, 11, 30));
    d.setUTCDate(d.getUTCDate() + value);
    return d;
  }
  if (typeof value === "string") {
    const m = value.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
    if (m) return new Date(Date.UTC(Number(m[3]), Number(m[2]) - 1, Number(m[1])));
    const d = new Date(value);
    if (!Number.isNaN(d.valueOf())) return d;
  }
  return null;
}

function monthKey(d) {
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

function monthDate(key) {
  const [y, m] = key.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, 1));
}

function monthRange(firstKey, lastKey) {
  const result = [];
  const d = monthDate(firstKey);
  const end = monthDate(lastKey);
  while (d <= end) {
    result.push(monthKey(d));
    d.setUTCMonth(d.getUTCMonth() + 1);
  }
  return result;
}

function weekStartMonday(d) {
  const result = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const daysSinceMonday = (result.getUTCDay() + 6) % 7;
  result.setUTCDate(result.getUTCDate() - daysSinceMonday);
  return result;
}

function weekKey(d) {
  return weekStartMonday(d).toISOString().slice(0, 10);
}

function weekRange(firstKey, lastKey) {
  const result = [];
  const d = new Date(`${firstKey}T00:00:00Z`);
  const end = new Date(`${lastKey}T00:00:00Z`);
  while (d <= end) {
    result.push(d.toISOString().slice(0, 10));
    d.setUTCDate(d.getUTCDate() + 7);
  }
  return result;
}

function nearestObserved(keys, observedSet, index, direction) {
  for (let i = index + direction; i >= 0 && i < keys.length; i += direction) {
    if (observedSet.has(keys[i])) return i;
  }
  return null;
}

function excelCol(index) {
  let n = index + 1;
  let s = "";
  while (n > 0) {
    n -= 1;
    s = String.fromCharCode(65 + (n % 26)) + s;
    n = Math.floor(n / 26);
  }
  return s;
}

async function loadBook(filename) {
  const blob = await FileBlob.load(path.join(sourceDir, filename));
  return SpreadsheetFile.importXlsx(blob);
}

async function inspectSources() {
  await fs.mkdir(previewDir, { recursive: true });
  for (const filename of ["Compras.xlsx", "Ventas.xlsx"]) {
    const wb = await loadBook(filename);
    const summary = await wb.inspect({
      kind: "workbook,sheet,table",
      maxChars: 5000,
      tableMaxRows: 8,
      tableMaxCols: 12,
      tableMaxCellChars: 60,
    });
    console.log(`INSPECT ${filename}\n${summary.ndjson}`);
    const sheet = wb.worksheets.getItem("Hoja1");
    const preview = await wb.render({
      sheetName: "Hoja1",
      range: filename === "Compras.xlsx" ? "A1:J20" : "A1:Y18",
      scale: 1.2,
      format: "png",
    });
    const out = path.join(previewDir, filename.replace(".xlsx", ".png"));
    await fs.writeFile(out, new Uint8Array(await preview.arrayBuffer()));
    console.log(`PREVIEW ${out}`);
  }
}

function applySheetStyle(sheet, lastRow, lastCol, imputedRows) {
  const endCol = excelCol(lastCol - 1);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(4);
  sheet.getRange(`A1:${endCol}${lastRow}`).format.font = { name: "Arial", size: 10 };
  sheet.getRange(`A1:${endCol}1`).format.font = { name: "Arial", size: 15, bold: true, color: "#1F2937" };
  sheet.getRange(`A2:${endCol}2`).format.font = { name: "Arial", size: 10, italic: true, color: "#4B5563" };
  sheet.getRange(`A4:${endCol}4`).format = {
    fill: "#1F4E78",
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: "#1F4E78" },
  };
  sheet.getRange(`A5:${endCol}${lastRow}`).format.borders = {
    insideHorizontal: { style: "thin", color: "#E5E7EB" },
    bottom: { style: "thin", color: "#D1D5DB" },
  };
  for (const row of imputedRows) {
    sheet.getRange(`A${row}:${endCol}${row}`).format.fill = "#FFF2CC";
    sheet.getRange(`F${row}`).format.font = { name: "Arial", size: 10, bold: true, color: "#9C5700" };
  }
  sheet.getRange(`A5:A${lastRow}`).setNumberFormat("mmm yyyy");
  sheet.getRange(`B5:B${lastRow}`).setNumberFormat("#,##0.00");
  sheet.getRange(`C5:C${lastRow}`).setNumberFormat("#,##0.00");
  sheet.getRange(`D5:E${lastRow}`).setNumberFormat("#,##0");
  sheet.getRange(`H5:I${lastRow}`).setNumberFormat("mmm yyyy");
  sheet.getRange(`A1:${endCol}${lastRow}`).format.verticalAlignment = "center";
  sheet.getRange(`A1:${endCol}${lastRow}`).format.autofitRows();
  const widths = [15, 18, 17, 13, 18, 13, 34, 16, 16];
  widths.forEach((width, i) => sheet.getRange(`${excelCol(i)}:${excelCol(i)}`).format.columnWidth = width);
  sheet.getRange("G:G").format.wrapText = true;
}

function applyWeeklyStyle(sheet, lastRow, imputedRows) {
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(4);
  sheet.getRange(`A1:J${lastRow}`).format.font = { name: "Arial", size: 10 };
  sheet.getRange("A1:J1").format.font = { name: "Arial", size: 15, bold: true, color: "#1F2937" };
  sheet.getRange("A2:J2").format.font = { name: "Arial", size: 10, italic: true, color: "#4B5563" };
  sheet.getRange("A4:J4").format = {
    fill: "#1F4E78",
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: "#1F4E78" },
  };
  sheet.getRange(`A5:J${lastRow}`).format.borders = {
    insideHorizontal: { style: "thin", color: "#E5E7EB" },
    bottom: { style: "thin", color: "#D1D5DB" },
  };
  for (const row of imputedRows) {
    sheet.getRange(`A${row}:J${row}`).format.fill = "#FFF2CC";
    sheet.getRange(`G${row}`).format.font = { name: "Arial", size: 10, bold: true, color: "#9C5700" };
  }
  sheet.getRange(`A5:B${lastRow}`).setNumberFormat("dd-mmm-yyyy");
  sheet.getRange(`C5:D${lastRow}`).setNumberFormat("#,##0.00");
  sheet.getRange(`E5:F${lastRow}`).setNumberFormat("#,##0");
  sheet.getRange(`I5:J${lastRow}`).setNumberFormat("dd-mmm-yyyy");
  sheet.getRange(`A1:J${lastRow}`).format.verticalAlignment = "center";
  sheet.getRange(`A1:J${lastRow}`).format.autofitRows();
  const widths = [16, 16, 18, 17, 13, 18, 13, 34, 18, 18];
  widths.forEach((width, i) => sheet.getRange(`${excelCol(i)}:${excelCol(i)}`).format.columnWidth = width);
  sheet.getRange("H:H").format.wrapText = true;
}

function addCompletedWeeklySheet(wb, config) {
  const raw = wb.worksheets.getItem("Hoja1");
  const values = raw.getUsedRange(true).values;
  const headers = values[0].map((v) => String(v ?? ""));
  const dateIndex = headers.indexOf(config.dateHeader);
  const amountIndex = headers.indexOf(config.amountHeader);
  const quantityIndex = config.quantityHeader ? headers.indexOf(config.quantityHeader) : -1;
  const aggregates = new Map();

  for (let r = 1; r < values.length; r += 1) {
    const d = asDate(values[r][dateIndex]);
    if (!d) continue;
    const key = weekKey(d);
    if (!aggregates.has(key)) aggregates.set(key, { amount: 0, quantity: 0, rows: 0, days: new Set() });
    const item = aggregates.get(key);
    const amount = Number(values[r][amountIndex]);
    const quantity = quantityIndex >= 0 ? Number(values[r][quantityIndex]) : 0;
    if (Number.isFinite(amount)) item.amount += amount;
    if (Number.isFinite(quantity)) item.quantity += quantity;
    item.rows += 1;
    item.days.add(d.toISOString().slice(0, 10));
  }

  const observedKeys = [...aggregates.keys()].sort();
  const keys = weekRange(observedKeys[0], observedKeys.at(-1));
  const observedSet = new Set(observedKeys);
  const sheet = wb.worksheets.add("Semanal completado");
  sheet.getRange("A1").values = [[config.weeklyTitle]];
  sheet.getRange("A2").values = [["Semanas de lunes a domingo. Cada semana ausente se estima con el promedio aritmético de las semanas observadas inmediatamente anterior y posterior al hueco."]];
  sheet.getRange("A3").values = [[`Fuente: ${config.filename}, hoja Hoja1. Las transacciones originales no fueron modificadas.`]];
  sheet.getRange("A4:J4").values = [[
    "Inicio de semana", "Fin de semana", config.amountLabel, config.quantityLabel, "Registros", "Días con movimiento",
    "Estado", "Método", "Semana anterior", "Semana siguiente",
  ]];

  const rows = [];
  const formulaRows = [];
  const imputedRows = [];
  keys.forEach((key, i) => {
    const excelRow = i + 5;
    const start = new Date(`${key}T00:00:00Z`);
    const end = new Date(start);
    end.setUTCDate(end.getUTCDate() + 6);
    const agg = aggregates.get(key);
    if (agg) {
      rows.push([start, end, agg.amount, config.hasQuantity ? agg.quantity : null, agg.rows, agg.days.size, "Observado", "Dato original", null, null]);
    } else {
      const prevIndex = nearestObserved(keys, observedSet, i, -1);
      const nextIndex = nearestObserved(keys, observedSet, i, 1);
      const prevRow = prevIndex + 5;
      const nextRow = nextIndex + 5;
      rows.push([start, end, null, null, null, null, "Imputado", "Promedio simple de semanas vecinas", new Date(`${keys[prevIndex]}T00:00:00Z`), new Date(`${keys[nextIndex]}T00:00:00Z`)]);
      formulaRows.push({ excelRow, prevRow, nextRow });
      imputedRows.push(excelRow);
    }
  });

  sheet.getRange(`A5:J${rows.length + 4}`).values = rows;
  for (const { excelRow, prevRow, nextRow } of formulaRows) {
    sheet.getRange(`C${excelRow}`).formulas = [[`=AVERAGE(C${prevRow},C${nextRow})`]];
    if (config.hasQuantity) sheet.getRange(`D${excelRow}`).formulas = [[`=AVERAGE(D${prevRow},D${nextRow})`]];
    sheet.getRange(`E${excelRow}`).formulas = [[`=ROUND(AVERAGE(E${prevRow},E${nextRow}),0)`]];
    sheet.getRange(`F${excelRow}`).formulas = [[`=ROUND(AVERAGE(F${prevRow},F${nextRow}),0)`]];
  }
  const lastRow = rows.length + 4;
  applyWeeklyStyle(sheet, lastRow, imputedRows);
  return { lastRow, imputedCount: imputedRows.length };
}

function addCompletedSheet(wb, config) {
  const raw = wb.worksheets.getItem("Hoja1");
  const used = raw.getUsedRange(true);
  const values = used.values;
  const headers = values[0].map((v) => String(v ?? ""));
  const dateIndex = headers.indexOf(config.dateHeader);
  const amountIndex = headers.indexOf(config.amountHeader);
  const quantityIndex = config.quantityHeader ? headers.indexOf(config.quantityHeader) : -1;
  const aggregates = new Map();

  for (let r = 1; r < values.length; r += 1) {
    const d = asDate(values[r][dateIndex]);
    if (!d) continue;
    const key = monthKey(d);
    if (!aggregates.has(key)) aggregates.set(key, { amount: 0, quantity: 0, rows: 0, days: new Set() });
    const item = aggregates.get(key);
    const amount = Number(values[r][amountIndex]);
    const quantity = quantityIndex >= 0 ? Number(values[r][quantityIndex]) : 0;
    if (Number.isFinite(amount)) item.amount += amount;
    if (Number.isFinite(quantity)) item.quantity += quantity;
    item.rows += 1;
    item.days.add(d.toISOString().slice(0, 10));
  }

  const observedKeys = [...aggregates.keys()].sort();
  const keys = monthRange(observedKeys[0], observedKeys.at(-1));
  const observedSet = new Set(observedKeys);
  const sheet = wb.worksheets.add("Mensual completado");
  sheet.getRange("A1").values = [[config.title]];
  sheet.getRange("A2").values = [["Los meses ausentes se estiman con el promedio aritmético de los meses observados inmediatamente anterior y posterior al hueco."]];
  sheet.getRange("A3").values = [[`Fuente: ${config.filename}, hoja Hoja1. Las transacciones originales no fueron modificadas.`]];
  sheet.getRange("A4:I4").values = [[
    "Periodo", config.amountLabel, config.quantityLabel, "Registros", "Días con movimiento",
    "Estado", "Método", "Mes anterior", "Mes siguiente",
  ]];

  const rows = [];
  const formulaRows = [];
  const imputedRows = [];
  keys.forEach((key, i) => {
    const excelRow = i + 5;
    const agg = aggregates.get(key);
    if (agg) {
      rows.push([monthDate(key), agg.amount, config.hasQuantity ? agg.quantity : null, agg.rows, agg.days.size, "Observado", "Dato original", null, null]);
    } else {
      const prevIndex = nearestObserved(keys, observedSet, i, -1);
      const nextIndex = nearestObserved(keys, observedSet, i, 1);
      const prevRow = prevIndex + 5;
      const nextRow = nextIndex + 5;
      rows.push([monthDate(key), null, null, null, null, "Imputado", "Promedio simple de meses vecinos", monthDate(keys[prevIndex]), monthDate(keys[nextIndex])]);
      formulaRows.push({ excelRow, prevRow, nextRow });
      imputedRows.push(excelRow);
    }
  });

  sheet.getRange(`A5:I${rows.length + 4}`).values = rows;
  for (const { excelRow, prevRow, nextRow } of formulaRows) {
    sheet.getRange(`B${excelRow}`).formulas = [[`=AVERAGE(B${prevRow},B${nextRow})`]];
    if (config.hasQuantity) sheet.getRange(`C${excelRow}`).formulas = [[`=AVERAGE(C${prevRow},C${nextRow})`]];
    sheet.getRange(`D${excelRow}`).formulas = [[`=ROUND(AVERAGE(D${prevRow},D${nextRow}),0)`]];
    sheet.getRange(`E${excelRow}`).formulas = [[`=ROUND(AVERAGE(E${prevRow},E${nextRow}),0)`]];
  }

  const lastRow = rows.length + 4;
  applySheetStyle(sheet, lastRow, 9, imputedRows);
  return { sheet, lastRow, imputedCount: imputedRows.length };
}

async function build() {
  await fs.mkdir(outputDir, { recursive: true });
  const jobs = [
    {
      input: "Compras.xlsx",
      output: "Compras_completado_promedio_simple.xlsx",
      config: {
        filename: "Compras.xlsx", title: "Compras mensuales completadas", dateHeader: "FECHA",
        amountHeader: "MONTO", quantityHeader: "CANT", hasQuantity: true,
        amountLabel: "Monto mensual", quantityLabel: "Cantidad mensual",
      },
    },
    {
      input: "Ventas.xlsx",
      output: "Ventas_completado_promedio_simple.xlsx",
      config: {
        filename: "Ventas.xlsx", title: "Ventas mensuales completadas", dateHeader: "Fecha",
        amountHeader: "Importe", quantityHeader: null, hasQuantity: false,
        amountLabel: "Importe mensual", quantityLabel: "Cantidad mensual",
      },
    },
  ];

  for (const job of jobs) {
    const wb = await loadBook(job.input);
    const result = addCompletedSheet(wb, job.config);
    const check = await wb.inspect({
      kind: "table",
      range: `Mensual completado!A1:I${result.lastRow}`,
      include: "values,formulas",
      tableMaxRows: 90,
      tableMaxCols: 9,
      maxChars: 18000,
    });
    console.log(`CHECK ${job.output} imputed=${result.imputedCount}\n${check.ndjson}`);
    const errors = await wb.inspect({
      kind: "match",
      searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
      options: { useRegex: true, maxResults: 100 },
      summary: "final formula error scan",
    });
    console.log(`ERRORS ${job.output}\n${errors.ndjson}`);
    const preview = await wb.render({ sheetName: "Mensual completado", range: `A1:I${Math.min(result.lastRow, 30)}`, scale: 1.3, format: "png" });
    await fs.mkdir(previewDir, { recursive: true });
    await fs.writeFile(path.join(previewDir, job.output.replace(".xlsx", ".png")), new Uint8Array(await preview.arrayBuffer()));
    const output = await SpreadsheetFile.exportXlsx(wb);
    await output.save(path.join(outputDir, job.output));
    console.log(`OUTPUT ${path.join(outputDir, job.output)}`);
  }
}

async function verifyOutputs() {
  const jobs = [
    ["Compras_completado_promedio_simple.xlsx", "A88:I108"],
    ["Ventas_completado_promedio_simple.xlsx", "A1:I18"],
  ];
  for (const [filename, range] of jobs) {
    const blob = await FileBlob.load(path.join(outputDir, filename));
    const wb = await SpreadsheetFile.importXlsx(blob);
    const check = await wb.inspect({ kind: "table", range: `Mensual completado!${range}`, include: "values,formulas", tableMaxRows: 30, tableMaxCols: 9, maxChars: 9000 });
    const formulas = await wb.inspect({ kind: "formula", sheetId: "Mensual completado", range, options: { maxResults: 300 }, maxChars: 9000 });
    const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "saved formula error scan" });
    console.log(`SAVED CHECK ${filename}\n${check.ndjson}\nSAVED FORMULAS\n${formulas.ndjson}\nSAVED ERRORS\n${errors.ndjson}`);
  }
}

async function buildWeekly() {
  await fs.mkdir(outputDir, { recursive: true });
  const jobs = [
    {
      input: "Compras.xlsx", output: "Compras_completado_semanal_promedio_simple.xlsx",
      config: {
        filename: "Compras.xlsx", weeklyTitle: "Compras semanales completadas", dateHeader: "FECHA",
        amountHeader: "MONTO", quantityHeader: "CANT", hasQuantity: true,
        amountLabel: "Monto semanal", quantityLabel: "Cantidad semanal",
      },
    },
    {
      input: "Ventas.xlsx", output: "Ventas_completado_semanal_promedio_simple.xlsx",
      config: {
        filename: "Ventas.xlsx", weeklyTitle: "Ventas semanales completadas", dateHeader: "Fecha",
        amountHeader: "Importe", quantityHeader: null, hasQuantity: false,
        amountLabel: "Importe semanal", quantityLabel: "Cantidad semanal",
      },
    },
  ];
  for (const job of jobs) {
    const wb = await loadBook(job.input);
    const result = addCompletedWeeklySheet(wb, job.config);
    const check = await wb.inspect({ kind: "table", range: `Semanal completado!A1:J${Math.min(result.lastRow, 40)}`, include: "values,formulas", tableMaxRows: 40, tableMaxCols: 10, maxChars: 12000 });
    const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "weekly formula error scan" });
    console.log(`WEEKLY CHECK ${job.output} imputed=${result.imputedCount}\n${check.ndjson}\nWEEKLY ERRORS\n${errors.ndjson}`);
    const preview = await wb.render({ sheetName: "Semanal completado", range: "A1:J30", scale: 1.2, format: "png" });
    await fs.mkdir(previewDir, { recursive: true });
    await fs.writeFile(path.join(previewDir, job.output.replace(".xlsx", ".png")), new Uint8Array(await preview.arrayBuffer()));
    const output = await SpreadsheetFile.exportXlsx(wb);
    await output.save(path.join(outputDir, job.output));
    console.log(`OUTPUT ${path.join(outputDir, job.output)}`);
  }
}

async function verifyWeekly() {
  const jobs = ["Compras_completado_semanal_promedio_simple.xlsx", "Ventas_completado_semanal_promedio_simple.xlsx"];
  for (const filename of jobs) {
    const blob = await FileBlob.load(path.join(outputDir, filename));
    const wb = await SpreadsheetFile.importXlsx(blob);
    const formulaCheck = await wb.inspect({ kind: "formula", sheetId: "Semanal completado", range: "A1:J600", options: { maxResults: 1000 }, maxChars: 3000 });
    const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "saved weekly formula error scan" });
    const stateCheck = await wb.inspect({ kind: "match", searchTerm: "Imputado", options: { useRegex: false, maxResults: 1000 }, summary: "saved imputed weeks" });
    console.log(`SAVED WEEKLY ${filename}\n${formulaCheck.ndjson}\n${errors.ndjson}\n${stateCheck.ndjson}`);
  }
}

function dateText(d) {
  return `${String(d.getUTCDate()).padStart(2, "0")}/${String(d.getUTCMonth() + 1).padStart(2, "0")}/${d.getUTCFullYear()}`;
}

function isoWeekId(d) {
  const target = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  target.setUTCDate(target.getUTCDate() + 3 - ((target.getUTCDay() + 6) % 7));
  const week1 = new Date(Date.UTC(target.getUTCFullYear(), 0, 4));
  const week = 1 + Math.round(((target - week1) / 86400000 - 3 + ((week1.getUTCDay() + 6) % 7)) / 7);
  return `${target.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

async function loadOutputBook(filename) {
  const blob = await FileBlob.load(path.join(outputDir, filename));
  return SpreadsheetFile.importXlsx(blob);
}

function getImputedWeeklyRows(wb) {
  const sheet = wb.worksheets.getItem("Semanal completado");
  const values = sheet.getUsedRange(true).values;
  return values.slice(4).filter((row) => row[6] === "Imputado").map((row) => ({
    start: asDate(row[0]), end: asDate(row[1]), amount: Number(row[2]), quantity: Number(row[3]),
    estimatedRecords: Number(row[4]), activeDays: Number(row[5]), previous: asDate(row[8]), next: asDate(row[9]),
  }));
}

async function buildHoja1Completed() {
  await fs.mkdir(outputDir, { recursive: true });
  const jobs = [
    ["Compras_completado_semanal_promedio_simple.xlsx", "Compras_Hoja1_completada_semanal.xlsx", "compras"],
    ["Ventas_completado_semanal_promedio_simple.xlsx", "Ventas_Hoja1_completada_semanal.xlsx", "ventas"],
  ];
  for (const [input, outputName, type] of jobs) {
    const wb = await loadOutputBook(input);
    const induced = getImputedWeeklyRows(wb);
    const raw = wb.worksheets.getItem("Hoja1");
    const table = raw.tables.items[0];
    const originalLastRow = raw.getUsedRange(true).values.length;
    let rows;
    if (type === "compras") {
      rows = induced.map((x) => {
        const id = `IMP-${isoWeekId(x.start)}`;
        const unitPrice = Number.isFinite(x.quantity) && x.quantity !== 0 ? x.amount / x.quantity : null;
        return [
          "IMPUTADO", x.start, id, x.quantity, "estimado",
          "Registro inducido por promedio simple semanal", x.amount, unitPrice,
          "IMPUTADO", "PROMEDIO_SEMANAL",
        ];
      });
    } else {
      rows = induced.map((x) => {
        const id = `IMP-${isoWeekId(x.start)}`;
        const date = dateText(x.start);
        const observation = `Promedio simple semanal entre ${dateText(x.previous)} y ${dateText(x.next)}; no corresponde a una venta individual`;
        return [
          id, "Imputado", `${date} 12:00:00 a. m.`, 1, 1,
          "Registro inducido por promedio simple semanal", x.amount, 0, 0, 0,
          x.amount, null, "REGISTRO IMPUTADO", "PROMEDIO SEMANAL", observation,
          date, x.start.getUTCFullYear(), x.start.getUTCMonth() + 1, x.start.getUTCDate(),
          null, null, null, null, null, id,
        ];
      });
    }
    const firstNewRow = originalLastRow + 1;
    const lastNewRow = originalLastRow + rows.length;
    const endCol = type === "compras" ? "J" : "Y";
    if (table) table.rows.add(null, rows);
    else raw.getRange(`A${firstNewRow}:${endCol}${lastNewRow}`).values = rows;
    raw.getRange(`A${firstNewRow}:${endCol}${lastNewRow}`).format.fill = "#FFF2CC";
    raw.getRange(`A${firstNewRow}:${endCol}${lastNewRow}`).format.font = { name: "Arial", size: 10, color: "#7F6000" };
    if (type === "compras") {
      raw.getRange(`B${firstNewRow}:B${lastNewRow}`).setNumberFormat("dd-mmm-yyyy");
      raw.getRange(`D${firstNewRow}:D${lastNewRow}`).setNumberFormat("#,##0.00");
      raw.getRange(`G${firstNewRow}:H${lastNewRow}`).setNumberFormat("$#,##0.00");
      const widths = [16, 14, 18, 14, 12, 42, 14, 14, 20, 24];
      widths.forEach((width, i) => raw.getRange(`${excelCol(i)}:${excelCol(i)}`).format.columnWidth = width);
      raw.getRange(`F${firstNewRow}:F${lastNewRow}`).format.wrapText = true;
    }
    if (type === "ventas") {
      const widths = [18, 12, 22, 10, 13, 42, 14, 12, 10, 12, 14, 14, 20, 20, 52, 14, 10, 10, 10, 10, 10, 10, 10, 12, 18];
      widths.forEach((width, i) => raw.getRange(`${excelCol(i)}:${excelCol(i)}`).format.columnWidth = width);
      raw.getRange(`F${firstNewRow}:F${lastNewRow}`).format.wrapText = true;
      raw.getRange(`O${firstNewRow}:O${lastNewRow}`).format.wrapText = true;
    }
    const check = await wb.inspect({ kind: "table", range: `Hoja1!A${firstNewRow}:${endCol}${Math.min(lastNewRow, firstNewRow + 14)}`, include: "values,formulas", tableMaxRows: 20, tableMaxCols: type === "compras" ? 10 : 25, maxChars: 12000 });
    const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "Hoja1 completed error scan" });
    console.log(`HOJA1 CHECK ${outputName} appended=${rows.length} rows=${firstNewRow}:${lastNewRow}\n${check.ndjson}\n${errors.ndjson}`);
    const preview = await wb.render({ sheetName: "Hoja1", range: `A${Math.max(1, firstNewRow - 2)}:${endCol}${Math.min(lastNewRow, firstNewRow + 18)}`, scale: type === "compras" ? 1.2 : 0.8, format: "png" });
    await fs.writeFile(path.join(previewDir, outputName.replace(".xlsx", ".png")), new Uint8Array(await preview.arrayBuffer()));
    const output = await SpreadsheetFile.exportXlsx(wb);
    await output.save(path.join(outputDir, outputName));
    console.log(`OUTPUT ${path.join(outputDir, outputName)}`);
  }
}

async function verifyHoja1Completed() {
  const jobs = [
    ["Compras_Hoja1_completada_semanal.xlsx", "J", 1684, 1972, 289],
    ["Ventas_Hoja1_completada_semanal.xlsx", "Y", 1002, 1055, 54],
  ];
  for (const [filename, endCol, firstRow, lastRow, expected] of jobs) {
    const wb = await loadOutputBook(filename);
    const raw = wb.worksheets.getItem("Hoja1");
    const usedRows = raw.getUsedRange(true).values.length;
    const matches = await wb.inspect({ kind: "match", searchTerm: "IMPUTADO", sheetId: "Hoja1", range: `A${firstRow}:${endCol}${lastRow}`, options: { useRegex: false, maxResults: 1000 }, summary: "induced rows in Hoja1" });
    const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "saved Hoja1 error scan" });
    console.log(`SAVED HOJA1 ${filename} usedRows=${usedRows} expectedAppended=${expected}\n${matches.ndjson}\n${errors.ndjson}`);
  }
}

if (mode === "inspect") await inspectSources();
else if (mode === "build") await build();
else if (mode === "verify") await verifyOutputs();
else if (mode === "build-weekly") await buildWeekly();
else if (mode === "verify-weekly") await verifyWeekly();
else if (mode === "build-hoja1") await buildHoja1Completed();
else if (mode === "verify-hoja1") await verifyHoja1Completed();
else throw new Error(`Unknown mode: ${mode}`);
