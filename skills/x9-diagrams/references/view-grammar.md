# View grammar

Load only the selected view's section. Shared reading order, routing, complexity budgets, and acceptance belong to [the design method](design-method.md); notation and serialization belong to the selected format adapter.

## Architecture change comparison

Use this view when components, connections, or meaningful boundaries change between two named system snapshots. Attribute-only differences belong in a table; migration order belongs in a process or timeline view.

### Model

Match components and relationships by stable logical identity. Distinguish additions, removals, semantic changes, moves, and endpoint changes. A renamed surviving component keeps its identity; a replacement receives a new identity. For relationships, compare ordered endpoints separately from protocol or operation changes.

Maintain one logical inventory with before/after presence, attributes, containment, and endpoints. Native IDs remain unique: if one file contains both snapshots, prefix each drawn instance with its snapshot and show the shared logical ID when readers need to match it. Logical matching is an authoring record, not a claim that the bundled summarizer automatically compares snapshots.

### Composition

Use equally sized Before and After panels with a short change list between or immediately below them. Start from matching local positions in both panels. Move a retained object only when the movement carries meaning and appears in the change list. A connector reroute with the same endpoints is a layout adjustment, not an endpoint change.

Use words or symbols alongside color to identify changes. Keep unchanged components quiet. Describe every actual component or relationship change once, including the old and new endpoints of a changed connection; a drawing must not manufacture continuity from position alone. A boundary or containment change belongs in the same list.

Each drawn instance counts toward the existing complexity budget. When the paired view cannot fit, split by named subsystem while preserving logical IDs; comparison is not an exemption from the budget.

### Acceptance and example

Check the logical inventory against both rendered snapshots: every addition, removal, changed attribute, meaningful move, changed containment, and endpoint change has an entry; no unchanged object is described as changed. Do not imply migration order, availability, or rollback from the two pictures.

[The worked SVG](../assets/architecture-change.svg) shows a fictional order path before and after adding a durable queue. Read it with [the SVG adapter](svg.md); it is an illustrative composition, not an automatically converted source diagram. The seven drawn nodes represent four logical components; five relationships represent three logical relationships. Only the API and worker change; the queue and its output relationship are added, and the API's output relationship changes endpoint.

## Manually composed sequence

Use this view when messages between participants and their order carry the answer. One subject's phases belong in a state view instead.

Give each participant a header and a vertical lifeline; time advances down the page and each message occupies a distinct level. Place activation intervals on the receiving lifeline and close them at the corresponding completion. Self-calls return to the same participant through a separate lane.

Keep synchronous calls, replies, and asynchronous messages visually distinguishable using the selected notation's line and arrowhead conventions. When there is no formal convention, label the relationship explicitly rather than inventing UML conformance. Branches and repeated sections use visibly bounded fragments with operators and guards spanning only participating lifelines; concurrent messages do not acquire a false sequential order from their drawn positions.

Avoid upward message arrows, unclosed activations, branch clusters with no frame, and labels crossing unrelated lifelines. Preserve exact operation names when they carry the technical meaning.

For Mermaid, [the Mermaid adapter](mermaid.md#sequence) owns syntax. If a manually authored format cannot represent lifelines, activations, fragments, or message attachment points within its supported native and validation contract, choose an available compatible notation or identify the unsupported part; do not disguise it as a generic box-and-arrow flowchart.
