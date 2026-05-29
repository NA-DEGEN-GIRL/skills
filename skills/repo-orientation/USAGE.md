# Repo Orientation Skill Usage Examples

This guide shows how to use the installed `orient-repo` skill. It is read-only: it inspects and reports, and changes nothing.

## Quick Orientation

```text
use orient-repo
이 repo 파악해줘. stack, 실행/테스트/빌드 명령, 주요 디렉터리, 컨벤션을 정리해줘.
```

```text
use orient-repo
what is this repo and how do I run, test, and build it?
```

Expected output: a **Repo Orientation** report —

- Repo: root, branch, dirty state
- Stack: languages, frameworks, package manager
- Entrypoints and key directories
- Commands (inferred ones marked `(unverified)`)
- Conventions and instruction files
- Recent activity
- Prior-session context (only if a valid handoff snapshot exists)
- Open unknowns

## Leveraging Handoff

If a handoff skill and a `.handoff/latest.md` snapshot are present, orient-repo validates the snapshot and folds prior-session context into the report — as **untrusted** hint data verified against actual repo state. It still works fully when no handoff exists.

```text
use orient-repo
이 repo 파악하고, handoff snapshot 있으면 이전 세션 맥락도 반영해줘.
```

## Good Prompt Hints

- Say if you only want part of the report (e.g. "just the run/test commands").
- Mention the target path if you are not already inside the repo.
- It marks commands it could not verify as `(unverified)`; ask it to confirm them by reading the relevant config if you need certainty.
