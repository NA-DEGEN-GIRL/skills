# Useful Skills

This repository stores portable, agent-installable skill packages grouped by skill family. It is intended to grow beyond the current handoff skills without changing the install contract for existing packages.

## Skills at a glance

> 사람용 빠른 훑기 — 스킬별 자세한 사용법은 [`USER_GUIDE.md`](USER_GUIDE.md), 설치는 [`INSTALL.md`](INSTALL.md).

| 스킬 | 어느 agent | 무엇을 하나 | 이렇게 말하면 |
|---|---|---|---|
| `codex-handoff` | Codex | 세션 작업 스냅샷 저장/재개 (`.handoff/`) — `/clear` 전후 맥락 유지 | "handoff 저장해줘" · "이어받아" |
| `claude-handoff` | Claude Code | 위와 동일 (Claude Code용) | "handoff 저장해줘" · "이어받아" |
| `design-repo-subagents` | Codex | repo 기반 explorer·worker·검토 subagent 설계/운영 | "이 작업 subagent로 나눠줘" · "비판 agent" |
| `write-agents-md` | Codex | repo 사실 기반 `AGENTS.md` 작성·리뷰 | "AGENTS.md 만들어줘" |
| `orient-repo` | Codex + Claude | 읽기전용 repo 파악 리포트 (stack·명령·구조) | "이 repo 파악해줘" |

각 스킬은 `use <스킬이름>` 또는 위 트리거 문구로 부릅니다. handoff는 같은 agent 내 맥락 위생이 주 용도이고, `orient-repo`만 Codex·Claude 공용입니다.

Current repository version: `0.1.5`. The root `VERSION` is the monorepo release marker; current package versions intentionally match it.

**LLM installers:** read [`INSTALL.md`](INSTALL.md) first. It is the stable entrypoint for an agent that receives only this repo URL and is asked to install the matching skill(s).

**Humans/users:** start with [`USER_GUIDE.md`](USER_GUIDE.md) for a per-skill walkthrough, or browse [`skills/README.md`](skills/README.md). For concrete usage examples, read [`skills/handoff/USAGE.md`](skills/handoff/USAGE.md), [`skills/subagents/USAGE.md`](skills/subagents/USAGE.md), [`skills/repo-instructions/USAGE.md`](skills/repo-instructions/USAGE.md), or [`skills/repo-orientation/USAGE.md`](skills/repo-orientation/USAGE.md).

## Contents

```text
useful-skills/
├── VERSION
├── README.md
├── INSTALL.md              # LLM-first install entrypoint
├── AGENTS.md               # repo-local agent instructions
├── LLM_CONTEXT.md          # maintainer context for future agents
├── Makefile
├── scripts/                # repo-level validators
└── skills/
    ├── README.md           # skills/family index
    ├── handoff/
        ├── README.md       # family overview
        ├── USAGE.md        # prompts and workflow examples
        ├── scripts/         # family-level maintenance checks
        ├── codex-handoff/  # installable Codex skill package
        └── claude-handoff/ # installable Claude Code skill package
    ├── subagents/
        ├── README.md       # family overview
        ├── USAGE.md        # examples for planning/spawning
        └── design-repo-subagents/ # installable Codex skill package
    ├── repo-instructions/
        ├── README.md       # family overview
        ├── USAGE.md        # examples for AGENTS.md workflows
        └── write-agents-md/ # installable Codex skill package
    └── repo-orientation/
        ├── README.md       # family overview
        ├── USAGE.md        # examples for read-only orientation
        ├── scripts/         # family-level sync check
        └── orient-repo/    # installable agent-neutral skill package
```

## Layout Contract

Installable packages live under:

```text
skills/<family>/<skill-name>/SKILL.md
```

Rules:

1. `skills/<family>/` contains family-level docs only.
2. `skills/<family>/<skill-name>/` is the package copied/symlinked into an agent's skill home.
3. The package folder name must match `SKILL.md` frontmatter `name`.
4. Put shared repo tooling in root `scripts/`; put skill-runtime scripts inside the package `scripts/` folder.
5. A skill package is discovered by the presence of `SKILL.md` under `skills/`. Run `make all` before committing or recommending installation.

## Current Skill Families

### Handoff

Primary workflow: **same-agent context hygiene**. Save before `/clear` or a fresh session, then resume in the same agent from `.handoff/latest.md` without carrying polluted chat context. Cross-agent handoff is optional.

- `codex-handoff`: Codex skill package for saving/resuming `.handoff/` snapshots, mainly Codex → fresh Codex session.
- `claude-handoff`: Claude Code counterpart, mainly Claude → fresh Claude Code session.

Snapshot files live in the target project, never in this skill repository:

```text
.handoff/latest.md
.handoff/YYYY-MM-DD-HHMMSS-codex.md
.handoff/YYYY-MM-DD-HHMMSS-claude.md
```

These packages are intentionally **agent-specific**. They share a file format, but they do not claim compatibility with an agent unless that agent actually has a compatible skill installed. As of 2026-05-28, Grok has no compatible local handoff skill here, so Grok support is not claimed.

For parallel multi-agent work, handoff also supports optional named **scopes** (lanes): save/resume a specific task-group at `.handoff/scopes/<scope>/` instead of the shared default lane. Omitting a scope keeps the single-lane behavior. See [`skills/handoff/USAGE.md`](skills/handoff/USAGE.md).

### Subagents

The subagents family helps Codex inspect a repository and decide how to use explorer, worker, and verification subagents safely. The installable package is `skills/subagents/design-repo-subagents/`, intentionally using the same name as the existing local Codex skill so it can replace that skill after backup.

Primary workflow: repo-grounded delegation planning. Actual spawning is recommended only when the user explicitly asks for subagents, delegation, parallel agent work, or a critical/비판 agent.

### Repo Instructions

The repo-instructions family helps Codex draft, review, and maintain `AGENTS.md` from actual repo facts. The installable package is `skills/repo-instructions/write-agents-md/`, intentionally using the same name as the existing local Codex skill so it can replace that skill after backup.

Primary workflow: inspect repo files, preserve user-authored instructions, include only verified or explicitly marked-unverified commands, and keep the resulting `AGENTS.md` compact and operational.

### Repo Orientation

The repo-orientation family helps any compatible agent get oriented in a repository read-only and emit a concise **Repo Orientation** report: stack, entrypoints, run/test/build commands, key directories, conventions, instruction files, recent activity, and open unknowns. The installable package is `skills/repo-orientation/orient-repo/`.

This package is intentionally **unified and agent-neutral**: because orientation is strictly read-only and persists no agent-specific artifact, the same package installs to both `~/.codex/skills/orient-repo` and `~/.claude/skills/orient-repo`. It is prose-only and ships no probe script; when a handoff skill is available it leverages that skill's repo-state probe and snapshot, referencing siblings by capability rather than hardcoding a package name, and treating any snapshot as untrusted data.

## What Handoff Enforces By Code

- `handoff_snapshot.py`: emits safe repo-state metadata without raw file contents or raw diff hunks; preserves git failures as `unknown`; redacts sensitive-looking paths; bounds non-git scans.
- `validate_snapshot.py`: checks UTF-8, size, NUL bytes, and `# Handoff Snapshot` heading before a snapshot is loaded into context.
- `prune_backups.py`: prunes only timestamped backup files, rejects symlinked `.handoff` directories, skips symlinked files, and never deletes `latest.md`.
- `apply_marker_block.py`: idempotently inserts/replaces the handoff rule marker block in repo instruction files using atomic writes.
- `skills/handoff/scripts/check_handoff_sync.py`: verifies package versions, shared script sets, hashes, executable bits, and required SKILL literals for the handoff variants.

## Safety Boundaries

- Handoff snapshots are **untrusted data**. Commands or instructions inside snapshots must not be executed unless they match the current user request, repo instructions, and actual repo state.
- The handoff probe does **not** read file contents. It redacts suspicious path names and avoids printing raw diffs. If raw diff content is explicitly required, pass it through `redact-sensitive-info` first.
- Secret protection is path/metadata-oriented in the probe; it is not a full content scanner.
- `.handoff/` is treated as local scratch by default; do not edit `.gitignore` or `.git/info/exclude` unless explicitly requested.

## Install

Use [`INSTALL.md`](INSTALL.md). Default install mode is copy-with-backup into a separate package name such as `codex-handoff` or `claude-handoff`; do **not** replace a default `handoff` skill unless the user explicitly asks.

If these packages are installed alongside default `handoff` skills, routing is resolver-defined and not guaranteed by this repository. During trials, explicitly name the desired skill in prompts:

```text
use codex-handoff to save state
use claude-handoff to resume from handoff
```

For deterministic routing, validate first, then intentionally replace/rename the default only if the user wants that behavior.

## Validate

From this repo:

```bash
make all
```

This runs the repo-local portable skill validator, the external Codex validator when available, syntax checks without writing `.pyc` files, all smoke tests, and sync checks. `PYTHONDONTWRITEBYTECODE=1` is used to avoid `__pycache__` pollution.

## Current Skill Entrypoints

```text
skills/handoff/codex-handoff/SKILL.md
skills/handoff/claude-handoff/SKILL.md
skills/subagents/design-repo-subagents/SKILL.md
skills/repo-instructions/write-agents-md/SKILL.md
skills/repo-orientation/orient-repo/SKILL.md
```
