import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import type { ClientConfig, PetMood, StatusMood } from "@devotchi/shared";
import { connect, sendMessage, disconnect } from "./connection.js";

export async function startMcpServer(config: ClientConfig): Promise<void> {
  connect(config);

  const server = new McpServer({
    name: "devotchi",
    version: "0.1.0",
  });

  server.tool(
    "show_status",
    "Update the Devotchi pet display with what the agent is currently doing",
    {
      msg: z.string().max(200).describe("What the agent is doing"),
      mood: z
        .enum(["focused", "working", "thinking", "idle"])
        .optional()
        .default("working")
        .describe("Agent activity mood"),
    },
    async ({ msg, mood }) => {
      const sent = sendMessage({
        type: "status",
        msg,
        mood: mood as StatusMood,
        timestamp: new Date().toISOString(),
      });
      return {
        content: [{ type: "text" as const, text: JSON.stringify({ ok: true, brokerConnected: sent }) }],
      };
    }
  );

  server.tool(
    "notify",
    "Send a notification to the Devotchi pet (tests passed, build failed, etc.)",
    {
      event: z.string().describe("Event identifier (e.g. tests_passed, build_failed)"),
      mood: z
        .enum(["happy", "sad", "excited", "anxious", "sleeping", "angry", "proud", "idle"])
        .describe("How the pet should feel"),
      detail: z.string().max(1000).optional().describe("Additional info to display"),
    },
    async ({ event, mood, detail }) => {
      const sent = sendMessage({
        type: "notify",
        event,
        mood: mood as PetMood,
        detail,
        timestamp: new Date().toISOString(),
      });
      return {
        content: [{ type: "text" as const, text: JSON.stringify({ ok: true, brokerConnected: sent }) }],
      };
    }
  );

  server.tool(
    "set_mood",
    "Set the Devotchi pet's mood to reflect overall project state",
    {
      mood: z
        .enum(["happy", "sad", "excited", "anxious", "sleeping", "angry", "proud", "idle"])
        .describe("The mood to set"),
      reason: z.string().max(1000).optional().describe("Why this mood was set"),
    },
    async ({ mood, reason }) => {
      const sent = sendMessage({
        type: "mood",
        mood: mood as PetMood,
        reason,
        timestamp: new Date().toISOString(),
      });
      return {
        content: [{ type: "text" as const, text: JSON.stringify({ ok: true, brokerConnected: sent }) }],
      };
    }
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[devotchi] MCP server started on stdio");

  process.stdin.on("end", () => {
    disconnect();
    process.exit(0);
  });
}
