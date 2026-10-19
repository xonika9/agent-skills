# Development rule blocks

Optional reusable rules and explicitly selected workflow overrides, maintained from one template per block. Project-specific requirements belong in repository instructions outside the marked blocks and take precedence over template defaults. Do not create registries, trackers, decision logs, or other standing process documents merely to fill Local; evidence required by an accepted task contract remains required. This skill owns the text between its block markers; the templates in [rule-blocks/](rule-blocks/) are the canonical wording. The blocks leave out what the user's global instructions already say: for this package's maintainer, the shared personal core in the package's `global-files/`. Keep it that way when a template changes.

| Block | Heading | Offer when |
| --- | --- | --- |
| [`execution`](rule-blocks/execution.md) | Execution discipline | the repository holds application or library code |
| [`sources-of-truth`](rule-blocks/sources-of-truth.md) | Sources of truth and decisions | the repository has multiple existing information sources whose ownership could be confused |
| [`documentation`](rule-blocks/documentation.md) | Documentation discipline | the repository keeps documentation beyond a README |
| [`dependency-updates`](rule-blocks/dependency-updates.md) | Dependency updates | an update bot is configured, such as `renovate.json*` or `.github/dependabot.yml` |
| [`interface-references`](rule-blocks/interface-references.md) | Interface references | the repository has a user interface and the user names reference products |
| [`compound-engineering`](rule-blocks/compound-engineering.md) | Compound Engineering | the repository uses Compound Engineering, such as `.compound-engineering/` or its plans |

The section between `<!-- BEGIN COMPOUND ENGINEERING POLICY -->` and `<!-- END COMPOUND ENGINEERING POLICY -->` is the hand-maintained predecessor of `compound-engineering`, not another skill's block; treat it as an older section of the same rules.

## Offer

After the regular Create, Update, or Audit result, check the repository. Do not offer the blocks in a content repository, such as a blog or a notes vault, even when it holds site-generator code, unless the user asks. Otherwise run:

```bash
python3 <skill-directory>/scripts/rule_blocks.py <repository>/AGENTS.md
```

It reports each block as `current`, `outdated`, `absent`, or `duplicate`, names a same-heading section or the predecessor above, and reports whether repository rules precede the marked blocks. `absent` does not mean the rules are absent: compare the template with sections under other headings before offering it. Show one line per block whose condition holds or that is already present, with its status, the useful behavior its insertion or update would add, and any older section that covers it. Compare obligations, not just headings: when an existing repository rule or another skill's block already owns an obligation, do not introduce an alternative owner or recommend a redundant block. Ask once which applicable insertions or updates to make. A request that names blocks authorizes them without that question. In Audit, offer applicable block insertions or updates even when the audit has no findings. Combine block selection with any question about applying audit fixes. The audit remains read-only until the user selects or explicitly authorizes blocks. A declined block is not offered again in the same run. On `duplicate` or a script error, stop work on that file and report it.

## Write

The shared part is copied, not written: apply `x9-agent-instructions` and the derivability test only to Local and to text outside the blocks.

- **Absent.** Copy the template's shared part exactly. Fill Local from repository evidence. Use only existing relevant project facts, resource pointers, and explicit scoped delegations. Omit unfilled optional entries and the `### Local` heading when none remain; do not ask the user to establish a process just to fill a template.
- **Outdated.** Inspect both the shared part and Local under [Refreshing existing blocks](#refreshing-existing-blocks). Show the complete proposed file diff, including removals and the destination of preserved project rules. Approval of the refresh authorizes those shown changes, not deletion of the underlying documents or project data.
- **Same rules outside the block.** When the chosen block covers an older section or rules outside markers, show which lines the block covers, which resource pointers or factual values move into Local, and which project-specific rules stay outside. Delete a line outside the block only after the user approves that mapping. A rule that conflicts with the block stays in place next to it until the user chooses.

## Refreshing existing blocks

A status of `outdated` or a line beginning with `-` does not establish whether a rule is obsolete template text or a project customization. The checker compares against the current template only; it does not establish provenance.

- Use the existing block, Local, repository history, and an earlier template version when available. Remove inherited requirements superseded by the selected current template; do not move all deleted template text into project rules, which would restore the discarded workflow.
- Preserve project-specific requirements, permissions, prohibitions, and incident-driven exceptions. Put behavioral rules above the marked blocks, keeping their actors, conditions, scope, and authority. Keep useful resource pointers and factual values in Local. Cover customizations inside the old shared part as well as Local and unmarked predecessor sections.
- When origin or intended preservation cannot be established, identify only the ambiguous statements and request one grouped decision. Do not infer authorship from a heading or marker, silently delete an unknown rule, or block unrelated confirmed updates.
- A foreign block remains owned by its skill. Inspect that owner's current block contract to report overlaps and stale rules. An authorized refresh follows that owner's contract and stays scoped to the instruction block; it does not run the owner's full audit, rewrite its notes, or adopt another format. Never replace it with a new generator-owned block covering the same obligations.

An Audit reports the proposed removals, moves, and owner-specific refreshes without editing. A fix or an approval applies the agreed diff through the relevant owners. A passing checker proves template agreement, not preservation of every project instruction; inspect the complete resulting file for lost rules and duplicate owners.

## Order

The file holds the repository's own rules first, then other skills' marked blocks, then this skill's blocks in table order. The checker treats substantive text outside marked blocks and Markdown code examples as repository rules, including ordinary paragraphs and lists. When it reports repository rules after a marked block or marked blocks out of order, propose restoring that order; move repository rules above the first marked block. For that move, another skill's block may be relocated as a whole, byte for byte, with its markers.

## Done

The script reports every chosen block `current` and no block `duplicate`; repository rules precede the marked blocks, or the user declined the move; every retained project-specific rule has its intended surviving owner and scope; no deleted template requirement is silently restored elsewhere; every Local entry is applicable; all removals and moves match the approved diff.
