# Authenticated Chromium/CDP setup

Use the portable contract below for any Chromium browser. The Microsoft Edge/macOS recipe uses a dedicated profile, local CDP on port `9222`, `chrome-devtools` as the primary controller, and `agent-edge` as a fallback attached to the same profile. The configuration intentionally follows `chrome-devtools-mcp@latest`; check its live help before configuring it because supported flags can change.

## Portable adapter contract

Choose these values for the target machine instead of copying the Edge-specific paths blindly:

| Parameter | Requirement |
|---|---|
| Browser executable | A locally installed Chromium browser that supports remote debugging |
| User-data directory | A dedicated automation profile, separate from the default daily profile |
| CDP endpoint | A localhost-only port or browser WebSocket endpoint |
| Launcher | Starts that executable with the dedicated profile and remote debugging enabled |
| Primary controller | Attaches to the existing CDP endpoint and can create a new page |
| Fallback controller | Attaches to the same endpoint; it must not launch a clean browser |

Before adding runtime configuration, launch the browser and verify its local CDP discovery endpoint. If the browser exposes only a WebSocket endpoint, configure a controller that accepts that endpoint directly; do not assume `http://127.0.0.1:9222` works for every Chromium version. Keep the endpoint local, open a task-owned page for verification, and close only pages created by the check.

## Verified Microsoft Edge adapter on macOS

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
      "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222", "--no-usage-statistics", "--no-performance-crux", "--redactNetworkHeaders"]
    }
  }
}
```

Codex, in `~/.codex/config.toml`:

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222", "--no-usage-statistics", "--no-performance-crux", "--redactNetworkHeaders"]
startup_timeout_sec = 120.0
```

Restart Claude Code or Codex after changing MCP configuration.

These flags disable the controller's usage statistics and CrUX URL lookup and redact sensitive network headers before returning network data to the client. They reduce exposure but do not make inspected pages private from the controller or model. Use a least-privilege account/profile and avoid opening unrelated private data.

Existing installations are not migrated automatically. If a live Claude Code or Codex configuration omits these flags, update it only with authority to change global runtime configuration, then restart that runtime. Otherwise report the mismatch and keep the browsing result `DEGRADED` for private or authenticated work.

## 3. Add the fallback wrapper

Install `agent-browser`, confirm that its current `--help` includes the required `--cdp` route, and put this executable script on `PATH` as `agent-edge`:

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
