# Development rule blocks

Optional blocks of development rules that hold in any code repository, so the same words can be maintained in every repository from one template. This skill owns the text between its block markers; the templates in [rule-blocks/](rule-blocks/) are the canonical wording. The blocks leave out what the user's global instructions already say: for this package's maintainer, the shared personal core in the package's `global-files/`. Keep it that way when a template changes.

| Block | Heading | Offer when |
| --- | --- | --- |
| [`execution`](rule-blocks/execution.md) | Execution discipline | the repository holds application or library code |
| [`sources-of-truth`](rule-blocks/sources-of-truth.md) | Sources of truth and decisions | the repository keeps a decision log and a record of accepted work, or tracks work state outside Git |
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

It reports each block as `current`, `outdated`, `absent`, or `duplicate`, names a same-heading section or the predecessor above, and reports whether repository rules precede the marked blocks. `absent` does not mean the rules are absent: compare the template with sections under other headings before offering it. Show one line per block whose condition holds or that is already present, with its status and any older section that covers it, and ask once which to insert or update. A request that names blocks authorizes them without that question. In Audit, report the status only. A declined block is not offered again in the same run. On `duplicate` or a script error, stop work on that file and report it.

## Write

The shared part is copied, not written: apply `x9-agent-instructions` and the derivability test only to Local and to text outside the blocks.

- **Absent.** Copy the template's shared part exactly. Fill Local from repository evidence. A Local line that the shared part refers to, such as the owner "named in Local", is required: ask for its value when the repository does not establish it. Delete any other Local line with nothing to say, and the `### Local` heading when no line remains.
- **Outdated.** Show the shared-part diff (`--diff`): `-` lines are in the file and leave, `+` lines come from the template. Choosing the update replaces the shared part and keeps Local unchanged; a `-` line the user wants to keep moves into Local.
- **Same rules outside the block.** When the chosen block covers an older section or rules outside markers, show which lines the block covers, which repository facts move into Local, and which rules stay outside because the block does not cover them. Delete a line outside the block only after the user approves that mapping. A rule that conflicts with the block stays in place next to it until the user chooses.

## Order

The file holds the repository's own rules first, then other skills' marked blocks, then this skill's blocks in table order. When the script reports repository sections after a marked block, propose moving those sections above the first marked block. For that move, another skill's block may be relocated as a whole, byte for byte, with its markers.

## Done

The script reports every chosen block `current` and no block `duplicate`; repository rules precede the marked blocks, or the user declined the move; every Local line states a fact of this repository; every line removed outside a block is covered by the block, moved into Local, or approved for removal.
