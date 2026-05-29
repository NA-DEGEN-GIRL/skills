# Repo Analysis Checklist

Use this checklist to ground a subagent plan in repo facts.

## Project Shape

- Repo root, current branch, and dirty state
- Existing instruction files: `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, nested instructions
- README and contribution docs
- Language and framework markers
- Package manager and lockfiles
- App, library, API, worker, and CLI entrypoints
- Test, lint, typecheck, build, and dev commands
- CI workflow commands and required checks
- Generated, vendored, build-output, and cache directories to avoid

## Work Boundaries

- Files or modules most likely to change
- Shared contracts: APIs, schemas, migrations, public types, prompts, generated interfaces
- Cross-cutting utilities that create merge-conflict risk
- Areas with weak tests or expensive setup
- File ownership that can be made disjoint for worker agents

## Delegation Fit

Good explorer tasks:

- Find the source of a behavior.
- Map an API, schema, or data flow.
- Identify relevant tests and fixtures.
- Compare two implementations.

Good worker tasks:

- Update one component, endpoint, module, or test group.
- Add a narrow feature behind an existing interface.
- Fix a bug with a known reproduction path.
- Refactor a clearly owned slice.

Good verification tasks:

- Review a completed patch for regressions.
- Check edge cases or missing tests in a bounded area.
- Compare implementation against a plan or contract.

Keep local:

- The immediate critical-path blocker.
- Ambiguous product decisions.
- Final integration and conflict resolution.
- Broad architectural choices that depend on multiple outputs.
- Anything involving secrets, credentials, deploys, or irreversible external state.
