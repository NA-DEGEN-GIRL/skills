# Install Guide For LLM Agents

Use this file when a user gives you this repository and says something like:

```text
Install the matching handoff skill(s) from https://github.com/NA-DEGEN-GIRL/skills.git
```

This repo contains two separate skill packages:

| Target agent | Source folder | Install destination |
|---|---|---|
| Codex | `codex-handoff/` | `${CODEX_HOME:-$HOME/.codex}/skills/codex-handoff` |
| Claude Code | `claude-handoff/` | `$HOME/.claude/skills/claude-handoff` |

Do **not** replace existing default `handoff` skills unless the user explicitly asks for replacement. Install these as separate `codex-handoff` / `claude-handoff` skills by default.

## Quick Install From Repo URL

If you are not already inside the cloned repo:

```bash
tmpdir=$(mktemp -d)
git clone --depth 1 https://github.com/NA-DEGEN-GIRL/skills.git "$tmpdir/skills"
cd "$tmpdir/skills"
```

Validate before installing:

```bash
make all
```

## Choose What To Install

- If the user is in **Codex** or asks for Codex: install `codex-handoff` only.
- If the user is in **Claude Code** or asks for Claude: install `claude-handoff` only.
- If the user asks for both, install both.
- If the target is unclear, ask one short question: `Codex용, Claude용, 둘 다 중 무엇을 설치할까요?`

## Safe Copy Install Commands

Copy install is safest when this repo was cloned into a temp directory. It backs up any existing same-name install path and does not touch default `handoff`.

### Codex

```bash
src="$PWD/codex-handoff"
dest="${CODEX_HOME:-$HOME/.codex}/skills/codex-handoff"
mkdir -p "$(dirname "$dest")"
if [ -L "$dest" ]; then
  rm "$dest"
elif [ -e "$dest" ]; then
  mv "$dest" "$dest.bak.$(date +%Y%m%d%H%M%S)"
fi
cp -a "$src" "$dest"
```

### Claude Code

```bash
src="$PWD/claude-handoff"
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
# Codex
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -sfn "$PWD/codex-handoff" "${CODEX_HOME:-$HOME/.codex}/skills/codex-handoff"

# Claude Code
mkdir -p "$HOME/.claude/skills"
ln -sfn "$PWD/claude-handoff" "$HOME/.claude/skills/claude-handoff"
```

## After Installing

Tell the user to restart the target agent or open a fresh session so skill metadata is discovered.

Suggested final message:

```text
Installed codex-handoff/claude-handoff. Restart Codex/Claude Code or start a fresh session to pick up the new skill. During trial, explicitly request `codex-handoff` or `claude-handoff` because default `handoff` may still coexist.
```

## Routing Caveat

If the default `handoff` skill is also installed, routing is resolver-defined. For deterministic routing, the user must explicitly request this skill by name or intentionally replace/rename the default after validation.
