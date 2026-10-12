# Diagram design method

Use this reference for decisions shared by Excalidraw, Mermaid, draw.io, and SVG. Format syntax and serialization live in [excalidraw-format.md](excalidraw-format.md), [mermaid.md](mermaid.md), [drawio.md](drawio.md), and [svg.md](svg.md).

## Contents

- [Start with one question and one path](#start-with-one-question-and-one-path)
- [Compose for the delivery viewport](#compose-for-the-delivery-viewport)
- [Make boundaries mean something](#make-boundaries-mean-something)
- [Route relationships](#route-relationships)
- [Limit visual vocabulary](#limit-visual-vocabulary)
- [Respect the complexity budget](#respect-the-complexity-budget)
- [Split before the diagram fails](#split-before-the-diagram-fails)
- [Visual acceptance](#visual-acceptance)

## Start with one question and one path

When the delivery medium is open, compare the diagram with a short paragraph or table. Recommend the medium that answers the question more directly.

Write the one-sentence question the diagram answers. Rank content as:

1. primary: necessary to answer the question in the declared delivery mode;
2. secondary: useful explanation at normal reading or editing scale;
3. detail: better placed in a focused view, note, or linked artifact.

For a new diagram or an explicitly authorized redesign, remove or merge any node, connector, or label whose absence leaves that answer intact; two nodes that always appear together are one node. Do not retain decoration merely to fill space.

Before drawing a new diagram, state in one short message the view, the format, the delivery mode, and anything the [complexity budget](#respect-the-complexity-budget) forces out. If a cut removes content the user asked for and the user is reachable, let them redirect before drawing; otherwise proceed and list the cuts beside the deliverable.

For a revision, preserve the existing view type, dominant reading direction, canvas orientation, major topology, node identity, and meaningful boundaries. A request to review, fix, polish, or improve does not authorize changing them; only an explicit redesign request does.

Choose one entry point and one dominant reading direction. Left-to-right suits pipelines and causality; top-to-bottom suits long processes and layered flows; radial layouts suit one center with independent branches; matched columns suit comparison. A direction change needs a visible boundary or phase transition.

Choose topology from the relationship rather than the nouns:

| Relationship | Suitable view |
| --- | --- |
| Ordered actions and decisions | Flowchart or activity view |
| Messages over time | Sequence diagram |
| Lifecycle and valid transitions | State diagram |
| Data movement or transformation | Data-flow or pipeline |
| Containment, ownership, trust, or deployment | Layered architecture with boundaries |
| Domain types and their structural relationships | Class diagram |
| Tables, keys, and cardinality | Entity-relationship diagram |
| Parent/child structure | Tree |
| Events placed against time | Timeline |
| Alternatives under common criteria | Matched comparison |
| One center with independent branches | Hub-and-spoke or mind map |

### Behavior patterns

When behavior, not structure, carries the answer, one pattern specializes the chosen view. Use one primary pattern per diagram; a second need means a second view.

- **Trust boundary crossing** (architecture view): show the boundary, every permitted route across it with its control point, and the forbidden or blocked routes as visibly distinct lines with a label. Pitfalls: a boundary drawn without any crossing, or a blocked route shown only by color.
- **Lifecycle** (state view): one subject's main phases on a single rail in reading order, waits and retries in a separate band, and each terminal outcome, such as cancelled and failed, as its own labeled state. Pitfalls: actor messages disguised as phases, or a retry loop without a labeled re-entry point.
- **Bottleneck** (data-flow view): distinct sources converging on one constrained point with its capacity stated in units (`8/hour`, `3 slots`), plus both admitted and deferred or rejected outcomes. Aggregate more than five sources into a named group. Pitfall: contention implied only by box size or color.

## Compose for the delivery viewport

Use scale, grouping, and whitespace to reveal hierarchy. Primary peers share visual weight; secondary notes are quieter without becoming illegible; boundaries describe ownership or scope and must not compete with their children.

Keep labels short enough to scan. Separate a human-facing label from a technical identifier when both matter. Move paragraphs into nearby notes or focused views rather than turning every node into a document.

Use hard line breaks only for semantic boundaries such as a heading/body split or separate list items. Width-driven wrapping belongs to the selected format's layout engine; a format without one, such as SVG, delegates line breaking to its adapter. If rendering produces orphaned one-word lines, leading separators, or broken compounds, shorten the label or enlarge the node instead of hand-tuning line breaks.

Choose the delivery mode before laying out the canvas:

- **Whole view:** the complete argument must fit the delivery viewport. Required body text stays comfortably readable and connector labels do not require zoom. If important text becomes too small, simplify or split the diagram.
- **Scrollable canvas:** use this only when normal-zoom scrolling is an explicit part of the handoff. Validate the main path in consecutive viewport-sized regions at normal zoom; each region needs readable text, visible connectors, and enough overlap with the next region to preserve orientation. Do not use a whole-scene fit calculation as a failure gate for this mode.

Pages are appropriate only when each page answers a distinct question or presents a stable level of detail; they are not a hiding place for an overloaded canvas.

## Make boundaries mean something

Use a boundary only for ownership, trust, deployment location, phase, responsibility, or a group that must move as a unit. Do not box every sentence. Nested boundaries need distinguishable strength and enough padding to avoid border tangles.

## Route relationships

Use a connector when the relationship must be followed; position alone is not enough for causality, transfer, dependency, or cardinality.

- Follow the dominant reading direction for the main path.
- Give fan-out and convergence their own visual lanes.
- Keep every connector individually traceable from source to target. Do not overlap routes or reuse an attachment point when that makes relationships indistinguishable; if automatic layout does so, revise the source or split the view.
- Keep connectors out of unrelated nodes, text, and boundary headings.
- Minimize crossings and keep labels away from intersections.
- Use short relationship labels in clear connector space.
- Do not rely on color alone to distinguish relationship types.

Solid, dashed, and dotted lines may distinguish primary, asynchronous or optional, and annotative relationships when the selected notation supports that meaning. Keep the convention consistent and label it when it is not obvious.

## Limit visual vocabulary

Start with neutral text and connectors, one quiet boundary treatment, and a small set of semantic accents. Apply the same visual treatment to the same role. Reserve the focal accent for one or two elements: the answer to the question or the path the reader follows first. Needing more focal accents means the focus is still undecided. Use shape, label, or line style alongside color so the meaning survives grayscale and color-vision differences.

Decoration must support the requested tone without obscuring structure. A legend earns space only when visual encoding cannot be inferred from labels.

## Respect the complexity budget

One whole-view diagram carries at most 9 primary nodes and 12 relationships. Views with their own grammar have tighter ceilings:

| View | Ceiling |
| --- | --- |
| Sequence | 5 participants, 1 nested fragment level |
| Swimlane | 5 lanes |
| Tree or hierarchy | depth 4 |
| Entity-relationship or class | 8 entities |

Boundaries, connector labels, and notes do not count as nodes. Above a ceiling, aggregate peers into a named group; if that is not enough, [split](#split-before-the-diagram-fails) before laying out. A scrollable canvas applies the ceilings to each viewport-sized region. A conversion or review of an existing diagram keeps the source's content: report the overrun instead of cutting, unless the user asked for a simplified result.

## Split before the diagram fails

Create an overview plus focused views when the [complexity budget](#respect-the-complexity-budget) calls for a split, or when any of these remain after one layout revision:

- the reading order cannot be described in one short sentence;
- required text is illegible at delivery size;
- independent stories compete for the same entry point;
- one node needs incompatible positions for different flows;
- cross-boundary connectors dominate internal relationships;
- unavoidable crossings obscure the main path;
- nodes become prose cards;
- a whole-view delivery requires panning to discover the conclusion;
- a scrollable delivery loses the main path between adjacent viewports.

Preserve identifiers between views so the overview and details can be cross-referenced.

## Visual acceptance

A successful diagram has an obvious entry point, stable scan path, readable primary content in its declared delivery mode, balanced mass and whitespace, consistent peer roles, meaningful boundaries, and unambiguous connector landing points.

Failure signals include a wall of equal boxes, more colors than meanings, clipped or detached labels, large accidental voids, dense islands, long connector labels squeezed between nodes, and valid source that has never been rendered.
