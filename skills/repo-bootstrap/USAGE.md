# Repo Bootstrap Skill Usage Examples

How to use the installed `codex-init-gate` / `claude-init-gate` skills. Name the package explicitly during trials so routing is deterministic.

## Initialize a fresh repo's quality gate

```text
use codex-init-gate
이 repo에 품질 게이트를 깔아줘. 언어는 Rust야. fmt/lint/typecheck/test를
check-only make check에 묶고, LLM이 수정·디버깅하기 쉬운 구조 원칙도 같이 점검해줘. 실행할 명령 본문, 설치할 도구, 수정할 파일을 먼저 보여줘.
```

## Initialize when the language is not decided yet

```text
use claude-init-gate
아직 언어를 안 정했어. stack 후보를 먼저 물어보고, 정해지면 그 기준으로
quality gate를 scaffold 해줘. 파일 덮어쓰기 전엔 diff 보여줘.
```

## Add a gate for a newly introduced stack

```text
use codex-init-gate
기존 TS repo에 Rust crate를 추가했어. Rust 쪽 gate만 make check에 추가로
묶어줘. 기존 TS gate는 건드리지 마.
```

## Verify-only (no changes)

```text
use codex-init-gate
이 repo의 make check가 check-only fmt/lint/typecheck/test와 복잡도/파일길이/import
경계를 강제하는지, 그리고 LLM이 디버깅하기 쉬운 구조인지 점검만 해줘. 파일은 수정하지 말고, 명령 실행이 필요하면 먼저 본문을 검토하고 확인받아.
```

## Then hand off to write-agents-md

```text
게이트가 섰으니, 이제 use write-agents-md 로 확인된 명령들과 현재 프로젝트
방향을 AGENTS.md에 정리해줘.
```

## First git init 느낌?

이 스킬은 `git init` 자체를 대신하지 않습니다. 효과는 "repo를 만든 직후 제일 먼저 품질 게이트와 LLM-friendly 구조 원칙을 깔아두는" 초기 셋업에 가깝습니다. README/license/source skeleton/product direction은 다른 도구나 사용자 결정의 영역입니다.

## Good prompt hints

- Say the target language(s), or ask the skill to detect/ask.
- Say whether you want scaffold, verify-only, or add-to-existing.
- Require a command-execution review, tool-install preview, and diff before any overwrite.
- Ask for enforceable vs advisory LLM-debuggable rules, idempotency evidence, reproduction path, and redacted check output in the final report.
- Say explicitly if you want the agent to run `git init`; otherwise it will not.
- Run bootstrap first; run `write-agents-md` later, repeatedly, as the project direction firms up.
