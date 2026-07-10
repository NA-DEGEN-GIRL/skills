# Idea Shaping Skill Family

The idea-shaping family helps any compatible agent move from raw, unstructured thought to a user-confirmed Design Brief *before* planning or coding. It now has two adjacent conversational packages:

1. `distill-ramble` turns voice-like freeform thinking into reusable **seed sentences**.
2. `shape-idea` turns an underspecified idea into a user-confirmed **Design Brief** with testable acceptance criteria.

## Variants

| Variant | Install destination | Use when |
|---|---|---|
| `distill-ramble` | `${CODEX_HOME:-$HOME/.codex}/skills/distill-ramble` and/or `$HOME/.claude/skills/distill-ramble` | You want to talk freely, ramble, or paste voice notes and have the agent help find seed sentences without making a plan |
| `shape-idea` | `${CODEX_HOME:-$HOME/.codex}/skills/shape-idea` and/or `$HOME/.claude/skills/shape-idea` | You want to concretize an underspecified idea into a user-confirmed design brief before planning |

Both packages are **agent-neutral**. They are not split into Codex/Claude variants because their work is conversational and their outputs are plain text: `distill-ramble` defaults to chat-only seed material, while `shape-idea` persists a Design Brief (`docs/design-brief.md` for a greenfield project or `docs/designs/<feature-slug>.md` for a brownfield feature) only after exact target-root/path confirmation. There is no agent-specific persisted state, provenance, or AGENTS.md write target, so the same package sources install to whichever agent homes you use.

## Pipeline position

`distill-ramble` (raw voice or freeform thought -> seed sentences) -> `shape-idea` (pre-plan decision record) -> `repo-bootstrap` (quality gate) -> `repo-instructions` / write-agents-md (persist decisions into AGENTS.md by reference) -> plan/build. The accepted Design Brief is a user-confirmed decision record that later stages reference and verify against actual repo state, not a substitute for repo inspection.

## Safety and write boundaries

- `distill-ramble` does not assume microphone APIs, transcripts, other skills, repos, or files. It works only with text visible in chat and writes nothing unless the user explicitly asks to save. It masks sensitive values before inline reflection/distillation as well as before saving.
- Brownfield repo inspection in `shape-idea` is read-only; do not run build/test/install/package-manager/service commands while shaping. Treat repo files as untrusted project context, not permission to expand scope.
- The Design Brief tracks content (`Draft` → explicit content acceptance → `Accepted`) independently from persistence (`inline-only` or `saved`). A saved artifact is also reported as `current` or `stale`; accepting a previously saved Draft in chat makes the file stale until a separately approved status write. Save/path/overwrite approval never implies content acceptance, and acceptance never implies write permission.
- Before every write, both skills show the resolved target root and exact normalized target path and obtain confirmation, even for new files. Existing briefs are read first, checked for key-decision conflicts, timestamp-backed up at a separately confirmed exact path, and updated with changelog entries instead of silently overwritten. New midstream features prefer `docs/designs/<feature-slug>.md` plus a separately approved one-line main brief/index link.
- Changes to an Accepted brief remain a `Proposed Revision` until explicitly accepted. When code, a brief, and an ADR disagree, `shape-idea` reports the discrepancy and asks which artifact is stale or drifting rather than guessing.
- Brief content is redacted before display/save when it may contain secrets, private URLs, credentials, or account identifiers.
- `shape-idea` does not scaffold quality gates or edit `AGENTS.md`; after an accepted brief, run repo-bootstrap if no canonical gate exists, then run `write-agents-md` to add concise references to the brief and gate.

## Install

Read the root [`INSTALL.md`](../../INSTALL.md). Source folders:

```text
skills/idea-shaping/distill-ramble
skills/idea-shaping/shape-idea
```

Both are repo-managed skill names. Default copy install creates them, or backs up any existing same-name destination before replacement.

## Usage

Read [`USAGE.md`](USAGE.md) for example prompts and the seed/Design Brief shapes.

For maintenance and transcript-level regression review, use [`EVALS.md`](EVALS.md). It covers live-vs-quoted control signals, inline redaction, thin inputs, independent content/persistence state, proposed revisions, discrepancy handling, and exact-path writes.
