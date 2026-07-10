# Subagents Skill Family

The subagents family helps Codex inspect a real repository, apply the active runtime's delegation policy, and design or operate safe explorer/worker delegation plus review/verification prompt patterns.

## Variants

| Variant | Install destination | Use when |
|---|---|---|
| `design-repo-subagents` | `${CODEX_HOME:-$HOME/.codex}/skills/design-repo-subagents` | Working in Codex with subagent/delegation tools |

## Install

Read the root [`INSTALL.md`](../../INSTALL.md). Source folder:

```text
skills/subagents/design-repo-subagents
```

This package intentionally uses the same name as the existing local Codex skill so it can replace that skill after backing it up. It is Codex-only because delegation runtimes are exposed through Codex, but it does not assume a fixed tool vocabulary, context-fork model, filesystem isolation, concurrency limit, or lifecycle API.

## Usage

Read [`USAGE.md`](USAGE.md) for planning-only and actual-delegation examples.
