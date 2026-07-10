#!/usr/bin/env python3
"""Safety and orphan-discovery tests for list_lanes.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("list_lanes.py")


def snapshot(scope: str | None, goal: str, agent: str = "codex") -> str:
    scope_line = f"- Scope: {scope}\n" if scope else ""
    return (
        "# Handoff Snapshot\n\n## Metadata\n"
        "- Schema Version: handoff-v1\n"
        f"- Agent: {agent}\n"
        "- Created at: 2026-07-09T00:00:00Z\n"
        f"{scope_line}\n## Project Goal\n- {goal}\n"
    )


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cmd: list[str], check_result: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check_result)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_list_lanes() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        write(handoff / "latest.md", snapshot(None, "default lane goal"))
        write(handoff / "scopes" / "auth-refactor" / "latest.md", snapshot("auth-refactor", "auth lane goal"))
        # Orphan lane: dated backup exists without latest.md.
        write(
            handoff / "scopes" / "orphan" / "2026-07-09-000001-codex.md",
            snapshot("orphan", "api_key=supersecretvalue http://build.internal/job /home/alice/.ssh/id_rsa"),
        )
        write(handoff / "scopes" / "Bad_Name" / "latest.md", snapshot("Bad_Name", "skipped"))
        write(handoff / "scopes" / "broken" / "latest.md", "not a handoff file\n")
        result = run([sys.executable, str(SCRIPT), "--root", str(root)], check_result=False)
        out = result.stdout
        check(result.returncode == 1, "an invalid discovered lane should make status nonzero")
        check("(default)" in out and "auth-refactor" in out, "default and scoped lanes should be listed")
        check("orphan" in out and "source=backup" in out, "backup-only orphan lane should be listed")
        check("auth lane goal" in out, "goal summary missing")
        check("supersecretvalue" not in out and "[REDACTED]" in out, "goal secrets must be redacted")
        check("build.internal" not in out and "alice" not in out and ".ssh" not in out, "private URL/path leaked")
        check("Bad_Name" not in out, "invalid-slug lane should be skipped")
        check("broken: INVALID" in out, "invalid lane should be marked")
        check(str(root) not in out, "absolute root must not be printed")


def test_fallback_and_scope_mismatch() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lane = root / ".handoff" / "scopes" / "auth"
        write(lane / "latest.md", snapshot("wrong", "wrong scope"))
        write(lane / "2026-07-09-000001-codex.md", snapshot("auth", "backup goal"))
        result = run([sys.executable, str(SCRIPT), "--root", str(root)])
        check("source=backup" in result.stdout, "invalid latest should fall back in lane")
        check("Scope metadata/path mismatch" in result.stdout, "fallback reason should explain mismatch")


def test_no_lanes_and_unsafe_scopes() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".handoff").mkdir()
        out = run([sys.executable, str(SCRIPT), "--root", str(root)]).stdout
        check("No handoff lanes found" in out, "empty .handoff should report no lanes")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        outside = root / "outside"
        outside.mkdir()
        (handoff / "scopes").symlink_to(outside, target_is_directory=True)
        result = run([sys.executable, str(SCRIPT), "--root", str(root)], check_result=False)
        check(result.returncode != 0 and "unsafe scopes" in result.stderr, "unsafe scopes root must be signaled")


def main() -> int:
    test_list_lanes()
    test_fallback_and_scope_mismatch()
    test_no_lanes_and_unsafe_scopes()
    print("list_lanes.py safety tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
