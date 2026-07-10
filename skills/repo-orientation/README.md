# Repo Orientation Skill Family

The repo-orientation family helps any compatible agent inspect a real repository read-only and produce a concise orientation report: stack, entrypoints, run/test/build commands, key directories, conventions, instruction files, decision docs/Design Briefs, recent activity, and open unknowns.

## Variants

| Variant | Install destination | Use when |
|---|---|---|
| `orient-repo` | `${CODEX_HOME:-$HOME/.codex}/skills/orient-repo` and/or `$HOME/.claude/skills/orient-repo` | You want a read-only tour/orientation of a repo in any compatible agent |

This family ships a **single, agent-neutral package**. Unlike the handoff family, it is not split into Codex/Claude variants: orientation is strictly read-only and produces no agent-specific persisted artifact (no snapshot provenance, no per-agent backup, no instruction-file write target), so the same package is correct for both runtimes. Install the same source folder to whichever agent homes you use.

## Install

Read the root [`INSTALL.md`](../../INSTALL.md). Source folder:

```text
skills/repo-orientation/orient-repo
```

Use the root installer workflow. It detects an existing same-name destination and keeps any required backup outside agent skill-discovery roots.

## Usage

Read [`USAGE.md`](USAGE.md) for example prompts and the orientation-report shape.

Handoff context is optional. When available, the skill keeps default/scoped lanes separate, uses a safe selector or bounded manual validation, and never treats snapshot content as authority.
