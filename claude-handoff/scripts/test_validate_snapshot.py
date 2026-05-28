#!/usr/bin/env python3
"""Smoke tests for validate_snapshot.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("validate_snapshot.py")
VALID = """# Handoff Snapshot

## Metadata
- Schema Version: handoff-v1
- Skill Version: 0.1.1
- Skill Variant: codex-handoff
- Agent: codex

## Next Actions
1. Continue.
"""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cmd: list[str], check_result: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check_result)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        valid = root / "latest.md"
        valid.write_text(VALID, encoding="utf-8")
        ok = run([sys.executable, str(SCRIPT), str(valid)])
        check("OK:" in ok.stdout and "Schema Version: handoff-v1" in ok.stdout, "valid snapshot should pass")

        wrong = root / "wrong.md"
        wrong.write_text("# Not A Snapshot\n", encoding="utf-8")
        bad = run([sys.executable, str(SCRIPT), str(wrong)], check_result=False)
        check(bad.returncode == 1 and "first heading" in bad.stdout, "wrong heading should fail")

        binary = root / "binary.md"
        binary.write_bytes(b"\xff\xfe\x00")
        bad2 = run([sys.executable, str(SCRIPT), str(binary)], check_result=False)
        check(bad2.returncode == 1 and "valid UTF-8" in bad2.stdout, "binary snapshot should fail")
    print("validate_snapshot.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
