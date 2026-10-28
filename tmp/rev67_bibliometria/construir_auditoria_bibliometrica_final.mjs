import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Python/tesis/tmp/rev67_bibliometria/auditoria_bibliometrica.json";
const outputDir = "C:/Python/tesis/outputs/auditoria_bibliometrica_rev67";
const outputPath = `${outputDir}/Auditoria_bibliometrica_final_Rev67.xlsx`;
const previewDir = `${outputDir}/previews`;
const audit = JSON.parse(await fs.readFile(inputPath, "utf8"));

const manual = {
  "REF-01": { final: "Verificación manual necesaria", action: "Comprobar el registro arXiv/DataCite. El 404 de Crossref no invalida un DOI de arXiv.", source: "https://arxiv.org/abs/2405.15598", quality: "Media (preprint)" },
  "REF-04": { final: "Corrección necesaria", action: "Cambiar el primer autor a Omrane en la referencia y sustituir Ben Abdallah et al. (2022) en las páginas 12 y 16.", quality: "Muy alta" },
  "REF-10": { final: "Corrección necesaria", action: "Verificar la fecha editorial y, si se confirma el metadato del volumen 226, cambiar 2021 por 2020 en referencia y citas de las páginas 3, 12, 13 y 16.", quality: "Muy alta" },
  "REF-13": { final: "Verificación manual necesaria", action: "Confirmar título, año y URL en el portal oficial de Global Entrepreneurship Monitor.", source: "https://www.gemconsortium.org/report/51377", quality: "Media (informe institucional)" },
  "REF-18": { final: "Verificación manual necesaria", action: "Confirmar edición y URL en el sitio oficial OTexts.", source: "https://otexts.com/fpp3/", quality: "Alta (libro académico abierto)" },
  "REF-22": { final: "Verificación manual necesaria", action: "Confirmar título y vigencia del archivo en el portal oficial de INEGI.", quality: "Media (fuente oficial)" },
  "REF-23": { final: "Verificación manual necesaria", action: "Localizar el registro oficial de Prodem y completar URL o identificador editorial.", quality: "Media (informe institucional)" },
  "REF-35": { final: "Verificación manual necesaria", action: "Confirmar ISBN, edición y editorial en catálogo bibliográfico o de la editorial.", quality: "Alta (libro académico/profesional)" },
  "REF-36": { final: "Verificación manual necesaria", action: "Confirmar ISBN y datos de la edición en español publicada por Deusto.", quality: "Media (libro profesional)" },
  "REF-38": { final: "Corrección necesaria", action: "Retirar o reemplazar el DOI: 10.22201/fca.24488410e.2020.2215 corresponde a otro artículo. Revalidar además título, autoría y año antes de conservar la fuente.", quality: "Pendiente" },
  "REF-40": { final: "Corrección necesaria", action: "Retirar o reemplazar el DOI: 10.3390/forecast7010012 corresponde a un artículo sobre velocidad del viento. Revalidar la existencia y datos completos de la fuente citada.", quality: "Pendiente" },
};

function qualityFor(r) {
  if (manual[r.id]?.quality) return manual[r.id].quality;
  const p = (r.crossref_publisher || "").toLowerCase();
  if (/elsevier|springer/.test(p)) return "Muy alta";
  if (/oxford|wiley|sage|informa|taylor|world scientific|institute of mathematical|project euclid|jstor|emerald|mdpi|plos/.test(p)) return "Alta";
  if (/oecd/.test(p)) return "Media (fuente oficial)";
  return r.doi ? "Alta" : "Media";
}

function finalStatus(r) {
  if (manual[r.id]?.final) return manual[r.id].final;
  if (r.verification === "Verificada con Crossref") return "Correcta según metadatos";
  if (r.verification === "Verificada con diferencia menor") return "Revisión menor necesaria";
  return "Verificación manual necesaria";
}

function verificationUrl(r) {
  return manual[r.id]?.source || r.crossref_url || r.url || (r.doi ? `https://doi.org/${r.doi}` : "");
}

function recommendation(r) {
  if (manual[r.id]?.action) return manual[r.id].action;
  if (r.issues?.length) return r.issues.join("; ");
  return "Sin ajuste bibliográfico identificado por la validación automatizada.";
}

function recentClass(year) {
  if (year >= 2021) return "Reciente (2021–2026)";
  return "Clásica o fundacional (≤2020)";
}

const records = audit.records.map(r => ({
  ...r,
  finalStatus: finalStatus(r),
  recommendation: recommendation(r),
  verificationUrl: verificationUrl(r),
  quality: qualityFor(r),
  recentClass: recentClass(r.year),
}));

const wb = Workbook.create();
const summary = wb.worksheets.add("Resumen");
const detail = wb.worksheets.add("Auditoría completa");
const issues = wb.worksheets.add("Hallazgos");
const method = wb.worksheets.add("Método y fuentes");
for (const s of [summary, detail, issues, method]) s.showGridLines = false;

const navy = "#16324F";
const blue = "#24557A";
const lightBlue = "#DCEAF5";
const amber = "#FFF1CC";
const red = "#FDE2E1";
const green = "#E3F3E8";
const gray = "#EEF1F4";
const text = "#1F2933";
const font = "Arial";

function titleBlock(sheet, title, subtitle, endCol) {
  sheet.getRange(`A2:${endCol}2`).merge();
  sheet.getRange("A2").values = [[title]];
  sheet.getRange("A2").format = { font: { name: font, size: 16, bold: true, color: navy }, verticalAlignment: "center" };
  sheet.getRange(`A3:${endCol}3`).merge();
  sheet.getRange("A3").values = [[subtitle]];
  sheet.getRange("A3").format = { font: { name: font, size: 10, italic: true, color: "#51606D" }, verticalAlignment: "center" };
  sheet.getRange(`A4:${endCol}4`).format.borders = { bottom: { style: "thin", color: blue } };
}

titleBlock(summary, "Auditoría bibliométrica final — Tesis Rev67", "Corte: 28 de octubre de 2026. Correspondencia interna y validación externa de metadatos.", "J");
summary.getRange("A6:B6").values = [["Indicador", "Resultado"]];
summary.getRange("A7:A14").values = [
  ["Referencias en la lista"], ["Referencias citadas en el texto"], ["Referencias no citadas"], ["Correctas según metadatos"],
  ["Correcciones necesarias"], ["Revisión manual necesaria"], ["Con DOI"], ["Sin DOI"]
];
summary.getRange("B7").formulas = [["=COUNTA('Auditoría completa'!A7:A54)"]];
summary.getRange("B8").formulas = [["=COUNTIF('Auditoría completa'!G7:G54,\"Citada\")"]];
summary.getRange("B9").formulas = [["=B7-B8"]];
summary.getRange("B10").formulas = [["=COUNTIF('Auditoría completa'!K7:K54,\"Correcta según metadatos\")"]];
summary.getRange("B11").formulas = [["=COUNTIF('Auditoría completa'!K7:K54,\"Corrección necesaria\")"]];
summary.getRange("B12").formulas = [["=COUNTIF('Auditoría completa'!K7:K54,\"Verificación manual necesaria\")"]];
summary.getRange("B13").values = [[audit.summary.with_doi]];
summary.getRange("B14").formulas = [["=B7-B13"]];
summary.getRange("D6:J6").merge();
summary.getRange("D6").values = [["Conclusión ejecutiva"]];
summary.getRange("D7:J10").merge();
summary.getRange("D7").values = [["La correspondencia interna está completa: las 48 referencias de la bibliografía tienen al menos una mención localizable en la Rev67. Sin embargo, la bibliografía todavía no puede calificarse como totalmente correcta: cuatro registros requieren corrección y siete requieren verificación manual. Además, las citas Makridakis et al. (2018) deben desambiguarse como 2018a o 2018b según la obra realmente utilizada."]];
summary.getRange("D12:J12").merge();
summary.getRange("D12").values = [["Prioridades antes de declarar cierre bibliográfico"]];
summary.getRange("D13:J17").values = [
  ["1", "REF-38", "DOI asignado a otro artículo; revalidar fuente completa.", "Alta", "Págs. 14 y 16", "", ""],
  ["2", "REF-40", "DOI asignado a otro artículo; revalidar fuente completa.", "Alta", "Págs. 2, 7, 10 y 15", "", ""],
  ["3", "REF-04", "Primer autor incorrecto; corregir referencia y citas.", "Alta", "Págs. 12 y 16", "", ""],
  ["4", "REF-10", "Diferencia de año 2021/2020; confirmar y homologar.", "Media", "Págs. 3, 12, 13 y 16", "", ""],
  ["5", "Makridakis 2018", "Agregar sufijo a/b en citas ambiguas.", "Media", "Págs. 3, 8, 27 y 79", "", ""],
];

const detailHeaders = ["ID", "Referencia en Rev67", "Autor base", "DOI", "Año", "Actualidad", "Mencionada", "Páginas de cita", "Validación externa", "Incidencias detectadas", "Dictamen final", "Acción recomendada", "Calidad de fuente", "Título externo", "Autor externo", "Año externo", "Editorial / revista", "URL de verificación"];
detail.getRange("A1:R1").merge();
detail.getRange("A1").values = [["Auditoría bibliométrica final — detalle por referencia"]];
detail.getRange("A2:R2").merge();
detail.getRange("A2").values = [["Páginas reportadas según numeración impresa del cuerpo de la tesis. Referencias: inicio en la página impresa 86."]];
detail.getRange("A6:R6").values = [detailHeaders];
const detailRows = records.map(r => [
  r.id, r.reference, r.first_author, r.doi || "", r.year, r.recentClass, r.citation_status,
  r.citation_pages.join(", "), r.verification, (r.issues || []).join("; "), r.finalStatus,
  r.recommendation, r.quality, r.crossref_title || "", r.crossref_first_author || "",
  r.crossref_year || "", [r.crossref_container, r.crossref_publisher].filter(Boolean).join(" / "), r.verificationUrl
]);
detail.getRange("A7").write(detailRows);
detail.tables.add("A6:R54", true, "AuditoriaBibliometrica").style = "TableStyleMedium2";
detail.freezePanes.freezeRows(6);
detail.freezePanes.freezeColumns(1);

const issueHeaders = ["Prioridad", "Tipo", "Referencia / cita", "Páginas", "Evidencia", "Acción concreta", "Estado"];
issues.getRange("A1:G1").merge();
issues.getRange("A1").values = [["Hallazgos que impiden declarar la bibliografía totalmente cerrada"]];
issues.getRange("A2:G2").merge();
issues.getRange("A2").values = [["Los candidatos huérfanos detectados por apellidos de coautores fueron descartados como falsos positivos."]];
issues.getRange("A5:G5").values = [issueHeaders];
const issueRows = [
  ["Alta", "DOI incorrecto", "REF-38 — Saavedra-García y Tapia-Sánchez (2020)", "14, 16", "El DOI registrado corresponde a Tunay (2019) y a un artículo sobre crisis bancarias.", "Revalidar la fuente; reemplazar DOI y metadatos o retirar la cita.", "Pendiente"],
  ["Alta", "DOI incorrecto", "REF-40 — Spiliotis et al. (2025)", "2, 7, 10, 15", "El DOI registrado corresponde a Macabiog et al. (2025), sobre pronóstico de velocidad del viento.", "Revalidar la existencia de la fuente; reemplazar DOI y datos o retirar la cita.", "Pendiente"],
  ["Alta", "Autor incorrecto", "REF-04 — Ben Abdallah et al. (2022)", "12, 16", "Crossref identifica a Omrane como primer autor del DOI y conserva el mismo título.", "Corregir la referencia y las dos citas en texto.", "Pendiente"],
  ["Media", "Año discrepante", "REF-10 — Dubey et al. (2021)", "3, 12, 13, 16", "Crossref registra 2020 para el volumen 226 y el DOI indicado.", "Confirmar en la página editorial y homologar el año en lista y texto.", "Pendiente"],
  ["Media", "Cita ambigua", "Makridakis et al. (2018)", "3, 8, 27, 79", "La bibliografía contiene dos obras de 2018 (2018a y 2018b), pero varias citas omiten el sufijo.", "Asignar 2018a o 2018b según el argumento de cada párrafo.", "Pendiente"],
  ["Baja", "Verificación manual", "REF-01, 13, 18, 22, 23, 35 y 36", "Véase detalle", "Fuentes sin validación Crossref concluyente o sin DOI.", "Confirmar en portal institucional, catálogo editorial, ISBN o DataCite/arXiv.", "Pendiente"],
];
issues.getRange("A6").write(issueRows);
issues.tables.add("A5:G11", true, "HallazgosBibliometricos").style = "TableStyleMedium2";
issues.freezePanes.freezeRows(5);

method.getRange("A1:F1").merge();
method.getRange("A1").values = [["Método, alcance y fuentes de verificación"]];
method.getRange("A3:B3").values = [["Elemento", "Descripción"]];
method.getRange("A4:B11").values = [
  ["Documento auditado", "TESIS_OCT2026_Rev67_(ZUJ)_Final.docx"],
  ["Alcance interno", "Extracción de 48 entradas bibliográficas y búsqueda de autor-año en las páginas impresas de la Rev67."],
  ["Alcance externo", "Consulta automática de 42 DOI contra Crossref; revisión manual señalada para DOI de arXiv/DataCite, URL institucional y libros sin DOI."],
  ["Criterio de correspondencia", "Una referencia se considera mencionada cuando autor principal y año aparecen en el cuerpo, tablas o anexos antes de la bibliografía."],
  ["Criterio de corrección", "Coincidencia de título, autor principal y año con el registro externo. Un DOI que resuelve a otra obra se clasifica como corrección necesaria."],
  ["Paginación", "Páginas del cuerpo impresas en el documento; la bibliografía comienza en la página 86."],
  ["Limitación", "La presencia de una cita no prueba que la fuente respalde semánticamente cada afirmación. Esa revisión requiere lectura de contenido fuente por fuente."],
  ["Fecha de corte", "28 de octubre de 2026"],
];
method.getRange("D3:F3").values = [["Fuente", "Uso", "Enlace"]];
method.getRange("D4:F8").values = [
  ["Crossref", "Metadatos DOI de artículos, capítulos, libros e informes.", "https://api.crossref.org/works/"],
  ["DOI Foundation", "Resolución del identificador DOI.", "https://doi.org/"],
  ["arXiv", "Verificación manual de preprints.", "https://arxiv.org/"],
  ["Portales institucionales", "GEM, INEGI, OECD, OTexts y Prodem.", "Según la URL de cada referencia"],
  ["Rev67", "Correspondencia entre citas del texto y lista bibliográfica.", "Documento local auditado"],
];

const allSheets = [summary, detail, issues, method];
for (const sheet of allSheets) {
  const used = sheet.getUsedRange();
  used.format.font = { name: font, size: 10, color: text };
  used.format.verticalAlignment = "center";
}
summary.getRange("A6:B6").format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
summary.getRange("D6:J6").format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "left" };
summary.getRange("D12:J12").format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" } };
summary.getRange("D7:J10").format = { fill: lightBlue, font: { name: font, size: 11, color: text }, wrapText: true, verticalAlignment: "top" };
summary.getRange("A7:B14").format.borders = { preset: "inside", style: "thin", color: "#D6DEE5" };
summary.getRange("B7:B14").format.font = { name: font, size: 12, bold: true, color: navy };
summary.getRange("D13:J17").format.wrapText = true;
summary.getRange("D13:D17").format.font = { name: font, size: 10, bold: true, color: navy };
summary.getRange("A1:J18").format.rowHeight = 21;
summary.getRange("D7:J10").format.rowHeight = 28;
summary.getRange("A:A").format.columnWidth = 34;
summary.getRange("B:B").format.columnWidth = 16;
summary.getRange("C:C").format.columnWidth = 3;
summary.getRange("D:D").format.columnWidth = 8;
summary.getRange("E:E").format.columnWidth = 16;
summary.getRange("F:H").format.columnWidth = 24;
summary.getRange("I:J").format.columnWidth = 18;

detail.getRange("A1:R2").format.font = { name: font, color: navy, bold: true };
detail.getRange("A1").format.font = { name: font, size: 15, bold: true, color: navy };
detail.getRange("A2").format.font = { name: font, size: 10, italic: true, color: "#51606D" };
detail.getRange("A6:R6").format = { fill: navy, font: { name: font, size: 9, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", wrapText: true };
detail.getRange("A7:R54").format.verticalAlignment = "top";
detail.getRange("B7:B54").format.wrapText = true;
detail.getRange("J7:M54").format.wrapText = true;
detail.getRange("N7:R54").format.wrapText = true;
detail.getRange("A:A").format.columnWidth = 10;
detail.getRange("B:B").format.columnWidth = 66;
detail.getRange("C:C").format.columnWidth = 20;
detail.getRange("D:D").format.columnWidth = 32;
detail.getRange("E:E").format.columnWidth = 9;
detail.getRange("F:F").format.columnWidth = 25;
detail.getRange("G:G").format.columnWidth = 12;
detail.getRange("H:H").format.columnWidth = 18;
detail.getRange("I:I").format.columnWidth = 26;
detail.getRange("J:J").format.columnWidth = 40;
detail.getRange("K:K").format.columnWidth = 25;
detail.getRange("L:L").format.columnWidth = 52;
detail.getRange("M:M").format.columnWidth = 28;
detail.getRange("N:N").format.columnWidth = 48;
detail.getRange("O:Q").format.columnWidth = 22;
detail.getRange("R:R").format.columnWidth = 45;
detail.getRange("A7:R54").conditionalFormats.add("containsText", { text: "Corrección necesaria", format: { fill: red, font: { bold: true, color: "#9B1C1C" } } });
detail.getRange("A7:R54").conditionalFormats.add("containsText", { text: "Verificación manual necesaria", format: { fill: amber, font: { color: "#7A4E00" } } });
detail.getRange("A7:R54").conditionalFormats.add("containsText", { text: "Correcta según metadatos", format: { fill: green, font: { color: "#1E6335" } } });

issues.getRange("A1:G1").format.font = { name: font, size: 15, bold: true, color: navy };
issues.getRange("A2:G2").format.font = { name: font, size: 10, italic: true, color: "#51606D" };
issues.getRange("A5:G5").format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", wrapText: true };
issues.getRange("A6:G11").format.wrapText = true;
issues.getRange("A:A").format.columnWidth = 12;
issues.getRange("B:B").format.columnWidth = 22;
issues.getRange("C:C").format.columnWidth = 38;
issues.getRange("D:D").format.columnWidth = 18;
issues.getRange("E:F").format.columnWidth = 54;
issues.getRange("G:G").format.columnWidth = 14;
issues.getRange("A6:G11").conditionalFormats.add("containsText", { text: "Alta", format: { fill: red, font: { bold: true, color: "#9B1C1C" } } });
issues.getRange("A6:G11").conditionalFormats.add("containsText", { text: "Media", format: { fill: amber, font: { color: "#7A4E00" } } });

method.getRange("A1:F1").format.font = { name: font, size: 15, bold: true, color: navy };
method.getRange("A3:B3").format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
method.getRange("D3:F3").format = { fill: navy, font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
method.getRange("A4:B11").format.wrapText = true;
method.getRange("D4:F8").format.wrapText = true;
method.getRange("A:A").format.columnWidth = 26;
method.getRange("B:B").format.columnWidth = 76;
method.getRange("C:C").format.columnWidth = 4;
method.getRange("D:D").format.columnWidth = 24;
method.getRange("E:E").format.columnWidth = 48;
method.getRange("F:F").format.columnWidth = 50;

wb.recalculate();
await fs.mkdir(previewDir, { recursive: true });
const previews = [
  ["Resumen", "A1:J18", "resumen.png"],
  ["Auditoría completa", "A1:R18", "auditoria_completa.png"],
  ["Hallazgos", "A1:G12", "hallazgos.png"],
  ["Método y fuentes", "A1:F12", "metodo_fuentes.png"],
];
for (const [sheetName, range, file] of previews) {
  const blob = await wb.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(`${previewDir}/${file}`, new Uint8Array(await blob.arrayBuffer()));
}

const check = await wb.inspect({ kind: "table", range: "Resumen!A1:J18", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 12 });
console.log(check.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });
console.log(errors.ndjson);
await fs.mkdir(outputDir, { recursive: true });
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(outputPath);
console.log(JSON.stringify({ outputPath, previews: previews.map(x => `${previewDir}/${x[2]}`) }, null, 2));
