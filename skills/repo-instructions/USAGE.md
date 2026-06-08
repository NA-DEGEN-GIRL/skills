# Repo Instructions Skill Usage Examples

This guide shows how to use the installed `write-agents-md` skill.

## Review Existing AGENTS.md

```text
use write-agents-md
현재 repo의 AGENTS.md를 검토하고, 실제 repo 파일과 모순되거나 불필요한 부분만 지적해줘. 파일은 수정하지 마.
```

## Draft Without Editing

```text
use write-agents-md
이 repo에 맞는 AGENTS.md 초안을 만들어줘. 아직 파일은 쓰지 말고, 확인한 명령과 unverified 명령을 구분해줘.
```

## Create Or Update

```text
use write-agents-md
이 repo의 root AGENTS.md를 실제 Makefile/README/scripts 기준으로 업데이트해줘. 기존 사용자 지침은 보존해.
```

## Nested Instructions

```text
use write-agents-md
packages/api/에 별도 AGENTS.md가 필요한지 판단하고, 필요하면 root와 중복되지 않게 작성해줘.
```

## Good Prompt Hints

- Say whether you want review-only, draft-only, or file edits.
- Mention the target path if you care about a subdirectory.
- Ask the agent to mark commands unverified if it cannot run them.
- Ask for compact output; `AGENTS.md` should be operational, not a long README.

## Design Brief references

If `docs/design-brief.md` or `docs/designs/*.md` exists, `write-agents-md` should reference accepted/current briefs concisely and add a changelog/update rule when relevant; it should not paste the brief's reasoning into `AGENTS.md`.
