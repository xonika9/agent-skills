# Project notes

Audits and campaigns leave notes in the project, so the next run starts from what is already known, a long campaign survives a lost context, and the owner sees how the test setup changed between runs. Keep them in `docs/testing/` unless the project keeps such documents elsewhere. The adopted rules and commands belong to the [testing policy file](project-audit.md#testing-policy-file), not to these notes; the notes link to it rather than restating it.

## Layout

- `findings.md` — the register of findings, described below, and the quarantine snapshot.
- `audits/YYYY-MM-DD.md` — each project audit's or test audit's report, described below.
- `campaigns/<subsystem>/` — one folder per [campaign](campaign.md): the baseline, the lane list, each lane's ledger and plan, and which step each lane has completed. A resumed campaign continues from here.

Raw run output stays outside the repository; the notes hold summaries and say where the raw output was.

## Findings register

`findings.md` holds the current state of every finding recorded in the project, one row each: ID, what is wrong and where, priority, status, first seen, last checked, and the report or change that last set its status. IDs take the form `TQ-<n>`, are assigned in order, and are never reused or renumbered, so a finding keeps its ID when its wording changes. Named follow-ups from a test audit or campaign go in as `open` rows.

Statuses:

- `open` — found and not fixed;
- `fixed` — a check on the current code shows it gone; name the check;
- `declined` — the owner chose not to act, with the reason; do not propose it again without new evidence;
- `obsolete` — the code or setup it concerned no longer exists.

Before giving a finding a new ID, match it against rows of every status: a finding that returns after `fixed`, or a `declined` one raised again with new evidence, reopens under its old ID.

Each project audit rebuilds the quarantine snapshot from its inventory, since the tests themselves stay the source of truth: every quarantined test with its owner, issue, and expiry. A test past its expiry, or missing what the [scale](project-audit.md#flaky-tests) requires, is a finding.

## Reports

Each project audit or test audit adds `audits/YYYY-MM-DD.md`, with a suffix for a second run that day, and never edits the report of an earlier run. Its header gives the date, commit, mode, and scope: what was inspected and what was not. Its first section, **Since the previous report**, lists by ID the new findings, the fixed ones, the ones that came back after a fix, the ones still open, and the ones not checked this time. A new finding in code unchanged since the previous report's commit is labelled as newly detected rather than new in the project. The first report says there is no previous one.

A project audit report also records the suite health numbers its [scale](project-audit.md#scale-and-scope) enables, so progress shows in numbers: from the slowest tests for a solo project up to tests per size class, full-suite and change-request feedback time, the flaky rate, and skip and quarantine counts with the oldest age. Take each number from a cheap local run or CI history and give its source; one that would need a long run is marked not measured.

## When to write

Project audits, test audits, and campaigns write the notes. Ordinary work, such as writing a test during a change, adds no report; it updates only a register row the change fixes.

## Reading and closing a run

Before an audit or campaign, read `findings.md`, the latest report, the testing policy file when one exists, and for a campaign its folder. Treat recorded numbers and statuses as history: recheck a finding before relying on its status.

At the end, recheck every `open` row inside the run's scope, set its status, and update its last-checked date. A row the run did not look at keeps its status and date and goes into the report as not checked, never as fixed. Then add the new rows and write the report.

## AGENTS.md block

Add or refresh this block only when the task authorizes changing repository instructions; otherwise include the proposed block in the report. When the notes are first created under that authority, add this block to the repository's `AGENTS.md` after the repository's own rules, among the other skills' marked blocks, changing only the paths when the project keeps these files elsewhere and dropping the policy-file clause when it does not exist. On later runs, replace only the text between the markers. When `AGENTS.md` is missing, do not create it here: offer to create it through x9-context-files-generator, and name the pending block in the report.

```markdown
<!-- x9-test-quality:start -->
## Testing

The testing rules for this repository are in `TESTING.md`; audit notes live in `docs/testing/`.

- Before changing the test setup, CI test stages, or quarantine, read `docs/testing/findings.md`; do not reintroduce a finding recorded as `fixed` or propose one recorded as `declined` without new evidence.
- When a change fixes a finding in `docs/testing/findings.md`, set it to `fixed` and name the check.
<!-- x9-test-quality:end -->
```
