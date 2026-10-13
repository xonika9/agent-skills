# Project notes

Performance work leaves notes in the project, so the next agent starts from what is already known instead of repeating dead ends or removing a guard someone already explained. When the project already has a place for research or evidence notes, keep these notes in a `performance/` folder inside it, so no existing file is overwritten; otherwise use `docs/performance/`.

## Layout

- `README.md` — how to work on performance in this project: how to start a production-like build, how to measure each main path (commands, where timing marks and logs are), what may run locally and what is paid or shared, and known traps. Change it when the way of measuring changes; keep current numbers out of it.
- `journal.md` — append-only, one entry per attempt: date, commit, change, conditions, before and after numbers, verdict, and reason. Reverted attempts and dead ends are recorded too.
- `audits/YYYY-MM-DD.md` — each audit's report, with the before-and-after table when fixes followed.

Raw measurement data stays outside the repository, such as in the system temporary directory; the notes hold summaries and say where the raw data was. A guard found in code — a wait, retry, or limit that protects a condition — is recorded in the notes; when work changes code at that guard, it also gets a comment there naming the condition.

## When to write

Audit and any work that changes code write the notes. A question that only locates a cause writes them after the owner agrees.

## Reading

Before Audit or Optimize, read the README, the recent journal entries, and the latest audit. Do not retry an approach the journal rejects without new evidence. Treat recorded numbers as history: re-measure the baseline on the current code before comparing against it.

## AGENTS.md block

When the notes are first created, add this block to the repository's `AGENTS.md`, changing only the path when the project keeps its notes elsewhere. On later runs, replace only the text between the markers. When `AGENTS.md` is missing, do not create it here: offer to create it through x9-context-files-generator, and name the pending block in the report.

```markdown
<!-- x9-performance:start -->
## Performance

Performance notes for this repository live in `docs/performance/`.

- Before changing code for speed, memory, load, or cost, read `docs/performance/README.md` and the recent entries of `docs/performance/journal.md`; do not retry an approach the journal records as rejected without new evidence.
- Keep any wait, retry, or limit that the notes or a code comment mark as a guard, unless the condition it protects is handled another way.
- Claim a performance gain only with before-and-after numbers measured as `docs/performance/README.md` describes, and record the attempt in the journal, including reverted ones.
<!-- x9-performance:end -->
```
