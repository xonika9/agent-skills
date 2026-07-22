---
name: x9-research
description: Use when the user wants a genuinely researched answer based on current or primary sources, including what people are saying on X/Twitter or Reddit — «разберись в вопросе», «изучи тему», «что сейчас с…», «собери факты», «посмотри, что пишут в Twitter/Reddit», "research this", "verify this claim". Do not use for library/API documentation (find-docs), product search owned by another skill, personal advice, or questions answerable from stable supplied context.
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

## Deliver in chat or a dossier

- For a quick or narrow question, answer in chat with sources near the claims. Do not create a dossier by default.
- When the user asks to save the research, or repository rules make a durable artifact part of the workflow, create or extend a `docs/research/` dossier under those repository rules.
- Before creating a dossier, inspect existing research folders and search their names and headings. Extend the related dossier instead of creating a new folder for a follow-up to the same decision area.

A research request authorizes gathering and answering, not persistent file creation by itself. When a dossier is authorized, preserve its local format, index, freshness metadata, and update log rather than imposing a new generic template.

## Failure behavior

- Report a failed or cancelled search/tool call; do not fill the gap from memory.
- If the authoritative source is inaccessible, label the claim unverified and state the best next retrieval step.
- If evidence remains mixed, preserve the disagreement and lower confidence.
- If all load-bearing sources are unavailable or the conclusion cannot be checked, return `BLOCKED/NOT_PROVEN`; do not present a memory-based answer as a degraded research result.

## Done

- Every load-bearing current claim traces to a source opened in this run.
- Evidence strength matches claim risk; contradictions and freshness are visible.
- Persistent artifacts were created only with authority.
- X/Twitter or Reddit evidence followed the platform-specific route and sampling limits in `references/sources.md`.
- High-stakes or durable conclusions received a fresh independent check.
