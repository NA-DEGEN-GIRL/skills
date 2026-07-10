#!/usr/bin/env python3
"""Safety tests for validate_snapshot.py and the shared bounded reader."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from snapshot_common import sanitize_display

SCRIPT = Path(__file__).with_name("validate_snapshot.py")


def snapshot(scope: str | None = None, agent: str = "codex") -> str:
    scope_line = f"- Scope: {scope}\n" if scope else ""
    return (
        "# Handoff Snapshot\n\n"
        "## Metadata\n"
        "- Schema Version: handoff-v1\n"
        "- Skill Version: 0.1.11\n"
        f"- Skill Variant: {agent}-handoff\n"
        f"- Agent: {agent}\n"
        f"{scope_line}"
        "- Created at: 2026-07-09T00:00:00Z\n\n"
        "## Next Actions\n1. Continue.\n"
    )


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cmd: list[str], check_result: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check_result)


def main() -> int:
    sanitized = sanitize_display(
        "owner@example.invalid /home/private-user/.ssh/id_rsa http://build.internal/job?token=secret"
    )
    check("private-user" not in sanitized, "absolute home username leaked")
    check(".ssh" not in sanitized and "id_rsa" not in sanitized, "sensitive path hint leaked")
    check("build.internal" not in sanitized and "REDACTED-URL" in sanitized, "internal URL leaked")
    check("owner@example.invalid" not in sanitized, "email leaked")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        valid = handoff / "latest.md"
        valid.write_text(snapshot(), encoding="utf-8")
        ok = run([sys.executable, str(SCRIPT), "./.handoff/latest.md", "--root", str(root)])
        check("OK:" in ok.stdout and "Schema Version: handoff-v1" in ok.stdout, "valid snapshot should pass")
        check(str(root) not in ok.stdout, "absolute root must not be printed")

        wrong = handoff / "2026-07-09-000001-codex.md"
        wrong.write_text("# Not A Snapshot\n", encoding="utf-8")
        bad = run([sys.executable, str(SCRIPT), str(wrong), "--root", str(root)], check_result=False)
        check(bad.returncode == 1 and "first heading" in bad.stdout, "wrong heading should fail")

        binary = handoff / "2026-07-09-000002-codex.md"
        binary.write_bytes(b"\xff\xfe\x00")
        bad2 = run([sys.executable, str(SCRIPT), str(binary), "--root", str(root)], check_result=False)
        check(bad2.returncode == 1 and "valid UTF-8" in bad2.stdout, "binary snapshot should fail")

        oversized = handoff / "2026-07-09-000003-codex.md"
        oversized.write_bytes(b"x" * 65)
        too_big = run(
            [sys.executable, str(SCRIPT), str(oversized), "--root", str(root), "--max-bytes", "64"],
            check_result=False,
        )
        check(too_big.returncode == 1 and "exceeds max bytes" in too_big.stdout, "max+1 input must fail")

        outside = root / "outside.md"
        outside.write_text(snapshot(), encoding="utf-8")
        out = run([sys.executable, str(SCRIPT), str(outside), "--root", str(root)], check_result=False)
        check(out.returncode == 1 and "outside selected lane" in out.stdout, "out-of-lane read must fail")

        target = root / "target.md"
        target.write_text(snapshot(), encoding="utf-8")
        link = handoff / "2026-07-09-000004-codex.md"
        link.symlink_to(target)
        linked = run([sys.executable, str(SCRIPT), str(link), "--root", str(root)], check_result=False)
        check(linked.returncode == 1 and "symlink" in linked.stdout, "leaf symlink must fail")

        nonregular = handoff / "2026-07-09-000005-codex.md"
        nonregular.mkdir()
        directory = run([sys.executable, str(SCRIPT), str(nonregular), "--root", str(root)], check_result=False)
        check(directory.returncode == 1 and "regular file" in directory.stdout, "non-regular input must fail")

        valid.write_text(snapshot("wrong-scope"), encoding="utf-8")
        mismatch = run([sys.executable, str(SCRIPT), str(valid), "--root", str(root)], check_result=False)
        check(mismatch.returncode == 1 and "must omit Scope" in mismatch.stdout, "default scope metadata must fail")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        outside = root / "outside"
        outside.mkdir()
        (outside / "latest.md").write_text(snapshot(), encoding="utf-8")
        (root / ".handoff").symlink_to(outside, target_is_directory=True)
        result = run(
            [sys.executable, str(SCRIPT), str(root / ".handoff" / "latest.md"), "--root", str(root)],
            check_result=False,
        )
        check(result.returncode == 1 and "symlinked path component" in result.stdout, "symlinked lane root must fail")

    print("validate_snapshot.py safety tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
