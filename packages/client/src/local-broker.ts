import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { WebSocketServer, WebSocket } from "ws";
import {
  type DevotchiMessage,
  type ClientRole,
  type ErrorCode,
  HEARTBEAT_INTERVAL,
  RATE_LIMIT_PER_MINUTE,
  MAX_MESSAGE_SIZE,
  DEFAULT_APPROVAL_TIMEOUT,
} from "@devotchi/shared";

interface ClientInfo {
  ws: WebSocket;
  role: ClientRole;
  roomId: string;
  alive: boolean;
  messageTimestamps: number[];
}

interface PairingRoom {
  producer: ClientInfo | null;
  consumers: Set<ClientInfo>;
}

export function startLocalBroker(port: number): Promise<ReturnType<typeof createServer>> {
  const rooms = new Map<string, PairingRoom>();
  const clients = new Map<WebSocket, ClientInfo>();
  const pendingHookRequests = new Map<
    string,
    { resolve: (msg: DevotchiMessage) => void; timer: ReturnType<typeof setTimeout> }
  >();

  function getOrCreateRoom(roomId: string): PairingRoom {
    let room = rooms.get(roomId);
    if (!room) {
      room = { producer: null, consumers: new Set() };
      rooms.set(roomId, room);
    }
    return room;
  }

  function cleanupRoom(roomId: string): void {
    const room = rooms.get(roomId);
    if (room && !room.producer && room.consumers.size === 0) {
      rooms.delete(roomId);
    }
  }

  function peerCount(room: PairingRoom): number {
    return (room.producer ? 1 : 0) + room.consumers.size;
  }

  function isRateLimited(client: ClientInfo): boolean {
    const now = Date.now();
    client.messageTimestamps = client.messageTimestamps.filter((t) => now - t < 60_000);
    if (client.messageTimestamps.length >= RATE_LIMIT_PER_MINUTE) return true;
    client.messageTimestamps.push(now);
    return false;
  }

  function send(ws: WebSocket, msg: DevotchiMessage): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }

  function sendToConsumers(roomId: string, msg: DevotchiMessage): void {
    const room = rooms.get(roomId);
    if (!room) return;
    for (const consumer of room.consumers) {
      send(consumer.ws, msg);
    }
  }

  function sendError(ws: WebSocket, message: string, code: ErrorCode): void {
    send(ws, { type: "error", message, code });
  }

  function generateId(): string {
    return crypto.randomUUID().replace(/-/g, "").slice(0, 8);
  }

  function readBody(req: IncomingMessage): Promise<string> {
    return new Promise((resolve, reject) => {
      const chunks: Buffer[] = [];
      let size = 0;
      req.on("data", (chunk: Buffer) => {
        size += chunk.length;
        if (size > 64 * 1024) {
          req.destroy();
          reject(new Error("Body too large"));
          return;
        }
        chunks.push(chunk);
      });
      req.on("end", () => resolve(Buffer.concat(chunks).toString()));
      req.on("error", reject);
    });
  }

  function getQueryParam(url: string, param: string): string | null {
    try {
      return new URL(url, "http://localhost").searchParams.get(param);
    } catch {
      return null;
    }
  }

  function jsonResponse(res: ServerResponse, status: number, body: unknown): void {
    res.writeHead(status, {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    });
    res.end(JSON.stringify(body));
  }

  // Local mode: use roomId from register message, no token validation
  function handleRegister(ws: WebSocket, msg: DevotchiMessage): void {
    if (msg.type !== "register") {
      sendError(ws, "First message must be register", "INVALID_MESSAGE");
      ws.close();
      return;
    }

    // In local mode, accept any roomId (default to "local")
    const roomId = msg.roomId || "local";
    const room = getOrCreateRoom(roomId);
    const client: ClientInfo = {
      ws,
      role: msg.role,
      roomId,
      alive: true,
      messageTimestamps: [],
    };

    if (msg.role === "producer") {
      if (room.producer) {
        send(room.producer.ws, { type: "error", message: "Replaced by new producer", code: "INVALID_MESSAGE" });
        room.producer.ws.close(4001, "replaced");
        clients.delete(room.producer.ws);
      }
      room.producer = client;
    } else {
      room.consumers.add(client);
    }

    clients.set(ws, client);
    send(ws, {
      type: "register_ack",
      role: msg.role,
      roomId,
      pairingCode: roomId,
      connectedPeers: peerCount(room) - 1,
    });
  }

  function handleMessage(ws: WebSocket, data: string): void {
    const client = clients.get(ws);

    let msg: DevotchiMessage;
    try {
      msg = JSON.parse(data);
    } catch {
      sendError(ws, "Invalid JSON", "INVALID_MESSAGE");
      return;
    }

    if (!msg || typeof msg !== "object" || !("type" in msg)) {
      sendError(ws, "Missing type field", "INVALID_MESSAGE");
      return;
    }

    if (!client) {
      handleRegister(ws, msg);
      return;
    }

    if (msg.type === "pong") { client.alive = true; return; }
    if (msg.type === "ping") { send(ws, { type: "pong" }); return; }

    if (isRateLimited(client)) {
      sendError(ws, "Rate limited", "RATE_LIMITED");
      return;
    }

    const room = rooms.get(client.roomId);
    if (!room) return;

    if (client.role === "producer") {
      for (const consumer of room.consumers) {
        send(consumer.ws, msg);
      }
    } else {
      if (
        (msg.type === "approval_response" || msg.type === "permission_response") &&
        "id" in msg
      ) {
        const pending = pendingHookRequests.get(msg.id);
        if (pending) {
          clearTimeout(pending.timer);
          pendingHookRequests.delete(msg.id);
          pending.resolve(msg);
          return;
        }
      }

      if (room.producer) {
        send(room.producer.ws, msg);
      } else {
        sendError(ws, "No producer connected", "NO_PRODUCER");
      }
    }
  }

  function handleDisconnect(ws: WebSocket): void {
    const client = clients.get(ws);
    if (!client) return;

    const room = rooms.get(client.roomId);
    if (room) {
      if (client.role === "producer" && room.producer?.ws === ws) {
        room.producer = null;
      } else {
        room.consumers.delete(client);
      }
      cleanupRoom(client.roomId);
    }

    clients.delete(ws);
  }

  // Local broker hook endpoints use a simple room lookup
  // In local mode, find the first room (there's usually only one)
  function findRoomForHook(): string | null {
    for (const [roomId] of rooms) {
      return roomId;
    }
    return null;
  }

  async function handleHookPermission(req: IncomingMessage, res: ServerResponse): Promise<void> {
    const roomId = findRoomForHook();
    if (!roomId) {
      jsonResponse(res, 200, {});
      return;
    }

    const room = rooms.get(roomId);
    if (!room || room.consumers.size === 0) {
      jsonResponse(res, 200, {});
      return;
    }

    let body: any;
    try {
      body = JSON.parse(await readBody(req));
    } catch {
      jsonResponse(res, 400, { error: "Invalid JSON body" });
      return;
    }

    const id = generateId();
    const toolName = body.tool_name || "unknown";
    const toolInput = body.tool_input || {};
    const details = typeof toolInput === "object"
      ? JSON.stringify(toolInput).slice(0, 1000)
      : String(toolInput).slice(0, 1000);

    sendToConsumers(roomId, {
      type: "permission",
      id,
      action: toolName,
      details,
      timeout: DEFAULT_APPROVAL_TIMEOUT,
      timestamp: new Date().toISOString(),
    });

    const response = await new Promise<DevotchiMessage | null>((resolve) => {
      const timer = setTimeout(() => {
        pendingHookRequests.delete(id);
        resolve(null);
      }, DEFAULT_APPROVAL_TIMEOUT);

      pendingHookRequests.set(id, { resolve, timer });

      res.on("close", () => {
        if (res.writableEnded) return;
        const pending = pendingHookRequests.get(id);
        if (pending) {
          clearTimeout(pending.timer);
          pendingHookRequests.delete(id);
          sendToConsumers(roomId, { type: "dismiss", id });
          resolve(null);
        }
      });
    });

    if (response && response.type === "permission_response") {
      jsonResponse(res, 200, {
        hookSpecificOutput: {
          hookEventName: "PermissionRequest",
          decision: { behavior: response.granted ? "allow" : "deny" },
        },
      });
    } else {
      jsonResponse(res, 200, {
        hookSpecificOutput: {
          hookEventName: "PermissionRequest",
          decision: { behavior: "deny" },
        },
      });
    }
  }

  function handleHookStatus(req: IncomingMessage, res: ServerResponse): void {
    const roomId = findRoomForHook();
    readBody(req)
      .then((raw) => {
        if (!roomId) return;
        const body = JSON.parse(raw);
        const toolName = body.tool_name || "unknown";
        const toolInput = body.tool_input || {};

        let description = toolName;
        if (toolName === "Bash" && toolInput.command) {
          description = toolInput.command.slice(0, 200);
        } else if ((toolName === "Write" || toolName === "Edit") && toolInput.file_path) {
          description = `${toolName}: ${toolInput.file_path}`;
        }

        sendToConsumers(roomId, {
          type: "status",
          msg: description.slice(0, 200),
          mood: "working",
          timestamp: new Date().toISOString(),
        });
      })
      .catch(() => {})
      .finally(() => {
        jsonResponse(res, 200, {});
      });
  }

  function handleHookStop(req: IncomingMessage, res: ServerResponse): void {
    const roomId = findRoomForHook();
    if (roomId) {
      sendToConsumers(roomId, {
        type: "notify",
        event: "task_complete",
        mood: "idle",
        detail: "Agent stopped",
        timestamp: new Date().toISOString(),
      });
      sendToConsumers(roomId, {
        type: "mood",
        mood: "sleeping",
        reason: "Waiting for instructions",
        timestamp: new Date().toISOString(),
      });
    }

    readBody(req).catch(() => {}).finally(() => {
      jsonResponse(res, 200, {});
    });
  }

  const server = createServer(async (req, res) => {
    const url = req.url || "/";
    const pathname = url.split("?")[0];

    if (req.method === "OPTIONS") {
      res.writeHead(204, {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      });
      res.end();
      return;
    }

    if (req.method === "GET" && pathname === "/") {
      jsonResponse(res, 200, { status: "ok", connections: clients.size });
      return;
    }

    // Local broker: accept token-based hook URLs (ignore token validation)
    if (req.method === "POST" && pathname.startsWith("/hook/")) {
      switch (pathname) {
        case "/hook/permission":
          await handleHookPermission(req, res);
          return;
        case "/hook/status":
          handleHookStatus(req, res);
          return;
        case "/hook/stop":
          handleHookStop(req, res);
          return;
      }
    }

    // Local broker: simple token endpoint (returns a dummy token)
    if (req.method === "POST" && pathname === "/api/auth/token") {
      jsonResponse(res, 201, { token: "local-token", id: "local", roomId: "local" });
      return;
    }

    if (req.method === "POST" && pathname === "/api/pair") {
      jsonResponse(res, 201, { pairingCode: "LOCAL", expiresAt: new Date(Date.now() + 300000).toISOString() });
      return;
    }

    res.writeHead(404);
    res.end();
  });

  const wss = new WebSocketServer({ server, maxPayload: MAX_MESSAGE_SIZE });

  wss.on("connection", (ws: WebSocket) => {
    ws.on("message", (data: Buffer) => {
      const str = data.toString();
      if (str.length > MAX_MESSAGE_SIZE) {
        sendError(ws, "Message too large", "INVALID_MESSAGE");
        return;
      }
      handleMessage(ws, str);
    });
    ws.on("close", () => handleDisconnect(ws));
    ws.on("error", () => handleDisconnect(ws));
  });

  const heartbeatInterval = setInterval(() => {
    for (const [ws, client] of clients) {
      if (!client.alive) {
        ws.terminate();
        handleDisconnect(ws);
        continue;
      }
      client.alive = false;
      send(ws, { type: "ping" });
    }
  }, HEARTBEAT_INTERVAL);

  wss.on("close", () => clearInterval(heartbeatInterval));

  return new Promise((resolve) => {
    server.listen(port, () => {
      console.log(`Devotchi local broker listening on port ${port}`);
      resolve(server);
    });
  });
}
