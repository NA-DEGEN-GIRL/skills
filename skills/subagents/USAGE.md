# Subagents Skill Usage Examples

This guide shows how to use the installed `design-repo-subagents` skill.

## Planning Only

Use this when you want a delegation plan but do not want agents spawned yet.

```text
use design-repo-subagents
이 repo에서 현재 작업을 subagent로 나눌 수 있는지 계획만 짜줘. 실제 spawn은 하지 마.
```

Expected output:

- repo facts discovered from files
- what the main agent should keep local
- explorer/worker/verification prompts
- coordination and wait rules

## Actual Delegation

Use this when you want Codex to spawn agents if the environment supports it.

```text
use design-repo-subagents
비판/review agent와 explorer agent를 실제로 띄워서 병렬로 이 변경 계획을 검토해줘. 로컬 critical path는 네가 유지해.
```

Expected behavior:

1. Inspect the repo and decide what stays local.
2. Spawn only bounded sidecar tasks.
3. Continue non-overlapping local work while agents run.
4. Wait only when their result is needed.
5. Review subagent output before using it.
6. Close agents that are no longer useful.

## Worker Split Example

```text
use design-repo-subagents
이 기능 구현을 worker subagent로 나눠줘. 파일 소유권이 겹치지 않게 하고, 각 worker prompt를 바로 실행 가능하게 써줘.
```

## Verification Example

```text
use design-repo-subagents
현재 패치를 독립 검증할 비판/review 프롬프트를 만들어줘. 실제로 띄울 수 있으면 review-only explorer나 worker를 띄워줘.
```

## Good Prompt Hints

- Say whether you want planning only or actual spawning. Role nouns alone default to planning.
- Mention known target files or modules if you already know them.
- Ask for a critical/비판 agent when you want independent review, not implementation.
- For worker agents, require disjoint file ownership.
