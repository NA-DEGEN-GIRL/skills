# Delegation Decision Guide

Use this guide before spawning or recommending subagents.

## First Decision: Is Spawning Authorized?

Spawn actual subagents only when the user explicitly asks for subagents, delegation, parallel agent work, a worker/explorer/verification agent, or a critical/비판 agent. Otherwise, provide a plan and copy-ready prompts only.

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
- `verification`: independent review of a plan or completed change. Usually read-only.

## Wait / Send / Close

- Do not wait immediately after spawning unless the main path is blocked on the result.
- Continue local non-overlapping work while agents run.
- Use `send_input` only to clarify or redirect an existing related agent; do not create duplicate threads for the same unresolved task.
- Close agents once their result is integrated, rejected, or no longer useful.

## Parallelism Rules

Good parallel splits:

- Multiple independent explorer questions.
- Workers with disjoint directories or modules.
- Verification running while the main agent prepares docs/tests that do not depend on the verification result.

Bad parallel splits:

- Two workers editing the same files.
- Delegating the immediate blocker and then waiting idle.
- Asking multiple agents the same broad question.
- Spawning agents without a concrete expected output.
