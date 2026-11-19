# Ideas & Notes

## Desktop Devotchi

A larger touchscreen version that sits on your desk. Unlike the portable pocket device (2.0" TFT LCD, 4 buttons), this would have a 3.5"–5" touchscreen with a UI similar to the browser simulator.

**Multi-session management:** The killer feature. Power users run multiple Claude Code sessions across different projects. The desktop device shows all active sessions at once — each project gets its own pet with mood and status. Tap a project to see details, approve/reject pending requests.

The server already supports multiple consumers per room and multiple rooms simultaneously. The desktop device could connect as a consumer to multiple rooms at once, or we could add a "multi-room consumer" mode.

The web dashboard is essentially a prototype of this UI — start from that codebase.

**Hardware ideas:**
- ESP32-S3 with a 3.5" or 5" capacitive touchscreen (ILI9488 or similar)
- Powered via USB-C (desk device, no battery needed)
- Optional: small speaker for notification sounds
- Could run a lightweight web view (LVGL or direct framebuffer) or even a local web server serving the simulator UI on a built-in display

---

## Session Awareness

Right now the device doesn't know which Claude Code session it's connected to. Could add session metadata (project name, directory, git branch) to the register message so the device can show "devotchi — main branch" or "api-refactor" as context.

---

## Approval Queue

When multiple approval requests come in quickly, the current simulator shows one modal at a time. A queue view would let you see all pending requests and batch-approve or prioritize them. Especially useful for the desktop version.

---

## Mood History / Activity Graph

Track mood changes over time and show a small graph on the device — like a heartbeat monitor for your project. Green = tests passing, red = failures. Could be a fun visual for the desktop version.

---

## Community Pet Skins

Let users customize the Tamagotchi character. The current emoji-based display is functional but pixel art sprites would be much more charming. Could have community-contributed sprite sets.

---

## Webhook Integration

Besides Claude Code hooks, support generic webhooks from CI/CD (GitHub Actions, etc.) so the device shows build/deploy status even when no agent is running. The server already has HTTP endpoints — just add a `/webhook` route.
