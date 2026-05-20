import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

import { killSession } from "../src/core.js";

test("stdio MCP server exposes the unified LLM router tools", async () => {
  const client = new Client({
    name: "llm-router-mcp-test-client",
    version: "0.0.0"
  });
  const transport = new StdioClientTransport({
    command: "node",
    args: ["bin/llm-router-mcp.js"],
    cwd: process.cwd(),
    stderr: "pipe"
  });

  try {
    await client.connect(transport);
    const result = await client.listTools();
    const names = result.tools.map((tool) => tool.name).sort();

    assert.deepEqual(names, [
      "llm_headless_ask",
      "llm_list_providers",
      "llm_tmux_ask",
      "llm_tmux_capture",
      "llm_tmux_send",
      "llm_tmux_start",
      "llm_tmux_status",
      "llm_tmux_wait",
      "llm_tmux_wait_start",
      "llm_write_input"
    ]);
  } finally {
    await client.close();
  }
});

test("stdio MCP server can ask a provider through a tmux-backed fake session", async (t) => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "llm-router-mcp-stdio-"));
  const sessionName = `lrm-stdio-${process.pid}-${Date.now()}`;
  const fakeLlm = path.resolve("test/fixtures/fake-llm.js");
  t.after(async () => {
    await killSession({ provider: "claude", sessionName });
    await fs.rm(tmp, { recursive: true, force: true });
  });

  const client = new Client({
    name: "llm-router-mcp-test-client",
    version: "0.0.0"
  });
  const transport = new StdioClientTransport({
    command: "node",
    args: ["bin/llm-router-mcp.js"],
    cwd: process.cwd(),
    stderr: "pipe"
  });

  try {
    await client.connect(transport);
    const written = parseToolResult(
      await client.callTool({
        name: "llm_write_input",
        arguments: {
          provider: "claude",
          markdown: "End-to-end MCP request.",
          filename: "stdio.md",
          stateDir: tmp
        }
      })
    );

    const asked = parseToolResult(
      await client.callTool({
        name: "llm_tmux_ask",
        arguments: {
          provider: "claude",
          inputPath: written.inputPath,
          sessionName,
          command: `node ${fakeLlm}`,
          cwd: process.cwd(),
          stateDir: tmp,
          timeoutMs: 5000,
          pollMs: 50
        }
      })
    );

    assert.equal(asked.completed, true);
    assert.equal(asked.timedOut, false);
    assert.match(asked.answer, /fake tmux/);
    assert.match(asked.responsePath, /\.response\.md$/);
    assert.match(await fs.readFile(asked.responsePath, "utf8"), /fake tmux/);
  } finally {
    await client.close();
  }
});

function parseToolResult(result) {
  assert.equal(result.content.length, 1);
  assert.equal(result.content[0].type, "text");
  return JSON.parse(result.content[0].text);
}
