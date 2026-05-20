#!/usr/bin/env node

import fs from "node:fs";

const args = process.argv.slice(2);

if (args.includes("--version") || args.includes("version")) {
  console.log("fake-llm 0.1.0");
  process.exit(0);
}

if (isHeadless(args)) {
  const prompt = readHeadlessPrompt(args);
  answer(prompt, "headless");
} else {
  process.stdin.setEncoding("utf8");
  process.stdout.write("fake LLM ready\n");

  let buffer = "";
  let requestCount = 0;
  process.stdin.on("data", (chunk) => {
    buffer += chunk;
    if (!buffer.includes("--- END MCP MARKDOWN INPUT ---")) {
      return;
    }
    const request = buffer;
    buffer = "";
    requestCount += 1;
    answer(request, `tmux ${requestCount}`);
  });
}

function isHeadless(args) {
  return (
    args.includes("exec") ||
    args.includes("-p") ||
    args.includes("--print") ||
    args.includes("--prompt-file")
  );
}

function readHeadlessPrompt(args) {
  const promptFileIndex = args.indexOf("--prompt-file");
  if (promptFileIndex !== -1 && args[promptFileIndex + 1]) {
    return fs.readFileSync(args[promptFileIndex + 1], "utf8");
  }
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function answer(prompt, mode) {
  const markers = findMarkers(prompt);
  if (!markers) {
    console.log(`fake ${mode} response without markers`);
    return;
  }

  process.stdout.write(`${markers.startPrefix}${markers.nonce}\n`);

  if (prompt.includes("NO_DONE_MARKER")) {
    process.stdout.write(`fake ${mode} started without done marker\n`);
    return;
  }

  process.stdout.write(`fake ${mode} answer\n`);
  process.stdout.write(`prompt bytes ${Buffer.byteLength(prompt, "utf8")}\n`);
  process.stdout.write(`${markers.donePrefix}${markers.nonce}\n`);
}

function findMarkers(value) {
  const prefixes = [...value.matchAll(/- literal prefix:\s*([A-Z_]+_TMUX_(?:STARTED|DONE):)/g)].map(
    (match) => match[1]
  );
  const nonceMatch = /- nonce:\s*([A-Za-z0-9_.:-]{6,96})/.exec(value);
  if (prefixes.length < 2 || !nonceMatch) {
    return null;
  }
  return {
    startPrefix: prefixes[0],
    donePrefix: prefixes[1],
    nonce: nonceMatch[1]
  };
}
