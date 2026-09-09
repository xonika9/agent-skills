# Markdown and properties

For syntax-sensitive edits consult [internal links](https://help.obsidian.md/links), [embeds](https://help.obsidian.md/embeds), and [properties](https://obsidian.md/help/properties). Property behavior below was checked against the official documentation on 2026-09-09.

A wikilink may carry a target, heading or block anchor, and display text: `[[Project#Milestones|schedule]]`, `[[Project#^decision]]`. An embed prefixes the link with `!`; it can refer to a note, an anchor, or an attachment. Preserve those components separately when modifying a target. Markdown links also occur, including encoded paths and fragment identifiers. Do not treat links inside fenced examples as live references without context.

A narrow note edit preserves task checkboxes, callout markers, block IDs, and embed options outside the requested change. When adding a link, resolve its destination from the source note, including basename collisions; avoid creating a plausible-looking link to a nonexistent file unless an intentional future note is requested.

Properties live in leading YAML frontmatter. Keep keys unique, use literal booleans and numbers for their respective types, preserve list values, and quote wikilinks in property values. For example:

```yaml
---
aliases:
  - Project overview
related:
  - "[[Projects/Example]]"
reviewed: false
---
```

Obsidian assigns one property type per name across a vault. Changing that type can affect other notes; inspect the existing convention before introducing a conflicting value. Nested YAML may be preserved as source even though the property editor does not support it; do not flatten it merely to fit the UI. Metadata migration is separate from a prose edit, and OKF rules belong to `x9-okf-docs` when the vault requires them.
