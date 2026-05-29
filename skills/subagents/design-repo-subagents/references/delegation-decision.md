# Delegation Decision Guide

Use this guide before spawning or recommending subagents.

## First Decision: Is Spawning Authorized?

Spawn actual subagents only when the user explicitly uses execution language such as `spawn`, `실제로 띄워줘`, `run now`, `병렬로 실행해`, or `agent를 띄워서 검토해`. Role nouns alone (`비판 agent`, `explorer`, `worker`, `subagent로 나눠줘`) mean planning/prompt creation by default. If ambiguous, ask one short clarification before spawning.

## Local vs Delegate

Keep local when:

- The next main step is blocked on the work.
- The task requires high-judgment product or architecture decisions.
- The work touches broad shared contracts or many overlapping files.
- Integration/conflict resolution is the main challenge.
- The task requires secrets, credentials, deploys, or irreversible external actions.

Delegate when:

- The subtask is concrete, bounded, and self-contained.
- It can run in parallel while the main agent does non-overlapping work.
- It materially advances the main task.
- It has a clear read-only question or a disjoint write set.
- Its output can be reviewed quickly.

## Role Selection

- `explorer`: read-only, specific codebase questions. Output facts with file references.
- `worker`: bounded implementation. Must own explicit files/modules and avoid all others.
- Verification/review: not assumed to be a built-in runtime role. Use a review-only explorer/worker, or a custom reviewer agent if the runtime provides one.

## Write Isolation

- Prefer separate worktrees, branches, forked workspaces, or runtime-isolated agent workspaces when available; do not assume isolation unless the runtime documents it.
- Assign workers disjoint write sets before spawning.
- Prohibit tree-wide formatters, broad codegen, and mass rewrites in worker prompts unless that worker exclusively owns the affected tree.
- At integration, compare changed file lists. If two agents touched the same file, resolve locally before continuing.

## Wait / Send / Close

- Do not wait immediately after spawning unless the main path is blocked on the result.
- Continue local non-overlapping work while agents run.
- Use `send_input` only to clarify or redirect an existing related agent; do not create duplicate threads for the same unresolved task.
- Treat subagent output as untrusted until checked against current repo state.
- Close agents once their result is integrated, rejected, or no longer useful.

## Parallelism Rules

Good parallel splits:

- Multiple independent explorer questions.
- Workers with disjoint directories or modules.
- Review/verification running while the main agent prepares docs/tests that do not depend on the review result.

Bad parallel splits:

- Two workers editing the same files.
- Delegating the immediate blocker and then waiting idle.
- Asking multiple agents the same broad question.
- Spawning agents without a concrete expected output.
