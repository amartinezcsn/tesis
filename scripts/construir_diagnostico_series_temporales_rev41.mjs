import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectDir = path.resolve("C:/Python/tesis");
const sourceDir = path.join(projectDir, "output", "semanal", "series_temporales");
const outputPath = path.join(projectDir, "output", "semanal", "01b_diagnostico_series_temporales.xlsx");
const previewDir = path.join(projectDir, ".artifact_work", "diagnostico_series_temporales_rev41");

function parseCsv(text) {
  const rows = [];
  let row = [], value = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') { value += '"'; i += 1; }
      else if (char === '"') quoted = false;
      else value += char;
    } else if (char === '"') quoted = true;
    else if (char === ",") { row.push(value); value = ""; }
    else if (char === "\n") { row.push(value.replace(/\r$/, "")); rows.push(row); row = []; value = ""; }
    else value += char;
  }
  if (value.length || row.length) { row.push(value.replace(/\r$/, "")); rows.push(row); }
  return rows.filter((r) => r.some((cell) => cell !== ""));
}

function typedValue(value, header) {
  if (value === "") return null;
  if (/^(true|false)$/i.test(value)) return value.toLowerCase() === "true";
  if (/fecha|semana_inicio/i.test(header) && /^\d{4}-\d{2}-\d{2}/.test(value)) return new Date(value.slice(0, 10) + "T00:00:00");
  if (/^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(value)) return Number(value);
  return value;
}

async function loadCsv(fileName) {
  const raw = await fs.readFile(path.join(sourceDir, fileName), "utf8");
  const rows = parseCsv(raw.replace(/^\uFEFF/, ""));
  const headers = rows[0];
  return [headers, ...rows.slice(1).map((row) => headers.map((header, i) => typedValue(row[i] ?? "", header)))];
}

function columnName(index) {
  let result = "", current = index;
  while (current > 0) { current -= 1; result = String.fromCharCode(65 + (current % 26)) + result; current = Math.floor(current / 26); }
  return result;
}

function styleDataSheet(sheet, matrix, options = {}) {
  const rows = matrix.length;
  const cols = matrix[0].length;
  const end = columnName(cols);
  sheet.getRange(`A1:${end}${rows}`).values = matrix;
  sheet.getRange(`A1:${end}1`).format = {
    fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center", verticalAlignment: "center", wrapText: true,
  };
  sheet.getRange(`A1:${end}${rows}`).format.font = { name: "Aptos", size: 10 };
  sheet.getRange(`A2:${end}${rows}`).format.verticalAlignment = "center";
  sheet.getRange(`A1:${end}${rows}`).format.autofitColumns();
  sheet.getRange(`A1:${end}${rows}`).format.autofitRows();
  for (let col = 1; col <= cols; col += 1) {
    const letter = columnName(col);
    const header = String(matrix[0][col - 1]);
    if (/fecha|semana_inicio/.test(header)) sheet.getRange(`${letter}2:${letter}${rows}`).format.numberFormat = "yyyy-mm-dd";
    if (/importe|media|mediana|desviacion|min|max|acf|pacf|estadistico|z_robusto|fuerza|cv2|adi/.test(header)) sheet.getRange(`${letter}2:${letter}${rows}`).format.numberFormat = "#,##0.000";
  }
  if (options.wideTextColumn) sheet.getRange(`${options.wideTextColumn}:${options.wideTextColumn}`).format.columnWidth = 48;
  sheet.showGridlines = false;
}

const workbook = Workbook.create();
const summary = JSON.parse(await fs.readFile(path.join(sourceDir, "resumen_diagnostico.json"), "utf8"));

const summarySheet = workbook.worksheets.add("Resumen");
summarySheet.getRange("A1:F1").merge();
summarySheet.getRange("A1").values = [["Diagnóstico de la serie temporal semanal de compras"]];
summarySheet.getRange("A1:F1").format = { fill: "#17365D", font: { bold: true, color: "#FFFFFF", size: 16 }, horizontalAlignment: "left", verticalAlignment: "center" };
summarySheet.getRange("A3:B3").values = [["Indicador", "Resultado"]];
const summaryRows = [
  ["Frecuencia", summary.frecuencia], ["Bloque continuo principal", `${summary.inicio_bloque_principal} a ${summary.fin_bloque_principal}`],
  ["Semanas del bloque continuo principal", summary.semanas_bloque_continuo_principal], ["Semanas excluidas por cobertura", summary.semanas_excluidas_por_cobertura],
  ["Brechas de cobertura identificadas", summary.brechas_cobertura_identificadas],
  ["Semanas del diagnóstico de desarrollo", summary.semanas_desarrollo_diagnostico], ["Semanas finales reservadas", summary.semanas_evaluacion_reservadas],
  ["Semanas con compra positiva", summary.semanas_positivas], ["Semanas con cero (%)", summary.ceros_pct / 100],
  ["ADI", summary.adi], ["CV² de importes positivos", summary.cv2_importes_positivos],
  ["Clasificación de intermitencia", summary.clasificacion], ["Mediana semanal", summary.mediana_desarrollo],
  ["Media semanal", summary.media_desarrollo], ["Desviación estándar", summary.desviacion_desarrollo],
  ["Atípicos robustos identificados", summary.atipicos_robustos_observados], ["Ciclos anuales aproximados", summary.stl.ciclos_aproximados],
  ["Fuerza estacional STL", summary.stl.fuerza_estacional ?? "No interpretable (<3 ciclos)"], ["Fuerza de tendencia STL", summary.stl.fuerza_tendencia ?? "No interpretable (<3 ciclos)"],
];
summarySheet.getRange(`A4:B${3 + summaryRows.length}`).values = summaryRows;
summarySheet.getRange("A3:B3").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" } };
summarySheet.getRange(`A4:A${3 + summaryRows.length}`).format.font = { bold: true, color: "#17365D" };
const zeroRow = 4 + summaryRows.findIndex((row) => row[0] === "Semanas con cero (%)");
summarySheet.getRange(`B${zeroRow}`).format.numberFormat = "0.0%";
summarySheet.getRange("D3:F3").merge(); summarySheet.getRange("D3").values = [["Interpretación metodológica"]];
summarySheet.getRange("D3:F3").format = { fill: "#D9EAF7", font: { bold: true, color: "#17365D" } };
summarySheet.getRange("D4:F8").merge(); summarySheet.getRange("D4").values = [[`La serie se clasifica como ${summary.clasificacion}. Los diagnósticos se calcularon sin las ${summary.semanas_evaluacion_reservadas} semanas finales y fundamentan la selección de modelos estadísticos y de aprendizaje automático.`]];
summarySheet.getRange("D4:F8").format = { wrapText: true, verticalAlignment: "top", fill: "#F4F8FB" };
summarySheet.getRange("D10:F10").merge(); summarySheet.getRange("D10").values = [["Limitación"]];
summarySheet.getRange("D10:F10").format = { fill: "#FCE4D6", font: { bold: true, color: "#9C5700" } };
summarySheet.getRange("D11:F15").merge(); summarySheet.getRange("D11").values = [[summary.stl.advertencia + " " + summary.limitacion]];
summarySheet.getRange("D11:F15").format = { wrapText: true, verticalAlignment: "top", fill: "#FFF4EC" };
summarySheet.getRange("A1:F23").format.font = { name: "Aptos", size: 10 };
summarySheet.getRange("A1:F23").format.autofitColumns(); summarySheet.getRange("A1:F23").format.autofitRows();
summarySheet.getRange("A:A").format.columnWidth = 37; summarySheet.getRange("B:B").format.columnWidth = 24;
summarySheet.getRange("D:F").format.columnWidth = 18; summarySheet.showGridlines = false;

const definitions = [
  ["Métrica", "Definición", "Uso en la investigación"],
  ["ADI", "Intervalo promedio entre semanas con compra positiva.", "Caracteriza la intermitencia."],
  ["CV²", "Cuadrado del coeficiente de variación de los importes positivos.", "Caracteriza la variabilidad del tamaño de compra."],
  ["ADF", "Contrasta la hipótesis nula de raíz unitaria.", "Diagnóstico complementario de estacionariedad."],
  ["KPSS", "Contrasta la hipótesis nula de estacionariedad en nivel.", "Se interpreta junto con ADF."],
  ["ACF/PACF", "Dependencia lineal entre la serie y sus rezagos.", "Orienta rezagos y especificaciones parsimoniosas."],
  ["STL", "Descomposición robusta en tendencia, estacionalidad y residuo.", "Exploratoria por la longitud limitada de la serie."],
];
const definitionsSheet = workbook.worksheets.add("Definiciones"); styleDataSheet(definitionsSheet, definitions, { wideTextColumn: "B" }); definitionsSheet.getRange("C:C").format.columnWidth = 48;

const inputs = [
  ["Serie semanal", "serie_semanal.csv"], ["Pruebas de estacionariedad", "pruebas_estacionariedad.csv"],
  ["Autocorrelaciones", "acf_pacf.csv"], ["Intermitencia", "resumen_diagnostico.json"],
  ["Atípicos", "atipicos_robustos.csv"], ["Brechas de cobertura", "brechas_cobertura.csv"],
  ["Descomposición", "componentes_stl.csv"],
];
summarySheet.getRange("D17:E23").values = inputs;
summarySheet.getRange("D17:E17").format = { fill: "#D9EAF7", font: { bold: true, color: "#17365D" } };

const sheetSpecs = [
  ["Serie semanal", "serie_semanal.csv"], ["ACF PACF", "acf_pacf.csv"],
  ["Estacionariedad", "pruebas_estacionariedad.csv"], ["Ljung Box", "ljung_box.csv"],
  ["Perfil anual", "perfil_semana_anio.csv"], ["Perfil mensual", "perfil_mes.csv"],
  ["Atipicos", "atipicos_robustos.csv"], ["Brechas cobertura", "brechas_cobertura.csv"],
  ["Componentes STL", "componentes_stl.csv"],
  ["Figuras", "manifiesto_figuras.csv"],
];
for (const [name, fileName] of sheetSpecs) {
  const matrix = await loadCsv(fileName);
  const sheet = workbook.worksheets.add(name);
  styleDataSheet(sheet, matrix, { wideTextColumn: name === "Figuras" ? "C" : undefined });
  if (name === "Serie semanal") {
    const chart = sheet.charts.add("line", sheet.getRange(`A1:B${matrix.length}`));
    chart.title = "Importe semanal observado de compras"; chart.hasLegend = false;
    chart.xAxis = { axisType: "textAxis", textStyle: { fontSize: 9 } };
    chart.yAxis = { numberFormatCode: "$#,##0" }; chart.setPosition("J2", "R20");
  }
  if (name === "ACF PACF") {
    const chart = sheet.charts.add("line", sheet.getRange(`A1:C${matrix.length}`));
    chart.title = "Autocorrelación semanal"; chart.hasLegend = true;
    chart.xAxis = { axisType: "textAxis" }; chart.yAxis = { numberFormatCode: "0.00" };
    chart.setPosition("H2", "P20");
  }
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
const inspect = await workbook.inspect({ kind: "workbook,sheet,table,drawing", maxChars: 7000, tableMaxRows: 5, tableMaxCols: 8 });
console.log(inspect.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 200 }, summary: "final formula error scan" });
console.log(errors.ndjson);
for (const sheetName of ["Resumen", "Serie semanal", "ACF PACF", "Estacionariedad", "Perfil anual", "Atipicos", "Componentes STL"]) {
  const image = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName.replaceAll(" ", "_")}.png`), new Uint8Array(await image.arrayBuffer()));
}
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);
console.log(`Workbook generado: ${outputPath}`);
