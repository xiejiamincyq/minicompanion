import { randomUUID } from "node:crypto";
import Router from "@koa/router";
import type { Database } from "../db/index.js";
import { runQuery, getAll, getOne } from "../db/index.js";
import { generatePairingCode } from "@devotchi/shared";
import { tokenAuth, hashToken } from "../middleware/auth.js";

const PAIRING_EXPIRY_MINUTES = 5;

export function deviceRoutes(db: Database): Router {
  const router = new Router({ prefix: "/api" });
  const auth = tokenAuth(db);

  router.get("/devices", auth, async (ctx) => {
    const rows = getAll(
      db,
      "SELECT id, room_id, label, last_used FROM tokens WHERE room_id = ?",
      [ctx.state.roomId]
    );

    ctx.body = {
      devices: rows.map((r) => ({
        id: r.id,
        roomId: r.room_id,
        lastSeen: r.last_used,
        label: r.label,
      })),
    };
  });

  router.post("/pair", auth, async (ctx) => {
    const id = randomUUID().replace(/-/g, "").slice(0, 8);
    const pairingCode = generatePairingCode();
    const expiresAt = new Date(Date.now() + PAIRING_EXPIRY_MINUTES * 60_000).toISOString();

    runQuery(
      db,
      "INSERT INTO pairings (id, room_id, pairing_code, expires_at) VALUES (?, ?, ?, ?)",
      [id, ctx.state.roomId, pairingCode, expiresAt]
    );

    ctx.status = 201;
    ctx.body = { pairingCode, expiresAt };
  });

  router.post("/pair/claim", async (ctx) => {
    const body = ctx.request.body as { code?: string } | undefined;
    if (!body?.code) {
      ctx.status = 400;
      ctx.body = { error: "code is required" };
      return;
    }

    const code = body.code.toUpperCase();
    const row = getOne(
      db,
      "SELECT id, room_id, expires_at, claimed FROM pairings WHERE pairing_code = ?",
      [code]
    );

    if (!row) {
      ctx.status = 404;
      ctx.body = { error: "Invalid pairing code" };
      return;
    }

    if (row.claimed) {
      ctx.status = 410;
      ctx.body = { error: "Pairing code already used" };
      return;
    }

    if (new Date(row.expires_at as string) < new Date()) {
      ctx.status = 410;
      ctx.body = { error: "Pairing code expired" };
      return;
    }

    // Mark as claimed
    runQuery(db, "UPDATE pairings SET claimed = 1 WHERE id = ?", [row.id]);

    // Create a device token in the same room
    const deviceToken = randomUUID();
    const deviceTokenId = randomUUID().replace(/-/g, "").slice(0, 8);
    const hash = hashToken(deviceToken);

    runQuery(
      db,
      "INSERT INTO tokens (id, token_hash, room_id, label) VALUES (?, ?, ?, ?)",
      [deviceTokenId, hash, row.room_id, "device"]
    );

    ctx.status = 201;
    ctx.body = { token: deviceToken, roomId: row.room_id };
  });

  return router;
}
