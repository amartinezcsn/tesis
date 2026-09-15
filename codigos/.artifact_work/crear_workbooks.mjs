import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workDir = "C:/Python/tesis/codigos/.artifact_work";
const outputDir = "C:/Python/tesis/codigos/outputs/pipeline_hibrido_real";
const fontFamily = "Arial";

function columnName(index) {
  let name = "";
  for (let n = index + 1; n > 0; n = Math.floor((n - 1) / 26)) {
    name = String.fromCharCode(65 + ((n - 1) % 26)) + name;
  }
  return name;
}

async function build(inputName, outputName, tableName) {
  const spec = JSON.parse(await fs.readFile(path.join(workDir, inputName), "utf8"));
  const wb = Workbook.create();
  const dataSheet = wb.worksheets.add("Datos");
  const metaSheet = wb.worksheets.add("Metodologia");
  const headers = spec.headers;
  const rows = spec.rows.map((row) => row.map((value, index) => {
    if (value === null) return null;
    if (spec.date_columns.includes(headers[index])) return new Date(`${String(value).slice(0, 10)}T00:00:00`);
    return value;
  }));

  dataSheet.getRange("A1").write([headers, ...rows]);
  const lastColumn = columnName(headers.length - 1);
  const lastRow = rows.length + 1;
  const used = dataSheet.getRange(`A1:${lastColumn}${lastRow}`);
  used.format.font = { name: fontFamily, size: 10 };
  dataSheet.getRange(`A1:${lastColumn}1`).format = {
    fill: "#1F4E78",
    font: { name: fontFamily, size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
  dataSheet.freezePanes.freezeRows(1);
  dataSheet.tables.add(`A1:${lastColumn}${lastRow}`, true, tableName).style = "TableStyleMedium2";
  for (const dateColumn of spec.date_columns) {
    const idx = headers.indexOf(dateColumn);
    if (idx >= 0) dataSheet.getRange(`${columnName(idx)}2:${columnName(idx)}${lastRow}`).format.numberFormat = "yyyy-mm-dd";
  }
  for (const numericColumn of spec.numeric_columns) {
    const idx = headers.indexOf(numericColumn);
    if (idx >= 0) dataSheet.getRange(`${columnName(idx)}2:${columnName(idx)}${lastRow}`).format.numberFormat = "#,##0.00";
  }
  used.format.autofitColumns();
  used.format.autofitRows();
  headers.forEach((header, idx) => {
    const col = dataSheet.getRange(`${columnName(idx)}:${columnName(idx)}`);
    if (["DESCRIPCION", "Descri. Items", "descripcion_normalizada"].includes(header)) col.format.columnWidth = 38;
    else if (["metodo_sintesis", "evidencia"].includes(header)) col.format.columnWidth = 48;
    else if (["regla_asignacion", "clasificaciones_detectadas"].includes(header)) col.format.columnWidth = 30;
    else if (["fuente"].includes(header)) col.format.columnWidth = 40;
    else if (["PROVEEDOR", "CLASIFICACION", "SUBCLASIFICACION"].includes(header)) col.format.columnWidth = 20;
    else if (["estado", "clasificacion_elegida"].includes(header)) col.format.columnWidth = 24;
    else col.format.columnWidth = 16;
  });

  metaSheet.getRange("A1:B1").values = [["Complemento sintético para entrenamiento", null]];
  metaSheet.mergeCells("A1:B1");
  metaSheet.getRange("A1:B1").format = { font: { name: fontFamily, size: 14, bold: true, color: "#1F1F1F" } };
  metaSheet.getRange("A3:B3").values = [["Campo", "Valor"]];
  metaSheet.getRange("A4").write(spec.metadata);
  const metaLast = spec.metadata.length + 3;
  metaSheet.getRange(`A3:B${metaLast}`).format.font = { name: fontFamily, size: 10 };
  metaSheet.getRange("A3:B3").format = { fill: "#1F4E78", font: { name: fontFamily, bold: true, color: "#FFFFFF" } };
  metaSheet.getRange(`A3:B${metaLast}`).format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
  metaSheet.getRange(`B4:B${metaLast}`).format.wrapText = true;
  metaSheet.getRange("A:A").format.columnWidth = 26;
  metaSheet.getRange("B:B").format.columnWidth = 90;
  metaSheet.getRange(`A1:B${metaLast}`).format.autofitRows();
  metaSheet.showGridLines = false;

  const inspection = await wb.inspect({ kind: "table", sheetId: "Datos", range: `A1:${lastColumn}6`, include: "values,formulas", tableMaxRows: 6, tableMaxCols: headers.length, maxChars: 8000 });
  console.log(inspection.ndjson);
  const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: `${outputName} formula error scan` });
  console.log(errors.ndjson);
  for (const sheetName of ["Datos", "Metodologia"]) {
    const previewRange = sheetName === "Datos" ? `A1:${lastColumn}${Math.min(lastRow, 25)}` : `A1:B${metaLast}`;
    const preview = await wb.render({ sheetName, range: previewRange, scale: 1, format: "png" });
    await fs.writeFile(path.join(outputDir, `${outputName}-${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
  const output = await SpreadsheetFile.exportXlsx(wb);
  await output.save(path.join(outputDir, outputName));
}

await fs.mkdir(outputDir, { recursive: true });
await build("catalogo_pipeline.json", "catalogo_hibrido.xlsx", "CatalogoHibrido");
await build("cobertura_pipeline.json", "cobertura_hibrida.xlsx", "CoberturaHibrida");
await build("ventas_semanales_pipeline.json", "ventas_semanales_hibridas.xlsx", "VentasSemanalesHibridas");
