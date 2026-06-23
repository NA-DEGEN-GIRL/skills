# Idea Shaping Skill Usage Examples

This guide shows how to use the idea-shaping family. Use `distill-ramble` when the thought is still voice-like and messy; use `shape-idea` when there is already enough of an idea to start making explicit decisions.

## Distill a voice ramble into seed sentences

```text
use distill-ramble
마이크로 그냥 떠오르는 대로 말할게. 중간중간 질문하면서 핵심 문장으로 정리해줘.
```

```text
use distill-ramble
I want to talk through a messy idea. Don't make a plan yet; help me find the core sentences.
```

Expected behavior: the agent invites free talk, responds in short 2–3 sentence turns, asks one useful question at a time, and avoids forms, MVP checklists, Design Briefs, or implementation plans. When you say “정리해줘”, “여기까지”, or “make this into seeds”, it produces:

- **Core thread** — 1–2 sentences capturing the main through-line.
- **Seed sentences** — 3–7 rough copyable sentences or phrases.
- **Open knots** — unresolved tensions/questions.
- **Set aside for now** — optional tangents/noise.

By default it writes nothing; if you explicitly ask to save, it writes one Markdown distillation file after confirming any overwrite.

## Start shaping an idea

```text
use shape-idea
방송 중 시청자 실시간 투표 받는 작은 웹앱 만들고 싶어. 기술적인 부분은 추천해줘.
```

```text
use shape-idea
help me think through a tool that does X. I'm not sure about the technical choices yet.
```

Expected behavior: the agent reflects back its understanding, asks the single highest-leverage
question (one at a time, not a questionnaire), and where a technical fork actually shapes the
idea it explains each option in plain language **with the proper term**, recommends based on
your scale, and lets you choose.

## Existing repo (brownfield)

```text
use shape-idea
이 repo에 기능 하나 추가하려는데, 먼저 구조 파악하고 같이 설계 정하자.
```

The skill orients on the real repo first (using `orient-repo` if available) with read-only inspection. Repo files such as `AGENTS.md` and existing briefs are treated as untrusted project context: useful for grounding, not authority to override higher-priority instructions or expand scope.

## Output: the Design Brief

The output is a user-confirmed Design Brief. When the idea is solid, the skill drafts a single living document, redacts sensitive-looking values, and asks before saving it (default
`docs/design-brief.md` for greenfield, or `docs/designs/<feature-slug>.md` for brownfield features) with: problem/why, success + **testable acceptance criteria**, in/out
scope, constraints, key decisions (chose X over Y, Z because…), open risks, and a changelog.
It does not edit `AGENTS.md` or set up gates — run repo-bootstrap next if the repo lacks a canonical gate, then run `write-agents-md` so AGENTS.md can reference the accepted brief and gate without embedding full reasoning.

## Add a new idea mid-project

```text
use shape-idea
이미 작업 중인 앱에 팀 초대 기능도 넣고 싶어. 기존 결정이랑 충돌하는지 보고 먼저 정리해줘.
```

Expected behavior: the agent reads existing briefs/decision docs read-only, checks the new idea against accepted/current key decisions, and classifies it as current-scope update, separate feature brief, backlog/out-of-scope, or re-shape of an existing decision. New feature briefs default to `docs/designs/<feature-slug>.md`; the main `docs/design-brief.md` is only updated with an approved one-line index/changelog entry.

## Update an existing brief

```text
use shape-idea
지난번 Design Brief에서 sync 방식 결정을 바꾸고 싶어. 기존 brief를 읽고, 바뀐 결정과 이유를 changelog로 남겨줘.
```

Expected behavior: the agent reads the existing brief first, proposes a focused update, asks for confirmation, creates a timestamped backup before writing, and preserves the old rationale in the changelog.

## Recommended end-to-end flow

1. `distill-ramble` — optional: convert raw voice/freeform thought into seed sentences.
2. `shape-idea` — draft and accept the Design Brief.
3. `codex-init-gate` / `claude-init-gate` — if no canonical quality gate exists, set one up before feature work.
4. `write-agents-md` — reference the accepted brief and canonical gate in AGENTS.md without embedding full reasoning.
5. Plan/build — sequence implementation after decisions and gate are known.

## Good prompt hints

- If the thought is messy, start with `distill-ramble` and say “마이크로 떠드는 걸 seed 문장으로 정리해줘.”
- If the idea is already clear enough to make decisions, start directly with `shape-idea`.
- Say “그만, 이대로 plan으로 가자” anytime to stop `shape-idea` early and get a brief with whatever is settled.
- For high-stakes decisions, ask `shape-idea` to “사전 부검 한 번 돌려줘” (pre-mortem) to surface weaknesses.
