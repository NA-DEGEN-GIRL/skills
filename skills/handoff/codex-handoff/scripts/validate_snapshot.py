#!/usr/bin/env python3
"""Validate a handoff snapshot before loading it into an LLM context."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAX_DEFAULT_BYTES = 1024 * 1024
REQUIRED_HEADING = "# Handoff Snapshot"
METADATA_RE = re.compile(r"^-\s*([^:]+):\s*(.*)$")


def parse_metadata(text: str) -> dict[str, str]:
    lines = text.splitlines()
    metadata: dict[str, str] = {}
    in_metadata = False
    for line in lines:
        if line.strip() == "## Metadata":
            in_metadata = True
            continue
        if in_metadata and line.startswith("## "):
            break
        if in_metadata:
            match = METADATA_RE.match(line.strip())
            if match:
                metadata[match.group(1).strip()] = match.group(2).strip() or "Unknown"
    return metadata


def validate(path: Path, max_bytes: int) -> tuple[bool, list[str]]:
    messages: list[str] = []
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return False, ["snapshot file not found"]
    if max_bytes > 0 and len(data) > max_bytes:
        return False, [f"snapshot exceeds max bytes ({len(data)} > {max_bytes})"]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False, ["snapshot is not valid UTF-8"]
    if "\x00" in text:
        return False, ["snapshot contains NUL bytes"]
    first_nonempty = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if first_nonempty != REQUIRED_HEADING:
        return False, [f"first heading is not `{REQUIRED_HEADING}`"]
    metadata = parse_metadata(text)
    schema = metadata.get("Schema Version", "Unknown")
    agent = metadata.get("Agent", "Unknown")
    skill_variant = metadata.get("Skill Variant", "Unknown")
    messages.append(f"Schema Version: {schema}")
    messages.append(f"Agent: {agent}")
    messages.append(f"Skill Variant: {skill_variant}")
    if not metadata:
        messages.append("Metadata: missing or unparseable; treat missing fields as Unknown")
    return True, messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanity-check a handoff snapshot before reading it into context.")
    parser.add_argument("path", help="Snapshot path, usually .handoff/latest.md")
    parser.add_argument("--max-bytes", type=int, default=MAX_DEFAULT_BYTES, help="Maximum snapshot size to load")
    args = parser.parse_args()

    ok, messages = validate(Path(args.path), args.max_bytes)
    prefix = "OK" if ok else "INVALID"
    print(f"{prefix}: {args.path}")
    for message in messages:
        print(f"- {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
