# Vault audits

Resolve the vault and the requested whole-vault or subtree audit scope before scanning. Exclude archives, generated content, attachments, templates, or plugin directories only when the user, vault instructions, or an existing audit configuration establishes that policy; record every exclusion and its reason.

## Evidence routes

When the [CLI adapter](cli.md) verifies app access, use only the requested app-aware checks supported by live command help and follow that adapter's vault- and target-selection contract. Treat their output as Obsidian-resolved evidence for that app version, selected vault, and target scope.

With a filesystem fallback, use bounded searches to discover candidates, then inspect each source in context. Account for wikilinks, Markdown links, embeds, aliases, heading and block fragments, properties, code fences, and any path-bearing structured format in scope. A text match cannot by itself prove Obsidian link resolution, an orphan, or a broken anchor; label those findings as literal or structurally inferred until an app-aware route verifies them.

## Finding contract

Report only checks actually performed. For each finding retain its category, vault-relative source path, line or structured object identifier when available, literal target, and evidence route. Separate these cases:

- unresolved targets and missing heading or block anchors;
- ambiguous basename resolution;
- orphan or dead-end candidates, which may be intentional and are not defects without a vault convention or user goal;
- invalid `.base` or `.canvas` structure, missing Canvas `file` or `background` targets, and edges whose endpoints do not exist;
- property, index, or other convention violations only when the selected vault defines that convention.

Group the result by navigation breakage, ambiguity, structured-file integrity, and convention-specific maintainability. Distinguish observed structure from suggested remediation; do not create placeholder notes, normalize metadata, or infer a personal knowledge-management policy to make the counts smaller.

## Repair and completion

When repair is authorized, scope the edit to the selected findings, follow the relevant Markdown, move, Base, or Canvas reference, and preserve the original audit as the baseline. After mutation, rerun the same checks with the same scope and exclusions, compare the affected findings, and report both remaining findings and any app-level behavior that was not verified.
