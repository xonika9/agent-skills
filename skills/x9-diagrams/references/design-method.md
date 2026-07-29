# Diagram design method

Use this reference for decisions shared by Excalidraw, Mermaid, and draw.io. Format syntax and serialization live in [excalidraw-format.md](excalidraw-format.md), [mermaid.md](mermaid.md), and [drawio.md](drawio.md).

## Start with one question and one path

Write the one-sentence question the diagram answers. Rank content as:

1. primary: necessary to answer the question in the declared delivery mode;
2. secondary: useful explanation at normal reading or editing scale;
3. detail: better placed in a focused view, note, or linked artifact.

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

## Compose for the delivery viewport

Use scale, grouping, and whitespace to reveal hierarchy. Primary peers share visual weight; secondary notes are quieter without becoming illegible; boundaries describe ownership or scope and must not compete with their children.

Keep labels short enough to scan. Separate a human-facing label from a technical identifier when both matter. Move paragraphs into nearby notes or focused views rather than turning every node into a document.

Use hard line breaks only for semantic boundaries such as a heading/body split or separate list items. Width-driven wrapping belongs to the selected format's layout engine. If rendering produces orphaned one-word lines, leading separators, or broken compounds, shorten the label or enlarge the node instead of hand-tuning line breaks.

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
- Keep connectors out of unrelated nodes, text, and boundary headings.
- Minimize crossings and keep labels away from intersections.
- Use short relationship labels in clear connector space.
- Do not rely on color alone to distinguish relationship types.

Solid, dashed, and dotted lines may distinguish primary, asynchronous or optional, and annotative relationships when the selected notation supports that meaning. Keep the convention consistent and label it when it is not obvious.

## Limit visual vocabulary

Start with neutral text and connectors, one quiet boundary treatment, and a small set of semantic accents. Apply the same visual treatment to the same role. Use shape, label, or line style alongside color so the meaning survives grayscale and color-vision differences.

Decoration must support the requested tone without obscuring structure. A legend earns space only when visual encoding cannot be inferred from labels.

## Split before the diagram fails

Create an overview plus focused views when any of these remain after one layout revision:

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
