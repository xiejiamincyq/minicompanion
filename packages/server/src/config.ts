import { join } from "node:path";
import { homedir } from "node:os";
import type { ServerConfig, ServerMode } from "@devotchi/shared";

export function loadConfig(): ServerConfig {
  const mode = (process.env.DEVOTCHI_MODE || "single-user") as ServerMode;
  const port = parseInt(process.env.DEVOTCHI_PORT || "8080", 10);
  const dbPath =
    process.env.DEVOTCHI_DB_PATH || join(homedir(), ".devotchi", "devotchi.db");
  const jwtSecret = process.env.DEVOTCHI_JWT_SECRET;
  const corsOrigins = process.env.DEVOTCHI_CORS_ORIGINS
    ? process.env.DEVOTCHI_CORS_ORIGINS.split(",").map((s) => s.trim())
    : undefined;

  if (mode === "multi-user" && !jwtSecret) {
    throw new Error(
      "DEVOTCHI_JWT_SECRET is required in multi-user mode"
    );
  }

  return { mode, port, dbPath, jwtSecret, corsOrigins };
}
