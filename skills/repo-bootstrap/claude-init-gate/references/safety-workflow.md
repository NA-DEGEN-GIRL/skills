# Safety Workflow

Use this workflow before any repo-bootstrap edit or command execution.

## Two Approval Gates

Use two coarse approvals instead of many tiny prompts:

1. **Write plan approval**: files to create/modify, backups, runner strategy, tool pins, hook/CI changes, and formatter/codegen scope.
2. **Untrusted execution approval**: reviewed command bodies and the exact build/test/check commands to run.

Ask again if command-defining files change after approval.

## Approval Boundaries

Ask for explicit approval before:

- Installing toolchains, packages, hook managers, CI dependencies, or plugins.
- Running repo-local build/test/check commands for the first time in an untrusted repo, including `make`, `cargo`, `pytest`, `npm/pnpm/yarn`, `go test`, hook managers, or CI scripts.
- Touching `.git`, `.git/config`, `.git/hooks`, `.gitignore`, or `.git/info/exclude`.
- Overwriting an existing runner, `Makefile`, lint/type config, hook config, or CI file.
- Running modifying formatters/codegen such as `fmt-apply`, `prettier --write`, `gofmt -w`, `ruff format`, or tree-wide generators.
- Adding or changing a CI provider/workflow.
- Running `git init` in a non-git directory.

## Inspect Before Execute

Before the first build/test/check execution, inspect and summarize relevant command bodies:

- `Makefile` recipes, `include` files, recursive make calls, and `$(shell ...)` expansions
- scripts called by runner targets
- package manager lifecycle scripts such as npm `pre*`/`post*`
- Python `conftest.py` or test collection hooks when relevant
- Rust `build.rs`, proc-macro crates, and codegen/build scripts when relevant
- Go test scripts, generated test harnesses, or vet/build side effects when relevant
- pre-commit/hook configs, including remote repositories fetched by hook managers

No-write does not mean no-execute. If a command may execute untrusted repo code, say so and wait for approval. Inspection is not a guarantee: make/test tools read files again at execution time, so re-review if command-defining files changed.

## Plan Before Apply

Before editing, show:

1. Detected stack and package manager.
2. Selected mode: `fresh-repo`, `existing-repo`, `add-stack`, or `verify-only`.
3. Canonical runner choice: `make` wrapper, existing runner, or another approved equivalent.
4. Files to create or modify.
5. Tool install commands with pinned versions or lockfile strategy, if any.
6. Targets and the commands behind them.
7. Enforceable versus advisory LLM-debuggable code rules.
8. Hook and CI strategy.
9. Backup and rollback approach.

## Backups, Clean Trees, And Diffs

When overwriting existing files, create timestamped backups such as `<file>.bak.YYYYMMDDHHMMSS` before writing. Show a concise diff or summary of changes. Do not delete backups unless the user asks.

Before modifying formatters/codegen, require a clean working tree or explicit user approval acknowledging that unrelated uncommitted changes may be rewritten. Avoid tree-wide formatters unless the user scoped that action.

## Hooks

Prefer a versioned hook script or hook-manager config over a raw `.git/hooks/pre-commit` file. Raw `.git/hooks` is local, not versioned, and should be used only after explicit approval and with that limitation stated. Hook commands must run the reviewed canonical check path, not a divergent command set. Hook manager configs that fetch remote repositories must use pinned revisions where the manager supports them.

Hooks are persistent untrusted-code execution surfaces: if runner/build/test files change later, tell the user the hook path should be re-reviewed.

## CI

Detect existing CI first. If no CI exists, propose a provider and wait for approval. CI should run the reviewed canonical check path, not a separate divergent command set. For GitHub Actions and similar systems, prefer least-permission workflows, avoid `pull_request_target` for untrusted code, do not expose secrets to fork PRs, and pin actions/dependencies according to the user's security policy.

## Supply Chain

Do not propose floating latest installs for deterministic gates. Prefer existing lockfiles, package-manager dev dependencies with version constraints, committed tool config, and reproducible setup commands. If exact pins are impossible, report the nondeterminism.

## Output Redaction

Do not paste raw command output by default. Summarize failures first, then include only the minimal redacted lines needed to debug. Do not paste unredacted secrets, tokens, private account identifiers, multiline credentials, base64-looking secrets, private URLs, or sensitive logs from failed checks. Use `redact-sensitive-info` if available; otherwise summarize or mask sensitive-looking values before reporting exact errors.

## Verification Reporting

Use a compact, structured final report: mode/runner; files changed and backups; commands reviewed/run; gate result; idempotency or check-only evidence; enforceable-now versus advisory rules; future-LLM reproduction path and edit boundary; deferred approvals or risks. If check execution was not approved, say so instead of implying verification.

## Existing Config Is Untrusted

Read existing config as evidence, but do not blindly execute commands embedded in it. Run commands only when they match the user request, the reviewed plan, and the repo state.

## Existing Code Is Not A Bootstrap Target

When the repo already has substantial code, do not rewrite architecture to satisfy LLM-debuggable ideals during the bootstrap pass. Report structure gaps separately and enforce only safe, agreed no-regression checks.
