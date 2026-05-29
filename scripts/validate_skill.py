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


OPENAI_STRING_RE = re.compile(r'^  (display_name|short_description|default_prompt): "([^"]+)"$')


def validate_openai_yaml(path: Path, skill_name: str) -> list[str]:
    errors: list[str] = []
    meta = path / "agents" / "openai.yaml"
    if not meta.exists():
        return errors
    lines = meta.read_text(encoding="utf-8").splitlines()
    content = [line for line in lines if line.strip() and not line.lstrip().startswith("#")]
    if not content:
        return ["agents/openai.yaml is empty"]
    if content[0] != "interface:":
        errors.append("agents/openai.yaml must use top-level `interface:`")
    found: dict[str, str] = {}
    for line in content[1:]:
        match = OPENAI_STRING_RE.match(line)
        if match:
            found[match.group(1)] = match.group(2)
        elif re.match(r"^[A-Za-z_]+:", line):
            errors.append("agents/openai.yaml interface fields must be nested under `interface:`")
        elif ":" in line and not line.startswith("  "):
            errors.append(f"agents/openai.yaml unexpected top-level line `{line}`")
        elif ":" in line and not re.search(r': "[^"]+"$', line):
            errors.append(f"agents/openai.yaml string values must be quoted: `{line}`")
    for key in ("display_name", "short_description", "default_prompt"):
        if key not in found:
            errors.append(f"agents/openai.yaml missing interface.{key}")
    short = found.get("short_description", "")
    if short and not (25 <= len(short) <= 64):
        errors.append("agents/openai.yaml interface.short_description must be 25-64 characters")
    prompt = found.get("default_prompt", "")
    if prompt and f"${skill_name}" not in prompt:
        errors.append(f"agents/openai.yaml interface.default_prompt must mention `${skill_name}`")
    return errors


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
    if name:
        errors.extend(validate_openai_yaml(path, name))
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
