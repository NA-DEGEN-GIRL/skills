# AGENTS.md Template

Use this as a compact starting point. Delete sections that are not supported by repo facts.

```md
# AGENTS.md

## Project Overview

[One short paragraph describing what this repo is, the primary stack, and the main entrypoints.]

## Commands

- Install: `[command]`
- Develop: `[command]`
- Build: `[command]`
- Test: `[command]`
- Lint/typecheck: `[command]`

Only include commands confirmed from manifests, scripts, CI, docs that match current repo files, or successful local execution. Mark commands as unverified if inferred but not run.

## Code Style

- Follow the existing formatter, linter, naming conventions, and project layout.
- Keep changes scoped to the requested behavior.
- Prefer existing helpers and patterns over new abstractions.

## Testing

- Add or update tests near the behavior being changed.
- Run the smallest relevant test first, then broader checks when touching shared code.
- Note any tests that cannot be run and why.

## Safety

- Do not revert or overwrite user changes.
- Do not commit secrets, tokens, local paths with usernames, generated files, or build artifacts.
- Avoid editing vendored/generated directories unless the task explicitly requires it.
- Preserve public APIs, schemas, migrations, and compatibility contracts unless the user asks to change them.

## Subagents

- Use explorer subagents for bounded read-only codebase questions.
- Use worker subagents only for independent implementation slices with clear file ownership.
- Keep final integration, conflict resolution, and product decisions in the main agent.
```

## Root vs Nested Instructions

- Put repo-wide rules in root `AGENTS.md`.
- Put directory-specific commands or ownership rules in nested `AGENTS.md` only when they differ materially from the root.
- Nested files should be shorter than the root and should not repeat global rules unless repetition prevents mistakes.
