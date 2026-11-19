import { createHash } from "node:crypto";
import type { Middleware } from "koa";
import type { Database } from "../db/index.js";
import { getOne, runQuery } from "../db/index.js";

export function hashToken(token: string): string {
  return createHash("sha256").update(token).digest("hex");
}

export function tokenAuth(db: Database): Middleware {
  return async (ctx, next) => {
    const header = ctx.get("Authorization");
    if (!header || !header.startsWith("Bearer ")) {
      ctx.status = 401;
      ctx.body = { error: "Missing or invalid Authorization header" };
      return;
    }

    const rawToken = header.slice(7);
    const hash = hashToken(rawToken);
    const row = getOne(db, "SELECT id, room_id FROM tokens WHERE token_hash = ?", [hash]);

    if (!row) {
      ctx.status = 401;
      ctx.body = { error: "Invalid token" };
      return;
    }

    runQuery(db, "UPDATE tokens SET last_used = datetime('now') WHERE id = ?", [row.id]);
    ctx.state.tokenId = row.id as string;
    ctx.state.roomId = row.room_id as string;
    await next();
  };
}

export function tokenFromQuery(db: Database): Middleware {
  return async (ctx, next) => {
    const rawToken = ctx.query.token as string | undefined;
    if (!rawToken) {
      ctx.status = 401;
      ctx.body = { error: "Missing token query parameter" };
      return;
    }

    const hash = hashToken(rawToken);
    const row = getOne(db, "SELECT id, room_id FROM tokens WHERE token_hash = ?", [hash]);

    if (!row) {
      ctx.status = 401;
      ctx.body = { error: "Invalid token" };
      return;
    }

    runQuery(db, "UPDATE tokens SET last_used = datetime('now') WHERE id = ?", [row.id]);
    ctx.state.tokenId = row.id as string;
    ctx.state.roomId = row.room_id as string;
    await next();
  };
}

export function lookupTokenHash(db: Database, rawToken: string): { id: string; roomId: string } | null {
  const hash = hashToken(rawToken);
  const row = getOne(db, "SELECT id, room_id FROM tokens WHERE token_hash = ?", [hash]);
  if (!row) return null;
  runQuery(db, "UPDATE tokens SET last_used = datetime('now') WHERE id = ?", [row.id]);
  return { id: row.id as string, roomId: row.room_id as string };
}
