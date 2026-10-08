# Test audit

Find existing tests that re-assert source, duplicate stronger proof, couple behavior to implementation, or keep test-only production seams alive, and remove or repair them without losing protection. The judgment rules are the [junk patterns](../SKILL.md#junk-patterns) and the [retention bar](../SKILL.md#retention-bar); this file adds how to search, what evidence a change needs, and how to land it. Optimize for confidence, not deletion count.

## Discovery

Keep discovery read-only and record evidence before editing; stop for approval only on an audit request. For a broad scope, run parallel read-only lanes when the runtime supports them, split along production owner boundaries (for example core libraries, plugins or integrations, apps and tooling) plus one cross-cutting pattern sweep. Lane workers do not edit, run mutating commands, or delegate further.

Outside a campaign, prefer a few high-confidence candidates over a large speculative inventory. An existing test that must change for a behavior-preserving source reorganization is a candidate, not automatically deletable.

## Candidate evidence

Scale the evidence to what removing the test could lose.

A test that cannot fail (assertion-free, a pure self-comparison, a swallowed exception, a property test with zero cases) needs only its location, why it cannot fail, and the command that validates the change.

Removing or rewriting a test that can fail needs, before editing:

- exact test name and location;
- what failure it can actually detect;
- non-test callers of the covered production or support seam;
- stronger remaining owner-boundary proof, or why no proof is needed;
- the reason the test or seam exists, from its history when the reason is not evident;
- production or test-support deletion unlocked;
- risk and the focused validation command.

For these, read the complete test and its production owner, the owner's entry point, callers, callees, sibling implementations, overlapping tests, and CI routing, plus any scoped instruction files governing those paths. When the test claims dependency-backed behavior, inspect the dependency source or types directly. A test that resembles implementation may still be the only independent proof of a contract; prove otherwise before removing it. A retained test that fails on the baseline is reproduced and repaired at its owner.

## Edit shape

Choose one coherent owner-boundary batch. Delete obsolete test-only exports, globals, wrappers, and dead production paths whose only callers are tests, instead of preserving aliases; removing code that exists only for tests is a goal, line counts are not. Move retained regressions to their canonical owners. Consolidate repeated package or dependency assertions into one generic contract.

Do not add replacement tests that restate the same implementation, and do not turn uncertain candidates into cleanup to increase deletion counts.

## Validation

For an audit batch, beyond [checking your work](../SKILL.md#checking-your-work):

- for each removed source grep or plan assertion, the executable script, build, or dry-run that owns the real contract passes;
- each changed test configuration or CI rule is exercised: the selection, timeout, or gate it defines demonstrably applies;
- targeted formatting is clean and `git diff --check` passes;
- the repository's changed-files or pre-merge gate passes, or, without one, the checks its policy requires for the changed paths;
- when the batch removes tests that could fail, a fresh-context review of the final diff found no contract that lost its only proof and no new assertion that cannot fail; report it as not run when no independent reviewer is available.

## Landing and continuation

Land one coherent batch per change set, only as far as the [authority](../SKILL.md#authority) allows and under the repository's commit and pull-request policy. Afterwards, offer the next high-confidence batch; do not start it unasked.

## Handoff

Report:

- removed low-value categories and their root cause;
- production owner simplifications;
- retained false positives and why they remain valuable;
- proof actually run, and checks not run;
- production versus test lines changed;
- commit, pull-request, and merge state, or that none was requested;
- named follow-ups.
