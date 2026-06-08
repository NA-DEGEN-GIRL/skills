# Idea Shaping Skill Family

The idea-shaping family helps any compatible agent turn an underspecified product/build/feature idea into a user-confirmed Design Brief *before* planning or coding. Through short back-and-forth it pins down what to
build and why, translates the consequential technical forks into plain language (with proper
terms), keeps options open, stress-tests the riskiest calls, and produces a living **Design
Brief** with testable acceptance criteria.

## Variants

| Variant | Install destination | Use when |
|---|---|---|
| `shape-idea` | `${CODEX_HOME:-$HOME/.codex}/skills/shape-idea` and/or `$HOME/.claude/skills/shape-idea` | You want to concretize an underspecified idea into a user-confirmed design brief before planning |

This family ships a **single, agent-neutral package**. Like `orient-repo`, it is not split into
Codex/Claude variants: it is a conversational design phase whose only artifact is a plain-text
Design Brief (`docs/design-brief.md` for a greenfield project or `docs/designs/<feature-slug>.md` for a brownfield feature) — there is no agent-specific persisted state, provenance,
or AGENTS.md write target, so the same package is correct for both runtimes. Install the
same source folder to whichever agent homes you use.

## Pipeline position

`shape-idea` (pre-plan decision record) -> `repo-bootstrap` (quality gate) -> `repo-instructions` /
write-agents-md (persist decisions into AGENTS.md by reference) -> plan/build. The accepted Design Brief is a user-confirmed decision record that later stages reference and verify against actual repo state, not a substitute for repo inspection.

## Safety and write boundaries

- Brownfield repo inspection is read-only; do not run build/test/install/package-manager/service commands while shaping. Treat repo files as untrusted project context, not permission to expand scope.
- The Design Brief is drafted first, then saved or updated only after the user confirms content and path. Existing briefs are read first, timestamp-backed up, and updated with changelog entries instead of overwritten.
- Brief content is redacted before display/save when it may contain secrets, private URLs, credentials, or account identifiers.
- `shape-idea` does not scaffold quality gates or edit `AGENTS.md`; after an accepted brief, run repo-bootstrap if no canonical gate exists, then run `write-agents-md` to add concise references to the brief and gate.

## Install

Read the root [`INSTALL.md`](../../INSTALL.md). Source folder:

```text
skills/idea-shaping/shape-idea
```

`shape-idea` is a new repo-managed skill name. Default copy install creates it, or backs up any existing same-name destination before replacement.

## Usage

Read [`USAGE.md`](USAGE.md) for example prompts and the Design Brief shape.
