# Orientation Checklist

Use this checklist to ground a read-only repo orientation in actual facts. Inspect; do not modify anything.

## Repo Identity

- Repo root, current branch, and dirty state (or `Unknown` if not a git repo).
- Remotes and whether the working tree is a git submodule.
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
- For each, note whether it is **documented** (instruction files, README, manifest scripts, CI) or **inferred** — mark inferred ones `(unverified)`.

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
- Concentrations of TODO/FIXME or clearly stale areas, if cheap to spot.

## Unknowns To Surface

- Facts that cannot be determined without running code or asking the user.
- Ambiguous or conflicting commands/conventions across instruction files.
- Anything the orientation could not verify read-only.
