#!/usr/bin/env python3
"""Safety-oriented smoke tests for handoff_snapshot.py."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("handoff_snapshot.py")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=True, env=env)


def run_probe(root: Path, *extra: str, env: dict[str, str] | None = None) -> str:
    return run([sys.executable, str(SCRIPT), "--root", str(root), *extra], env=env).stdout


def test_non_git() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "note.txt").write_text("hello\n", encoding="utf-8")
        out = run_probe(root)
        check("- Git repo: no" in out, "non-git root should be reported")
        check("### Recent Files" in out, "recent files block missing")
        check("note.txt" in out, "ordinary filename should be shown")
        check("Raw file contents" in out, "safety note missing")


def test_git_and_sensitive_paths() -> None:
    if shutil.which("git") is None:
        print("git not found; skipping git smoke test")
        return
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run(["git", "init"], root)
        run(["git", "config", "user.email", "test@example.invalid"], root)
        run(["git", "config", "user.name", "Handoff Test"], root)
        (root / "tracked.txt").write_text("one\n", encoding="utf-8")
        run(["git", "add", "tracked.txt"], root)
        run(["git", "commit", "-m", "init"], root)
        (root / "tracked.txt").write_text("one\ntwo\n", encoding="utf-8")
        (root / "anthropic_api.txt").write_text("not printed\n", encoding="utf-8")
        ssh = root / ".ssh"
        ssh.mkdir()
        (ssh / "mykey").write_text("not printed\n", encoding="utf-8")
        out = run_probe(root, "--limit", "20", "--max-bytes", "4096")
        check("- Git repo: yes" in out, "git root should be reported")
        check("### Git Status Short" in out, "git status block missing")
        check("tracked.txt" in out, "ordinary tracked filename should be shown")
        check("anthropic_api.txt" not in out, "sensitive filename leaked")
        check(".ssh/mykey" not in out, "sensitive ssh path leaked")
        check("[SENSITIVE-PATH:" in out, "sensitive path should be redacted")
        check("not printed" not in out, "file contents leaked")


def test_git_status_failure_is_unknown() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fakebin = root / "bin"
        fakebin.mkdir()
        fakegit = fakebin / "git"
        fakegit.write_text(
            "#!/bin/sh\n"
            "if [ \"$1 $2\" = 'rev-parse --show-toplevel' ]; then pwd; exit 0; fi\n"
            "if [ \"$1 $2\" = 'branch --show-current' ]; then echo main; exit 0; fi\n"
            "if [ \"$1 $2 $3\" = 'rev-parse --short HEAD' ]; then echo deadbee; exit 0; fi\n"
            "if [ \"$1 $2\" = 'status --short' ]; then echo fail >&2; exit 2; fi\n"
            "exit 2\n",
            encoding="utf-8",
        )
        fakegit.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{fakebin}:{env.get('PATH', '')}"
        out = run_probe(root, env=env)
        check("- Git repo: yes" in out, "fake git root should be accepted")
        check("- Git dirty: unknown" in out, "failed git status must not be reported clean")
        check("git status --short failed" in out, "status failure warning missing")


def test_non_git_caps() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for i in range(5):
            (root / f"file-{i}.txt").write_text("x\n", encoding="utf-8")
        out = run_probe(root, "--max-files", "2", "--recent-limit", "5")
        check("non-git scan stopped after 2 files" in out, "non-git max-files cap not reported")


def main() -> int:
    test_non_git()
    test_git_and_sensitive_paths()
    test_git_status_failure_is_unknown()
    test_non_git_caps()
    print("handoff_snapshot.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
