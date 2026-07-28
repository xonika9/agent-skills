# Focused skill questions

Ask only for information that cannot be recovered from the request, existing skill, repository, or runtime. One question at a time; stop when the contract is implementable.

## Blind spots for a new skill

Check before writing:

- overlap with an existing skill;
- scope broad enough to contain unrelated jobs;
- missing near-miss or authority boundary;
- fragile repeated operation left in prose;
- claimed runtime/tool behavior not verified;
- no observable way to tell success from failure.

Surface only blind spots that plausibly apply. Do not perform an interview ritual for a complete request.

## Load-bearing questions

- What real user phrases should trigger it, and what adjacent request should not?
- Which runtimes and canonical location?
- What inputs and artifacts are in scope?
- What actions may change local or external state?
- Which step is deterministic enough to require a script?
- What exact evidence separates complete, degraded, and failed?
- Which existing skill already owns part of this contract, and what stays a link to it rather than a copy?

## Existing-skill action

Infer intent and runtime from the existing skill when clear. Choose `Audit` for report-only work and `Fix` for authorized changes; confirm only if the request leaves that distinction load-bearing and ambiguous. Known complaints guide the scenarios but do not replace the full rubric.
