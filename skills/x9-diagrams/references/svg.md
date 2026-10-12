# SVG source and HTML preview

Use this adapter for a hand-composed diagram delivered as standalone SVG. The canonical source is one `.svg` file. An HTML page is a wrapper for a page or an in-chat preview: it inlines or references the same SVG and never becomes a second source to edit.

SVG has no automatic layout and no visual editor that round-trips it losslessly; every coordinate is authored.

## Contents

- [Scope](#scope)
- [Document contract](#document-contract)
- [Semantic markup](#semantic-markup)
- [Geometry and text](#geometry-and-text)
- [Styling](#styling)
- [HTML wrapper](#html-wrapper)
- [Validation](#validation)

## Scope

This route draws the same schematic views as the other formats; [the trigger boundary](../SKILL.md#trigger-boundary) excludes charts and mockups. Animation, brand theming, and external fonts or images are outside this route.

## Document contract

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600"
     role="img" aria-labelledby="checkout-flow-title checkout-flow-desc">
  <title id="checkout-flow-title">Checkout flow</title>
  <desc id="checkout-flow-desc">An order passes payment and stock checks before fulfilment.</desc>
  <style>/* classes only; see Styling */</style>
  <defs><!-- markers --></defs>
  <g data-layer="boundaries">…</g>
  <g data-layer="edges">…</g>
  <g data-layer="nodes">…</g>
  <g data-layer="labels">…</g>
</svg>
```

- `<title>` comes first and names the subject; `<desc>` is one sentence about content, not geometry. Prefix their IDs with the file slug.
- The four layers appear once each, in this order, as direct children of the root. The order is the paint order: boundaries stay behind everything, connectors pass behind nodes, and connector labels stay on top.
- The file is self-contained and inert: no `<script>`, event-handler attributes, `<foreignObject>`, animation elements, `@import`, CSS escapes, or `href`/`url()` that does not point to a local `#id`. A `<!DOCTYPE>` may name the public SVG DTD but carries no internal subset or entity declarations.
- Semantic groups contain plain shapes and text only: no nested `<svg>` or `<use>` inside the layers, because checks and summaries cannot follow their geometry.
- IDs are unique across the file.

## Semantic markup

Semantic attributes carry the diagram's model so that review, summaries, and conversion do not have to infer it from pixels.

| Element | Markup | Contents |
| --- | --- | --- |
| Boundary | `<g data-boundary="id">` in `boundaries` | One shape plus its heading text |
| Node | `<g data-node="id">` in `nodes` | One shape (`rect`, `ellipse`, `circle`, `polygon`, or `path`) plus text |
| Connector | `<g data-edge="id" data-from="node" data-to="node">` in `edges` | One `path`, `line`, or `polyline` |
| Connector label | `<g data-label-for="edge-id">` in `labels` | An opaque mask `rect` plus text |

- `data-from` and `data-to` name nodes or boundaries. The arrowhead sits at `data-to`; an undirected relationship has no marker, and a two-way relationship has both `marker-start` and `marker-end`.
- A node or boundary inside a boundary declares `data-parent="boundary-id"`.
- An optional `data-role` names the semantic role (`store`, `external`, `actor`, `decision`, `focus`) when the same visual treatment repeats.
- Visible text is the human label. Keep stable technical identifiers in the semantic IDs, and repeat a technical token in visible text only when the reader needs it.

## Geometry and text

- Place every shape on the canvas inside the `viewBox`, with margin.
- Use `translate()` for group offsets. Avoid `rotate`, `scale`, and `matrix` on semantic groups because summaries and geometry checks cannot follow them.
- Route connectors as horizontal and vertical segments, with small rounded corners when they help tracing. Start and end each connector on its node's edge, not inside or short of it.
- SVG never wraps text. Break lines explicitly with `<tspan x="…" dy="…">`, size the shape from the longest line, and confirm the fit in the render; a line too long for its node is shortened or the node is enlarged.
- Center a connector label on a segment through open space; its mask `rect` stays clear of every node and uses the fill of the surface behind it, such as the boundary fill inside a boundary, so the mask hides the line without showing as a patch.

## Styling

Use one internal `<style>` with class selectors and literal colors, then apply classes to elements. Editors that import SVG, such as Figma and Inkscape, keep class styles more reliably than CSS custom properties. A dark variant may override the same classes inside `@media (prefers-color-scheme: dark)`; editors that ignore it keep the light rendering.

Use a system font stack such as `system-ui, -apple-system, "Segoe UI", sans-serif`, and a monospace stack only for technical tokens. Define each arrow marker once in `<defs>` per stroke treatment.

## HTML wrapper

When the delivery is a page or an in-chat preview, write a minimal HTML document that embeds the SVG inline or via `<img src="diagram.svg">`. Inline markup must stay identical to the canonical file. Keep the SVG at its `viewBox` width inside a wrapper with `overflow-x: auto`, so a narrow screen scrolls the diagram instead of shrinking its text. A preview renders the delivered SVG; it does not prove anything about a different file.

## Validation

Run the bundled checker on the canonical file:

```bash
python3 ../scripts/check_svg.py diagram.svg
```

It exits `1` on contract errors and reports geometry problems as `WARN`; add `--strict-geometry` to fail on them and on any element whose geometry it could not check. Geometry warnings are estimates from declared coordinates, and text width is approximate.

Then render the `.svg` in a browser engine, for example a headless browser screenshot or the host's HTML preview, at the delivery size. Inspect the rendered view for clipped or overflowing text, connector landing points, crossings, and hierarchy. A checker pass without a render is `DEGRADED`.
