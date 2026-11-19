# System Architecture

## Overview

Devotchi has 3 software layers plus ESP32 firmware (Layer 4, built separately in C).

```
                    User's PC                          Cloud / LAN
              +--------------------+            +--------------------+
              |                    |   hooks    |                    |
              |   Claude Code   ---|---(HTTP)-->|   Server           |
              |                    |            |   (WebSocket +     |
              |   Client        ---|---(WS)---->|    REST + SQLite)  |
              |   (CLI + MCP)      |            |                    |
              +--------------------+            +---------+----------+
                                                          |
                                                          | WebSocket
                                                          |
                                    +---------------------+---------------------+
                                    |                     |                     |
                              +-----+------+        +----+-----+        +------+-----+
                              |  Web UI    |        |  ESP32   |        |  Phone PWA |
                              | (dashboard)|        | (device) |        |  (future)  |
                              +------------+        +----------+        +------------+
```

## Layer 1: Client (`packages/client/`)

Unified PC application that combines the MCP server, web dashboard, and hook configuration into one CLI tool.

### Components

- **CLI** (`src/cli.ts`) — Commander-based entry point with subcommands: `start`, `mcp`, `setup`, `config`
- **MCP Server** (`src/mcp.ts`) — 3 voluntary tools (show_status, notify, set_mood) over stdio transport
- **Connection** (`src/connection.ts`) — WebSocket connection to server with auto-reconnect
- **Hook Config** (`src/hooks.ts`) — Auto-configures `.claude/settings.local.json`
- **Web Server** (`src/web-server.ts`) — Serves dashboard UI, proxies WebSocket to upstream server
- **Local Broker** (`src/local-broker.ts`) — Embedded minimal server for `--local` mode
- **Web UI** (`web/`) — Vite SPA with pet display, approval modals, event log, settings

### MCP Tools

| Tool | Returns |
|---|---|
| `show_status(message, mood?)` | `{ ok: true }` |
| `notify(event, mood, detail?)` | `{ ok: true }` |
| `set_mood(mood, reason?)` | `{ ok: true }` |

### Configuration

Stored in `~/.devotchi/config.json`:
```json
{
  "serverUrl": "ws://localhost:8080",
  "token": "...",
  "pairingCode": "A7X9K2",
  "webPort": 3456,
  "localMode": false
}
```

---

## Layer 2: Server (`packages/server/`)

Koa-based HTTP + WebSocket server with SQLite persistence and token-based auth.

### Server Modes

- **Single-user** (default): Just tokens, no accounts. For self-hosted and local use.
- **Multi-user**: Accounts, signup, token management. For hosted service.

Set via `DEVOTCHI_MODE=multi-user` env var.

### How pairing works

1. Client calls `POST /api/auth/token` → gets an API token
2. Client calls `POST /api/pair` → gets a pairing code
3. Client connects via WebSocket with token and registers as producer
4. Device connects via WebSocket and registers as consumer with same pairing code
5. Messages flow: producer → server → all consumers with that code

### REST API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/token` | none | Generate anonymous token |
| POST | `/api/auth/register` | none | Create account (multi-user only) |
| POST | `/api/auth/login` | none | Login (multi-user only) |
| GET | `/api/devices` | token | List paired devices |
| POST | `/api/pair` | token | Create pairing code |

### Hook Endpoints

| Endpoint | Hook Event | Behavior |
|---|---|---|
| `POST /hook/permission?token=T` | `PermissionRequest` | Long-poll: waits for device response |
| `POST /hook/status?token=T` | `PostToolUse` | Fire-and-forget: status update |
| `POST /hook/stop?token=T` | `Stop` | Fire-and-forget: agent stopped |

### Key design decisions

- **SQLite persistence** — tokens and pairings survive restarts
- **Token auth** — SHA-256 hashed API tokens for WebSocket and REST auth
- **Multi-consumer** — one producer can have multiple consumers simultaneously
- **Graceful degradation** — if no consumers connected, `/hook/permission` returns allow
- **Same codebase** for hosted and self-hosted (config flag for multi-user mode)

### Configuration (env vars)

| Env Var | Default | Description |
|---------|---------|-------------|
| `DEVOTCHI_PORT` | `8080` | Server port |
| `DEVOTCHI_MODE` | `single-user` | `single-user` or `multi-user` |
| `DEVOTCHI_DB_PATH` | `~/.devotchi/devotchi.db` | SQLite database path |
| `DEVOTCHI_JWT_SECRET` | — | Required for multi-user mode |
| `DEVOTCHI_CORS_ORIGINS` | `*` | Comma-separated allowed origins |

---

## Claude Code Hooks

Approvals and status updates are handled automatically via Claude Code `http` hooks — no AI involvement, zero context cost.

### How it works

1. Claude Code fires a `PermissionRequest` hook → HTTP POST to server's `/hook/permission?token=TOKEN`
2. Server translates to a Devotchi `permission` message, sends to all consumers via WebSocket
3. User approves/rejects on device/simulator
4. Consumer sends `permission_response` back via WebSocket
5. Server returns hook JSON response: `{ decision: { behavior: "allow"|"deny" } }`
6. Claude Code proceeds or blocks — all within one HTTP request/response cycle

Run `devotchi setup` to auto-configure hooks in `.claude/settings.local.json`.

---

## Phone PWA (future)

A companion phone app. Not part of the current build. May be added later as:
- A phone-based Tamagotchi UI (WebSocket to server)
- A BLE bridge between phone and ESP32 device
- Installable as PWA with push notifications for approvals

---

## Layer 4: ESP32 Firmware (`firmware/`)

Written in C using ESP-IDF (not Arduino). Runs on the physical device.

### Responsibilities
- Connect to WiFi and/or BLE
- Receive protocol messages (via WebSocket over WiFi, or via BLE from phone)
- Render Tamagotchi character on ST7789 TFT LCD display (320x240, SPI)
- Handle button presses (approve/reject/action)
- Send responses back
- Manage power (deep sleep, wake on event)
- Drive vibration motor and status LED

See [hardware/README.md](../hardware/README.md) for component details and pin assignments.

---

## Data Flow Examples

### Permission request via hook (automatic)
```
Claude Code wants to run "rm -rf dist"
  → PermissionRequest hook fires
  → HTTP POST to server /hook/permission?token=TOKEN
  → Server generates ID, sends permission message to consumers
  → Device/web UI shows permission modal
  → User presses Approve
  → Device sends permission_response to server
  → Server returns { decision: { behavior: "allow" } }
  → Claude Code proceeds with the command
```

### Status update via hook (automatic)
```
Claude Code finishes running a Bash command
  → PostToolUse hook fires
  → HTTP POST to server /hook/status?token=TOKEN
  → Server sends status message to consumers
  → Device/web UI updates display
  → Server returns {} immediately
```

### Voluntary status update via MCP
```
Claude Code calls show_status("Refactoring auth...", "focused")
  → MCP Server sends status message to server via WebSocket
  → Server forwards to all consumers
  → Device/web UI updates display
  → MCP Server returns {ok: true} to Claude Code
```
