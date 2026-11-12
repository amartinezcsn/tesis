import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const artifactPath = "C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1111-570-0_26.1111.570.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const { FileBlob, PresentationFile } = await import(pathToFileURL(artifactPath).href);

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function inspectDeck(inputPath, outputDir) {
  await fs.mkdir(outputDir, { recursive: true });
  const presentation = await PresentationFile.importPptx(await FileBlob.load(inputPath));
  const info = {
    inputPath,
    slideCount: presentation.slides.items.length,
    slideSize: presentation.slideSize,
    masters: presentation.masters.items.map((m) => ({ id: m.id, name: m.name })),
    layouts: presentation.layouts.items.map((l) => ({
      id: l.id,
      name: l.name,
      placeholders: l.placeholders.summary(),
    })),
  };
  await fs.writeFile(path.join(outputDir, "deck-info.json"), JSON.stringify(info, null, 2));
  const content = await presentation.inspect({
    select: "$.slides[*]",
    include: ["id", "index", "layout", "title", "elements.id", "elements.kind", "elements.name", "elements.text", "elements.alt", "notes.text"],
    fileName: path.join(outputDir, "content.ndjson"),
  });
  await fs.writeFile(path.join(outputDir, "content.ndjson"), content.ndjson);
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(outputDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout", detail: "full" });
    await fs.writeFile(path.join(outputDir, `${stem}.layout.json`), await layout.text());
  }
  await writeBlob(path.join(outputDir, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 0.5 }));
  return info;
}

const workspace = "C:/Python/tesis";
const targets = [
  [path.join(workspace, "Plantilla_2026.pptx"), path.join(workspace, ".pptx_build/inspect/template")],
  [path.join(workspace, "documentacion/Planeación_Financiera_Predictiva_con_IA_Híbrida.pptx"), path.join(workspace, ".pptx_build/inspect/current")],
];

for (const [input, output] of targets) {
  const info = await inspectDeck(input, output);
  console.log(JSON.stringify(info));
}
