# Excalidraw design method

Use this reference for decisions that should remain stable across Excalidraw versions. Current JSON values and bindings live in [excalidraw-format.md](excalidraw-format.md).

## Contents

- [Start with one question and one path](#start-with-one-question-and-one-path)
- [Compose the canvas](#compose-the-canvas)
- [Size nodes from content](#size-nodes-from-content)
- [Use text roles deliberately](#use-text-roles-deliberately)
- [Make boundaries mean something](#make-boundaries-mean-something)
- [Route relationships](#route-relationships)
- [Limit the palette and decoration](#limit-the-palette-and-decoration)
- [Split before the canvas fails](#split-before-the-canvas-fails)
- [Visual acceptance signals](#visual-acceptance-signals)

## Start with one question and one path

Write a one-sentence question the diagram answers. Rank content as:

1. primary: necessary to answer the question at fit-to-view;
2. secondary: useful explanation at normal zoom;
3. detail: belongs in a focused view, note, or linked artifact.

Choose one entry point and one dominant reading direction. Left-to-right suits pipelines and causality; top-to-bottom suits long processes and layered flows; radial layouts suit one center with independent branches; matched columns suit comparisons. Direction changes require a visible boundary or phase transition.

Choose the diagram type from the relationship rather than the nouns:

| Relationship to expose | Suitable view |
| --- | --- |
| Ordered actions and decisions | Flowchart |
| Messages over time | Sequence |
| Data movement or transformation | Data-flow or pipeline |
| Containment, ownership, trust, deployment | Layered architecture with zones |
| Parent/child structure | Tree |
| Alternatives with common criteria | Matched comparison |
| One center with mostly independent branches | Hub-and-spoke or mind map |

## Compose the canvas

Use an alignment grid as a rhythm, not as a visible decoration. Start with 20 px increments and adjust only when measured text or connector routing requires it.

- Outer margin: normally 64–96 px around the meaningful content.
- Zone padding: normally 48–64 px from children to the boundary; reserve extra header space inside the top edge.
- Peer gap: normally 48–80 px when no connector label must fit.
- Connected gap: normally 120–200 px when a connector and its label occupy the gutter.
- Section gap: normally 96–160 px so a phase break is stronger than an ordinary peer gap.

These are starting ranges, not coordinate templates. Increase them for long labels or converging connectors. Reduce them only after a whole-view render shows excessive separation.

Align peer nodes by the edge that carries meaning: tops for parallel services, centers for a pipeline, baselines for labels, and columns for successive stages. Distribute repeated peers evenly. Avoid a small dense cluster beside a large empty void unless that isolation deliberately marks importance.

Use scale to express hierarchy:

- one hero or entry point may be about 1.3–1.6 times a primary node;
- primary peers share visual weight;
- secondary notes are quieter through size, color, or stroke, not by becoming illegible;
- zones describe ownership or boundary and must not compete with their children.

## Size nodes from content

Measure rendered text when the active Excalidraw API can do so. Without metrics, estimate each script separately and leave 20–28 px horizontal padding and 16–24 px vertical padding around the measured block.

When writing native JSON directly, give an explicit `n`-line text element at least `n × fontSize × lineHeight` height before adding any surrounding gap. A shape can contain the element geometrically while Excalidraw still clips later lines when the text element's own `height` describes only one line.

Prefer two to four lines inside an ordinary node. If a node needs more:

- separate a short heading from the explanation;
- move technical identifiers to a second grouped text element;
- turn supporting prose into a nearby note;
- create a focused view when the detail is part of a second story.

Same-role nodes may share dimensions when their content is comparable. Do not force a long label into a peer's width merely for symmetry; either widen the whole peer set or restructure the label.

## Use text roles deliberately

Excalifont is the expressive display face; Nunito is the compact reading face. One text element has one `fontFamily`, so mixed roles need separate grouped text elements.

| Text role | Family | Typical size | Alignment and use |
| --- | --- | ---: | --- |
| Diagram title | Excalifont | 30–36 px | Left-aligned to the content frame or centered over a symmetric composition |
| Section or zone heading | Excalifont | 22–28 px | Anchored consistently inside or just above its region |
| Short node label | Excalifont | 18–22 px | One or two lines; centered for compact nodes, left-aligned for cards |
| Explanatory text | Nunito | 16–18 px | Left-aligned; short lines and explicit wrapping |
| Technical identifier | Nunito | 15–18 px | Preserve exact spelling; visually secondary to the human label |
| Connector label | Nunito | 14–16 px | One to four words, placed in clear connector space |
| Minor annotation | Nunito | 14–16 px | Use sparingly; never carry a required conclusion below 14 px |

For mixed Russian prose and identifiers, keep Russian phrases intact and preserve exact identifiers such as `workspace-service`, `POST /v1/jobs`, or `order.created`. Break identifiers only at meaningful separators such as `/`, `.`, `-`, or `::`; do not insert arbitrary spaces. If a node contains both a human label and an identifier, put them on separate visual lines and often in separate text elements.

At the delivery viewport, required body text should remain effectively at least 14 px and connector or minor labels at least 12 px. Effective size is approximately:

```text
element font size × delivery width / scene content width
```

Use the actual export or embedding width. When no target is known, test a 1600 px-wide whole-scene view. If fit-to-view makes important text smaller, simplify, split, or deliver a larger output instead of relying on zoom.

## Make boundaries mean something

Use containers and zones only for:

- ownership or system boundary;
- security or trust boundary;
- deployment/runtime location;
- phase or responsibility;
- a group that must move as a unit.

Do not box every sentence. Free text can serve as a title, annotation, legend, or evidence note. A zone is a background element with a quiet stroke and fill; place it behind its children and keep its title in a consistent corner. Nested zones need visibly different boundary strength and enough padding to avoid border tangles.

Use `groupIds` for elements that should move together. A visible container and a logical group solve different problems and may both be needed.

## Route relationships

Use a connector only when it expresses a relationship the viewer must follow. Position alone is not enough for causality, transfer, or dependency.

- Follow the dominant reading direction for the main path.
- Give fan-out and convergence their own routing lanes.
- Prefer straight connectors for clear adjacent relationships and orthogonal or gently curved routes around obstacles.
- Keep connector segments out of unrelated nodes, text, and zone headers.
- Minimize crossings. When a crossing remains, make the paths visually distinct and keep labels away from the intersection.
- Bind endpoints to their nodes and keep reciprocal references so connectors survive edits.
- Keep labels short and center them in a clear segment. Move longer explanation into a note.

Use line styles semantically and redundantly:

- solid: primary or synchronous path;
- dashed: asynchronous, optional, or deferred path;
- dotted: annotation or weak association.

Do not rely on color alone to distinguish meanings. A bidirectional relationship may use arrowheads at both ends when it is one symmetric relation; use two separately routed arrows when the two directions carry different semantics or labels.

## Limit the palette and decoration

Start with a neutral text/stroke family, one quiet zone treatment, and two to four semantic accent families. Use the same fill/stroke pair for the same role. Prefer a light fill with a darker related stroke and text.

Use solid fills for technical and production diagrams by default. Use hachure, roughness, icons, or ornamental marks only when the requested tone benefits from them. Keep one roughness level across comparable elements; emphasis comes from scale, stroke width, whitespace, and semantic color before decoration.

Legends are a cost. Add one only when color, line style, or shape meaning cannot be inferred from labels. If the diagram needs multiple legends or the legend becomes a paragraph, reduce the encoding vocabulary.

## Split before the canvas fails

Create an overview plus focused views when any of these remain true after one layout revision:

- the whole-view reading order cannot be described in one short sentence;
- required text fails the delivery-size legibility test;
- two or more independent stories compete for the same entry point;
- a node needs two incompatible positions to support different flows;
- cross-zone connectors dominate internal relationships;
- unavoidable crossings or long return paths obscure the main path;
- nodes become prose cards rather than visual units;
- the viewer must pan to discover the conclusion.

Preserve identifiers between views so the overview and details can be cross-referenced.

## Visual acceptance signals

A successful composition has:

- an obvious entry point and stable scan path;
- primary content visible at fit-to-view;
- balanced mass and whitespace without accidental voids or cramped islands;
- peer alignment and repeatable spacing;
- containers that fully wrap their children with breathing room;
- no clipped, colliding, or ambiguously anchored text;
- connectors that land on the intended nodes and avoid unrelated content;
- a small semantic palette and consistent text roles;
- enough concrete detail to teach the intended fact without turning every node into a document.

Failure signals include a wall of equal boxes, a title centered over the canvas rather than the content, more colors than meanings, repeated font roles with different families, long arrow labels squeezed between nodes, free text that looks accidentally detached, large areas visible only by panning, and a diagram that is valid JSON but has not been rendered.
