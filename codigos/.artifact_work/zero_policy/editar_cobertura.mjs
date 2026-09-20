import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const base = 'C:/Python/tesis/codigos/outputs/revision_datos_20260919';
const source = `${base}/revision_catalogo_cobertura_con_ids.xlsx`;
const target = `${base}/revision_catalogo_cobertura_sin_ceros.xlsx`;
const work = 'C:/Python/tesis/codigos/.artifact_work/zero_policy';
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(source));
const sheet = workbook.worksheets.getItem('Cobertura');

async function render(name) {
  for (const [suffix, range] of [['agosto', 'A118:G126'], ['enero', 'A138:G143']]) {
    const png = await workbook.render({sheetName: 'Cobertura', range, scale: 1.4, format: 'png'});
    await fs.writeFile(`${work}/${name}_${suffix}.png`, new Uint8Array(await png.arrayBuffer()));
  }
}

if (process.argv.includes('--preview')) {
  await render('cobertura_antes');
  console.log('Vista previa creada.');
} else {
  sheet.getRange('E123:F123').values = [[
    'incierta',
    'Decisión del usuario: ningún importe cero es válido. Filas 512, 516, 517, 518 y 519 de Compras.xlsx con importe cero; semana excluida del modelado hasta corregir la fuente.',
  ]];
  sheet.getRange('E141:F141').values = [[
    'incierta',
    'Decisión del usuario: no aceptar objetivos cero. Sólo consta peaje excluido en la fila 250 de Compras.xlsx; no hay compras de insumos incluidas que acrediten cero semanal.',
  ]];
  const check = await workbook.inspect({kind: 'table', sheetId: 'Cobertura', range: 'A120:G125', include: 'values,formulas', tableMaxRows: 6, tableMaxCols: 7, maxChars: 5000});
  console.log(check.ndjson);
  const errors = await workbook.inspect({kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: {useRegex: true, maxResults: 100}, summary: 'Revisión de errores de fórmula'});
  console.log(errors.ndjson);
  await render('cobertura_sin_ceros');
  const blob = await SpreadsheetFile.exportXlsx(workbook);
  await blob.save(target);
  console.log(`Guardado: ${target}`);
}
