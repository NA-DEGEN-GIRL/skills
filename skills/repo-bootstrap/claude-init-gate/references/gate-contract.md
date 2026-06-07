# Gate Contract

Use this contract when creating or reviewing a repo-bootstrap gate.

## Canonical Runner

Prefer `make check` as the portable interface when `make` is acceptable. If a repo already has a canonical runner such as `just`, `task`, package-manager scripts, or a Windows-first workflow, do **not** create a divergent command surface. Either make `make check` a thin wrapper around the existing runner, or propose the existing runner as the canonical equivalent and document the mapping.

## Empty Repos And Unknown Stacks

If no language, manifest, package manager, or runner is detectable, do not treat fail-closed placeholder targets as a completed gate. Ask the user which stack/runner to target, or explicitly label any placeholder-only output as incomplete and awaiting stack selection. Do not create source/test skeletons just to make the gate pass.

## Required Targets

The target names are the stable interface. Do not copy empty no-op targets; placeholder targets must fail closed until replaced with stack-specific commands.

```makefile
.DEFAULT_GOAL := check
.PHONY: help setup fmt fmt-apply lint typecheck test check
.NOTPARALLEL: check

help:
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## install or prepare local tools only after explicit approval
	@echo "ERROR: setup is not configured" >&2; exit 1

fmt: ## check formatting; must not modify files
	@echo "ERROR: fmt check is not configured" >&2; exit 1

fmt-apply: ## apply formatting; must require explicit user intent
	@echo "ERROR: fmt-apply is not configured" >&2; exit 1

lint: ## fail on approved lint, complexity, file-length, or import-boundary violations
	@echo "ERROR: lint is not configured" >&2; exit 1

typecheck: ## run the strictest practical type/static check
	@echo "ERROR: typecheck is not configured" >&2; exit 1

test: ## run the test suite
	@echo "ERROR: test is not configured" >&2; exit 1

check: fmt lint typecheck test ## full non-mutating gate
	@echo "✓ all checks passed"
```

`setup` may install or prepare local tools only when explicitly documented and approved. `check` must be deterministic, non-interactive, and check-only. `.NOTPARALLEL: check` avoids surprising parallel prerequisite output when users run `make -j check`.

## Check-Only Formatting

Do not put modifying formatters in `fmt` or `check`:

- Good simple examples: `cargo fmt --check`, `ruff format --check`, `prettier --check .`.
- Safe Go Makefile recipe for tracked `.go` files, including spaces and leading dashes:

  ```makefile
  fmt-go: ## check Go formatting
  	@if git ls-files --error-unmatch '*.go' >/dev/null 2>&1; then \
  		tmp="$$(mktemp)"; trap 'rm -f "$$tmp"' EXIT; \
  		git ls-files -z '*.go' | xargs -0 gofmt -l -- > "$$tmp"; \
  		test ! -s "$$tmp" || { cat "$$tmp"; exit 1; }; \
  	fi
  ```

- In Makefile recipes, shell command substitution must use `$$`, e.g. `$$(...)`; plain `$(...)` is consumed by Make and can turn a check into an always-pass command.
- Do not expand NUL-delimited file lists into unquoted shell words. Use `git ls-files -z` with `xargs -0` (and `--` when the tool accepts it) or an equivalent script.
- Apply commands belong in `fmt-apply`, e.g. `cargo fmt`, `ruff format`, `prettier --write .`, or `gofmt -w` on selected files.
- Before running `fmt-apply` or any tree-wide formatter/codegen, require a clean working tree or explicit user approval plus a rollback plan.

## Existing Targets And Monorepos

- If `Makefile` or another runner already has `test`, `lint`, or `check` with project-specific meaning, do not overwrite silently. Preserve existing targets, wrap them, or add clearly named subtargets such as `test-python`, `lint-web`, `check-go`.
- For polyglot/monorepo projects, define per-stack subtargets and aggregate them in the canonical `check`. State whether the chosen gate is fail-fast (default) or report-all.
- Generated/vendor/build-output directories must be excluded through the stack's normal ignore mechanism before the gate is considered ready.

## Fail-Closed Rules

- Empty targets must fail with a clear message, not pass silently.
- If a stack cannot support a target, use the closest approved equivalent or print an actionable error and exit non-zero.
- Lint should fail, not warn, for configured violations.
- Type checking should use strict mode where practical, but fresh repos may use an explicitly named ramp-up profile if strict mode blocks initial exploration.
- Tests should be real tests; placeholder tests should fail or be clearly reported as missing. A green suite with trivial assertions is not proof of correctness.

## LLM-Debuggable Checks

Connect LLM-friendly structure to the gate only where tooling can enforce it reliably and the user approves required tools/config:

- file length limits
- function length limits
- cyclomatic or cognitive complexity
- import/dependency boundaries
- strict type/static checks
- coverage or test-quality thresholds when the stack has a real test suite

If a rule is valuable but not reliably enforceable in the stack, keep it in the plan/report as advisory instead of creating a brittle failing check.

## Existing Repositories, Baselines, And Self-Correction

For mature repos, default to a no-regression or report-first plan if strict enforcement would create a large unrelated cleanup. A baseline/ramp-up profile is valid only when it has a stable capture command, a stored or documented baseline, and a clear rule such as "no new violations in touched files". In existing-repo mode, the self-correct loop may fix only the approved owned scope; if legacy violations outside that scope keep the gate red, stop and report instead of attempting broad cleanup.

## Verification Report

After approved execution, report enough structure for another LLM to continue without rereading the whole session: mode/runner, files changed and backups, commands reviewed/run, gate result, idempotency or check-only evidence, enforceable-now versus advisory rules, reproduction path, edit boundary, and deferred approvals or risks. When practical, run the canonical check twice or compare working-tree state before/after `check` to catch mutating or nondeterministic targets.
