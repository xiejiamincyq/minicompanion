import "./types.js";
import { createServer } from "node:http";
import Koa from "koa";
import cors from "@koa/cors";
import { loadConfig } from "./config.js";
import { initDatabase, saveDatabase } from "./db/index.js";
import { authRoutes } from "./routes/auth.js";
import { deviceRoutes } from "./routes/devices.js";
import { hookRoutes } from "./routes/hooks.js";
import { RoomState } from "./ws/rooms.js";
import { attachWebSocket } from "./ws/router.js";

async function main(): Promise<void> {
  const config = loadConfig();
  const db = await initDatabase(config.dbPath);
  const state = new RoomState();

  const app = new Koa();

  app.use(
    cors({
      origin: config.corsOrigins
        ? (ctx) => {
            const origin = ctx.get("Origin");
            return config.corsOrigins!.includes(origin) ? origin : "";
          }
        : "*",
    })
  );

  app.use(async (ctx, next) => {
    if (ctx.is("application/json")) {
      const chunks: Buffer[] = [];
      for await (const chunk of ctx.req) {
        chunks.push(chunk as Buffer);
      }
      const raw = Buffer.concat(chunks).toString();
      if (raw) {
        try {
          ctx.request.body = JSON.parse(raw);
        } catch {
          ctx.status = 400;
          ctx.body = { error: "Invalid JSON" };
          return;
        }
      }
    }
    await next();
  });

  const health = new (await import("@koa/router")).default();
  health.get("/", async (ctx) => {
    ctx.body = {
      status: "ok",
      connections: state.connectionCount,
      mode: config.mode,
    };
  });

  const auth = authRoutes(db, config);
  const devices = deviceRoutes(db);
  const hooks = hookRoutes(state, db);

  app.use(health.routes()).use(health.allowedMethods());
  app.use(auth.routes()).use(auth.allowedMethods());
  app.use(devices.routes()).use(devices.allowedMethods());
  app.use(hooks.routes()).use(hooks.allowedMethods());

  const server = createServer(app.callback());
  const { wss, heartbeatInterval } = attachWebSocket(server, state, db);

  function shutdown(): void {
    console.log("[shutdown] closing connections...");
    clearInterval(heartbeatInterval);

    for (const [id, pending] of state.pendingHookRequests) {
      clearTimeout(pending.timer);
      state.pendingHookRequests.delete(id);
    }

    for (const [ws] of state.clients) {
      ws.close(1001, "server shutting down");
    }

    saveDatabase();

    wss.close(() => {
      server.close(() => {
        console.log("[shutdown] done");
        process.exit(0);
      });
    });

    setTimeout(() => process.exit(0), 5000).unref();
  }

  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);

  server.listen(config.port, () => {
    console.log(`Devotchi server listening on port ${config.port} (${config.mode} mode)`);
  });
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
