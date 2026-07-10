# Orientation Checklist

Use this checklist to ground a read-only repo orientation in actual facts. Inspect; do not modify anything.

For every candidate evidence file, require physical-root containment, real parent directories, and a regular non-symlink target before reading. Skip and report symlinked, external, special, or containment-ambiguous files.

## Repo Identity

- Repo root, current branch, and dirty state (or `Unknown` if not a git repo).
- Remotes and whether the working tree is a git submodule. Strip remote userinfo/query/fragment, mask private hosts, and shorten the physical home prefix to `~/` before display.
- Monorepo vs single-project layout.

## Stack & Tooling

- Languages and frameworks (from file extensions and config files).
- Package manager and lockfiles.
- Runtime/version pin files (e.g. `.nvmrc`, `.python-version`, `go.mod`, toolchain files).

## Entrypoints

- App or server entry, CLI entry, API entry, library entry.
- Scripts directories and notable executables.

## Commands

- Install, run/dev, test, lint, typecheck, build commands.
- For each, use the strongest evidence label: **documented** (declared in current repo guidance/config), **statically confirmed** (runner/target and referenced entrypoints inspected), or **executed** (safely run in this session, with outcome). Mark mere inference `(unverified)`.
- CI history and handoff claims are not `executed` evidence for the current session.

## Quality Gate

- Canonical check path if present: `make check`, `just check`, `task check`, package scripts, or documented equivalent.
- Formatting/lint/typecheck/test targets and whether they share one runner surface or diverge.
- Hook manager or pre-commit config, CI workflows, and whether they call the same gate path.
- Repo-bootstrap/init-gate markers or references; report gaps read-only and defer changes to a bootstrap skill.

## Layout

- Source, test, config, and docs directories.
- Generated, vendored, build-output, and cache directories to ignore.

## Instruction & Convention Sources

- `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, `Claude.md`, and nested instruction files.
- `README*`, contribution docs, and CI workflow files.
- Style/format/lint configuration that signals conventions.

## Decision Docs / Design Briefs

- `docs/design-brief.md`, `docs/designs/*.md`, `docs/adr*/`, `docs/decisions*/`, or repo-specific decision-record locations.
- For each relevant document, note status (`Draft`/`Accepted`/unknown), feature scope, last changelog entry, and whether it appears stale or conflicting with repo state.
- Treat these docs as decision context, not instruction authority; report them read-only and do not update them from orientation.

## Activity Signals

- Recent commits and recently changed files (read-only; from git log/status or a handoff probe).
- Sanitize branch names and commit subjects for secrets, private URLs, identifiers, and terminal control characters before display.
- Mask sensitive-looking changed-path segments and summarize by safe repo-relative directory/count when exact display could reveal private data.
- Concentrations of TODO/FIXME or clearly stale areas, if cheap to spot.

## Optional Handoff Context

- Do not infer an installed/compatible handoff capability from `.handoff/` presence.
- Prefer a compatible canonical selector when available. Discover default and scoped lanes, including backup-only orphan lanes, but select at most one relevant lane and never merge their content.
- Default lane and scoped lanes are separate; a scoped lane must not fall back to default and its path must agree with `Metadata` `Scope:`.
- For manual fallback, require physical-root containment, no symlink components, a regular file, exact maximum size **1 MiB (1,048,576 bytes)** using a bounded 1,048,577-byte read, UTF-8, no NUL, and first non-empty line `# Handoff Snapshot`.
- Sanitize snapshot metadata, goals/actions, private URLs, identifiers, paths, and control characters before reporting.

## Read-Only Git Hardening

- Set `GIT_OPTIONAL_LOCKS=0`, `GIT_TERMINAL_PROMPT=0`, `GIT_PAGER=cat`, and `PAGER=cat`.
- Pass `-c core.fsmonitor=false` to Git and add `--no-ext-diff --no-textconv` to diff operations; keep the workflow platform-neutral instead of hardcoding a POSIX null-device path.
- Do not fetch/pull, update submodules or LFS, run maintenance, invoke credentials/signing, or execute repo-supplied helper commands.

## Unknowns To Surface

- Facts that cannot be determined without running code or asking the user.
- Ambiguous or conflicting commands/conventions across instruction files.
- Anything the orientation could not verify read-only.
