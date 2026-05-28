#!/usr/bin/env python3
"""Idempotently insert or replace a Markdown marker block.

Reads a complete block from --block-file or stdin. The block must include both
markers, e.g. <!-- BEGIN handoff-rule --> and <!-- END handoff-rule -->.
Writes atomically via a temporary file and os.replace().
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_BEGIN = "<!-- BEGIN handoff-rule -->"
DEFAULT_END = "<!-- END handoff-rule -->"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def apply_block(original: str, block: str, begin: str, end: str) -> tuple[str, str]:
    if begin not in block or end not in block or block.index(begin) > block.index(end):
        raise ValueError("block must contain begin/end markers in order")
    start = original.find(begin)
    finish = original.find(end)
    if (start == -1) ^ (finish == -1):
        raise ValueError("target contains only one marker; refusing partial replacement")
    if start != -1:
        if start > finish:
            raise ValueError("target markers are out of order")
        finish += len(end)
        new_text = original[:start].rstrip() + "\n\n" + block.strip() + "\n" + original[finish:].lstrip("\n")
        return new_text, "replaced"
    separator = "\n\n" if original.strip() else ""
    return original.rstrip() + separator + block.strip() + "\n", "inserted"


def main() -> int:
    parser = argparse.ArgumentParser(description="Insert or replace a marker-delimited Markdown block.")
    parser.add_argument("--file", required=True, help="Target Markdown file")
    parser.add_argument("--block-file", help="File containing full marker block; stdin is used when omitted")
    parser.add_argument("--begin", default=DEFAULT_BEGIN, help="Begin marker")
    parser.add_argument("--end", default=DEFAULT_END, help="End marker")
    parser.add_argument("--dry-run", action="store_true", help="Print action without writing")
    args = parser.parse_args()

    target = Path(args.file)
    block = Path(args.block_file).read_text(encoding="utf-8") if args.block_file else sys.stdin.read()
    try:
        new_text, action = apply_block(read_text(target), block, args.begin, args.end)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"Would {action} marker block in {target}")
        return 0
    atomic_write(target, new_text)
    print(f"{action.capitalize()} marker block in {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
