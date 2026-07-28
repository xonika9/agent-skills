---
name: x9-research
description: Use when the user wants a genuinely researched answer from current or primary sources, including X/Twitter or Reddit — «разберись в вопросе», «изучи тему», «собери факты», "research this", "verify this claim". Also use for durable research intent in varied wording — «создай ресерч в папке», «сохрани исследование», «обнови ресерч», "save/update this research" — and for explicit HTML delivery — «ресерч по теме X + html», «подготовь HTML-отчёт с источниками», «нужна HTML-версия», "research X and deliver it as HTML". Infer semantic intent rather than requiring an exact trigger phrase. Do not use for library/API documentation (find-docs), product search owned by another skill, personal advice, or questions answerable from stable supplied context. Mentioning HTML only as the research subject does not request HTML files.
compatibility: Requires Python 3 for deterministic HTML output validation.
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

Read [references/sources.md](references/sources.md) before browser or social research. It owns source selection, platform sampling, and the intentional authenticated-browser exception for X/Twitter; `x9-browser-session` owns controller selection, task-tab isolation, private-surface safety, and browser-route failure.

## Route the result

Return a sourced answer in chat unless the request conveys persistence, update, or HTML-output intent. For any such intent, read [references/delivery-modes.md](references/delivery-modes.md); it owns classification, OKF discovery, artifact lifecycle, authority, ambiguity, and completion. When it selects HTML, also read [references/html-reports.md](references/html-reports.md) and use [assets/editorial-theme.css](assets/editorial-theme.css) for shared visual tokens and optional components, never as a layout template.

## Failure behavior

- Report a failed or cancelled search/tool call; do not fill the gap from memory.
- If the authoritative source is inaccessible, label the claim unverified and state the best next retrieval step.
- If evidence remains mixed, preserve the disagreement and lower confidence.
- If all load-bearing sources are unavailable or the conclusion cannot be checked, return `BLOCKED/NOT_PROVEN`; do not present a memory-based answer as a degraded research result.

## Done

- Every load-bearing current claim traces to a source opened in this run.
- Evidence strength matches claim risk; contradictions and freshness are visible.
- The applicable completion contract passes in [delivery modes](references/delivery-modes.md), [HTML reports](references/html-reports.md), and [source selection](references/sources.md).
- High-stakes or durable conclusions include the independent-review disposition required by [the methodology](references/methodology.md).
