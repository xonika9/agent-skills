<!-- x9-context-files-generator:sources-of-truth:start -->
## Sources of truth and decisions

Shared rules from the `x9-context-files-generator` template. Edit only Local, which takes precedence; the rest is replaced when the template changes.

- Each kind of project information has one owner, listed in Local. Other files link to the owner instead of restating it.
- Current state, open problems, and the order of work belong to the state owner named in Local.
- Acceptance stays in Git, tied to a commit and a report. On state and order the state owner wins; on whether something is accepted or decided, the acceptance registry and the decision log win.
- A decision is `accepted` only through an explicit owner confirmation or a delegation recorded in the decision log. A proposed form stays a proposal until the decision log records the decision. Change the decision log only for a new owner decision or for evidence that changes an existing decision.
- Research is dated supporting evidence and the archive is historical evidence; neither overrides the active canon.
- Before planning, read the state owner, the acceptance registry, and the decision log. Do not reopen a completed gate or an accepted decision without contradictory evidence.
- Keep replaceable implementation checkpoints out of the product and architecture canon until their owning gate records an outcome.

### Local

- Requirements: <path>
- Decision log: <path>
- Architecture boundaries: <path>
- State owner (current state, open problems, order of work): <tracker, board, or card>
- Acceptance registry (accepted work and its evidence, assigned work IDs): <path>
- Research and archive: <paths>
- <who may accept decisions on the owner's behalf, and within which limits>
<!-- x9-context-files-generator:sources-of-truth:end -->
