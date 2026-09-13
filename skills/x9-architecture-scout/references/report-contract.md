# Architecture report contract

This reference owns the report's content hierarchy, HTML contract, and validation boundary. It applies after `x9-architecture-scout` has selected a repository and report destination.

## Required hierarchy

Use semantic HTML with one `h1`, one `main` landmark, and headings that advance by no more than one level. Give these sections the exact IDs below, in this order:

1. `decision-question` — the decision or audit question and the repository/subsystem scope.
2. `statuses` — a definition list with visible labels for `Method status`, `Structure status`, and `Render status`.
3. `conclusion` — the current conclusion and an explicit confidence statement.
4. `comparison` — alternatives on shared criteria. The exact ID belongs on a `<section>`. Put the native `table` inside that `#comparison` section, with a `caption`, column headers with `scope="col"`, and row headings with `scope="row"`; do not compare candidates by unrelated one-off claims.
5. `evidence` — source trace, observations, and clearly marked inferences. Repository-derived excerpts use `<pre data-repository-evidence="true"><code>…</code></pre>` and escape every repository-controlled `<`, `>`, and `&`.
6. `diagrams` — one or more architecture diagrams when they make a boundary or dependency easier to see. The exact ID belongs on a `<section>`, and every `figure.diagram` belongs inside that `#diagrams` section. Each figure has exactly one non-empty valid Mermaid-renderable `.mermaid` element inside `.diagram-container` with escaped Mermaid text directly inside it (no nested `<code>`), exactly one separately visible `.mermaid-source` outside that container containing the same normalized Mermaid text, and a `.diagram-text-equivalent` that explains nodes, boundaries, and relationships without relying on colour or JavaScript. Do not hide either fallback with `display: none`, `visibility: hidden`, the `hidden` class, or the HTML `hidden` attribute.
7. `risks` — limitations, counter-evidence, and consequences.
8. `next-step` — the smallest decision-unblocking or planning action.

The report itself is its reader-facing evidence: embed all prose, evidence, and Mermaid source. Put the same valid Mermaid declaration directly in the renderable `.mermaid` element, without nested markup, and in `<pre class="mermaid-source"><code>…</code></pre>`; the latter is the no-JavaScript source fallback. The validator normalizes line endings, leading/trailing blank lines, and trailing whitespace before comparing the two. A failure to load a CDN or execute JavaScript must leave the conclusion, comparison, source, and text equivalent readable.

## Status model

Show all statuses as words, never only as colour or an icon.

- `Method status` is `PASS` only when a live readable `codebase-design` method was used; it is `DEGRADED` for a direct baseline audit; it is `BLOCKED` when the user required that exact unavailable method.
- `Structure status` is `PASS` only when `validate_report.py` exits `0`; otherwise it is `FAIL`.
- `Render status` is `PASS` only after a real browser inspection at both `1280px` and `390px`; otherwise it is `DEGRADED` or `NOT_PROVEN` with the missing condition.

These statuses answer different questions. A passing validator does not prove rendering, and a rendered page does not prove that the external method was available.

## Presentation and resources

Use UTF-8, `<meta name="viewport" content="width=device-width, initial-scale=1">`, and responsive CSS in screen-applicable `<style>` blocks. The validator requires these deterministic hooks:

```css
@media (max-width: 600px) {
  .report-grid { grid-template-columns: 1fr; }
  .comparison-table { display: block; } /* `grid` is also accepted */
}

.diagram-container { overflow-x: auto; }
```

For grid layout declarations, the checker accepts simple compound selectors (a tag, classes and IDs, optionally comma-separated) that match the actual `.report-grid` element. Include `.report-grid` explicitly in its one-column media rule. Use exactly `@media (max-width: Npx)` or `@media screen and (max-width: Npx)`, where `390 <= N < 1280`; these conditions cover the narrow render checkpoint and smaller widths. The winning `grid-template-columns` value must be `1fr`, accounting for declaration order, selector specificity and `!important` across all style blocks.

Keep this layout hook in that supported CSS subset: descendant, sibling, attribute and pseudo-class selectors for grid declarations, nested or other conditional layout rules, inline grid declarations, and `grid`/`grid-template`/`all` resets on `.report-grid` are rejected. Migrate a rule such as `body main.report-grid { grid-template-columns: 1fr; }` to `main.report-grid { grid-template-columns: 1fr; }` inside the supported media rule, then inspect the rendered report. This deterministic contract is intentionally narrower than browser CSS support.

The `.comparison-table` rule must set `display` to `block` or `grid` for reflow. Only `.diagram-container` may provide horizontal scrolling; keep diagram labels and the textual equivalent outside that overflow region.

The only network-loaded resources are these exact pinned URLs:

```text
https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.3.3
https://cdn.jsdelivr.net/npm/mermaid@11.17.1/dist/mermaid.esm.min.mjs
```

Load Tailwind with a `script src`. The sole `script type="module"` must normalize to this exact body, with whitespace differences only:

```js
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.17.1/dist/mermaid.esm.min.mjs";
mermaid.initialize({ startOnLoad: true });
```

Do not use `latest`, a URL alias, `fetch`, dynamic imports, extra module statements, `@import`, CSS `url(...)` in any form, CSS backslash escapes, external fonts, images, trackers, iframes, resource hints, forms, controls, refresh redirects, or extra scripts/styles. The only allowed network-capable attributes are Tailwind's exact `script src` and evidence `a href` values; anchors must not use `ping`. Ordinary source links in `<a href>` are evidence links, not loaded resources, but must be either `https://…` or a fragment beginning with `#`; protocol-relative, `http:`, `ftp:`, and other schemes are rejected.

Mermaid source must be valid-looking text beginning with a supported diagram declaration such as `flowchart`, `sequenceDiagram`, `classDiagram`, `stateDiagram`, `erDiagram`, `C4Context`, `C4Container`, `C4Component`, or `architecture-beta`. Prefer the simplest view that makes the audited relation legible; split diagrams before labels become prose cards.

## Structural validation boundary

Run:

```bash
python3 scripts/validate_report.py <report.html>
```

The checker verifies the fixed hierarchy, basic landmarks and heading order, comparison semantics, the three textual statuses, safe and exact loaded resources, absence of unsafe active content, escaped repository evidence, a Mermaid-renderable element, separately visible Mermaid source, text equivalents, and responsive/overflow hooks. It cannot prove that the CSS is visually readable, that Mermaid rendered, or that source evidence is factually sufficient. Those remain the separate render and method statuses.
