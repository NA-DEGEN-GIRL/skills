#!/usr/bin/env python3
"""Deterministically select latest, then newest valid same-lane backup."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from snapshot_common import (
    MAX_DEFAULT_BYTES,
    SnapshotError,
    lane_for,
    path_display,
    resolve_handoff,
    sanitize_display,
    select_valid_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Select a validated snapshot from exactly one handoff lane.")
    parser.add_argument("--root", default=".", help="Repo root or working directory")
    parser.add_argument("--dir", default=".handoff", help="Handoff directory under root")
    parser.add_argument("--scope", help="Selected scoped lane; omit for the default lane")
    parser.add_argument("--max-bytes", type=int, default=MAX_DEFAULT_BYTES, help="Positive maximum snapshot size")
    parser.add_argument("--path-only", action="store_true", help="Print only the repo-relative selected path")
    args = parser.parse_args()

    try:
        root, handoff = resolve_handoff(Path(args.root).expanduser(), Path(args.dir).expanduser())
        lane = lane_for(handoff, args.scope)
        snapshot, errors = select_valid_snapshot(lane, args.max_bytes)
    except SnapshotError as exc:
        print(f"Error: {sanitize_display(str(exc), 300)}", file=sys.stderr)
        return 2

    if snapshot is None or snapshot.path is None:
        print(f"No valid handoff snapshot in lane {lane.label}.", file=sys.stderr)
        for error in errors:
            print(f"- {sanitize_display(error, 300)}", file=sys.stderr)
        return 1

    selected = path_display(snapshot.path, root)
    if args.path_only:
        print(selected)
        return 0
    source = "latest" if snapshot.path.name == "latest.md" else "dated backup"
    print(f"SELECTED: {selected}")
    print(f"- Lane: {lane.label}")
    print(f"- Source: {source}")
    print(f"- Agent: {sanitize_display(snapshot.metadata.get('Agent', 'Unknown'))}")
    print(f"- Created at: {sanitize_display(snapshot.metadata.get('Created at', 'Unknown'))}")
    print(f"- SHA-256: {snapshot.sha256}")
    for error in errors:
        print(f"- Skipped: {sanitize_display(error, 300)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
