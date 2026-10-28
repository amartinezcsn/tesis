import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const input = "C:/Python/tesis/tmp/rev68_bibliometria/auditoria_bibliometrica.json";
const outputDir = "C:/Python/tesis/outputs/auditoria_bibliometrica_rev68";
const output = `${outputDir}/Auditoria_bibliometrica_Rev68.xlsx`;
const previewDir = `${outputDir}/previews`;
const data = JSON.parse(await fs.readFile(input, "utf8"));

const manual = {
  "REF-01": { status: "Correcta (verificación manual)", evidence: "Registro oficial de arXiv confirmado; Crossref no cubre de forma concluyente este DOI de arXiv/DataCite.", url: "https://arxiv.org/abs/2405.15598" },
  "REF-13": { status: "Correcta (verificación manual)", evidence: "Informe 2023/2024 confirmado en el portal oficial de GEM.", url: "https://www.gemconsortium.org/report/51377" },
  "REF-18": { status: "Correcta (verificación manual)", evidence: "Autores, año, edición y título confirmados en OTexts.", url: "https://otexts.com/fpp3/" },
  "REF-22": { status: "Correcta (verificación manual)", evidence: "Comunicado 71/25 y fecha confirmados en el portal oficial de INEGI.", url: "https://inegi.org.mx/contenidos/saladeprensa/aproposito/2025/EAP_MIPYMES_25.pdf" },
  "REF-23": { status: "Corrección necesaria", evidence: "El reporte oficial de 2020 incluye cuatro autores y un subtítulo; la Rev68 registra tres autores, abrevia incorrectamente Ibarra García y omite a Cristina Fernández y el subtítulo.", url: "https://prodem.ungs.edu.ar/wp-content/uploads/2020/12/informe-espa%C3%B1ol-17dec-Version-Final.pdf", action: "Referencia propuesta: Kantis, H., Federico, J., Ibarra García, S., & Fernández, C. (2020). Índice de condiciones sistémicas para el emprendimiento dinámico: Más allá de la pandemia: Imaginando los ecosistemas emprendedores del futuro. Prodem. En el texto, sustituir “Kantis, Federico y García (2020)” por “Kantis et al. (2020)”." },
  "REF-35": { status: "Correcta (verificación manual)", evidence: "Autor, título, editorial, año e ISBN confirmados en catálogo bibliográfico.", url: "https://discover.library.unt.edu/catalog/b2558469" },
  "REF-36": { status: "Correcta (verificación manual)", evidence: "Título, autor y edición Deusto confirmados en el catálogo editorial.", url: "https://www.planetadelibros.com/libro-el-metodo-lean-startup/63526" },
  "REF-38": { status: "Correcta (verificación manual)", evidence: "Autoría, año, título, revista, volumen y páginas confirmados en copia institucional de UNAM/Redalyc.", url: "https://www.paginaspersonales.unam.mx/app/webroot/files/210/57_Uso_de_las_TI_en_las_PYME_Industriales.pdf" },
};

const rows = data.records.map(r => {
  const m = manual[r.id];
  const status = m?.status || (r.verification === "Verificada con Crossref" ? "Correcta (Crossref)" : "Revisión necesaria");
  const evidence = m?.evidence || (r.issues?.length ? r.issues.join("; ") : "Título, autor principal y año coinciden con el registro Crossref.");
  const url = m?.url || r.crossref_url || r.url || (r.doi ? `https://doi.org/${r.doi}` : "");
  const action = m?.action || (status.startsWith("Correcta") ? "Sin ajuste." : "Revisar metadatos.");
  return [r.id, r.reference, r.first_author, r.year, r.doi || "", r.citation_status, r.citation_pages.join(", "), r.verification, status, evidence, action, r.crossref_title || "", r.crossref_first_author || "", r.crossref_year || "", r.crossref_publisher || "", url];
});

const wb = Workbook.create();
const resumen = wb.worksheets.add("Resumen");
const auditoria = wb.worksheets.add("Auditoría completa");
const hallazgos = wb.worksheets.add("Hallazgos");
const metodo = wb.worksheets.add("Método y fuentes");
for (const s of [resumen, auditoria, hallazgos, metodo]) s.showGridLines = false;

const navy = "#173A5E";
const blue = "#DCEAF5";
const red = "#FDE2E1";
const green = "#E4F3E8";
const gray = "#E9EEF3";
const font = "Arial";
const white = "#FFFFFF";
const body = "#1F2933";

function title(sheet, text, subtitle, lastCol) {
  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[text]];
  sheet.getRange("A2").format.font = { name: font, size: 16, bold: true, color: navy };
  sheet.getRange(`A3:${lastCol}3`).merge();
  sheet.getRange("A3").values = [[subtitle]];
  sheet.getRange("A3").format.font = { name: font, size: 10, italic: true, color: "#566573" };
}

title(resumen, "Auditoría bibliométrica posterior a correcciones — Rev68", "Documento auditado: TESIS_OCT2026_Rev68_(ZUJ)_Final.docx. Corte: 28 de octubre de 2026.", "J");
resumen.getRange("A6:B6").values = [["Indicador", "Resultado"]];
resumen.getRange("A7:A15").values = [["Referencias en bibliografía"], ["Referencias citadas"], ["Referencias sin citar"], ["Correctas con Crossref"], ["Correctas por verificación manual"], ["Correcciones pendientes"], ["Con DOI"], ["Sin DOI"], ["Citas 2018 ambiguas"]];
resumen.getRange("B7:B15").values = [[47], [47], [0], [39], [7], [1], [40], [7], [0]];
resumen.getRange("D6:J6").merge();
resumen.getRange("D6").values = [["Dictamen"]];
resumen.getRange("D7:J10").merge();
resumen.getRange("D7").values = [["La Rev68 corrigió satisfactoriamente REF-04, REF-10, REF-38 y eliminó REF-40. Las 47 referencias restantes están citadas y las menciones Makridakis 2018 utilizan 2018a o 2018b. La auditoría detectó una observación nueva en REF-23: el reporte Prodem 2020 está incompleto en autoría y título, y su cita narrativa no cumple la forma APA para cuatro autores."]];
resumen.getRange("D12:J12").merge();
resumen.getRange("D12").values = [["Única acción pendiente"]];
resumen.getRange("D13:J16").merge();
resumen.getRange("D13").values = [[manual["REF-23"].action]];

resumen.getRange("A6:B6").format = { fill: navy, font: { name: font, size: 10, bold: true, color: white }, horizontalAlignment: "center" };
resumen.getRange("D6:J6").format = { fill: navy, font: { name: font, size: 10, bold: true, color: white } };
resumen.getRange("D12:J12").format = { fill: navy, font: { name: font, size: 10, bold: true, color: white } };
resumen.getRange("D7:J10").format = { fill: blue, font: { name: font, size: 11, color: body }, wrapText: true, verticalAlignment: "top" };
resumen.getRange("D13:J16").format = { fill: red, font: { name: font, size: 10, color: "#8B1E1E" }, wrapText: true, verticalAlignment: "top" };
resumen.getRange("B7:B15").format.font = { name: font, size: 12, bold: true, color: navy };
resumen.getRange("A:A").format.columnWidth = 34;
resumen.getRange("B:B").format.columnWidth = 15;
resumen.getRange("C:C").format.columnWidth = 3;
resumen.getRange("D:J").format.columnWidth = 20;
resumen.getRange("D7:J10").format.rowHeight = 28;

title(auditoria, "Detalle de la auditoría bibliométrica Rev68", "Páginas conforme a la numeración impresa del cuerpo; la bibliografía inicia en la página 86.", "P");
const headers = ["ID", "Referencia en Rev68", "Autor base", "Año", "DOI", "Citada", "Páginas", "Validación automática", "Dictamen final", "Evidencia", "Acción", "Título externo", "Autor externo", "Año externo", "Editorial", "Fuente de verificación"];
auditoria.getRange("A6:P6").values = [headers];
auditoria.getRange("A7").write(rows);
auditoria.tables.add("A6:P53", true, "AuditoriaRev68").style = "TableStyleMedium2";
auditoria.freezePanes.freezeRows(6);
auditoria.freezePanes.freezeColumns(1);
auditoria.getRange("A6:P6").format = { fill: navy, font: { name: font, size: 9, bold: true, color: white }, horizontalAlignment: "center", wrapText: true };
auditoria.getRange("A7:P53").format.font = { name: font, size: 9, color: body };
auditoria.getRange("A7:P53").format.verticalAlignment = "top";
auditoria.getRange("B7:B53").format.wrapText = true;
auditoria.getRange("H7:P53").format.wrapText = true;
const widths = [9,64,19,8,30,11,16,25,27,46,52,44,19,11,22,46];
for (let i = 0; i < widths.length; i++) auditoria.getRangeByIndexes(0, i, 53, 1).format.columnWidth = widths[i];
auditoria.getRange("A7:P53").conditionalFormats.add("containsText", { text: "Corrección necesaria", format: { fill: red, font: { bold: true, color: "#8B1E1E" } } });
auditoria.getRange("A7:P53").conditionalFormats.add("containsText", { text: "Correcta", format: { fill: green, font: { color: "#1F6335" } } });

title(hallazgos, "Hallazgos de la nueva auditoría", "Los apellidos de coautores detectados por el patrón automático se descartaron como falsos positivos.", "G");
hallazgos.getRange("A6:G6").values = [["Prioridad", "Referencia", "Páginas", "Problema", "Evidencia externa", "Corrección propuesta", "Estado"]];
hallazgos.getRange("A7:G7").values = [["Media", "REF-23 — Kantis et al. (2020)", "1 y 86–89", "Autoría y título incompletos; cita narrativa no ajustada a APA.", manual["REF-23"].evidence, manual["REF-23"].action, "Pendiente"]];
hallazgos.getRange("A10:G10").values = [["Control", "Resultado", "", "", "", "", ""]];
hallazgos.getRange("A11:B15").values = [["REF-04 Omrane", "Corregida"], ["REF-10 Dubey 2020", "Corregida"], ["REF-38 Saavedra 2013", "Corregida"], ["REF-40 inválida", "Eliminada"], ["Makridakis 2018", "Sin ambigüedad"]];
hallazgos.getRange("A6:G6").format = { fill: navy, font: { name: font, size: 10, bold: true, color: white }, horizontalAlignment: "center", wrapText: true };
hallazgos.getRange("A7:G7").format = { fill: red, font: { name: font, size: 10, color: body }, wrapText: true, verticalAlignment: "top" };
hallazgos.getRange("A10:G10").format = { fill: navy, font: { name: font, size: 10, bold: true, color: white } };
hallazgos.getRange("A11:B15").format = { fill: green, font: { name: font, size: 10, color: body } };
hallazgos.getRange("A:A").format.columnWidth = 18;
hallazgos.getRange("B:B").format.columnWidth = 34;
hallazgos.getRange("C:C").format.columnWidth = 17;
hallazgos.getRange("D:E").format.columnWidth = 48;
hallazgos.getRange("F:F").format.columnWidth = 68;
hallazgos.getRange("G:G").format.columnWidth = 15;

title(metodo, "Método y fuentes de verificación", "Auditoría bidireccional de citas y referencias, complementada con metadatos y portales institucionales.", "F");
metodo.getRange("A6:B6").values = [["Componente", "Procedimiento"]];
metodo.getRange("A7:B13").values = [
  ["Correspondencia interna", "Extracción de 47 referencias y búsqueda de autor-año en cuerpo, tablas y anexos."],
  ["Metadatos DOI", "40 DOI contrastados con Crossref mediante título, primer autor y año."],
  ["Fuentes sin Crossref", "Verificación en arXiv, GEM, OTexts, INEGI, Prodem, catálogo bibliográfico, editorial Deusto y copia institucional UNAM/Redalyc."],
  ["Desambiguación", "Búsqueda explícita de Makridakis 2018 sin sufijo; resultado: cero casos."],
  ["Falsos positivos", "Apellidos de coautores identificados por el patrón automático se revisaron y no constituyen citas huérfanas."],
  ["Limitación", "La auditoría confirma identidad bibliográfica y presencia de citas; no sustituye una lectura semántica completa de cada obra."],
  ["Fecha de corte", "28 de octubre de 2026"],
];
metodo.getRange("D6:F6").values = [["Fuente", "Uso", "URL"]];
metodo.getRange("D7:F14").values = [
  ["Crossref", "Metadatos DOI", "https://api.crossref.org/works/"],
  ["arXiv", "REF-01", manual["REF-01"].url],
  ["GEM", "REF-13", manual["REF-13"].url],
  ["OTexts", "REF-18", manual["REF-18"].url],
  ["INEGI", "REF-22", manual["REF-22"].url],
  ["Prodem", "REF-23", manual["REF-23"].url],
  ["UNT Library", "REF-35", manual["REF-35"].url],
  ["UNAM / Redalyc", "REF-38", manual["REF-38"].url],
];
metodo.getRange("A6:B6").format = { fill: navy, font: { name: font, size: 10, bold: true, color: white }, horizontalAlignment: "center" };
metodo.getRange("D6:F6").format = { fill: navy, font: { name: font, size: 10, bold: true, color: white }, horizontalAlignment: "center" };
metodo.getRange("A7:B13").format.wrapText = true;
metodo.getRange("D7:F14").format.wrapText = true;
metodo.getRange("A:A").format.columnWidth = 25;
metodo.getRange("B:B").format.columnWidth = 74;
metodo.getRange("C:C").format.columnWidth = 4;
metodo.getRange("D:D").format.columnWidth = 24;
metodo.getRange("E:E").format.columnWidth = 34;
metodo.getRange("F:F").format.columnWidth = 58;

for (const s of [resumen, auditoria, hallazgos, metodo]) {
  s.getUsedRange().format.verticalAlignment = "center";
}

wb.recalculate();
await fs.mkdir(previewDir, { recursive: true });
const previews = [["Resumen", "A1:J17", "resumen.png"], ["Auditoría completa", "A1:P17", "auditoria.png"], ["Hallazgos", "A1:G16", "hallazgos.png"], ["Método y fuentes", "A1:F15", "metodo.png"]];
for (const [sheetName, range, name] of previews) {
  const img = await wb.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(`${previewDir}/${name}`, new Uint8Array(await img.arrayBuffer()));
}
const check = await wb.inspect({ kind: "table", range: "Resumen!A1:J17", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 12 });
console.log(check.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });
console.log(errors.ndjson);
await fs.mkdir(outputDir, { recursive: true });
const blob = await SpreadsheetFile.exportXlsx(wb);
await blob.save(output);
console.log(JSON.stringify({ output, previews: previews.map(x => `${previewDir}/${x[2]}`) }, null, 2));
