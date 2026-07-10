#!/usr/bin/env python3
"""Smoke tests for the safe skill installer using isolated temporary homes."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).with_name("install_skill.py")
REPO_ROOT = Path(__file__).resolve().parents[1]


def load_installer_module():
    spec = importlib.util.spec_from_file_location("repo_install_skill", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load installer module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(args)}\n{result.stdout}\n{result.stderr}"
        )
    return result


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_copy_backup_doctor_and_rollback() -> None:
    with tempfile.TemporaryDirectory() as raw:
        home = Path(raw) / "codex"
        common = ("--agent", "codex", "--skill", "distill-ramble", "--agent-home", str(home))

        dry = run("install", *common)
        check("No changes made" in dry.stdout, "install must be dry-run by default")
        check(not (home / "skills").exists(), "dry-run created the skills directory")

        run("install", *common, "--apply")
        dest = home / "skills" / "distill-ramble"
        check((dest / "SKILL.md").is_file(), "copy install did not create the package")
        check(not list((home / "skills").glob("*.bak.*")), "backup leaked into discovery root")

        (dest / "VERSION").write_text("0.0.0\n", encoding="utf-8")
        run("install", *common, "--apply")
        backups = sorted((home / "skill-backups" / "distill-ramble").glob("*/payload"))
        check(len(backups) == 1, "replacement did not create exactly one external backup")
        check((backups[0] / "VERSION").read_text(encoding="utf-8").strip() == "0.0.0", "wrong backup payload")

        doctor = run("doctor", *common)
        check("OK distill-ramble" in doctor.stdout, "doctor did not report current install")

        run("rollback", *common, "--apply")
        check((dest / "VERSION").read_text(encoding="utf-8").strip() == "0.0.0", "rollback did not restore backup")


def test_symlink_replaces_directory_instead_of_nesting() -> None:
    with tempfile.TemporaryDirectory() as raw:
        home = Path(raw) / "claude"
        dest = home / "skills" / "orient-repo"
        dest.mkdir(parents=True)
        (dest / "old.txt").write_text("old\n", encoding="utf-8")
        run(
            "install",
            "--agent",
            "claude",
            "--skill",
            "orient-repo",
            "--agent-home",
            str(home),
            "--mode",
            "symlink",
            "--apply",
        )
        check(dest.is_symlink(), "symlink mode left a directory at the destination")
        check(not (dest / "orient-repo").is_symlink(), "installer created a nested symlink")
        payloads = list((home / "skill-backups" / "orient-repo").glob("*/payload"))
        check(len(payloads) == 1 and (payloads[0] / "old.txt").is_file(), "old directory was not backed up")

        run(
            "rollback",
            "--agent",
            "claude",
            "--skill",
            "orient-repo",
            "--agent-home",
            str(home),
            "--apply",
        )
        check(not dest.is_symlink() and (dest / "old.txt").is_file(), "rollback did not restore the arbitrary old directory")


def test_doctor_reports_discoverable_duplicate() -> None:
    with tempfile.TemporaryDirectory() as raw:
        home = Path(raw) / "codex"
        common = ("--agent", "codex", "--skill", "orient-repo", "--agent-home", str(home))
        run("install", *common, "--apply")
        duplicate = home / "skills" / "orient-repo.bak.legacy"
        shutil.copytree(REPO_ROOT / "skills" / "repo-orientation" / "orient-repo", duplicate)
        result = run("doctor", *common, check=False)
        check(result.returncode == 1, "doctor must fail when a duplicate is discoverable")
        check("DUPLICATE" in result.stdout, "doctor did not identify the duplicate")


def test_backup_root_inside_discovery_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw:
        home = Path(raw) / "codex"
        result = run(
            "install",
            "--agent",
            "codex",
            "--skill",
            "orient-repo",
            "--agent-home",
            str(home),
            "--backup-root",
            str(home / "skills" / "backups"),
            check=False,
        )
        check(result.returncode == 2, "unsafe backup root must be rejected")
        check("outside the agent skills" in result.stderr, "unsafe backup error was not actionable")


def test_source_tree_symlink_is_rejected() -> None:
    if not hasattr(os, "symlink"):
        return
    installer = load_installer_module()
    with tempfile.TemporaryDirectory() as raw:
        source = Path(raw) / "package"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
        outside = Path(raw) / "outside.txt"
        outside.write_text("private\n", encoding="utf-8")
        try:
            (source / "linked.txt").symlink_to(outside)
        except OSError:
            return
        try:
            installer.validate_source_tree(source)
        except installer.InstallError as exc:
            check("contains a symlink" in str(exc), "source symlink error was not actionable")
        else:
            raise AssertionError("source package symlink must be rejected")


def test_source_path_rejects_symlink_before_parsing_entrypoint() -> None:
    if not hasattr(os, "symlink"):
        return
    installer = load_installer_module()
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw) / "repo"
        source = root / "skills" / "demo"
        source.mkdir(parents=True)
        outside = Path(raw) / "outside-skill.md"
        outside.write_text("---\nname: demo\n---\n", encoding="utf-8")
        try:
            (source / "SKILL.md").symlink_to(outside)
        except OSError:
            return
        previous_root = installer.REPO_ROOT
        installer.REPO_ROOT = root
        try:
            installer.source_path({"name": "demo", "source": "skills/demo"})
        except installer.InstallError as exc:
            check("contains a symlink" in str(exc), "entrypoint symlink was read before rejection")
        else:
            raise AssertionError("source_path must reject a symlinked SKILL.md")
        finally:
            installer.REPO_ROOT = previous_root


def test_per_skill_backup_symlink_is_rejected() -> None:
    if not hasattr(os, "symlink"):
        return
    with tempfile.TemporaryDirectory() as raw:
        home = Path(raw) / "codex"
        trap = home / "skills" / "trap"
        trap.mkdir(parents=True)
        backup_root = home / "skill-backups"
        backup_root.mkdir()
        try:
            (backup_root / "distill-ramble").symlink_to(trap, target_is_directory=True)
        except OSError:
            return
        result = run(
            "install",
            "--agent",
            "codex",
            "--skill",
            "distill-ramble",
            "--agent-home",
            str(home),
            "--apply",
            check=False,
        )
        check(result.returncode == 2, "symlinked per-skill backup directory must fail")
        check("symlinked per-skill backup" in result.stderr, "backup symlink error was not actionable")
        check(not list(trap.iterdir()), "backup payload escaped into the skills discovery tree")


def test_operation_lock_rejects_concurrent_mutation() -> None:
    installer = load_installer_module()
    with tempfile.TemporaryDirectory() as raw:
        home = Path(raw) / "codex"
        lock = home / "skill-locks" / "distill-ramble.lock"
        lock.parent.mkdir(parents=True)
        handle = installer.acquire_operation_lock(lock)
        try:
            result = run(
                "install",
                "--agent",
                "codex",
                "--skill",
                "distill-ramble",
                "--agent-home",
                str(home),
                "--backup-root",
                str(home / "alternate-backups"),
                "--apply",
                check=False,
            )
        finally:
            installer.release_operation_lock(handle)
        check(result.returncode == 2, "concurrent install must fail closed")
        check("holds this skill lock" in result.stderr, "concurrency error was not actionable")
        check(not (home / "skills" / "distill-ramble").exists(), "blocked install mutated destination")


def test_operation_lock_symlink_is_rejected() -> None:
    if not hasattr(os, "symlink"):
        return
    installer = load_installer_module()
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        lock = root / "skill-locks" / "demo.lock"
        lock.parent.mkdir()
        outside = root / "outside.lock"
        outside.write_text("sentinel\n", encoding="utf-8")
        try:
            lock.symlink_to(outside)
        except OSError:
            return
        try:
            installer.acquire_operation_lock(lock)
        except installer.InstallError as exc:
            check("operation lock must be a real" in str(exc), "lock symlink error was not actionable")
        else:
            raise AssertionError("symlinked operation lock must be rejected")
        check(outside.read_text(encoding="utf-8") == "sentinel\n", "lock symlink target was modified")


def test_doctor_handles_invalid_utf8() -> None:
    with tempfile.TemporaryDirectory() as raw:
        home = Path(raw) / "codex"
        common = ("--agent", "codex", "--skill", "distill-ramble", "--agent-home", str(home))
        run("install", *common, "--apply")
        (home / "skills" / "distill-ramble" / "SKILL.md").write_bytes(b"\xff\xfe")
        result = run("doctor", *common, check=False)
        check(result.returncode == 1, "doctor must report invalid UTF-8 as an issue")
        check("INVALID distill-ramble" in result.stdout, "doctor did not classify invalid UTF-8")
        check("Traceback" not in result.stderr, "doctor crashed on invalid UTF-8")


def main() -> int:
    test_copy_backup_doctor_and_rollback()
    test_symlink_replaces_directory_instead_of_nesting()
    test_doctor_reports_discoverable_duplicate()
    test_backup_root_inside_discovery_is_rejected()
    test_source_tree_symlink_is_rejected()
    test_source_path_rejects_symlink_before_parsing_entrypoint()
    test_per_skill_backup_symlink_is_rejected()
    test_operation_lock_rejects_concurrent_mutation()
    test_operation_lock_symlink_is_rejected()
    test_doctor_handles_invalid_utf8()
    print("install_skill.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
