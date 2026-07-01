#!/usr/bin/env python3
"""Emit a compact, safe Markdown repo-state fragment for handoff snapshots.

This script intentionally avoids raw diffs and file contents. It uses git metadata
when available and a bounded filesystem-only fallback for non-git directories.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_VERSION = "0.1.10"
SCHEMA_VERSION = "handoff-v1"

EXCLUDE_DIRS = {
    ".git",
    ".handoff",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".next",
    "dist",
    "build",
    ".ssh",
    ".aws",
    ".gnupg",
    ".kube",
    ".docker",
    "gcloud",
}
SENSITIVE_HINTS = (
    ".env",
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".ssh/",
    "anthropic_api",
    "api-key",
    "apikey",
    "api_key",
    "auth.json",
    "authorized_keys",
    "aws_access",
    "client_secret",
    "cookie",
    "credential",
    "credentials",
    "docker-config.json",
    "gcp-sa",
    "github_token",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
    "kubeconfig",
    "openai_api",
    "passwd",
    "password",
    "private",
    "private_key",
    "secret",
    "secrets",
    "service-account",
    "service_account",
    "slack_bot",
    "token",
    ".pem",
    ".p12",
    ".pfx",
)
SENSITIVE_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"sk-[A-Za-z0-9_-]{8,}",
        r"AKIA[0-9A-Z]{8,}",
        r"ASIA[0-9A-Z]{8,}",
        r"ghp_[A-Za-z0-9_]{8,}",
        r"github_pat_[A-Za-z0-9_]{8,}",
        r"xox[baprs]-[A-Za-z0-9-]{8,}",
        r"ya29\.[A-Za-z0-9_-]{8,}",
        r"(?:^|[/_.-])(?:access|refresh|id)?token(?:[/_.-]|$)",
        r"(?:^|[/_.-])(?:api|private|secret|access)[_-]?key(?:[/_.-]|$)",
    )
)


@dataclass
class CmdResult:
    code: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


def load_version() -> str:
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    try:
        value = version_file.read_text(encoding="utf-8").strip()
        return value or DEFAULT_VERSION
    except OSError:
        return DEFAULT_VERSION


def run(cmd: list[str], cwd: Path) -> CmdResult:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as exc:
        return CmdResult(127, stderr=str(exc))
    except subprocess.TimeoutExpired:
        return CmdResult(124, stderr="command timed out", timed_out=True)
    return CmdResult(p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip())


def git_root(start: Path) -> Path | None:
    result = run(["git", "rev-parse", "--show-toplevel"], start)
    return Path(result.stdout) if result.code == 0 and result.stdout else None


def git_cmd(root: Path, *args: str) -> CmdResult:
    return run(["git", *args], root)


def limit_output(text: str, line_limit: int, byte_limit: int) -> list[str]:
    truncated_bytes = False
    if byte_limit > 0:
        raw = text.encode("utf-8", "replace")
        if len(raw) > byte_limit:
            text = raw[:byte_limit].decode("utf-8", "ignore")
            truncated_bytes = True

    lines = [line.rstrip() for line in text.splitlines() if line.rstrip()]
    omitted_lines = 0
    if line_limit > 0 and len(lines) > line_limit:
        omitted_lines = len(lines) - line_limit
        lines = lines[:line_limit]

    if omitted_lines:
        lines.append(f"... ({omitted_lines} more lines omitted)")
    if truncated_bytes:
        lines.append(f"... (output truncated at {byte_limit} bytes)")
    return lines


def is_sensitive_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    lower = normalized.lower()
    return any(hint in lower for hint in SENSITIVE_HINTS) or any(p.search(normalized) for p in SENSITIVE_PATTERNS)


def redacted_path_label(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:12]
    return f"[SENSITIVE-PATH:{digest}]"


def code_span(value: str) -> str:
    return value.replace("`", "ˋ")


def display_path_like(value: str) -> tuple[str, bool]:
    if is_sensitive_path(value):
        return redacted_path_label(value), True
    return code_span(value), False


def print_block(title: str, lines: Iterable[str], empty: str = "none") -> None:
    print(f"### {title}")
    material = list(lines)
    if not material:
        print(f"- {empty}")
        return
    for line in material:
        if line.startswith("... ("):
            print(f"- {line}")
            continue
        shown, redacted = display_path_like(line)
        suffix = " [sensitive-looking path redacted; contents not inspected]" if redacted else ""
        print(f"- `{shown}`{suffix}")


def git_lines(root: Path, args: tuple[str, ...], line_limit: int, byte_limit: int) -> list[str]:
    result = git_cmd(root, *args)
    if result.code != 0:
        return [f"git {' '.join(args)} failed (exit {result.code}); output omitted"]
    return limit_output(result.stdout, line_limit, byte_limit)


def git_recent_files(root: Path, limit: int) -> list[str]:
    candidates: set[str] = set()
    for args in (
        ("ls-files", "-m", "-o", "--exclude-standard"),
        ("diff", "--name-only"),
        ("diff", "--cached", "--name-only"),
    ):
        result = git_cmd(root, *args)
        if result.code == 0:
            candidates.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    rows: list[tuple[float, str]] = []
    for rel in candidates:
        path = root / rel
        try:
            rows.append((path.stat().st_mtime, rel))
        except OSError:
            rows.append((0, rel))
    rows.sort(reverse=True)
    return [rel for _, rel in rows[:limit]]


def fs_recent_files(root: Path, limit: int, max_files: int, max_depth: int) -> tuple[list[str], bool]:
    rows: list[tuple[float, str]] = []
    seen = 0
    truncated = False
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        depth = len(base.parts) - root_depth
        if max_depth >= 0 and depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            seen += 1
            if max_files > 0 and seen > max_files:
                truncated = True
                return [rel for _, rel in sorted(rows, reverse=True)[:limit]], truncated
            path = base / name
            try:
                rel = path.relative_to(root).as_posix()
                rows.append((path.stat().st_mtime, rel))
            except OSError:
                continue
    rows.sort(reverse=True)
    return [rel for _, rel in rows[:limit]], truncated


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit compact Markdown repo state for handoff snapshots.")
    parser.add_argument("--root", default=".", help="Repo root or working directory to inspect")
    parser.add_argument("--limit", type=int, default=80, help="Maximum lines per git output block; <=0 disables line limiting")
    parser.add_argument("--max-bytes", type=int, default=32768, help="Maximum UTF-8 bytes per git output block; <=0 disables byte limiting")
    parser.add_argument("--recent-limit", type=int, default=20, help="Maximum recent files to list")
    parser.add_argument("--max-files", type=int, default=5000, help="Maximum files to scan in non-git fallback; <=0 disables cap")
    parser.add_argument("--max-depth", type=int, default=6, help="Maximum directory depth for non-git fallback; <0 disables cap")
    args = parser.parse_args()

    start = Path(args.root).expanduser().resolve()
    found_root = git_root(start)
    root = found_root or start
    is_git = found_root is not None
    version = load_version()

    print("## Repo State Probe")
    print(f"- Schema Version: {SCHEMA_VERSION}")
    print(f"- Probe script version: {version}")
    print(f"- Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"- Root: `{root}`")
    print(f"- Git repo: {'yes' if is_git else 'no'}")

    if is_git:
        branch_result = git_cmd(root, "branch", "--show-current")
        commit_result = git_cmd(root, "rev-parse", "--short", "HEAD")
        status_result = git_cmd(root, "status", "--short")
        super_result = git_cmd(root, "rev-parse", "--show-superproject-working-tree")
        branch = branch_result.stdout if branch_result.code == 0 and branch_result.stdout else "Unknown"
        commit = commit_result.stdout if commit_result.code == 0 and commit_result.stdout else "Unknown"
        dirty = "unknown" if status_result.code != 0 else ("yes" if status_result.stdout.strip() else "no")
        print(f"- Branch: `{code_span(branch)}`")
        print(f"- Commit: `{code_span(commit)}`")
        print(f"- Git dirty: {dirty}")
        if super_result.code == 0 and super_result.stdout:
            shown, redacted = display_path_like(super_result.stdout)
            suffix = " [redacted]" if redacted else ""
            print(f"- Git submodule: yes; superproject root: `{shown}`{suffix}")
        else:
            print("- Git submodule: no/unknown")
        if status_result.code != 0:
            print(f"- Git status warning: `git status --short` failed (exit {status_result.code}); treating dirty state as unknown")
        print()
        print_block("Git Status Short", limit_output(status_result.stdout, args.limit, args.max_bytes) if status_result.code == 0 else [f"git status --short failed (exit {status_result.code}); output omitted"])
        print()
        print_block("Unstaged Diff Stat", git_lines(root, ("diff", "--stat"), args.limit, args.max_bytes))
        print()
        print_block("Unstaged Changed Files", git_lines(root, ("diff", "--name-status"), args.limit, args.max_bytes))
        print()
        print_block("Staged Diff Stat", git_lines(root, ("diff", "--cached", "--stat"), args.limit, args.max_bytes))
        print()
        print_block("Staged Changed Files", git_lines(root, ("diff", "--cached", "--name-status"), args.limit, args.max_bytes))
        print()
        print_block("Recent Modified/Untracked Files", git_recent_files(root, args.recent_limit))
    else:
        print("- Branch: `Unknown`")
        print("- Commit: `Unknown`")
        print("- Git dirty: `unknown`")
        print(f"- Non-git scan caps: max files={args.max_files}, max depth={args.max_depth}")
        print()
        recent, truncated = fs_recent_files(root, args.recent_limit, args.max_files, args.max_depth)
        print_block("Recent Files", recent, empty="no files found")
        if truncated:
            print(f"- ... (non-git scan stopped after {args.max_files} files)")
        print()
        print("### Non-Git Notes")
        print("- Filesystem metadata only; no git status/diff is available.")
        print("- Large/private non-git trees are scanned only up to the configured caps.")

    print()
    print("### Safety Notes")
    print("- Raw file contents and raw diff hunks were not inspected or emitted.")
    print("- Sensitive-looking paths are redacted and values are not read or printed.")
    print("- If a raw diff is required later, redact it before adding it to a handoff snapshot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
