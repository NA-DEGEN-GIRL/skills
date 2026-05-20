# llm-router-mcp

`llm-router-mcp` is a local MCP server for asking the LLM CLIs you use most:

- Codex
- Claude
- Grok
- Antigravity (`agy`)

It supports two workflows:

1. Persistent `tmux` sessions for context continuity.
2. Headless one-shot calls for questions that do not need conversation context.

Both workflows use Markdown files for input and output. Persistent sessions use nonce markers so the MCP client can detect when a model starts and finishes without relying on fragile prompt typing.

## Requirements

- Node.js 20+
- tmux
- The desired CLIs installed and logged in:
  - `codex`
  - `claude`
  - `grok`
  - `agy`

## Install

```bash
cd ~/llm-router-mcp
npm install
npm test
```

## Codex MCP Config

Add this to `~/.codex/config.toml`:

```toml
[mcp_servers.llm-router]
command = "node"
args = ["~/llm-router-mcp/bin/llm-router-mcp.js"]

[mcp_servers.llm-router.env]
LLM_ROUTER_MCP_STATE_DIR = "~/.local/state/llm-router-mcp"
```

Restart Codex after changing MCP config.

## Other MCP Clients

The server is a normal stdio MCP server, so it can also be used from Claude,
Grok, Antigravity, or any MCP client that can launch a local command.

JSON-style clients can use:

```json
{
  "mcpServers": {
    "llm-router": {
      "command": "node",
      "args": ["~/llm-router-mcp/bin/llm-router-mcp.js"],
      "env": {
        "LLM_ROUTER_MCP_STATE_DIR": "~/.local/state/llm-router-mcp"
      }
    }
  }
}
```

The machine running this MCP must have the target CLI installed and logged in.
For example, asking Grok through this MCP requires `grok` to be available on the
same PATH used by the MCP process.

## Tools

- `llm_list_providers`
- `llm_write_input`
- `llm_tmux_start`
- `llm_tmux_send`
- `llm_tmux_wait_start`
- `llm_tmux_wait`
- `llm_tmux_ask`
- `llm_headless_ask`
- `llm_tmux_status`
- `llm_tmux_capture`

## Provider Defaults

| Provider | Persistent command | Headless command | Default model behavior |
| --- | --- | --- | --- |
| `codex` | `codex -m gpt-5.4 --ask-for-approval never` | `codex exec -m gpt-5.4 ...` | `gpt-5.4` |
| `claude` | `claude --model sonnet --permission-mode dontAsk` | `claude -p --model sonnet ...` | `sonnet` alias |
| `grok` | `grok --no-alt-screen` | `grok --prompt-file ...` | CLI default/latest |
| `antigravity` | `agy` | `agy --print ...` | CLI default/latest |

Antigravity currently does not expose a known model selection flag in `agy --help`. If you pass `model` for Antigravity, the MCP includes it as a Markdown instruction instead of a CLI flag.

## Security Notes

- Do not commit runtime state. Inputs, generated prompts, raw responses, and
  response Markdown files may contain private project details.
- The default state directory is outside the repo:
  `~/.local/state/llm-router-mcp`.
- `.gitignore` also excludes common local state paths in case the state
  directory is pointed at the project.
- This MCP automates local CLIs. It does not bypass login, permission prompts,
  provider policy, or model-side refusal behavior.
- Persistent tmux sessions preserve conversation context. Use
  `llm_headless_ask` for sensitive one-off questions that should not enter a
  long-lived provider session.
- Before publishing, run a secret scan over tracked files:

```bash
grep -RInEi '(api[_-]?key|token|secret|password|authorization|bearer|oauth|credential|cookie|private[_-]?key)' \
  . --exclude-dir=node_modules --exclude-dir=.git --exclude=package-lock.json
```

## Example Flow

Persistent context:

```text
llm_write_input(provider="claude", markdown="Review this design...")
llm_tmux_ask(provider="claude", inputPath="...")
```

One-shot:

```text
llm_headless_ask(provider="codex", markdown="Give a second opinion on this API.")
```

Specific model:

```text
llm_tmux_ask(provider="codex", model="gpt-5.4", inputPath="...")
llm_headless_ask(provider="claude", model="opus", markdown="...")
```

Provider aliases:

- `agy` and `gemini` route to `antigravity`.
- `gpt` and `openai` route to `codex`.
- `xai` routes to `grok`.

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
