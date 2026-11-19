// Configuration types for server and client

import type { ServerMode } from "./api.js";

export interface ServerConfig {
  mode: ServerMode;
  port: number;
  dbPath: string;
  jwtSecret?: string; // required for multi-user mode
  corsOrigins?: string[];
}

export interface ClientConfig {
  serverUrl: string;
  token: string;
  roomId: string;
  pairingCode: string;
  webPort: number;
  localMode: boolean;
}

export const DEFAULT_SERVER_PORT = 8080;
export const DEFAULT_CLIENT_WEB_PORT = 3456;
export const DEFAULT_SERVER_URL = "http://localhost:8080";
