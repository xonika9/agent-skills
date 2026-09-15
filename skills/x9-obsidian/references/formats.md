# Bases and Canvas

Load only the format involved in the request. Preserve existing extension fields and plugin-specific data rather than rewriting a file from a simplified model.

## Bases

[Bases](https://obsidian.md/help/bases) describes views over note files and their properties; it is not a separate copy of the note data. View definitions may be `.base` files or embedded code blocks. Checked against official documentation on 2026-09-09.

Read the current definition and a small sample of its matching notes. Before authoring filters, formulas, or view options, retrieve the relevant official [Bases syntax](https://help.obsidian.md/bases/syntax) and formula/function documentation linked there; do not borrow syntax from Dataview or SQL. Match property names and types actually present. Distinguish changing a view from editing the underlying notes.

Evidence: the definition parses, the intended view opens or queries through available Obsidian tooling, and representative included/excluded notes match the requested filter. A YAML parser alone cannot prove formulas or view behavior. If app validation is unavailable, report the definition as structurally checked with view execution unverified.

## JSON Canvas

Use the [JSON Canvas 1.0 specification](https://jsoncanvas.org/spec/1.0/) for `.canvas`; checked on 2026-09-09. Preserve node IDs, stacking order, geometry, and edge endpoints outside the requested change. New IDs must be unique. Apply the main skill's root-confinement contract to `file` and `background` references. A file node's `subpath` is separate from its file path.

For edits, inspect neighboring nodes and existing coordinates before choosing placement. Validate JSON and the fields, unique IDs, edge endpoints, integer coordinates, and integer dimensions required by the specification. Treat non-positive width or height as a geometry or legibility problem rather than a specification violation unless current app-aware evidence rejects it. A group is a visual region rather than a parent: check new nodes for unintended overlap and requested group overflow without moving unrelated nodes.

A `link` node stores a URL, and a viewer may fetch remote previews while opening the canvas rather than only when a node is activated. Writing the JSON is not network authorization. Before app or viewer validation, inventory the link-node hosts; unless that egress is already in scope, use only a route demonstrated not to fetch them or leave the visual check unverified. An authorized scene view is still needed to establish legibility and correct attachments; parsing does not prove either.
