# The rules block in AGENTS.md

The block gives every agent working in the project the development rules it cannot recover from code or tooling, so the project does not depend on this skill being invoked. This skill owns only the content between the markers; the rest of `AGENTS.md`, `CLAUDE.md` normalization, and README belong to `x9-context-files-generator`, whose agent-file contract governs preservation.

## Format

```markdown
<!-- x9-web-stack:start -->
## Development rules

<one line: what the block covers and that a project override goes outside the block>

### Before finishing
### Structure
### Data and access
### Database
### Never edit by hand
<!-- x9-web-stack:end -->
```

- Keep the headings and their order; omit a heading with nothing to say.
- At most about 60 lines between the markers.
- One rule per bullet, imperative, with the project's real paths and commands. Add the reason in a short clause when it changes how an agent handles an unlisted case.

## Choosing rules

Start from [rules.md](rules.md). A rule enters the block only when all of these hold:

- It applies to this project now: the layer exists, or the on-demand trigger has happened.
- Nothing mechanical enforces it here. A rule enforced by the project's linter, types, tests, or CI stays out; an unenforced rule that could be enforced cheaply is an audit finding, not a block line.
- An agent would plausibly break it while doing ordinary work.

**Before finishing** always names the project's single verify command, verified from its manifests; if the project has none, say so in the report instead of inventing one.

For a project on a different stack, express each chosen principle in that stack's terms and paths, and leave out template-only mechanics. For example, S4 in a Django project becomes "Service functions take their dependencies as arguments; views only parse input and call services".

## Writing and updating

- With no markers, insert the block after the file's opening summary or setup section. Create a missing `AGENTS.md` through the `x9-context-files-generator` contract.
- With markers, replace only the content between them. Text outside the markers is never changed by this skill.
- A rule outside the block that conflicts with one inside is a decision for the user: report it and keep both until they choose. A project rule outside the block that already covers a pool rule replaces that pool rule; do not duplicate it.
- Load `x9-agent-instructions` before writing the block, because it is agent-facing prose.

## Done

The diff touches only the block (plus the agreed insertion point on first write), the block is within budget, every command in it runs or is labelled unverified, and every included rule passes the three tests above.
