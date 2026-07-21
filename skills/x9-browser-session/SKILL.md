---
name: x9-browser-session
description: Use when browser work requires choosing between a connector, a local browser, and an existing authenticated session, or when an agent must safely operate the user's logged-in browser - «открой в моём браузере», «используй мою сессию», «поработай в залогиненном браузере», "use my logged-in browser". Do not use for ordinary web research that can be completed with direct HTTP/search tools or for browser implementation details already owned by a project-specific test skill.
---

# Browser session

Use this skill in Claude Code and Codex. It owns the shared route selection, the exact logged-in Edge connection, runtime-specific browser surfaces, and fallbacks. The setup below was verified on 2026-07-21; re-check installed tool instructions and live schemas when a named surface is absent.

## Choose the surface

1. Prefer a purpose-built connector, API, or CLI when it can perform the semantic operation on the linked resource.
2. Use the runtime's local-app browser surface for public pages, visual inspection, and UI testing.
3. Use the dedicated Microsoft Edge automation profile when account state, region, cart, saved data, or private pages matter.
4. Once selected, keep one browser surface through ordinary stale-reference or timeout errors. Switch only when the surface is unavailable or the user changes the requested browser.

## Logged-in Edge

- Profile: `~/Library/Application Support/Microsoft Edge Automation`.
- Launcher: `~/Applications/Edge (Agent).app` with remote-debugging port `9222`.
- Primary: `chrome-devtools` MCP configured with `--browserUrl http://127.0.0.1:9222`.
- Fallback only when that MCP is not attached: `agent-edge`, which wraps `agent-browser --cdp 9222` against the same profile.
- With `chrome-devtools`, call `new_page`, select that page, and operate only there. With `agent-edge`, create a task tab before the first snapshot.
- Leave pre-existing tabs, windows, downloads, bookmarks, and settings untouched.
- Re-snapshot after navigation, filtering, modal changes, and redraws because element references become stale.
- If neither route attaches, launch `Edge (Agent).app` or ask the user to do so, then retry the same surface.

Keep credentials, cookies, tokens, local storage, and private page contents inside the browser session. Read before mutating. Posting, purchasing, sending, deleting, or changing account data still requires authority from the user's request.

## Claude Code

- Local app UI: Claude Preview when available; otherwise headed `agent-browser`.
- Logged-in Edge: use the `chrome-devtools` MCP from `~/.claude.json`.
- If its tools are absent after Edge is running, restart Claude Code before using `agent-edge`.

## Codex

- In-app browser: read and follow the installed `browser:control-in-app-browser` skill. It owns its current initialization and selection APIs.
- Logged-in Edge: use the `chrome-devtools` MCP from `~/.codex/config.toml`.
- If its tools are absent after Edge is running, restart Codex before using `agent-edge`.

## Install the same setup

Read [references/setup.md](references/setup.md) to create the dedicated Edge profile, launcher, MCP entries, and fallback wrapper. Bind CDP to localhost and never commit browser profile contents or credentials.

## Failure behavior

Report cancelled or failed browser calls as failures. Do not substitute remembered data, a public page, or another browser when the task required the authenticated source. Return `DEGRADED` or `BLOCKED` with the failed route and missing prerequisite when the documented retry cannot attach.

## Done

Report the surface used, the task-owned tab or page, the requested result, and any checks that could not be completed. For mutating work, verify the resulting UI state or server response before claiming completion.
