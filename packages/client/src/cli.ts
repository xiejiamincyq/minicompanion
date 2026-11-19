#!/usr/bin/env node
import { Command } from "commander";
import { loadConfig, saveConfig, provisionToken } from "./config.js";
import { startMcpServer } from "./mcp.js";
import { startWebServer } from "./web-server.js";
import { configureHooks } from "./hooks.js";
import { startLocalBroker } from "./local-broker.js";
import { connect } from "./connection.js";
import { DEFAULT_CLIENT_WEB_PORT } from "@devotchi/shared";

const program = new Command();

program
  .name("devotchi")
  .description("Devotchi — AI coding agent companion")
  .version("0.1.0");

program
  .command("start", { isDefault: true })
  .description("Start the Devotchi dashboard")
  .option("--server <url>", "Devotchi server URL")
  .option("--local", "Run with embedded local broker")
  .option("--port <number>", "Web UI port", String(DEFAULT_CLIENT_WEB_PORT))
  .option("--no-open", "Don't open browser automatically")
  .action(async (opts) => {
    let config = await loadConfig();

    if (opts.server) config.serverUrl = opts.server;
    if (opts.port) config.webPort = parseInt(opts.port, 10);
    if (opts.local) config.localMode = true;

    if (config.localMode) {
      const brokerPort = config.webPort + 1;
      await startLocalBroker(brokerPort);
      config.serverUrl = `http://localhost:${brokerPort}`;
    }

    // Provision token from server if needed
    if (!config.localMode) {
      config = await provisionToken(config);
    }

    connect(config);
    await startWebServer(config);

    if (opts.open !== false) {
      const open = (await import("open")).default;
      await open(`http://localhost:${config.webPort}`);
    }
  });

program
  .command("mcp")
  .description("Run MCP server on stdio (for claude mcp add)")
  .option("--server <url>", "Devotchi server URL")
  .action(async (opts) => {
    let config = await loadConfig();
    if (opts.server) config.serverUrl = opts.server;

    if (!config.localMode) {
      config = await provisionToken(config);
    }

    await startMcpServer(config);
  });

program
  .command("setup")
  .description("Auto-configure Claude Code hooks")
  .option("--server <url>", "Devotchi server URL")
  .option("--dir <path>", "Project directory", process.cwd())
  .action(async (opts) => {
    let config = await loadConfig();
    if (opts.server) config.serverUrl = opts.server;

    // Ensure we have a token
    config = await provisionToken(config);

    await configureHooks(config, opts.dir);
    console.log("Claude Code hooks configured in", opts.dir);
    console.log("  Server URL:", config.serverUrl);
    console.log("  Token: ****" + config.token.slice(-8));
    console.log("  Hooks use token-based auth (no pairing code in URLs)");
  });

program
  .command("config")
  .description("Show current configuration")
  .action(async () => {
    const config = await loadConfig();
    const display = {
      ...config,
      token: config.token ? "****" + config.token.slice(-8) : "(none)",
    };
    console.log(JSON.stringify(display, null, 2));
  });

program
  .command("pair")
  .description("Generate a new pairing code for device setup")
  .action(async () => {
    let config = await loadConfig();
    config = await provisionToken(config);

    const baseUrl = config.serverUrl.replace(/\/$/, "");
    const res = await fetch(`${baseUrl}/api/pair`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${config.token}`,
      },
    });

    if (!res.ok) {
      console.error("Failed to create pairing code:", res.status);
      process.exit(1);
    }

    const data = await res.json() as { pairingCode: string; expiresAt: string };
    console.log(`Pairing code: ${data.pairingCode}`);
    console.log(`Expires: ${data.expiresAt}`);
    console.log("Enter this code on your Devotchi device to pair it.");
  });

program.parse();
