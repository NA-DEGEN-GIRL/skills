# MCP Server Instructions

These instructions apply under `mcp-servers/` in addition to the repository
root `AGENTS.md`.

- Put each repository-owned server directly at
  `mcp-servers/<server-name>/` and register it in `catalog.json` only after its
  complete source is present.
- Keep catalog entries minimal and exact: `name`, `source`, `runtime`, and
  `transport`. Do not register external checkouts or placeholder directories.
- MCP packages own their versions and release cadence through their manifests;
  they do not inherit the root skill bundle `VERSION`.
- For Node packages, commit both `package.json` and `package-lock.json`, expose
  the named executable through `bin`, declare the Node engine and test script,
  run `npm ci` for setup, and run `npm test` for package validation.
- Keep package source and entrypoints as real in-tree files and directories;
  do not use symlinks or paths that escape the package.
- Do not commit `node_modules/`, `.env` files, credentials, logs, generated
  prompts/responses, or runtime state. Keep MCP state outside the repository.
- Do not edit a user's MCP client configuration or installed server checkout
  unless the user explicitly asks. Prefer redacted templates with placeholders.
- During migration, keep the standalone source intact until native tests and
  client smoke checks pass; afterward maintain only one writable canonical
  source rather than synchronizing two copies.
- After cloning or changing an MCP lockfile, run `make setup-mcps`; then run
  `make all` before committing or recommending use.
