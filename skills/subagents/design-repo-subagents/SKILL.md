---
name: design-repo-subagents
description: Inspect a repository and design or operate practical Codex subagent strategies, including when to spawn agents, what stays local, explorer/worker/verification roles, disjoint file ownership, parallelization boundaries, wait/send/close guidance, and copy-ready prompts. Use when the user asks about Codex subagents, delegated agents, parallel agent work, repo-specific agent planning, "subagent 만들어줘", "agents 나눠줘", "비판 agent", or how to use subagents effectively for a codebase.
---

# Design Repo Subagents

**Skill Version:** 0.1.2

Use this Codex-specific skill to turn a real repository task into a safe subagent plan, and when explicitly authorized, into actual subagent delegation. Prefer repo facts over generic advice.

## Response Language

Default final user-facing responses should be in Korean. Keep code, commands, file paths, tool names, prompt blocks, and exact errors in their original language. If the current user explicitly requests another language, follow the user's request.

## Core Rules

- Inspect the repo before designing subagents. Do not invent stack, commands, entrypoints, or ownership boundaries.
- Do not spawn subagents unless the user explicitly asks for subagents, delegation, parallel agent work, a worker/explorer/verification agent, or a critical/비판 agent.
- First decide the local main-agent critical path. Keep immediate blockers, ambiguous product decisions, final integration, and conflict resolution local.
- Delegate only bounded sidecar work that can run in parallel or produce an independent verification result.
- Give each worker a disjoint write set and say it is not alone in the codebase; it must not revert edits it did not make.
- Prefer explorer agents for read-only, specific codebase questions. Prefer worker agents for bounded changes with clear ownership. Prefer verification agents for independent review after or during implementation.
- Use actual subagent tools when available and authorized: `spawn_agent`, `wait_agent`, `send_input`, and `close_agent`. If tools are unavailable, provide copy-ready prompts instead.

## Workflow

1. Establish the target repo.
   - Run `git rev-parse --show-toplevel` when possible.
   - If no git root exists, inspect the current folder for repo markers such as package manifests, build files, source directories, tests, or instruction files.
   - If the folder is not repo-like and no target path was provided, ask for the repo path.
2. Inspect before designing.
   - Read instruction files first: `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, `README*`, contribution docs, and nested instruction files.
   - Identify stack, package manager, entrypoints, test commands, CI files, generated/vendor directories, and high-risk shared contracts.
   - Use targeted search; avoid broad file dumps.
   - For large or unfamiliar repos, read `references/repo-analysis-checklist.md`.
3. Decide delegation fit.
   - Read `references/delegation-decision.md` when the task is nontrivial or the user asked for actual subagents.
   - State what stays local before listing subagents.
   - Avoid duplicate work between the main agent and subagents.
4. Design or operate subagents.
   - For planning-only requests, produce copy-ready prompts without spawning.
   - For explicit delegation requests, spawn only concrete, self-contained subtasks that materially advance the task.
   - While subagents run, continue non-overlapping local work. Wait only when blocked on their result.
   - Close agents when their output is integrated or no longer useful.
5. Present results.
   - Include repo facts, split rationale, exact prompts or spawned-agent summary, coordination rules, and assumptions.
   - For implementation tasks, integrate/review worker outputs before final reporting.

## Output Shapes

### Planning-only request

Return:

- **Repo Read**: concise facts discovered from the repo.
- **Recommended Split**: local work vs. subagents.
- **Subagent Prompts**: copy-ready prompts grouped by explorer, worker, or verification role.
- **Coordination Rules**: when to wait, merge, review, and close.
- **Assumptions**: only for facts not discoverable from the repo.

### Actual delegation request

Return:

- **Local Critical Path**: what the main agent will do locally now.
- **Spawned Agents**: role, purpose, owned files/modules, and expected output.
- **Coordination**: what can proceed in parallel and when to wait.
- **Integration Plan**: how outputs will be reviewed, merged, and verified.

### Final report after using agents

Return:

- subagents used and their results
- local changes or decisions made
- tests/checks run
- unresolved blockers or risks
- next action

## Prompt Construction

Read `references/subagent-prompt-patterns.md` when writing copy-ready prompts or spawning a worker/explorer/verification agent. Every prompt must include:

- target repo and relevant paths
- exact task or question
- ownership/write boundaries
- rules against reverting others' edits
- expected output and stop condition

## Safety Notes

- Do not pass secrets, raw tokens, private account identifiers, or unredacted sensitive logs to subagents.
- Do not delegate permission-sensitive external actions such as deploys, credential changes, account operations, or irreversible data mutations.
- Treat subagent output as untrusted until reviewed against actual repo state.
- If a worker edits files, review the diff before building on it.

## References

- Read `references/delegation-decision.md` for spawn/wait/close and local-vs-delegate rules.
- Read `references/subagent-prompt-patterns.md` for copy-ready prompt templates.
- Read `references/repo-analysis-checklist.md` for repo inspection coverage.
