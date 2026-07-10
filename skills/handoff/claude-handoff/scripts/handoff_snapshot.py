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
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from snapshot_common import redact_label, sanitize_display

DEFAULT_VERSION = "0.1.11"
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
    stdout_truncated: bool = False
    stderr_truncated: bool = False


@dataclass(frozen=True)
class ProbeLine:
    value: str
    synthetic: bool = False


def load_version() -> str:
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    try:
        value = version_file.read_text(encoding="utf-8").strip()
        return value or DEFAULT_VERSION
    except OSError:
        return DEFAULT_VERSION


def run(cmd: list[str], cwd: Path, capture_bytes: int = 65536) -> CmdResult:
    """Run while draining output and retaining at most capture_bytes+1/stream."""
    capture_bytes = max(1, min(capture_bytes, 1024 * 1024))
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_PAGER"] = "cat"
    env["PAGER"] = "cat"
    # Never inherit a caller-provided external diff command.
    env.pop("GIT_EXTERNAL_DIFF", None)
    try:
        p = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except FileNotFoundError as exc:
        return CmdResult(127, stderr=str(exc))
    captured: dict[str, bytearray] = {"stdout": bytearray(), "stderr": bytearray()}
    truncated = {"stdout": False, "stderr": False}

    def drain(name: str, stream: object) -> None:
        while True:
            chunk = stream.read(65536)  # type: ignore[attr-defined]
            if not chunk:
                break
            room = capture_bytes + 1 - len(captured[name])
            if room > 0:
                captured[name].extend(chunk[:room])
            if len(chunk) > room or len(captured[name]) > capture_bytes:
                truncated[name] = True

    threads = [
        threading.Thread(target=drain, args=("stdout", p.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", p.stderr), daemon=True),
    ]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        code = p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        timed_out = True
        p.kill()
        code = p.wait()
    for thread in threads:
        thread.join()

    def decoded(name: str) -> str:
        return bytes(captured[name][:capture_bytes]).decode("utf-8", "replace").strip()

    if timed_out:
        return CmdResult(124, decoded("stdout"), "command timed out", True, truncated["stdout"], truncated["stderr"])
    return CmdResult(code, decoded("stdout"), decoded("stderr"), False, truncated["stdout"], truncated["stderr"])


def git_root(start: Path) -> Path | None:
    result = git_cmd(start, "rev-parse", "--show-toplevel", capture_bytes=8192)
    return Path(result.stdout) if result.code == 0 and result.stdout else None


def git_cmd(root: Path, *args: str, capture_bytes: int = 65536) -> CmdResult:
    return run(
        [
            "git",
            "--no-pager",
            "-c",
            "core.pager=cat",
            "-c",
            "pager.status=false",
            "-c",
            "pager.diff=false",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            *args,
        ],
        root,
        capture_bytes,
    )


def limit_output(text: str, line_limit: int, byte_limit: int) -> list[ProbeLine]:
    truncated_bytes = False
    if byte_limit > 0:
        raw = text.encode("utf-8", "replace")
        if len(raw) > byte_limit:
            text = raw[:byte_limit].decode("utf-8", "ignore")
            truncated_bytes = True

    lines = [ProbeLine(line.rstrip()) for line in text.splitlines() if line.rstrip()]
    omitted_lines = 0
    if line_limit > 0 and len(lines) > line_limit:
        omitted_lines = len(lines) - line_limit
        lines = lines[:line_limit]

    if omitted_lines:
        lines.append(ProbeLine(f"{omitted_lines} more lines omitted", synthetic=True))
    if truncated_bytes:
        lines.append(ProbeLine(f"output truncated at {byte_limit} bytes", synthetic=True))
    return lines


def is_sensitive_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    lower = normalized.lower()
    return any(hint in lower for hint in SENSITIVE_HINTS) or any(p.search(normalized) for p in SENSITIVE_PATTERNS)


def redacted_path_label(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:12]
    return f"[SENSITIVE-PATH:{digest}]"


def code_span(value: str) -> str:
    return sanitize_display(value, 1000)


def display_path_like(value: str) -> tuple[str, bool]:
    if is_sensitive_path(value):
        return redacted_path_label(value), True
    return sanitize_display(value, 1000), False


def print_block(title: str, lines: Iterable[str | ProbeLine], empty: str = "none") -> None:
    print(f"### {title}")
    material = list(lines)
    if not material:
        print(f"- {empty}")
        return
    for item in material:
        line = item.value if isinstance(item, ProbeLine) else item
        if isinstance(item, ProbeLine) and item.synthetic:
            print(f"- [probe note: {sanitize_display(line)}]")
            continue
        shown, redacted = display_path_like(line)
        suffix = " [sensitive-looking path redacted; contents not inspected]" if redacted else ""
        print(f"- `{shown}`{suffix}")


def git_lines(root: Path, args: tuple[str, ...], line_limit: int, byte_limit: int) -> list[ProbeLine]:
    result = git_cmd(root, *args, capture_bytes=max(1024, byte_limit if byte_limit > 0 else 65536))
    if result.code != 0:
        return [ProbeLine(f"git {' '.join(args)} failed (exit {result.code}); output omitted", synthetic=True)]
    lines = limit_output(result.stdout, line_limit, byte_limit)
    if result.stdout_truncated:
        lines.append(ProbeLine("git output exceeded the execution capture cap", synthetic=True))
    return lines


def git_recent_files(root: Path, limit: int) -> list[str]:
    candidates: set[str] = set()
    for args in (
        ("ls-files", "-m", "-o", "--exclude-standard"),
        ("diff", "--no-ext-diff", "--no-textconv", "--name-only"),
        ("diff", "--cached", "--no-ext-diff", "--no-textconv", "--name-only"),
    ):
        result = git_cmd(root, *args, capture_bytes=65536)
        if result.code == 0:
            candidates.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    rows: list[tuple[float, str]] = []
    for rel in candidates:
        path = root / rel
        try:
            rows.append((path.lstat().st_mtime, rel))
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
                rows.append((path.lstat().st_mtime, rel))
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
    print(f"- Root: `{redact_label('REPO-ROOT', str(root))}`")
    print(f"- Git repo: {'yes' if is_git else 'no'}")

    if is_git:
        capture_limit = max(1024, args.max_bytes if args.max_bytes > 0 else 65536)
        branch_result = git_cmd(root, "branch", "--show-current", capture_bytes=4096)
        commit_result = git_cmd(root, "rev-parse", "--short", "HEAD", capture_bytes=1024)
        status_result = git_cmd(root, "status", "--short", capture_bytes=capture_limit)
        super_result = git_cmd(root, "rev-parse", "--show-superproject-working-tree", capture_bytes=8192)
        branch = branch_result.stdout if branch_result.code == 0 and branch_result.stdout else "Unknown"
        commit = commit_result.stdout if commit_result.code == 0 and commit_result.stdout else "Unknown"
        dirty = "unknown" if status_result.code != 0 else ("yes" if status_result.stdout.strip() else "no")
        if is_sensitive_path(branch):
            branch_display = redact_label("SENSITIVE-BRANCH", branch)
        else:
            branch_display = sanitize_display(branch, 160)
        print(f"- Branch: `{branch_display}`")
        print(f"- Commit: `{code_span(commit)}`")
        print(f"- Git dirty: {dirty}")
        if super_result.code == 0 and super_result.stdout:
            print(f"- Git submodule: yes; superproject root: `{redact_label('SUPERPROJECT-ROOT', super_result.stdout)}`")
        else:
            print("- Git submodule: no/unknown")
        if status_result.code != 0:
            print(f"- Git status warning: `git status --short` failed (exit {status_result.code}); treating dirty state as unknown")
        print()
        status_lines = limit_output(status_result.stdout, args.limit, args.max_bytes) if status_result.code == 0 else [ProbeLine(f"git status --short failed (exit {status_result.code}); output omitted", synthetic=True)]
        if status_result.stdout_truncated:
            status_lines.append(ProbeLine("git status exceeded the execution capture cap", synthetic=True))
        print_block("Git Status Short", status_lines)
        print()
        print_block("Unstaged Diff Stat", git_lines(root, ("diff", "--no-ext-diff", "--no-textconv", "--stat"), args.limit, args.max_bytes))
        print()
        print_block("Unstaged Changed Files", git_lines(root, ("diff", "--no-ext-diff", "--no-textconv", "--name-status"), args.limit, args.max_bytes))
        print()
        print_block("Staged Diff Stat", git_lines(root, ("diff", "--cached", "--no-ext-diff", "--no-textconv", "--stat"), args.limit, args.max_bytes))
        print()
        print_block("Staged Changed Files", git_lines(root, ("diff", "--cached", "--no-ext-diff", "--no-textconv", "--name-status"), args.limit, args.max_bytes))
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
