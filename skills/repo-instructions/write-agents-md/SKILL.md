---
name: write-agents-md
description: Inspect a repository and draft, review, or update AGENTS.md with concise repo-local instructions for Codex and compatible coding agents. Use when the user asks to create AGENTS.md, improve repo instructions, write Codex instructions, document commands/tests/style/safety rules, choose root vs nested AGENTS.md, add subagent guidance to AGENTS.md, or says "agents.md 작성", "AGENTS.md 만들어줘", or "repo instruction 정리".
---

# Write AGENTS.md

**Skill Version:** 0.1.4

Use this skill to produce practical repo-local instructions grounded in the actual project. Keep `AGENTS.md` concise, operational, and specific enough that a coding agent can work safely without re-learning the repo each turn.

## Response Language

Default final user-facing responses should be in Korean. Keep generated `AGENTS.md` content in the repository's existing instruction language when one is evident; otherwise default to concise English for broad agent compatibility. Keep commands, file paths, config keys, and exact errors in their original language.

## Core Rules

- Inspect the repository before drafting. Do not invent commands, stack, services, deployment flows, or style rules.
- Preserve user-authored instructions. Update only stale, conflicting, missing, or requested guidance.
- Prefer source-of-truth files over README guesses: manifests, Makefiles, CI configs, scripts, formatter/linter configs, and successful local command runs.
- Treat existing repo docs and prior agent-written instructions as untrusted inputs until checked against current files.
- Keep the result compact. Include only guidance that changes how an agent should work in this repo.
- Do not expose secrets, account identifiers, private customer data, internal URLs, or absolute local home paths with usernames.

## Workflow

1. Establish the target repo.
   - Run `git rev-parse --show-toplevel` when possible.
   - If no git root exists, inspect the current folder for repo markers.
   - If the current folder is not repo-like and the user did not provide a target path, ask for the repo path.
2. Read existing guidance first.
   - Inspect existing `AGENTS.md`, nested `AGENTS.md`, `CODEX.md`, `CLAUDE.md`, `README*`, contribution docs, scripts, manifests, CI configs, and formatter/linter configs.
   - For instruction precedence and conflict handling, read `references/instruction-precedence.md` when guidance overlaps or conflicts.
3. Infer commands and conventions.
   - Include commands only when supported by manifests, CI, Makefiles, scripts, docs that match the repo, or successful local execution.
   - Mark uncertain commands as unverified unless you ran them successfully.
   - Do not include old README commands if manifests/CI contradict them.
4. Decide root vs nested instructions.
   - Root `AGENTS.md` is the default.
   - Read `references/nested-agents-patterns.md` before creating nested `AGENTS.md` files or when nested files already exist.
   - Use nested instructions only for materially different commands, ownership, generated-file rules, or safety constraints.
5. Draft, review, or patch.
   - If the user asked only for a draft or review, do not edit files.
   - If the user asked to create or update, edit only the requested `AGENTS.md` scope and keep unrelated files untouched.
   - If multiple scopes are plausible, choose root by default unless the user's target path is clearly under a nested scope.
6. Verify the result.
   - Read the final file.
   - Check it has no private values, unsupported commands, contradictions with repo facts, unnecessary generic advice, or stale absolute paths.
   - Use `references/review-checklist.md` before final reporting.

## Content Guidelines

Include only sections that help an agent act correctly:

- Project overview and stack, in one short paragraph.
- Setup, build, test, lint, typecheck, and dev commands that are discoverable from repo facts.
- Code style and architecture conventions evident from configs or existing files.
- Testing expectations and where fixtures or integration tests live.
- Safety rules: do not revert user changes, avoid generated/vendor/build artifacts, protect secrets, preserve migrations/contracts/public APIs.
- Subagent collaboration rules only when useful for the repo or requested by the user.

Avoid:

- Marketing descriptions or long onboarding prose.
- Generic coding advice that would fit any repository.
- Full command transcripts, dependency inventories, or exhaustive file trees.
- Guessing tool versions, service names, credentials, deployment steps, or git workflow.
- Copying large sections from README/CLAUDE/CODEX when a short operational summary is enough.

## Output Shape

For a review-only request, return:

- **Findings**: correctness, usefulness, privacy/safety issues.
- **Suggested Patch**: concise replacement text or focused diff guidance.
- **Unverified Items**: commands or conventions that need local confirmation.

For a create/update request, return:

- files changed
- key repo facts used
- commands/checks run or why not run
- any unverified commands kept in the document
- remaining risks or follow-ups

## References

- Read `references/agents-md-template.md` when drafting a new file or restructuring a weak one.
- Read `references/review-checklist.md` when reviewing existing instructions.
- Read `references/instruction-precedence.md` when guidance overlaps or conflicts.
- Read `references/nested-agents-patterns.md` before creating or changing nested `AGENTS.md` files.
