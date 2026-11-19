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
