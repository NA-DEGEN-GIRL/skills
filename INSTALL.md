# Install Guide For LLM Agents

Use this file when a user gives you this repository and says something like:

```text
Install the matching skill(s) from https://github.com/NA-DEGEN-GIRL/skills.git
```

This is the stable LLM-first entrypoint. The repository may contain multiple skill families over time; install only the package(s) matching the user's target agent and requested capability. For maintenance or repo editing, also read `LLM_CONTEXT.md`.

## Current Installable Packages

| Capability | Target agent | Source folder | Install destination |
|---|---|---|---|
| handoff | Codex | `skills/handoff/codex-handoff/` | `${CODEX_HOME:-$HOME/.codex}/skills/codex-handoff` |
| handoff | Claude Code | `skills/handoff/claude-handoff/` | `$HOME/.claude/skills/claude-handoff` |

Do **not** replace existing default `handoff` skills unless the user explicitly asks for replacement. Install the current handoff packages as separate `codex-handoff` / `claude-handoff` skills by default.

## Quick Install From Repo URL

If you are not already inside the cloned repo:

```bash
tmpdir=$(mktemp -d)
git clone --depth 1 https://github.com/NA-DEGEN-GIRL/skills.git "$tmpdir/skills"
cd "$tmpdir/skills"
```

Validate before installing. A package is discovered by a `SKILL.md` file under `skills/`; current validation also runs family-specific sync checks such as `skills/handoff/scripts/check_handoff_sync.py`.

```bash
make all
```

## Choose What To Install

1. Identify the user's target agent: Codex, Claude Code, both, or another compatible skill system.
2. Identify the requested capability/family, e.g. `handoff`. If the user only says "useful skills" and gives no capability, show the table above and ask which ones to install.
3. Install only matching packages. Currently:
   - Codex + handoff: install `codex-handoff` only.
   - Claude Code + handoff: install `claude-handoff` only.
   - Both + handoff: install both.
4. If the target agent is unclear, ask one short question: `Codex용, Claude용, 둘 다 중 무엇을 설치할까요?`

## Safe Copy Install Commands

Copy install is safest when this repo was cloned into a temp directory. It backs up any existing same-name install path and does not touch default `handoff`.

### Codex handoff

```bash
src="$PWD/skills/handoff/codex-handoff"
dest="${CODEX_HOME:-$HOME/.codex}/skills/codex-handoff"
mkdir -p "$(dirname "$dest")"
if [ -L "$dest" ]; then
  rm "$dest"
elif [ -e "$dest" ]; then
  mv "$dest" "$dest.bak.$(date +%Y%m%d%H%M%S)"
fi
cp -a "$src" "$dest"
```

### Claude Code handoff

```bash
src="$PWD/skills/handoff/claude-handoff"
dest="$HOME/.claude/skills/claude-handoff"
mkdir -p "$(dirname "$dest")"
if [ -L "$dest" ]; then
  rm "$dest"
elif [ -e "$dest" ]; then
  mv "$dest" "$dest.bak.$(date +%Y%m%d%H%M%S)"
fi
cp -a "$src" "$dest"
```

## Optional Symlink Install

Use symlinks only if the clone path is persistent and the user wants updates to track the working copy.

```bash
# Codex handoff
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -sfn "$PWD/skills/handoff/codex-handoff" "${CODEX_HOME:-$HOME/.codex}/skills/codex-handoff"

# Claude Code handoff
mkdir -p "$HOME/.claude/skills"
ln -sfn "$PWD/skills/handoff/claude-handoff" "$HOME/.claude/skills/claude-handoff"
```

## Generic Rule For Future Packages

If a future package is added under `skills/<family>/<skill-name>/`:

1. Confirm it contains `SKILL.md` and passes `make all` or the documented package-specific validation.
2. Copy the whole `<skill-name>/` directory into the target agent's skill home under the same name, backing up any same-name destination first.
3. Do not infer cross-agent compatibility from folder proximity; install only variants whose `SKILL.md` and docs identify the target agent.

## After Installing

Tell the user to restart the target agent or open a fresh session so skill metadata is discovered.

Suggested final message for current handoff installs:

```text
Installed codex-handoff/claude-handoff. Restart Codex/Claude Code or start a fresh session to pick up the new skill. During trial, explicitly request `codex-handoff` or `claude-handoff` because default `handoff` may still coexist.
```

## Routing Caveat

If the default `handoff` skill is also installed, routing is resolver-defined. For deterministic routing, the user must explicitly request this skill by name or intentionally replace/rename the default after validation.
