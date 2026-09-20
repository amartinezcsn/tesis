import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = process.cwd();
const outputDir = path.join(root, 'outputs', 'revision_datos_20260919');
const payload = JSON.parse(await fs.readFile(path.join(outputDir, '_datos_revision.json'), 'utf8'));
const workbook = Workbook.create();

function writeSheet(name, headers, rows, widths, tableName) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  sheet.getRangeByIndexes(0, 0, rows.length + 1, headers.length).values = [headers, ...rows];
  sheet.getRangeByIndexes(0, 0, 1, headers.length).format = {
    fill: '#243B53',
    font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' },
  };
  sheet.getRangeByIndexes(1, 0, rows.length, headers.length).format.font = { name: 'Arial', size: 10 };
  widths.forEach((width, index) => {
    sheet.getRangeByIndexes(0, index, rows.length + 1, 1).format.columnWidth = width;
  });
  sheet.freezePanes.freezeRows(1);
  sheet.tables.add(`A1:${String.fromCharCode(64 + headers.length)}${rows.length + 1}`, true, tableName);
  return sheet;
}

const catalogHeaders = [
  'descripcion_normalizada', 'clasificacion_original', 'registros', 'importe_nominal_MXN',
  'decision', 'insumo_id', 'aprobado', 'evidencia', 'clasificacion_analitica', 'pendiente',
];
const catalogRows = payload.catalog.map((row) => [
  row.descripcion_normalizada, row.clasificacion_original, Number(row.registros),
  Number(row.importe_nominal), row.decision, row.insumo_id || '', Boolean(row.aprobado),
  row.evidencia || '', row.clasificacion_analitica || '', Boolean(row.pendiente),
]);
const catalog = writeSheet('Catalogo', catalogHeaders, catalogRows,
  [31, 29, 12, 20, 14, 31, 12, 64, 30, 12], 'CatalogoRevision');
catalog.getRange(`C2:C${catalogRows.length + 1}`).setNumberFormat('#,##0');
catalog.getRange(`D2:D${catalogRows.length + 1}`).setNumberFormat('#,##0.00');
catalog.getRange(`E2:I${payload.summary.pending + 1}`).format.fill = '#FFF2CC';
catalog.getRange(`E2:E${catalogRows.length + 1}`).dataValidation = {
  rule: { type: 'list', values: ['incluir', 'excluir', 'revisar'] },
};

const coverageHeaders = [
  'semana_inicio', 'registros_detectados', 'importe_registrado_MXN', 'articulos_con_cero',
  'estado', 'evidencia', 'fecha_revision',
];
const coverageRows = payload.coverage.map((row) => [
  new Date(`${row.semana_inicio}T00:00:00Z`), Number(row.registros_detectados),
  Number(row.importe_registrado), Number(row.articulos_con_cero), row.estado,
  row.evidencia, row.fecha_revision,
]);
const coverage = writeSheet('Cobertura', coverageHeaders, coverageRows,
  [17, 20, 24, 20, 22, 70, 19], 'CoberturaRevision');
coverage.getRange(`A2:A${coverageRows.length + 1}`).setNumberFormat('yyyy-mm-dd');
coverage.getRange(`B2:B${coverageRows.length + 1}`).setNumberFormat('#,##0');
coverage.getRange(`C2:C${coverageRows.length + 1}`).setNumberFormat('#,##0.00');
coverage.getRange(`D2:D${coverageRows.length + 1}`).setNumberFormat('#,##0');
coverage.getRange(`E2:G${coverageRows.length + 1}`).format.fill = '#FFF2CC';
coverage.getRange(`E2:E${coverageRows.length + 1}`).dataValidation = {
  rule: { type: 'list', values: ['registrada', 'observada', 'cero_confirmado', 'incierta', 'incompleta', 'desconocida'] },
};

const notes = workbook.worksheets.add('Instrucciones');
notes.showGridLines = false;
notes.getRange('A1:B9').values = [
  ['Tema', 'Criterio'],
  ['Fuente', 'Compras.xlsx, hoja Hoja1; importes nominales en MXN.'],
  ['SHA-256', payload.source_sha256],
  ['Duplicados', 'Se conservan los 12 registros idénticos por decisión del usuario.'],
  ['Catálogo', 'Resolver cada fila pendiente: incluir o excluir, indicar insumo_id cuando se incluye, aprobar y documentar evidencia.'],
  ['Cobertura', 'Cada lunes requiere estado. Los estados utilizables exigen evidencia y fecha; las semanas inciertas permanecen ausentes.'],
  ['Sin registros', 'Confirmar cero solo si existe evidencia de que se registraron todas las compras de la semana.'],
  ['Cero por artículo', 'La semana del 2023-08-28 tiene cinco renglones con importe cero; requieren revisión de la fuente.'],
  ['Uso', 'Este libro organiza la revisión. No autoriza entrenamiento hasta completar y validar ambas tablas.'],
];
notes.getRange('A1:B1').format = {
  fill: '#243B53', font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' },
};
notes.getRange('A2:B9').format.font = { name: 'Arial', size: 10 };
notes.getRange('A1:A9').format.columnWidth = 23;
notes.getRange('B1:B9').format.columnWidth = 105;
notes.getRange('B2:B9').format.wrapText = true;

for (const [sheetName, range] of [['Catalogo', 'A1:J8'], ['Cobertura', 'A1:G8'], ['Instrucciones', 'A1:B9']]) {
  const result = await workbook.inspect({ kind: 'table', range: `${sheetName}!${range}`, include: 'values,formulas', tableMaxRows: 10, tableMaxCols: 10, maxChars: 2200 });
  console.log(sheetName, result.ndjson);
  const preview = await workbook.render({ sheetName, range, scale: 1.2, format: 'png' });
  await fs.writeFile(path.join(root, '.artifact_work', 'revision_datos_20260919', `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}
const errors = await workbook.inspect({
  kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',
  options: { useRegex: true, maxResults: 50 }, summary: 'final formula error scan', maxChars: 1000,
});
console.log('errors', errors.ndjson);
const exportFile = await SpreadsheetFile.exportXlsx(workbook);
await exportFile.save(path.join(outputDir, 'revision_catalogo_cobertura.xlsx'));
