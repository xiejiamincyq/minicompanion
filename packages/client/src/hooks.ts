import { readFile, writeFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import type { ClientConfig } from "@devotchi/shared";

interface HookDef {
  type: string;
  url: string;
  timeout?: number;
  [key: string]: unknown;
}

interface HookGroup {
  matcher?: string;
  hooks: HookDef[];
}

interface SettingsFile {
  permissions?: Record<string, unknown>;
  hooks?: Record<string, HookGroup[]>;
  [key: string]: unknown;
}

export async function configureHooks(config: ClientConfig, projectDir: string): Promise<void> {
  const settingsDir = join(projectDir, ".claude");
  const settingsPath = join(settingsDir, "settings.local.json");

  let settings: SettingsFile = {};
  try {
    const raw = await readFile(settingsPath, "utf-8");
    settings = JSON.parse(raw);
  } catch {
    // file doesn't exist or is invalid
  }

  const baseUrl = config.serverUrl.replace(/\/$/, "");
  const token = config.token;

  if (!settings.hooks) {
    settings.hooks = {};
  }

  // Remove old devotchi hooks (any hook with /hook/ in the URL)
  for (const event of Object.keys(settings.hooks)) {
    settings.hooks[event] = settings.hooks[event].filter((group) => {
      group.hooks = group.hooks.filter(
        (h) => !(h.type === "http" && typeof h.url === "string" && h.url.includes("/hook/"))
      );
      return group.hooks.length > 0;
    });
    if (settings.hooks[event].length === 0) {
      delete settings.hooks[event];
    }
  }

  // Add new devotchi hooks with token auth
  settings.hooks.PermissionRequest = [
    ...(settings.hooks.PermissionRequest || []),
    {
      hooks: [
        {
          type: "http",
          url: `${baseUrl}/hook/permission?token=${token}`,
          timeout: 310,
        },
      ],
    },
  ];

  settings.hooks.PostToolUse = [
    ...(settings.hooks.PostToolUse || []),
    {
      matcher: "Bash|Write|Edit",
      hooks: [
        {
          type: "http",
          url: `${baseUrl}/hook/status?token=${token}`,
          timeout: 5,
        },
      ],
    },
  ];

  settings.hooks.Stop = [
    ...(settings.hooks.Stop || []),
    {
      hooks: [
        {
          type: "http",
          url: `${baseUrl}/hook/stop?token=${token}`,
          timeout: 5,
        },
      ],
    },
  ];

  await mkdir(settingsDir, { recursive: true });
  await writeFile(settingsPath, JSON.stringify(settings, null, 2) + "\n");
}
