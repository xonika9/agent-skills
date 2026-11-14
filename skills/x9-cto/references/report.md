# Report

The owner reads a report, often on a phone, to learn what changed, which
problems exist and whether each is in hand, and what the CTO decided alone,
without having to ask again. Selected by `x9-cto pilot report` or by an owner
request for a report or status over a period, in any CTO chat; a running pilot
is not required. Reports are produced on request only.

## Contents

- [Period](#period)
- [Verify at report time](#verify-at-report-time)
- [Problems](#problems)
- [Items](#items)
- [CTO decisions](#cto-decisions)
- [Content, in order](#content-in-order)
- [Form](#form)

## Period

From the previous report to now. The repository's pilot owner names where the
previous report's time is kept; record the new time there after delivering the
report. Without a recorded time, cover the last 24 hours and say so in the
header. A period the owner names replaces the default.

## Verify at report time

The chat's memory and the shared state card lag behind the work, so every state
in the report comes from sources read for this report. Through the sources the
repository's pilot owner lists, or without one the repository's own state
sources, named in the header, read:

- the board: cards finished in the period, cards in progress and blocked;
- merges into the main branch in the period;
- the newest accepted deploy receipt against the main branch tip, which tells
  what is on the server;
- the end of every chat working on started work, collected by a
  fact-extraction worker as on a tick;
- decisions recorded in the period.

An item that could not be checked says `Не сверено:` and what was not checked;
it is never filled from memory. The header names the check time and, when
chats were read at different times, which state is older.

## Problems

A problem is red when it affects people now, or when the CTO has no plan for
it; otherwise it is yellow: the remedy is known and under way. Every problem
carries:

- labels: whether it affects people, what it slows or risks, and `срок не
  назван` when no executor named a time;
- what is broken;
- what it threatens for the owner, users, money, or time;
- what is being done, by whom, with the chat link;
- when to expect the result, and what makes a yellow problem red.

A red problem without a plan says `Плана пока нет`, what is being done to find
one, and the owner question it needs.

## Items

Every item carries its card link, its chat link while work runs, and its state:
on the server; in the main branch, waiting for deploy; with the merge train;
running, with the current stage of plan, code, review, checks, merge, server,
the step, and the expected finish when the chat named one; or stopped, with
what it waits for. An item without a card says so. A finished item says in one
line what it gives the user or the team.

## CTO decisions

For each decision the CTO made alone in the period:

- what was decided;
- why, in words the owner understands without reading the canon; a departure
  from an accepted principle names the principle and the condition that allows
  it;
- what it changes for users, money, or risk;
- what follows: the work the decision depends on or starts, with its state;
- the link to its decision record, when one exists.

A reason resting on a fact that can change, such as a measurement, a price, an
external offering, or another party's resource use, carries the date the fact
was checked; a fact checked before the period began is checked again or marked
`Не сверено:`. Minor technical records share one line.

## Content, in order

1. Header: period, check time, and counters: red problems, yellow problems,
   work running, work finished.
2. `Главное за сутки` (or for the period): two or three factual sentences on
   what changed for users and what slows the work, without reassurance or
   verdicts; then owner questions count, whether all merged code is on the
   server, and the numbers of merges, deploys, and decisions.
3. Problems, each fully expanded.
4. Running work, collapsed, in two groups, product then infrastructure; its
   summary names how many are in each stage.
5. CTO decisions, collapsed.
6. Finished in the period, collapsed, grouped into product and infrastructure.
7. Next: the first entries of the queue, each with what it gives.

Order within each block is fixed, so two reports read the same way and the
writer's taste does not decide what the owner sees first:

- problems: red before yellow; within a color, those affecting people, then
  money, then the pace of work;
- running work, in each group: the later stage first; at an equal stage, the
  earlier start first;
- CTO decisions: those whose follow-up is still pending, then those in effect;
- finished work, in each group: what people notice first;
- next: the queue's own order.

Shortening never drops what an item gives, its state, its plan, or its links:
the owner should not need to ask.

## Form

Where the runtime renders an HTML page inline in the chat, deliver the report as
that page, built from [the page template](../assets/report-page.html), and check
it at phone and desktop widths before showing it; the page uses the template's
drawn icons and status colors, the runtime's theme variables, and carries no
icons in section headings. Otherwise deliver one chat message with the same
content and order, where every fact is its own list item and every work title is
its own line, because single line breaks collapse into one paragraph.
