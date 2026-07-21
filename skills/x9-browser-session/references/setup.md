# Logged-in Edge setup on macOS

This reproduces the browser session used by `x9-browser-session`: a dedicated Microsoft Edge profile, local CDP on port `9222`, `chrome-devtools` as the primary controller, and `agent-edge` as a fallback attached to the same profile.

## 1. Create the automation profile and launcher

Create `~/Applications/Edge (Agent).app` in Script Editor and save it as an Application with this AppleScript:

```applescript
do shell script "open -na \"Microsoft Edge\" --args --user-data-dir=\"$HOME/Library/Application Support/Microsoft Edge Automation\" --remote-debugging-port=9222"
```

Launch the app once. Edge creates the profile at:

```text
~/Library/Application Support/Microsoft Edge Automation
```

Sign in to the services the agent may use. Keep this profile separate from the normal daily profile.

## 2. Configure `chrome-devtools`

Claude Code, in `~/.claude.json`:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222"]
    }
  }
}
```

Codex, in `~/.codex/config.toml`:

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222"]
startup_timeout_sec = 120.0
```

Restart Claude Code or Codex after changing MCP configuration.

## 3. Add the fallback wrapper

Install `agent-browser`, then put this executable script on `PATH` as `agent-edge`:

```bash
#!/usr/bin/env bash
set -euo pipefail

PORT=9222

if ! curl -s -m 3 -o /dev/null "http://127.0.0.1:$PORT/json/version"; then
  echo "Edge (Agent) is not running on port $PORT" >&2
  exit 1
fi

exec agent-browser --cdp "$PORT" "$@"
```

The wrapper must attach to the existing Edge profile. It must not launch a separate Chromium session.

## 4. Verify without touching existing tabs

1. Launch `~/Applications/Edge (Agent).app`.
2. Confirm that `http://127.0.0.1:9222/json/version` responds locally.
3. Attach with `chrome-devtools` and create a new page.
4. Navigate that page to a harmless public URL and take a fresh snapshot.
5. Repeat the read with `agent-edge --session main tab new` and `agent-edge --session main snapshot` only if fallback verification is needed.
6. Close only pages created by the check.

The setup passes when both controllers attach to the same profile and all pre-existing tabs remain unchanged.
