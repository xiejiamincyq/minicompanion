// Devotchi protocol types — see docs/protocol.md for specification

// --- Enums & Mood Types ---

export type StatusMood = "focused" | "working" | "thinking" | "idle";

export type PetMood =
  | "happy"
  | "sad"
  | "excited"
  | "anxious"
  | "sleeping"
  | "angry"
  | "proud"
  | "idle";

export type ClientRole = "producer" | "consumer";

// --- Producer -> Consumer Messages ---

export interface StatusMessage {
  type: "status";
  msg: string;
  mood?: StatusMood;
  timestamp: string;
}

export interface ApprovalRequest {
  type: "approval";
  id: string;
  desc: string;
  details?: string;
  timeout: number;
  timestamp: string;
}

export interface PermissionRequest {
  type: "permission";
  id: string;
  action: string;
  details?: string;
  timeout: number;
  timestamp: string;
}

export interface Notification {
  type: "notify";
  event: string;
  mood: PetMood;
  detail?: string;
  timestamp: string;
}

export interface MoodUpdate {
  type: "mood";
  mood: PetMood;
  reason?: string;
  timestamp: string;
}

// --- Consumer -> Producer Messages ---

export interface ApprovalResponse {
  type: "approval_response";
  id: string;
  approved: boolean;
  timestamp: string;
}

export interface PermissionResponse {
  type: "permission_response";
  id: string;
  granted: boolean;
  timestamp: string;
}

// --- System Messages ---

export interface RegisterMessage {
  type: "register";
  role: ClientRole;
  roomId?: string;
  token?: string;
}

export interface RegisterAck {
  type: "register_ack";
  role: ClientRole;
  roomId: string;
  pairingCode: string;
  connectedPeers: number;
}

export interface PingMessage {
  type: "ping";
}

export interface PongMessage {
  type: "pong";
}

export interface ErrorMessage {
  type: "error";
  message: string;
  code: ErrorCode;
}

export interface DismissMessage {
  type: "dismiss";
  id: string;
}

// --- Union Type ---

export type DevotchiMessage =
  | StatusMessage
  | ApprovalRequest
  | PermissionRequest
  | Notification
  | MoodUpdate
  | ApprovalResponse
  | PermissionResponse
  | RegisterMessage
  | RegisterAck
  | PingMessage
  | PongMessage
  | ErrorMessage
  | DismissMessage;

// --- Constants ---

export type ErrorCode =
  | "INVALID_PAIRING_CODE"
  | "NO_PRODUCER"
  | "RATE_LIMITED"
  | "INVALID_MESSAGE";

export const PAIRING_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
export const PAIRING_CODE_LENGTH = 6;

export const DEFAULT_APPROVAL_TIMEOUT = 300_000; // 5 minutes
export const HEARTBEAT_INTERVAL = 30_000; // 30 seconds
export const HEARTBEAT_TIMEOUT = 10_000; // 10 seconds
export const RATE_LIMIT_PER_MINUTE = 60;

export const MAX_SHORT_FIELD_LENGTH = 200; // msg, desc, action
export const MAX_LONG_FIELD_LENGTH = 1000; // details, detail, reason
export const MAX_MESSAGE_SIZE = 2048; // 2 KB

// --- Helpers ---

export function generatePairingCode(): string {
  let code = "";
  for (let i = 0; i < PAIRING_CODE_LENGTH; i++) {
    code += PAIRING_CODE_ALPHABET[Math.floor(Math.random() * PAIRING_CODE_ALPHABET.length)];
  }
  return code;
}

export function isValidPairingCode(code: string): boolean {
  if (code.length !== PAIRING_CODE_LENGTH) return false;
  for (const ch of code) {
    if (!PAIRING_CODE_ALPHABET.includes(ch)) return false;
  }
  return true;
}
