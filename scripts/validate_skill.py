#!/usr/bin/env python3
"""Portable minimal validator for local Codex/Claude skill packages.

This is intentionally dependency-free. It does not replace official agent-side
validators, but it catches the schema issues this repository cares about when a
Codex-local skill-creator validator is unavailable.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
REQUIRED_KEYS = ("name", "description")


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, ["SKILL.md must start with YAML frontmatter delimiter `---`"]
    end = text.find("\n---", 4)
    if end == -1:
        return {}, ["SKILL.md is missing closing frontmatter delimiter `---`"]
    raw = text[4:end]
    data: dict[str, str] = {}
    for lineno, line in enumerate(raw.splitlines(), start=2):
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"frontmatter line {lineno} is not key: value")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in data:
            errors.append(f"duplicate frontmatter key `{key}`")
        data[key] = value
    return data, errors


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        return [f"{path}: missing SKILL.md"]
    text = skill_md.read_text(encoding="utf-8")
    data, parse_errors = parse_frontmatter(text)
    errors.extend(parse_errors)
    for key in REQUIRED_KEYS:
        if not data.get(key):
            errors.append(f"missing required frontmatter key `{key}`")
    name = data.get("name", "")
    if name and not NAME_RE.match(name):
        errors.append(f"invalid skill name `{name}`; use lowercase letters, digits, and hyphens, max 64 chars")
    if name and path.name != name:
        errors.append(f"folder name `{path.name}` must match frontmatter name `{name}`")
    desc = data.get("description", "")
    if desc and len(desc) < 40:
        errors.append("description is too short to be useful")
    if "[TODO" in text or "TODO:" in text:
        errors.append("SKILL.md contains TODO placeholder text")
    if "name" in data and "description" in data and set(data) - set(REQUIRED_KEYS):
        errors.append(f"unexpected frontmatter keys: {sorted(set(data) - set(REQUIRED_KEYS))}")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: validate_skill.py <skill-dir> [<skill-dir> ...]", file=sys.stderr)
        return 2
    failed = False
    for raw in argv[1:]:
        path = Path(raw)
        errors = validate_skill(path)
        if errors:
            failed = True
            print(f"INVALID {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"Skill is valid: {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
