import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  buildTmuxCommand,
  headlessAsk,
  killSession,
  listProviders,
  runCommand,
  sendInput,
  status,
  tmuxAsk,
  waitForResponse,
  writeInputFile
} from "../src/core.js";

const PROVIDERS = ["codex", "claude", "grok", "antigravity"];

async function requireTmux(t) {
  const result = await runCommand("tmux", ["-V"], {
    allowFailure: true,
    timeoutMs: 5000
  });
  if (result.code !== 0) {
    t.skip("tmux is not available");
  }
}

async function makeFixture(t) {
  await requireTmux(t);
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "llm-router-mcp-test-"));
  const fakeLlm = path.resolve("test/fixtures/fake-llm.js");
  const sessionPrefix = `lrm-${process.pid}-${Date.now()}-${Math.random()
    .toString(16)
    .slice(2)}`;
  t.after(async () => {
    for (const provider of PROVIDERS) {
      await killSession({ provider, sessionName: `${sessionPrefix}-${provider}` });
    }
    await fs.rm(tmp, { recursive: true, force: true });
  });
  return {
    tmp,
    fakeCommand: `node ${fakeLlm}`,
    sessionPrefix,
    cwd: process.cwd()
  };
}

async function makeFakePath(t) {
  const fakeBin = await fs.mkdtemp(path.join(os.tmpdir(), "llm-router-fake-bin-"));
  const fakeLlm = path.resolve("test/fixtures/fake-llm.js");
  for (const name of ["codex", "claude", "grok", "agy"]) {
    const target = path.join(fakeBin, name);
    await fs.writeFile(target, `#!/usr/bin/env bash\nnode ${shellQuote(fakeLlm)} "$@"\n`, {
      mode: 0o755
    });
  }
  const oldPathPrefix = process.env.LLM_ROUTER_MCP_PATH_PREFIX;
  process.env.LLM_ROUTER_MCP_PATH_PREFIX = fakeBin;
  t.after(async () => {
    if (oldPathPrefix === undefined) {
      delete process.env.LLM_ROUTER_MCP_PATH_PREFIX;
    } else {
      process.env.LLM_ROUTER_MCP_PATH_PREFIX = oldPathPrefix;
    }
    await fs.rm(fakeBin, { recursive: true, force: true });
  });
}

test("provider list and tmux commands expose all requested CLIs", () => {
  const providers = listProviders();
  assert.deepEqual(
    providers.map((provider) => provider.id),
    PROVIDERS
  );
  assert.match(buildTmuxCommand("codex", "gpt-test"), /codex -m gpt-test/);
  assert.match(buildTmuxCommand("claude", "opus"), /claude --model opus/);
  assert.match(buildTmuxCommand("grok", "grok-test"), /grok --no-alt-screen -m grok-test/);
  assert.equal(buildTmuxCommand("antigravity", "ignored-model"), "agy");
});

test("tmux ask preserves context-capable Markdown nonce protocol for each provider", async (t) => {
  const fixture = await makeFixture(t);

  for (const provider of PROVIDERS) {
    const input = await writeInputFile({
      provider,
      markdown: `# ${provider} review\n\nThis is a long Markdown prompt.\n`,
      filename: `${provider}.md`,
      stateDir: fixture.tmp
    });

    const result = await tmuxAsk({
      provider,
      inputPath: input.inputPath,
      sessionName: `${fixture.sessionPrefix}-${provider}`,
      command: fixture.fakeCommand,
      cwd: fixture.cwd,
      stateDir: fixture.tmp,
      timeoutMs: 5000,
      pollMs: 50
    });

    assert.equal(result.mode, "tmux");
    assert.equal(result.sent, true);
    assert.equal(result.started, true);
    assert.equal(result.completed, true);
    assert.equal(result.timedOut, false);
    assert.match(result.answer, /fake tmux \d+ answer/);
    assert.match(result.responsePath, /\.response\.md$/);
    assert.equal(await fs.readFile(result.responsePath, "utf8"), `${result.answer}\n`);

    const current = await status({
      provider,
      sessionName: `${fixture.sessionPrefix}-${provider}`,
      nonce: result.nonce
    });
    assert.equal(current.running, true);
    assert.equal(current.markerStatus.started, true);
    assert.equal(current.markerStatus.completed, true);
  }
});

test("tmux wait returns timeout state and Markdown fallback when done marker is missing", async (t) => {
  const fixture = await makeFixture(t);
  const input = await writeInputFile({
    provider: "grok",
    markdown: "NO_DONE_MARKER",
    filename: "timeout.md",
    stateDir: fixture.tmp
  });

  const sent = await sendInput({
    provider: "grok",
    inputPath: input.inputPath,
    sessionName: `${fixture.sessionPrefix}-timeout`,
    command: fixture.fakeCommand,
    cwd: fixture.cwd,
    stateDir: fixture.tmp,
    timeoutMs: 5000
  });

  assert.equal(sent.sent, true);

  const waited = await waitForResponse({
    provider: "grok",
    sessionName: `${fixture.sessionPrefix}-timeout`,
    nonce: sent.nonce,
    timeoutMs: 300,
    pollMs: 50,
    stateDir: fixture.tmp
  });
  assert.equal(waited.completed, false);
  assert.equal(waited.timedOut, true);
  assert.match(waited.fallbackPath, /\.fallback\.md$/);
  assert.match(await fs.readFile(waited.fallbackPath, "utf8"), /timed out/);
});

test("headless ask uses one-shot CLI calls and writes Markdown outputs", async (t) => {
  await makeFakePath(t);
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "llm-router-headless-test-"));
  t.after(async () => {
    await fs.rm(tmp, { recursive: true, force: true });
  });

  for (const provider of PROVIDERS) {
    const result = await headlessAsk({
      provider,
      markdown: `# ${provider} one shot\n\nReturn a short answer.`,
      filename: `${provider}.md`,
      stateDir: tmp,
      cwd: process.cwd(),
      timeoutMs: 5000,
      model: provider === "antigravity" ? "ui-selected" : "test-model"
    });

    assert.equal(result.mode, "headless");
    assert.equal(result.success, true);
    assert.equal(result.exitCode, 0);
    assert.match(result.answer, /fake headless answer/);
    assert.match(result.responsePath, /\.response\.md$/);
    assert.match(result.rawResponsePath, /\.raw\.md$/);
    assert.equal(await fs.readFile(result.responsePath, "utf8"), `${result.answer}\n`);
  }
});

function shellQuote(value) {
  return `'${String(value).replace(/'/g, "'\\''")}'`;
}
