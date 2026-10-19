# Project notes

Security work leaves notes, so the next run starts from what is already known, does not ask the owner again for facts already given, and shows how findings and coverage changed between runs.

## Where the notes live

Open findings tell an attacker where to look, so the location depends on who can read the repository. In a private repository whose `docs/` is not published as a site, keep the notes in `docs/security/` unless the project keeps such documents elsewhere. When the repository is public, its visibility cannot be established, or `docs/` is published, ask the owner where to keep them before the first write, proposing `docs/security/` excluded through the file `git rev-parse --git-path info/exclude` names: the notes stay in the local working copy without a committed ignore rule, and they are lost with that working copy. Record the chosen location in the AGENTS.md block below; describe a location outside the repository there without a personal path, and ask the owner again when a later run cannot find the notes.

## Layout

- `README.md` — what the next run needs and cannot find in source: the actors and trust boundaries mapped so far, deployment facts and who owns each externally managed control, each owner-stated fact with its date and source and labelled as stated rather than observed, and known traps.
- `findings.md` — the register of findings and the coverage table, described below.
- `audits/YYYY-MM-DD.md` — each pre-release audit's or saved review's report, described below.

Keep credential values, tokens, personal data, and exploit payloads that work against a deployed system out of the notes; describe them instead.

## Findings register

`findings.md` holds the current state of every finding and hypothesis recorded in the project, one row each: ID, problem and affected resource, priority, status, first seen, last checked, and the report or change that last set its status. IDs take the form `SEC-<n>`, are assigned in order, and are never reused or renumbered, so a finding keeps its ID when its wording changes.

Statuses:

- `open` — a confirmed finding, not fixed;
- `hypothesis` — unconfirmed, with the decisive missing fact;
- `fixed` — a check on the current code or configuration shows it gone; name the check;
- `accepted` — the owner accepts the risk, with who accepted it as a role or handle, the reason, and a review date; on or after that date, the next run rechecks it. A confirmed remaining risk returns to `open` unless the owner renews it with a new date; use `fixed` or `obsolete` when current evidence supports that state. If evidence is insufficient, keep the previous status and last-checked date and report the missing check without claiming a confirmed open finding or renewed acceptance;
- `declined` — the owner judged it not a problem, with the reason; do not raise it again without new evidence;
- `obsolete` — the code or setup it concerned no longer exists.

Before giving a finding a new ID, match it against rows of every status: a finding that returns after `fixed`, or a `declined` one raised again with new evidence, reopens under its old ID.

The coverage table lists each surface from [trust surfaces](trust-surfaces.md) that the project has, with its last disposition — checked, finding IDs, hypothesis, or not covered — and the date and commit it was last examined. The table shows how coverage grew between runs.

## Reports

Each pre-release audit adds `audits/YYYY-MM-DD.md`, with a suffix for a second run that day, and never edits the report of an earlier run; a review adds one only when the owner agrees. Its header gives the date, commit, mode, and scope: what was examined, by source review or authorized active testing, and what was not. Its first section, **Since the previous report**, lists by ID the new findings, the fixed ones, the ones that came back after a fix, the ones still open, accepted risks past their review date, and the ones not checked this time, then the surfaces whose disposition changed. A new finding in code unchanged since the previous report's commit is labelled as newly detected rather than new in the project. The first report says there is no previous one.

An active-testing authorization is recorded in its run's report as history: target, environment, limits, and who granted it as a role or handle. It never authorizes a later run.

## When to write

A pre-release audit writes the notes. A review writes them only when the owner agrees. Development adds no report; it updates only a register row the change fixes, with the check that shows it.

## Reading and closing a run

Before a pre-release audit or review, read the README, `findings.md`, and the latest report. Treat recorded statuses and owner-stated facts as history: recheck a finding before relying on its status, and confirm a deployment fact with the owner when a decision depends on it.

At the end, recheck every `open`, `hypothesis`, and past-review `accepted` row inside the run's scope, set its status, and update its last-checked date. A row the run did not look at keeps its status and date and goes into the report as not checked, never as fixed. Update the coverage table, add the new rows, and write the report.

## AGENTS.md block

When the notes are first created, add this block to the repository's `AGENTS.md` after the repository's own rules, among the other skills' marked blocks, changing only the paths when the notes live elsewhere. When they are not under version control, the location line says so and that they may be absent from a given copy; the rules then apply wherever the notes are present. On later runs, replace only the text between the markers. When `AGENTS.md` is missing, do not create it here: offer to create it through x9-context-files-generator, and name the pending block in the report.

```markdown
<!-- x9-appsec:start -->
## Security

Security notes for this repository live in `docs/security/`.

- Before changing authentication, authorization, handling of untrusted input, secrets, or deployment configuration, read `docs/security/README.md` and the `open`, `hypothesis`, and `accepted` rows of `docs/security/findings.md`.
- When a change fixes a finding there, set it to `fixed` and name the check.
<!-- x9-appsec:end -->
```
