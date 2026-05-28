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
            "apply_marker_block.py",
        ]
        missing = [item for item in expected if item not in skill]
        if missing:
            print(f"SKILL LITERAL MISSING in {package.name}: {missing}")
            failed = True
        else:
            print(f"OK {package.name} SKILL literals")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
