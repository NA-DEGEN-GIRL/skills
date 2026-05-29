# Nested AGENTS.md Patterns

Use nested `AGENTS.md` files sparingly. Root instructions should cover the common case.

## Create Or Keep Nested Instructions When

- A subdirectory has different build/test commands.
- A generated, vendored, migration, schema, or fixture directory needs special safety rules.
- Ownership or review rules differ materially from the rest of the repo.
- A monorepo package has its own manifest, CI job, or language/toolchain.

## Avoid Nested Instructions When

- The nested file would only repeat root guidance.
- The difference can be expressed as one short root bullet.
- The directory is small and not independently worked on.
- The user asked only for a root `AGENTS.md`.

## Nested File Shape

Nested files should be shorter than the root and focus only on local differences:

```md
# AGENTS.md

## Scope

These instructions apply to `[directory]/`.

## Commands

- Test this package: `[command]`

## Local Rules

- [Directory-specific safety, generated-file, ownership, or style rule.]
```

Do not duplicate global safety rules unless repetition prevents likely mistakes.
