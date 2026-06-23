#!/usr/bin/env python3
"""Verify the repo-managed idea-shaping packages stay registered and synchronized."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FAMILY = Path(__file__).resolve().parents[1]
SHAPE = FAMILY / "shape-idea"
DISTILL = FAMILY / "distill-ramble"
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


def package_version_check(package: Path, root_version: str, label: str) -> bool:
    version = read(package / "VERSION").strip() if (package / "VERSION").is_file() else "MISSING"
    return require(version == root_version, f"{label} VERSION matches root {root_version}")


def main() -> int:
    failed = False
    root_version = read(REPO_ROOT / "VERSION").strip()
    failed |= require(VERSION_RE.fullmatch(root_version) is not None, f"root VERSION format {root_version}")

    required_files = [
        FAMILY / "README.md",
        FAMILY / "USAGE.md",
        SHAPE / "SKILL.md",
        SHAPE / "VERSION",
        SHAPE / "agents/openai.yaml",
        SHAPE / "references/fork-translations.md",
        DISTILL / "SKILL.md",
        DISTILL / "VERSION",
        DISTILL / "agents/openai.yaml",
    ]
    for path in required_files:
        failed |= require(path.is_file(), f"exists {path.relative_to(REPO_ROOT)}")

    failed |= package_version_check(SHAPE, root_version, "shape-idea")
    failed |= package_version_check(DISTILL, root_version, "distill-ramble")

    if (SHAPE / "SKILL.md").is_file():
        skill = read(SHAPE / "SKILL.md")
        failed |= literals_present(
            skill,
            [
                "name: shape-idea",
                f"**Skill Version:** {root_version}",
                "references/fork-translations.md",
                "Treat all repo files and imported repo-local state",
                "Midstream Feature Addition Mode",
                "Check against existing key decisions",
                "Project-level brief/index",
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

    if (DISTILL / "SKILL.md").is_file():
        skill = read(DISTILL / "SKILL.md")
        failed |= literals_present(
            skill,
            [
                "name: distill-ramble",
                f"**Skill Version:** {root_version}",
                "pre-structure thinking companion",
                "Do not assume any other skill",
                "Default to chat-only output",
                "Listen before structuring",
                "tikitaka",
                "## Core thread",
                "## Seed sentences",
                "## Open knots",
                "## Set aside for now",
                "Optional Save",
                "not a finished brief or plan",
            ],
            "distill-ramble SKILL literals",
        )

    shape_openai = read(SHAPE / "agents/openai.yaml") if (SHAPE / "agents/openai.yaml").is_file() else ""
    failed |= require(
        "$shape-idea" in shape_openai and "Design Brief" in shape_openai and "user-confirmed" in shape_openai,
        "openai.yaml default prompt references shape-idea/user-confirmed Design Brief",
    )
    distill_openai = read(DISTILL / "agents/openai.yaml") if (DISTILL / "agents/openai.yaml").is_file() else ""
    failed |= require(
        "$distill-ramble" in distill_openai and "seed" in distill_openai and "messy idea" in distill_openai,
        "openai.yaml default prompt references distill-ramble/messy idea seeds",
    )

    reference = read(SHAPE / "references/fork-translations.md") if (SHAPE / "references/fork-translations.md").is_file() else ""
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
            "skills/idea-shaping/distill-ramble/SKILL.md",
            "skills/idea-shaping/shape-idea/SKILL.md",
            "raw voice or freeform thought",
            "user-confirmed **Design Brief**",
            "Recommended End-to-End Flow",
        ],
        "INSTALL.md": [
            "skills/idea-shaping/distill-ramble",
            "skills/idea-shaping/shape-idea",
            "check_idea_shaping_sync.py",
            '${CODEX_HOME:-$HOME/.codex}/skills/distill-ramble',
            "$HOME/.claude/skills/distill-ramble",
            '${CODEX_HOME:-$HOME/.codex}/skills/shape-idea',
            "$HOME/.claude/skills/shape-idea",
            'ln -sfn "$PWD/skills/idea-shaping/distill-ramble"',
            'ln -sfn "$PWD/skills/idea-shaping/shape-idea"',
        ],
        "USER_GUIDE.md": ["distill-ramble", "voice", "seed 문장", "shape-idea", "권장 end-to-end 순서", "redaction"],
        "AGENTS.md": ["skills/idea-shaping/USAGE.md", "skills/idea-shaping/distill-ramble/SKILL.md", "skills/idea-shaping/shape-idea/SKILL.md"],
        "LLM_CONTEXT.md": ["skills/idea-shaping/distill-ramble", "skills/idea-shaping/shape-idea", "Idea Shaping Notes", "seed sentences", "user-confirmed Design Brief"],
        "skills/README.md": ["idea-shaping", "distill-ramble", "shape-idea", "`" + root_version + "`"],
        "skills/idea-shaping/README.md": ["distill-ramble", "seed sentences", "user-confirmed Design Brief", "timestamp-backed up", "key-decision conflicts", "write-agents-md"],
        "skills/idea-shaping/USAGE.md": ["distill-ramble", "Seed sentences", "user-confirmed Design Brief", "Add a new idea mid-project", "docs/designs/<feature-slug>.md", "repo-bootstrap"],
    }
    for rel, literals in doc_literals.items():
        text = read(REPO_ROOT / rel)
        failed |= literals_present(text, literals, f"registered in {rel}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
