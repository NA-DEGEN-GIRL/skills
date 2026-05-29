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

## Layout

- Source, test, config, and docs directories.
- Generated, vendored, build-output, and cache directories to ignore.

## Instruction & Convention Sources

- `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, `Claude.md`, and nested instruction files.
- `README*`, contribution docs, and CI workflow files.
- Style/format/lint configuration that signals conventions.

## Activity Signals

- Recent commits and recently changed files (read-only; from git log/status or a handoff probe).
- Concentrations of TODO/FIXME or clearly stale areas, if cheap to spot.

## Unknowns To Surface

- Facts that cannot be determined without running code or asking the user.
- Ambiguous or conflicting commands/conventions across instruction files.
- Anything the orientation could not verify read-only.
