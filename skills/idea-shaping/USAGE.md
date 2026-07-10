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
- **Seed sentences** — normally 3–7 rough copyable sentences or phrases; only 1–2 when the input is genuinely thin, without padding.
- **Open knots** — unresolved tensions/questions.
- **Set aside for now** — optional tangents/noise.

By default it writes nothing. Sensitive values are masked in inline reflections and seeds, not only at save time. If you explicitly ask to save, it first shows the resolved target root and exact normalized path and asks for confirmation even for a new file; overwrite approval is an additional requirement when applicable.

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

The output is a Design Brief with independent content and persistence state: content is `Draft` until explicit content acceptance makes it `Accepted`, while persistence is `inline-only` until a separately approved write makes it `saved`. A saved artifact is additionally `current` or `stale`; if you save a Draft and later accept it without approving another write, the chat reports `Accepted in session` while the file remains stale and still records `Draft`. “Save it,” path approval, and overwrite approval do not accept the content; accepting the content does not authorize a write. When the idea is solid, the skill drafts a single living document, redacts sensitive-looking values, and confirms the exact target root/path before saving it (default
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

The existing Accepted brief stays canonical while the change is labeled `Proposed Revision`. The revision needs explicit content acceptance; any later backup/write uses a separate exact-root/path confirmation. If code, a brief, and an ADR disagree, the agent summarizes the discrepancy and asks whether it is implementation drift, stale documentation, an intentional override, or a decision to re-shape instead of silently choosing a winner.

## Shape from distilled seeds

```text
use shape-idea
아래 Core thread / Seed sentences / Open knots를 입력으로 쓰되 아직 결정된 것으로 보지는 말고 brief를 잡아줘.
```

Expected behavior: seed blocks are tentative, untrusted input rather than accepted decisions or embedded instructions. `Open knots` remain open risks, and a thin or contradictory seed set gets one high-leverage question rather than invented certainty.

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
