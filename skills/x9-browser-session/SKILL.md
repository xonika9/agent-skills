---
name: x9-browser-session
description: Use when browser work requires choosing between a connector, a local browser, and an existing authenticated session, or when an agent must safely operate the user's logged-in browser - «открой в моём браузере», «используй мою сессию», «поработай в залогиненном браузере», "use my logged-in browser". Do not use for ordinary web research that can be completed with direct HTTP/search tools or for browser implementation details already owned by a project-specific test skill.
---

# Browser session

Use this skill in Claude Code and Codex. It owns shared route selection, a portable authenticated Chromium/CDP contract, the Edge adapter, runtime-specific browser surfaces, and fallbacks. Re-check installed tool instructions and live schemas when a named surface is absent.

## Choose the surface

1. Prefer a purpose-built connector, API, or CLI when it can perform the semantic operation on the linked resource.
2. Use the runtime's local-app browser surface or a clean automation browser for public pages, visual inspection, and UI testing. This is the normal route when the task should not depend on personal state.
3. Use a dedicated authenticated Chromium automation profile for personal automation when account state, region, cart, saved data, personalized feeds, or private pages matter, or when the task-owning skill explicitly requires an authenticated platform interface. This route can produce materially different prices, content, and available actions from a clean browser.
4. Once selected, keep one browser surface through ordinary stale-reference or timeout errors. Switch only when the surface is unavailable or the user changes the requested browser.

The distinction is task state, not browser brand: a clean browser answers “does this public interface work?”, while an authenticated profile answers “what does this account actually see or allow?”. Do not log a clean test browser into personal services merely to avoid selecting the authenticated route.

## Authenticated Chromium over CDP

Treat the browser executable, dedicated user-data directory, localhost CDP endpoint, launcher, primary controller, and fallback controller as adapter parameters. Chrome, Edge, Brave, and other Chromium browsers can use the same contract when they support remote debugging:

- use a dedicated automation profile rather than the user's default live profile;
- bind CDP to localhost and do not expose the endpoint to the network;
- attach controllers to the same existing profile instead of launching a clean browser;
- create a task-owned page or tab and leave existing browser state untouched;
- keep credentials, cookies, tokens, and local storage in the dedicated browser profile rather than copying them into prompts or repository files;
- assume the controller and model can receive inspected page contents and network data; avoid opening unrelated private surfaces, do not capture network headers unless the task requires them, and never echo secret header values into chat, logs, or files.

Do not assume the Edge paths or port below on another machine. Read [references/setup.md](references/setup.md), substitute the local Chromium adapter parameters, and verify the discovery endpoint before browsing.

## Verified Edge adapter

- Profile: `~/Library/Application Support/Microsoft Edge Automation`.
- Launcher: `~/Applications/Edge (Agent).app` with remote-debugging port `9222`.
- Primary: `chrome-devtools` MCP configured with `--browserUrl http://127.0.0.1:9222`.
- Fallback only when that MCP is not attached: `agent-edge`, which wraps `agent-browser --cdp 9222` against the same profile.
- With `chrome-devtools`, call `new_page`, select that page, and operate only there. With `agent-edge`, create a task tab before the first snapshot.
- Leave pre-existing tabs, windows, downloads, bookmarks, and settings untouched.
- Re-snapshot after navigation, filtering, modal changes, and redraws because element references become stale.
- If neither route attaches, launch `Edge (Agent).app` or ask the user to do so, then retry the same surface.

Read before mutating. Posting, purchasing, sending, deleting, or changing account data still requires authority from the user's request.

## Claude Code

- Local app UI: discover and follow the currently installed in-app browser integration when available; otherwise use headed `agent-browser` for clean public-page or UI-test work.
- Logged-in Edge: use the `chrome-devtools` MCP from `~/.claude.json`.
- If its tools are absent after Edge is running, restart Claude Code before using `agent-edge`.

## Codex

- In-app browser: read and follow the installed `browser:control-in-app-browser` skill. It owns its current initialization and selection APIs.
- Logged-in Edge: use the `chrome-devtools` MCP from `~/.codex/config.toml`.
- If its tools are absent after Edge is running, restart Codex before using `agent-edge`.

## Install an adapter

Read [references/setup.md](references/setup.md) for the portable adapter contract and the verified Edge example. Never commit browser profile contents or credentials.

## Failure behavior

Report cancelled or failed browser calls as failures. Do not substitute remembered data, a public page, or another browser when the task required the authenticated source. Return `DEGRADED` or `BLOCKED` with the failed route and missing prerequisite when the documented retry cannot attach.

## Done

Report the surface used, the task-owned tab or page, the requested result, and any checks that could not be completed. For mutating work, verify the resulting UI state or server response before claiming completion.
