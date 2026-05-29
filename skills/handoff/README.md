# Handoff Skill Family

The handoff family stores compact repo-local snapshots so an agent can resume work after `/clear`, a fresh session, or an optional transfer to another compatible agent.

Primary workflow: **same-agent context hygiene**.

```text
Codex long session  -> codex-handoff Save  -> fresh Codex session  -> codex-handoff Resume
Claude long session -> claude-handoff Save -> fresh Claude session -> claude-handoff Resume
```

Cross-agent transfer is optional:

```text
Codex Save -> Claude Resume
Claude Save -> Codex Resume
```

Both variants also support optional **scoped lanes** (`.handoff/scopes/<scope>/`) so parallel agents can save/resume a specific task-group instead of one shared snapshot; omit a scope for the single default lane. See [`USAGE.md`](USAGE.md).

## Variants

| Variant | Install destination | Use when |
|---|---|---|
| `codex-handoff` | `${CODEX_HOME:-$HOME/.codex}/skills/codex-handoff` | Working in Codex |
| `claude-handoff` | `$HOME/.claude/skills/claude-handoff` | Working in Claude Code |

## Family Maintenance

Family-only sync checks live in `scripts/`, currently `scripts/check_handoff_sync.py`. Installable packages remain the `codex-handoff/` and `claude-handoff/` directories.

## Install

Read the root [`INSTALL.md`](../../INSTALL.md). Source folders are:

```text
skills/handoff/codex-handoff
skills/handoff/claude-handoff
```

## Usage

Read [`USAGE.md`](USAGE.md) for concrete Save/Resume prompts.
