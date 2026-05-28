#!/usr/bin/env python3
"""Prune dated handoff backups, keeping the N newest valid snapshots.

Safety defaults:
- never deletes latest.md
- refuses symlinked .handoff directories
- skips symlinked files
- only prunes timestamped handoff names like YYYY-MM-DD-HHMMSS-codex.md
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

PROTECTED_NAMES = {"latest.md"}
VALID_BACKUP_RE = re.compile(r"^(?P<stamp>\d{4}-\d{2}-\d{2}-\d{6})-(?P<agent>[A-Za-z0-9_-]+)\.md$")


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Keep newest N valid dated handoff backups and delete the rest.")
    parser.add_argument("--dir", default=".handoff", help="Directory containing backups; should be .handoff")
    parser.add_argument("--root", default=".", help="Expected project root used to prevent pruning outside the project")
    parser.add_argument("--agent", help="Agent suffix to prune, e.g. codex or claude; derives pattern '*-<agent>.md'")
    parser.add_argument("--pattern", help="Explicit glob such as '*-codex.md'; must still match timestamped snapshot names")
    parser.add_argument("--keep", type=int, default=20, help="Number of newest matching files to keep")
    parser.add_argument("--sort", choices=("name", "mtime"), default="name", help="Sort criterion for newest files")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without deleting")
    args = parser.parse_args()

    if args.keep < 1:
        print("--keep must be >= 1", file=sys.stderr)
        return 2
    if args.pattern and args.agent:
        print("Use either --agent or --pattern, not both", file=sys.stderr)
        return 2
    pattern = args.pattern or (f"*-{args.agent}.md" if args.agent else None)
    if not pattern:
        print("Specify --agent <name> or --pattern '*-<name>.md'", file=sys.stderr)
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

    matches, warnings = find_matches(directory, pattern)
    for warning in warnings:
        print(f"Warning: {warning}")
    matches = sort_matches(matches, args.sort)
    if not matches:
        print(f"No valid snapshot files matching `{pattern}` in {directory}; nothing to prune.")
        return 0

    keep, drop = matches[: args.keep], matches[args.keep :]

    print(f"Directory: {directory}")
    print(f"Pattern:   {pattern}")
    print(f"Sort:      {args.sort}")
    print(f"Matched:   {len(matches)} valid snapshot file(s)")
    print(f"Keeping:   {len(keep)} (newest)")
    print(f"Pruning:   {len(drop)}")

    for path in drop:
        action = "would delete" if args.dry_run else "deleting"
        print(f"  {action}: {path.name}")
        if not args.dry_run:
            try:
                path.unlink()
            except OSError as exc:
                print(f"    failed: {exc}", file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
