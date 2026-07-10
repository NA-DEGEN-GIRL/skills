#!/usr/bin/env python3
"""Focused regression tests for repository-local Markdown discovery."""
from __future__ import annotations

import contextlib
import io
import tempfile
from pathlib import Path

import check_markdown_links as checker


def run_quietly() -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return checker.main()


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        checker.ROOT = root
        (root / "README.md").write_text("[valid](target.md)\n", encoding="utf-8")
        (root / "target.md").write_text("# Target\n", encoding="utf-8")

        dependency = root / "mcp-servers" / "demo" / "node_modules" / "dependency"
        dependency.mkdir(parents=True)
        (dependency / "README.md").write_text(
            "[package-only link](missing-from-install.md)\n",
            encoding="utf-8",
        )
        if run_quietly() != 0:
            raise AssertionError("ignored node_modules Markdown affected repository links")

        (root / "BROKEN.md").write_text("[missing](missing.md)\n", encoding="utf-8")
        if run_quietly() != 1:
            raise AssertionError("ordinary repository Markdown was not checked")

    print("check_markdown_links.py discovery tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
