# LLM-Debuggable Code

Use these principles when repo-bootstrap is asked to create or review a gate for code that future LLMs should safely edit and debug.

## Goal

Start the repo so an LLM can quickly answer three questions:

1. What boundary should I edit?
2. How do I reproduce the failure safely?
3. How do I know the fix is correct?

The gate can strongly support question 3 and partially support questions 1 and 2. Be honest when a property is advisory rather than mechanically enforced.

## Structure Principles

- Keep files and functions small enough to inspect in one pass.
- Separate domain/core logic from IO, CLI, API, database, network, and framework adapters.
- Push side effects to explicit boundaries; keep core logic deterministic where practical.
- Use clear module names that describe responsibility; avoid vague buckets like `utils` unless genuinely generic.
- Keep import boundaries simple and intentional; avoid circular imports and cross-layer shortcuts.
- Prefer explicit parameters or dependency injection over hidden globals when it improves testability.

## Debuggability Principles

- Keep one canonical reproduction path: `make check` or an explicitly chosen equivalent, plus clear individual targets for narrower failures.
- Treat build/test/check commands as code execution. Review command bodies and ask before first execution in an untrusted repo.
- Prefer deterministic tests, fixtures, and seeds over timing/network/order-dependent tests.
- Make errors actionable: include the failing input/operation and the next likely debug step without leaking secrets.
- Redact or summarize sensitive-looking command output before reporting exact errors.
- Report generated/vendor/cache directories so agents do not edit them by mistake; defer durable repo docs to `write-agents-md` unless the user asks.

## Potentially Enforceable vs Advisory

Potentially enforce only when the repo already has, or the user approves installing, reliable tooling:

- file length limits
- function length limits
- cyclomatic or cognitive complexity
- import boundaries or dependency rules
- strict type/static checks
- coverage or test-quality thresholds

Keep as advisory unless the repo has reliable tooling:

- pure-core/IO-shell architecture
- module naming quality
- log usefulness
- fixture design
- hidden global state

## Fresh Repos

For a fresh repo with a detectable or user-selected stack, propose a minimal structure that makes edit boundaries obvious, for example a core/domain area, an adapter/IO area, and tests. If no stack/runner is detectable, ask first; do not present fail-closed placeholders as a completed LLM-debuggable setup. Do not create directories, source files, test skeletons, README/license text, or business architecture unless the user explicitly requests scaffolding beyond the gate.

## Existing Repos

For an existing repo, do not force a broad architecture cleanup. Report LLM-debuggability gaps as:

- `enforced now`: already covered by an approved gate
- `can enforce after approval`: needs tool/config install or a new rule
- `recommended`: useful but not automatically enforced
- `defer`: too broad or risky for the bootstrap pass
