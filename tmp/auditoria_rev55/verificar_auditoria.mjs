import fs from "node:fs/promises";
import { SpreadsheetFile } from "@oai/artifact-tool";

const path = process.env.AUDIT_OUTPUT || "C:/Python/tesis/outputs/01a0df82-e8ad-7653-b078-d5c80402c853/Auditoria_referencias_Rev55.xlsx";
const input = await fs.readFile(path);
const workbook = await SpreadsheetFile.importXlsx(input);

for (const [sheetName, range] of [
  ["Resumen", "A1:B20"],
  ["Comparativo", "A1:D11"],
  ["Auditoría por párrafo", "A1:M144"],
  ["Hyndman 2021", "A1:I45"],
  ["Referencias únicas", "A1:F80"],
  ["Bibliografía", "A1:E84"],
]) {
  const result = await workbook.inspect({
    kind: "table",
    range: `${sheetName}!${range}`,
    tableMaxRows: 4,
    tableMaxCols: 13,
    tableMaxCellChars: 120,
    maxChars: 3500,
  });
  console.log(result.ndjson);
}

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "final formula error scan",
  maxChars: 3000,
});
console.log(errors.ndjson);
