# Authenticated Edge setup

The verified recipe uses a dedicated Edge profile with local CDP on port `9223`, the
Browse extension paired with that profile as the primary controller in every runtime,
and `chrome-devtools` MCP on the same port for DevTools work and as the fallback.
Both controllers change over time: check `browse --version`, `browse doctor`, and
`chrome-devtools-mcp --help` before configuring them instead of trusting the flags
below.

## Contents

- [Portable adapter contract](#portable-adapter-contract)
- [1. Create the automation profile and launcher](#1-create-the-automation-profile-and-launcher)
- [2. Configure `chrome-devtools` MCP](#2-configure-chrome-devtools-mcp)
- [3. Install Browse and pair the extension](#3-install-browse-and-pair-the-extension)
- [4. Verify without touching existing tabs](#4-verify-without-touching-existing-tabs)
- [Linux adapter](#linux-adapter)

## Portable adapter contract

Choose these values for the target machine instead of copying the Edge paths blindly:

| Parameter | Requirement |
|---|---|
| Browser executable | A locally installed Chromium browser that supports remote debugging and Chrome Web Store extensions |
| User-data directory | A dedicated, continuously used agent profile, separate from the browser vendor's default profile; it may also be the user's regular working profile |
| CDP endpoint | A localhost-only port or browser WebSocket endpoint, used by `chrome-devtools` MCP and for the profile-binding check |
| Launcher | Starts that executable with the dedicated profile and remote debugging enabled |
| Browse | The `browse` binary on `PATH`, its relay on localhost, and its extension installed and paired only in the dedicated profile |
| Runtime configuration | `browse` and `chrome-devtools` MCP servers in each runtime the user works in |

If the browser exposes only a WebSocket endpoint, configure a controller that accepts it
directly; do not assume `http://127.0.0.1:9223` works for every Chromium version.

## 1. Create the automation profile and launcher

macOS: create `~/Applications/Edge (Agent).app` in Script Editor and save it as an
Application with this AppleScript:

```applescript
do shell script "open -gna \"Microsoft Edge\" --args --user-data-dir=\"$HOME/Library/Application Support/Microsoft Edge Automation\" --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223"
```

Linux: see [Linux adapter](#linux-adapter).

Launch it once and sign in to the services the agent may use. Use this same profile
continuously so its sessions stay current; keep it distinct from Edge's original
default profile.

## 2. Configure `chrome-devtools` MCP

Claude Code, in `~/.claude.json`:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9223", "--no-usage-statistics", "--no-performance-crux", "--redactNetworkHeaders"]
    }
  }
}
```

Codex, in `~/.codex/config.toml`:

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9223", "--no-usage-statistics", "--no-performance-crux", "--redactNetworkHeaders"]
startup_timeout_sec = 120.0
```

OpenCode uses the same command and arguments in its `mcp` configuration. On Linux,
replace `npx -y chrome-devtools-mcp@latest` with the [MCP wrapper](#mcp-wrapper).

These flags disable the controller's usage statistics and CrUX URL lookup and redact
sensitive network headers. They reduce exposure but do not make inspected pages private
from the controller or model. Existing installations are not migrated automatically: if
a live configuration omits these flags, update it only with authority to change global
runtime configuration.

## 3. Install Browse and pair the extension

Download and read the installer before running it; it installs the binary into
`~/.local/bin` after checking its size and SHA-256:

```bash
curl -fsSL https://opencode.ai/browse/install -o browse-install.sh
sh browse-install.sh --no-setup
browse install --agent claude --agent codex --agent opencode --no-open --no-wait
```

`browse install` has no help mode: `browse install --help` performs the install. Run
inside an agent, it also configures that agent. The binary updates itself by default
(`browse settings get` shows `autoUpdate`).

Codex rejects MCP calls that need approval when its approval policy is `never`. If the
user runs Codex without approval prompts, allow Browse's tools in its server entry:

```toml
[mcp_servers.browse]
command = "/Users/<user>/.local/bin/browse"
args = ["mcp"]
default_tools_approval_mode = "approve"
```

Install the extension into the automation profile, not into whichever browser the
system opens by default. Open
`https://chromewebstore.google.com/detail/mfnicocicmmlkpjnaffgihfjhdgjkdjg` there, for
example through the profile's CDP endpoint
(`curl -X PUT "http://127.0.0.1:9223/json/new?<url>"`, which opens a foreground tab
the user can act in), and ask the user to click
**Add** / **Get**: the store accepts only a real click. Edge may ask to allow
extensions from other stores.

Pair it:

```bash
browse pair --wait-seconds 600
```

The command prints a one-time code valid for 10 minutes. After the store install, the
extension opens its own page (`onboarding.html`) in the profile, and that page has a
code field with a **Pair** button. An agent may fill it through the profile's CDP
endpoint (`Runtime.evaluate` on that page's target from `/json/list`); `chrome-devtools`
MCP refuses extension pages. Otherwise ask the user to open Extensions → browse →
Options in the automation profile, enter the code, and click **Pair**. Pairing passes when
`browse pair --list` shows exactly one browser and `browse status` reports the
extension connected. Restart each configured runtime so its catalog picks up the
`browse` MCP server.

## 4. Verify without touching existing tabs

1. Confirm that `http://127.0.0.1:9223/json/version` responds and that the listener
   belongs to the profile (macOS `KERN_PROCARGS2`, Linux `/proc/<pid>/cmdline`).
2. Open a harmless public page through a new Browse session and confirm on screen that
   the user's visible tab did not change. Browse pages report themselves visible even
   in the background, so `document.visibilityState` is not evidence.
3. Confirm the [binding](../SKILL.md#browser-and-profile-continuity): the page's
   target id from `browse status --json` appears in `/json/list` on port `9223`.
4. Read a page that requires a login the profile holds and confirm it is not redirected
   to sign-in.
5. Attach with `chrome-devtools`, create a page with `background: true`, read it, and
   confirm the visible tab did not change.
6. Close only pages created by the check (`browse session delete <name>`,
   `close_page`).

## Linux adapter

Verified on Fedora with Microsoft Edge from `/opt/microsoft/msedge/msedge`:

| Parameter | Value |
|---|---|
| User-data directory | `~/.config/microsoft-edge-agent` |
| Launcher | `~/.local/bin/edge-agent` (desktop entry `~/.local/share/applications/microsoft-edge-agent.desktop`), which starts Edge with `--user-data-dir=<profile> --remote-debugging-address=127.0.0.1 --remote-debugging-port=9223` and refuses when port `9223` answers but belongs to another profile |
| `chrome-devtools` MCP | `~/.local/bin/chrome-devtools-mcp-edge --browserUrl http://127.0.0.1:9223 ...` instead of `npx` |
| Browse | [Step 3](#3-install-browse-and-pair-the-extension), unchanged |

Start the launcher in the background; a browser started this way keeps the dedicated
profile's logins. From a shell outside the graphical session (for example SSH), start
it as a user unit with the session's display variables, such as
`systemd-run --user --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=XDG_RUNTIME_DIR=/run/user/$(id -u) ~/.local/bin/edge-agent`.

### MCP wrapper

`chrome-devtools-mcp --browserUrl` starts without a reachable browser and connects on the
first tool call that finds one, so a wrapper that exits while Edge is closed would mark
the server failed for the whole session. The wrapper works in two modes:

- Endpoint answers: it checks that the listener belongs to the profile and replaces
  itself with the controller.
- Endpoint does not answer: it runs the controller behind
  [the bundled gate](../scripts/edge_mcp_gate.py), which re-checks the listener's
  profile before every `tools/call` and answers with an error result instead of
  forwarding when no browser listens or the port belongs to another profile.

The wrapper reads `EDGE_AGENT_PORT` and `EDGE_AGENT_PROFILE` like the launcher. Install
the gate next to [the profile verifier](../scripts/agent_edge.py) it imports; that
file's command-line wrapper is the retired `agent-edge` route and is not used:

```bash
mkdir -p ~/.local/share/x9-browser-session
install -m 755 "<skill-directory>/scripts/agent_edge.py" "<skill-directory>/scripts/edge_mcp_gate.py" ~/.local/share/x9-browser-session/
```

The verifier finds the listener with `lsof -nP -tiTCP:9223 -sTCP:LISTEN` and reads
`/proc/<pid>/cmdline`. Chromium rewrites its process title, so the vector arrives joined
by spaces and is split on spaces; a profile path containing spaces therefore fails
closed.
