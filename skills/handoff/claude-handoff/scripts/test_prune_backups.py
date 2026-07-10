#!/usr/bin/env python3
"""Safety-oriented smoke tests for prune_backups.py."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import contextlib
import io
import os
from pathlib import Path
from unittest import mock

import prune_backups as pruner

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
        check("invalid timestamp/name" in dry.stdout, "malformed names should be skipped with warning")
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
        check("Refusing unsafe requested lane" in result.stderr, "symlink rejection message missing")


def test_symlink_file_skipped() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        target = root / "target.md"
        target.write_text("do not delete target\n", encoding="utf-8")
        (handoff / "2026-05-28-000000-codex.md").symlink_to(target)
        result = run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--agent", "codex", "--dry-run"], check_result=False)
        check(result.returncode != 0 and "unsafe candidate refused" in result.stdout, "symlinked file warning/status missing")
        check(target.exists(), "symlink target should not be deleted")


def test_prune_scope_isolated() -> None:
    """--scope prunes only the named lane and leaves the default lane untouched."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        # default lane: 25 backups that must NOT be touched by a scoped prune
        create_backups(handoff, "codex")
        scope_dir = handoff / "scopes" / "auth-refactor"
        scope_dir.mkdir(parents=True)
        create_backups(scope_dir, "codex")
        run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--scope", "auth-refactor", "--agent", "codex", "--keep", "20"])
        scope_remaining = sorted(p.name for p in scope_dir.glob("2026-05-28-*-codex.md"))
        check(len(scope_remaining) == 20, "scoped lane should be pruned to 20")
        check((scope_dir / "latest.md").exists(), "scoped latest.md should be protected")
        default_remaining = list(handoff.glob("2026-05-28-*-codex.md"))
        check(len(default_remaining) == 25, "default lane must be untouched by --scope")


def test_all_lanes() -> None:
    """--all-lanes prunes the default lane plus every scoped lane, per lane."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        create_backups(handoff, "codex")
        for scope in ("auth-refactor", "ui"):
            d = handoff / "scopes" / scope
            d.mkdir(parents=True)
            create_backups(d, "codex")
        # a non-scope-name directory under scopes/ must be ignored by --all-lanes
        bad = handoff / "scopes" / "Bad_Name"
        bad.mkdir(parents=True)
        create_backups(bad, "codex")
        reserved_dirs = []
        for reserved in ("default", "latest", "scopes"):
            d = handoff / "scopes" / reserved
            d.mkdir(parents=True)
            create_backups(d, "codex")
            reserved_dirs.append(d)
        result = run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--all-lanes", "--agent", "codex", "--keep", "20"])
        check("== Lane:" in result.stdout, "all-lanes should print per-lane headers")
        check(len(list(handoff.glob("2026-05-28-*-codex.md"))) == 20, "default lane should be pruned to 20")
        check(len(list(bad.glob("2026-05-28-*-codex.md"))) == 25, "invalid-slug dir must be left untouched")
        for d in reserved_dirs:
            check(len(list(d.glob("2026-05-28-*-codex.md"))) == 25, f"reserved dir {d.name} must be left untouched")
        for scope in ("auth-refactor", "ui"):
            d = handoff / "scopes" / scope
            check(len(list(d.glob("2026-05-28-*-codex.md"))) == 20, f"scoped lane {scope} should be pruned to 20")
            check((d / "latest.md").exists(), f"scoped latest.md for {scope} should be protected")


def test_symlink_scopes_root_skipped() -> None:
    """A symlinked .handoff/scopes directory is skipped, not traversed."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        outside = root / "outside-scopes"
        outside.mkdir()
        (handoff / "scopes").symlink_to(outside, target_is_directory=True)
        result = run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--scope", "auth", "--agent", "codex"], check_result=False)
        check(result.returncode != 0 and "unsafe requested lane" in result.stderr, "symlinked scopes root should fail under --scope")
        all_lanes = run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--all-lanes", "--agent", "codex"], check_result=False)
        check(all_lanes.returncode != 0 and "unsafe scopes" in all_lanes.stderr, "symlinked scopes root should signal under --all-lanes")


def test_invalid_scope_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        result = run([sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--scope", "../evil", "--agent", "codex"], check_result=False)
        check(result.returncode == 2, "path-traversal scope should be rejected")
        check("invalid scope" in result.stderr, "invalid scope message missing")


def test_invalid_agent_and_timestamp_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        unsafe_agent = run(
            [sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--agent", "*"],
            check_result=False,
        )
        check(unsafe_agent.returncode == 2, "glob-like agent must be rejected")
        invalid_stamp = handoff / "2026-99-99-999999-codex.md"
        invalid_stamp.write_text("do not delete\n", encoding="utf-8")
        result = run(
            [sys.executable, str(SCRIPT), "--root", str(root), "--dir", str(handoff), "--agent", "codex", "--keep", "1"],
        )
        check("invalid timestamp/name" in result.stdout and invalid_stamp.exists(), "invalid timestamp must never be pruned")


def test_lane_swap_never_deletes_outside() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        handoff = root / ".handoff"
        handoff.mkdir()
        for second in range(3):
            name = f"2026-05-28-00000{second}-codex.md"
            (handoff / name).write_text("inside\n", encoding="utf-8")
        outside = root / "outside"
        outside.mkdir()
        outside_names = []
        for second in range(3):
            name = f"2026-05-28-00000{second}-codex.md"
            (outside / name).write_text("outside\n", encoding="utf-8")
            outside_names.append(name)

        original_find = pruner.find_matches
        swapped = False

        def swap_after_enumeration(handle: object, agent: str):
            nonlocal swapped
            result = original_find(handle, agent)
            if not swapped:
                swapped = True
                handoff.rename(root / ".handoff-moved")
                handoff.symlink_to(outside, target_is_directory=True)
            return result

        argv = [str(SCRIPT), "--root", str(root), "--agent", "codex", "--keep", "1"]
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", argv), mock.patch.object(
            pruner, "find_matches", side_effect=swap_after_enumeration
        ):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = pruner.main()
        check(rc != 0, "lane swap during prune should return nonzero")
        check(all((outside / name).exists() for name in outside_names), "lane swap deleted outside files")


def test_leaf_replacement_is_not_deleted() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        lane = root / ".handoff"
        lane.mkdir()
        old = lane / "2026-05-28-000000-codex.md"
        keep = lane / "2026-05-28-000001-codex.md"
        old.write_text("old\n", encoding="utf-8")
        keep.write_text("keep\n", encoding="utf-8")
        original_rename = pruner.os.rename
        replaced = False

        def replace_before_quarantine(src: str, dst: str, *args: object, **kwargs: object) -> None:
            nonlocal replaced
            if src == old.name and not replaced:
                replaced = True
                replacement = lane / ".replacement.tmp"
                replacement.write_text("replacement\n", encoding="utf-8")
                os.replace(replacement, old)
            original_rename(src, dst, *args, **kwargs)

        argv = [str(SCRIPT), "--root", str(root), "--agent", "codex", "--keep", "1"]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(
            pruner.os, "rename", side_effect=replace_before_quarantine
        ), mock.patch.object(pruner, "require_dirfd_support", return_value=None):
            rc = pruner.main()
        check(rc != 0, "leaf replacement should make prune nonzero")
        check(old.exists() and old.read_text() == "replacement\n", "replacement file was deleted")


def main() -> int:
    test_prune_agent("codex")
    test_prune_agent("claude")
    test_symlink_dir_rejected()
    test_symlink_file_skipped()
    test_prune_scope_isolated()
    test_all_lanes()
    test_symlink_scopes_root_skipped()
    test_invalid_scope_rejected()
    test_invalid_agent_and_timestamp_rejected()
    test_lane_swap_never_deletes_outside()
    test_leaf_replacement_is_not_deleted()
    print("prune_backups.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
