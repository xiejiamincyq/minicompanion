import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { join, extname } from "node:path";
import { fileURLToPath } from "node:url";
import { WebSocketServer, WebSocket } from "ws";
import type { ClientConfig } from "@devotchi/shared";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const WEB_DIR = join(__dirname, "web");

const MIME_TYPES: Record<string, string> = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
};

async function serveStatic(res: ServerResponse, urlPath: string): Promise<void> {
  let filePath = join(WEB_DIR, urlPath === "/" ? "index.html" : urlPath);

  try {
    const s = await stat(filePath);
    if (s.isDirectory()) {
      filePath = join(filePath, "index.html");
    }
  } catch {
    // fall through to 404
  }

  try {
    const data = await readFile(filePath);
    const ext = extname(filePath);
    res.writeHead(200, { "Content-Type": MIME_TYPES[ext] || "application/octet-stream" });
    res.end(data);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found");
  }
}

function wsServerUrl(config: ClientConfig): string {
  return config.serverUrl.replace(/^http/, "ws").replace(/\/$/, "");
}

export async function startWebServer(config: ClientConfig): Promise<void> {
  const server = createServer(async (req: IncomingMessage, res: ServerResponse) => {
    const url = req.url || "/";
    const pathname = url.split("?")[0];

    if (req.method === "GET" && pathname === "/api/config") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        pairingCode: config.pairingCode,
        roomId: config.roomId,
        serverUrl: config.serverUrl,
        localMode: config.localMode,
      }));
      return;
    }

    await serveStatic(res, pathname);
  });

  const wss = new WebSocketServer({ server, path: "/ws" });

  wss.on("connection", (clientWs: WebSocket) => {
    const serverWsUrl = `${wsServerUrl(config)}/ws?token=${encodeURIComponent(config.token)}`;
    const upstream = new WebSocket(serverWsUrl);

    upstream.on("open", () => {
      upstream.send(JSON.stringify({
        type: "register",
        role: "consumer",
        roomId: config.roomId,
      }));
    });

    upstream.on("message", (data) => {
      if (clientWs.readyState === WebSocket.OPEN) {
        clientWs.send(data.toString());
      }
    });

    upstream.on("close", () => {
      if (clientWs.readyState === WebSocket.OPEN) {
        clientWs.close();
      }
    });

    upstream.on("error", (err) => {
      console.error("[devotchi] Upstream WebSocket error:", err.message);
    });

    clientWs.on("message", (data) => {
      if (upstream.readyState === WebSocket.OPEN) {
        upstream.send(data.toString());
      }
    });

    clientWs.on("close", () => {
      upstream.close();
    });
  });

  return new Promise((resolve) => {
    server.listen(config.webPort, () => {
      console.log(`Devotchi dashboard: http://localhost:${config.webPort}`);
      resolve();
    });
  });
}
