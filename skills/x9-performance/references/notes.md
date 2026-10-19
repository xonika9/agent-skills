# Project notes

Performance work leaves notes in the project, so the next agent starts from what is already known instead of repeating dead ends or removing a guard someone already explained, and the owner sees what changed between runs. When the project already has a place for research or evidence notes, keep these notes in a `performance/` folder inside it, so no existing file is overwritten; otherwise use `docs/performance/`.

## Layout

- `README.md` — how to work on performance in this project: how to start a production-like build, how to measure each main path (commands, where timing marks and logs are), what may run locally and what is paid or shared, and known traps. Change it when the way of measuring changes; keep current numbers out of it.
- `findings.md` — the register of audit findings, described below.
- `journal.md` — append-only, one entry per attempt: date, commit, change, conditions, before and after numbers, verdict, and reason. Reverted attempts and dead ends are recorded too. An entry that changes a finding names its ID.
- `audits/YYYY-MM-DD.md` — each audit's report, described below, with the before-and-after table when fixes followed.

Raw measurement data stays outside the repository, such as in the system temporary directory; the notes hold summaries and say where the raw data was. A guard found in code — a wait, retry, or limit that protects a condition — is recorded in the notes; when work changes code at that guard, it also gets a comment there naming the condition.

## Findings register

`findings.md` holds the current state of every finding recorded in the project, one row each: ID, what is wrong and where, size with its evidence label, status, first seen, last checked, and the report or journal entry that last changed it. IDs take the form `PERF-<n>`, are assigned in order, and are never reused or renumbered, so a finding keeps its ID when its wording changes. Every item of an audit report gets a row; rejected candidates stay in the report only.

Statuses:

- `open` — found and not fixed;
- `hypothesis` — a candidate without evidence yet, with the measurement that would decide it;
- `fixed` — a check on the current code shows it gone; name the check;
- `declined` — the owner chose not to act, with the reason; do not propose it again without new evidence;
- `obsolete` — the code or setup it concerned no longer exists.

Before giving a finding a new ID, match it against rows of every status: a finding that returns after `fixed`, or a `declined` one raised again with new evidence, reopens under its old ID.

## Reports

Each audit adds `audits/YYYY-MM-DD.md`, with a suffix for a second audit that day, and never edits the report of an earlier run. Its header gives the date, commit, and scope: which paths were measured where, and what was not checked. Its first section, **Since the previous report**, lists by ID the new findings, the fixed ones, the ones that came back after a fix, the ones still open, and the ones not checked this time. A new finding in code unchanged since the previous report's commit is labelled as newly detected rather than new in the project. The first report says there is no previous one. When earlier audits exist but `findings.md` does not, first build the register from the latest audit's items, then compare against that audit.

## When to write

Audit and any work that changes code write the notes. A question that only locates a cause writes them after the owner agrees. Work outside an audit adds no report; it updates the register rows it changes.

## Reading and closing a run

Before Audit or Optimize, read the README, `findings.md`, the recent journal entries, and the latest audit. Do not retry an approach the journal rejects without new evidence. Treat recorded numbers and statuses as history: re-measure the baseline on the current code before comparing against it, and recheck a finding before relying on its status.

At the end of an audit, recheck every `open` and `hypothesis` row inside the run's scope, set its status, and update its last-checked date. A row the run did not look at keeps its status and date and goes into the report as not checked, never as fixed. Then add the new rows and write the report.

## AGENTS.md block

Add or update this block only when the user has authorized changes to repository instructions; an audit or locating request alone does not grant that authority. Otherwise include the proposed block in the report without changing `AGENTS.md`. For an authorized first insertion, place it after the repository's own rules, among the other skills' marked blocks, changing only the path when the project keeps its notes elsewhere. On later authorized updates, replace only the text between the markers. When `AGENTS.md` is missing, do not create it here: offer to create it through x9-context-files-generator, and name the pending block in the report.

```markdown
<!-- x9-performance:start -->
## Performance

Performance notes for this repository live in `docs/performance/`.

- Before changing code for speed, memory, load, or cost, read `docs/performance/README.md`, `docs/performance/findings.md`, and the recent entries of `docs/performance/journal.md`; do not retry an approach the journal records as rejected without new evidence.
- Keep any wait, retry, or limit that the notes or a code comment mark as a guard, unless the condition it protects is handled another way.
- Claim a performance gain only with before-and-after numbers measured as `docs/performance/README.md` describes, and record the attempt in the journal, including reverted ones. When the change fixes a finding in `docs/performance/findings.md`, set it to `fixed` and name the check.
<!-- x9-performance:end -->
```
