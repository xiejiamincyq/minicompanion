# Devotchi

Tamagotchi-style portable device for AI coding agents. Connects via MCP to show agent status, handle approvals, and reflect project mood on a physical TFT LCD screen with buttons.

## Project overview

- Monorepo using pnpm workspaces
- TypeScript for all software packages, C (ESP-IDF) for firmware
- Packages: `shared` (types/protocol/API contracts), `server` (Koa WebSocket server + SQLite), `client` (CLI + web UI + MCP)
- Firmware in `firmware/` — separate build, not part of pnpm workspaces

## Architecture

See `docs/architecture.md` for the full system architecture.
See `docs/protocol.md` for the wire protocol specification.
See `hardware/README.md` for hardware design and component details.

## Commands

```bash
pnpm install              # Install all workspace dependencies
pnpm run build            # Build all TypeScript packages
pnpm run server           # Start the server on port 8080
pnpm run client           # Start the client dashboard
pnpm run dev              # Start client in dev mode (Vite HMR)
```

## MCP server registration

```bash
claude mcp add devotchi -- devotchi mcp
# Or from source:
claude mcp add devotchi -- node packages/client/dist/cli.js mcp
```

## Client CLI

```bash
devotchi start                    # Start dashboard (default: connects to hosted server)
devotchi start --local            # Start with embedded local server
devotchi start --server <url>     # Connect to custom server
devotchi mcp                      # Run MCP server on stdio
devotchi setup                    # Auto-configure Claude Code hooks
devotchi config                   # Show current configuration
```

## Key design decisions

- The server routes WebSocket messages by pairing code with SQLite-backed token auth
- The MCP server gracefully degrades if the server is unreachable
- Approvals are handled automatically via Claude Code hooks (http type) → server HTTP endpoints — no AI involvement needed
- The server holds hook HTTP requests open until the device responds (long-polling pattern)
- The protocol is intentionally simple — JSON over WebSocket, messages under 2KB
- The client includes an embedded broker for standalone `--local` mode
- Token-first auth — anonymous tokens by default, accounts optional for multi-user hosted mode
- Display uses ST7789 TFT LCD (2.0", 320x240, color) with ESP-IDF `esp_lcd` driver + LovyanGFX for graphics
- Single PCB design — power and logic on one board

## Directory structure

```
packages/shared/src/           — Protocol types, API types, config types
packages/server/src/           — Koa server (routes, WebSocket, SQLite)
packages/client/src/           — CLI, MCP server, hook config, connection
packages/client/web/           — Web UI (Vite SPA, dashboard + simulator)
firmware/                      — ESP32 firmware (C, ESP-IDF)
docs/                          — Architecture, protocol, hardware docs + datasheets
```

## Commit message rules

- Short subject line (under 72 chars)
- No co-authored-by or AI attribution
- Use conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`
- No body unless absolutely needed

## Hooks (automatic — no AI action needed)

Permission requests are handled automatically via Claude Code hooks configured in `.claude/settings.local.json`. When Claude Code shows a permission prompt, an HTTP hook POSTs to the server, which forwards to the device. The user approves/rejects on the device and Claude Code proceeds or stops. Status updates are also sent automatically after Bash/Write/Edit tool use.

Run `devotchi setup` to auto-configure hooks.

## Devotchi MCP tool usage (voluntary — for AI agents with Devotchi connected)

When this MCP server is registered in a Claude Code session, the agent should use the tools as follows:

- Call `show_status` when starting a new task or subtask
- Call `notify` when tests pass/fail, builds succeed/fail, or tasks complete
- Call `set_mood` to reflect the overall project state

### Mood guide

- `happy` — tests passing, builds green, tasks completing
- `sad` — tests failing, errors, things not working
- `focused` — deep in a complex task
- `thinking` — analyzing, planning, reading code
- `anxious` — waiting for long operations, risky changes ahead
- `excited` — just shipped something, breakthrough moment
- `proud` — all tests green after a big refactor
- `angry` — repeated failures, flaky tests
- `sleeping` — idle, waiting for instructions
