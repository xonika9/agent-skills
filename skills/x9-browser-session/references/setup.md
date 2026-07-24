# Authenticated Chromium/CDP setup

Use the portable contract below for any Chromium browser. The Microsoft Edge/macOS
recipe uses a dedicated profile, the Codex browser extension as the Codex primary
outside local web development and explicit in-app requests,
local CDP on port `9222` as the Claude Code primary and Codex fallback, and
`agent-edge` as the last fallback attached to the same profile. The configuration intentionally follows
`chrome-devtools-mcp@latest`; check its live help before configuring it because
supported flags can change.

## Contents

- [Portable adapter contract](#portable-adapter-contract)
- [Verified Microsoft Edge adapter on macOS](#verified-microsoft-edge-adapter-on-macos)
  - [1. Create the automation profile and launcher](#1-create-the-automation-profile-and-launcher)
  - [2. Verify the Codex extension](#2-verify-the-codex-extension)
  - [3. Configure the Claude primary and Codex fallback](#3-configure-the-claude-primary-and-codex-fallback)
  - [4. Add the last-resort wrapper](#4-add-the-last-resort-wrapper)
  - [5. Verify without touching existing tabs](#5-verify-without-touching-existing-tabs)

## Portable adapter contract

Choose these values for the target machine instead of copying the Edge-specific paths blindly:

| Parameter | Requirement |
|---|---|
| Browser executable | A locally installed Chromium browser that supports remote debugging |
| User-data directory | A dedicated, continuously used agent profile, separate from the browser vendor's default profile; it may also be the user's regular working profile |
| Codex extension | The installed extension and its local native host |
| CDP endpoint | A localhost-only port or browser WebSocket endpoint |
| Launcher | Starts that executable with the dedicated profile and remote debugging enabled |
| Codex Edge primary | Outside local web development and explicit in-app requests, uses the Codex extension and creates a session-owned background tab |
| Claude primary / Codex fallback | Attaches to the existing CDP endpoint and creates a background page |
| Last fallback | Attaches to the same endpoint; it must not launch a clean browser |

Before adding runtime configuration, verify that the Codex extension is connected and
that the browser's local CDP discovery endpoint responds. If the browser exposes only a
WebSocket endpoint, configure a controller that accepts that endpoint directly; do not
assume `http://127.0.0.1:9222` works for every Chromium version. Keep the endpoint local,
open a task-owned background page for verification, and close only pages created by the
check.

## Verified Microsoft Edge adapter on macOS

### 1. Create the automation profile and launcher

Create `~/Applications/Edge (Agent).app` in Script Editor and save it as an Application with this AppleScript:

```applescript
do shell script "open -na \"Microsoft Edge\" --args --user-data-dir=\"$HOME/Library/Application Support/Microsoft Edge Automation\" --remote-debugging-port=9222"
```

Launch the app once. Edge creates the profile at:

```text
~/Library/Application Support/Microsoft Edge Automation
```

Sign in to the services the agent may use. Use this same profile continuously so its
sessions stay current. It may be your regular
working Edge profile; keep it distinct from Edge's original default profile.

### 2. Verify the Codex extension

In the Edge Automation profile, verify that the ChatGPT extension can connect to Codex.
Follow Codex's current extension troubleshooting instructions; do not replace them with
copied initialization APIs. The Claude extension is not part of the default Claude Code
route.

The extension verification passes when it can create and operate a task-owned inactive
tab without changing the user's visible tab.

### 3. Configure the Claude primary and Codex fallback

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

### 4. Add the last-resort wrapper

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

### 5. Verify without touching existing tabs

1. Launch `~/Applications/Edge (Agent).app`.
2. For Codex, verify its extension by creating an inactive task tab, navigating it to
   a harmless public URL, and confirming that the user's visible tab does not change.
3. Confirm that `http://127.0.0.1:9222/json/version` responds locally.
4. Attach with `chrome-devtools`, create a page with `background: true`, select it with
   `bringToFront: false`, navigate it, and confirm that the visible tab does not change.
5. Verify `agent-edge` only while the user is not working in Edge; its current
   `tab new` and `tab switch` behavior can foreground the task tab.
6. Close only pages created by the check.

The setup passes when the Codex extension and MCP attach to the same profile, both
complete the read without stealing focus, and all pre-existing tabs remain unchanged.
