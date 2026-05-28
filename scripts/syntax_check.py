#!/usr/bin/env python3
"""Parse Python files without writing __pycache__ artifacts."""
from __future__ import annotations

import ast
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    failed = False
    for pattern in argv[1:]:
        for path in sorted(Path().glob(pattern)):
            if not path.is_file():
                continue
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                print(f"SYNTAX ERROR {path}: {exc}", file=sys.stderr)
                failed = True
            else:
                print(f"OK syntax {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
