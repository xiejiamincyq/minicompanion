import { WebSocket } from "ws";
import type { ClientRole, DevotchiMessage } from "@devotchi/shared";

export interface ClientInfo {
  ws: WebSocket;
  role: ClientRole;
  roomId: string;
  alive: boolean;
  messageTimestamps: number[];
}

export interface PairingRoom {
  producer: ClientInfo | null;
  consumers: Set<ClientInfo>;
}

export interface PendingHook {
  resolve: (msg: DevotchiMessage) => void;
  timer: ReturnType<typeof setTimeout>;
}

export class RoomState {
  readonly rooms = new Map<string, PairingRoom>();
  readonly clients = new Map<WebSocket, ClientInfo>();
  readonly pendingHookRequests = new Map<string, PendingHook>();

  getOrCreateRoom(roomId: string): PairingRoom {
    let room = this.rooms.get(roomId);
    if (!room) {
      room = { producer: null, consumers: new Set() };
      this.rooms.set(roomId, room);
    }
    return room;
  }

  cleanupRoom(roomId: string): void {
    const room = this.rooms.get(roomId);
    if (room && !room.producer && room.consumers.size === 0) {
      this.rooms.delete(roomId);
    }
  }

  peerCount(room: PairingRoom): number {
    return (room.producer ? 1 : 0) + room.consumers.size;
  }

  send(ws: WebSocket, msg: DevotchiMessage): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }

  sendToConsumers(roomId: string, msg: DevotchiMessage): void {
    const room = this.rooms.get(roomId);
    if (!room) return;
    for (const consumer of room.consumers) {
      this.send(consumer.ws, msg);
    }
  }

  sendError(ws: WebSocket, message: string, code: import("@devotchi/shared").ErrorCode): void {
    this.send(ws, { type: "error", message, code });
  }

  get connectionCount(): number {
    return this.clients.size;
  }
}
