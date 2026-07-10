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
- Commands labeled `documented`, `statically confirmed`, or `executed` (mere inference remains `(unverified)`)
- Conventions, instruction files, and decision docs/Design Briefs
- Recent activity
- Prior-session context (only if a valid handoff snapshot exists)
- Open unknowns

## Leveraging Handoff

Handoff is optional. If a compatible selector is available, orient-repo can choose one relevant default or scoped lane, including a backup-only orphan lane. It never merges lanes. File presence alone does not prove compatibility, and the skill still works fully when no handoff capability or safe snapshot exists.

Without a selector, manual fallback rejects symlinks/path escapes/non-regular files, reads at most 1,048,577 bytes to enforce an exact 1 MiB (1,048,576-byte) limit, and validates UTF-8, NUL absence, and the exact first heading before parsing.

```text
use orient-repo
이 repo 파악하고, handoff snapshot 있으면 이전 세션 맥락도 반영해줘.
```

## Good Prompt Hints

- Say if you only want part of the report (e.g. "just the run/test commands").
- Mention the target path if you are not already inside the repo.
- It marks commands it could not verify as `(unverified)`; ask it to confirm them by reading the relevant config if you need certainty.
- Remote URLs, physical home prefixes, sensitive changed paths, and snapshot summaries are sanitized before display.
