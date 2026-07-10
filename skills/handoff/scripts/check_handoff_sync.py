#!/usr/bin/env python3
"""Verify local Codex/Claude handoff packages stay synchronized where intended."""
from __future__ import annotations

import hashlib
import re
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FAMILY_ROOT = Path(__file__).resolve().parents[1]
CODEX = FAMILY_ROOT / "codex-handoff"
CLAUDE = FAMILY_ROOT / "claude-handoff"
SCHEMA = "handoff-v1"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable_bit(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def read_version(path: Path) -> str:
    return (path / "VERSION").read_text(encoding="utf-8").strip()


def main() -> int:
    failed = False

    codex_version = read_version(CODEX)
    claude_version = read_version(CLAUDE)
    root_version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    versions = {"root": root_version, "codex": codex_version, "claude": claude_version}
    if len(set(versions.values())) != 1 or not VERSION_RE.match(root_version):
        print(f"VERSION MISMATCH/INVALID: {versions}")
        failed = True
    else:
        print(f"OK version: {root_version}")

    codex_scripts = {p.relative_to(CODEX / "scripts") for p in (CODEX / "scripts").glob("*.py")}
    claude_scripts = {p.relative_to(CLAUDE / "scripts") for p in (CLAUDE / "scripts").glob("*.py")}
    # Top-level helper scripts are intentionally outside the package pair.
    if codex_scripts != claude_scripts:
        print("SCRIPT SET MISMATCH")
        print(f"  codex-only : {sorted(str(p) for p in codex_scripts - claude_scripts)}")
        print(f"  claude-only: {sorted(str(p) for p in claude_scripts - codex_scripts)}")
        failed = True

    required_scripts = {
        Path("snapshot_common.py"),
        Path("validate_snapshot.py"),
        Path("list_lanes.py"),
        Path("select_snapshot.py"),
        Path("save_snapshot.py"),
        Path("prune_backups.py"),
        Path("apply_marker_block.py"),
        Path("handoff_snapshot.py"),
        Path("test_save_snapshot.py"),
        Path("test_select_snapshot.py"),
    }
    missing_scripts = required_scripts - (codex_scripts & claude_scripts)
    if missing_scripts:
        print(f"REQUIRED SCRIPT MISSING: {sorted(str(path) for path in missing_scripts)}")
        failed = True

    for rel in sorted(codex_scripts & claude_scripts):
        left = CODEX / "scripts" / rel
        right = CLAUDE / "scripts" / rel
        lhash, rhash = sha256(left), sha256(right)
        if lhash != rhash:
            print(f"MISMATCH scripts/{rel}")
            print(f"  codex : {lhash} {left}")
            print(f"  claude: {rhash} {right}")
            failed = True
        elif executable_bit(left) != executable_bit(right):
            print(f"MODE MISMATCH scripts/{rel}")
            failed = True
        else:
            print(f"OK scripts/{rel}: {lhash[:12]}")

    for package, agent in ((CODEX, "codex"), (CLAUDE, "claude")):
        skill = (package / "SKILL.md").read_text(encoding="utf-8")
        expected = [
            f"**Skill Version:** {root_version}",
            f"- Schema Version: {SCHEMA}",
            f"- Skill Version: {root_version}",
            f"- Skill Variant: {agent}-handoff",
            f"- Agent: {agent}",
            "validate_snapshot.py",
            "list_lanes.py",
            "select_snapshot.py",
            "save_snapshot.py",
            "prune_backups.py",
            "apply_marker_block.py",
        ]
        missing = [item for item in expected if item not in skill]
        if missing:
            print(f"SKILL LITERAL MISSING in {package.name}: {missing}")
            failed = True
        else:
            print(f"OK {package.name} SKILL literals")

        forbidden = ["There is no lock", "Read existing `.handoff/latest.md` if present"]
        present = [item for item in forbidden if item in skill]
        if present:
            print(f"STALE/UNSAFE SKILL LITERAL in {package.name}: {present}")
            failed = True

    family_docs = (FAMILY_ROOT / "README.md").read_text(encoding="utf-8") + (FAMILY_ROOT / "USAGE.md").read_text(encoding="utf-8")
    doc_missing = [name for name in ("save_snapshot.py", "select_snapshot.py", "backup-only", "orphan") if name not in family_docs]
    if doc_missing:
        print(f"FAMILY DOC LITERAL MISSING: {doc_missing}")
        failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
