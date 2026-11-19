import Router from "@koa/router";
import type { Database } from "../db/index.js";
import {
  type DevotchiMessage,
  DEFAULT_APPROVAL_TIMEOUT,
} from "@devotchi/shared";
import type { RoomState } from "../ws/rooms.js";
import { tokenFromQuery } from "../middleware/auth.js";

function generateId(): string {
  return crypto.randomUUID().replace(/-/g, "").slice(0, 8);
}

export function hookRoutes(state: RoomState, db: Database): Router {
  const router = new Router({ prefix: "/hook" });
  const auth = tokenFromQuery(db);

  router.post("/permission", auth, async (ctx) => {
    const roomId = ctx.state.roomId as string;
    const room = state.rooms.get(roomId);

    if (!room || room.consumers.size === 0) {
      console.log(`[hook/permission] no consumers for room ${roomId}, allowing`);
      ctx.body = {};
      return;
    }

    const body = ctx.request.body as Record<string, unknown> | undefined;
    if (!body) {
      ctx.status = 400;
      ctx.body = { error: "Invalid JSON body" };
      return;
    }

    const id = generateId();
    const toolName = (body.tool_name as string) || "unknown";
    const toolInput = body.tool_input || {};
    const details =
      typeof toolInput === "object"
        ? JSON.stringify(toolInput).slice(0, 1000)
        : String(toolInput).slice(0, 1000);

    const msg: DevotchiMessage = {
      type: "permission",
      id,
      action: toolName,
      details,
      timeout: DEFAULT_APPROVAL_TIMEOUT,
      timestamp: new Date().toISOString(),
    };

    state.sendToConsumers(roomId, msg);
    console.log(`[hook/permission] ${toolName} -> room ${roomId} (id=${id})`);

    const res = ctx.res;
    const response = await new Promise<DevotchiMessage | null>((resolve) => {
      const timer = setTimeout(() => {
        state.pendingHookRequests.delete(id);
        resolve(null);
      }, DEFAULT_APPROVAL_TIMEOUT);

      state.pendingHookRequests.set(id, { resolve, timer });

      res.on("close", () => {
        if (res.writableEnded) return;
        const pending = state.pendingHookRequests.get(id);
        if (pending) {
          clearTimeout(pending.timer);
          state.pendingHookRequests.delete(id);
          state.sendToConsumers(roomId, { type: "dismiss", id });
          console.log(`[hook/permission] ${id} -> dismissed (client disconnected)`);
          resolve(null);
        }
      });
    });

    if (response && response.type === "permission_response") {
      const granted = response.granted;
      console.log(`[hook/permission] ${id} -> ${granted ? "allow" : "deny"}`);
      ctx.body = {
        hookSpecificOutput: {
          hookEventName: "PermissionRequest",
          decision: { behavior: granted ? "allow" : "deny" },
        },
      };
    } else {
      console.log(`[hook/permission] ${id} -> timeout`);
      ctx.body = {
        hookSpecificOutput: {
          hookEventName: "PermissionRequest",
          decision: { behavior: "deny" },
        },
      };
    }
  });

  router.post("/status", auth, async (ctx) => {
    const roomId = ctx.state.roomId as string;

    try {
      const body = ctx.request.body as Record<string, unknown> | undefined;
      const toolName = (body?.tool_name as string) || "unknown";
      const toolInput = (body?.tool_input as Record<string, unknown>) || {};

      let description = toolName;
      if (toolName === "Bash" && toolInput.command) {
        description = String(toolInput.command).slice(0, 200);
      } else if (
        (toolName === "Write" || toolName === "Edit") &&
        toolInput.file_path
      ) {
        description = `${toolName}: ${toolInput.file_path}`;
      }

      state.sendToConsumers(roomId, {
        type: "status",
        msg: description.slice(0, 200),
        mood: "working",
        timestamp: new Date().toISOString(),
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      console.error("[hook/status] error:", message);
    }

    ctx.body = {};
  });

  router.post("/stop", auth, async (ctx) => {
    const roomId = ctx.state.roomId as string;

    state.sendToConsumers(roomId, {
      type: "notify",
      event: "task_complete",
      mood: "idle",
      detail: "Agent stopped",
      timestamp: new Date().toISOString(),
    });

    state.sendToConsumers(roomId, {
      type: "mood",
      mood: "sleeping",
      reason: "Waiting for instructions",
      timestamp: new Date().toISOString(),
    });

    ctx.body = {};
  });

  return router;
}
