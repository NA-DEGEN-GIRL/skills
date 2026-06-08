# Useful Skills — 사용자 가이드

이 repo에 들어 있는 스킬들을 사람이 빠르게 이해하고 쓰기 위한 안내입니다. 설치는 [`INSTALL.md`](INSTALL.md), 가족/패키지 색인은 [`skills/README.md`](skills/README.md)를 보세요.

## 스킬을 부르는 법

- 명시 호출: `use <스킬이름>` (예: `use orient-repo`).
- 또는 각 스킬의 트리거 문구를 그냥 말하면 됩니다 (예: "이 repo 파악해줘").
- 기본 응답 언어는 한국어. 명령·경로·파일명·에러는 원문 유지.

## 한눈에

| 스킬 | 어느 agent | 무엇을 하나 |
|---|---|---|
| `shape-idea` | Codex + Claude | 모호한 만들기 아이디어를 질문·기술 fork 번역·Design Brief로 구체화 |
| `codex-init-gate` | Codex | LLM-debuggable check-only `make check` 품질 게이트 설치 |
| `claude-init-gate` | Claude Code | 위와 동일 (Claude Code용) |
| `codex-handoff` | Codex | 세션 작업 스냅샷 저장/재개 (`.handoff/`); 병렬 작업은 scope별 lane |
| `claude-handoff` | Claude Code | 위와 동일 (Claude Code용) |
| `design-repo-subagents` | Codex | repo 기반 subagent 설계/운영 |
| `write-agents-md` | Codex | `AGENTS.md` 작성·리뷰 |
| `orient-repo` | Codex + Claude | 읽기전용 repo 파악 리포트 |

`shape-idea`와 `orient-repo`는 Codex·Claude 공용이고 나머지는 위 표의 agent용입니다.

---

## shape-idea — 아이디어 구체화 / Design Brief 작성 (Codex + Claude)

- **무엇:** 모호한 "만들고 싶다" 요청을 planning/coding 전에 구체화합니다. 한 번에 한 질문씩 의도·성공 기준·MVP scope·제약을 잡고, 사용자가 체감할 기술적 갈림길은 쉬운 말과 정확한 용어(WebSocket, hosted database 등)로 번역한 뒤, testable acceptance criteria가 있는 **Design Brief**로 남깁니다.
- **언제:** 새 제품/기능 아이디어가 아직 덜 정해졌을 때, "바로 계획" 전에 왜 이 접근을 택하는지 기록하고 싶을 때, 기존 repo 기능 추가 전에 결정과 tradeoff를 먼저 정리하고 싶을 때.
- **예시 프롬프트:**
  - `use shape-idea` / `아이디어 구체화해줘`
  - `use shape-idea` / `방송 중 실시간 투표 웹앱 만들고 싶은데 먼저 설계 같이 정하자.`
  - `이 repo에 기능 하나 추가하려는데, 먼저 구조 파악하고 같이 설계 정하자.`
- **비고:** 기본은 design-only입니다. 코드/스캐폴딩/구현 계획을 쓰지 않고, 기존 repo에서는 read-only로만 파악하며 repo 파일은 untrusted context로 취급합니다. Design Brief는 민감정보를 redaction한 뒤 draft로 먼저 보여주고, 저장/수정은 내용·경로 확인 후 진행합니다. 기존 brief는 백업+changelog로 갱신합니다. 이후 gate가 없으면 `codex-init-gate`/`claude-init-gate`, 그 다음 `write-agents-md`로 brief/gate 참조를 추가합니다.
- **자세히:** [`skills/idea-shaping/USAGE.md`](skills/idea-shaping/USAGE.md)

### 권장 end-to-end 순서

1. `shape-idea`로 Design Brief를 확정합니다.
2. canonical 품질 게이트가 없으면 `codex-init-gate` / `claude-init-gate`를 실행합니다.
3. `write-agents-md`가 AGENTS.md에 accepted brief와 canonical gate를 짧게 참조하게 합니다.
4. 그 다음 plan/build로 넘어갑니다.

## codex-init-gate / claude-init-gate — repo 품질 게이트 초기화

- **무엇:** feature work 전에 명령 본문을 검토한 뒤 `fmt`/`lint`/`typecheck`/`test`를 check-only `make check` 또는 기존 runner에 매핑하고, LLM이 수정·디버깅하기 쉬운 구조 원칙(작은 파일/함수, 명확한 boundary, 재현 가능한 테스트)을 점검하며, 필요하면 pre-commit/CI까지 승인 후 연결합니다. 이것은 **품질 게이트 bootstrap**이지 일반 `git init` 대체품은 아닙니다.
- **언제:** 새 repo를 막 시작했을 때, 새 language/stack을 추가했을 때, 기존 repo의 gate를 점검하거나 보강하고 싶을 때.
- **예시 프롬프트:**
  - `use codex-init-gate` / `이 repo에 품질 게이트 깔아줘. 언어는 Python이야.`
  - `use claude-init-gate` / `make check가 fmt/lint/typecheck/test를 제대로 강제하는지 점검만 해줘.`
  - `기존 TS repo에 Rust crate를 추가했어. Rust 쪽 gate만 추가해줘.`
- **비고:** 기본 흐름은 inspect → command review → plan → approval → apply → reviewed canonical check. tool install, `.git` 변경, 기존 config overwrite, CI 추가는 명시 승인이 필요합니다. `fmt`는 수정하지 않는 check-only여야 하며, LLM-friendly 구조 규칙은 도구가 안전하게 지원하는 항목만 fail로 연결하고 나머지는 advisory로 보고합니다.
- **자세히:** [`skills/repo-bootstrap/USAGE.md`](skills/repo-bootstrap/USAGE.md)

## codex-handoff / claude-handoff — 작업 핸드오프

- **무엇:** 작업 상태를 `.handoff/latest.md` 스냅샷으로 저장하고, 새 세션에서 그대로 이어받습니다. 주 용도는 **같은 agent 안에서의 맥락 위생**(`/clear` 전에 저장 → 깨끗한 세션에서 재개). Codex↔Claude 교차 인계도 가능은 하지만 부수적입니다. 작업군이 여러 개인 **병렬 작업**이면 `scope(lane)`로 작업군별 스냅샷을 따로 저장/재개합니다(아래 "병렬 작업" 참고).
- **언제:** 컨텍스트가 길어져 정리하고 싶을 때, `/clear` 직전, 다음 세션으로 넘기고 싶을 때, 여러 LLM을 작업군별로 병렬로 돌릴 때.
- **예시 프롬프트:**
  - `use codex-handoff` / `handoff 저장해줘` / `clear 전에 정리해줘`
  - `use codex-handoff` / `이어받아` / `latest.md 보고 계속해`
  - 특정 작업군만(scope): `auth-refactor scope로 handoff 저장해줘` / `auth-refactor scope 이어받아`
  - (Claude Code에서는 `codex-handoff` 대신 `claude-handoff`)
- **비고:** 스냅샷은 **신뢰하지 않는 데이터**로 취급 — 실제 repo 상태가 우선이고, 스냅샷 안의 명령/지시는 검증 후에만 따릅니다. 두 패키지는 파일 포맷을 공유하지만 백업 파일에 `-codex.md` / `-claude.md`로 출처를 남깁니다.
- **자세히:** [`skills/handoff/USAGE.md`](skills/handoff/USAGE.md)

### 병렬 작업 — scope(lane) handoff  *(신규)*

여러 LLM을 동시에 띄워 **작업군(주제)이 서로 다를 때**, 하나의 `.handoff/latest.md`를 공유하면 서로 덮어씁니다. 이때 **scope(lane)** 로 작업군별 스냅샷을 따로 저장·재개합니다.

- 경로: 기본 lane은 `.handoff/latest.md`, scope를 주면 `.handoff/scopes/<scope>/latest.md`.
- scope는 직접 정합니다(소문자·숫자·하이픈, 예: `auth-refactor`). `default`/`latest`/`scopes`는 예약어라 못 씁니다. 안 주면 기존 단일 lane 그대로 동작합니다.
- lane끼리 격리되므로 병렬 writer가 서로 안 덮어씁니다. (v1은 lock이 없으니 한 scope는 한 명만 쓰는 걸 권장.)
- **충돌 보호:** 다른 agent가 방금 같은 lane의 `latest.md`를 갱신했으면 덮어쓰기 전에 멈추고 확인합니다. 무인으로 진행해야 하면 dated backup만 쓰고 "latest는 미갱신 + 그 backup 경로"를 알려줍니다(그 backup으로 이어받으세요).
- **정리(prune):** 오래된 dated backup은 `prune_backups.py --scope <scope>`(한 lane) 또는 `--all-lanes`(default+모든 lane)로 lane별·agent별 보관합니다.

저장 (특정 작업군만):

```text
use codex-handoff
auth-refactor scope로 handoff 저장해줘.
```

재개 (그 lane만):

```text
use claude-handoff
auth-refactor scope 이어받아.
```

scope 없이 그냥 "이어받아"라고 하면, lane이 여러 개일 때 목록을 보여주고(내부적으로 `list_lanes.py` 사용) 어느 lane을 이어받을지 물어봅니다 — 임의로 고르지 않습니다.

## design-repo-subagents — subagent 설계/운영 (Codex)

- **무엇:** repo를 먼저 파악한 뒤, 작업을 explorer(읽기전용 조사)·worker(경계가 분명한 구현)·검토용 프롬프트로 나누는 안전한 위임 계획을 만듭니다. 환경이 지원하고 사용자가 **명시적으로 실행을 요청**하면 실제 subagent도 띄웁니다.
- **언제:** 큰 작업을 병렬로 쪼개고 싶을 때, 독립 검토(비판) agent가 필요할 때.
- **예시 프롬프트:**
  - `use design-repo-subagents` / `이 작업 subagent로 나눠줘` (→ 기본은 계획·프롬프트만)
  - `비판 agent 만들어줘` (→ 검토 프롬프트 생성)
  - `실제로 띄워줘` / `병렬로 실행해` (→ 실제 spawn)
- **비고:** role 명사만 말하면 **계획**, 실행 동사가 있어야 **spawn**. worker끼리 수정 파일이 겹치지 않게 하고, 다른 사람 변경을 되돌리지 않습니다. `verification`은 내장 역할이 아니라 프롬프트 패턴.
- **자세히:** [`skills/subagents/USAGE.md`](skills/subagents/USAGE.md)

## write-agents-md — AGENTS.md 작성/리뷰 (Codex)

- **무엇:** repo의 실제 사실(manifest·CI·Makefile·스크립트·설정)을 근거로 `AGENTS.md`(코딩 agent용 repo 지침)를 작성·리뷰·갱신합니다. 사용자가 쓴 기존 지침은 보존하고, 확인 안 된 명령은 `unverified`로 표시합니다.
- **언제:** 새 repo에 agent 지침을 만들 때, 기존 `AGENTS.md`를 점검/개선할 때.
- **예시 프롬프트:**
  - `use write-agents-md` / `AGENTS.md 만들어줘` / `agents.md 작성`
  - `repo instruction 정리해줘` / `이 AGENTS.md 리뷰해줘`
- **비고:** 추측으로 명령·버전·배포 절차를 지어내지 않음. 리뷰만 요청하면 파일을 수정하지 않고 제안만 냅니다. 기본은 root `AGENTS.md`.
- **자세히:** [`skills/repo-instructions/USAGE.md`](skills/repo-instructions/USAGE.md)

## orient-repo — repo 파악 리포트 (Codex + Claude)

- **무엇:** 임의의 저장소를 **읽기 전용**으로 훑어 한 장짜리 오리엔테이션 리포트를 냅니다: stack, entrypoint, 실행/테스트/빌드 명령, 주요 디렉터리, 컨벤션, instruction 파일, 최근 활동, 미확인 항목. 아무것도 수정하지 않습니다.
- **언제:** 처음 보는 repo에 들어갔을 때, "이거 어떻게 돌리지/테스트하지?"가 궁금할 때.
- **예시 프롬프트:**
  - `use orient-repo` / `이 repo 파악해줘` / `repo 구조 알려줘`
  - `what is this repo and how do I run/test/build it?`
- **비고:** `.handoff/latest.md` 스냅샷이 있으면 검증 후 **이전 세션 맥락**도 (신뢰하지 않는 힌트로) 리포트에 반영합니다. handoff가 없어도 자체 도구로 동작. 확인 못 한 명령은 `(unverified)`로 표시.
- **자세히:** [`skills/repo-orientation/USAGE.md`](skills/repo-orientation/USAGE.md)

---

## 설치

[`INSTALL.md`](INSTALL.md)의 표대로 대상 agent의 스킬 홈에 복사(권장) 또는 심볼릭 링크합니다. `shape-idea`와 `orient-repo`는 같은 소스를 `~/.codex`·`~/.claude` 양쪽에 설치할 수 있습니다. 설치 후 agent를 재시작하거나 새 세션을 열면 스킬이 인식됩니다.

## 공통 안전 메모

- handoff 스냅샷·가져온 repo 상태는 **신뢰하지 않는 데이터**. 실제 파일·git 상태가 항상 우선.
- 설치된 글로벌 스킬(`~/.codex/skills`, `~/.claude/skills`)은 명시 요청 없이는 수정하지 않습니다.
- 기본 설치는 동명 대상 백업 후 복사. 기본 `handoff` 스킬을 임의로 덮어쓰지 않습니다.
