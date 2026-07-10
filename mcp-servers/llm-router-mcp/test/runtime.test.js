import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  createRequestDirectory,
  ensureStateRoot,
  ensureStateSubdir,
  readJsonFile,
  readMarkdownInput,
  resolveStateRoot,
  validateMarkdownInput,
  writeFileAtomic,
  writeFileExclusive,
  writeJsonAtomic
} from "../src/runtime.js";

const mode = (stats) => stats.mode & 0o777;

async function makeTemp(t, prefix = "llm-router-runtime-") {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), prefix));
  t.after(async () => {
    await fs.rm(directory, { recursive: true, force: true });
  });
  return directory;
}

test("state root resolution honors explicit, configured, and XDG precedence", async (t) => {
  const temp = await makeTemp(t);
  const oldStateDir = process.env.LLM_ROUTER_MCP_STATE_DIR;
  const oldXdgStateHome = process.env.XDG_STATE_HOME;
  t.after(() => {
    restoreEnv("LLM_ROUTER_MCP_STATE_DIR", oldStateDir);
    restoreEnv("XDG_STATE_HOME", oldXdgStateHome);
  });

  delete process.env.LLM_ROUTER_MCP_STATE_DIR;
  process.env.XDG_STATE_HOME = path.join(temp, "xdg");
  assert.equal(resolveStateRoot(), path.join(temp, "xdg", "llm-router-mcp"));

  process.env.LLM_ROUTER_MCP_STATE_DIR = path.join(temp, "configured");
  assert.equal(resolveStateRoot(), path.join(temp, "configured"));
  assert.equal(resolveStateRoot(path.join(temp, "explicit")), path.join(temp, "explicit"));

  delete process.env.LLM_ROUTER_MCP_STATE_DIR;
  process.env.XDG_STATE_HOME = "relative-xdg-is-invalid";
  assert.equal(resolveStateRoot(), path.join(os.homedir(), ".local", "state", "llm-router-mcp"));
});

test("state root and every managed subdirectory are hardened to 0700", async (t) => {
  const temp = await makeTemp(t);
  const requestedRoot = path.join(temp, "state");
  const stateRoot = await ensureStateRoot(requestedRoot);
  assert.equal(stateRoot, await fs.realpath(requestedRoot));
  assert.equal(mode(await fs.stat(stateRoot)), 0o700);

  await fs.chmod(stateRoot, 0o777);
  assert.equal(await ensureStateRoot(stateRoot), stateRoot);
  assert.equal(mode(await fs.stat(stateRoot)), 0o700);

  const providerDir = await ensureStateSubdir(stateRoot, "requests", "codex");
  assert.equal(mode(await fs.stat(path.join(stateRoot, "requests"))), 0o700);
  assert.equal(mode(await fs.stat(providerDir)), 0o700);
});

test("state roots reject control characters that would break one-line transport", async (t) => {
  const temp = await makeTemp(t);
  await assert.rejects(
    () => ensureStateRoot(path.join(temp, "state\nsecond-line")),
    hasCode("ERR_INVALID_PATH")
  );
});

test("state helpers reject root and child symlinks", async (t) => {
  const temp = await makeTemp(t);
  const target = path.join(temp, "target");
  const linkedRoot = path.join(temp, "linked-state");
  await fs.mkdir(target);
  await fs.symlink(target, linkedRoot);
  await assert.rejects(() => ensureStateRoot(linkedRoot), hasCode("ERR_SYMLINK"));

  const stateRoot = await ensureStateRoot(path.join(temp, "state"));
  await fs.symlink(target, path.join(stateRoot, "requests"));
  await assert.rejects(
    () => ensureStateSubdir(stateRoot, "requests", "codex"),
    hasCode("ERR_SYMLINK")
  );
});

test("request directories are private, exclusive, and use safe components", async (t) => {
  const temp = await makeTemp(t);
  const stateDir = path.join(temp, "state");
  const created = await createRequestDirectory({
    stateDir,
    provider: "claude",
    requestId: "req-123"
  });

  assert.equal(mode(await fs.stat(created.requestDir)), 0o700);
  assert.equal(path.basename(created.requestDir), "req-123");
  await assert.rejects(
    () => createRequestDirectory({ stateDir, provider: "claude", requestId: "req-123" }),
    hasCode("ERR_REQUEST_EXISTS")
  );
  await assert.rejects(
    () => createRequestDirectory({ stateDir, provider: "claude", requestId: "../escape" }),
    hasCode("ERR_UNSAFE_COMPONENT")
  );
});

test("exclusive and atomic writes keep files 0600 and reject symlinks", async (t) => {
  const temp = await makeTemp(t);
  const stateRoot = await ensureStateRoot(path.join(temp, "state"));
  const filesDir = await ensureStateSubdir(stateRoot, "responses");
  const exclusivePath = path.join(filesDir, "exclusive.md");

  const exclusive = await writeFileExclusive(exclusivePath, "first\n", {
    stateDir: stateRoot
  });
  assert.equal(exclusive.bytes, 6);
  assert.equal(await fs.readFile(exclusivePath, "utf8"), "first\n");
  assert.equal(mode(await fs.stat(exclusivePath)), 0o600);
  await assert.rejects(
    () => writeFileExclusive(exclusivePath, "second", { stateDir: stateRoot }),
    hasCode("ERR_FILE_EXISTS")
  );

  await fs.chmod(exclusivePath, 0o666);
  await writeFileAtomic(exclusivePath, "replacement\n", { stateDir: stateRoot });
  assert.equal(await fs.readFile(exclusivePath, "utf8"), "replacement\n");
  assert.equal(mode(await fs.stat(exclusivePath)), 0o600);

  const outsideTarget = path.join(temp, "outside.txt");
  const linkedPath = path.join(filesDir, "linked.md");
  await fs.writeFile(outsideTarget, "untouched");
  await fs.symlink(outsideTarget, linkedPath);
  await assert.rejects(
    () => writeFileAtomic(linkedPath, "overwrite", { stateDir: stateRoot }),
    hasCode("ERR_SYMLINK")
  );
  assert.equal(await fs.readFile(outsideTarget, "utf8"), "untouched");
});

test("Markdown validation rejects wrong types, symlinks, oversize files, and escapes", async (t) => {
  const temp = await makeTemp(t);
  const stateRoot = await ensureStateRoot(path.join(temp, "state"));
  const inputsDir = await ensureStateSubdir(stateRoot, "inputs", "codex");
  const inputPath = path.join(inputsDir, "request.md");
  await writeFileExclusive(inputPath, "# Safe\n", { stateDir: stateRoot });

  const valid = await validateMarkdownInput(inputPath, {
    stateDir: stateRoot,
    requireWithinState: true
  });
  assert.equal(valid.inputPath, await fs.realpath(inputPath));
  assert.equal(valid.bytes, 7);
  assert.equal(valid.insideState, true);

  const read = await readMarkdownInput(inputPath, {
    stateDir: stateRoot,
    requireWithinState: true
  });
  assert.equal(read.markdown, "# Safe\n");

  const wrongExtension = path.join(temp, "request.txt");
  await fs.writeFile(wrongExtension, "text");
  await assert.rejects(
    () => validateMarkdownInput(wrongExtension),
    hasCode("ERR_INVALID_EXTENSION")
  );

  const directoryPath = path.join(temp, "directory.md");
  await fs.mkdir(directoryPath);
  await assert.rejects(
    () => validateMarkdownInput(directoryPath),
    hasCode("ERR_NOT_REGULAR_FILE")
  );

  const external = path.join(temp, "external.md");
  const linked = path.join(temp, "linked.md");
  await fs.writeFile(external, "external");
  await fs.symlink(external, linked);
  await assert.rejects(() => validateMarkdownInput(linked), hasCode("ERR_SYMLINK"));
  await assert.rejects(
    () => validateMarkdownInput(external, { stateDir: stateRoot, requireWithinState: true }),
    hasCode("ERR_OUTSIDE_STATE")
  );

  const tooLarge = path.join(temp, "large.md");
  await fs.writeFile(tooLarge, "12345");
  await assert.rejects(
    () => readMarkdownInput(tooLarge, { maxBytes: 4 }),
    hasCode("ERR_FILE_TOO_LARGE")
  );

  const escapedDir = path.join(temp, "escaped");
  await fs.mkdir(escapedDir);
  await fs.writeFile(path.join(escapedDir, "escape.md"), "escape");
  await fs.symlink(escapedDir, path.join(stateRoot, "linked-inputs"));
  await assert.rejects(
    () =>
      validateMarkdownInput(path.join(stateRoot, "linked-inputs", "escape.md"), {
        stateDir: stateRoot
      }),
    hasCode("ERR_OUTSIDE_STATE")
  );
});

test("JSON helpers atomically round-trip bounded private regular files", async (t) => {
  const temp = await makeTemp(t);
  const stateRoot = await ensureStateRoot(path.join(temp, "state"));
  const request = await createRequestDirectory({
    stateDir: stateRoot,
    provider: "codex",
    requestId: "json-1"
  });
  const jsonPath = path.join(request.requestDir, "request.json");

  await writeJsonAtomic(jsonPath, { status: "queued", count: 1 }, { stateDir: stateRoot });
  assert.deepEqual(await readJsonFile(jsonPath, { stateDir: stateRoot }), {
    status: "queued",
    count: 1
  });
  assert.equal(mode(await fs.stat(jsonPath)), 0o600);

  await writeJsonAtomic(jsonPath, { status: "complete" }, { stateDir: stateRoot });
  assert.deepEqual(await readJsonFile(jsonPath, { stateDir: stateRoot }), {
    status: "complete"
  });

  await fs.writeFile(jsonPath, "not-json", { mode: 0o600 });
  await assert.rejects(
    () => readJsonFile(jsonPath, { stateDir: stateRoot }),
    hasCode("ERR_INVALID_JSON")
  );
  await assert.rejects(
    () => readJsonFile(jsonPath, { stateDir: stateRoot, maxBytes: 2 }),
    hasCode("ERR_FILE_TOO_LARGE")
  );
});

function hasCode(code) {
  return (error) => error?.code === code;
}

function restoreEnv(name, value) {
  if (value === undefined) {
    delete process.env[name];
  } else {
    process.env[name] = value;
  }
}
