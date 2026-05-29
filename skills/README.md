# Skills Index

This directory contains installable skill packages grouped by skill family.

## Available Families

| Family | Purpose | Variants | Version | Docs |
|---|---|---|---|---|
| `handoff` | Save/resume repo-local handoff snapshots for clean sessions and optional cross-agent transfer | `codex-handoff`, `claude-handoff` | `0.1.2` | [`handoff/README.md`](handoff/README.md), [`handoff/USAGE.md`](handoff/USAGE.md) |
| `subagents` | Design and operate repo-specific Codex subagent delegation plans | `design-repo-subagents` | `0.1.2` | [`subagents/README.md`](subagents/README.md), [`subagents/USAGE.md`](subagents/USAGE.md) |

## Layout Convention

```text
skills/<family>/
├── README.md          # family overview
├── USAGE.md           # prompt examples when useful
├── scripts/           # optional family-level maintenance checks
├── <agent-skill>/     # installable skill package
│   ├── SKILL.md
│   ├── VERSION
│   ├── agents/openai.yaml
│   └── scripts/
└── ...
```

Discovery and documentation rules for adding future skills:

1. Put each new family under `skills/<family>/`.
2. Put each installable package under `skills/<family>/<skill-name>/` where folder name equals `SKILL.md` frontmatter `name`.
3. Update this index and root `README.md` / `INSTALL.md`.
4. A package is discovered by `make all` when it has a `SKILL.md` under `skills/`.
5. Use `README.md` for family overview and `USAGE.md` for concrete prompt/install/operation examples when needed.
6. Add tests or validation commands when the skill ships scripts.
7. Put family-only sync checks under `skills/<family>/scripts/check_*_sync.py`.
8. Run `make all` before committing.
