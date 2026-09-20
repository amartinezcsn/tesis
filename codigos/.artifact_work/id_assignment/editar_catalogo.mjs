import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const base = 'C:/Python/tesis/codigos/outputs/revision_datos_20260919';
const source = `${base}/revision_catalogo_cobertura.xlsx`;
const target = `${base}/revision_catalogo_cobertura_con_ids.xlsx`;
const previewDir = 'C:/Python/tesis/codigos/.artifact_work/id_assignment';
const assignmentsPath = `${base}/asignaciones_insumo_id.json`;

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(source));
const sheet = workbook.worksheets.getItem('Catalogo');

async function render(name) {
  const preview = await workbook.render({sheetName: 'Catalogo', range: 'A1:J12', scale: 1.2, format: 'png'});
  await fs.writeFile(`${previewDir}/${name}`, new Uint8Array(await preview.arrayBuffer()));
}

if (process.argv.includes('--preview')) {
  await render('catalogo_antes.png');
  console.log('Vista previa creada.');
} else {
  const {asignaciones} = JSON.parse(await fs.readFile(assignmentsPath, 'utf8'));
  for (const item of asignaciones) {
    sheet.getRange(`F${item.fila_excel}`).values = [[item.insumo_id]];
  }
  const check = await workbook.inspect({kind: 'table', sheetId: 'Catalogo', range: 'A1:J12', include: 'values,formulas', tableMaxRows: 12, tableMaxCols: 10, maxChars: 8000});
  console.log(check.ndjson);
  const errors = await workbook.inspect({kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: {useRegex: true, maxResults: 100}, summary: 'Revisión de errores de fórmula'});
  console.log(errors.ndjson);
  await render('catalogo_con_ids.png');
  const blob = await SpreadsheetFile.exportXlsx(workbook);
  await blob.save(target);
  console.log(`Guardado: ${target}`);
}
