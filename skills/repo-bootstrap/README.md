# Repo Bootstrap

The repo-bootstrap family stands up a repository's **LLM-debuggable enforcement infrastructure** before feature work begins: check-only `fmt` / `lint` / `typecheck` / `test` behind one selected canonical check path (`make check` or the repo's established equivalent), explicit code-structure guidance for future LLM edits, and optional pre-commit/CI wiring after approval.

Primary workflow: **gate-first initialization**. Run once at project start, or again when a new language/stack is added. This family creates *facts* (reviewed tools, pinned or lockfile-backed config, a runnable gate) and records which LLM-friendly structure rules are enforceable vs advisory; it does not write project narrative and it is not a general `git init` replacement.

## Packages

- `codex-init-gate`: Codex package. Uses Codex's edit → run the selected canonical check path → fix loop.
- `claude-init-gate`: Claude Code package. Uses the same gate contract; any Claude Code hook/settings wiring must be confirmed against current docs or user-provided config during planning, before write approval or any related write.

These are intentionally **agent-specific** (handoff-style): the gate core is identical, only the agent self-correct/persistence mechanism differs.

## Pipeline position

Bootstrap is the first stage of a three-stage repo lifecycle:

1. **repo-bootstrap** — create the gate (this family). Infrastructure; rarely changes.
2. **repo-instructions / `write-agents-md`** — document verified facts and the project's evolving direction. Run repeatedly as direction firms up.
3. **repo-orientation / `orient-repo`** — read-only orientation report.

## Safety boundaries

- Existing runner files (including `Makefile`), lint/type config, hooks, and CI files are backed up and diffed for approval before overwrite.
- Repository state (`empty-repo`, `fresh-repo`, `existing-repo`) and requested operation (`scaffold`, `add-stack`, `verify-only`) are independent axes and are both reported.
- The gate contract lives on the selected canonical runner. A `Makefile` is created only when Make is selected or an approved thin wrapper delegates to the repo's established runner.
- Repo-local build/test/check commands are treated as code execution; inspect command bodies and ask before first execution in an untrusted repo.
- Toolchain installs, modifying formatters/codegen, and any `.git`-touching action require explicit approval.
- Check-only means tracked source, tests, config, committed generated files, and lockfiles do not change. Approved ignored caches/build outputs may be created, and must be disclosed with before/after evidence; modifying formatters belong in `fmt-apply` or equivalent.
- Prefer frozen/locked dependency resolution and offline/no-network checks where supported. Any unavoidable fetch is a separately disclosed and approved install/network action.
- LLM-friendly structure rules are advisory unless the chosen stack/tooling can enforce them safely, such as file/function length, complexity, import boundaries, and strict types.
- Advisory rules remain in the report by default. Durable guidance requires a separately approved destination or a handoff to `write-agents-md`; it is not silently persisted in runner config.
- Empty repos with no detectable stack ask for language/runner selection instead of claiming placeholder targets are complete.
- Existing repos default to report-first/no-regression if strict enforcement would cause broad unrelated cleanup.
- Final reports include `repo_state` / `operation` / runner, files changed, commands reviewed/run, gate result, tracked before/after and idempotency evidence, approved ignored outputs, enforceable/advisory rules, reproduction path, and deferred risks.
- Pre-existing config is treated as untrusted data, never executed blindly. Command output is redacted or summarized before reporting sensitive-looking values.

## Validate

From the repo root:

```bash
make all
```

For behavioral regression review beyond literal/sync validation, use [`EVALS.md`](EVALS.md). It covers independent state/operation classification, non-Make runners, tracked-state evidence, frozen/offline behavior, advisory handoff, and pre-write Claude hook confirmation.
