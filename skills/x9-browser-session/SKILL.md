---
name: x9-browser-session
description: Use when browser work requires choosing between a connector, a local browser, and an existing authenticated session, or when an agent must safely operate the user's logged-in browser - «открой в моём браузере», «используй мою сессию», «поработай в залогиненном браузере», "use my logged-in browser". Do not use for ordinary web research that can be completed with direct HTTP/search tools or for browser implementation details already owned by a project-specific test skill.
---

# Browser session

Use this skill in Claude Code and Codex. It owns shared route selection, the verified
Edge adapter, runtime-specific extension and in-app surfaces, CDP fallbacks, task-tab
isolation, and focus safety. Re-check installed tool instructions and live schemas when
a named surface is absent.

## `chrome-devtools` MCP allowlist

Targets in this list bypass the browser extension in both runtimes. An entry matches
the exact hostname and its subdomains; do not infer sibling or look-alike domains.

- `avito.ru`

## Avito traffic discipline

Treat one account, browser profile, and public IP as one browsing lane for the whole
parent task. Avito work is sequential even when the rest of the research is delegated:

- appoint one Avito operator; subagents may analyze captured data but must not browse
  `avito.ru` concurrently;
- keep only one Avito navigation, search, or listing load in flight. Prefer one task
  tab; extra tabs may hold queued pages, but interact with only one at a time;
- let the current page finish loading and inspect it before requesting the next page;
  shortlist from search results and reuse captured data instead of repeatedly reopening
  or refreshing listings;
- do not bulk-load listings, paginate rapidly, poll availability, or run retry loops;
- when Avito shows an IP or security-check interstitial that requires no user action,
  keep the same page, controller, and profile. Wait five seconds once without
  reloading, navigating, or initiating another request, then inspect the same page
  again. Continue serial browsing if the requested content is visible;
- if the same interstitial remains on the second inspection, or Avito returns a CAPTCHA
  requiring user action, `429`, timeout, access-denied, or an error page, treat it as
  site throttling rather than a controller failure. Stop Avito requests across the
  parent task, preserve collected results, and return `DEGRADED`; do not switch
  controllers, profiles, agents, or IP addresses to continue;
- resume only when the user requests another check or ordinary access is already
  visibly restored. Perform that check serially through the same browser profile.

## Choose the surface

1. Prefer a purpose-built connector, API, or CLI when it can perform the semantic
   operation. An explicit request to open, inspect, or operate a browser UI overrides
   this preference.
2. When the target hostname matches the [`chrome-devtools` MCP allowlist](#chrome-devtools-mcp-allowlist),
   use MCP against the verified Edge profile. This route overrides the runtime default
   and an explicit in-app selection. If MCP cannot attach or complete the operation,
   continue directly to the `agent-edge` fallback under the shared unattended-Edge
   condition.
3. If the user explicitly requests the runtime's in-app browser, use it immediately.
   That explicit choice is sticky: do not substitute Edge or another browser after an
   authentication or connection failure unless the user approves the switch.
4. For local web development and previews, use the runtime's in-app browser unless the
   user explicitly requests Edge:
   - Codex: its in-app browser;
   - Claude Code: its Browser pane.
5. For every other browser-control task, use the runtime-specific default:
   - Codex: its browser extension in the verified Edge profile;
   - Claude Code: `chrome-devtools` MCP against that Edge profile. Do not use the
     Claude browser extension unless the user explicitly requests it.
6. In Codex, if the extension is unavailable, disconnected, or lacks a required
   DevTools capability, retry its documented recovery once and then use
   `chrome-devtools` MCP against the same Edge profile.
7. If MCP cannot attach or cannot perform the required operation, use `agent-edge`,
   which connects `agent-browser` to the same Edge profile. Because the current
   `agent-browser` brings newly created and selected tabs to the foreground, use this
   fallback only when the user is not simultaneously working in Edge. If that condition
   is unknown and the fallback would require creating or switching tabs, ask one short
   question instead of taking over the window.
8. Once a controller works, keep it through ordinary stale-reference, redraw, and
   timeout errors. Do not alternate controllers on the same task tab.

Outside the allowlist route above, the in-app browser remains the isolated route for an
explicit request and for local web development in both runtimes. It has a separate
profile and does not carry the user's Edge extensions. Use Edge when exact account
state, region, cart, saved data, personalized content, ad blocking, or another installed
extension matters.

## Shared Edge safety

Treat the executable, profile, extensions, localhost CDP endpoint, launcher, and
controllers as adapter parameters. On another machine, substitute and verify them
instead of copying the Edge-specific values below.

- use the dedicated, continuously used automation profile rather than the browser's
  default profile;
- attach every controller to that same existing Edge profile rather than launching a
  clean browser;
- create a task-owned background tab; never assume the user's active tab is the task tab;
- with an extension, use its session-owned logical task tab and leave it inactive;
- with `chrome-devtools`, create the page with `background: true`, select it with
  `bringToFront: false`, and never invoke `Page.bringToFront` or
  `Target.activateTarget`;
- never control one tab through the extension and CDP at the same time;
- keep credentials, cookies, tokens, and local storage in the dedicated browser profile rather than copying them into prompts or repository files;
- assume the controller and model can receive inspected page contents and network data; avoid opening unrelated private surfaces, do not capture network headers unless the task requires them, and never echo secret header values into chat, logs, or files.

Do not run browser-wide HAR or broad network capture in the personal Edge profile. Use
a clean standalone `agent-browser` session for that work.

## Verified Edge adapter

- Profile: `~/Library/Application Support/Microsoft Edge Automation`.
- Launcher: `~/Applications/Edge (Agent).app` with remote-debugging port `9222`.
- Codex primary outside the exceptions in [Choose the surface](#choose-the-surface):
  the ChatGPT browser extension installed in this Edge.
- Claude Code primary outside the local-development exception: `chrome-devtools` MCP.
- Codex MCP route: `chrome-devtools` MCP configured with
  `--browserUrl http://127.0.0.1:9222`.
- Last fallback: `agent-edge`, which wraps `agent-browser --cdp 9222` against the same
  profile.
- Leave pre-existing tabs, windows, downloads, bookmarks, and settings untouched.
- Re-snapshot after navigation, filtering, modal changes, and redraws because element references become stale.
- If an Edge route cannot attach, confirm that `Edge (Agent).app` is running before
  declaring that controller unavailable.

Read before mutating. Posting, purchasing, sending, deleting, or changing account data still requires authority from the user's request.

## Claude Code

- For local web development, previews, and an explicit request for the built-in
  browser, use the Claude Code Browser pane. Read its current tool instructions
  before acting; this exception remains primary for that scope.
- For other browser work, use the `chrome-devtools` MCP from `~/.claude.json` with the
  shared focus-safe rules. Do not initialize or fall back to the Claude browser
  extension unless the user explicitly requests that extension.
- If MCP tools are absent after Edge is running, restart Claude Code once. Use
  `agent-edge` only under the shared unattended-Edge condition.

## Codex

- For local web development, previews, and an explicit request for the in-app browser,
  read and follow `browser:control-in-app-browser` and select its distinct in-app
  binding immediately. This exception remains primary for that scope.
- Except for the allowlist route in [Choose the surface](#choose-the-surface),
  select the Edge extension directly for other browser work. Do not let
  `getDefault()` or `getForUrl()` silently choose the in-app browser. Read and follow
  the installed `chrome:control-chrome` skill; it owns the current setup and extension
  APIs.
- The Codex MCP route uses `~/.codex/config.toml` and the shared focus-safe rules.
  Outside the earlier exceptions, enter it only after the Edge extension remains
  unavailable following its documented troubleshooting.
- If MCP tools are absent after Edge is running, restart Codex once. Use `agent-edge`
  only under the shared unattended-Edge condition.

## Install an adapter

Read [references/setup.md](references/setup.md) for the portable adapter contract and the verified Edge example. Never commit browser profile contents or credentials.

## Failure behavior

For the Avito signals defined in
[Avito traffic discipline](#avito-traffic-discipline), follow that section's stop rule
instead of entering the controller fallback chain.

Report cancelled or failed browser calls as failures. For an implicit/default Edge
selection, use the runtime-specific chain: Codex extension → MCP → `agent-edge`;
Claude Code MCP → `agent-edge`; use the allowlist route defined in
[Choose the surface](#choose-the-surface) instead of the Codex default. For an allowed
explicit in-app choice, do not enter an Edge chain without approval. If an implicitly
selected local-development browser is unavailable, use the runtime's Edge chain and
report the fallback. Do not substitute remembered data or a public page when the task
required the authenticated source. Return `DEGRADED` or `BLOCKED` with the failed route
and missing prerequisite when the permitted chain is exhausted.

## Done

Report the runtime, browser surface, controller, task-owned tab or page, requested
result, and any checks that could not be completed. For mutating work, verify the
resulting UI state or server response before claiming completion.

The [onboarding declaration](references/onboarding.json) is the machine-readable onboarding contract.
