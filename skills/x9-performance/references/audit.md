# Audit

Use when the person does not know what is slow or wasteful. The result is a ranked report in plain words, saved in the notes.

## Map the product

One worker maps what the product does and where it runs: the main user paths (open a page, sign in, send, upload, download), service startup, background jobs, the local development loop, and which data is reachable — logs, metrics, traces, the bill. Ask the owner one question: what matters most, and where may measurements run — locally only, on a staging environment, or against production logs? Without an answer, take the main user paths and measure locally only.

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

Write in plain words. For each item give what is wrong, who pays, its size with the evidence label, fix cost, confidence, and how a fix would be verified. Group the items:

- **Cheap fixes:** local, verifiable, and without a change to architecture, cost, or shared systems.
- **Owner decisions:** fixes that change architecture, cost, or shared systems, with the expected payoff and the price.
- **No data:** candidates that failed only the evidence condition, with what to start collecting.

List the checked and rejected candidates with the condition each failed.

## Audit and fix

When the request also asks to fix, take the cheap fixes one at a time through Optimize, largest payoff first. After several kept changes, re-measure the main paths, because the picture shifts. End with a before-and-after table per item, including reverted attempts and why.
