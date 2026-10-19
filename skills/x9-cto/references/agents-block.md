# CTO block in AGENTS.md

`x9-cto` owns the content between `<!-- x9-cto:start -->` and
`<!-- x9-cto:end -->`. The rest of the file belongs to the repository and its
context-file owner. Markers bound maintenance; they do not implement selective
context loading or grant permission to execute a linked procedure.

## When to write

Write only when the owner asks to configure or update CTO integration, or when
that configuration is explicitly part of an already-authorized outcome. A
consultation, report review, or ordinary invocation does not create or refresh a
block. An absent block does not disable the global role.

Read the live file and relevant local owners before editing. Keep only
information whose omission would change the CTO's next action and that cannot
already be recovered directly from the applicable instructions. Useful entries
are a local handoff route, a non-obvious local constraint, or a narrowly scoped
delegation with no other owner. Link an existing owner instead of copying its
policy. Do not repeat the global method, repository map, shared execution rules,
accepted decisions, current work state, secrets, or tool availability.

If nothing is missing, create no block. An explicitly requested empty skeleton
may use this shape:

```markdown
<!-- x9-cto:start -->
## CTO
<!-- x9-cto:end -->
```

The entire body is local. There is no fixed shared-policy section and no
mandatory `Local` field set. Preserve existing meaning when updating; a template
refresh does not overwrite local rules. Remove a redundant entry only when its
remaining owner is verified and no instruction or granted authority is lost.

## Preservation and completion

Change only the named CTO block and any separately authorized targets. Place a
new block after the repository's own rules, among the other skills' marked
blocks. Preserve all neighboring text and other skills' blocks. Duplicate,
nested, or unpaired CTO markers make the edit ambiguous: stop that edit and
report their locations; do not repair them by choosing an arbitrary match.

When `AGENTS.md` is missing, use `x9-context-files-generator` if available for
the authorized file creation. Without it, propose a minimal file rather than
silently creating a repository onboarding system. Preserve any existing
`CLAUDE.md` and follow the repository's normalization policy; do not replace it
as a side effect of configuring CTO.

Before completion, read back the block, resolve every declared source or bundled
reference through its owner, and inspect the diff against the pre-edit file.
Verify that unrelated text is unchanged and every retained local instruction
has one owner. Follow repository-required document checks. Report the block's
actual path and any unresolved input; do not claim that a route was exercised
merely because its link resolved.
