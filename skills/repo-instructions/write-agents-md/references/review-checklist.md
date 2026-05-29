# AGENTS.md Review Checklist

Use this checklist before presenting or saving an `AGENTS.md` change.

## Correctness

- Commands exist in package manifests, scripts, CI configs, Makefiles, task files, or docs that match current repo files.
- Test instructions match the repo's actual test layout.
- Style guidance is supported by formatter/linter configs or visible code patterns.
- Nested instruction scopes do not conflict with root instructions.
- The file does not claim a git workflow, deployment process, service dependency, or tool version that was not discovered.
- Unrun but plausible commands are marked unverified.

## Usefulness

- The first screen tells an agent what the project is and how to work on it.
- Sections are short and action-oriented.
- High-risk areas, generated files, migrations, schemas, and public APIs are called out when relevant.
- Subagent guidance is included only if useful or requested.
- Content is operational rather than descriptive marketing.

## Privacy And Safety

- No secrets, tokens, cookies, signed URLs, emails, account identifiers, internal URLs, or private customer data.
- No absolute local home paths with usernames.
- No instructions to run destructive commands by default.
- Explicitly tells agents not to revert user changes.
- Does not tell agents to edit generated/vendor/build artifacts unless the repo requires it.

## Final Pass

- Remove generic advice that would fit any repo.
- Remove unsupported commands.
- Keep the document compact enough to read before editing.
