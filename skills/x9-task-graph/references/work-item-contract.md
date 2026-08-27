# Work-item contract

Load this reference after the input gate accepts an approved plan. It defines the draft artifact; it does not authorize saving or publishing it.

## Source ledger

Extract the plan's known requirements, accepted decisions, and implementation or work units into a source ledger before mapping them. Retain each source identifier and its meaning. If the source lacks stable identifiers, assign draft-local labels and show the exact source heading or quotation that they represent.

Treat a contradiction as an input-gate failure, not a mapping choice. Treat a source element already explicitly complete, deliberately out of scope, or not actionable as an exclusion only when that status is supported by the approved plan; record why it has no independent work item.

## Vertical work items

Each work item is a tracer bullet: the smallest outcome-oriented slice that can move one user-visible or operational result from start to finish within the accepted plan. It may cross layers when that is necessary for the outcome. Do not make layers, teams, or file types the primary slicing rule.

Give every item a stable draft ID such as `WI-01`, then include:

- **Title and outcome slice:** a concise result, not an activity list.
- **Sources:** requirement IDs, decision IDs, and source-unit IDs that this item traces.
- **Dependencies:** predecessor work-item IDs and the source reason for each edge; use `none` when there is no predecessor.
- **Frontier:** `ready` only when all dependencies are resolved and no blocker remains; otherwise state the nearest prerequisite work item or blocker.
- **Blockers:** unresolved source ambiguity, unavailable prerequisite, or external dependency; use `none known` only when the source supports that conclusion.
- **Acceptance:** observable conditions drawn from the plan's verification and acceptance material.
- **Risks and mitigation:** material delivery risks already present in the plan and the source-consistent response; never create a new product decision as mitigation.

Keep independent ready items on the same frontier. An edge represents a real prerequisite, not a convenient delivery order.

## Tracker-ready form

For every work item, present a tracker-ready draft that can be copied without reconstructing its contract:

```markdown
ID: WI-01
Title: <outcome-oriented title>
Outcome: <vertical slice>
Sources: R..., D..., U...
Depends on: WI-... | none
Frontier: ready | blocked by <work item or blocker>
Blockers: <none known or concrete blocker>
Acceptance:
- <observable condition>
Risks / mitigation:
- <risk> — <source-consistent mitigation>
```

This form is a draft, not a tracker object. Preserve unknown tracker-specific fields rather than inventing owners, dates, estimates, labels, or project settings.

## Coverage matrix

Append one matrix that accounts for every entry in the source ledger. Use one row per known requirement, decision, and source work unit:

| Source kind | Source ID | Covered by work item IDs | Exclusion or mapping explanation |
| --- | --- | --- | --- |
| Requirement | R1 | WI-01 | Direct trace |
| Decision | D2 | WI-01, WI-03 | Split: each item carries a distinct accepted consequence |
| Work unit | U4 | WI-02 | Merged with U5 because both are one indivisible outcome slice |

Each row must name at least one work-item ID or give a source-supported exclusion. Explain every split and merge in the final column. A matrix with an unaccounted source entry is incomplete even if the graph otherwise looks plausible.

## Draft layout

Return, in order:

1. Source identity and approval evidence.
2. Work-item graph: the items and their dependency edges.
3. Current frontier and blockers.
4. Tracker-ready forms.
5. Coverage matrix and any explained exclusions.

The draft is complete only when a reader can trace each source ledger entry through the matrix to a work item or an explained exclusion, and inspect each item's acceptance conditions without consulting unstated assumptions.
