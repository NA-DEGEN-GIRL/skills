# MCP Servers

This directory is the repository-owned home for local MCP server packages. It
is intentionally separate from `skills/`: MCP servers keep their own runtime,
manifest, dependency lock, tests, and release version.

The catalog is currently empty because no MCP server source has been imported
into this repository yet. Do not register an external checkout as though it
were repository-owned source. Add a catalog entry only when the complete
package is present here.

## Layout

Each package lives directly under its catalog name:

```text
mcp-servers/
├── catalog.json
└── <server-name>/
    ├── README.md
    ├── package.json
    ├── package-lock.json
    ├── bin/
    ├── src/
    └── test/
```

Schema version 1 entries have exactly four fields:

```json
{
  "name": "example-mcp",
  "source": "mcp-servers/example-mcp",
  "runtime": "node",
  "transport": "stdio"
}
```

- `name` is the package name and direct child directory name.
- `source` is a repository-relative path and must equal
  `mcp-servers/<name>`.
- `runtime` is currently `node`.
- `transport` is currently `stdio`.

Do not duplicate the package version, Node engine, test command, or executable
path in the catalog. Those values are owned by `package.json`; its named `bin`
entry is the MCP entrypoint. Node packages must commit `package-lock.json` so
CI and local setup can use `npm ci` deterministically.

## Validation and Safety

Run the repository gate before committing:

```bash
make all
```

The focused metadata check is:

```bash
python3 scripts/check_mcp_catalog.py
```

Keep `node_modules/`, credentials, generated requests/responses, logs, and MCP
runtime state out of version control. Runtime state and user-specific client
configuration belong outside this repository; commit only reviewed examples or
templates with placeholders.

## Bringing In A Standalone Server

Use a one-time history import, not a permanently synchronized submodule or a
second writable copy:

1. Leave `mcp-servers/<server-name>/` absent until import time.
2. Keep the standalone repository active while the imported copy is tested.
3. Import its history into the direct-child package path and add the catalog
   entry in the same reviewed change.
4. Run `npm ci`, the package's native tests, and `make all`.
5. Update client configuration only after reviewing paths and backups, then
   restart each client and run a smoke check.
6. After the cutover is verified, make this repository the single writable
   canonical source and archive the old repository with a pointer here.

For the planned `llm-router-mcp` migration, keep the standalone repository and
its current client configuration unchanged until those steps are completed.
