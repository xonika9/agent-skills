# Diagram design method

Use this reference for decisions shared by Excalidraw, Mermaid, and draw.io. Format syntax and serialization live in [excalidraw-format.md](excalidraw-format.md), [mermaid.md](mermaid.md), and [drawio.md](drawio.md).

## Start with one question and one path

Write the one-sentence question the diagram answers. Rank content as:

1. primary: necessary to answer the question at whole-view scale;
2. secondary: useful explanation at normal reading or editing scale;
3. detail: better placed in a focused view, note, or linked artifact.

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

At whole-view size, required body text should remain comfortably readable and connector labels should not require zoom. If automatic layout or fit-to-view makes important text too small, simplify or split the diagram instead of relying on panning. Pages are appropriate only when each page answers a distinct question or presents a stable level of detail; they are not a hiding place for an overloaded canvas.

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
- the viewer must pan to discover the conclusion.

Preserve identifiers between views so the overview and details can be cross-referenced.

## Visual acceptance

A successful diagram has an obvious entry point, stable scan path, readable primary content at whole-view size, balanced mass and whitespace, consistent peer roles, meaningful boundaries, and unambiguous connector landing points.

Failure signals include a wall of equal boxes, more colors than meanings, clipped or detached labels, large accidental voids, dense islands, long connector labels squeezed between nodes, and valid source that has never been rendered.
