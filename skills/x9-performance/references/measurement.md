# Measurement

Change one thing and decide whether to keep it. A worker runs the measurements and writes the raw numbers to a file outside the repository.

## Unit

One scenario with its conditions recorded: commit, build mode, machine, load, cold or warm start, versions. In a browser, one user action on a production build, read from a trace. On a server, percentiles over many requests in a run; report a percentile only with about 20 samples beyond it, together with the request count, duration, and unfinished requests.

## Keep rule

Alternate before and after runs under identical conditions, with the count fixed in advance: 5 per side, or 3 when the spread is at most half the minimum gain or the removed work visibly disappears from the trace. A count that does not vary between runs, such as bytes, queries, or tokens, needs one run per side.

- **Better:** every after-run beats every before-run, and the median improves by at least the minimum gain. Keep the change.
- **Not confirmed:** anything else. Revert, or declare a larger comparison in advance within the budget.

Measure guard metrics in the same runs; name any guard that could not be measured in the verdict, and let the owner decide. Stop a run that takes three times the baseline duration and count it as failed.

## Known waste

Before removing a sleep, poll, retry, or serial step, record why it exists and what condition it stood in for — a readiness signal, a notification, a completed write — and wait for that condition instead.

## Fake wins

Reject a gain that moves the cost to where the same person or system still pays it, hides work outside the measured window, or needed a test changed. Moving request-independent work earlier is legitimate under [locate](locate.md#time-of-one-operation).

## Order of work

Check correctness before the metric. Change one thing at a time. After a kept change, re-measure the whole scenario: the main cause moves. Record every attempt, including reverted ones, in the journal described in [notes](notes.md). Runs on a shared staging environment go one at a time, with rollback.

## Handing off to ce-optimize

When the target is code measured by a local command, several variants should be searched, and ce-optimize is installed, read its spec schema from the installed skill and write a spec with the metric, guard metrics, minimum gain, serial execution when the metric is time, and the measurement harness in its immutable scope. Then run ce-optimize with that spec; its own approval gate is where the owner agrees to its branch and commits. Afterwards, record its kept and reverted experiments in the journal. If the schema cannot express the guards, run the experiment here.

## Done

Each attempt has a journal entry with its verdict, kept changes pass the project's checks, and what was not verified is named.
