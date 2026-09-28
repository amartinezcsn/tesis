import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const inputPath = process.env.AUDIT_JSON || "C:/Python/tesis/tmp/auditoria_rev55/auditoria_clasificada.json";
const outputDir = "C:/Python/tesis/outputs/01a0df82-e8ad-7653-b078-d5c80402c853";
const version = process.env.AUDIT_VERSION || "Rev55";
const outputPath = process.env.AUDIT_OUTPUT || `${outputDir}/Auditoria_referencias_Rev55.xlsx`;
const previewDir = process.env.AUDIT_PREVIEW_DIR || "C:/Python/tesis/tmp/auditoria_rev55/previews";
const data = JSON.parse(await fs.readFile(inputPath, "utf8"));
const oldData = JSON.parse(await fs.readFile("C:/Python/tesis/tmp/auditoria_rev55/auditoria_clasificada.json", "utf8"));

const wb = Workbook.create();
const font = "Arial";
const dark = "#1F4E78";
const light = "#D9EAF7";
const border = "#D9D9D9";

function styleTitle(sheet, range, title, subtitle) {
  sheet.showGridLines = false;
  sheet.getRange(range).values = [[title]];
  sheet.getRange(range).format.font = { name: font, size: 16, bold: true, color: "#000000" };
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2").format.font = { name: font, size: 10, italic: true, color: "#404040" };
}

function styleHeader(range) {
  range.format = {
    fill: dark,
    font: { name: font, size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: "#FFFFFF" },
  };
}

function styleBody(range) {
  range.format.font = { name: font, size: 9, color: "#000000" };
  range.format.verticalAlignment = "top";
  range.format.wrapText = true;
  range.format.borders = { preset: "all", style: "thin", color: border };
}

function addStatusFormatting(range) {
  range.conditionalFormats.add("containsText", { text: "No coincide", format: { fill: "#F4CCCC", font: { color: "#9C0006", bold: true } } });
  range.conditionalFormats.add("containsText", { text: "No trazable", format: { fill: "#FCE5CD", font: { color: "#9C5700", bold: true } } });
  range.conditionalFormats.add("containsText", { text: "Coincidencia parcial", format: { fill: "#FFF2CC", font: { color: "#7F6000", bold: true } } });
  range.conditionalFormats.add("containsText", { text: "Coincide", format: { fill: "#D9EAD3", font: { color: "#274E13", bold: true } } });
}

// Resumen
const summary = wb.worksheets.add("Resumen");
styleTitle(summary, "A1", `Auditoría de referencias de la ${version}`, "Correspondencia entre afirmaciones y fuentes, con ubicación por página y párrafo");
summary.getRange("A4:B11").values = [
  ["Indicador", "Valor"],
  ["Párrafos o filas con citas", data.summary.citation_paragraphs],
  ["Grupos de citación", data.summary.citation_groups],
  ["Citas únicas tal como aparecen", data.summary.unique_raw_citations],
  ["Apariciones de Hyndman y Athanasopoulos (2021)", data.summary.hyndman_2021_occurrences],
  ["Coinciden", data.summary.status_counts["Coincide"]],
  ["Coincidencia parcial", data.summary.status_counts["Coincidencia parcial"]],
  ["No trazables", data.summary.status_counts["No trazable"]],
];
summary.getRange("A12:B12").values = [["No coinciden", data.summary.status_counts["No coincide"]]];
styleHeader(summary.getRange("A4:B4"));
styleBody(summary.getRange("A5:B12"));
const hyStatus = data.hyndman_rows.reduce((acc, row) => {
  acc[row.status] = (acc[row.status] || 0) + 1;
  return acc;
}, {});
summary.getRange("A14:B20").values = [
  ["Hallazgo prioritario", "Implicación"],
  [`Hyndman y Athanasopoulos (2021) aparece ${data.summary.hyndman_2021_occurrences} veces`, `${hyStatus["Coincide"] || 0} usos coinciden, ${hyStatus["Coincidencia parcial"] || 0} son parciales y ${hyStatus["No coincide"] || 0} no sostienen la afirmación concreta.`],
  ["Afirmaciones no sustentadas", "Quedan 3: cifra OCDE inferior a 25%, clasificación ADI-CV²/TSB y prácticas de decisión atribuidas a García-Pérez et al."],
  ["Correcciones verificadas", "Ya no aparecen Alekseeva et al. (2021), Cao et al. (2025) ni sus DOI incorrectos."],
  ["Fuentes ausentes", "GEM 2023 e INEGI 2023 continúan citados sin entrada bibliográfica completa."],
  ["Bibliografía", `${data.summary.bibliography_entries} entradas; ${data.summary.bibliography_known_issues} requieren corrección o verificación adicional.`],
  ["Criterio", "Coincidencia parcial significa que la fuente respalda solo una parte del párrafo o que el texto añade una inferencia propia."],
];
styleHeader(summary.getRange("A14:B14"));
styleBody(summary.getRange("A15:B20"));
summary.getRange("A1:B20").format.autofitRows();
summary.getRange("A:A").format.columnWidth = 40;
summary.getRange("B:B").format.columnWidth = 95;

// Comparativo entre versiones
const comparison = wb.worksheets.add("Comparativo");
styleTitle(comparison, "A1", "Cambios entre Rev55 y Rev56", "Variación en la correspondencia entre afirmaciones y fuentes después de las correcciones");
comparison.getRange("A4:D11").values = [
  ["Indicador", "Rev55", "Rev56", "Cambio"],
  ["Párrafos o filas con citas", oldData.summary.citation_paragraphs, data.summary.citation_paragraphs, data.summary.citation_paragraphs - oldData.summary.citation_paragraphs],
  ["Apariciones de Hyndman y Athanasopoulos (2021)", oldData.summary.hyndman_2021_occurrences, data.summary.hyndman_2021_occurrences, data.summary.hyndman_2021_occurrences - oldData.summary.hyndman_2021_occurrences],
  ["Coinciden", oldData.summary.status_counts["Coincide"], data.summary.status_counts["Coincide"], data.summary.status_counts["Coincide"] - oldData.summary.status_counts["Coincide"]],
  ["Coincidencia parcial", oldData.summary.status_counts["Coincidencia parcial"], data.summary.status_counts["Coincidencia parcial"], data.summary.status_counts["Coincidencia parcial"] - oldData.summary.status_counts["Coincidencia parcial"]],
  ["No trazables", oldData.summary.status_counts["No trazable"], data.summary.status_counts["No trazable"], data.summary.status_counts["No trazable"] - oldData.summary.status_counts["No trazable"]],
  ["No coinciden", oldData.summary.status_counts["No coincide"], data.summary.status_counts["No coincide"], data.summary.status_counts["No coincide"] - oldData.summary.status_counts["No coincide"]],
  ["Entradas bibliográficas", oldData.summary.bibliography_entries, data.summary.bibliography_entries, data.summary.bibliography_entries - oldData.summary.bibliography_entries],
];
styleHeader(comparison.getRange("A4:D4"));
styleBody(comparison.getRange("A5:D11"));
comparison.getRange("A:A").format.columnWidth = 52;
comparison.getRange("B:D").format.columnWidth = 16;
comparison.getRange("B5:D11").format.horizontalAlignment = "center";
comparison.getRange("A1:D11").format.autofitRows();

// Auditoría por párrafo
const audit = wb.worksheets.add("Auditoría por párrafo");
styleTitle(audit, "A1", "Referencias por página y párrafo", "Página PDF = posición física en el archivo; página impresa = número visible en el documento");
const auditHeaders = ["ID", "Página PDF", "Página impresa", "Párrafo con cita en página", "Párrafo DOCX", "Ubicación", "Sección", "Cita", "Texto del párrafo o fila", "Dictamen", "Fundamento", "Acción recomendada", "Fuente URL"];
const auditRows = data.audit_rows.map((r) => [r.id, r.pdf_page, r.printed_page ?? "", r.citation_paragraph_on_page ?? "", r.docx_paragraph, r.location, r.section, r.citations, r.paragraph_text, r.status, r.rationale, r.recommended_action, r.source_urls]);
audit.getRangeByIndexes(3, 0, auditRows.length + 1, auditHeaders.length).values = [auditHeaders, ...auditRows];
styleHeader(audit.getRangeByIndexes(3, 0, 1, auditHeaders.length));
styleBody(audit.getRangeByIndexes(4, 0, auditRows.length, auditHeaders.length));
audit.tables.add(`A4:M${auditRows.length + 4}`, true, "AuditoriaParrafos").style = "TableStyleMedium2";
audit.freezePanes.freezeRows(4);
audit.getRange("A:A").format.columnWidth = 7;
audit.getRange("B:E").format.columnWidth = 13;
audit.getRange("F:F").format.columnWidth = 15;
audit.getRange("G:G").format.columnWidth = 28;
audit.getRange("H:H").format.columnWidth = 34;
audit.getRange("I:I").format.columnWidth = 85;
audit.getRange("J:J").format.columnWidth = 21;
audit.getRange("K:L").format.columnWidth = 62;
audit.getRange("M:M").format.columnWidth = 48;
addStatusFormatting(audit.getRange(`J5:J${auditRows.length + 4}`));

// Hyndman 2021
const hy = wb.worksheets.add("Hyndman 2021");
styleTitle(hy, "A1", "Usos de Hyndman y Athanasopoulos 2021", `Listado específico de las ${data.summary.hyndman_2021_occurrences} apariciones detectadas`);
const hyHeaders = ["Página PDF", "Página impresa", "Párrafo DOCX", "Sección", "Cita", "Texto", "Dictamen", "Fundamento", "Acción recomendada"];
const hyRows = data.hyndman_rows.map((r) => [r.pdf_page, r.printed_page ?? "", r.docx_paragraph, r.section, r.citations, r.paragraph_text, r.status, r.rationale, r.recommended_action]);
hy.getRangeByIndexes(3, 0, hyRows.length + 1, hyHeaders.length).values = [hyHeaders, ...hyRows];
styleHeader(hy.getRangeByIndexes(3, 0, 1, hyHeaders.length));
styleBody(hy.getRangeByIndexes(4, 0, hyRows.length, hyHeaders.length));
hy.tables.add(`A4:I${hyRows.length + 4}`, true, "HyndmanUsos").style = "TableStyleMedium2";
hy.freezePanes.freezeRows(4);
hy.getRange("A:C").format.columnWidth = 14;
hy.getRange("D:D").format.columnWidth = 30;
hy.getRange("E:E").format.columnWidth = 40;
hy.getRange("F:F").format.columnWidth = 85;
hy.getRange("G:G").format.columnWidth = 22;
hy.getRange("H:I").format.columnWidth = 65;
addStatusFormatting(hy.getRange(`G5:G${hyRows.length + 4}`));

// Citas únicas
const unique = wb.worksheets.add("Referencias únicas");
styleTitle(unique, "A1", "Referencias citadas", `Agrupación según la forma exacta en que cada cita aparece en la ${version}`);
const uniqueHeaders = ["Cita", "Apariciones", "Páginas PDF", "Páginas impresas", "Peor dictamen", "Fuente URL"];
const uniqueRows = data.unique_citations.map((r) => [r.citation, r.count, r.pdf_pages, r.printed_pages, r.worst_status, r.urls]);
unique.getRangeByIndexes(3, 0, uniqueRows.length + 1, uniqueHeaders.length).values = [uniqueHeaders, ...uniqueRows];
styleHeader(unique.getRangeByIndexes(3, 0, 1, uniqueHeaders.length));
styleBody(unique.getRangeByIndexes(4, 0, uniqueRows.length, uniqueHeaders.length));
unique.tables.add(`A4:F${uniqueRows.length + 4}`, true, "ReferenciasUnicas").style = "TableStyleMedium2";
unique.freezePanes.freezeRows(4);
unique.getRange("A:A").format.columnWidth = 52;
unique.getRange("B:B").format.columnWidth = 13;
unique.getRange("C:D").format.columnWidth = 35;
unique.getRange("E:E").format.columnWidth = 22;
unique.getRange("F:F").format.columnWidth = 58;
addStatusFormatting(unique.getRange(`E5:E${uniqueRows.length + 4}`));

// Bibliografía
const bib = wb.worksheets.add("Bibliografía");
styleTitle(bib, "A1", "Revisión de la bibliografía", `Problemas de metadatos y trazabilidad detectados en las ${data.summary.bibliography_entries} entradas`);
const bibHeaders = ["Núm.", "Entrada bibliográfica", "Citas estimadas", "Estado de metadatos", "Observación"];
const bibRows = data.bibliography_audit.map((r) => [r.number, r.entry, r.cited_estimate, r.metadata_status, r.issue]);
bib.getRangeByIndexes(3, 0, bibRows.length + 1, bibHeaders.length).values = [bibHeaders, ...bibRows];
styleHeader(bib.getRangeByIndexes(3, 0, 1, bibHeaders.length));
styleBody(bib.getRangeByIndexes(4, 0, bibRows.length, bibHeaders.length));
bib.tables.add(`A4:E${bibRows.length + 4}`, true, "BibliografiaAuditada").style = "TableStyleMedium2";
bib.freezePanes.freezeRows(4);
bib.getRange("A:A").format.columnWidth = 8;
bib.getRange("B:B").format.columnWidth = 105;
bib.getRange("C:C").format.columnWidth = 15;
bib.getRange("D:D").format.columnWidth = 23;
bib.getRange("E:E").format.columnWidth = 72;

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const previews = [
  ["Resumen", "A1:B20", "resumen.png"],
  ["Comparativo", "A1:D11", "comparativo.png"],
  ["Auditoría por párrafo", "A1:M16", "auditoria.png"],
  ["Hyndman 2021", "A1:I18", "hyndman.png"],
  ["Referencias únicas", "A1:F24", "referencias.png"],
  ["Bibliografía", "A1:E22", "bibliografia.png"],
];
for (const [sheetName, range, fileName] of previews) {
  const image = await wb.render({ sheetName, range, scale: 1.2, format: "png" });
  await fs.writeFile(`${previewDir}/${fileName}`, new Uint8Array(await image.arrayBuffer()));
}

const result = await SpreadsheetFile.exportXlsx(wb);
await result.save(outputPath);

const inspect = await wb.inspect({ kind: "workbook,sheet,table", maxChars: 8000, tableMaxRows: 4, tableMaxCols: 8, tableMaxCellChars: 90 });
console.log(inspect.ndjson);
console.log(outputPath);
