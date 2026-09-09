# Bases and Canvas

Load only the format involved in the request. Preserve existing extension fields and plugin-specific data rather than rewriting a file from a simplified model.

## Bases

[Bases](https://obsidian.md/help/bases) describes views over note files and their properties; it is not a separate copy of the note data. View definitions may be `.base` files or embedded code blocks. Checked against official documentation on 2026-09-09.

Read the current definition and a small sample of its matching notes. Before authoring filters, formulas, or view options, retrieve the relevant official [Bases syntax](https://help.obsidian.md/bases/syntax) and formula/function documentation linked there; do not borrow syntax from Dataview or SQL. Match property names and types actually present. Distinguish changing a view from editing the underlying notes.

Evidence: the definition parses, the intended view opens or queries through available Obsidian tooling, and representative included/excluded notes match the requested filter. A YAML parser alone cannot prove formulas or view behavior. If app validation is unavailable, report the definition as structurally checked with view execution unverified.

## JSON Canvas

Use the [JSON Canvas 1.0 specification](https://jsoncanvas.org/spec/1.0/) for `.canvas`; checked on 2026-09-09. Preserve node IDs, stacking order, geometry, and edge endpoints outside the requested change. New IDs must be unique. Resolve file references and group backgrounds in the target vault; a file node's `subpath` is separate from its file path.

For edits, inspect neighboring nodes and existing coordinates before choosing placement. Validate JSON, required fields for each node type, unique IDs, and edge endpoints referring to existing nodes. A scene also needs an app view to establish legibility and correct attachments; parsing does not prove either. If no compatible viewer is available, deliver the file with the visual check explicitly unverified. Other diagram formats remain with `x9-diagrams`.
