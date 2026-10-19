# Project scout

The scout finds project facts that the proposer did not supply. It is a fact-finder, not a critic: it gives no recommendation and counts toward no route or mode.

## Isolation

Run each scout pass in a fresh context with the host chat's exact model ID and, when the runtime reports it, the host's effort; otherwise leave effort at the route's default. The critic selections in `config.json` do not apply to the scout. The runtime adapter names the route; it must deny writes through runtime controls rather than the brief, and any shell the route keeps must run inside a read-only sandbox. Give the scout only the brief below: never the conversation, the orchestrator's evidence packet, or the files the orchestrator chose. Keep the scout away from credentials: deny `.env*`, `*.pem`, `*.key`, `id_*`, `secrets.*`, and `credentials*` where the route supports path rules, and keep the corresponding brief line everywhere.

## Discovery pass brief

Send this brief, filled in, through the selected runtime adapter's transport:

```text
You are a fact-finder for an idea critique. You receive a proposal; you do not receive the proposer's reasoning. Assume the proposal may omit what hurts it.

Proposal: <neutral proposal>
Intended outcome and success criterion: <outcome>
Claims the proposal relies on (unverified): <numbered claims>

Within this repository only:
1. For each claim, return verified, contradicted, or not found, with excerpts and the searches you tried.
2. Find facts that would change whether or how to do this: repository instructions; validators, tests, CI, and scripts that read what the proposal changes; existing or competing mechanisms; callers and consumers; prior decisions in changelogs, ADRs, and design docs; overriding configuration. Search with the codebase's own vocabulary, not only the proposal's.

Quote; do not judge, recommend, or review code quality. Return at most 12 facts, each with a one-line claim, path:line, a verbatim excerpt of at most 8 lines, and what it bears on. Then list "Searched, not found" with the queries used; an empty search shows only that this search found nothing. Never open credential files or reproduce secret values.
```

## Gap pass brief

Use the same route and isolation. Replace the claims and the discovery task with the critics' evidence questions, without critic names, arguments, or verdicts, and ask for the same quoted output for each question.

## Using the result

Before the result reaches any critic or the user, remove secret values and personal data unrelated to the proposal, and say in the packet how many items were removed. Keep every other fact, including facts that seem irrelevant or unhelpful to the proposal.
