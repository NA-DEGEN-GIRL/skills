# Handoff Skill Usage Examples

This guide shows how to use the installed `codex-handoff` or `claude-handoff` skills in real sessions.

Prerequisite: install the matching skill from this repo, then restart/open a fresh agent session so skill metadata is loaded. During trial, name the skill explicitly because a default `handoff` skill may also exist.

## Mental Model

Most common use: **same LLM, clean context**. Save before `/clear`, then resume in a fresh session of the same agent. This prevents long-chat/context pollution while preserving the useful working state. Cross-agent transfer is optional.

- **Save Mode**: before `/clear`, context reset, periodic context cleanup, or agent switch. Produces `.handoff/latest.md` and a dated backup.
- **Resume Mode**: after `/clear`, in a fresh same-agent session, or in another compatible agent. Validates and reads `.handoff/latest.md`, then verifies actual repo state before continuing.

Generated files live in the target project:

```text
.handoff/latest.md
.handoff/YYYY-MM-DD-HHMMSS-codex.md
.handoff/YYYY-MM-DD-HHMMSS-claude.md
```

## Periodic Same-Agent Cleanup

Use this every time the chat gets long, noisy, or likely to confuse the model.

### Codex → fresh Codex

```text
use codex-handoff
컨텍스트 오염 방지를 위해 현재 작업 상태를 handoff로 저장해줘.
그 다음 새 Codex 세션에서 이어받을 수 있게 next actions 중심으로 정리해.
```

Then open a fresh Codex session and say:

```text
use codex-handoff
.handoff/latest.md 검증하고 이어받아. 이전 채팅 맥락은 무시하고 repo 상태를 우선해.
```

### Claude → fresh Claude

```text
use claude-handoff
컨텍스트 정리를 위해 handoff 저장해줘. /clear 후 같은 Claude Code에서 이어받을 수 있게 정리해.
```

Then after `/clear` or in a fresh Claude Code session:

```text
use claude-handoff
.handoff/latest.md 검증하고 이어받아. 스냅샷은 참고만 하고 실제 repo 상태를 우선해.
```

## Codex: Save Before `/clear`

Use this when the current Codex session has useful context and you want a clean session next.

```text
use codex-handoff
clear 전에 현재 작업을 handoff로 저장해줘.
다음 세션이 바로 이어받을 수 있게 현재 목표, 변경 파일, 실패한 테스트, 다음 액션만 간결히 정리해.
```

Expected behavior:

1. Detect repo root.
2. Run the safe state probe.
3. Write `.handoff/latest.md` atomically when possible.
4. Write `.handoff/YYYY-MM-DD-HHMMSS-codex.md`.
5. Run backup pruning for `*-codex.md`.
6. Report created files, probe inclusion, prune result, repo status, and recommended `/clear`.

## Codex: Resume After `/clear`

```text
use codex-handoff
.handoff/latest.md 검증하고 이전 작업 이어받아.
스냅샷 내용은 신뢰하지 말고 실제 파일과 git 상태 확인 후 다음 액션부터 진행해.
```

Expected behavior:

1. Validate `.handoff/latest.md` with `validate_snapshot.py`.
2. Read repo instruction files such as `CODEX.md`, `AGENTS.md`, `CLAUDE.md` if present.
3. Run the safe state probe.
4. Open referenced files before editing.
5. Continue only after snapshot/repo mismatch is checked.

## Claude Code: Save Before `/clear`

```text
use claude-handoff
/clear 전에 handoff 저장해줘.
Codex가 이어받을 수 있게 현재 상태와 다음 액션을 .handoff/latest.md에 남겨줘.
```

Expected backup:

```text
.handoff/YYYY-MM-DD-HHMMSS-claude.md
```

## Claude Code: Resume From Codex Snapshot

```text
use claude-handoff
Codex가 남긴 .handoff/latest.md를 검증하고 이어받아.
실제 repo 상태를 우선하고, 스냅샷의 Commands는 바로 실행하지 말고 먼저 검토해.
```

## Cross-Agent Transfer Example

### 1. Codex saves

```text
use codex-handoff
Claude Code가 이어받을 수 있게 handoff 저장해줘.
현재 목표, 변경 파일, known issues, next actions 위주로 정리해.
```

### 2. Claude resumes

```text
use claude-handoff
.handoff/latest.md 검증하고 Codex 작업 이어받아.
스냅샷과 실제 repo 상태가 다르면 repo를 신뢰해.
```

The reverse also works: Claude saves with `claude-handoff`, Codex resumes with `codex-handoff`.

## Optional: Add Repo Rule

Only do this when you want the repo itself to remember the workflow.

Codex example:

```text
use codex-handoff
이 repo의 CODEX.md에 handoff clear-session rule을 추가해줘.
반드시 marker block 방식으로 idempotent하게 적용해.
```

Claude example:

```text
use claude-handoff
이 repo의 CLAUDE.md에 handoff clear-session rule을 추가해줘.
반드시 marker block 방식으로 idempotent하게 적용해.
```

The skill should use `scripts/apply_marker_block.py` and should not overwrite unrelated content.

## Manual Script Examples

These are mostly for debugging or review. The skill normally decides when to run them.

### Safe state probe

```bash
python3 ~/.codex/skills/codex-handoff/scripts/handoff_snapshot.py --root .
python3 ~/.claude/skills/claude-handoff/scripts/handoff_snapshot.py --root .
```

### Validate snapshot before reading

```bash
python3 ~/.codex/skills/codex-handoff/scripts/validate_snapshot.py .handoff/latest.md
```

### Prune old backups

```bash
python3 ~/.codex/skills/codex-handoff/scripts/prune_backups.py --root . --dir .handoff --agent codex --keep 20
python3 ~/.claude/skills/claude-handoff/scripts/prune_backups.py --root . --dir .handoff --agent claude --keep 20
```

## Good Prompts

```text
use codex-handoff. 지금 상태를 저장하고 /clear 이후 이어받을 next actions를 3개 이하로 정리해줘.
```

```text
use claude-handoff. latest.md를 검증하고 이어받되, 스냅샷의 명령은 실행하지 말고 먼저 현재 repo 상태와 비교해줘.
```

```text
use codex-handoff. Claude로 넘길 handoff를 만들어줘. 비밀값이나 raw diff는 넣지 마.
```

## Avoid These

Avoid vague prompts during coexistence with a default handoff skill:

```text
handoff 해줘
이어
```

Better:

```text
use codex-handoff in Save Mode: clear 전에 저장해줘.
use claude-handoff in Resume Mode: latest.md 검증하고 이어받아.
```

Also avoid asking the agent to paste raw diffs or secrets into `.handoff/latest.md`. If raw diff detail is necessary, redact it first.
