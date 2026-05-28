#!/usr/bin/env python3
"""Smoke tests for apply_marker_block.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("apply_marker_block.py")
BLOCK1 = """<!-- BEGIN handoff-rule -->
## Handoff / Clear Session Rule
first
<!-- END handoff-rule -->
"""
BLOCK2 = """<!-- BEGIN handoff-rule -->
## Handoff / Clear Session Rule
second
<!-- END handoff-rule -->
"""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cmd: list[str], input_text: str | None = None, check_result: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, capture_output=True, check=check_result)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "CODEX.md"
        target.write_text("# Existing\n", encoding="utf-8")
        run([sys.executable, str(SCRIPT), "--file", str(target)], BLOCK1)
        text = target.read_text(encoding="utf-8")
        check("# Existing" in text and "first" in text, "block should be inserted")
        run([sys.executable, str(SCRIPT), "--file", str(target)], BLOCK2)
        text = target.read_text(encoding="utf-8")
        check("second" in text and "first" not in text, "block should be replaced idempotently")

        broken = Path(td) / "BROKEN.md"
        broken.write_text("before\n<!-- BEGIN handoff-rule -->\npartial\n", encoding="utf-8")
        result = run([sys.executable, str(SCRIPT), "--file", str(broken)], BLOCK1, check_result=False)
        check(result.returncode == 2, "partial marker target should fail")
    print("apply_marker_block.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
