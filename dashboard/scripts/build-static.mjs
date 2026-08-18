import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const projectRoot = resolve(import.meta.dirname, "..");
const sourcePath = resolve(projectRoot, "public", "index.html");
const outputDir = resolve(projectRoot, "dist", "server");
const outputPath = resolve(outputDir, "index.js");

const html = await readFile(sourcePath);
const encoded = html.toString("base64");

const worker = `const HTML_BASE64 = ${JSON.stringify(encoded)};

function decodeHtml() {
  return Uint8Array.from(atob(HTML_BASE64), (character) => character.charCodeAt(0));
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return new Response("ok", {
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    return new Response(decodeHtml(), {
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "public, max-age=300",
        "content-security-policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        "referrer-policy": "strict-origin-when-cross-origin",
        "x-content-type-options": "nosniff",
      },
    });
  },
};
`;

await mkdir(outputDir, { recursive: true });
await writeFile(outputPath, worker, "utf8");
console.log(`Built ${outputPath}`);
