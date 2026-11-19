import { type IncomingMessage } from "node:http";
import type { Server } from "node:http";
import { WebSocketServer, WebSocket } from "ws";
import {
  type DevotchiMessage,
  HEARTBEAT_INTERVAL,
  RATE_LIMIT_PER_MINUTE,
  MAX_MESSAGE_SIZE,
} from "@devotchi/shared";
import type { Database } from "../db/index.js";
import { lookupTokenHash } from "../middleware/auth.js";
import { RoomState, type ClientInfo } from "./rooms.js";

function isRateLimited(client: ClientInfo): boolean {
  const now = Date.now();
  client.messageTimestamps = client.messageTimestamps.filter(
    (t) => now - t < 60_000
  );
  if (client.messageTimestamps.length >= RATE_LIMIT_PER_MINUTE) {
    return true;
  }
  client.messageTimestamps.push(now);
  return false;
}

function getQueryParam(url: string, param: string): string | null {
  try {
    return new URL(url, "http://localhost").searchParams.get(param);
  } catch {
    return null;
  }
}

function handleRegister(state: RoomState, ws: WebSocket, msg: DevotchiMessage, roomId: string): void {
  if (msg.type !== "register") {
    state.sendError(ws, "First message must be register", "INVALID_MESSAGE");
    ws.close();
    return;
  }

  const room = state.getOrCreateRoom(roomId);
  const client: ClientInfo = {
    ws,
    role: msg.role,
    roomId,
    alive: true,
    messageTimestamps: [],
  };

  if (msg.role === "producer") {
    if (room.producer) {
      state.send(room.producer.ws, {
        type: "error",
        message: "Replaced by new producer",
        code: "INVALID_MESSAGE",
      });
      room.producer.ws.close(4001, "replaced");
      state.clients.delete(room.producer.ws);
    }
    room.producer = client;
  } else {
    room.consumers.add(client);
  }

  state.clients.set(ws, client);

  state.send(ws, {
    type: "register_ack",
    role: msg.role,
    roomId,
    pairingCode: roomId,
    connectedPeers: state.peerCount(room) - 1,
  });

  console.log(
    `[register] ${msg.role} joined room ${roomId} (${state.peerCount(room)} in room)`
  );
}

function handleMessage(state: RoomState, ws: WebSocket, data: string, wsRoomId: string): void {
  const client = state.clients.get(ws);

  let msg: DevotchiMessage;
  try {
    msg = JSON.parse(data);
  } catch {
    state.sendError(ws, "Invalid JSON", "INVALID_MESSAGE");
    return;
  }

  if (!msg || typeof msg !== "object" || !("type" in msg)) {
    state.sendError(ws, "Missing type field", "INVALID_MESSAGE");
    return;
  }

  if (!client) {
    handleRegister(state, ws, msg, wsRoomId);
    return;
  }

  if (msg.type === "pong") {
    client.alive = true;
    return;
  }

  if (msg.type === "ping") {
    state.send(ws, { type: "pong" });
    return;
  }

  if (isRateLimited(client)) {
    state.sendError(ws, "Rate limited", "RATE_LIMITED");
    return;
  }

  const room = state.rooms.get(client.roomId);
  if (!room) return;

  if (client.role === "producer") {
    for (const consumer of room.consumers) {
      state.send(consumer.ws, msg);
    }
  } else {
    if (
      (msg.type === "approval_response" || msg.type === "permission_response") &&
      "id" in msg
    ) {
      const pending = state.pendingHookRequests.get(msg.id);
      if (pending) {
        clearTimeout(pending.timer);
        state.pendingHookRequests.delete(msg.id);
        pending.resolve(msg);
        return;
      }
    }

    if (room.producer) {
      state.send(room.producer.ws, msg);
    } else {
      state.sendError(ws, "No producer connected", "NO_PRODUCER");
    }
  }
}

function handleDisconnect(state: RoomState, ws: WebSocket): void {
  const client = state.clients.get(ws);
  if (!client) return;

  const room = state.rooms.get(client.roomId);
  if (room) {
    if (client.role === "producer" && room.producer?.ws === ws) {
      room.producer = null;
    } else {
      room.consumers.delete(client);
    }
    state.cleanupRoom(client.roomId);
  }

  state.clients.delete(ws);
  console.log(`[disconnect] ${client.role} left room ${client.roomId}`);
}

export function attachWebSocket(server: Server, state: RoomState, db: Database): {
  wss: WebSocketServer;
  heartbeatInterval: ReturnType<typeof setInterval>;
} {
  const wss = new WebSocketServer({ noServer: true, maxPayload: MAX_MESSAGE_SIZE });

  server.on("upgrade", (req: IncomingMessage, socket, head) => {
    const token = getQueryParam(req.url || "", "token");

    if (!token) {
      socket.write("HTTP/1.1 401 Unauthorized\r\n\r\n");
      socket.destroy();
      return;
    }

    const tokenInfo = lookupTokenHash(db, token);
    if (!tokenInfo) {
      socket.write("HTTP/1.1 401 Unauthorized\r\n\r\n");
      socket.destroy();
      return;
    }

    wss.handleUpgrade(req, socket, head, (ws) => {
      (ws as any).__roomId = tokenInfo.roomId;
      wss.emit("connection", ws, req);
    });
  });

  wss.on("connection", (ws: WebSocket, req: IncomingMessage) => {
    const roomId = (ws as any).__roomId as string;
    console.log(`[connect] new connection from ${req.socket.remoteAddress} (room: ${roomId})`);

    ws.on("message", (data: Buffer) => {
      const str = data.toString();
      if (str.length > MAX_MESSAGE_SIZE) {
        state.sendError(ws, "Message too large", "INVALID_MESSAGE");
        return;
      }
      handleMessage(state, ws, str, roomId);
    });

    ws.on("close", () => handleDisconnect(state, ws));
    ws.on("error", (err) => {
      console.error(`[error] ${err.message}`);
      handleDisconnect(state, ws);
    });
  });

  const heartbeatInterval = setInterval(() => {
    for (const [ws, client] of state.clients) {
      if (!client.alive) {
        console.log(
          `[heartbeat] ${client.role} room ${client.roomId} timed out`
        );
        ws.terminate();
        handleDisconnect(state, ws);
        continue;
      }
      client.alive = false;
      state.send(ws, { type: "ping" });
    }
  }, HEARTBEAT_INTERVAL);

  wss.on("close", () => clearInterval(heartbeatInterval));

  return { wss, heartbeatInterval };
}
