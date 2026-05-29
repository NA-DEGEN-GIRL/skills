#!/usr/bin/env python3
"""Prune dated handoff backups, keeping the N newest valid snapshots per lane.

Safety defaults:
- never deletes latest.md
- refuses symlinked .handoff directories
- skips symlinked files and symlinked scope lane directories
- only prunes timestamped handoff names like YYYY-MM-DD-HHMMSS-codex.md

Lanes:
- default lane: backups directly under .handoff/
- scoped lanes: backups under .handoff/scopes/<scope>/
Retention is enforced per lane and per agent. With no lane flag, only the
default lane is pruned (back-compatible). Use --scope <slug> for one scoped
lane, or --all-lanes for the default lane plus every scoped lane.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

PROTECTED_NAMES = {"latest.md"}
VALID_BACKUP_RE = re.compile(r"^(?P<stamp>\d{4}-\d{2}-\d{2}-\d{6})-(?P<agent>[A-Za-z0-9_-]+)\.md$")
SCOPES_DIRNAME = "scopes"
SCOPE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESERVED_SCOPES = {"default", "latest", "scopes"}


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def valid_scope(scope: str) -> bool:
    return bool(SCOPE_RE.match(scope)) and scope not in RESERVED_SCOPES


def find_matches(directory: Path, pattern: str) -> tuple[list[Path], list[str]]:
    warnings: list[str] = []
    if not directory.is_dir():
        return [], warnings
    matches: list[Path] = []
    for entry in directory.iterdir():
        if entry.name in PROTECTED_NAMES:
            continue
        if entry.is_symlink():
            if fnmatch.fnmatch(entry.name, pattern):
                warnings.append(f"skipping symlink: {entry.name}")
            continue
        if not entry.is_file():
            continue
        if not fnmatch.fnmatch(entry.name, pattern):
            continue
        if not VALID_BACKUP_RE.match(entry.name):
            warnings.append(f"skipping non-snapshot filename: {entry.name}")
            continue
        matches.append(entry)
    return matches, warnings


def sort_matches(paths: list[Path], mode: str) -> list[Path]:
    if mode == "mtime":
        return sorted(paths, key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
    return sorted(paths, key=lambda p: p.name, reverse=True)


def prune_lane(directory: Path, pattern: str, keep: int, sort_mode: str, dry_run: bool) -> int:
    """Prune one lane directory. Returns 0 on success, 1 if a delete failed."""
    matches, warnings = find_matches(directory, pattern)
    for warning in warnings:
        print(f"Warning: {warning}")
    matches = sort_matches(matches, sort_mode)
    if not matches:
        print(f"No valid snapshot files matching `{pattern}` in {directory}; nothing to prune.")
        return 0

    keep_list, drop = matches[:keep], matches[keep:]

    print(f"Directory: {directory}")
    print(f"Pattern:   {pattern}")
    print(f"Sort:      {sort_mode}")
    print(f"Matched:   {len(matches)} valid snapshot file(s)")
    print(f"Keeping:   {len(keep_list)} (newest)")
    print(f"Pruning:   {len(drop)}")

    rc = 0
    for path in drop:
        action = "would delete" if dry_run else "deleting"
        print(f"  {action}: {path.name}")
        if not dry_run:
            try:
                path.unlink()
            except OSError as exc:
                print(f"    failed: {exc}", file=sys.stderr)
                rc = 1
    return rc


def resolve_lanes(directory: Path, scope: str | None, all_lanes: bool) -> list[Path]:
    """Return the lane directories to prune for the requested mode."""
    scopes_root = directory / SCOPES_DIRNAME
    if scope is not None:
        if scopes_root.exists() and scopes_root.is_symlink():
            print(f"Warning: skipping symlinked scopes directory: {scopes_root}")
            return []
        return [scopes_root / scope]
    if all_lanes:
        lanes = [directory]
        if scopes_root.exists() and scopes_root.is_symlink():
            print(f"Warning: skipping symlinked scopes directory: {scopes_root}")
        elif scopes_root.is_dir():
            for entry in sorted(scopes_root.iterdir()):
                if entry.is_symlink():
                    print(f"Warning: skipping symlinked lane: {entry.name}")
                    continue
                if not entry.is_dir():
                    continue
                if not valid_scope(entry.name):
                    print(f"Warning: skipping non-scope directory: {entry.name}")
                    continue
                lanes.append(entry)
        return lanes
    return [directory]


def main() -> int:
    parser = argparse.ArgumentParser(description="Keep newest N valid dated handoff backups per lane and delete the rest.")
    parser.add_argument("--dir", default=".handoff", help="Directory containing backups; should be .handoff")
    parser.add_argument("--root", default=".", help="Expected project root used to prevent pruning outside the project")
    parser.add_argument("--agent", help="Agent suffix to prune, e.g. codex or claude; derives pattern '*-<agent>.md'")
    parser.add_argument("--pattern", help="Explicit glob such as '*-codex.md'; must still match timestamped snapshot names")
    parser.add_argument("--keep", type=int, default=20, help="Number of newest matching files to keep per lane")
    parser.add_argument("--sort", choices=("name", "mtime"), default="name", help="Sort criterion for newest files")
    parser.add_argument("--scope", help="Prune only this scoped lane (.handoff/scopes/<scope>/)")
    parser.add_argument("--all-lanes", action="store_true", help="Prune the default lane and every .handoff/scopes/<scope>/ lane")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without deleting")
    args = parser.parse_args()

    if args.keep < 1:
        print("--keep must be >= 1", file=sys.stderr)
        return 2
    if args.pattern and args.agent:
        print("Use either --agent or --pattern, not both", file=sys.stderr)
        return 2
    if args.scope is not None and args.all_lanes:
        print("Use either --scope or --all-lanes, not both", file=sys.stderr)
        return 2
    pattern = args.pattern or (f"*-{args.agent}.md" if args.agent else None)
    if not pattern:
        print("Specify --agent <name> or --pattern '*-<name>.md'", file=sys.stderr)
        return 2
    if args.scope is not None and not valid_scope(args.scope):
        print(
            f"Invalid scope '{args.scope}': use lowercase letters, digits, and hyphens; "
            f"reserved names: {sorted(RESERVED_SCOPES)}",
            file=sys.stderr,
        )
        return 2

    raw_directory = Path(args.dir).expanduser()
    if raw_directory.exists() and raw_directory.is_symlink():
        print(f"Refusing to prune symlinked handoff directory: {raw_directory}", file=sys.stderr)
        return 2
    if raw_directory.name != ".handoff":
        print(f"Refusing to prune non-.handoff directory without explicit review: {raw_directory}", file=sys.stderr)
        return 2

    root = Path(args.root).expanduser().resolve()
    directory = raw_directory.resolve()
    if directory.exists() and not is_relative_to(directory, root):
        print(f"Refusing to prune outside root: {directory} not under {root}", file=sys.stderr)
        return 2

    lane_dirs = resolve_lanes(directory, args.scope, args.all_lanes)
    multi = len(lane_dirs) > 1
    rc = 0
    for lane in lane_dirs:
        if multi:
            print(f"== Lane: {lane} ==")
        if lane.exists() and lane.is_symlink():
            print(f"Warning: skipping symlinked lane: {lane}")
            continue
        if lane.exists() and not is_relative_to(lane.resolve(), root):
            print(f"Refusing to prune outside root: {lane} not under {root}", file=sys.stderr)
            rc = rc or 1
            continue
        lane_rc = prune_lane(lane, pattern, args.keep, args.sort, args.dry_run)
        rc = rc or lane_rc

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
