# Wire Protocol Specification

All messages between the MCP server, server, and consumers are JSON objects sent over WebSocket text frames. Every message has a `type` field.

## Message Types

### Producer -> Consumer messages

These are sent by the MCP server (voluntary tools) or the server (hook endpoints) and forwarded to all consumers in the same room.

#### `status`
Updates the pet's display with what the agent is currently doing.

```json
{
  "type": "status",
  "msg": "Refactoring auth module...",
  "mood": "focused",
  "timestamp": "2026-03-17T14:30:00.000Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `msg` | string | yes | What the agent is doing (max 200 chars) |
| `mood` | StatusMood | no | `"focused"`, `"working"`, `"thinking"`, `"idle"`. Default: `"working"` |
| `timestamp` | string (ISO 8601) | yes | When this status was set |

#### `approval`
Requests user approval for a risky action. The consumer must respond with an `approval_response`.

```json
{
  "type": "approval",
  "id": "a1b2c3d4",
  "desc": "Delete 3 test files?",
  "details": "test1.js, test2.js, test3.js",
  "timeout": 300000,
  "timestamp": "2026-03-17T14:30:00.000Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique ID (UUID v4). Used to match response. |
| `desc` | string | yes | Short description of what needs approval |
| `details` | string | no | Additional context |
| `timeout` | number | yes | Timeout in ms. Consumer should show a countdown. |
| `timestamp` | string (ISO 8601) | yes | When the request was created |

#### `permission`
Lighter version of approval for routine permissions.

```json
{
  "type": "permission",
  "id": "d4e5f6g7",
  "action": "Run npm install",
  "details": "Adding 2 new dependencies: lodash, express",
  "timeout": 300000,
  "timestamp": "2026-03-17T14:30:00.000Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique ID (UUID v4). Used to match response. |
| `action` | string | yes | What permission is being requested |
| `details` | string | no | Additional context |
| `timeout` | number | yes | Timeout in ms |
| `timestamp` | string (ISO 8601) | yes | When the request was created |

#### `notify`
Fire-and-forget notification. No response expected.

```json
{
  "type": "notify",
  "event": "tests_passed",
  "mood": "happy",
  "detail": "47/47 tests passing",
  "timestamp": "2026-03-17T14:30:00.000Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `event` | string | yes | Event identifier (see Event types below) |
| `mood` | PetMood | yes | How the pet should feel |
| `detail` | string | no | Additional info to display |
| `timestamp` | string (ISO 8601) | yes | When the event occurred |

#### `mood`
Directly set the pet's mood without a specific event.

```json
{
  "type": "mood",
  "mood": "anxious",
  "reason": "Long-running build in progress...",
  "timestamp": "2026-03-17T14:30:00.000Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `mood` | PetMood | yes | The mood to set |
| `reason` | string | no | Why this mood was set |
| `timestamp` | string (ISO 8601) | yes | When the mood was set |

---

### Consumer -> Producer messages

These are sent by devices/web UI and forwarded by the server to the producer in the same room.

#### `approval_response`
Response to an `approval` request.

```json
{
  "type": "approval_response",
  "id": "a1b2c3d4",
  "approved": true,
  "timestamp": "2026-03-17T14:30:15.000Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Must match the `approval` request `id` |
| `approved` | boolean | yes | `true` = approved, `false` = rejected |
| `timestamp` | string (ISO 8601) | yes | When the user responded |

#### `permission_response`
Response to a `permission` request.

```json
{
  "type": "permission_response",
  "id": "d4e5f6g7",
  "granted": true,
  "timestamp": "2026-03-17T14:30:15.000Z"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Must match the `permission` request `id` |
| `granted` | boolean | yes | `true` = granted, `false` = denied |
| `timestamp` | string (ISO 8601) | yes | When the user responded |

---

### System messages

These are exchanged between clients and the server. They are never forwarded.

#### `register`
Sent by a client immediately after WebSocket connection is established.

```json
{
  "type": "register",
  "role": "producer",
  "roomId": "a1b2c3d4e5f6",
  "token": "..."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `role` | `"producer"` or `"consumer"` | yes | What this client is |
| `roomId` | string | yes | Room identifier (from token provisioning) |
| `token` | string | no | API token (also passed as query param on WS connect) |

#### `register_ack`
Sent by the server to confirm registration.

```json
{
  "type": "register_ack",
  "role": "producer",
  "roomId": "a1b2c3d4e5f6",
  "pairingCode": "A7X9K2",
  "connectedPeers": 2
}
```

#### `ping` / `pong`
Heartbeat messages to keep the connection alive.

```json
{ "type": "ping" }
{ "type": "pong" }
```

Server sends `ping` every 30 seconds. Client must respond with `pong` within 10 seconds or the connection is considered dead.

#### `error`
Sent by the server when something goes wrong.

```json
{
  "type": "error",
  "message": "Invalid pairing code format",
  "code": "INVALID_PAIRING_CODE"
}
```

Error codes:
- `INVALID_PAIRING_CODE` — code is not 6 alphanumeric characters
- `NO_PRODUCER` — consumer tried to send a message but no producer is registered for this room
- `RATE_LIMITED` — too many messages too fast
- `INVALID_MESSAGE` — message could not be parsed as JSON or is missing required fields

#### `dismiss`
Sent by the server when a pending permission/approval request is cancelled (e.g., the requesting client disconnected).

```json
{
  "type": "dismiss",
  "id": "d4e5f6g7"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | The ID of the request being dismissed |

---

## Enums

### StatusMood
Used in `status` messages only. Represents what the agent is doing.

```
"focused" | "working" | "thinking" | "idle"
```

### PetMood
Used in `notify`, `mood`, and `set_mood`. Represents the pet's emotional state.

```
"happy" | "sad" | "excited" | "anxious" | "sleeping" | "angry" | "proud" | "idle"
```

### Event types
Used in `notify` messages. Not enforced — any string is valid — but these are the standard ones:

```
"tests_passed" | "tests_failed"
"build_succeeded" | "build_failed"
"deploy_complete" | "deploy_failed"
"task_complete"
"error"
```

---

## Pairing Code Format

- 6 characters
- Uppercase alphanumeric (A-Z, 0-9)
- Excludes ambiguous characters: `0`, `O`, `I`, `L`, `1` (to avoid confusion when reading)
- Valid alphabet (31 chars): `A B C D E F G H J K M N P Q R S T U V W X Y Z 2 3 4 5 6 7 8 9`
- 31^6 = ~887 million possible codes

---

## Size Limits

- `msg` / `desc` / `action`: max 200 characters
- `details` / `detail` / `reason`: max 1000 characters
- Total message size: max 2 KB
- These limits are enforced by the server. Oversized messages are rejected with `INVALID_MESSAGE`.

---

## Hook HTTP Endpoints

The server exposes HTTP endpoints for Claude Code hooks. These translate between Claude Code's hook JSON format and the Devotchi WebSocket protocol. All hook endpoints require token auth via query parameter.

### POST `/hook/permission?token=TOKEN`

Receives Claude Code `PermissionRequest` hook body, forwards as a `permission` message to consumers, waits for `permission_response`, and returns a hook decision.

**Request body** (sent by Claude Code automatically):
```json
{
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf dist" }
}
```

**Response** (after user approves/rejects on device):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": { "behavior": "allow" }
  }
}
```

- Long-polling: holds the HTTP connection until a consumer responds or timeout (5 minutes).
- If no consumers are connected, returns `{}` immediately (allow by default).

### POST `/hook/status?token=TOKEN`

Receives Claude Code `PostToolUse` hook body, sends a `status` message to consumers. Fire-and-forget.

**Request body:**
```json
{
  "hook_event_name": "PostToolUse",
  "tool_name": "Edit",
  "tool_input": { "file_path": "/work/project/src/index.ts" }
}
```

**Response:** `{}`

### POST `/hook/stop?token=TOKEN`

Receives Claude Code `Stop` hook body, sends `notify` (task_complete) and `mood` (sleeping) to consumers.

**Response:** `{}`

---

## BLE Protocol (future — for ESP32 hardware)

When the device connects via BLE through the phone PWA, the same JSON messages are sent over BLE characteristics. The BLE service definition:

- **Service UUID**: `d3v07c41-0000-1000-8000-00805f9b34fb` (custom base UUID for Devotchi)
- **Status Characteristic** (write): receives status/mood/notify JSON from phone
- **Request Characteristic** (write): receives approval/permission request JSON from phone
- **Response Characteristic** (notify): device sends approval/permission response JSON to phone
- **Device Info Characteristic** (read): `{ battery: 85, firmware: "1.0.0", display: "ssd1351" }`

Messages over BLE use the same JSON format but are limited to 512 bytes per characteristic write (BLE MTU constraint). If a message exceeds this, it must be chunked — but in practice our messages are well under this limit.
