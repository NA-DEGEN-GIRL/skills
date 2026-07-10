#!/usr/bin/env python3
"""Deterministic same-lane selection tests for select_snapshot.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("select_snapshot.py")


def snapshot(scope: str | None, goal: str = "goal") -> str:
    scope_line = f"- Scope: {scope}\n" if scope else ""
    return (
        "# Handoff Snapshot\n\n## Metadata\n"
        "- Schema Version: handoff-v1\n- Agent: codex\n"
        "- Created at: 2026-07-09T00:00:00Z\n"
        f"{scope_line}\n## Project Goal\n- {goal}\n"
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(root: Path, *args: str, check_result: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        text=True,
        capture_output=True,
        check=check_result,
    )


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_latest_precedence() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lane = root / ".handoff"
        write(lane / "latest.md", snapshot(None, "latest"))
        write(lane / "2026-07-09-235959-codex.md", snapshot(None, "new backup"))
        result = run(root, "--path-only")
        check(result.stdout.strip() == ".handoff/latest.md", "valid latest must win over backups")


def test_invalid_latest_and_newest_invalid_fallback() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lane = root / ".handoff"
        write(lane / "latest.md", "invalid\n")
        write(lane / "2026-07-09-000003-codex.md", "invalid newest\n")
        write(lane / "2026-07-09-000002-codex.md", snapshot(None, "chosen"))
        write(lane / "2026-07-09-000001-codex.md", snapshot(None, "old"))
        result = run(root)
        check("2026-07-09-000002-codex.md" in result.stdout, "newest valid backup should be selected")
        check(result.stdout.count("Skipped:") == 2, "both invalid candidates should be reported")


def test_scoped_orphan_and_no_cross_lane_fallback() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        write(root / ".handoff" / "latest.md", snapshot(None, "default"))
        orphan = root / ".handoff" / "scopes" / "auth"
        write(orphan / "2026-07-09-000001-codex.md", snapshot("auth", "orphan"))
        selected = run(root, "--scope", "auth", "--path-only")
        check("scopes/auth/2026-07-09-000001-codex.md" in selected.stdout, "orphan scoped backup should select")

        bad_lane = root / ".handoff" / "scopes" / "broken"
        write(bad_lane / "latest.md", snapshot("wrong", "mismatch"))
        failed = run(root, "--scope", "broken", check_result=False)
        check(failed.returncode == 1, "invalid scoped lane should have no selection")
        check(".handoff/latest.md" not in failed.stdout, "scoped selection must never fall back to default")


def test_symlink_latest_is_skipped() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lane = root / ".handoff"
        lane.mkdir()
        target = root / "outside.md"
        target.write_text(snapshot(None), encoding="utf-8")
        (lane / "latest.md").symlink_to(target)
        write(lane / "2026-07-09-000001-codex.md", snapshot(None, "safe"))
        result = run(root)
        check("2026-07-09-000001-codex.md" in result.stdout, "symlink latest should be skipped")
        check("symlink" in result.stdout, "symlink rejection should be reported")


def main() -> int:
    test_latest_precedence()
    test_invalid_latest_and_newest_invalid_fallback()
    test_scoped_orphan_and_no_cross_lane_fallback()
    test_symlink_latest_is_skipped()
    print("select_snapshot.py safety tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
