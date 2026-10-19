# Repository context

Resolve local context only to the depth the current request needs. Applicable
repository instructions already supplied by the runtime are the starting point;
do not require a new profile or a complete repository inventory for a quick fact.

## Questions to resolve

- Which sources own product requirements, architecture, accepted decisions,
  document placement, and accepted evidence?
- Which source owns current task state and work order, when coordination matters?
- Which execution and acceptance workflow closes this outcome?
- Which decisions or actions remain reserved for the owner?
- Which local handoff kinds or other CTO-specific instructions apply?

Use explicit ownership declarations and the task's accepted contract. Load the
optional block between `<!-- x9-cto:start -->` and `<!-- x9-cto:end -->` when
present in the applicable `AGENTS.md`; it adds local information, not a second
inventory of the repository. A skill named there is loaded by its discoverable
name before resolving one of its bundled references.

Where no declaration answers a needed question, inspect the relevant local
documentation index and code with a bounded search. A filename, recent edit, or
the fact that a script exists does not establish authority. A source not found
is not proven absent. Report a load-bearing unknown instead of inventing an
owner, a tracker, a command, a release procedure, or a standing permission.

## Missing sources and conflicts

In a small repository with no declared persistent canon or tracker, the current
request and code may suffice for advice. State material limits. A recommendation
does not become accepted policy because the CTO gave it; missing documentation
does not authorize creating it during consultation.

An explicitly required source that is missing, stale, or inaccessible stops the
dependent action. Do not replace it with an old note, a reconstruction, or an
assumption. A current authoritative redirect may resolve a moved path; verify
the actual target and applicability rather than substituting a similar file.
Continue independent authorized work and leave the affected condition unproven.

Resolve conflicts through the declared ownership and applicable instruction
hierarchy. Do not choose by date or filename. When authority remains ambiguous,
name the competing sources and stop the dependent action for the owner's
decision. A route to a source cannot create authority or expand a mode's allowed
write set. The local handoff contract may carry a scoped grant already supplied
by the owner; retain its exact actor, conditions, and withheld actions.

## Recording and configuring

Route an authorized result to its existing canonical owner; where the
repository canon names another location, the canon is the `source of truth`. If
none exists, propose the smallest appropriate location. Do not create a parallel
decision ledger, task-state file, or cached tracker in the CTO block.

Record only what became a decision, principle, or working direction, and do not
bloat documents. A disputed decision goes only into a brainstorm, research, or
temporary note; an accepted and stable one updates the canonical document. Keep
temporary, exploratory, or post-release topics out of the main canon, and do not
rewrite canonical documents while the discussion has not closed the disputed
question.

Creating or updating CTO integration follows the
[marked-block contract](agents-block.md). Ordinary advice does not write it.
