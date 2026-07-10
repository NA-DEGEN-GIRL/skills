import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

export const PROVIDERS = {
  codex: {
    id: "codex",
    displayName: "Codex",
    envName: "CODEX",
    defaultSessionName: "codex-mcp",
    defaultCommand: "codex",
    defaultModel: "gpt-5.4",
    supportsModelFlag: true,
    tmuxArgs(model) {
      return ["codex", ...(model ? ["-m", model] : []), "--ask-for-approval", "never"];
    },
    headlessArgs(model) {
      return [
        "exec",
        ...(model ? ["-m", model] : []),
        "--skip-git-repo-check",
        "--color",
        "never",
        "-"
      ];
    }
  },
  claude: {
    id: "claude",
    displayName: "Claude",
    envName: "CLAUDE",
    defaultSessionName: "claude-mcp",
    defaultCommand: "claude",
    defaultModel: "sonnet",
    supportsModelFlag: true,
    tmuxArgs(model) {
      return [
        "claude",
        ...(model ? ["--model", model] : []),
        "--permission-mode",
        "dontAsk"
      ];
    },
    headlessArgs(model) {
      return [
        "-p",
        "--output-format",
        "text",
        "--permission-mode",
        "dontAsk",
        "--no-session-persistence",
        ...(model ? ["--model", model] : [])
      ];
    }
  },
  grok: {
    id: "grok",
    displayName: "Grok",
    envName: "GROK",
    defaultSessionName: "grok-mcp",
    defaultCommand: "grok --no-alt-screen",
    defaultModel: "",
    supportsModelFlag: true,
    tmuxArgs(model) {
      return ["grok", "--no-alt-screen", ...(model ? ["-m", model] : [])];
    },
    headlessArgs(model, promptPath) {
      return [
        ...(model ? ["-m", model] : []),
        "--prompt-file",
        promptPath,
        "--output-format",
        "plain",
        "--permission-mode",
        "dontAsk",
        "--max-turns",
        "80",
        "--no-memory"
      ];
    }
  },
  antigravity: {
    id: "antigravity",
    displayName: "Antigravity",
    envName: "ANTIGRAVITY",
    defaultSessionName: "antigravity-mcp",
    defaultCommand: "agy",
    defaultModel: "",
    supportsModelFlag: false,
    tmuxArgs() {
      return ["agy"];
    },
    headlessArgs(_model, _promptPath, timeoutMs) {
      return ["--print", "--print-timeout", durationForAgy(timeoutMs)];
    }
  }
};

export const PROVIDER_ALIASES = {
  agy: "antigravity",
  google: "antigravity",
  gemini: "antigravity",
  gpt: "codex",
  openai: "codex",
  xai: "grok"
};

const DEFAULT_CAPTURE_LINES = 4000;
const DEFAULT_TIMEOUT_MS = 120000;
const DEFAULT_HEADLESS_TIMEOUT_MS = 600000;
const DEFAULT_POLL_MS = 300;
const DEFAULT_READY_TIMEOUT_MS = 15000;
const DEFAULT_COLUMNS = 160;
const DEFAULT_ROWS = 50;

export class LlmRouterError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = "LlmRouterError";
    this.details = details;
  }
}

export function listProviders() {
  return Object.values(PROVIDERS).map((provider) => ({
    id: provider.id,
    displayName: provider.displayName,
    defaultSessionName: provider.defaultSessionName,
    defaultModel: provider.defaultModel || "CLI default/latest",
    supportsModelFlag: provider.supportsModelFlag,
    defaultTmuxCommand: buildTmuxCommand(provider.id),
    headlessAvailable: true
  }));
}

export function normalizeProvider(provider) {
  const raw = String(provider || "").trim().toLowerCase();
  const id = PROVIDER_ALIASES[raw] || raw;
  if (!PROVIDERS[id]) {
    throw new LlmRouterError("provider must be one of: codex, claude, grok, antigravity", {
      provider
    });
  }
  return id;
}

export function providerConfig(provider) {
  return PROVIDERS[normalizeProvider(provider)];
}

export function defaultStateDir() {
  return (
    process.env.LLM_ROUTER_MCP_STATE_DIR ||
    path.join(os.homedir(), ".local", "state", "llm-router-mcp")
  );
}

export function defaultWorkDir(provider, stateDir = defaultStateDir()) {
  const config = providerConfig(provider);
  return path.join(path.resolve(stateDir), "workdirs", config.id);
}

export function makeNonce() {
  return crypto.randomUUID();
}

export function markerSet(provider, nonce) {
  const config = providerConfig(provider);
  validateNonce(nonce);
  return {
    nonce,
    startMarker: `${config.envName}_TMUX_STARTED:${nonce}`,
    doneMarker: `${config.envName}_TMUX_DONE:${nonce}`,
    startPrefix: `${config.envName}_TMUX_STARTED:`,
    donePrefix: `${config.envName}_TMUX_DONE:`
  };
}

export function validateNonce(nonce) {
  if (typeof nonce !== "string" || !/^[A-Za-z0-9_.:-]{6,96}$/.test(nonce)) {
    throw new LlmRouterError(
      "nonce must be 6-96 chars and contain only letters, numbers, dot, underscore, colon, or dash",
      { nonce }
    );
  }
}

export function validateSessionName(sessionName) {
  if (
    typeof sessionName !== "string" ||
    !/^[A-Za-z0-9_.:-]{1,120}$/.test(sessionName)
  ) {
    throw new LlmRouterError(
      "sessionName must be 1-120 chars and contain only letters, numbers, dot, underscore, colon, or dash",
      { sessionName }
    );
  }
}

export function normalizeTimeout(timeoutMs, fallback = DEFAULT_TIMEOUT_MS) {
  if (timeoutMs === undefined || timeoutMs === null) {
    return fallback;
  }
  const parsed = Number(timeoutMs);
  if (!Number.isFinite(parsed) || parsed < 1) {
    throw new LlmRouterError("timeoutMs must be a positive number", { timeoutMs });
  }
  return Math.trunc(parsed);
}

export function normalizeDimension(value, fallback) {
  if (value === undefined || value === null || value === "") {
    return fallback;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 20) {
    throw new LlmRouterError("terminal dimensions must be numbers >= 20", { value });
  }
  return Math.trunc(parsed);
}

export function resolveModel(provider, requestedModel) {
  const config = providerConfig(provider);
  const envModel = process.env[`LLM_ROUTER_MCP_${config.envName}_MODEL`];
  const model = requestedModel ?? envModel ?? config.defaultModel;
  return typeof model === "string" && model.trim() ? model.trim() : "";
}

export function buildTmuxCommand(provider, model) {
  const config = providerConfig(provider);
  const resolvedModel = resolveModel(config.id, model);
  const envCommand = process.env[`LLM_ROUTER_MCP_${config.envName}_CMD`];
  if (envCommand) {
    return envCommand;
  }
  return config.tmuxArgs(config.supportsModelFlag ? resolvedModel : "").map(shellQuote).join(" ");
}

export async function runCommand(command, args = [], options = {}) {
  const timeoutMs = normalizeTimeout(options.timeoutMs, 15000);
  const startedAt = Date.now();

  return await new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      env: mergedEnv(options.env),
      stdio: ["pipe", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";
    let settled = false;

    const timer = setTimeout(() => {
      if (settled) {
        return;
      }
      settled = true;
      child.kill("SIGTERM");
      reject(
        new LlmRouterError(`command timed out after ${timeoutMs}ms`, {
          command,
          args,
          stdout,
          stderr
        })
      );
    }, timeoutMs);

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", (error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      reject(
        new LlmRouterError(`failed to run command: ${command}`, {
          command,
          args,
          cause: error.message
        })
      );
    });
    child.on("close", (code, signal) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      const result = {
        command,
        args,
        code,
        signal,
        stdout,
        stderr,
        elapsedMs: Date.now() - startedAt
      };
      if (code !== 0 && !options.allowFailure) {
        reject(
          new LlmRouterError(`command failed: ${command} ${args.join(" ")}`, {
            ...result
          })
        );
        return;
      }
      resolve(result);
    });

    if (options.input !== undefined) {
      child.stdin.end(options.input);
    } else {
      child.stdin.end();
    }
  });
}

export async function tmuxVersion() {
  const result = await runCommand("tmux", ["-V"]);
  return result.stdout.trim();
}

export async function hasSession(options = {}) {
  const sessionName = resolveSessionName(options.provider, options.sessionName);
  validateSessionName(sessionName);
  const result = await runCommand("tmux", ["has-session", "-t", sessionName], {
    allowFailure: true,
    timeoutMs: 5000
  });
  return result.code === 0;
}

export async function killSession(options = {}) {
  const sessionName = resolveSessionName(options.provider, options.sessionName);
  validateSessionName(sessionName);
  const result = await runCommand("tmux", ["kill-session", "-t", sessionName], {
    allowFailure: true,
    timeoutMs: 5000
  });
  return result.code === 0;
}

export async function ensureSession(options = {}) {
  const provider = normalizeProvider(options.provider);
  const config = providerConfig(provider);
  const sessionName = resolveSessionName(provider, options.sessionName);
  const stateDir = path.resolve(options.stateDir || defaultStateDir());
  const cwd =
    options.cwd ||
    process.env[`LLM_ROUTER_MCP_${config.envName}_CWD`] ||
    (await ensureDefaultWorkDir(provider, stateDir));
  const command = options.command || buildTmuxCommand(provider, options.model);
  const timeoutMs = normalizeTimeout(options.timeoutMs, DEFAULT_READY_TIMEOUT_MS);
  const columns = normalizeDimension(options.columns, DEFAULT_COLUMNS);
  const rows = normalizeDimension(options.rows, DEFAULT_ROWS);

  validateSessionName(sessionName);
  await tmuxVersion();

  if (await hasSession({ provider, sessionName })) {
    return {
      provider,
      sessionName,
      command,
      cwd,
      created: false,
      running: true,
      ready: true,
      paneTail: await capturePane({ provider, sessionName, lines: 80 })
    };
  }

  const args = [
    "new-session",
    "-d",
    "-x",
    String(columns),
    "-y",
    String(rows),
    "-s",
    sessionName,
    "-c",
    cwd,
    command
  ];
  await runCommand("tmux", args, { timeoutMs });

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await hasSession({ provider, sessionName })) {
      await sleep(150);
      return {
        provider,
        sessionName,
        command,
        cwd,
        created: true,
        running: true,
        ready: true,
        paneTail: await capturePane({ provider, sessionName, lines: 80 }),
        columns,
        rows
      };
    }
    await sleep(100);
  }

  throw new LlmRouterError("tmux session did not become available before timeout", {
    provider,
    sessionName,
    timeoutMs
  });
}

export async function capturePane(options = {}) {
  const provider = normalizeProvider(options.provider);
  const sessionName = resolveSessionName(provider, options.sessionName);
  const lines = Math.max(1, Math.trunc(Number(options.lines || DEFAULT_CAPTURE_LINES)));

  validateSessionName(sessionName);
  const result = await runCommand(
    "tmux",
    ["capture-pane", "-p", "-J", "-t", sessionName, "-S", `-${lines}`],
    { timeoutMs: 5000 }
  );
  return stripAnsi(result.stdout);
}

export async function writeInputFile(options = {}) {
  const provider = options.provider ? normalizeProvider(options.provider) : "shared";
  const markdown = options.markdown;
  if (typeof markdown !== "string" || markdown.length === 0) {
    throw new LlmRouterError("markdown must be a non-empty string");
  }

  const stateDir = path.resolve(options.stateDir || defaultStateDir());
  const inputDir = path.join(stateDir, "inputs", provider);
  await fs.mkdir(inputDir, { recursive: true });

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const requestedName = options.filename
    ? path.basename(options.filename)
    : `${timestamp}-${crypto.randomBytes(4).toString("hex")}.md`;
  const safeName = requestedName.replace(/[^A-Za-z0-9_.-]/g, "_");
  const filename = /\.(md|markdown)$/i.test(safeName) ? safeName : `${safeName}.md`;
  const inputPath = path.join(inputDir, filename);

  await fs.writeFile(inputPath, markdown, "utf8");
  return { inputPath, bytes: Buffer.byteLength(markdown, "utf8") };
}

export async function sendInput(options = {}) {
  const provider = normalizeProvider(options.provider);
  const config = providerConfig(provider);
  const sessionName = resolveSessionName(provider, options.sessionName);
  const stateDir = path.resolve(options.stateDir || defaultStateDir());
  const timeoutMs = normalizeTimeout(options.timeoutMs, DEFAULT_TIMEOUT_MS);
  const nonce = options.nonce || makeNonce();
  const { startMarker, doneMarker } = markerSet(provider, nonce);

  validateSessionName(sessionName);
  const inputPath = path.resolve(requireInputPath(options.inputPath));
  validateMarkdownPath(inputPath);
  const markdown = await fs.readFile(inputPath, "utf8");
  if (markdown.includes(startMarker) || markdown.includes(doneMarker)) {
    throw new LlmRouterError(
      "input file already contains the generated nonce markers; pass a different nonce",
      { inputPath, nonce }
    );
  }

  await ensureSession({
    provider,
    sessionName,
    command: options.command,
    cwd: options.cwd,
    timeoutMs,
    stateDir,
    columns: options.columns,
    rows: options.rows,
    model: options.model
  });

  const prompt = buildPrompt({
    provider,
    mode: "tmux",
    inputPath,
    markdown,
    nonce,
    model: options.model
  });

  if (prompt.includes(startMarker) || prompt.includes(doneMarker)) {
    throw new LlmRouterError(
      "internal prompt unexpectedly contains full markers before the model can emit them",
      { provider, nonce }
    );
  }

  const requestDir = path.join(stateDir, "requests", config.id);
  await fs.mkdir(requestDir, { recursive: true });
  const promptPath = path.join(requestDir, `${safeFilePart(nonce)}.prompt.md`);
  await fs.writeFile(promptPath, prompt, "utf8");

  await pasteFileToTmux({ provider, sessionName, promptPath, nonce });

  return {
    provider,
    sessionName,
    nonce,
    inputPath,
    promptPath,
    startMarker,
    doneMarker,
    sent: true,
    sentAt: new Date().toISOString()
  };
}

export async function waitForResponse(options = {}) {
  const provider = normalizeProvider(options.provider);
  const sessionName = resolveSessionName(provider, options.sessionName);
  const timeoutMs = normalizeTimeout(options.timeoutMs, DEFAULT_TIMEOUT_MS);
  const pollMs = normalizeTimeout(options.pollMs, DEFAULT_POLL_MS);
  const { nonce, startMarker, doneMarker } = markerSet(
    provider,
    requireNonce(options.nonce)
  );
  const stateDir = path.resolve(options.stateDir || defaultStateDir());
  const deadline = Date.now() + timeoutMs;
  let started = false;
  let startSeenAt = null;
  let lastPane = "";

  validateSessionName(sessionName);

  while (Date.now() <= deadline) {
    try {
      lastPane = await capturePane({
        provider,
        sessionName,
        lines: options.captureLines || DEFAULT_CAPTURE_LINES
      });
    } catch (error) {
      if (!(await hasSession({ provider, sessionName }))) {
        const fallbackPath = await writeFallbackFile({
          provider,
          stateDir,
          nonce,
          title: `${providerConfig(provider).displayName} tmux session ended before done marker`,
          paneTail: lastPane,
          error
        });
        return {
          provider,
          sessionName,
          nonce,
          started,
          completed: false,
          timedOut: false,
          sessionEnded: true,
          startMarker,
          doneMarker,
          startSeenAt,
          completedAt: null,
          answer: null,
          responsePath: null,
          fallbackPath,
          paneTail: tailLines(lastPane, 160),
          error: error instanceof Error ? error.message : String(error)
        };
      }
      throw error;
    }

    const startIndex = lastPane.indexOf(startMarker);
    const doneIndex = lastPane.indexOf(doneMarker);

    if (startIndex !== -1 && !started) {
      started = true;
      startSeenAt = new Date().toISOString();
    }

    if (doneIndex !== -1 && (startIndex === -1 || doneIndex > startIndex)) {
      const answer = extractAnswer(lastPane, startMarker, doneMarker);
      const response = await writeResponseFile({ provider, stateDir, nonce, answer });
      return {
        provider,
        sessionName,
        nonce,
        started: startIndex !== -1,
        completed: true,
        timedOut: false,
        sessionEnded: false,
        startMarker,
        doneMarker,
        startSeenAt,
        completedAt: new Date().toISOString(),
        answer,
        responsePath: response.responsePath,
        responseBytes: response.bytes,
        fallbackPath: null,
        paneTail: tailLines(lastPane, 120)
      };
    }

    await sleep(Math.min(pollMs, Math.max(1, deadline - Date.now())));
  }

  const fallbackPath = await writeFallbackFile({
    provider,
    stateDir,
    nonce,
    title: `${providerConfig(provider).displayName} tmux wait timed out before done marker`,
    paneTail: lastPane
  });

  return {
    provider,
    sessionName,
    nonce,
    started,
    completed: false,
    timedOut: true,
    sessionEnded: false,
    startMarker,
    doneMarker,
    startSeenAt,
    completedAt: null,
    answer: null,
    responsePath: null,
    fallbackPath,
    paneTail: tailLines(lastPane, 160)
  };
}

export async function waitForStart(options = {}) {
  const provider = normalizeProvider(options.provider);
  const sessionName = resolveSessionName(provider, options.sessionName);
  const timeoutMs = normalizeTimeout(options.timeoutMs, 30000);
  const pollMs = normalizeTimeout(options.pollMs, DEFAULT_POLL_MS);
  const { nonce, startMarker, doneMarker } = markerSet(
    provider,
    requireNonce(options.nonce)
  );
  const deadline = Date.now() + timeoutMs;
  let lastPane = "";

  validateSessionName(sessionName);

  while (Date.now() <= deadline) {
    lastPane = await capturePane({
      provider,
      sessionName,
      lines: options.captureLines || DEFAULT_CAPTURE_LINES
    });
    const started = lastPane.includes(startMarker);
    const completed = lastPane.includes(doneMarker);

    if (started || completed) {
      return {
        provider,
        sessionName,
        nonce,
        started,
        completed,
        timedOut: false,
        startMarker,
        doneMarker,
        startSeenAt: started ? new Date().toISOString() : null,
        paneTail: tailLines(lastPane, 120)
      };
    }

    await sleep(Math.min(pollMs, Math.max(1, deadline - Date.now())));
  }

  return {
    provider,
    sessionName,
    nonce,
    started: false,
    completed: false,
    timedOut: true,
    startMarker,
    doneMarker,
    startSeenAt: null,
    paneTail: tailLines(lastPane, 160)
  };
}

export async function tmuxAsk(options = {}) {
  const sent = await sendInput(options);
  const waited = await waitForResponse({
    provider: sent.provider,
    sessionName: sent.sessionName,
    nonce: sent.nonce,
    timeoutMs: options.timeoutMs,
    pollMs: options.pollMs,
    captureLines: options.captureLines,
    stateDir: options.stateDir
  });
  return { ...sent, ...waited, mode: "tmux" };
}

export async function headlessAsk(options = {}) {
  const provider = normalizeProvider(options.provider);
  const config = providerConfig(provider);
  const stateDir = path.resolve(options.stateDir || defaultStateDir());
  const timeoutMs = normalizeTimeout(options.timeoutMs, DEFAULT_HEADLESS_TIMEOUT_MS);
  const nonce = options.nonce || makeNonce();
  const input =
    options.inputPath !== undefined
      ? { inputPath: path.resolve(requireInputPath(options.inputPath)) }
      : await writeInputFile({
          provider,
          markdown: options.markdown,
          filename: options.filename,
          stateDir
        });
  const inputPath = input.inputPath;
  validateMarkdownPath(inputPath);

  const markdown = await fs.readFile(inputPath, "utf8");
  const prompt = buildPrompt({
    provider,
    mode: "headless",
    inputPath,
    markdown,
    nonce,
    model: options.model
  });
  const { startMarker, doneMarker } = markerSet(provider, nonce);
  if (prompt.includes(startMarker) || prompt.includes(doneMarker)) {
    throw new LlmRouterError(
      "internal prompt unexpectedly contains full markers before the model can emit them",
      { provider, nonce }
    );
  }

  const requestDir = path.join(stateDir, "requests", config.id);
  await fs.mkdir(requestDir, { recursive: true });
  const promptPath = path.join(requestDir, `${safeFilePart(nonce)}.headless.prompt.md`);
  await fs.writeFile(promptPath, prompt, "utf8");

  const cwd =
    options.cwd ||
    process.env[`LLM_ROUTER_MCP_${config.envName}_CWD`] ||
    (await ensureDefaultWorkDir(provider, stateDir));
  const model = resolveModel(provider, options.model);
  const run = await runHeadlessProvider({
    provider,
    model,
    prompt,
    promptPath,
    cwd,
    timeoutMs
  });

  const raw = await writeRawResponseFile({
    provider,
    stateDir,
    nonce,
    stdout: run.stdout,
    stderr: run.stderr,
    code: run.code
  });
  const answer = run.code === 0 ? extractHeadlessAnswer(run.stdout, startMarker, doneMarker) : null;
  const response = await writeResponseFile({ provider, stateDir, nonce, answer });

  return {
    provider,
    mode: "headless",
    nonce,
    inputPath,
    promptPath,
    startMarker,
    doneMarker,
    cwd,
    model: model || "CLI default/latest",
    command: run.command,
    args: run.args,
    exitCode: run.code,
    success: run.code === 0,
    elapsedMs: run.elapsedMs,
    answer,
    responsePath: response.responsePath,
    responseBytes: response.bytes,
    rawResponsePath: raw.rawResponsePath,
    rawResponseBytes: raw.bytes,
    stderr: run.stderr.trim() || null
  };
}

export async function status(options = {}) {
  const provider = normalizeProvider(options.provider);
  const sessionName = resolveSessionName(provider, options.sessionName);
  const running = await hasSession({ provider, sessionName });
  let markerStatus = null;
  let paneTail = "";

  if (running) {
    paneTail = await capturePane({
      provider,
      sessionName,
      lines: options.lines || 160
    });
    if (options.nonce) {
      const { startMarker, doneMarker } = markerSet(provider, options.nonce);
      markerStatus = {
        nonce: options.nonce,
        started: paneTail.includes(startMarker),
        completed: paneTail.includes(doneMarker),
        startMarker,
        doneMarker
      };
    }
  }

  return {
    provider,
    sessionName,
    running,
    markerStatus,
    paneTail
  };
}

function buildPrompt({ provider, mode, inputPath, markdown, nonce, model }) {
  const config = providerConfig(provider);
  const { startPrefix, donePrefix } = markerSet(provider, nonce);
  const requestedModel = resolveModel(provider, model);
  const modelInstruction = requestedModel
    ? config.supportsModelFlag
      ? `The MCP caller requested model: ${requestedModel}. The launcher should already have selected it when the CLI supports model flags.`
      : `The MCP caller requested model: ${requestedModel}. This CLI does not expose a known model flag here; if the UI/agent asks or supports in-session selection, use that model.`
    : "Use the CLI default/latest model for this provider.";

  return `You are being asked through llm-router-mcp from ${mode === "tmux" ? "a persistent tmux session" : "a headless one-shot run"} for ${config.displayName}.

The request and the final answer are Markdown artifacts. Read the Markdown input exactly and answer in Markdown.

Automation markers are required so the MCP client can detect progress and completion.

Before any substantive answer, print a start marker on its own line.
- literal prefix: ${startPrefix}
- nonce: ${nonce}
- format: prefix immediately followed by nonce, with no spaces

After the final answer is complete, print a done marker on its own line.
- literal prefix: ${donePrefix}
- nonce: ${nonce}
- format: prefix immediately followed by nonce, with no spaces

Do not put either marker in a code block. Do not print the done marker until the answer is finished.
For ordinary questions, answer directly. Do not run shell commands, edit files, or send notifications unless the Markdown input explicitly asks you to do that.

${modelInstruction}

Markdown input file path:
${inputPath}

Markdown input begins below.

--- BEGIN MCP MARKDOWN INPUT ---
${markdown}
--- END MCP MARKDOWN INPUT ---
`;
}

async function runHeadlessProvider({ provider, model, prompt, promptPath, cwd, timeoutMs }) {
  const config = providerConfig(provider);
  let command = config.defaultCommand.split(/\s+/)[0];
  let args = [];
  let input = prompt;

  if (provider === "codex") {
    command = "codex";
    args = config.headlessArgs(model);
  } else if (provider === "claude") {
    command = "claude";
    args = config.headlessArgs(model);
  } else if (provider === "grok") {
    command = "grok";
    args = config.headlessArgs(model, promptPath);
    input = undefined;
  } else if (provider === "antigravity") {
    command = "agy";
    args = config.headlessArgs(model, promptPath, timeoutMs);
  }

  return await runCommand(command, args, {
    cwd,
    input,
    timeoutMs,
    allowFailure: true
  });
}

async function pasteFileToTmux({ provider, sessionName, promptPath, nonce }) {
  const bufferName = `${provider}-tmux-${nonce}`.replace(/[^A-Za-z0-9_.:-]/g, "-");
  await runCommand("tmux", ["load-buffer", "-b", bufferName, promptPath], {
    timeoutMs: 10000
  });
  try {
    await runCommand("tmux", ["paste-buffer", "-p", "-b", bufferName, "-t", sessionName], {
      timeoutMs: 10000
    });
    await runCommand("tmux", ["send-keys", "-t", sessionName, "Enter"], {
      timeoutMs: 5000
    });
  } finally {
    await runCommand("tmux", ["delete-buffer", "-b", bufferName], {
      allowFailure: true,
      timeoutMs: 5000
    });
  }
}

function extractAnswer(paneText, startMarker, doneMarker) {
  const lines = paneText.replace(/\r/g, "").split("\n");
  const startLine = lines.findIndex((line) => line.includes(startMarker));
  if (startLine === -1) {
    return null;
  }
  const doneLine = lines.findIndex(
    (line, index) => index > startLine && line.includes(doneMarker)
  );
  if (doneLine === -1 || doneLine < startLine) {
    return null;
  }

  const answerLines = lines.slice(startLine + 1, doneLine).map(cleanPaneLine);
  return stripCommonIndent(answerLines).join("\n").trimEnd();
}

function extractHeadlessAnswer(stdout, startMarker, doneMarker) {
  const answer = extractAnswer(stdout, startMarker, doneMarker);
  if (answer !== null && answer !== undefined) {
    return answer;
  }
  return stdout.trimEnd();
}

async function ensureDefaultWorkDir(provider, stateDir) {
  const config = providerConfig(provider);
  const cwd = defaultWorkDir(provider, stateDir);
  await fs.mkdir(cwd, { recursive: true });

  const agentsPath = path.join(cwd, "AGENTS.md");
  const agentsText = `# AGENTS.md

This is a private scratch workspace for llm-router-mcp ${config.displayName} chat automation.

- For ordinary questions, answer directly in chat.
- Do not run shell commands, edit files, or send completion notifications unless the user explicitly asks inside the prompt.
- Preserve the ${config.envName}_TMUX_STARTED/${config.envName}_TMUX_DONE nonce marker protocol requested by llm-router-mcp.
`;
  await fs.writeFile(agentsPath, agentsText, "utf8");

  try {
    await fs.access(path.join(cwd, ".git"));
  } catch {
    await runCommand("git", ["init", "-q"], {
      cwd,
      allowFailure: true,
      timeoutMs: 10000
    });
  }

  return cwd;
}

async function writeResponseFile({ provider, stateDir, nonce, answer }) {
  const config = providerConfig(provider);
  const responseDir = path.join(stateDir, "responses", config.id);
  await fs.mkdir(responseDir, { recursive: true });
  const responsePath = path.join(responseDir, `${safeFilePart(nonce)}.response.md`);
  const content = answer === null || answer === undefined ? "" : `${answer}\n`;
  await fs.writeFile(responsePath, content, "utf8");
  return {
    responsePath,
    bytes: Buffer.byteLength(content, "utf8")
  };
}

async function writeRawResponseFile({ provider, stateDir, nonce, stdout, stderr, code }) {
  const config = providerConfig(provider);
  const responseDir = path.join(stateDir, "responses", config.id);
  await fs.mkdir(responseDir, { recursive: true });
  const rawResponsePath = path.join(responseDir, `${safeFilePart(nonce)}.raw.md`);
  const content = `# Raw ${config.displayName} Headless Response

- nonce: ${nonce}
- exitCode: ${code}
- writtenAt: ${new Date().toISOString()}

## stdout

\`\`\`text
${stdout || ""}
\`\`\`

## stderr

\`\`\`text
${stderr || ""}
\`\`\`
`;
  await fs.writeFile(rawResponsePath, content, "utf8");
  return {
    rawResponsePath,
    bytes: Buffer.byteLength(content, "utf8")
  };
}

async function writeFallbackFile({ provider, stateDir, nonce, title, paneTail, error }) {
  const config = providerConfig(provider);
  const responseDir = path.join(stateDir, "responses", config.id);
  await fs.mkdir(responseDir, { recursive: true });
  const fallbackPath = path.join(responseDir, `${safeFilePart(nonce)}.fallback.md`);
  const content = `# ${title}

- nonce: ${nonce}
- writtenAt: ${new Date().toISOString()}
${error ? `- error: ${error instanceof Error ? error.message : String(error)}\n` : ""}
## Captured pane tail

\`\`\`text
${tailLines(paneTail || "", 240)}
\`\`\`
`;
  await fs.writeFile(fallbackPath, content, "utf8");
  return fallbackPath;
}

function resolveSessionName(provider, sessionName) {
  const config = providerConfig(provider);
  return (
    sessionName ||
    process.env[`LLM_ROUTER_MCP_${config.envName}_SESSION`] ||
    config.defaultSessionName
  );
}

function safeFilePart(value) {
  return value.replace(/[^A-Za-z0-9_.:-]/g, "-");
}

function cleanPaneLine(line) {
  return line
    .replace(/[ \t]*[|│┃█▌▐]+[ \t]*$/g, "")
    .replace(/[ \t]{2,}\d{1,2}:\d{2}\s*(?:AM|PM)[ \t]*$/i, "")
    .replace(/[ \t]+$/g, "");
}

function stripCommonIndent(lines) {
  const nonEmpty = lines.filter((line) => line.trim().length > 0);
  if (nonEmpty.length === 0) {
    return lines;
  }
  const common = Math.min(
    ...nonEmpty.map((line) => {
      const match = /^[ \t]*/.exec(line);
      return match ? match[0].length : 0;
    })
  );
  if (common <= 0) {
    return lines;
  }
  return lines.map((line) => line.slice(Math.min(common, line.length)));
}

function stripAnsi(value) {
  return value.replace(
    // eslint-disable-next-line no-control-regex
    /[\u001b\u009b][[\]()#;?]*(?:(?:(?:[a-zA-Z\d]*(?:;[a-zA-Z\d]*)*)?\u0007)|(?:(?:\d{1,4}(?:;\d{0,4})*)?[\dA-PR-TZcf-nq-uy=><~]))/g,
    ""
  );
}

function tailLines(value, count) {
  const lines = value.split(/\r?\n/);
  return lines.slice(Math.max(0, lines.length - count)).join("\n");
}

function requireInputPath(inputPath) {
  if (typeof inputPath !== "string" || inputPath.length === 0) {
    throw new LlmRouterError("inputPath is required and must point to a Markdown file");
  }
  return inputPath;
}

function requireNonce(nonce) {
  if (typeof nonce !== "string" || nonce.length === 0) {
    throw new LlmRouterError("nonce is required");
  }
  return nonce;
}

function validateMarkdownPath(inputPath) {
  if (!/\.(md|markdown)$/i.test(inputPath)) {
    throw new LlmRouterError("inputPath must end with .md or .markdown", { inputPath });
  }
}

function shellQuote(value) {
  if (/^[A-Za-z0-9_./:=+-]+$/.test(value)) {
    return value;
  }
  return `'${String(value).replace(/'/g, "'\\''")}'`;
}

function mergedEnv(extra = {}) {
  const home = os.homedir();
  const pathPrefix = [path.join(home, ".local", "bin"), path.join(home, ".npm-global", "bin")].join(
    path.delimiter
  );
  const customPrefix = process.env.LLM_ROUTER_MCP_PATH_PREFIX || "";
  return {
    ...process.env,
    PATH: [customPrefix, pathPrefix, process.env.PATH || ""]
      .filter(Boolean)
      .join(path.delimiter),
    ...extra
  };
}

function durationForAgy(timeoutMs) {
  const seconds = Math.max(1, Math.ceil(normalizeTimeout(timeoutMs, 300000) / 1000));
  return `${seconds}s`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
