#!/usr/bin/env python3
"""List handoff lanes (default + scoped) with metadata, for resume disambiguation.

Read-only. Scans `.handoff/latest.md` (default lane) and
`.handoff/scopes/<scope>/latest.md` (scoped lanes, valid slugs only), validates
each, and prints scope, agent, created-at, and the first Project Goal line so a
resuming agent can pick a lane without ad-hoc shell globbing.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADING = "# Handoff Snapshot"
MAX_DEFAULT_BYTES = 1024 * 1024
SCOPES_DIRNAME = "scopes"
SCOPE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESERVED_SCOPES = {"default", "latest", "scopes"}
METADATA_RE = re.compile(r"^-\s*([^:]+):\s*(.*)$")


def read_snapshot(path: Path, max_bytes: int) -> tuple[str | None, str]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, f"unreadable ({exc})"
    if max_bytes > 0 and len(data) > max_bytes:
        return None, f"too large ({len(data)} bytes)"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None, "not utf-8"
    if "\x00" in text:
        return None, "contains NUL"
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    if first != REQUIRED_HEADING:
        return None, "missing handoff heading"
    return text, "ok"


def valid_scope(scope: str) -> bool:
    return bool(SCOPE_RE.match(scope)) and scope not in RESERVED_SCOPES


def parse_metadata(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    in_meta = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Metadata":
            in_meta = True
            continue
        if in_meta and stripped.startswith("## "):
            break
        if in_meta:
            match = METADATA_RE.match(stripped)
            if match:
                meta[match.group(1).strip()] = match.group(2).strip() or "Unknown"
    return meta


def first_goal(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "## Project Goal":
            for nxt in lines[index + 1:]:
                token = nxt.strip()
                if token.startswith("## "):
                    break
                if token:
                    return token.lstrip("- ").strip()[:80]
            break
    return ""


def lane_snapshots(handoff: Path) -> list[tuple[str, Path]]:
    entries: list[tuple[str, Path]] = []
    default = handoff / "latest.md"
    if default.is_file():
        entries.append(("(default)", default))
    scopes_root = handoff / SCOPES_DIRNAME
    if scopes_root.is_dir() and not scopes_root.is_symlink():
        for entry in sorted(scopes_root.iterdir()):
            if entry.is_symlink() or not entry.is_dir():
                continue
            if not valid_scope(entry.name):
                continue
            latest = entry / "latest.md"
            if latest.is_file():
                entries.append((entry.name, latest))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="List handoff lanes with metadata for resume selection.")
    parser.add_argument("--root", default=".", help="Repo root or working directory")
    parser.add_argument("--dir", default=".handoff", help="Handoff directory under root")
    parser.add_argument("--max-bytes", type=int, default=MAX_DEFAULT_BYTES, help="Maximum snapshot size to read")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    dir_arg = Path(args.dir)
    handoff = dir_arg if dir_arg.is_absolute() else (root / dir_arg)

    entries = lane_snapshots(handoff)
    if not entries:
        print(f"No handoff lanes found under {handoff}")
        return 0

    print(f"Handoff lanes under {handoff}:")
    for scope, path in entries:
        text, status = read_snapshot(path, args.max_bytes)
        if text is None:
            print(f"- {scope}: INVALID ({status}) [{path}]")
            continue
        meta = parse_metadata(text)
        agent = meta.get("Agent", "Unknown")
        created = meta.get("Created at", "Unknown")
        scope_field = meta.get("Scope", "(none)")
        goal = first_goal(text) or "(no goal line)"
        print(f"- {scope}: agent={agent}, created={created}, scope_field={scope_field}")
        print(f"    goal: {goal}")
        print(f"    path: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
