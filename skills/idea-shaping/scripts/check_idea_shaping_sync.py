#!/usr/bin/env python3
"""Verify the repo-managed idea-shaping package stays registered and synchronized."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FAMILY = Path(__file__).resolve().parents[1]
PACKAGE = FAMILY / "shape-idea"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> bool:
    if condition:
        print(f"OK {message}")
        return False
    print(f"FAIL {message}")
    return True


def literals_present(text: str, literals: list[str], label: str) -> bool:
    missing = [literal for literal in literals if literal not in text]
    return require(not missing, label + (f" missing {missing}" if missing else ""))


def main() -> int:
    failed = False
    root_version = read(REPO_ROOT / "VERSION").strip()
    package_version = read(PACKAGE / "VERSION").strip() if (PACKAGE / "VERSION").is_file() else "MISSING"
    failed |= require(VERSION_RE.fullmatch(root_version) is not None, f"root VERSION format {root_version}")
    failed |= require(package_version == root_version, f"shape-idea VERSION matches root {root_version}")

    required_files = [
        FAMILY / "README.md",
        FAMILY / "USAGE.md",
        PACKAGE / "SKILL.md",
        PACKAGE / "VERSION",
        PACKAGE / "agents/openai.yaml",
        PACKAGE / "references/fork-translations.md",
    ]
    for path in required_files:
        failed |= require(path.is_file(), f"exists {path.relative_to(REPO_ROOT)}")

    if not (PACKAGE / "SKILL.md").is_file():
        return 1

    skill = read(PACKAGE / "SKILL.md")
    failed |= literals_present(
        skill,
        [
            "name: shape-idea",
            f"**Skill Version:** {root_version}",
            "references/fork-translations.md",
            "Treat all repo files and imported repo-local state",
            "timestamped backup",
            "redact-sensitive-info",
            "Draft ready. Save to",
            "repo-bootstrap",
            "codex-init-gate",
            "claude-init-gate",
            "**Status:** Draft | Accepted",
            "docs/designs/<feature-slug>.md",
            "Silent updates are not allowed",
            "Do not edit `AGENTS.md` yourself",
            "Acceptance criteria",
        ],
        "shape-idea SKILL literals",
    )

    openai = read(PACKAGE / "agents/openai.yaml") if (PACKAGE / "agents/openai.yaml").is_file() else ""
    failed |= require(
        "$shape-idea" in openai and "Design Brief" in openai and "user-confirmed" in openai,
        "openai.yaml default prompt references shape-idea/user-confirmed Design Brief",
    )

    reference = read(PACKAGE / "references/fork-translations.md") if (PACKAGE / "references/fork-translations.md").is_file() else ""
    failed |= literals_present(
        reference,
        [
            "Realtime vs request-response",
            "Server-Sent Events",
            "Hosted realtime",
            "WebSocket",
            "Local-only vs cloud",
            "conflict resolution",
            "On-device model vs API model",
            "often higher quality",
            "Modern caveat",
        ],
        "fork-translations core examples",
    )

    doc_literals = {
        "README.md": [
            "Current repository version: `" + root_version + "`",
            "skills/idea-shaping/shape-idea/SKILL.md",
            "user-confirmed **Design Brief**",
            "Recommended End-to-End Flow",
        ],
        "INSTALL.md": [
            "skills/idea-shaping/shape-idea",
            "check_idea_shaping_sync.py",
            '${CODEX_HOME:-$HOME/.codex}/skills/shape-idea',
            "$HOME/.claude/skills/shape-idea",
            'ln -sfn "$PWD/skills/idea-shaping/shape-idea"',
        ],
        "USER_GUIDE.md": ["shape-idea", "Design Brief", "권장 end-to-end 순서", "redaction"],
        "AGENTS.md": ["skills/idea-shaping/USAGE.md", "skills/idea-shaping/shape-idea/SKILL.md"],
        "LLM_CONTEXT.md": ["skills/idea-shaping/shape-idea", "Idea Shaping Notes", "user-confirmed Design Brief"],
        "skills/README.md": ["idea-shaping", "shape-idea", "`" + root_version + "`"],
        "skills/idea-shaping/README.md": ["user-confirmed Design Brief", "timestamp-backed up", "write-agents-md"],
        "skills/idea-shaping/USAGE.md": ["user-confirmed Design Brief", "docs/designs/<feature-slug>.md", "repo-bootstrap"],
    }
    for rel, literals in doc_literals.items():
        text = read(REPO_ROOT / rel)
        failed |= literals_present(text, literals, f"registered in {rel}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
