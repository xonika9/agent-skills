# Project notes

Audits leave notes in the project, so the next audit starts from what is already known, does not raise again what the owner deliberately chose, and shows how the project moved against the template. Keep them in `docs/stack/` unless the project keeps such documents elsewhere. Deliberate departures from the template are decision records in `docs/decisions/`, per [stack](stack.md); the notes link to them rather than restating them.

## Layout

- `README.md` — what the next audit needs and cannot find in code: what could not be checked and why, such as no access to deployment, and facts the owner stated, each with its date. Keep findings and current results out of it.
- `findings.md` — the register of findings, described below.
- `audits/YYYY-MM-DD.md` — each audit's report, described below. Bootstrap writes the first one: the stack map, layers still pending such as sign-in, and the verify results, as the point later audits compare against.

## Findings register

`findings.md` holds the current state of every finding recorded in the project, one row each: ID, the rule ID from [rules](rules.md), what is wrong and where, priority, status, first seen, last checked, and the report or change that last set its status. IDs take the form `WS-<n>`, are assigned in order, and are never reused or renumbered, so a finding keeps its ID when its wording or the rule ID changes.

Statuses:

- `open` — found and not fixed;
- `hypothesis` — an unconfirmed suspicion, with the fact that would decide it;
- `fixed` — a check on the current code shows it gone; name the check;
- `declined` — the owner chose not to act, with the reason or the decision record; do not propose it again without new evidence;
- `obsolete` — the code or setup it concerned no longer exists.

Before giving a finding a new ID, match it against rows of every status: a finding that returns after `fixed`, or a `declined` one raised again with new evidence, reopens under its old ID.

## Reports

Each audit adds `audits/YYYY-MM-DD.md`, with a suffix for a second audit that day, and never edits the report of an earlier run. Its header gives the date, commit, and scope: what was inspected and what was not. Its first section, **Since the previous report**, lists by ID the new findings, the fixed ones, the ones that came back after a fix, the ones still open, and the ones not checked this time, then the layers whose tool or Same / Different / Absent class changed. A new finding in code unchanged since the previous report's commit is labelled as newly detected rather than new in the project. The first report says there is no previous one.

## When to write

Bootstrap and audits write the notes. Fixing selected findings and writing the rules block add no report; they update the register rows they change.

## Reading and closing a run

Before an audit, read the README, `findings.md`, the latest report, and the decision records. Treat recorded statuses as history: recheck a finding before relying on its status.

At the end, recheck every `open` and `hypothesis` row inside the run's scope, set its status, and update its last-checked date. A row the run did not look at keeps its status and date and goes into the report as not checked, never as fixed. Then add the new rows and write the report.

## Pointer in the rules block

When the notes exist, the [rules block](agents-block.md) names them in its opening lines. When an audit creates the notes and the block lacks that line, the report's question about the rules block offers to add it.
