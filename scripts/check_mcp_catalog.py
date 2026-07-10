#!/usr/bin/env python3
"""Validate the repository-owned MCP server catalog and Node manifests."""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_KEYS = {"schema_version", "servers"}
SERVER_KEYS = {"name", "source", "runtime", "transport"}
ALLOWED_RUNTIMES = {"node"}
ALLOWED_TRANSPORTS = {"stdio"}
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def check(condition: bool, message: str) -> bool:
    print(("OK " if condition else "FAIL ") + message)
    return not condition


def is_real_file(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False


def is_real_dir(path: Path) -> bool:
    try:
        return stat.S_ISDIR(path.lstat().st_mode)
    except OSError:
        return False


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_package_path(value: Any) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    if "\\" in value:
        return None
    while value.startswith("./"):
        value = value[2:]
    if not value:
        return None
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    return candidate


def contained_real_file(source: Path, relative: PurePosixPath) -> bool:
    current = source
    for part in relative.parts[:-1]:
        current = current / part
        if not is_real_dir(current):
            return False
    candidate = source.joinpath(*relative.parts)
    if not is_real_file(candidate):
        return False
    try:
        candidate.resolve(strict=True).relative_to(source.resolve(strict=True))
    except (OSError, ValueError):
        return False
    return True


def forbidden_package_entries(source: Path) -> list[Path]:
    """Find generated or potentially sensitive paths that must not ship."""
    forbidden: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
        base = Path(dirpath)
        for name in list(dirnames):
            lowered = name.lower()
            is_env = lowered == ".env" or lowered.startswith(".env.")
            if name == "node_modules" or (
                is_env and not lowered.endswith(".example")
            ) or lowered.endswith(".log"):
                forbidden.append(base / name)
                dirnames.remove(name)
        for name in filenames:
            lowered = name.lower()
            is_env = lowered == ".env" or lowered.startswith(".env.")
            if (is_env and not lowered.endswith(".example")) or lowered.endswith(".log"):
                forbidden.append(base / name)
    return sorted(forbidden)


def validate_node_manifest(source: Path, name: str) -> bool:
    failed = False
    manifest_path = source / "package.json"
    lock_path = source / "package-lock.json"
    readme_path = source / "README.md"

    failed |= check(is_real_file(manifest_path), f"{name} has a real package.json")
    failed |= check(is_real_file(lock_path), f"{name} has a real package-lock.json")
    failed |= check(is_real_file(readme_path), f"{name} has a real README.md")
    if not is_real_file(manifest_path):
        return failed

    try:
        manifest = load_json(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL cannot load {manifest_path}: {exc}")
        return True
    if not isinstance(manifest, dict):
        failed |= check(False, f"{name} package.json is an object")
        return failed

    package_name = manifest.get("name")
    version = manifest.get("version")
    engines = manifest.get("engines")
    scripts = manifest.get("scripts")
    failed |= check(package_name == name, f"{name} package name matches catalog")
    failed |= check(
        isinstance(version, str) and bool(SEMVER_RE.fullmatch(version)),
        f"{name} package version is SemVer",
    )
    failed |= check(
        isinstance(engines, dict)
        and isinstance(engines.get("node"), str)
        and bool(engines["node"].strip()),
        f"{name} declares a Node engine",
    )
    failed |= check(
        isinstance(scripts, dict)
        and isinstance(scripts.get("test"), str)
        and bool(scripts["test"].strip()),
        f"{name} declares a test script",
    )

    raw_bin = manifest.get("bin")
    if isinstance(raw_bin, str):
        raw_entrypoint: Any = raw_bin
    elif isinstance(raw_bin, dict):
        raw_entrypoint = raw_bin.get(name)
    else:
        raw_entrypoint = None
    entrypoint = safe_package_path(raw_entrypoint)
    failed |= check(entrypoint is not None, f"{name} has a safe named bin entry")
    if entrypoint is not None:
        failed |= check(
            contained_real_file(source, entrypoint),
            f"{name} bin entrypoint is a real in-package file",
        )

    if not is_real_file(lock_path):
        return failed
    try:
        lock = load_json(lock_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL cannot load {lock_path}: {exc}")
        return True
    if not isinstance(lock, dict):
        failed |= check(False, f"{name} package-lock.json is an object")
        return failed
    lockfile_version = lock.get("lockfileVersion")
    failed |= check(lock.get("name") == name, f"{name} lockfile name matches catalog")
    failed |= check(lock.get("version") == version, f"{name} lockfile version matches package")
    failed |= check(
        isinstance(lockfile_version, int)
        and not isinstance(lockfile_version, bool)
        and lockfile_version >= 2,
        f"{name} lockfile version is supported",
    )
    return failed


def discover_sources(mcp_root: Path) -> set[str]:
    discovered: set[str] = set()
    try:
        children = list(mcp_root.iterdir())
    except OSError:
        return discovered
    for child in children:
        if child.name.startswith(".") or child.name == "__pycache__":
            continue
        try:
            mode = child.lstat().st_mode
        except OSError:
            continue
        if stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
            discovered.add(f"mcp-servers/{child.name}")
    return discovered


def validate(root: Path, catalog_path: Path) -> int:
    failed = False
    mcp_root = root / "mcp-servers"
    failed |= check(is_real_dir(mcp_root), "mcp-servers is a real directory")
    if not is_real_dir(mcp_root):
        return 1
    failed |= check(is_real_file(catalog_path), "MCP catalog is a real file")
    if not is_real_file(catalog_path):
        return 1

    try:
        catalog = load_json(catalog_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL cannot load {catalog_path}: {exc}")
        return 1
    if not isinstance(catalog, dict):
        print("FAIL MCP catalog must be an object")
        return 1

    failed |= check(set(catalog) == CATALOG_KEYS, "MCP catalog keys are exact")
    schema_version = catalog.get("schema_version")
    failed |= check(
        isinstance(schema_version, int)
        and not isinstance(schema_version, bool)
        and schema_version == 1,
        "MCP catalog schema_version is 1",
    )
    servers = catalog.get("servers")
    if not isinstance(servers, list):
        print("FAIL MCP catalog servers must be a list")
        return 1

    names: list[str] = []
    sources: list[str] = []
    valid_entries: list[tuple[str, str, str]] = []
    for index, server in enumerate(servers):
        if not isinstance(server, dict):
            failed |= check(False, f"MCP server #{index} is an object")
            continue
        label = server.get("name", index)
        failed |= check(set(server) == SERVER_KEYS, f"{label} catalog keys are exact")
        name = server.get("name")
        source_rel = server.get("source")
        runtime = server.get("runtime")
        transport = server.get("transport")

        name_valid = isinstance(name, str) and bool(NAME_RE.fullmatch(name))
        source_valid = isinstance(source_rel, str) and name_valid and source_rel == f"mcp-servers/{name}"
        runtime_valid = isinstance(runtime, str) and runtime in ALLOWED_RUNTIMES
        transport_valid = isinstance(transport, str) and transport in ALLOWED_TRANSPORTS
        failed |= check(name_valid, f"MCP name {name!r}")
        failed |= check(source_valid, f"{name!r} source matches mcp-servers/<name>")
        failed |= check(runtime_valid, f"{name!r} runtime is supported")
        failed |= check(transport_valid, f"{name!r} transport is supported")

        if isinstance(name, str):
            names.append(name)
        if isinstance(source_rel, str):
            sources.append(source_rel)
        if name_valid and source_valid and runtime_valid and transport_valid:
            valid_entries.append((name, source_rel, runtime))

    failed |= check(len(names) == len(set(names)), "MCP catalog names are unique")
    failed |= check(len(sources) == len(set(sources)), "MCP catalog sources are unique")

    discovered = discover_sources(mcp_root)
    catalog_sources = set(sources)
    failed |= check(catalog_sources == discovered, "MCP catalog and package directories match")
    if catalog_sources != discovered:
        for value in sorted(catalog_sources - discovered):
            print(f"  CATALOG ONLY {value}")
        for value in sorted(discovered - catalog_sources):
            print(f"  DISCOVERED ONLY {value}")

    validated: set[str] = set()
    for name, source_rel, runtime in valid_entries:
        if source_rel in validated:
            continue
        validated.add(source_rel)
        source = root / source_rel
        failed |= check(is_real_dir(source), f"{name} source is a real directory")
        if not is_real_dir(source):
            continue
        try:
            contained = source.resolve(strict=True).parent == mcp_root.resolve(strict=True)
        except OSError:
            contained = False
        failed |= check(contained, f"{name} source is contained directly in mcp-servers")
        if not contained:
            continue
        forbidden = forbidden_package_entries(source)
        failed |= check(
            not forbidden,
            f"{name} contains no node_modules, private env files, or logs",
        )
        for path in forbidden:
            print(f"  FORBIDDEN {source_rel}/{path.relative_to(source)}")
        if runtime == "node":
            failed |= validate_node_manifest(source, name)

    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--catalog", type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=False)
    catalog = args.catalog or root / "mcp-servers" / "catalog.json"
    return validate(root, catalog)


if __name__ == "__main__":
    raise SystemExit(main())
