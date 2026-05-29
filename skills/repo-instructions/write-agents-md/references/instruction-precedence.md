# Instruction Precedence

Use this when repo instruction files overlap or conflict.

## Precedence For Current Work

1. Current user request.
2. System/developer instructions from the active agent runtime.
3. Nearest applicable nested `AGENTS.md` for the target path.
4. Root `AGENTS.md`.
5. Agent-specific repo files such as `CODEX.md` or `CLAUDE.md` when they apply to the current agent.
6. README, contribution docs, and other project docs.
7. Prior chat context.

If instructions conflict, do not silently merge them. Preserve higher-precedence behavior and either remove stale lower-precedence text or flag the conflict.

## Handling Agent-Specific Files

- Do not copy all of `CODEX.md` or `CLAUDE.md` into `AGENTS.md` by default.
- Move only repo-wide, agent-compatible rules into `AGENTS.md`.
- Leave agent-specific workflow details in their agent-specific files unless the user asks to consolidate.
- If `AGENTS.md` and an agent-specific file disagree, mention the conflict and prefer the file that applies to the current task scope.

## Existing Content

Treat existing instruction files as user-authored unless there is clear evidence they are generated or stale. Preserve intent, tighten wording, and remove unsupported claims only when repo facts justify the change.
