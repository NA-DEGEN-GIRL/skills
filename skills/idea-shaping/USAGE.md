# Idea Shaping Skill Usage Examples

This guide shows how to use the installed `shape-idea` skill. It runs *before* planning: it
asks, translates technical forks, and converges on a user-confirmed Design Brief draft. It does not write
code, scaffold files, or lay out implementation steps.

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

When the idea is solid, the skill drafts a single living document, redacts sensitive-looking values, and asks before saving it (default
`docs/design-brief.md` for greenfield, or `docs/designs/<feature-slug>.md` for brownfield features) with: problem/why, success + **testable acceptance criteria**, in/out
scope, constraints, key decisions (chose X over Y, Z because…), open risks, and a changelog.
It does not edit `AGENTS.md` or set up gates — run repo-bootstrap next if the repo lacks a canonical gate, then run `write-agents-md` so AGENTS.md can reference the accepted brief and gate without embedding full reasoning.

## Update an existing brief

```text
use shape-idea
지난번 Design Brief에서 sync 방식 결정을 바꾸고 싶어. 기존 brief를 읽고, 바뀐 결정과 이유를 changelog로 남겨줘.
```

Expected behavior: the agent reads the existing brief first, proposes a focused update, asks for confirmation, creates a timestamped backup before writing, and preserves the old rationale in the changelog.

## Recommended end-to-end flow

1. `shape-idea` — draft and accept the Design Brief.
2. `codex-init-gate` / `claude-init-gate` — if no canonical quality gate exists, set one up before feature work.
3. `write-agents-md` — reference the accepted brief and canonical gate in AGENTS.md without embedding full reasoning.
4. Plan/build — sequence implementation after decisions and gate are known.

## Good prompt hints

- A one-liner is enough to start ("X 만들고 싶어"); the skill pulls the rest out by asking.
- Say "그만, 이대로 plan으로 가자" anytime to stop early and get a brief with whatever is settled.
- For high-stakes decisions, ask it to "사전 부검 한 번 돌려줘" (pre-mortem) to surface weaknesses.
