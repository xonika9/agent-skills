---
name: x9-research
description: Use when the user wants a genuinely researched answer from current or primary sources, including X/Twitter or Reddit — «разберись в вопросе», «изучи тему», «собери факты», "research this", "verify this claim" — or a choice or recommendation that depends on current facts such as prices, availability, offers, versions, or rules — «подбери», «что лучше купить и где», «сравни варианты», "which should I buy". Also use for durable research intent in varied wording — «создай ресерч в папке», «сохрани исследование», «обнови ресерч», "save/update this research" — and for explicit HTML delivery — «ресерч по теме X + html», «подготовь HTML-отчёт с источниками», «нужна HTML-версия», "research X and deliver it as HTML". Do not use for library/API documentation (find-docs), product search owned by another skill, personal advice, or questions answerable from stable supplied context. Mentioning HTML only as the research subject does not request HTML files.
compatibility: Requires Python 3 for deterministic HTML output validation.
---

# Research

Treat prior knowledge as a hypothesis, especially when a question feels familiar: familiarity is what makes an agent skip retrieval. A research answer is built from sources opened in this run; an answer without them is not research, whatever its disclaimer. Trace every load-bearing claim, search for disconfirming evidence, and label uncertainty.

The [machine-readable onboarding contract](references/onboarding.json) lists external prerequisites.

## Method

1. Define the real question, test its premises, and list what the answer must cover: the claims it depends on, the set it chooses among (options, sellers, sources, periods, viewpoints), and the user's constraints that change the result, such as budget, location, cards or subscriptions they hold, size, or free-only. A false premise is the main finding. Ask only about a constraint or ambiguity that would change the result and cannot be inferred.
2. Choose search breadth by the claim: open the owning primary source directly for a specific authoritative fact; broaden the search when the question, source ownership, coverage, or disagreement remains unresolved.
3. Match evidence to claim type using [the evidence thresholds](references/methodology.md#evidence-thresholds); social sampling is owned by [source selection](references/sources.md#social-search).
4. Resolve source conflicts explicitly; do not average incompatible claims.
5. Close every gap you can reach: open the remaining pages, prices, links, and listings instead of estimating them or labelling them unchecked. Stop when every coverage item is researched or excluded with a stated reason and new queries no longer change a load-bearing claim.
6. Answer at the level the user will act on: conclusion first, naming the specific option, place, price with its conditions, and an opened link; evidence near each claim, freshness, and calibrated confidence. Say what an unfamiliar entity is when it first appears. Before handing off, note the follow-up questions the user would most likely ask and answer those the research can settle. When a sourced finding outside the question would change the user's decision, add it in a short final block; do not research it in depth unasked.

Read [references/methodology.md](references/methodology.md) for evidence thresholds and independent verification. Read [references/sources.md](references/sources.md) when selecting search/browser surfaces.

## Runtime and browser

Use the live tools exposed by the current runtime; do not assume Claude-only names. Prefer purpose-built connectors/APIs for structured resources. Before browser work, follow `x9-browser-session`.

Read [references/sources.md](references/sources.md) before browser or social research. It owns source selection, platform sampling, and the intentional authenticated-browser exception for X/Twitter; `x9-browser-session` owns controller selection, task-tab isolation, private-surface safety, and browser-route failure.

## Route the result

Return a sourced answer in chat unless the request conveys persistence, update, or HTML-output intent. For any such intent, read [references/delivery-modes.md](references/delivery-modes.md); it owns classification, OKF discovery, artifact lifecycle, authority, ambiguity, and completion. When it selects HTML, also read [references/html-reports.md](references/html-reports.md) and use [assets/editorial-theme.css](assets/editorial-theme.css) for shared visual tokens and optional components, never as a layout template.

## Failure behavior

- Report a failed or cancelled search/tool call; do not fill the gap from memory.
- If the authoritative source stays inaccessible after the available routes, including the browser, have failed, label the claim unverified and state the best next retrieval step.
- If evidence remains mixed, preserve the disagreement and lower confidence.
- If all load-bearing sources are unavailable or the conclusion cannot be checked, return `BLOCKED/NOT_PROVEN`; do not present a memory-based answer as a degraded research result.

## Done

- Every coverage item is researched or excluded with a stated reason; no reachable gap is left as an estimate or an unchecked label.
- The user can act on the answer without another search: each recommendation names the place, price with conditions, and an opened link where one exists.
- When researching or refreshing evidence, every load-bearing current claim traces to a source opened in this run; HTML-only work uses the current Markdown evidence and states its freshness.
- Evidence strength matches claim risk; contradictions and freshness are visible.
- The applicable completion contract passes in [delivery modes](references/delivery-modes.md), [HTML reports](references/html-reports.md), and [source selection](references/sources.md).
- High-stakes or durable conclusions include the independent-review disposition required by [the methodology](references/methodology.md).
