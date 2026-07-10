import crypto from "node:crypto";
import { constants as fsConstants } from "node:fs";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const PRIVATE_DIRECTORY_MODE = 0o700;
const PRIVATE_FILE_MODE = 0o600;
const OPEN_NOFOLLOW = fsConstants.O_NOFOLLOW || 0;
const OPEN_DIRECTORY = fsConstants.O_DIRECTORY || 0;

export const DEFAULT_MAX_MARKDOWN_BYTES = 8 * 1024 * 1024;
export const DEFAULT_MAX_JSON_BYTES = 1024 * 1024;

export class RuntimeStateError extends Error {
  constructor(code, message, details = {}, options = {}) {
    super(message, options.cause ? { cause: options.cause } : undefined);
    this.name = "RuntimeStateError";
    this.code = code;
    this.details = details;
  }
}

/**
 * Resolve the configured state root without creating it.
 *
 * Precedence: explicit stateDir, LLM_ROUTER_MCP_STATE_DIR, XDG_STATE_HOME,
 * then ~/.local/state/llm-router-mcp. A relative XDG_STATE_HOME is ignored as
 * required by the XDG base-directory specification.
 */
export function resolveStateRoot(stateDir) {
  if (stateDir !== undefined && stateDir !== null) {
    return resolveNonEmptyPath(stateDir, "stateDir");
  }

  const configured = process.env.LLM_ROUTER_MCP_STATE_DIR;
  if (configured && configured.trim()) {
    return path.resolve(configured);
  }

  const xdgStateHome = process.env.XDG_STATE_HOME;
  if (xdgStateHome && xdgStateHome.trim() && path.isAbsolute(xdgStateHome)) {
    return path.join(path.normalize(xdgStateHome), "llm-router-mcp");
  }

  return path.join(os.homedir(), ".local", "state", "llm-router-mcp");
}

/** Create or harden the state root and return its canonical path. */
export async function ensureStateRoot(stateDir) {
  const requestedRoot = resolveStateRoot(stateDir);
  if (/[\x00-\x1F\x7F]/.test(requestedRoot)) {
    throw runtimeError(
      "ERR_INVALID_PATH",
      "state root must not contain control characters",
      { stateRoot: requestedRoot }
    );
  }
  if (path.parse(requestedRoot).root === requestedRoot) {
    throw runtimeError("ERR_UNSAFE_STATE_ROOT", "state root cannot be a filesystem root", {
      stateRoot: requestedRoot
    });
  }

  await mkdirPrivate(requestedRoot, { recursive: true });
  return await hardenDirectory(requestedRoot);
}

/**
 * Create private directories below a hardened state root.
 * Each segment must be one filesystem component, never a path.
 */
export async function ensureStateSubdir(stateDir, ...segments) {
  const stateRoot = await ensureStateRoot(stateDir);
  let current = stateRoot;

  for (const segment of segments.flat()) {
    const safeSegment = validatePathComponent(segment, "state directory segment");
    const next = path.join(current, safeSegment);
    assertContained(stateRoot, next, "ERR_OUTSIDE_STATE");
    await mkdirPrivate(next);
    current = await hardenDirectory(next);
    assertContained(stateRoot, current, "ERR_OUTSIDE_STATE");
  }

  return current;
}

/**
 * Exclusively create <state>/requests/<provider>/<requestId>.
 * A repeated request ID is rejected rather than reusing prior artifacts.
 */
export async function createRequestDirectory({ stateDir, provider = "shared", requestId } = {}) {
  const safeProvider = validatePathComponent(provider, "provider");
  const safeRequestId = validatePathComponent(requestId, "requestId");
  const providerDir = await ensureStateSubdir(stateDir, "requests", safeProvider);
  const stateRoot = await ensureStateRoot(stateDir);
  const requestDir = path.join(providerDir, safeRequestId);
  assertContained(stateRoot, requestDir, "ERR_OUTSIDE_STATE");

  try {
    await fs.mkdir(requestDir, { mode: PRIVATE_DIRECTORY_MODE });
  } catch (error) {
    if (error?.code === "EEXIST") {
      throw runtimeError(
        "ERR_REQUEST_EXISTS",
        `request directory already exists: ${safeRequestId}`,
        { provider: safeProvider, requestId: safeRequestId },
        error
      );
    }
    throw error;
  }

  const canonicalRequestDir = await hardenDirectory(requestDir);
  assertContained(stateRoot, canonicalRequestDir, "ERR_OUTSIDE_STATE");
  return { stateRoot, requestDir: canonicalRequestDir };
}

/** Create a new private file and fail if any destination already exists. */
export async function writeFileExclusive(filePath, data, options = {}) {
  const payload = toBuffer(data, options.encoding);
  const { targetPath, parentHandle } = await prepareWriteTarget(filePath, options);
  let handle;

  try {
    await assertDestinationSafe(targetPath, { allowExistingRegular: false });
    handle = await openExclusivePrivate(targetPath);
    await handle.writeFile(payload);
    await handle.chmod(PRIVATE_FILE_MODE);
    await handle.sync();
  } catch (error) {
    if (error?.code === "EEXIST") {
      throw runtimeError("ERR_FILE_EXISTS", `file already exists: ${targetPath}`, {
        filePath: targetPath
      }, error);
    }
    if (error?.code === "ELOOP") {
      throw runtimeError("ERR_SYMLINK", `refusing to follow symlink: ${targetPath}`, {
        filePath: targetPath
      }, error);
    }
    throw error;
  } finally {
    await handle?.close();
    await parentHandle.close();
  }

  return { filePath: targetPath, bytes: payload.byteLength };
}

/**
 * Atomically replace a missing or regular destination using a private temp
 * file in the same directory. Existing symlinks and non-regular files fail.
 */
export async function writeFileAtomic(filePath, data, options = {}) {
  const payload = toBuffer(data, options.encoding);
  const { parentPath, targetPath, parentHandle } = await prepareWriteTarget(filePath, options);
  let tempPath;
  let tempHandle;

  try {
    await assertDestinationSafe(targetPath, { allowExistingRegular: true });
    ({ tempPath, handle: tempHandle } = await createAtomicTemp(parentPath, path.basename(targetPath)));
    await tempHandle.writeFile(payload);
    await tempHandle.chmod(PRIVATE_FILE_MODE);
    await tempHandle.sync();
    await tempHandle.close();
    tempHandle = null;

    // rename(2) replaces the directory entry rather than following a symlink.
    // The pre-check provides a clear rejection for an already-present symlink;
    // the private 0700 parent prevents an untrusted same-host replacement race.
    await fs.rename(tempPath, targetPath);
    tempPath = null;
    await syncDirectory(parentHandle);
  } finally {
    await tempHandle?.close();
    if (tempPath) {
      await fs.rm(tempPath, { force: true });
    }
    await parentHandle.close();
  }

  return { filePath: targetPath, bytes: payload.byteLength };
}

/** Validate a Markdown input without following symlinks. */
export async function validateMarkdownInput(inputPath, options = {}) {
  const opened = await openValidatedRegularFile(inputPath, {
    ...options,
    extensions: [".md", ".markdown"],
    maxBytes: options.maxBytes ?? DEFAULT_MAX_MARKDOWN_BYTES
  });
  try {
    return fileMetadata(opened);
  } finally {
    await opened.handle.close();
  }
}

/** Validate and read a Markdown input through the same no-follow file handle. */
export async function readMarkdownInput(inputPath, options = {}) {
  const maxBytes = normalizeMaxBytes(
    options.maxBytes ?? DEFAULT_MAX_MARKDOWN_BYTES,
    "maxBytes"
  );
  const opened = await openValidatedRegularFile(inputPath, {
    ...options,
    extensions: [".md", ".markdown"],
    maxBytes
  });

  try {
    const content = await opened.handle.readFile();
    if (content.byteLength > maxBytes) {
      throw fileTooLarge(opened.realPath, content.byteLength, maxBytes);
    }
    return {
      ...fileMetadata(opened),
      bytes: content.byteLength,
      markdown: content.toString(options.encoding || "utf8")
    };
  } finally {
    await opened.handle.close();
  }
}

/** Serialize JSON with a trailing newline and atomically write it as 0600. */
export async function writeJsonAtomic(filePath, value, options = {}) {
  let serialized;
  try {
    serialized = JSON.stringify(value, null, options.spaces ?? 2);
  } catch (error) {
    throw runtimeError("ERR_INVALID_JSON_VALUE", "value cannot be serialized as JSON", {}, error);
  }
  if (serialized === undefined) {
    throw runtimeError("ERR_INVALID_JSON_VALUE", "value cannot be serialized as JSON");
  }
  return await writeFileAtomic(filePath, `${serialized}\n`, options);
}

/** Read and parse a bounded regular JSON file without following symlinks. */
export async function readJsonFile(filePath, options = {}) {
  const maxBytes = normalizeMaxBytes(options.maxBytes ?? DEFAULT_MAX_JSON_BYTES, "maxBytes");
  const opened = await openValidatedRegularFile(filePath, { ...options, maxBytes });

  try {
    const content = await opened.handle.readFile();
    if (content.byteLength > maxBytes) {
      throw fileTooLarge(opened.realPath, content.byteLength, maxBytes);
    }
    try {
      return JSON.parse(content.toString(options.encoding || "utf8"));
    } catch (error) {
      throw runtimeError(
        "ERR_INVALID_JSON",
        `invalid JSON file: ${opened.realPath}`,
        { filePath: opened.realPath },
        error
      );
    }
  } finally {
    await opened.handle.close();
  }
}

async function prepareWriteTarget(filePath, options) {
  const absolutePath = resolveNonEmptyPath(filePath, "filePath");
  const basename = path.basename(absolutePath);
  validateFileBasename(basename);
  const parentPath = await hardenDirectory(path.dirname(absolutePath));
  const targetPath = path.join(parentPath, basename);

  if (options.requireWithinState || options.stateDir !== undefined) {
    const stateRoot = await ensureStateRoot(options.stateDir);
    assertContained(stateRoot, targetPath, "ERR_OUTSIDE_STATE");
  }

  const parentHandle = await openDirectory(parentPath);
  return { parentPath, targetPath, parentHandle };
}

async function openValidatedRegularFile(filePath, options) {
  const absolutePath = resolveNonEmptyPath(filePath, "filePath");
  if (options.extensions) {
    const extension = path.extname(absolutePath).toLowerCase();
    if (!options.extensions.includes(extension)) {
      throw runtimeError(
        "ERR_INVALID_EXTENSION",
        `file must end with ${options.extensions.join(" or ")}`,
        { filePath: absolutePath }
      );
    }
  }

  const maxBytes = normalizeMaxBytes(options.maxBytes, "maxBytes");
  const before = await fs.lstat(absolutePath);
  if (before.isSymbolicLink()) {
    throw runtimeError("ERR_SYMLINK", `refusing to follow symlink: ${absolutePath}`, {
      filePath: absolutePath
    });
  }
  if (!before.isFile()) {
    throw runtimeError("ERR_NOT_REGULAR_FILE", `not a regular file: ${absolutePath}`, {
      filePath: absolutePath
    });
  }

  let handle;
  try {
    handle = await fs.open(absolutePath, fsConstants.O_RDONLY | OPEN_NOFOLLOW);
  } catch (error) {
    if (error?.code === "ELOOP") {
      throw runtimeError("ERR_SYMLINK", `refusing to follow symlink: ${absolutePath}`, {
        filePath: absolutePath
      }, error);
    }
    throw error;
  }

  try {
    const opened = await handle.stat();
    if (!opened.isFile() || !sameFile(before, opened)) {
      throw runtimeError("ERR_FILE_CHANGED", `file changed while opening: ${absolutePath}`, {
        filePath: absolutePath
      });
    }
    if (opened.size > maxBytes) {
      throw fileTooLarge(absolutePath, opened.size, maxBytes);
    }

    const realPath = await fs.realpath(absolutePath);
    const after = await fs.stat(realPath);
    if (!sameFile(opened, after)) {
      throw runtimeError("ERR_FILE_CHANGED", `file changed while resolving: ${absolutePath}`, {
        filePath: absolutePath
      });
    }

    const configuredRoot = resolveStateRoot(options.stateDir);
    const lexicallyInsideState = isContained(configuredRoot, absolutePath);
    let insideState = false;
    if (options.requireWithinState || lexicallyInsideState) {
      const stateRoot = await ensureStateRoot(options.stateDir);
      insideState = isContained(stateRoot, realPath);
      if (!insideState) {
        throw runtimeError("ERR_OUTSIDE_STATE", "file resolves outside the state root", {
          filePath: realPath,
          stateRoot
        });
      }
    }

    return { handle, requestedPath: absolutePath, realPath, bytes: opened.size, insideState };
  } catch (error) {
    await handle.close();
    throw error;
  }
}

async function hardenDirectory(directoryPath) {
  const absolutePath = resolveNonEmptyPath(directoryPath, "directoryPath");
  const before = await fs.lstat(absolutePath);
  if (before.isSymbolicLink()) {
    throw runtimeError("ERR_SYMLINK", `refusing to use symlink directory: ${absolutePath}`, {
      directoryPath: absolutePath
    });
  }
  if (!before.isDirectory()) {
    throw runtimeError("ERR_NOT_DIRECTORY", `not a directory: ${absolutePath}`, {
      directoryPath: absolutePath
    });
  }

  const handle = await openDirectory(absolutePath);
  try {
    const opened = await handle.stat();
    if (!opened.isDirectory() || !sameFile(before, opened)) {
      throw runtimeError("ERR_DIRECTORY_CHANGED", `directory changed while opening: ${absolutePath}`, {
        directoryPath: absolutePath
      });
    }
    await handle.chmod(PRIVATE_DIRECTORY_MODE);
  } finally {
    await handle.close();
  }

  return await fs.realpath(absolutePath);
}

async function openDirectory(directoryPath) {
  try {
    return await fs.open(
      directoryPath,
      fsConstants.O_RDONLY | OPEN_DIRECTORY | OPEN_NOFOLLOW
    );
  } catch (error) {
    if (error?.code === "ELOOP") {
      throw runtimeError("ERR_SYMLINK", `refusing to use symlink directory: ${directoryPath}`, {
        directoryPath
      }, error);
    }
    throw error;
  }
}

async function mkdirPrivate(directoryPath, options = {}) {
  try {
    await fs.mkdir(directoryPath, {
      mode: PRIVATE_DIRECTORY_MODE,
      recursive: options.recursive || false
    });
  } catch (error) {
    if (error?.code !== "EEXIST") {
      throw error;
    }
  }
}

async function assertDestinationSafe(targetPath, { allowExistingRegular }) {
  let current;
  try {
    current = await fs.lstat(targetPath);
  } catch (error) {
    if (error?.code === "ENOENT") {
      return;
    }
    throw error;
  }

  if (current.isSymbolicLink()) {
    throw runtimeError("ERR_SYMLINK", `refusing to replace symlink: ${targetPath}`, {
      filePath: targetPath
    });
  }
  if (!current.isFile()) {
    throw runtimeError("ERR_NOT_REGULAR_FILE", `destination is not a regular file: ${targetPath}`, {
      filePath: targetPath
    });
  }
  if (!allowExistingRegular) {
    throw runtimeError("ERR_FILE_EXISTS", `file already exists: ${targetPath}`, {
      filePath: targetPath
    });
  }
}

async function openExclusivePrivate(filePath) {
  return await fs.open(
    filePath,
    fsConstants.O_WRONLY | fsConstants.O_CREAT | fsConstants.O_EXCL | OPEN_NOFOLLOW,
    PRIVATE_FILE_MODE
  );
}

async function createAtomicTemp(parentPath, basename) {
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const token = crypto.randomBytes(10).toString("hex");
    const tempPath = path.join(parentPath, `.${basename}.${process.pid}.${token}.tmp`);
    try {
      const handle = await openExclusivePrivate(tempPath);
      return { tempPath, handle };
    } catch (error) {
      if (error?.code !== "EEXIST") {
        throw error;
      }
    }
  }
  throw runtimeError("ERR_TEMPFILE_COLLISION", "could not allocate an atomic temp file", {
    parentPath,
    basename
  });
}

async function syncDirectory(handle) {
  try {
    await handle.sync();
  } catch (error) {
    // Directory fsync is available on Linux, but tolerate filesystems that do
    // not implement it. The rename remains atomic even without this durability
    // enhancement.
    if (!["EINVAL", "ENOTSUP", "EISDIR"].includes(error?.code)) {
      throw error;
    }
  }
}

function fileMetadata(opened) {
  return {
    inputPath: opened.realPath,
    requestedPath: opened.requestedPath,
    bytes: opened.bytes,
    insideState: opened.insideState
  };
}

function validatePathComponent(value, label) {
  if (
    typeof value !== "string" ||
    value.length < 1 ||
    value.length > 128 ||
    !/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(value)
  ) {
    throw runtimeError(
      "ERR_UNSAFE_COMPONENT",
      `${label} must be 1-128 safe filename characters and start with a letter or number`,
      { [label]: value }
    );
  }
  return value;
}

function validateFileBasename(value) {
  if (!value || value === "." || value === ".." || value.includes("\0")) {
    throw runtimeError("ERR_UNSAFE_FILENAME", "filePath must name a file", { filename: value });
  }
}

function resolveNonEmptyPath(value, label) {
  if (typeof value !== "string" || value.trim() === "" || value.includes("\0")) {
    throw runtimeError("ERR_INVALID_PATH", `${label} must be a non-empty filesystem path`, {
      [label]: value
    });
  }
  return path.resolve(value);
}

function normalizeMaxBytes(value, label) {
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 1) {
    throw runtimeError("ERR_INVALID_LIMIT", `${label} must be a positive safe integer`, {
      [label]: value
    });
  }
  return parsed;
}

function toBuffer(data, encoding = "utf8") {
  if (typeof data === "string") {
    return Buffer.from(data, encoding);
  }
  if (Buffer.isBuffer(data)) {
    return data;
  }
  if (ArrayBuffer.isView(data)) {
    return Buffer.from(data.buffer, data.byteOffset, data.byteLength);
  }
  throw runtimeError("ERR_INVALID_FILE_DATA", "file data must be a string, Buffer, or typed array");
}

function sameFile(left, right) {
  return left.dev === right.dev && left.ino === right.ino;
}

function isContained(rootPath, candidatePath) {
  const relative = path.relative(path.resolve(rootPath), path.resolve(candidatePath));
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function assertContained(rootPath, candidatePath, code) {
  if (!isContained(rootPath, candidatePath)) {
    throw runtimeError(code, "path is outside the state root", {
      stateRoot: rootPath,
      path: candidatePath
    });
  }
}

function fileTooLarge(filePath, bytes, maxBytes) {
  return runtimeError("ERR_FILE_TOO_LARGE", `file exceeds ${maxBytes} byte limit`, {
    filePath,
    bytes,
    maxBytes
  });
}

function runtimeError(code, message, details = {}, cause) {
  return new RuntimeStateError(code, message, details, { cause });
}
