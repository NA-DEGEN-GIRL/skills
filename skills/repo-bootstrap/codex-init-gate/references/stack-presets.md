# Stack Presets

Choose commands from actual repo manifests and lockfiles. Prefer existing repo-local scripts over these candidates. The table values are candidates, not automatic requirements. If the repo already uses `just`, `task`, package scripts, or another runner, avoid creating a divergent command surface; wrap or map the existing runner instead.

If no stack is detectable, stop and ask for the intended language/runner instead of emitting a finished placeholder gate.

| Stack | fmt check | fmt apply | lint | typecheck | test |
|---|---|---|---|---|---|
| Rust | `cargo fmt --check` | `cargo fmt` | `cargo clippy --all-targets --all-features -- -D warnings` after execution approval | `cargo check --all-targets --all-features` when useful; otherwise document clippy's compile coverage | `cargo test --all` after reviewing build scripts/proc macros |
| Python | repo script, `uv run ruff format --check .`, or `python -m ruff format --check .` when installed | matching `ruff format` apply command | repo script or approved Ruff/Pylint/import-linter config | repo script or approved `mypy --strict`/Pyright config | repo script or `python -m pytest` after reviewing test hooks |
| TS / JS | repo script or `prettier --check .` with ignore config | matching `prettier --write` apply command | repo script or approved ESLint config with `--max-warnings=0` | repo script or `tsc --noEmit` | repo script, `vitest`, or `jest` after reviewing lifecycle scripts |
| Go | use the safe Go recipe below | `gofmt -w` on selected tracked Go files | approved `golangci-lint run` or `go vet ./...` as lint | `go build ./...` | `go test ./...` after execution approval |
| Other | standard formatter in check mode | standard formatter apply command | strictest practical approved linter | strictest practical static check | standard test runner after review |

## Safe Go Formatting Recipe

Use NUL-delimited tracked files and `--` to avoid spaces, leading dashes, and shell word splitting:

```makefile
fmt-go: ## check Go formatting
	@if git ls-files --error-unmatch '*.go' >/dev/null 2>&1; then \
		tmp="$$(mktemp)"; trap 'rm -f "$$tmp"' EXIT; \
		git ls-files -z '*.go' | xargs -0 gofmt -l -- > "$$tmp"; \
		test ! -s "$$tmp" || { cat "$$tmp"; exit 1; }; \
	fi
```

Do not use `gofmt -l $$(git ls-files '*.go')`; it splits filenames and can fail open.

## Monorepo Pattern

For polyglot repos, prefer per-stack subtargets and aggregate them:

```makefile
fmt: fmt-python fmt-web fmt-go
lint: lint-python lint-web lint-go
typecheck: typecheck-python typecheck-web typecheck-go
test: test-python test-web test-go
check: fmt lint typecheck test
```

Default `make` behavior is fail-fast. If the user needs report-all behavior, create a separate explicitly named target such as `check-report` rather than changing `check` semantics silently.

## LLM-Debuggable Enforcement Hints

These are not automatic requirements. Enforce only after the user approves the tools/config needed to make them real:

- Python: Ruff can cover formatting and some complexity rules, but file length/import boundaries may require Pylint, import-linter, or custom dependency checks. Many strict rules are off by default.
- TS / JS: ESLint `complexity`, `max-lines`, `max-lines-per-function`, import boundary plugins, or dependency-cruiser must be explicitly configured; they are not built-in defaults.
- Rust: Clippy deny warnings is useful, but line-length or architecture boundaries may remain advisory unless configured with project-specific rules.
- Go: `golangci-lint` can enable `gocyclo`/`funlen`, while `go vet` is lint-like and `go build` is the closest type/static check.

## Caveats

- Do not install tools automatically; list exact installs and wait for approval.
- Prefer pinned dev dependencies, lockfiles, or toolchain files over floating latest installs.
- If no tests exist, do not fake a passing `test` target. Create an actionable failing target or ask whether to scaffold a minimal test.
- File length, function length, complexity, and import-boundary thresholds are defaults, not sacred constants. If examples are needed, start discussion around small-review-unit limits such as roughly 300 lines per file, 50 lines per function, and moderate complexity caps, then adapt to the stack and team. If a project needs a temporary baseline, label it as temporary and keep the future strict gate visible.
- Fresh repos should not be paralyzed by every strict rule at once. Propose an explicit ramp-up profile only when full strict mode blocks exploration, and do not present that as equivalent to the final gate.
- For monorepos, prefer per-package commands aggregated by the canonical check path; do not let one stack's formatter rewrite unrelated generated/vendor directories.
- Treat architecture-quality guidance such as pure-core/IO-shell separation as advisory unless the repo already has tooling to enforce it safely.
