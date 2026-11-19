import initSqlJs, { type Database } from "sql.js";
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname } from "node:path";

export type { Database } from "sql.js";

const SCHEMA = `
CREATE TABLE IF NOT EXISTS tokens (
  id TEXT PRIMARY KEY,
  token_hash TEXT NOT NULL,
  room_id TEXT NOT NULL,
  label TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  last_used TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_tokens (
  user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
  token_id TEXT REFERENCES tokens(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, token_id)
);

CREATE TABLE IF NOT EXISTS pairings (
  id TEXT PRIMARY KEY,
  room_id TEXT NOT NULL,
  pairing_code TEXT UNIQUE NOT NULL,
  expires_at TEXT NOT NULL,
  claimed INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
`;

let dbPath: string;
let db: Database;
let saveTimer: ReturnType<typeof setTimeout> | null = null;

function scheduleSave(): void {
  if (saveTimer) return;
  saveTimer = setTimeout(() => {
    saveTimer = null;
    const data = db.export();
    writeFileSync(dbPath, Buffer.from(data));
  }, 1000);
}

export async function initDatabase(path: string): Promise<Database> {
  dbPath = path;
  mkdirSync(dirname(path), { recursive: true });

  const SQL = await initSqlJs();

  if (existsSync(path)) {
    const buffer = readFileSync(path);
    db = new SQL.Database(buffer);
  } else {
    db = new SQL.Database();
  }

  db.run("PRAGMA foreign_keys = ON");
  db.run(SCHEMA);
  scheduleSave();

  return db;
}

export function saveDatabase(): void {
  if (saveTimer) {
    clearTimeout(saveTimer);
    saveTimer = null;
  }
  const data = db.export();
  writeFileSync(dbPath, Buffer.from(data));
}

export function runQuery(db: Database, sql: string, params: unknown[] = []): void {
  db.run(sql, params as any[]);
  scheduleSave();
}

export function getOne(db: Database, sql: string, params: unknown[] = []): Record<string, unknown> | undefined {
  const stmt = db.prepare(sql);
  stmt.bind(params as any[]);
  if (stmt.step()) {
    const row = stmt.getAsObject();
    stmt.free();
    return row as Record<string, unknown>;
  }
  stmt.free();
  return undefined;
}

export function getAll(db: Database, sql: string, params: unknown[] = []): Record<string, unknown>[] {
  const results: Record<string, unknown>[] = [];
  const stmt = db.prepare(sql);
  stmt.bind(params as any[]);
  while (stmt.step()) {
    results.push(stmt.getAsObject() as Record<string, unknown>);
  }
  stmt.free();
  return results;
}
