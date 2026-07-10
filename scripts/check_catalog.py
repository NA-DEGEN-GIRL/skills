#!/usr/bin/env python3
"""Validate the package catalog, exact layout, versions, and root registration."""
from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CATALOG = SKILLS / "catalog.json"
ALLOWED_TARGETS = {"codex", "claude"}
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
ROOT_DOCS = [
    ROOT / "README.md",
    ROOT / "INSTALL.md",
    ROOT / "USER_GUIDE.md",
    ROOT / "LLM_CONTEXT.md",
    ROOT / "AGENTS.md",
    SKILLS / "README.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_catalog() -> dict[str, Any]:
    return json.loads(read(CATALOG))


def frontmatter_name(text: str) -> str:
    match = re.search(r"^name:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", text, flags=re.M)
    return match.group(1) if match else ""


def check(condition: bool, message: str) -> bool:
    print(("OK " if condition else "FAIL ") + message)
    return not condition


def main() -> int:
    failed = False
    try:
        catalog = load_catalog()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL cannot load {CATALOG.relative_to(ROOT)}: {exc}")
        return 1

    failed |= check(catalog.get("schema_version") == 1, "catalog schema_version is 1")
    packages = catalog.get("packages")
    if not isinstance(packages, list):
        print("FAIL catalog packages must be a list")
        return 1

    root_version = read(ROOT / "VERSION").strip()
    failed |= check(bool(VERSION_RE.fullmatch(root_version)), f"root VERSION format {root_version}")

    discovered = sorted(SKILLS.rglob("SKILL.md"))
    bad_layout = [path for path in discovered if len(path.relative_to(SKILLS).parts) != 3]
    failed |= check(not bad_layout, "all SKILL.md files use skills/<family>/<name>/SKILL.md")
    if bad_layout:
        for path in bad_layout:
            print(f"  BAD LAYOUT {path.relative_to(ROOT)}")

    names: list[str] = []
    sources: list[str] = []
    per_target_destinations: set[tuple[str, str]] = set()
    allowed_keys = {"name", "family", "source", "targets"}
    for index, package in enumerate(packages):
        if not isinstance(package, dict):
            failed |= check(False, f"catalog package #{index} is an object")
            continue
        unknown_keys = set(package) - allowed_keys
        failed |= check(not unknown_keys, f"{package.get('name', index)} catalog keys are supported")
        name = str(package.get("name", ""))
        family = str(package.get("family", ""))
        source_rel = str(package.get("source", ""))
        targets = package.get("targets", [])
        names.append(name)
        sources.append(source_rel)

        failed |= check(bool(NAME_RE.fullmatch(name)), f"catalog name {name!r}")
        failed |= check(isinstance(targets, list) and bool(targets), f"{name} has targets")
        failed |= check(set(targets).issubset(ALLOWED_TARGETS), f"{name} targets are known")
        failed |= check(len(targets) == len(set(targets)), f"{name} targets are unique")
        for target in targets:
            key = (str(target), name)
            failed |= check(key not in per_target_destinations, f"{name} destination unique for {target}")
            per_target_destinations.add(key)

        source = ROOT / source_rel
        expected_source = ROOT / "skills" / family / name
        failed |= check(source == expected_source, f"{name} source matches family/name")
        required = [source / "SKILL.md", source / "VERSION", source / "agents" / "openai.yaml"]
        for path in required:
            failed |= check(path.is_file(), f"exists {path.relative_to(ROOT)}")
        if not all(path.is_file() for path in required):
            continue
        skill = read(source / "SKILL.md")
        failed |= check(frontmatter_name(skill) == name, f"{name} frontmatter matches catalog")
        failed |= check(read(source / "VERSION").strip() == root_version, f"{name} VERSION matches root")
        failed |= check(f"**Skill Version:** {root_version}" in skill, f"{name} body version matches root")
        openai = read(source / "agents" / "openai.yaml")
        failed |= check(f"${name}" in openai, f"{name} default prompt names the package")

    failed |= check(len(names) == len(set(names)), "catalog package names are unique")
    failed |= check(len(sources) == len(set(sources)), "catalog source paths are unique")
    discovered_rel = {str(path.parent.relative_to(ROOT)) for path in discovered}
    failed |= check(set(sources) == discovered_rel, "catalog and discovered SKILL.md package sets match")
    if set(sources) != discovered_rel:
        for value in sorted(set(sources) - discovered_rel):
            print(f"  CATALOG ONLY {value}")
        for value in sorted(discovered_rel - set(sources)):
            print(f"  DISCOVERED ONLY {value}")

    for doc in ROOT_DOCS:
        if not doc.is_file():
            failed |= check(False, f"exists {doc.relative_to(ROOT)}")
            continue
        text = read(doc)
        missing = [name for name in names if name not in text]
        failed |= check(not missing, f"all catalog names registered in {doc.relative_to(ROOT)}")
        if missing:
            print(f"  MISSING {missing}")

    backup_dirs = [path for path in SKILLS.rglob("*") if path.is_dir() and ".bak." in path.name]
    failed |= check(not backup_dirs, "repository skills tree contains no discoverable backup directories")

    unsafe_entries: list[Path] = []
    generated_entries: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(SKILLS, followlinks=False):
        base = Path(dirpath)
        for name in [*dirnames, *filenames]:
            entry = base / name
            try:
                info = entry.lstat()
            except OSError:
                unsafe_entries.append(entry)
                continue
            if stat.S_ISLNK(info.st_mode) or (
                name in filenames and not stat.S_ISREG(info.st_mode)
            ):
                unsafe_entries.append(entry)
            if name == "__pycache__" or name.endswith((".pyc", ".pyo")):
                generated_entries.append(entry)
    failed |= check(not unsafe_entries, "repository skills tree contains only real directories and regular files")
    for entry in unsafe_entries:
        print(f"  UNSAFE ENTRY {entry.relative_to(ROOT)}")
    failed |= check(not generated_entries, "repository skills tree contains no Python cache artifacts")
    for entry in generated_entries:
        print(f"  GENERATED {entry.relative_to(ROOT)}")

    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    failed |= check(workflow.is_file(), "quality-gate CI workflow exists")
    if workflow.is_file():
        workflow_text = read(workflow)
        action_refs = re.findall(r"uses:\s*[^@\s]+@([^\s#]+)", workflow_text)
        failed |= check(bool(action_refs), "CI declares action references")
        failed |= check(all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in action_refs), "CI actions are pinned to full commit SHAs")
        failed |= check("contents: read" in workflow_text, "CI uses read-only contents permission")
        failed |= check("runs-on: ubuntu-24.04" in workflow_text and "ubuntu-latest" not in workflow_text, "CI runner image is pinned")
        failed |= check('python-version: ["3.10", "3.14"]' in workflow_text, "CI tests minimum and current Python lines")
        failed |= check('node-version: ["20", "22", "24"]' in workflow_text, "CI tests declared and current Node lines")
        failed |= check(
            "actions/setup-node@48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e" in workflow_text,
            "CI pins setup-node v6.4.0",
        )
        failed |= check("apt-get install --yes --no-install-recommends tmux" in workflow_text, "CI installs the MCP tmux prerequisite")
        required_make_runs = {
            "run: make check-skills",
            "run: make setup-mcps",
            "run: make check-mcps",
        }
        workflow_lines = {line.strip() for line in workflow_text.splitlines()}
        failed |= check(
            required_make_runs.issubset(workflow_lines),
            "CI runs the separated skill check and MCP setup/check targets",
        )

    makefile = ROOT / "Makefile"
    failed |= check(makefile.is_file(), "canonical Makefile exists")
    if makefile.is_file():
        makefile_text = read(makefile)
        failed |= check(bool(re.search(r"^all:\s+check\s*$", makefile_text, flags=re.M)), "make all aliases the canonical check gate")
        failed |= check(
            bool(re.search(r"^check:\s+check-skills\s+check-mcps\s*$", makefile_text, flags=re.M)),
            "canonical check aggregates skill and MCP gates",
        )
        failed |= check("ci --ignore-scripts" in makefile_text, "MCP setup uses locked npm ci without lifecycle scripts")
        failed |= check(
            bool(re.search(r"^check-mcps:\s*$", makefile_text, flags=re.M)),
            "MCP check does not depend on mutating setup",
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
