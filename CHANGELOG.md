# Changelog

This file summarizes repository releases. Installable package folders remain focused on runtime assets; release history stays at the repository root.

## Unreleased

### Repository structure

- Expanded the repository contract from skills-only packaging to a broader local-agent toolkit while preserving the existing `skills/` layout and installer behavior.
- Added a separate `mcp-servers/` catalog and nested maintenance rules so MCP manifests, versions, tests, credentials, and runtime state remain isolated from the skills bundle.
- Added MCP catalog validation to the existing `make all` gate without importing or changing the standalone `llm-router-mcp` source yet.

## 0.1.11 — 2026-07-09

### Safety and installation

- Added the dry-run-first `scripts/install_skill.py` installer, external backup storage, installed-state `doctor`, metadata-validated rollback, duplicate detection, source-tree link/special-file rejection, fixed per-skill mutation locks, and isolated smoke tests.
- Added `skills/catalog.json` as the package/target registry and exact-layout/catalog validation.
- Hardened handoff snapshot selection, validation, saving, path containment, concurrency checks, output redaction, and helper edge cases.
- Extended idea distillation redaction to inline output and made all idea-shaping writes require an explicit root/path confirmation.

### Workflow contracts

- Separated Design Brief content acceptance from persistence state.
- Applied repo-bootstrap gate contracts to the selected canonical runner instead of requiring Make in every repository.
- Split bootstrap repository state from requested operation and clarified allowed ignored cache/build outputs.
- Made subagent behavior follow active runtime capabilities and delegation policy.
- Added safe consolidation/write boundaries for `write-agents-md` and scoped handoff/confidence reporting for `orient-repo`.

### Quality

- Added pinned, least-permission GitHub Actions checks on Python 3.10 and 3.14.
- Added high-risk behavior scenarios under `evals/` and validation that every package is covered.
- Added `make check` as an alias for the historical `make all` gate.

## 0.1.10 — 2026-07-01

- Added `distill-ramble` and tightened `write-agents-md` guardrails while keeping all package versions aligned with the monorepo release marker.
