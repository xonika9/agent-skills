# Audit

Use when the person does not know what is slow or wasteful. The result is a ranked report in plain words, saved in the notes.

## Map the product

One worker maps what the product does and where it runs: the main user paths (open a page, sign in, send, upload, download), service startup, background jobs, the local development loop, and which data is reachable — logs, metrics, traces, the bill. Use the priorities and allowed places the owner already gave; otherwise take the main user paths and measure locally only, without stopping to ask.

## What counts as bad

Without a named complaint, judge against:

- waits a person feels: about 0.1 s feels instant, about 1 s is noticed, after about 10 s attention leaves; web thresholds for main content and input response change, so take them from current documentation;
- waste that is bad at any size: fixed sleeps, polling where a notification exists, the same query repeated, queries inside loops, independent work awaited in sequence, development builds served to users;
- growth: memory per repeated action, time or cost per request rising with history or data size;
- the owner's priorities.

## Sweep

Reading workers run in parallel, one per area: server and database; client; startup and infrastructure; background jobs and the development loop; resources and money. Each returns candidates in the reply format from SKILL.md. Then one measuring worker runs each main path 3–5 times, cold and warm, on a production build, and records memory and size, inside the budget.

## Select

A candidate enters the report only when all of these hold:

1. someone pays for it: a person waits, the system degrades at its expected load, or resources or money are spent;
2. it is frequent or large;
3. evidence exists;
4. the cause is under the project's control;
5. a fix exists that keeps correctness and isolation;
6. before and after can be measured.

Rank by size and frequency against fix cost.

## Report

The saved audit file is the full report, with the header and the comparison with the previous report that [notes](notes.md#reports) describes. Write it in plain words. For each item give its register ID, what is wrong, who pays, its size with the evidence label, fix cost, confidence, and how a fix would be verified. Group the items:

- **Local fixes:** changes inside the project that keep what users see and do, the data formats others read or the project stores, and the running cost. Size does not matter: an internal restructuring, a build setting, or a reused connection is a local fix.
- **Owner decisions:** fixes that spend money, touch a shared or non-local system, or change what users see or do, a stored or exchanged data format, or a capability, with the expected payoff and the price.
- **No data:** candidates that failed only the evidence condition, with what to start collecting.

List the checked and rejected candidates with the condition each failed.

## Reply to the owner

The chat reply lets an owner who does not read profiles choose the next step without opening the file, in the language SKILL.md sets for [the message that ends a turn](../SKILL.md#the-message-that-ends-a-turn). Leave budgets and unmeasured areas to the file unless they change the conclusion. Give, in order:

1. The verdict in one or two sentences: whether anything needs action, which paths were measured where, and, after an earlier audit, what was fixed, what is new, and what came back since then.
2. The recommended fixes, largest payoff for cost first: what is wrong, where, what improves for whom, and how sure.
3. Owner decisions and any fact the fixes need, each as a question; a decision has 2–4 options and the recommended one with its reason.
4. What to leave alone or measure first, one line each.
5. How to start: which items a plain go-ahead covers.

## Audit and fix

When the request also asks to fix, every local fix is in scope, not only the cheapest. Before the report is final, measure each candidate whose missing evidence can be produced locally within the budget, and place it by that result.

When the report has owner decisions or the fixes need a fact without a safe default, stop once after the audit with the reply above, so the fixes run as one pass that includes the owner's choices; otherwise go straight to the fixes. Take the local fixes and the chosen options one at a time through Optimize, largest payoff first, within the authority in SKILL.md; the audit's scope and defaults stand in for the metric confirmation. After several kept changes, re-measure the main paths, because the picture shifts.

The run is done when every item in the report is kept, reverted with its reason, declined by the owner, or stopped by the budget with what it would need, and the register shows each item's resulting status. The audit file ends with a before-and-after table per item, including reverted attempts and why; the reply gives the fix result from SKILL.md.

When the owner hands the fixes to a separate planning or implementation workflow, pass each agreed item with its metric, scenario, guard metrics, and verification, so the plan keeps before-and-after measurement and the journal entries.
