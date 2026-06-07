#!/usr/bin/env python3
"""Verify the repo-managed orient-repo package stays internally synchronized."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parents[1] / "orient-repo"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    failed = False
    root_version = read(REPO_ROOT / "VERSION").strip()
    package_version = read(PACKAGE / "VERSION").strip()
    skill = read(PACKAGE / "SKILL.md")

    versions = {"root": root_version, "package": package_version}
    if len(set(versions.values())) != 1 or not VERSION_RE.match(root_version):
        print(f"VERSION MISMATCH/INVALID: {versions}")
        failed = True
    else:
        print(f"OK repo-orientation version: {root_version}")

    required_files = [
        PACKAGE / "agents/openai.yaml",
        PACKAGE / "references/orientation-checklist.md",
    ]
    for path in required_files:
        if not path.is_file():
            print(f"MISSING {path.relative_to(REPO_ROOT)}")
            failed = True
        else:
            print(f"OK exists {path.relative_to(REPO_ROOT)}")

    expected_literals = [
        f"**Skill Version:** {root_version}",
        "references/orientation-checklist.md",
        "actual repo/git state > validated",
        "if a handoff skill is available",
        "Repo Orientation",
        "Quality Gate",
        "repo-bootstrap / init-gate",
        "read-only",
    ]
    missing = [literal for literal in expected_literals if literal not in skill]
    if missing:
        print(f"SKILL LITERAL MISSING in {PACKAGE.name}: {missing}")
        failed = True
    else:
        print("OK orient-repo SKILL literals")

    checklist = read(PACKAGE / "references/orientation-checklist.md")
    checklist_literals = ["Quality Gate", "Canonical check path", "Unknowns To Surface"]
    missing_checklist = [literal for literal in checklist_literals if literal not in checklist]
    if missing_checklist:
        print(f"CHECKLIST LITERAL MISSING: {missing_checklist}")
        failed = True
    else:
        print("OK orientation-checklist literals")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
