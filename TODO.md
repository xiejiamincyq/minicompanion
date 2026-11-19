# TODO

## MVP (current)

- [ ] Deploy server to a hosted environment (Railway/Render/Fly.io)
- [ ] Test with server on remote URL instead of localhost
- [ ] ESP32 firmware — first prototype with TFT LCD + buttons
- [ ] 3D print first case prototype

## Research

- [ ] Investigate Claude Code Buddy system — check how it works and whether Devotchi can integrate with it or replace hooks with it

## Soon

- [ ] Web UI auto-reconnect when server restarts
- [ ] Structured logging in server (timestamps, JSON output)
- [ ] Rate limiting on HTTP hook endpoints
- [ ] Max connection limit on server
- [ ] Web UI: show battery level, connection quality
- [ ] Publish `devotchi` and `@devotchi/server` to npm

## Later

- [ ] Multi-user mode (accounts, signup, token management)
- [ ] TLS/WSS support for production deployment
- [ ] Phone PWA as BLE bridge to ESP32
- [ ] Server clustering / horizontal scaling
- [ ] `ask_question` tool — freeform text input from device
- [ ] Notification sounds/vibration patterns per event type
- [ ] Community pet skins (pixel art sprite sets)
