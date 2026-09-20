import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const base = 'C:/Python/tesis/codigos/outputs/revision_datos_20260919';
const source = `${base}/revision_catalogo_cobertura_sin_ceros.xlsx`;
const target = `${base}/revision_catalogo_cobertura_trazada.xlsx`;
const work = 'C:/Python/tesis/codigos/.artifact_work/catalog_evidence';
const evidencePath = `${base}/evidencias_catalogo.json`;
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(source));
const sheet = workbook.worksheets.getItem('Catalogo');

async function render(label) {
  for (const [suffix, range] of [['principal', 'A1:J10'], ['ceros', 'E315:J321']]) {
    const png = await workbook.render({sheetName: 'Catalogo', range, scale: 1.2, format: 'png'});
    await fs.writeFile(`${work}/${label}_${suffix}.png`, new Uint8Array(await png.arrayBuffer()));
  }
}

if (process.argv.includes('--preview')) {
  await render('antes');
  console.log('Vista previa creada.');
} else {
  const {evidencias} = JSON.parse(await fs.readFile(evidencePath, 'utf8'));
  if (evidencias.length !== 319) throw new Error('Número inesperado de evidencias.');
  for (const item of evidencias) {
    sheet.getRange(`H${item.fila_catalogo}`).values = [[item.evidencia_catalogo]];
    sheet.getRange(`J${item.fila_catalogo}`).values = [[false]];
  }
  sheet.getRange('H2:H320').format.wrapText = true;
  sheet.getRange('H2:H320').format.autofitRows();
  const check = await workbook.inspect({kind: 'table', sheetId: 'Catalogo', range: 'E1:J7', include: 'values,formulas', tableMaxRows: 7, tableMaxCols: 6, maxChars: 6500});
  console.log(check.ndjson);
  const errors = await workbook.inspect({kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: {useRegex: true, maxResults: 100}, summary: 'Revisión de errores de fórmula'});
  console.log(errors.ndjson);
  await render('despues');
  const blob = await SpreadsheetFile.exportXlsx(workbook);
  await blob.save(target);
  console.log(`Guardado: ${target}`);
}
