import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import fs from "node:fs/promises";
import { z } from "zod";

import {
  capturePane,
  ensureSession,
  headlessAsk,
  listProviders,
  sendInput,
  status,
  tmuxAsk,
  waitForResponse,
  waitForStart,
  writeInputFile
} from "./core.js";

const providerSchema = z
  .enum(["codex", "claude", "grok", "antigravity", "agy", "gemini", "gpt", "openai", "xai"])
  .describe("LLM provider. Aliases: agy/gemini -> antigravity, gpt/openai -> codex, xai -> grok.");

const optionalCommon = {
  provider: providerSchema,
  sessionName: z
    .string()
    .optional()
    .describe("tmux session name. Defaults to llm-router provider defaults such as codex-mcp."),
  timeoutMs: z
    .number()
    .int()
    .positive()
    .optional()
    .describe("Maximum wait time in milliseconds."),
  stateDir: z
    .string()
    .optional()
    .describe("Runtime state directory for generated Markdown input, prompts, and responses."),
  model: z
    .string()
    .optional()
    .describe("Provider model to request. Codex/Claude/Grok use CLI flags; Antigravity receives this as an in-prompt instruction because agy exposes no model flag.")
};

export async function main() {
  const version = await loadPackageVersion();
  const server = new McpServer({
    name: "llm-router-mcp",
    version
  });

  server.registerTool(
    "llm_list_providers",
    {
      title: "List LLM providers",
      description:
        "Show the providers supported by llm-router-mcp, their default sessions, model defaults, and model flag support.",
      inputSchema: {}
    },
    async () => jsonContent({ providers: listProviders() })
  );

  server.registerTool(
    "llm_write_input",
    {
      title: "Write Markdown input",
      description:
        "Write a Markdown prompt to the llm-router state directory and return inputPath for tmux or headless calls.",
      inputSchema: {
        provider: providerSchema.optional(),
        markdown: z.string().min(1).describe("Markdown prompt content."),
        filename: z
          .string()
          .optional()
          .describe("Optional .md filename. Path components are ignored."),
        stateDir: optionalCommon.stateDir
      }
    },
    async (args) => jsonContent(await writeInputFile(args))
  );

  server.registerTool(
    "llm_tmux_start",
    {
      title: "Start persistent LLM tmux session",
      description:
        "Create or reuse a provider tmux session. Reusing the session preserves conversation context.",
      inputSchema: {
        provider: optionalCommon.provider,
        sessionName: optionalCommon.sessionName,
        command: z
          .string()
          .optional()
          .describe("Command tmux should run when creating the session. Overrides provider defaults."),
        model: optionalCommon.model,
        cwd: z
          .string()
          .optional()
          .describe("Working directory for a newly created session. Defaults to a provider scratch workdir."),
        timeoutMs: optionalCommon.timeoutMs,
        stateDir: optionalCommon.stateDir,
        columns: z.number().int().positive().optional(),
        rows: z.number().int().positive().optional()
      }
    },
    async (args) => jsonContent(await ensureSession(args))
  );

  server.registerTool(
    "llm_tmux_send",
    {
      title: "Send Markdown input to persistent LLM",
      description:
        "Send a Markdown input file through tmux and return nonce markers. Use llm_tmux_wait to collect the answer.",
      inputSchema: {
        provider: optionalCommon.provider,
        inputPath: z.string().describe("Absolute or relative path to a .md/.markdown input file."),
        nonce: z
          .string()
          .optional()
          .describe("Optional caller-supplied unique nonce. Generated when omitted."),
        sessionName: optionalCommon.sessionName,
        command: z
          .string()
          .optional()
          .describe("Command used only if the tmux session must be created."),
        model: optionalCommon.model,
        cwd: z
          .string()
          .optional()
          .describe("Working directory used only if the tmux session must be created."),
        timeoutMs: optionalCommon.timeoutMs,
        stateDir: optionalCommon.stateDir,
        columns: z.number().int().positive().optional(),
        rows: z.number().int().positive().optional()
      }
    },
    async (args) => jsonContent(await sendInput(args))
  );

  server.registerTool(
    "llm_tmux_wait_start",
    {
      title: "Wait for persistent LLM start marker",
      description:
        "Wait until the provider prints the start marker for a nonce. This confirms the request began.",
      inputSchema: {
        provider: optionalCommon.provider,
        nonce: z.string().describe("Nonce returned by llm_tmux_send."),
        sessionName: optionalCommon.sessionName,
        timeoutMs: optionalCommon.timeoutMs,
        pollMs: z.number().int().positive().optional(),
        captureLines: z.number().int().positive().optional(),
        stateDir: optionalCommon.stateDir
      }
    },
    async (args) => jsonContent(await waitForStart(args))
  );

  server.registerTool(
    "llm_tmux_wait",
    {
      title: "Wait for persistent LLM response",
      description:
        "Wait until the provider prints the done marker for a nonce. The answer is also written to a Markdown response file.",
      inputSchema: {
        provider: optionalCommon.provider,
        nonce: z.string().describe("Nonce returned by llm_tmux_send."),
        sessionName: optionalCommon.sessionName,
        timeoutMs: optionalCommon.timeoutMs,
        pollMs: z.number().int().positive().optional(),
        captureLines: z.number().int().positive().optional(),
        stateDir: optionalCommon.stateDir
      }
    },
    async (args) => jsonContent(await waitForResponse(args))
  );

  server.registerTool(
    "llm_tmux_ask",
    {
      title: "Ask persistent LLM and wait",
      description:
        "Convenience tool: send a Markdown input file to a provider through tmux, then wait for the done nonce marker.",
      inputSchema: {
        provider: optionalCommon.provider,
        inputPath: z.string().describe("Absolute or relative path to a .md/.markdown input file."),
        nonce: z
          .string()
          .optional()
          .describe("Optional caller-supplied unique nonce. Generated when omitted."),
        sessionName: optionalCommon.sessionName,
        command: z
          .string()
          .optional()
          .describe("Command used only if the tmux session must be created."),
        model: optionalCommon.model,
        cwd: z
          .string()
          .optional()
          .describe("Working directory used only if the tmux session must be created."),
        timeoutMs: optionalCommon.timeoutMs,
        pollMs: z.number().int().positive().optional(),
        captureLines: z.number().int().positive().optional(),
        stateDir: optionalCommon.stateDir,
        columns: z.number().int().positive().optional(),
        rows: z.number().int().positive().optional()
      }
    },
    async (args) => jsonContent(await tmuxAsk(args))
  );

  server.registerTool(
    "llm_headless_ask",
    {
      title: "Ask LLM once without persistent context",
      description:
        "Run a one-shot provider CLI call for questions that do not need persistent context. Input and output are Markdown files.",
      inputSchema: {
        provider: optionalCommon.provider,
        inputPath: z
          .string()
          .optional()
          .describe("Absolute or relative path to a .md/.markdown input file. Use this or markdown."),
        markdown: z
          .string()
          .optional()
          .describe("Markdown prompt content. Written to inputPath automatically when inputPath is omitted."),
        filename: z.string().optional(),
        nonce: z
          .string()
          .optional()
          .describe("Optional caller-supplied unique nonce. Generated when omitted."),
        model: optionalCommon.model,
        cwd: z
          .string()
          .optional()
          .describe("Working directory for the one-shot command. Defaults to a provider scratch workdir."),
        timeoutMs: optionalCommon.timeoutMs,
        stateDir: optionalCommon.stateDir
      }
    },
    async (args) => jsonContent(await headlessAsk(args))
  );

  server.registerTool(
    "llm_tmux_status",
    {
      title: "Check persistent LLM tmux status",
      description:
        "Capture tmux pane state and optionally check whether a nonce has started or completed.",
      inputSchema: {
        provider: optionalCommon.provider,
        nonce: z
          .string()
          .optional()
          .describe("Optional nonce to check for start/done markers in pane output."),
        sessionName: optionalCommon.sessionName,
        lines: z.number().int().positive().optional()
      }
    },
    async (args) => jsonContent(await status(args))
  );

  server.registerTool(
    "llm_tmux_capture",
    {
      title: "Capture persistent LLM tmux pane",
      description: "Return raw tmux pane text for debugging.",
      inputSchema: {
        provider: optionalCommon.provider,
        sessionName: optionalCommon.sessionName,
        lines: z.number().int().positive().optional()
      }
    },
    async (args) => jsonContent({ paneText: await capturePane(args) })
  );

  await server.connect(new StdioServerTransport());
}

export async function loadPackageVersion() {
  const manifestUrl = new URL("../package.json", import.meta.url);
  const manifest = JSON.parse(await fs.readFile(manifestUrl, "utf8"));
  if (typeof manifest.version !== "string" || manifest.version.trim() === "") {
    throw new Error("llm-router-mcp package.json must declare a non-empty version");
  }
  return manifest.version;
}

function jsonContent(value) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(value, null, 2)
      }
    ]
  };
}
