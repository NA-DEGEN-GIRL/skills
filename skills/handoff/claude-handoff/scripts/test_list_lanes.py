#!/usr/bin/env python3
"""Smoke tests for list_lanes.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("list_lanes.py")

SNAPSHOT = (
    "# Handoff Snapshot\n\n"
    "## Metadata\n"
    "- Schema Version: handoff-v1\n"
    "- Agent: codex\n"
    "- Created at: 2026-05-29T00:00:00Z\n"
    "- Scope: {scope}\n\n"
    "## Project Goal\n"
    "- {goal}\n"
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_list_lanes() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        write(handoff / "latest.md", SNAPSHOT.format(scope="(none)", goal="default lane goal"))
        write(handoff / "scopes" / "auth-refactor" / "latest.md", SNAPSHOT.format(scope="auth-refactor", goal="auth lane goal"))
        # invalid slug directory -> skipped
        write(handoff / "scopes" / "Bad_Name" / "latest.md", SNAPSHOT.format(scope="Bad_Name", goal="should be skipped"))
        # reserved scope names also match the slug regex but must be skipped
        for reserved in ("default", "latest", "scopes"):
            write(
                handoff / "scopes" / reserved / "latest.md",
                SNAPSHOT.format(scope=reserved, goal=f"reserved-{reserved}-goal"),
            )
        # valid slug but invalid snapshot -> marked INVALID
        write(handoff / "scopes" / "broken" / "latest.md", "not a handoff file\n")
        out = run([sys.executable, str(SCRIPT), "--root", str(root)]).stdout
        check("(default)" in out, "default lane should be listed")
        check("auth-refactor" in out, "valid scoped lane should be listed")
        check("auth lane goal" in out, "first goal line should be shown")
        check("Bad_Name" not in out, "invalid-slug lane should be skipped")
        for reserved in ("default", "latest", "scopes"):
            check(f"reserved-{reserved}-goal" not in out, f"reserved scope {reserved} should be skipped")
        check("broken: INVALID" in out, "broken snapshot should be marked INVALID")


def test_no_lanes() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".handoff").mkdir()
        out = run([sys.executable, str(SCRIPT), "--root", str(root)]).stdout
        check("No handoff lanes found" in out, "empty .handoff should report no lanes")


def main() -> int:
    test_list_lanes()
    test_no_lanes()
    print("list_lanes.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
