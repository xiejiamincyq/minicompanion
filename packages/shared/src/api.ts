// REST API request/response types — see docs/protocol.md for specification

// --- Token Management ---

export interface CreateTokenRequest {
  label?: string;
}

export interface CreateTokenResponse {
  token: string;
  id: string;
  roomId: string;
}

// --- Auth (multi-user mode only) ---

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  sessionToken: string;
  userId: string;
}

// --- Device & Pairing ---

export interface Device {
  id: string;
  pairingCode: string;
  lastSeen: string;
  label?: string;
}

export interface CreatePairingRequest {
  deviceId?: string;
  label?: string;
}

export interface CreatePairingResponse {
  pairingCode: string;
  expiresAt: string;
}

export interface ClaimPairingRequest {
  code: string;
}

export interface ClaimPairingResponse {
  token: string;
  roomId: string;
}

export interface ListDevicesResponse {
  devices: Device[];
}

// --- Health ---

export interface HealthResponse {
  status: "ok";
  connections: number;
  mode: ServerMode;
}

// --- Server Mode ---

export type ServerMode = "single-user" | "multi-user";
