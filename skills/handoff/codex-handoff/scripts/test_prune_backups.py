#!/usr/bin/env python3
"""Safety-oriented smoke tests for prune_backups.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("prune_backups.py")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(cmd: list[str], check_result: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check_result)


def create_backups(handoff: Path, agent: str) -> None:
    (handoff / "latest.md").write_text("protected\n", encoding="utf-8")
    for i in range(25):
        (handoff / f"2026-05-28-{i:06d}-{agent}.md").write_text(str(i), encoding="utf-8")
    (handoff / f"notes-{agent}.md").write_text("not a timestamped snapshot\n", encoding="utf-8")
    (handoff / f"zzzz-{agent}.md").write_text("not a timestamped snapshot\n", encoding="utf-8")


def test_prune_agent(agent: str) -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        create_backups(handoff, agent)
        dry = run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--agent", agent, "--keep", "20", "--dry-run"])
        check("Pruning:   5" in dry.stdout, f"dry-run prune count wrong for {agent}")
        check("skipping non-snapshot filename" in dry.stdout, "malformed names should be skipped with warning")
        check(len(list(handoff.glob(f"*-{agent}.md"))) == 27, "dry-run should not delete")
        run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--agent", agent, "--keep", "20"])
        check((handoff / "latest.md").exists(), "latest.md should be protected")
        remaining = sorted(p.name for p in handoff.glob(f"2026-05-28-*-{agent}.md"))
        check(len(remaining) == 20, "wrong remaining backup count")
        check(remaining[0] == f"2026-05-28-000005-{agent}.md", "oldest kept file wrong")
        check(remaining[-1] == f"2026-05-28-000024-{agent}.md", "newest kept file wrong")
        check((handoff / f"notes-{agent}.md").exists(), "malformed note file should not be pruned")


def test_symlink_dir_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        outside = root / "outside"
        outside.mkdir()
        link = root / ".handoff"
        link.symlink_to(outside, target_is_directory=True)
        result = run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(link), "--agent", "codex"], check_result=False)
        check(result.returncode == 2, "symlinked .handoff directory should be rejected")
        check("Refusing to prune symlinked" in result.stderr, "symlink rejection message missing")


def test_symlink_file_skipped() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        target = root / "target.md"
        target.write_text("do not delete target\n", encoding="utf-8")
        (handoff / "2026-05-28-000000-codex.md").symlink_to(target)
        result = run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--agent", "codex", "--dry-run"])
        check("skipping symlink" in result.stdout, "symlinked file warning missing")
        check(target.exists(), "symlink target should not be deleted")


def main() -> int:
    test_prune_agent("codex")
    test_prune_agent("claude")
    test_symlink_dir_rejected()
    test_symlink_file_skipped()
    print("prune_backups.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
