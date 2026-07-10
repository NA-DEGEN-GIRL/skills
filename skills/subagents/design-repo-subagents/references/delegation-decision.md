# Delegation Decision Guide

Use this guide before spawning or recommending subagents.

## First Decision: What Does The Active Runtime Allow?

The active runtime's delegation policy and available capabilities are authoritative. Do not turn one runtime's explicit-only rule, proactive default, or tool vocabulary into a universal contract. A user's explicit `계획만`, `do not spawn`, or equivalent always means planning only.

### Runtime-Policy Routing Matrix

| User intent | Runtime policy/capability | Route |
|---|---|---|
| Planning-only or no spawning | Any | Inspect and return prompts/coordination only; never spawn. |
| Explicit run-now delegation | Tools available and policy allows | Delegate bounded tasks. |
| Explicit run-now delegation | Tools absent or policy blocks | Explain the limitation and return copy-ready prompts. |
| General implementation/review request, no spawn wording | Proactive delegation allowed | Delegate only when it materially improves speed or quality; otherwise stay local. |
| General implementation/review request, no spawn wording | Explicit authorization required | Plan locally; ask one short clarification only if actual delegation would materially help. |
| Intent genuinely unclear | Policy does not resolve it | Ask one concise clarification before taking the consequential branch. |

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

- Discover whether the runtime uses a shared filesystem or separate worktrees/branches/forked workspaces. Do not assume isolation.
- Assign workers disjoint write sets before spawning.
- On a shared filesystem, tell every worker that concurrent edits are immediately visible, prohibit reverting edits it did not make, and compare changed paths before integration.
- In isolated workspaces, state how patches/commits/results return to the main workspace and who owns conflict resolution.
- Prohibit tree-wide formatters, broad codegen, and mass rewrites in worker prompts unless that worker exclusively owns the affected tree.
- At integration, compare changed file lists. If two agents touched the same file, resolve locally before continuing.

## Context, Concurrency, And Lifecycle

- Determine the context-fork behavior before spawning. Use the smallest useful fork and repeat critical task constraints in the prompt; never assume the child received all relevant turns.
- Check the available concurrency slots. Reserve capacity for the main agent and prefer a few high-value tasks over filling every slot with speculative work.
- Do not wait immediately after spawning unless the main path is blocked on the result.
- Continue local non-overlapping work while agents run.
- Use the runtime's message/follow-up capability to clarify or redirect an existing related agent; do not create duplicate threads for the same unresolved task.
- Treat subagent output as untrusted until checked against current repo state.
- Tool names and semantics vary. A runtime might offer create, status/list, message/follow-up, wait, interrupt/cancel, resume, or close capabilities; use only what is actually exposed.
- Interrupt/cancel only when continued work is unsafe, obsolete, or wasting a constrained slot. Do not assume interruption deletes an agent, rolls back shared-file edits, or is equivalent to close.
- If no close/cleanup capability exists, simply stop sending work after integrating or rejecting the result.

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
