#!/usr/bin/env python3
"""Smoke tests for the MCP catalog validator using isolated repositories."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).with_name("check_mcp_catalog.py")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_catalog(root: Path, servers: list[Any]) -> None:
    write_json(
        root / "mcp-servers" / "catalog.json",
        {"schema_version": 1, "servers": servers},
    )


def catalog_entry(name: str = "demo-mcp") -> dict[str, str]:
    return {
        "name": name,
        "source": f"mcp-servers/{name}",
        "runtime": "node",
        "transport": "stdio",
    }


def write_node_server(root: Path, name: str = "demo-mcp") -> Path:
    source = root / "mcp-servers" / name
    (source / "bin").mkdir(parents=True)
    (source / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    (source / "bin" / "server.js").write_text("#!/usr/bin/env node\n", encoding="utf-8")
    write_json(
        source / "package.json",
        {
            "name": name,
            "version": "0.1.0",
            "bin": {name: "./bin/server.js"},
            "scripts": {"test": "node --test"},
            "engines": {"node": ">=20"},
        },
    )
    write_json(
        source / "package-lock.json",
        {
            "name": name,
            "version": "0.1.0",
            "lockfileVersion": 3,
            "requires": True,
            "packages": {},
        },
    )
    return source


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def expect(result: subprocess.CompletedProcess[str], code: int, message: str) -> None:
    if result.returncode != code:
        raise AssertionError(
            f"{message}: expected {code}, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    if "Traceback" in result.stderr:
        raise AssertionError(f"{message}: validator crashed\n{result.stderr}")


def test_empty_catalog() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        write_catalog(root, [])
        expect(run(root), 0, "empty truthful catalog")


def test_valid_node_package() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        write_node_server(root)
        write_catalog(root, [catalog_entry()])
        expect(run(root), 0, "valid Node MCP package")


def test_malformed_catalog_fails_cleanly() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        write_json(
            root / "mcp-servers" / "catalog.json",
            {"schema_version": 1, "servers": [{"name": ["not-a-string"]}]},
        )
        expect(run(root), 1, "malformed catalog")


def test_duplicate_and_uncataloged_sources_fail() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        write_node_server(root)
        entry = catalog_entry()
        write_catalog(root, [entry, dict(entry)])
        result = run(root)
        expect(result, 1, "duplicate catalog entries")
        if "names are unique" not in result.stdout:
            raise AssertionError("duplicate name was not identified")

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        write_node_server(root)
        write_catalog(root, [])
        result = run(root)
        expect(result, 1, "uncataloged source")
        if "DISCOVERED ONLY mcp-servers/demo-mcp" not in result.stdout:
            raise AssertionError("uncataloged package directory was not identified")


def test_source_and_entrypoint_escape_are_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        write_catalog(
            root,
            [
                {
                    "name": "demo-mcp",
                    "source": "../outside",
                    "runtime": "node",
                    "transport": "stdio",
                }
            ],
        )
        expect(run(root), 1, "catalog source traversal")

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        source = write_node_server(root)
        write_catalog(root, [catalog_entry()])
        manifest = json.loads((source / "package.json").read_text(encoding="utf-8"))
        manifest["bin"] = {"demo-mcp": "../outside.js"}
        write_json(source / "package.json", manifest)
        (root / "mcp-servers" / "outside.js").write_text("outside\n", encoding="utf-8")
        result = run(root)
        expect(result, 1, "bin entrypoint traversal")
        if "safe named bin entry" not in result.stdout:
            raise AssertionError("unsafe bin entrypoint was not identified")


def test_symlinked_entrypoint_is_rejected() -> None:
    if not hasattr(os, "symlink"):
        return
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        source = write_node_server(root)
        write_catalog(root, [catalog_entry()])
        entrypoint = source / "bin" / "server.js"
        entrypoint.unlink()
        outside = root / "outside.js"
        outside.write_text("outside\n", encoding="utf-8")
        try:
            entrypoint.symlink_to(outside)
        except OSError:
            return
        result = run(root)
        expect(result, 1, "symlinked bin entrypoint")
        if "real in-package file" not in result.stdout:
            raise AssertionError("symlinked entrypoint was not identified")


def test_manifest_and_lock_mismatch_are_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        source = write_node_server(root)
        write_catalog(root, [catalog_entry()])
        manifest = json.loads((source / "package.json").read_text(encoding="utf-8"))
        manifest["name"] = "wrong-name"
        manifest["version"] = "not-semver"
        write_json(source / "package.json", manifest)
        result = run(root)
        expect(result, 1, "manifest mismatch")
        if "package name matches catalog" not in result.stdout:
            raise AssertionError("package name mismatch was not identified")
        if "package version is SemVer" not in result.stdout:
            raise AssertionError("bad package version was not identified")


def test_generated_and_sensitive_package_paths_are_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        source = write_node_server(root)
        write_catalog(root, [catalog_entry()])
        (source / "node_modules").mkdir()
        (source / ".env").write_text("SECRET=value\n", encoding="utf-8")
        (source / ".env.local").write_text("SECRET=value\n", encoding="utf-8")
        (source / "debug.log").write_text("private output\n", encoding="utf-8")
        (source / ".env.example").write_text("SECRET=placeholder\n", encoding="utf-8")
        result = run(root)
        expect(result, 1, "generated and sensitive package paths")
        for expected in ("node_modules", ".env", ".env.local", "debug.log"):
            if f"FORBIDDEN mcp-servers/demo-mcp/{expected}" not in result.stdout:
                raise AssertionError(f"forbidden path was not identified: {expected}")
        if "FORBIDDEN mcp-servers/demo-mcp/.env.example" in result.stdout:
            raise AssertionError("explicit .env.example template was rejected")

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        source = write_node_server(root)
        write_catalog(root, [catalog_entry()])
        (source / ".env.example").write_text("SECRET=placeholder\n", encoding="utf-8")
        expect(run(root), 0, "explicit env example template")


def main() -> int:
    test_empty_catalog()
    test_valid_node_package()
    test_malformed_catalog_fails_cleanly()
    test_duplicate_and_uncataloged_sources_fail()
    test_source_and_entrypoint_escape_are_rejected()
    test_symlinked_entrypoint_is_rejected()
    test_manifest_and_lock_mismatch_are_rejected()
    test_generated_and_sensitive_package_paths_are_rejected()
    print("check_mcp_catalog.py smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
