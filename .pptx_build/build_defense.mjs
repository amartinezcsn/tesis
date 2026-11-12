import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const workspaceDir = "C:/Python/tesis";
const SKILL_DIR = "C:/Users/ramartinez/.codex/plugins/cache/openai-primary-runtime/presentations/26.1111.10930/skills/presentations";
const RUNTIME_PYTHON = "C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1111-570-0_26.1111.570.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe";
const artifactPath = "C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1111-570-0_26.1111.570.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const { FileBlob, PresentationFile } = await import(pathToFileURL(artifactPath).href);
const { finalizePresentation, makeNativeBulletParagraphs, applyPresentationChartFont } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
);

const templatePath = path.join(workspaceDir, "Plantilla_2026.pptx");
const sourceDocx = path.join(workspaceDir, "documentacion/TESIS_OCT2026_Rev68_(ZUJ)_Final.docx");
const buildDir = path.join(workspaceDir, ".pptx_build/defense_v2");
const renderDir = path.join(buildDir, "renders");
const stagingDir = path.join(buildDir, "finalizer");
const FINAL_PPTX = path.join(workspaceDir, "outputs/defensa_tesis/Defensa_Tesis_Rev68_Plantilla_2026_v2.pptx");

const W = 1280;
const H = 720;
const FONT = "Arial";
const BLACK = "#111111";
const GRAY = "#5B6573";
const LIGHT_GRAY = "#E8EAED";
const PURPLE = "#701C7F";
const PURPLE_2 = "#8D3A98";
const PURPLE_LIGHT = "#F4EAF6";
const BLUE = "#4472C4";
const BLUE_LIGHT = "#E9F0FA";
const GREEN = "#2F7D32";
const GREEN_LIGHT = "#EAF4EA";
const AMBER = "#C87500";
const AMBER_LIGHT = "#FFF2DD";
const RED = "#B42A25";
const RED_LIGHT = "#FBE8E7";
const WHITE = "#FFFFFF";

await fs.mkdir(renderDir, { recursive: true });
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

const presentation = await PresentationFile.importPptx(await FileBlob.load(templatePath));

async function clearSlide(slide) {
  const blob = await slide.export({ format: "layout", detail: "full" });
  const layout = JSON.parse(await blob.text());
  const deleteIds = [];
  for (const element of layout.elements ?? []) {
    const p = element.position ?? {};
    const isHeaderLogo = element.kind === "image" && (p.top ?? 999) < 105 && (p.height ?? 999) < 110;
    if (!isHeaderLogo && element.editable !== false) deleteIds.push(element.id);
  }
  if (deleteIds.length) presentation.delete(deleteIds);
}

function addText(slide, text, position, style = {}, name = undefined) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: 24,
    color: BLACK,
    ...style,
  };
  shape.text.insets = style.insets ?? { top: 4, right: 6, bottom: 4, left: 6 };
  return shape;
}

function addTitle(slide, title, subtitle = undefined) {
  addText(slide, title, { left: 88, top: 112, width: 1104, height: 62 }, {
    fontSize: 36,
    bold: true,
    color: BLACK,
    verticalAlignment: "middle",
  }, "slide-title");
  if (subtitle) {
    addText(slide, subtitle, { left: 90, top: 169, width: 1098, height: 34 }, {
      fontSize: 18,
      color: GRAY,
      verticalAlignment: "middle",
    }, "slide-subtitle");
  }
}

function addRule(slide, top, color = PURPLE, left = 88, width = 1104, thickness = 3) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height: thickness },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
}

function addBullets(slide, items, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position,
    fill: options.fill ?? "none",
    line: options.line ?? { style: "solid", fill: "none", width: 0 },
  });
  shape.text = makeNativeBulletParagraphs(items, {
    marginLeftPoints: options.marginLeftPoints ?? 18,
    hangingPoints: options.hangingPoints ?? 9,
    spaceAfterPoints: options.spaceAfterPoints ?? 8,
  });
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 24,
    color: options.color ?? BLACK,
    autoFit: "none",
  };
  shape.text.insets = options.insets ?? { top: 8, right: 8, bottom: 8, left: 8 };
  return shape;
}

function addBand(slide, position, fill, line = fill, radius = 10) {
  return slide.shapes.add({
    geometry: "roundRect",
    position,
    fill,
    line: { style: "solid", fill: line, width: 1.5 },
    borderRadius: radius,
  });
}

function addMetric(slide, value, label, left, color = PURPLE) {
  addText(slide, value, { left, top: 246, width: 245, height: 96 }, {
    fontSize: 44,
    bold: true,
    color,
    alignment: "center",
    verticalAlignment: "middle",
  });
  addText(slide, label, { left, top: 338, width: 245, height: 74 }, {
    fontSize: 19,
    color: GRAY,
    alignment: "center",
    verticalAlignment: "top",
  });
}

function addStage(slide, label, left, top, width, height, fill, line, number) {
  const box = addBand(slide, { left, top, width, height }, fill, line, 12);
  addText(slide, String(number).padStart(2, "0"), { left: left + 12, top: top + 10, width: 46, height: 30 }, {
    fontSize: 16, bold: true, color: line, alignment: "center", verticalAlignment: "middle",
  });
  addText(slide, label, { left: left + 16, top: top + 48, width: width - 32, height: height - 62 }, {
    fontSize: 20, bold: true, color: BLACK, alignment: "center", verticalAlignment: "middle",
  });
  return box;
}

function addArrow(slide, from, to, color = GRAY, fromSide = "right", toSide = "left") {
  return slide.shapes.connect(from, to, {
    kind: "straight",
    fromSide,
    toSide,
    line: { style: "solid", fill: color, width: 2.5 },
    tail: { type: "triangle", width: "sm", length: "sm" },
  });
}

for (const slide of presentation.slides.items) await clearSlide(slide);

const slides = presentation.slides.items;

// 1. Portada
{
  const s = slides[0];
  addText(s, "UNIVERSIDAD POLITÉCNICA METROPOLITANA DE HIDALGO", { left: 150, top: 112, width: 980, height: 40 }, {
    fontSize: 26, bold: true, alignment: "center", color: BLACK,
  });
  addRule(s, 164, PURPLE, 193, 894, 4);
  addText(s, "MODELO HÍBRIDO ESTADÍSTICO Y DE APRENDIZAJE AUTOMÁTICO PARA EL PRONÓSTICO Y LA DISTRIBUCIÓN DEL PRESUPUESTO SEMANAL DE ABASTECIMIENTO", { left: 170, top: 190, width: 940, height: 168 }, {
    fontSize: 31, bold: true, alignment: "center", verticalAlignment: "middle", color: BLACK,
  });
  addText(s, "Estudio de caso en una microempresa de repostería creativa en Tizayuca, Hidalgo", { left: 235, top: 368, width: 810, height: 66 }, {
    fontSize: 22, alignment: "center", verticalAlignment: "middle", color: PURPLE,
  });
  addText(s, "Defensa de tesis para obtener el grado de Maestro en Inteligencia Artificial", { left: 240, top: 448, width: 800, height: 50 }, {
    fontSize: 19, alignment: "center", color: GRAY,
  });
  addText(s, "Rodrigo Adrián Martínez Flores", { left: 105, top: 548, width: 520, height: 40 }, {
    fontSize: 23, bold: true,
  });
  addText(s, "Director de tesis: Luis Eduardo Urban Rivero", { left: 105, top: 590, width: 650, height: 34 }, {
    fontSize: 18, color: GRAY,
  });
  addText(s, "Tolcayuca, Hidalgo · 2026", { left: 880, top: 584, width: 295, height: 40 }, {
    fontSize: 18, alignment: "right", color: GRAY,
  });
  s.speakerNotes.text = `Fuente principal: ${sourceDocx}, portada y resumen, revisión 68.`;
}

// 2. Índice
{
  const s = slides[1];
  addTitle(s, "Índice");
  addRule(s, 182);
  const sections = [
    ["01", "Problema y pregunta"],
    ["02", "Hipótesis y objetivos"],
    ["03", "Fundamentos"],
    ["04", "Metodología"],
    ["05", "Resultados"],
    ["06", "Conclusiones y aplicación"],
  ];
  for (let i = 0; i < sections.length; i++) {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const left = 100 + col * 375;
    const top = 230 + row * 175;
    addText(s, sections[i][0], { left, top, width: 86, height: 62 }, {
      fontSize: 42, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle",
    });
    addText(s, sections[i][1], { left: left + 92, top: top + 4, width: 255, height: 56 }, {
      fontSize: 22, bold: true, color: BLACK, verticalAlignment: "middle",
    });
    addRule(s, top + 78, LIGHT_GRAY, left, 335, 2);
  }
  s.speakerNotes.text = "Recorrido de la defensa: problema, evidencia y alcance de las conclusiones.";
}

// 3. Contexto
{
  const s = slides[2];
  addTitle(s, "Contexto del caso de estudio", "Cup&Cake, microempresa de repostería creativa en Tizayuca, Hidalgo");
  addRule(s, 202);
  addMetric(s, "Semanal", "Unidad de análisis del presupuesto de abastecimiento", 105, PURPLE);
  addMetric(s, "1 a 4", "Horizontes directos de pronóstico, expresados en semanas", 390, BLUE);
  addMetric(s, "2016–2026", "Periodo disponible en los registros integrados", 675, GREEN);
  addMetric(s, "MXN + %", "Importe total y distribución por insumo", 960, AMBER);
  addText(s, "La decisión operativa requiere estimar cuánto comprar y cómo distribuir el presupuesto entre insumos, sin sustituir el criterio del responsable del negocio.", { left: 170, top: 490, width: 940, height: 92 }, {
    fontSize: 24, color: BLACK, alignment: "center", verticalAlignment: "middle",
  });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, párrafos 183, 211 a 215 y 426 a 430.`;
}

// 4. Problema
{
  const s = slides[3];
  addTitle(s, "Problema de planeación", "La incertidumbre afecta el importe total y la mezcla de insumos");
  addRule(s, 202);
  addText(s, "Registros históricos", { left: 110, top: 250, width: 300, height: 46 }, { fontSize: 25, bold: true, color: BLUE });
  addBullets(s, [
    "Compras y ventas con cobertura irregular",
    "Fechas comerciales y calendario disponibles al origen",
    "Semanas sin cobertura tratadas como datos ausentes",
  ], { left: 100, top: 305, width: 380, height: 240 }, { fontSize: 21, color: BLACK });
  addText(s, "Necesidad de decisión", { left: 500, top: 250, width: 300, height: 46 }, { fontSize: 25, bold: true, color: PURPLE });
  addBullets(s, [
    "Reservar presupuesto de abastecimiento de corto plazo",
    "Distribuir el total entre categorías elegibles",
    "Revisar el resultado antes de emitir una compra",
  ], { left: 490, top: 305, width: 380, height: 240 }, { fontSize: 21, color: BLACK });
  addText(s, "Riesgo metodológico", { left: 890, top: 250, width: 300, height: 46 }, { fontSize: 25, bold: true, color: RED });
  addBullets(s, [
    "Pocos orígenes válidos para evaluación",
    "La complejidad puede no superar referencias simples",
    "Una mejora aparente puede depender del horizonte",
  ], { left: 880, top: 305, width: 310, height: 240 }, { fontSize: 21, color: BLACK });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, apartados 1.2 y 4.7.`;
}

// 5. Pregunta
{
  const s = slides[4];
  addTitle(s, "Pregunta de investigación");
  addRule(s, 182);
  addText(s, "¿En qué medida un modelo híbrido reduce, frente a modelos de referencia y mediante validación temporal, el error fuera de muestra del importe semanal de compras elegibles y de su distribución porcentual por insumo?", { left: 155, top: 245, width: 970, height: 210 }, {
    fontSize: 32, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle",
  });
  addText(s, "Alcance evaluado: registros disponibles de 2016 a 2026 y objetivos de evaluación entre marzo y julio de 2025.", { left: 215, top: 500, width: 850, height: 78 }, {
    fontSize: 21, color: GRAY, alignment: "center", verticalAlignment: "middle",
  });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, párrafo 217.`;
}

// 6. Hipótesis
{
  const s = slides[5];
  addTitle(s, "Hipótesis y criterio de evaluación");
  addRule(s, 182);
  addText(s, "H1", { left: 108, top: 230, width: 150, height: 120 }, { fontSize: 64, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle" });
  addText(s, "El modelo híbrido y el procedimiento de distribución porcentual presentarán menores errores fuera de muestra que sus respectivas referencias.", { left: 285, top: 230, width: 865, height: 120 }, { fontSize: 28, bold: true, color: BLACK, verticalAlignment: "middle" });
  addRule(s, 382, LIGHT_GRAY, 120, 1040, 2);
  addText(s, "Importe total", { left: 150, top: 425, width: 280, height: 42 }, { fontSize: 24, bold: true, color: BLUE, alignment: "center" });
  addText(s, "Comparación por horizonte mediante MAE y RMSE", { left: 145, top: 472, width: 290, height: 86 }, { fontSize: 21, color: GRAY, alignment: "center", verticalAlignment: "middle" });
  addText(s, "+", { left: 465, top: 455, width: 70, height: 70 }, { fontSize: 42, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle" });
  addText(s, "Composición", { left: 565, top: 425, width: 280, height: 42 }, { fontSize: 24, bold: true, color: GREEN, alignment: "center" });
  addText(s, "Error absoluto medio en puntos porcentuales", { left: 560, top: 472, width: 290, height: 86 }, { fontSize: 21, color: GRAY, alignment: "center", verticalAlignment: "middle" });
  addText(s, "Evidencia conjunta", { left: 930, top: 425, width: 250, height: 42 }, { fontSize: 24, bold: true, color: RED, alignment: "center" });
  addText(s, "Suficiencia de orígenes y estabilidad del resultado", { left: 910, top: 472, width: 290, height: 86 }, { fontSize: 21, color: GRAY, alignment: "center", verticalAlignment: "middle" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, párrafos 219 a 220 y apartados 3.8.6 y 4.6.`;
}

// 7. Objetivos
{
  const s = slides[6];
  addTitle(s, "Objetivos");
  addRule(s, 182);
  addText(s, "Objetivo general", { left: 100, top: 225, width: 300, height: 44 }, { fontSize: 25, bold: true, color: PURPLE });
  addText(s, "Determinar en qué medida el modelo híbrido reduce el error fuera de muestra del importe semanal y de su distribución porcentual por insumo.", { left: 100, top: 278, width: 430, height: 205 }, { fontSize: 25, bold: true, color: BLACK, verticalAlignment: "middle" });
  addRule(s, 515, PURPLE, 100, 430, 4);
  addText(s, "Objetivos específicos", { left: 610, top: 225, width: 330, height: 44 }, { fontSize: 25, bold: true, color: BLUE });
  addBullets(s, [
    "Depurar e integrar las fuentes disponibles en un panel semanal",
    "Implementar referencias, modelos estadísticos, aprendizaje automático e híbridos",
    "Estimar la distribución porcentual por insumo y verificar la conciliación",
    "Comparar el desempeño con validación temporal",
  ], { left: 600, top: 278, width: 570, height: 310 }, { fontSize: 22, color: BLACK });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, párrafos 224 a 229.`;
}

// 8. Justificación
{
  const s = slides[7];
  addTitle(s, "Aportación de la investigación");
  addRule(s, 182);
  const labels = [
    ["Aplicación", "Pronóstico semanal para revisar el presupuesto de abastecimiento", PURPLE, PURPLE_LIGHT],
    ["Método", "Comparación temporal homogénea entre referencias y modelos candidatos", BLUE, BLUE_LIGHT],
    ["Trazabilidad", "Manifiestos, particiones y controles que permiten reproducir la corrida", GREEN, GREEN_LIGHT],
    ["Gobernanza", "La salida apoya la decisión y no autoriza compras automáticas", AMBER, AMBER_LIGHT],
  ];
  for (let i = 0; i < labels.length; i++) {
    const top = 230 + i * 94;
    addText(s, labels[i][0], { left: 115, top, width: 210, height: 54 }, { fontSize: 24, bold: true, color: labels[i][2], verticalAlignment: "middle" });
    addText(s, labels[i][1], { left: 345, top, width: 805, height: 54 }, { fontSize: 22, color: BLACK, verticalAlignment: "middle" });
    addRule(s, top + 66, LIGHT_GRAY, 115, 1035, 1.5);
  }
  s.speakerNotes.text = `Fuente: ${sourceDocx}, apartados 1.5, 3.9.8 y 4.8.3.`;
}

// 9. Fundamentos
{
  const s = slides[8];
  addTitle(s, "Fundamentos del enfoque", "Demanda intermitente, datos limitados y comparación por horizonte");
  addRule(s, 202);
  const x = [120, 410, 700, 990];
  const items = [
    ["Referencias simples", "Último valor, promedio móvil y referencia estacional", BLUE],
    ["Modelos parsimoniosos", "SES, Holt, ARIMA, Ridge y árboles", PURPLE],
    ["Integración híbrida", "Ponderación y corrección de residuos por horizonte", GREEN],
    ["Evaluación temporal", "El entrenamiento precede siempre a la semana evaluada", AMBER],
  ];
  for (let i = 0; i < items.length; i++) {
    addText(s, String(i + 1), { left: x[i], top: 245, width: 70, height: 70 }, { fontSize: 40, bold: true, color: items[i][2], alignment: "center", verticalAlignment: "middle" });
    addText(s, items[i][0], { left: x[i] - 55, top: 330, width: 180, height: 62 }, { fontSize: 22, bold: true, alignment: "center", color: BLACK, verticalAlignment: "middle" });
    addText(s, items[i][1], { left: x[i] - 80, top: 405, width: 230, height: 115 }, { fontSize: 19, alignment: "center", color: GRAY, verticalAlignment: "top" });
  }
  addText(s, "La tesis evalúa una MLP pequeña. RNN, LSTM, Prophet y modelos log-ratio no forman parte de la corrida final.", { left: 230, top: 560, width: 820, height: 48 }, { fontSize: 20, color: RED, alignment: "center", verticalAlignment: "middle" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, tabla 31 y apartados 2.4 a 2.9.`;
}

// 10. Diseño
{
  const s = slides[9];
  addTitle(s, "Diseño del estudio");
  addRule(s, 182);
  addText(s, "Longitudinal y retrospectivo", { left: 110, top: 235, width: 475, height: 58 }, { fontSize: 30, bold: true, color: PURPLE });
  addText(s, "Evaluación exploratoria fuera de muestra con registros históricos del caso de estudio.", { left: 110, top: 305, width: 460, height: 100 }, { fontSize: 23, color: BLACK });
  addText(s, "No experimental", { left: 110, top: 445, width: 475, height: 58 }, { fontSize: 30, bold: true, color: BLUE });
  addText(s, "No se manipulan las operaciones del negocio. Se comparan procedimientos sobre los mismos periodos.", { left: 110, top: 515, width: 460, height: 100 }, { fontSize: 23, color: BLACK });
  addText(s, "Unidad y alcance", { left: 680, top: 235, width: 450, height: 58 }, { fontSize: 30, bold: true, color: GREEN });
  addBullets(s, [
    "Panel semanal de compras elegibles",
    "Variables históricas de ventas y calendario disponibles al origen",
    "Ventana de entrenamiento fija de 52 semanas",
    "Horizontes directos de una a cuatro semanas",
    "Seis orígenes monetarios válidos por horizonte",
  ], { left: 665, top: 305, width: 500, height: 300 }, { fontSize: 22, color: BLACK });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, apartados 3.1 a 3.7 y párrafo 568.`;
}

// 11. Pipeline
{
  const s = slides[10];
  addTitle(s, "Pipeline metodológico");
  addRule(s, 182);
  const stages = [
    ["Auditoría de fuentes", BLUE_LIGHT, BLUE],
    ["Panel semanal", BLUE_LIGHT, BLUE],
    ["Características disponibles al origen", PURPLE_LIGHT, PURPLE],
    ["Selección interna por horizonte", GREEN_LIGHT, GREEN],
    ["Evaluación final y asignación", AMBER_LIGHT, AMBER],
  ];
  const boxes = [];
  for (let i = 0; i < stages.length; i++) boxes.push(addStage(s, stages[i][0], 75 + i * 240, 265, 205, 190, stages[i][1], stages[i][2], i + 1));
  for (let i = 0; i < boxes.length - 1; i++) addArrow(s, boxes[i], boxes[i + 1]);
  addText(s, "Cada transformación conserva fuente, fecha, cobertura, parámetros y particiones para reproducir la corrida.", { left: 180, top: 510, width: 920, height: 62 }, { fontSize: 22, color: GRAY, alignment: "center", verticalAlignment: "middle" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, apartados 3.8 y 3.9.`;
}

// 12. Modelos (tabla nativa)
{
  const s = slides[11];
  addTitle(s, "Familias de modelos evaluadas");
  addRule(s, 182);
  const values = [
    ["Familia", "Candidatos", "Propósito"],
    ["Referencias", "Último valor, media móvil, estacional", "Medir el valor de la complejidad"],
    ["Estadísticos", "SES, Holt, SARIMAX, ARIMA", "Capturar nivel, tendencia y dependencia"],
    ["Aprendizaje automático", "Ridge, RF, HGB, MLP", "Modelar relaciones regularizadas o no lineales"],
    ["Híbridos", "Pesos y correctores residuales", "Combinar componentes por horizonte"],
    ["Composición", "Histórica y EWM", "Distribuir el total entre insumos"],
  ];
  const table = s.tables.add({ rows: values.length, columns: 3, left: 105, top: 225, width: 1070, height: 350, values, columnWidths: [220, 400, 450] });
  table.borders.assign({ style: "solid", fill: "#D9D9D9", width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: 3 }).assign({ fill: PURPLE, textStyle: { typeface: FONT, fontSize: 20, bold: true, color: WHITE }, margins: { top: 8, right: 8, bottom: 8, left: 8 }, anchor: "middle" });
  table.cells.block({ row: 1, column: 0, rowCount: 5, columnCount: 3 }).assign({ textStyle: { typeface: FONT, fontSize: 17, color: BLACK }, margins: { top: 7, right: 8, bottom: 7, left: 8 }, anchor: "middle" });
  for (let r = 1; r < values.length; r++) if (r % 2 === 0) table.cells.block({ row: r, column: 0, rowCount: 1, columnCount: 3 }).fill = PURPLE_LIGHT;
  addText(s, "No ejecutados en la corrida final: RNN, LSTM, Prophet y modelos log-ratio.", { left: 150, top: 592, width: 980, height: 36 }, { fontSize: 18, color: RED, alignment: "center" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, tabla 31.`;
}

// 13. Arquitectura híbrida
{
  const s = slides[12];
  addTitle(s, "Arquitectura híbrida por horizonte");
  addRule(s, 182);
  const stat = addBand(s, { left: 105, top: 260, width: 250, height: 130 }, BLUE_LIGHT, BLUE, 12);
  addText(s, "Componente estadístico\nSES o ARIMA", { left: 120, top: 285, width: 220, height: 80 }, { fontSize: 24, bold: true, alignment: "center", verticalAlignment: "middle" });
  const ml = addBand(s, { left: 105, top: 440, width: 250, height: 130 }, GREEN_LIGHT, GREEN, 12);
  addText(s, "Componente de ML\nRF, HGB o MLP", { left: 120, top: 465, width: 220, height: 80 }, { fontSize: 24, bold: true, alignment: "center", verticalAlignment: "middle" });
  const combine = addBand(s, { left: 470, top: 340, width: 300, height: 150 }, PURPLE_LIGHT, PURPLE, 12);
  addText(s, "Combinación seleccionada\nPeso estadístico 0.25, 0.50 o 0.75", { left: 490, top: 370, width: 260, height: 92 }, { fontSize: 24, bold: true, alignment: "center", verticalAlignment: "middle" });
  const amount = addBand(s, { left: 890, top: 260, width: 275, height: 130 }, AMBER_LIGHT, AMBER, 12);
  addText(s, "Pronóstico del importe\nno negativo", { left: 910, top: 290, width: 235, height: 70 }, { fontSize: 24, bold: true, alignment: "center", verticalAlignment: "middle" });
  const allocation = addBand(s, { left: 890, top: 440, width: 275, height: 130 }, PURPLE_LIGHT, PURPLE, 12);
  addText(s, "Distribución porcentual\ny conciliación", { left: 910, top: 470, width: 235, height: 70 }, { fontSize: 24, bold: true, alignment: "center", verticalAlignment: "middle" });
  addArrow(s, stat, combine); addArrow(s, ml, combine); addArrow(s, combine, amount); addArrow(s, amount, allocation, GRAY, "bottom", "top");
  s.speakerNotes.text = `Fuente: ${sourceDocx}, párrafos 467 a 471 y ecuaciones 37 a 39.`;
}

// 14. Validación temporal
{
  const s = slides[13];
  addTitle(s, "Validación temporal con ventana deslizante");
  addRule(s, 182);
  addText(s, "52 semanas de entrenamiento", { left: 120, top: 222, width: 610, height: 36 }, { fontSize: 21, bold: true, color: BLUE });
  addText(s, "Evaluación directa", { left: 900, top: 222, width: 250, height: 36 }, { fontSize: 21, bold: true, color: PURPLE, alignment: "center" });
  for (let i = 0; i < 5; i++) {
    const top = 285 + i * 62;
    const offset = i * 52;
    s.shapes.add({ geometry: "rect", position: { left: 120 + offset, top, width: 610, height: 30 }, fill: BLUE_LIGHT, line: { style: "solid", fill: BLUE, width: 1 } });
    s.shapes.add({ geometry: "rect", position: { left: 742 + offset, top, width: 46, height: 30 }, fill: PURPLE, line: { style: "solid", fill: PURPLE, width: 1 } });
    addText(s, `Origen ${i + 1}`, { left: 35, top: top - 4, width: 82, height: 38 }, { fontSize: 16, color: GRAY, alignment: "right", verticalAlignment: "middle" });
  }
  addText(s, "La ventana avanza una semana. Los modelos solo utilizan información conocida antes del origen.", { left: 220, top: 600, width: 840, height: 40 }, { fontSize: 20, color: GRAY, alignment: "center" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, apartados 3.8.5 y 3.9.6.`;
}

// 15. Métricas
{
  const s = slides[14];
  addTitle(s, "Métricas y regla de interpretación");
  addRule(s, 182);
  addText(s, "Importe total", { left: 115, top: 245, width: 300, height: 44 }, { fontSize: 26, bold: true, color: BLUE });
  addText(s, "MAE", { left: 115, top: 305, width: 140, height: 70 }, { fontSize: 42, bold: true, color: BLACK, alignment: "center", verticalAlignment: "middle" });
  addText(s, "Error medio en MXN", { left: 265, top: 315, width: 260, height: 48 }, { fontSize: 22, color: GRAY, verticalAlignment: "middle" });
  addText(s, "RMSE", { left: 115, top: 400, width: 140, height: 70 }, { fontSize: 42, bold: true, color: BLACK, alignment: "center", verticalAlignment: "middle" });
  addText(s, "Mayor peso a errores grandes", { left: 265, top: 410, width: 300, height: 48 }, { fontSize: 22, color: GRAY, verticalAlignment: "middle" });
  addText(s, "Composición", { left: 665, top: 245, width: 300, height: 44 }, { fontSize: 26, bold: true, color: GREEN });
  addText(s, "MAE pp", { left: 665, top: 315, width: 190, height: 70 }, { fontSize: 42, bold: true, color: BLACK, alignment: "center", verticalAlignment: "middle" });
  addText(s, "Desviación media de participaciones en puntos porcentuales", { left: 875, top: 305, width: 300, height: 96 }, { fontSize: 22, color: GRAY, verticalAlignment: "middle" });
  addRule(s, 510, LIGHT_GRAY, 115, 1060, 2);
  addText(s, "La hipótesis exige evidencia conjunta y suficiente. Un menor error aislado en un horizonte no demuestra superioridad general.", { left: 180, top: 545, width: 920, height: 70 }, { fontSize: 23, bold: true, color: RED, alignment: "center", verticalAlignment: "middle" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, apartados 2.9, 3.8.6 y 4.6.`;
}

// 16. Calidad y sensibilidad (tabla nativa)
{
  const s = slides[15];
  addTitle(s, "Calidad de datos y sensibilidad");
  addRule(s, 182);
  addText(s, "29 semanas estimadas", { left: 105, top: 228, width: 370, height: 58 }, { fontSize: 32, bold: true, color: AMBER });
  addText(s, "Se conservaron como artefactos de auditoría y se excluyeron del modelado.", { left: 105, top: 292, width: 370, height: 92 }, { fontSize: 22, color: BLACK });
  addText(s, "Resultado de sensibilidad", { left: 105, top: 420, width: 370, height: 44 }, { fontSize: 25, bold: true, color: GREEN });
  addText(s, "La ejecución sin parámetros de imputación reprodujo exactamente las métricas clave.", { left: 105, top: 470, width: 370, height: 100 }, { fontSize: 22, color: BLACK });
  const values = [
    ["Horizonte", "RMSE principal", "RMSE sin imputación", "Diferencia"],
    ["h=1", "521.60", "521.60", "0.00"],
    ["h=2", "695.41", "695.41", "0.00"],
    ["h=3", "801.62", "801.62", "0.00"],
    ["h=4", "700.88", "700.88", "0.00"],
  ];
  const table = s.tables.add({ rows: 5, columns: 4, left: 545, top: 245, width: 625, height: 300, values, columnWidths: [120, 170, 200, 135] });
  table.borders.assign({ style: "solid", fill: "#D9D9D9", width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: 4 }).assign({ fill: GREEN, textStyle: { typeface: FONT, fontSize: 17, bold: true, color: WHITE }, margins: { top: 7, right: 6, bottom: 7, left: 6 }, anchor: "middle" });
  table.cells.block({ row: 1, column: 0, rowCount: 4, columnCount: 4 }).assign({ textStyle: { typeface: FONT, fontSize: 18, color: BLACK }, margins: { top: 7, right: 6, bottom: 7, left: 6 }, anchor: "middle" });
  for (let r = 1; r < 5; r++) if (r % 2 === 0) table.cells.block({ row: r, column: 0, rowCount: 1, columnCount: 4 }).fill = GREEN_LIGHT;
  s.speakerNotes.text = `Fuente: ${sourceDocx}, apartado 4.2 y tabla 49.`;
}

// 17. RMSE híbrido
{
  const s = slides[16];
  addTitle(s, "Error del modelo híbrido por horizonte", "Evaluación final con seis orígenes monetarios válidos por horizonte");
  addRule(s, 202);
  const chart = s.charts.add("bar", {
    position: { left: 90, top: 230, width: 790, height: 360 },
    categories: ["1 semana", "2 semanas", "3 semanas", "4 semanas"],
    series: [{ name: "RMSE híbrido", values: [521.60, 695.41, 801.62, 700.88], fill: PURPLE }],
    hasLegend: false,
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 55, varyColors: false },
    xAxis: { textStyle: { typeface: FONT, fontSize: 16, fill: GRAY }, line: { style: "solid", fill: LIGHT_GRAY, width: 1 } },
    yAxis: { title: { text: "RMSE (MXN)", textStyle: { typeface: FONT, fontSize: 16, fill: GRAY } }, min: 0, max: 900, majorUnit: 200, textStyle: { typeface: FONT, fontSize: 15, fill: GRAY }, majorGridlines: { style: "solid", fill: LIGHT_GRAY, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "$0.00", textStyle: { typeface: FONT, fontSize: 15, bold: true, fill: BLACK } },
    chartFill: "none", chartLine: { style: "solid", fill: "none", width: 0 }, plotAreaFill: "none", plotAreaLine: { style: "solid", fill: "none", width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: FONT });
  addText(s, "$801.62", { left: 930, top: 280, width: 240, height: 70 }, { fontSize: 42, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle" });
  addText(s, "Mayor RMSE del híbrido\nen h=3", { left: 930, top: 350, width: 240, height: 70 }, { fontSize: 20, color: GRAY, alignment: "center", verticalAlignment: "middle" });
  addText(s, "El valor absoluto no determina por sí mismo si el híbrido supera al comparador del mismo horizonte.", { left: 900, top: 465, width: 300, height: 110 }, { fontSize: 20, color: BLACK, alignment: "center", verticalAlignment: "middle" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, tabla 43.`;
}

// 18. Comparación
{
  const s = slides[17];
  addTitle(s, "El híbrido solo obtiene el menor RMSE a tres semanas");
  addRule(s, 182);
  const chart = s.charts.add("bar", {
    position: { left: 90, top: 220, width: 850, height: 385 },
    categories: ["1 semana", "2 semanas", "3 semanas", "4 semanas"],
    series: [
      { name: "Híbrido", values: [521.60, 695.41, 801.62, 700.88], fill: PURPLE },
      { name: "Mejor comparador", values: [446.21, 596.17, 801.62, 578.95], fill: BLUE },
    ],
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { typeface: FONT, fontSize: 15, fill: GRAY } },
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 60 },
    xAxis: { textStyle: { typeface: FONT, fontSize: 16, fill: GRAY }, line: { style: "solid", fill: LIGHT_GRAY, width: 1 } },
    yAxis: { title: { text: "RMSE (MXN)", textStyle: { typeface: FONT, fontSize: 16, fill: GRAY } }, min: 0, max: 900, majorUnit: 200, textStyle: { typeface: FONT, fontSize: 15, fill: GRAY }, majorGridlines: { style: "solid", fill: LIGHT_GRAY, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "0.00", textStyle: { typeface: FONT, fontSize: 13, fill: BLACK } },
    chartFill: "none", chartLine: { style: "solid", fill: "none", width: 0 }, plotAreaFill: "none", plotAreaLine: { style: "solid", fill: "none", width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: FONT });
  addText(s, "1 de 4", { left: 965, top: 278, width: 210, height: 80 }, { fontSize: 48, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle" });
  addText(s, "horizontes con menor RMSE para el híbrido", { left: 970, top: 360, width: 200, height: 90 }, { fontSize: 21, color: GRAY, alignment: "center", verticalAlignment: "middle" });
  addText(s, "La superioridad depende del horizonte y del comparador.", { left: 960, top: 500, width: 220, height: 70 }, { fontSize: 21, bold: true, color: RED, alignment: "center", verticalAlignment: "middle" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, tabla 50 y párrafo 670.`;
}

// 19. Composición
{
  const s = slides[18];
  addTitle(s, "La distribución porcentual no tiene un método dominante");
  addRule(s, 182);
  const chart = s.charts.add("bar", {
    position: { left: 95, top: 220, width: 840, height: 390 },
    categories: ["h=1", "h=2", "h=3", "h=4"],
    series: [
      { name: "Participación histórica", values: [10.34, 7.14, 10.77, 11.80], fill: BLUE },
      { name: "Promedio temporal ponderado", values: [11.73, 6.93, 10.37, 12.23], fill: GREEN },
    ],
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { typeface: FONT, fontSize: 15, fill: GRAY } },
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 60 },
    xAxis: { textStyle: { typeface: FONT, fontSize: 16, fill: GRAY }, line: { style: "solid", fill: LIGHT_GRAY, width: 1 } },
    yAxis: { title: { text: "MAE (puntos porcentuales)", textStyle: { typeface: FONT, fontSize: 15, fill: GRAY } }, min: 0, max: 14, majorUnit: 2, textStyle: { typeface: FONT, fontSize: 15, fill: GRAY }, majorGridlines: { style: "solid", fill: LIGHT_GRAY, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "0.00", textStyle: { typeface: FONT, fontSize: 13, fill: BLACK } },
    chartFill: "none", chartLine: { style: "solid", fill: "none", width: 0 }, plotAreaFill: "none", plotAreaLine: { style: "solid", fill: "none", width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: FONT });
  addText(s, "Histórica", { left: 985, top: 265, width: 180, height: 46 }, { fontSize: 26, bold: true, color: BLUE, alignment: "center" });
  addText(s, "menor error en h=1 y h=4", { left: 970, top: 315, width: 210, height: 70 }, { fontSize: 20, color: GRAY, alignment: "center", verticalAlignment: "middle" });
  addText(s, "EWM", { left: 985, top: 435, width: 180, height: 46 }, { fontSize: 26, bold: true, color: GREEN, alignment: "center" });
  addText(s, "menor error en h=2 y h=3", { left: 970, top: 485, width: 210, height: 70 }, { fontSize: 20, color: GRAY, alignment: "center", verticalAlignment: "middle" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, tabla 51.`;
}

// 20. Contraste de hipótesis
{
  const s = slides[19];
  addTitle(s, "Contraste exploratorio de H1");
  addRule(s, 182);
  addText(s, "No confirmatorio", { left: 170, top: 250, width: 940, height: 105 }, { fontSize: 56, bold: true, color: RED, alignment: "center", verticalAlignment: "middle" });
  addText(s, "La evidencia disponible no permite afirmar que el híbrido mejore conjuntamente el importe total y la distribución porcentual.", { left: 235, top: 375, width: 810, height: 105 }, { fontSize: 28, bold: true, color: BLACK, alignment: "center", verticalAlignment: "middle" });
  addRule(s, 512, LIGHT_GRAY, 205, 870, 2);
  addText(s, "Seis orígenes monetarios por horizonte", { left: 165, top: 545, width: 405, height: 50 }, { fontSize: 21, color: GRAY, alignment: "center" });
  addText(s, "Tres a cinco observaciones válidas para composición", { left: 710, top: 545, width: 405, height: 50 }, { fontSize: 21, color: GRAY, alignment: "center" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, apartados 4.6 y 5.1, especialmente párrafo 671.`;
}

// 21. Aplicación
{
  const s = slides[20];
  addTitle(s, "Uso operativo del sistema de soporte a la decisión");
  addRule(s, 182);
  const labels = ["Actualizar datos", "Verificar cobertura", "Emitir pronóstico", "Revisar riesgo", "Decidir y registrar"];
  const boxes = [];
  for (let i = 0; i < labels.length; i++) {
    const fill = i < 2 ? BLUE_LIGHT : i < 4 ? GREEN_LIGHT : AMBER_LIGHT;
    const line = i < 2 ? BLUE : i < 4 ? GREEN : AMBER;
    boxes.push(addStage(s, labels[i], 75 + i * 240, 265, 205, 175, fill, line, i + 1));
  }
  for (let i = 0; i < boxes.length - 1; i++) addArrow(s, boxes[i], boxes[i + 1]);
  addText(s, "La salida constituye un insumo de consulta. El pronóstico histórico incluido en la tesis no representa un presupuesto vigente.", { left: 170, top: 500, width: 940, height: 76 }, { fontSize: 22, bold: true, color: RED, alignment: "center", verticalAlignment: "middle" });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, párrafo 673 y apartados 3.8.7 y 4.8.3.`;
}

// 22. Conclusiones
{
  const s = slides[21];
  addTitle(s, "Conclusiones");
  addRule(s, 182);
  addBullets(s, [
    "El pipeline integra compras, ventas y calendario, genera pronósticos de uno a cuatro pasos y concilia la asignación por insumo.",
    "El híbrido no domina todos los horizontes. Solo logra el menor RMSE entre los comparadores principales a tres semanas.",
    "La composición alterna entre el método histórico y el promedio temporal ponderado, sin un ganador general.",
    "La muestra reducida y la cobertura no certificada impiden una conclusión confirmatoria sobre H1.",
    "El resultado sirve como apoyo revisable para la planeación, no como orden automática de compra.",
  ], { left: 145, top: 235, width: 990, height: 370 }, { fontSize: 24, color: BLACK, spaceAfterPoints: 11 });
  s.speakerNotes.text = `Fuente: ${sourceDocx}, párrafos 670 a 673.`;
}

// 23. Cierre
{
  const s = slides[22];
  addText(s, "Gracias", { left: 250, top: 245, width: 780, height: 120 }, { fontSize: 64, bold: true, color: PURPLE, alignment: "center", verticalAlignment: "middle" });
  addText(s, "Preguntas", { left: 250, top: 370, width: 780, height: 70 }, { fontSize: 32, color: BLACK, alignment: "center", verticalAlignment: "middle" });
  addRule(s, 475, PURPLE, 440, 400, 4);
  addText(s, "Rodrigo Adrián Martínez Flores", { left: 350, top: 520, width: 580, height: 42 }, { fontSize: 22, color: GRAY, alignment: "center" });
  s.speakerNotes.text = "Cierre de la defensa.";
}

// Inspection and previews.
const content = await presentation.inspect({
  select: "$.slides[*]",
  include: ["id", "index", "layout", "title", "elements.id", "elements.kind", "elements.name", "elements.text", "notes.text"],
});
await fs.writeFile(path.join(buildDir, "content.ndjson"), content.ndjson);

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(renderDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
  const layout = await slide.export({ format: "layout", detail: "full" });
  await fs.writeFile(path.join(renderDir, `${stem}.layout.json`), await layout.text());
}
await writeBlob(path.join(buildDir, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 0.5 }));

const candidatePath = path.join(stagingDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const requirements = {
  explicitTotalSlideCount: 23,
  requiredNativeTableOwnerSlides: [12, 16],
  requiredNativeChartOwnerSlides: [17, 18, 19],
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
const expectedSlideSizeEmu = "12192000,6858000";
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
    "--expected-slide-size-emu", expectedSlideSizeEmu,
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
