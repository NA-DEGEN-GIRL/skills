#!/usr/bin/env python3
"""Check repository-local Markdown link targets without network access."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".handoff", ".vibe-ide-temp", "__pycache__", "node_modules"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\((<[^>]+>|[^)\s]+)(?:\s+['\"][^)]*['\"])?\)")


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts)
    )


def local_target(raw: str) -> str | None:
    value = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
    value = unquote(value)
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith(("#", "/", "$", "~")):
        return None
    return parsed.path or None


def main() -> int:
    failures: list[str] = []
    checked = 0
    for document in markdown_files():
        text = document.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = local_target(match.group(1))
            if target is None:
                continue
            checked += 1
            candidate = (document.parent / target).resolve(strict=False)
            try:
                candidate.relative_to(ROOT.resolve())
            except ValueError:
                failures.append(f"{document.relative_to(ROOT)} -> target escapes repo: {target}")
                continue
            if not candidate.exists():
                line = text.count("\n", 0, match.start()) + 1
                failures.append(f"{document.relative_to(ROOT)}:{line} -> missing {target}")

    if failures:
        print(f"FAIL Markdown links: {len(failures)} problem(s)")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"OK Markdown links: {checked} local target(s) across {len(markdown_files())} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
