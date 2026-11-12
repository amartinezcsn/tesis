import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const workspaceDir = "C:/Python/tesis";
const SKILL_DIR = "C:/Users/ramartinez/.codex/plugins/cache/openai-primary-runtime/presentations/26.1111.10930/skills/presentations";
const RUNTIME_PYTHON = "C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1111-570-0_26.1111.570.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe";
const artifactPath = "C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1111-570-0_26.1111.570.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const { FileBlob, PresentationFile } = await import(pathToFileURL(artifactPath).href);
const { finalizePresentation, makeNativeBulletParagraphs } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
);

const inputPath = path.join(workspaceDir, "outputs/defensa_tesis/Defensa_Tesis_Rev68_Plantilla_2026_v2.pptx");
const templatePath = path.join(workspaceDir, "Plantilla_2026.pptx");
const sourceDocx = path.join(workspaceDir, "documentacion/TESIS_OCT2026_Rev68_(ZUJ)_Final.docx");
const buildDir = path.join(workspaceDir, ".pptx_build/defense_v4_index");
const renderDir = path.join(buildDir, "renders");
const stagingDir = path.join(buildDir, "finalizer");
const FINAL_PPTX = path.join(workspaceDir, "outputs/defensa_tesis/Defensa_Tesis_Rev68_Indice_Original_v4.pptx");

const FONT = "Arial";
const BLACK = "#111111";
const GRAY = "#5B6573";
const LIGHT_GRAY = "#E8EAED";
const PURPLE = "#701C7F";
const BLUE = "#4472C4";

await fs.mkdir(renderDir, { recursive: true });
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

const presentation = await PresentationFile.importPptx(await FileBlob.load(inputPath));

function addText(slide, text, position, style = {}, name = undefined) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = { typeface: FONT, fontSize: 24, color: BLACK, ...style };
  shape.text.insets = style.insets ?? { top: 4, right: 6, bottom: 4, left: 6 };
  return shape;
}

function addRule(slide, top, color = PURPLE, left = 88, width = 1104, thickness = 3) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height: thickness },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
}

function addTitle(slide, title, subtitle = undefined) {
  addText(slide, title, { left: 88, top: 112, width: 1104, height: 62 }, {
    fontSize: 36, bold: true, color: BLACK, verticalAlignment: "middle",
  }, "slide-title");
  if (subtitle) {
    addText(slide, subtitle, { left: 90, top: 169, width: 1098, height: 34 }, {
      fontSize: 18, color: GRAY, verticalAlignment: "middle",
    }, "slide-subtitle");
  }
}

function addBullets(slide, items, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = makeNativeBulletParagraphs(items, {
    marginLeftPoints: options.marginLeftPoints ?? 18,
    hangingPoints: options.hangingPoints ?? 9,
    spaceAfterPoints: options.spaceAfterPoints ?? 10,
  });
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 24,
    color: options.color ?? BLACK,
    autoFit: "none",
  };
  shape.text.insets = { top: 8, right: 8, bottom: 8, left: 8 };
  return shape;
}

async function layoutOf(slide) {
  return JSON.parse(await (await slide.export({ format: "layout", detail: "full" })).text());
}

async function clearSlide(slide) {
  const layout = await layoutOf(slide);
  const deleteIds = [];
  for (const element of layout.elements ?? []) {
    const p = element.position ?? {};
    const isHeaderLogo = element.kind === "image" && (p.top ?? 999) < 105 && (p.height ?? 999) < 110;
    if (!isHeaderLogo && element.editable !== false) deleteIds.push(element.id);
  }
  if (deleteIds.length) presentation.delete(deleteIds);
}

async function setNamedText(slide, name, text) {
  const layout = await layoutOf(slide);
  const target = (layout.elements ?? []).find((element) => element.name === name);
  if (target) {
    presentation.resolve(target.id).text = text;
    return true;
  }
  return false;
}

async function setSectionTitle(slide, title, subtitle) {
  const layout = await layoutOf(slide);
  const titleElement = (layout.elements ?? []).find((element) => element.name === "slide-title");
  const subtitleElement = (layout.elements ?? []).find((element) => element.name === "slide-subtitle");
  if (titleElement) {
    const titleShape = presentation.resolve(titleElement.id);
    titleShape.text = title;
    titleShape.position = { left: 88, top: 112, width: 1104, height: 62 };
  } else {
    addTitle(slide, title, subtitle);
  }
  if (subtitleElement && subtitle) {
    const subtitleShape = presentation.resolve(subtitleElement.id);
    subtitleShape.text = subtitle;
    subtitleShape.position = { left: 90, top: 158, width: 1098, height: 28 };
  } else if (subtitle && !titleElement) {
    // addTitle already added the subtitle.
  } else if (subtitle) {
    addText(slide, subtitle, { left: 90, top: 158, width: 1098, height: 28 }, { fontSize: 18, color: GRAY }, "slide-subtitle");
  }
}

const original = [...presentation.slides.items];
if (original.length !== 23) throw new Error(`Expected 23 source slides, found ${original.length}`);

const [cover, indexSlide, intro, problem, question, hypothesis, objectives, justification, theory, methodology, development, modelFamilies, architecture, validation, metrics, quality, resultError, resultCompare, resultComposition, h1Result, dss, conclusions, close] = original;

// Separate the combined objectives slide into two slides.
const specificObjectives = objectives.duplicate();
await clearSlide(objectives);
await clearSlide(specificObjectives);

addTitle(objectives, "Objetivo general");
addRule(objectives, 182);
addText(objectives, "Determinar en qué medida un modelo híbrido de métodos estadísticos y aprendizaje automático reduce, frente a modelos de referencia y mediante validación temporal, el error fuera de muestra del importe semanal de compras elegibles y de su distribución porcentual por insumo.", { left: 170, top: 245, width: 940, height: 235 }, {
  fontSize: 31, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle",
});
addText(objectives, "Caso Cup&Cake · horizontes de una a cuatro semanas · evaluación temporal", { left: 245, top: 515, width: 790, height: 60 }, {
  fontSize: 21, color: GRAY, alignment: "center", verticalAlignment: "middle",
});
objectives.speakerNotes.text = `Fuente: ${sourceDocx}, párrafo 224.`;

addTitle(specificObjectives, "Objetivos específicos");
addRule(specificObjectives, 182);
addBullets(specificObjectives, [
  "Depurar e integrar las fuentes disponibles en un panel semanal",
  "Implementar referencias, modelos estadísticos, aprendizaje automático e híbridos",
  "Estimar la distribución porcentual por insumo y verificar la conciliación",
  "Comparar el desempeño mediante validación temporal con los mismos periodos y horizontes",
], { left: 180, top: 245, width: 920, height: 300 }, { fontSize: 27, color: BLACK, spaceAfterPoints: 13 });
specificObjectives.speakerNotes.text = `Fuente: ${sourceDocx}, párrafos 225 a 229.`;

// Restore the original 12-part index and its order.
await clearSlide(indexSlide);
addTitle(indexSlide, "Índice");
addRule(indexSlide, 182);
const indexItems = [
  "Introducción",
  "Planteamiento del problema",
  "Pregunta de investigación",
  "Objetivo general",
  "Justificación",
  "Objetivos específicos",
  "Hipótesis",
  "Marco teórico",
  "Metodología",
  "Desarrollo",
  "Resultados y hallazgos",
  "Conclusiones",
];
for (let i = 0; i < indexItems.length; i++) {
  const col = i % 3;
  const row = Math.floor(i / 3);
  const left = 88 + col * 373;
  const top = 218 + row * 100;
  addText(indexSlide, String(i + 1).padStart(2, "0"), { left, top, width: 68, height: 42 }, {
    fontSize: 27, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle",
  });
  addText(indexSlide, indexItems[i], { left: left + 76, top, width: 275, height: 48 }, {
    fontSize: 18, bold: true, color: BLACK, verticalAlignment: "middle",
  });
  addRule(indexSlide, top + 58, LIGHT_GRAY, left, 345, 1.5);
}
indexSlide.speakerNotes.text = "Índice original de la plantilla, conservado en el mismo orden.";

// Use the original section names on the corresponding content slides.
await setSectionTitle(intro, "Introducción", "Contexto del caso de estudio");
await setSectionTitle(justification, "Justificación", "Aportación práctica y metodológica");
await setSectionTitle(theory, "Marco teórico", "Demanda intermitente, datos limitados y comparación por horizonte");
await setSectionTitle(methodology, "Metodología", "Diseño longitudinal, retrospectivo y evaluativo exploratorio");
await setSectionTitle(development, "Desarrollo", "Pipeline metodológico y trazabilidad de la corrida");
await setSectionTitle(resultError, "Resultados y hallazgos", "Error del modelo híbrido por horizonte");

// Reorder slides to match the original index.
presentation.slides.reorder([
  cover.id,
  indexSlide.id,
  intro.id,
  problem.id,
  question.id,
  objectives.id,
  justification.id,
  specificObjectives.id,
  hypothesis.id,
  theory.id,
  methodology.id,
  development.id,
  modelFamilies.id,
  architecture.id,
  validation.id,
  metrics.id,
  quality.id,
  resultError.id,
  resultCompare.id,
  resultComposition.id,
  h1Result.id,
  dss.id,
  conclusions.id,
  close.id,
]);

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

const content = await presentation.inspect({
  select: "$.slides[*]",
  include: ["id", "index", "layout", "title", "elements.id", "elements.kind", "elements.name", "elements.text", "notes.text"],
});
await fs.writeFile(path.join(buildDir, "content.ndjson"), content.ndjson);

for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(renderDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
  await fs.writeFile(path.join(renderDir, `${stem}.layout.json`), await (await slide.export({ format: "layout", detail: "full" })).text());
}
await writeBlob(path.join(buildDir, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 0.5 }));

const candidatePath = path.join(stagingDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const requirements = {
  explicitTotalSlideCount: 24,
  requiredNativeTableOwnerSlides: [13, 17],
  requiredNativeChartOwnerSlides: [18, 19, 20],
  requiredEmbeddedWorkbookChartOwnerSlides: [],
  materializeLiteralChartWorkbooks: true,
  nativeChartTargetApplication: "powerpoint",
};
const fontPolicy = {
  basis: "reference",
  families: ["Arial"],
  referencePath: templatePath,
  referenceSha256: "f81fac59e4dd432d8b38a9b0e19a43fc3aa4c4bb6bc3408262309feb345c9964",
};
const tableOwners = requirements.requiredNativeTableOwnerSlides;
const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    ...tableOwners.flatMap((number) => ["--require-native-table-slide", String(number)]),
  ],
  requiredNativeTableOwnerSlides: tableOwners,
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, `${path.basename(FINAL_PPTX)}.validation.json`),
});

console.log(JSON.stringify({ finalPath: FINAL_PPTX, validation: result }, null, 2));
