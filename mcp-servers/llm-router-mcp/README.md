# llm-router-mcp

`llm-router-mcp` is a local stdio MCP server for asking the LLM CLIs you use
most from one MCP client:

- Codex
- Claude
- Grok
- Antigravity (`agy`)

It supports both persistent provider sessions and isolated one-shot calls.

This package is maintained inside
[`agent-toolkit`](https://github.com/NA-DEGEN-GIRL/agent-toolkit) at
`mcp-servers/llm-router-mcp/` and keeps its own manifest, lockfile, tests, and
release version.

| Workflow | Use it when | Main tool |
| --- | --- | --- |
| Persistent `tmux` session | You want the provider to keep multi-turn context. | `llm_tmux_ask` |
| Headless one-shot | You want an isolated answer that should not enter long-lived context. | `llm_headless_ask` |
| Split send/wait | You want to start a long request and poll or inspect it later. | `llm_tmux_send` + `llm_tmux_wait` |

Both workflows use Markdown files for input and output. Persistent sessions use
nonce markers so the MCP can detect when a model starts and finishes without
relying on fragile prompt typing. The high-level tools handle these markers for
you and return the extracted answer plus response file paths.

## Requirements

- Node.js 20+
- `tmux`
- The desired CLIs installed and logged in on the same machine that launches the
  MCP server:
  - `codex`
  - `claude`
  - `grok`
  - `agy`

## Quick Start

```bash
git clone https://github.com/NA-DEGEN-GIRL/agent-toolkit.git "$HOME/agent-toolkit"
cd "$HOME/agent-toolkit/mcp-servers/llm-router-mcp"
npm ci
npm test
```

`npm test` uses fake provider commands and local `tmux` sessions. It verifies the
MCP server starts, exposes the expected tools, builds provider command lines, and
writes Markdown request and response files. It does not require the real LLM
CLIs to be logged in. Its `pretest` fails fast when `tmux` is unavailable so the
integration coverage cannot pass by being silently skipped.

## Codex MCP Config

Add this to `~/.codex/config.toml`:

```toml
[mcp_servers.llm-router]
command = "node"
args = ["/absolute/path/to/agent-toolkit/mcp-servers/llm-router-mcp/bin/llm-router-mcp.js"]

[mcp_servers.llm-router.env]
LLM_ROUTER_MCP_STATE_DIR = "/home/USER/.local/state/llm-router-mcp"
```

Restart Codex after changing MCP config.

Use real absolute paths in `args` and `LLM_ROUTER_MCP_STATE_DIR`. Keep the state
directory outside the entire `agent-toolkit` checkout. Some MCP clients do not
expand `~` or `$HOME` when they launch a command.

## Other MCP Clients

The server is a normal stdio MCP server, so it can also be used from Claude,
Grok, Antigravity, or any MCP client that can launch a local command.

JSON-style clients can use:

```json
{
  "mcpServers": {
    "llm-router": {
      "command": "node",
      "args": ["/absolute/path/to/agent-toolkit/mcp-servers/llm-router-mcp/bin/llm-router-mcp.js"],
      "env": {
        "LLM_ROUTER_MCP_STATE_DIR": "/home/USER/.local/state/llm-router-mcp"
      }
    }
  }
}
```

The machine running this MCP must have the target CLI installed and logged in.
For example, asking Grok through this MCP requires `grok` to be available on the
same `PATH` used by the MCP process.

## Tools

| Tool | Purpose |
| --- | --- |
| `llm_list_providers` | List supported providers, aliases, default sessions, and model behavior. |
| `llm_write_input` | Write a Markdown prompt into the state directory and return `inputPath`. |
| `llm_headless_ask` | Run one provider once without persistent context. Accepts `markdown` or `inputPath`. |
| `llm_tmux_ask` | Send a Markdown input to a persistent provider session and wait for the final answer. |
| `llm_tmux_start` | Create or reuse a provider `tmux` session. Reuse preserves context. |
| `llm_tmux_send` | Send a Markdown input to a persistent session and return nonce markers. |
| `llm_tmux_wait_start` | Wait until the provider prints the nonce start marker. |
| `llm_tmux_wait` | Wait for the nonce done marker and write the response Markdown file. |
| `llm_tmux_status` | Check whether a session is running and whether a nonce started or completed. |
| `llm_tmux_capture` | Capture recent `tmux` pane text for debugging stuck sessions. |

Tool responses are returned as JSON text. Successful ask calls include the
extracted `answer`, a Markdown `responsePath`, the raw log path, nonce marker
metadata, and timing details. Timed-out `tmux` calls write a fallback Markdown
file so the partial pane output is still inspectable.

## Usage Examples

One-shot request with no persistent context:

```text
llm_headless_ask(
  provider="grok",
  markdown="# Review\n\nGive a second opinion on this API."
)
```

Persistent provider context:

```text
llm_write_input(
  provider="claude",
  filename="design-review.md",
  markdown="# Design Review\n\nReview this plan..."
)

llm_tmux_ask(
  provider="claude",
  inputPath="/path/from/llm_write_input/design-review.md"
)
```

Long-running request with separate send and wait:

```text
llm_tmux_send(provider="codex", inputPath="/path/to/prompt.md")
llm_tmux_wait(provider="codex", nonce="nonce-returned-by-send")
```

Specific model:

```text
llm_tmux_ask(provider="codex", model="gpt-5.4", inputPath="/path/to/prompt.md")
llm_headless_ask(provider="claude", model="opus", markdown="# Task\n\n...")
```

## Provider Behavior

| Provider | Aliases | Persistent command | Headless command | Default model behavior |
| --- | --- | --- | --- | --- |
| `codex` | `gpt`, `openai` | `codex -m gpt-5.4 --ask-for-approval never` | `codex exec -m gpt-5.4 ...` | Uses `gpt-5.4` unless overridden. |
| `claude` | none | `claude --model sonnet --permission-mode dontAsk` | `claude -p --model sonnet ...` | Uses the CLI `sonnet` alias unless overridden. |
| `grok` | `xai` | `grok --no-alt-screen` | `grok --prompt-file ...` | Uses the CLI default/latest unless overridden. |
| `antigravity` | `agy`, `gemini` | `agy` | `agy --print ...` | Uses the CLI default/latest. |

Model names are passed directly to the provider CLI when that CLI exposes a
known model flag. Check the provider's own `--help` output if a model string is
rejected.

Antigravity currently does not expose a known model selection flag in
`agy --help`. If you pass `model` for Antigravity, the MCP includes it as a
Markdown instruction instead of a CLI flag. Antigravity also requires browser
authentication before headless calls can return model output.

`grok --no-alt-screen` is used for persistent sessions so `tmux` pane capture can
see stable text output.

## Runtime State

By default, state is stored under:

```text
~/.local/state/llm-router-mcp
```

It contains:

- `inputs/` Markdown inputs
- `requests/` generated internal prompts
- `responses/` Markdown model outputs and raw logs
- `workdirs/` scratch workdirs for each provider

Runtime state may contain private project details and model responses. Keep it
outside the entire repository checkout and prune it periodically if it grows
large. On a shared machine, protect that directory with permissions appropriate
for private prompts and model output.

## Troubleshooting

**The MCP server does not appear in my client.** Restart the MCP client after
editing config, confirm `node` is available to that client, and check the
client's MCP server logs.

**A provider CLI is not found.** The MCP inherits the `PATH` from the process
that launched it, which can differ from your interactive shell. Use absolute
paths or adjust the launching environment if needed.

**A provider says authentication is required.** Log in with that provider's CLI
outside the MCP first, then retry. This is especially common for fresh
Antigravity CLI installs.

**A persistent session is stuck.** Use `llm_tmux_capture` or attach directly:

```bash
tmux attach -t claude-mcp
```

Then kill and recreate the session if needed:

```bash
tmux kill-session -t claude-mcp
```

**A request timed out.** Check the returned fallback or raw response path. For
long provider runs, prefer `llm_tmux_send` followed by `llm_tmux_wait` with a
larger `timeoutMs`.

## Security Notes

- Run this as a local stdio server for trusted MCP clients, not as a remotely
  exposed or multi-user service.
- This MCP runs local CLIs with the same OS account privileges as the MCP
  client. Those CLIs can read and write whatever that account can access.
- Tool callers can supply Markdown `inputPath` values and override `stateDir`,
  `cwd`, and the persistent-session `command`. A trusted caller can therefore
  read Markdown files, write runtime artifacts, or launch provider commands
  anywhere permitted to the OS account.
- Provider commands use a scratch workdir under the external state directory by
  default. Supplying `cwd` can expose a real project to provider reads and
  writes, so review that override deliberately.
- Do not commit runtime state. Inputs, generated prompts, raw responses, and
  response Markdown files may contain private project details.
- The default state directory is outside the repo:
  `~/.local/state/llm-router-mcp`.
- The package-local `.gitignore` excludes common state paths only when they are
  created inside this package directory. It is defense in depth, not a
  substitute for keeping state outside the complete checkout.
- Some default launcher commands request non-interactive operation with
  `--ask-for-approval never` or `--permission-mode dontAsk`. They do not grant
  privileges beyond the provider CLI's active sandbox and permission policy,
  but you should not expect an interactive confirmation step.
- This MCP does not bypass provider login, provider policy, or model-side
  refusal behavior.
- Persistent `tmux` sessions preserve conversation context. Use
  `llm_headless_ask` for sensitive one-off questions that should not enter a
  long-lived provider session.

Before staging or publishing changes, scan tracked files for accidental secrets:

```bash
grep -RInEi '(api[_-]?key|token|secret|password|authorization|bearer|oauth|credential|cookie|private[_-]?key)' \
  . --exclude-dir=node_modules --exclude-dir=.git --exclude=package-lock.json
```

For history scanning, use a dedicated tool such as
[`trufflehog`](https://github.com/trufflesecurity/trufflehog) or
[`git-secrets`](https://github.com/awslabs/git-secrets).

## Useful Commands

```bash
tmux ls
tmux attach -t codex-mcp
tmux attach -t claude-mcp
tmux attach -t grok-mcp
tmux attach -t antigravity-mcp
```

Kill a session:

```bash
tmux kill-session -t grok-mcp
```
