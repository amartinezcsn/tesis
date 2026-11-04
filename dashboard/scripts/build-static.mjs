import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { makeWorker } from "./build-hibrido.mjs";

const projectRoot = resolve(import.meta.dirname, "..");
const sourcePath = resolve(projectRoot, "public", "index.html");
const staticOutputPath = resolve(projectRoot, "dist", "index.html");
const outputDir = resolve(projectRoot, "dist", "server");
const outputPath = resolve(outputDir, "index.js");

const html = await readFile(sourcePath, "utf8");
const required = [
  'id="horizon"',
  'id="downloadCsv"',
  "Distribución presupuestaria",
  "Trazabilidad de la emisión",
  "calcula cantidades físicas",
];
const missing = required.filter((marker) => !html.includes(marker));
if (missing.length) {
  throw new Error(`El punto de entrada no contiene el dashboard híbrido: ${missing.join(", ")}`);
}

await mkdir(outputDir, { recursive: true });
await writeFile(staticOutputPath, html, "utf8");
await writeFile(outputPath, makeWorker(html), "utf8");
console.log(`Built ${outputPath}`);
