import { randomUUID } from "node:crypto";
import Router from "@koa/router";
import bcrypt from "bcryptjs";
import type { Database } from "../db/index.js";
import { runQuery, getOne } from "../db/index.js";
import type { ServerConfig } from "@devotchi/shared";
import { hashToken } from "../middleware/auth.js";

export function authRoutes(db: Database, config: ServerConfig): Router {
  const router = new Router({ prefix: "/api/auth" });

  router.post("/token", async (ctx) => {
    const body = ctx.request.body as { label?: string } | undefined;
    const label = body?.label ?? null;
    const rawToken = randomUUID();
    const id = randomUUID().replace(/-/g, "").slice(0, 8);
    const roomId = randomUUID().replace(/-/g, "").slice(0, 12);
    const hash = hashToken(rawToken);

    runQuery(db, "INSERT INTO tokens (id, token_hash, room_id, label) VALUES (?, ?, ?, ?)", [id, hash, roomId, label]);

    ctx.status = 201;
    ctx.body = { token: rawToken, id, roomId };
  });

  if (config.mode === "multi-user") {
    router.post("/register", async (ctx) => {
      const body = ctx.request.body as { email?: string; password?: string } | undefined;
      if (!body?.email || !body?.password) {
        ctx.status = 400;
        ctx.body = { error: "email and password are required" };
        return;
      }

      const existing = getOne(db, "SELECT id FROM users WHERE email = ?", [body.email]);
      if (existing) {
        ctx.status = 409;
        ctx.body = { error: "Email already registered" };
        return;
      }

      const id = randomUUID().replace(/-/g, "").slice(0, 16);
      const passwordHash = await bcrypt.hash(body.password, 12);
      runQuery(db, "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)", [id, body.email, passwordHash]);

      ctx.status = 201;
      ctx.body = { userId: id };
    });

    router.post("/login", async (ctx) => {
      const body = ctx.request.body as { email?: string; password?: string } | undefined;
      if (!body?.email || !body?.password) {
        ctx.status = 400;
        ctx.body = { error: "email and password are required" };
        return;
      }

      const row = getOne(db, "SELECT id, password_hash FROM users WHERE email = ?", [body.email]);
      if (!row) {
        ctx.status = 401;
        ctx.body = { error: "Invalid credentials" };
        return;
      }

      const valid = await bcrypt.compare(body.password, row.password_hash as string);
      if (!valid) {
        ctx.status = 401;
        ctx.body = { error: "Invalid credentials" };
        return;
      }

      const sessionToken = randomUUID();
      ctx.body = { sessionToken, userId: row.id };
    });
  }

  return router;
}
