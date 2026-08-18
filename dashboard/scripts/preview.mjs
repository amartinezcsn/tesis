import { createServer } from "node:http";

import worker from "../dist/server/index.js";

const port = Number(process.env.PORT || 8788);
const server = createServer(async (request, response) => {
  const bodyChunks = [];
  for await (const chunk of request) bodyChunks.push(chunk);
  const url = new URL(
    request.url || "/",
    `http://${request.headers.host || `127.0.0.1:${port}`}`,
  );
  const webRequest = new Request(url, {
    method: request.method,
    headers: request.headers,
    body: bodyChunks.length ? Buffer.concat(bodyChunks) : undefined,
  });
  const webResponse = await worker.fetch(webRequest);
  response.writeHead(webResponse.status, Object.fromEntries(webResponse.headers));
  response.end(Buffer.from(await webResponse.arrayBuffer()));
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Local: http://127.0.0.1:${port}`);
});
