---
name: x9-research
description: Use when the user wants a genuinely researched answer from current or primary sources, including X/Twitter or Reddit — «разберись в вопросе», «изучи тему», «собери факты», "research this", "verify this claim". Also use for durable research intent in varied wording — «создай ресерч в папке», «сохрани исследование», «обнови ресерч», "save/update this research" — and for explicit HTML delivery — «ресерч по теме X + html», «подготовь HTML-отчёт с источниками», «нужна HTML-версия», "research X and deliver it as HTML". Infer semantic intent rather than requiring an exact trigger phrase. Do not use for library/API documentation (find-docs), product search owned by another skill, personal advice, or questions answerable from stable supplied context. Mentioning HTML only as the research subject does not request HTML files.
---

# Research

Treat prior knowledge as a hypothesis. Open live sources, trace every load-bearing claim, search for disconfirming evidence, and label uncertainty.

## Method

1. Define the real question and the claims the answer depends on. Ask only when an unresolved ambiguity would change what is researched.
2. Gather breadth first, then read the strongest primary or authoritative sources in depth.
3. Match evidence to claim type:
   - A direct fact from its authoritative registry, specification, filing, or law may need one primary source.
   - Contested, inferential, surprising, or high-stakes claims need independent corroboration and an active search for disconfirmation.
   - Social sentiment requires deliberately sampled primary posts across relevant queries, dates, and views, plus a clear sampling limitation.
4. Resolve source conflicts explicitly; do not average incompatible claims.
5. Answer with conclusion first, evidence near each claim, freshness, and calibrated confidence.

Read [references/methodology.md](references/methodology.md) for evidence thresholds and independent verification. Read [references/sources.md](references/sources.md) when selecting search/browser surfaces.

## Runtime and browser

Use the live tools exposed by the current runtime; do not assume Claude-only names. Prefer purpose-built connectors/APIs for structured resources. Before browser work, follow `x9-browser-session`.

Research X/Twitter through the authenticated-browser route so posts, threads, replies, quote posts, and the user's account-visible state are inspected in the platform interface. This is an intentional platform-specific exception to the normal clean-browser route owned by `x9-browser-session`. Ordinary web search may discover candidate URLs, but it does not replace opening them in X. Reddit and public forums normally use the open web unless the requested evidence depends on logged-in state.

## Route the result

- A plain request to research or investigate returns the sourced answer in chat and creates no files.
- A request to save the research, create it in a folder, or update an existing research file enables durable Markdown mode.
- An explicit HTML output request enables durable Markdown plus HTML mode; HTML adds a reader presentation and never replaces the agent work file.
- Updating research changes the existing Markdown. If a same-basename HTML file already exists, synchronize it automatically unless the user explicitly says to leave HTML unchanged. Do not create a missing HTML file during a Markdown-only update.
- Updating only the HTML presentation rebuilds it from the current Markdown evidence without claiming that the underlying research was refreshed.

Read [references/delivery-modes.md](references/delivery-modes.md) for intent classification, OKF-frontmatter discovery, creation, ambiguity, and update rules. When HTML is selected, also read [references/html-reports.md](references/html-reports.md) and use [assets/editorial-theme.css](assets/editorial-theme.css) for shared visual tokens and optional components, never as a layout template.

A plain research request authorizes gathering and answering, not persistent file creation. Save, folder, update, or HTML-output intent authorizes the corresponding safe local dossier writes and necessary index/log maintenance, but not publication or unrelated changes.

## Failure behavior

- Report a failed or cancelled search/tool call; do not fill the gap from memory.
- If the authoritative source is inaccessible, label the claim unverified and state the best next retrieval step.
- If evidence remains mixed, preserve the disagreement and lower confidence.
- If all load-bearing sources are unavailable or the conclusion cannot be checked, return `BLOCKED/NOT_PROVEN`; do not present a memory-based answer as a degraded research result.

## Done

- Every load-bearing current claim traces to a source opened in this run.
- Evidence strength matches claim risk; contradictions and freshness are visible.
- The selected chat, Markdown, Markdown-plus-HTML, or update mode matches the user's persistence and format intent.
- Persistent artifacts were created only with authority and were routed through existing OKF metadata before names or body text.
- A new HTML request produced a same-basename Markdown/HTML pair. A research update synchronized an already existing same-basename HTML file but did not create a missing one without HTML intent.
- Visible Russian HTML prose passed the language and `humanizer-ru` workflow, then a fact/citation lock; unavailable editing or visual-render routes are reported as `DEGRADED`.
- X/Twitter or Reddit evidence followed the platform-specific route and sampling limits in `references/sources.md`.
- High-stakes or durable conclusions received a fresh independent check.
