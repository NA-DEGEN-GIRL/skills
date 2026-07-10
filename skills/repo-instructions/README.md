# Repo Instructions Skill Family

The repo-instructions family helps Codex draft, review, and maintain repository instruction files such as `AGENTS.md` from actual repo facts.

## Variants

| Variant | Install destination | Use when |
|---|---|---|
| `write-agents-md` | `${CODEX_HOME:-$HOME/.codex}/skills/write-agents-md` | Working in Codex or compatible agents that read `AGENTS.md` |

## Install

Read the root [`INSTALL.md`](../../INSTALL.md). Source folder:

```text
skills/repo-instructions/write-agents-md
```

This package intentionally uses the same name as the existing local Codex skill so it can replace that skill after backing it up.

## Usage

Read [`USAGE.md`](USAGE.md) for review, draft, and update examples.

`write-agents-md` can also add concise references to accepted/current Design Briefs or decision docs without embedding their full reasoning. Consequential brief changes remain owned by Shape Idea.

File edits are guarded: targets must remain inside the physical repo root with no symlink traversal, and existing instruction files require an exact-diff approval plus a verified timestamped backup before overwrite, deletion, or consolidation.
