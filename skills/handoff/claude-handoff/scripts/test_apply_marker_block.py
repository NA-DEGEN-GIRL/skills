#!/usr/bin/env python3
"""Smoke tests for apply_marker_block.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import stat
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
        target.chmod(0o640)
        run([sys.executable, str(SCRIPT), "--root", td, "--file", str(target)], BLOCK1)
        text = target.read_text(encoding="utf-8")
        check("# Existing" in text and "first" in text, "block should be inserted")
        check(stat.S_IMODE(target.stat().st_mode) == 0o640, "existing target mode should be preserved")
        run([sys.executable, str(SCRIPT), "--root", td, "--file", str(target)], BLOCK2)
        text = target.read_text(encoding="utf-8")
        check("second" in text and "first" not in text, "block should be replaced idempotently")

        broken = Path(td) / "BROKEN.md"
        broken.write_text("before\n<!-- BEGIN handoff-rule -->\npartial\n", encoding="utf-8")
        result = run([sys.executable, str(SCRIPT), "--root", td, "--file", str(broken)], BLOCK1, check_result=False)
        check(result.returncode == 2, "partial marker target should fail")

        duplicate = Path(td) / "DUPLICATE.md"
        duplicate.write_text(BLOCK1 + "\n" + BLOCK2, encoding="utf-8")
        duplicate_result = run([sys.executable, str(SCRIPT), "--root", td, "--file", str(duplicate)], BLOCK1, check_result=False)
        check(duplicate_result.returncode == 2 and "duplicate markers" in duplicate_result.stderr, "duplicate target markers should fail")

        duplicate_block = BLOCK1 + "\n<!-- BEGIN handoff-rule -->\n"
        block_result = run([sys.executable, str(SCRIPT), "--root", td, "--file", str(target)], duplicate_block, check_result=False)
        check(block_result.returncode == 2 and "exactly once" in block_result.stderr, "duplicate input markers should fail")

        repo = Path(td) / "repo"
        outside = Path(td) / "outside"
        repo.mkdir()
        outside.mkdir()
        outside_target = outside / "CODEX.md"
        outside_target.write_text("outside sentinel\n", encoding="utf-8")
        (repo / "link").symlink_to(outside, target_is_directory=True)
        escaped = run(
            [sys.executable, str(SCRIPT), "--root", str(repo), "--file", str(repo / "link" / "CODEX.md")],
            BLOCK1,
            check_result=False,
        )
        check(escaped.returncode == 2, "symlinked parent should be rejected")
        check(outside_target.read_text() == "outside sentinel\n", "symlink parent escaped trusted root")
    print("apply_marker_block.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
