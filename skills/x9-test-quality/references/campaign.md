# Test-pruning campaign

Campaign mode prunes one subsystem's whole test surface: a plugin, an integration, or one core area. Land it as one change set, or as one per lane once that lane's keepers pass when the repository prefers smaller changes. The [retention bar](../SKILL.md#retention-bar) and the [test audit](test-audit.md) evidence and validation apply to every lane; step 6's preservation review replaces the per-batch fresh-context review. This file adds the order of work and the lessons of a full campaign. Each step ends on its completion criterion; do not start the next step early.

## 1. Baseline

Record the subsystem's test and support line counts and every test file's pass/fail state at a pinned main-branch commit. Keep baseline failures in their own list: they are often real product bugs rather than stale tests.

Done when every in-scope test file has a recorded baseline result.

## 2. Lanes and inventory

Split the surface into **lanes** along production owner boundaries, not file prefixes. For a messaging integration these might be accounts, commands, context, dispatch, inbound, outbound, persistence, transport, shared code, the test harness, and live or QA scenarios. Include the subsystem's cases at shared core boundaries and its QA and live-proof harness tests.

Done when every test file and QA scenario the subsystem owns belongs to exactly one lane.

## 3. Read-only ledger per lane

Give each lane to its own read-only worker when the runtime supports delegation; otherwise work through the lanes in turn. The worker reads every assigned test in full, including parameter tables. It also reads the production owners and their entry points, callers, history, and CI routing. Each test declaration goes into a written **ledger** with one mark. A parameterized test is one declaration unless its rows need different marks; then mark each row.

- `R`: retain, naming the contract and the bug it catches; a retained test that only moves to a better-named file stays `R` with the move noted;
- `F`: retain the contract but repair the assertion, such as a vacuous negative that passes when only one of several items is missing;
- `C`: consolidate, naming the owner that absorbs the assertion first: a sibling table case, a stronger boundary suite, or the shared owner in another package;
- `D`: delete, naming the proof that remains, or why no contract exists.

Judge a test by its assertions, not its name: a test named for retiring a progress window can turn out to assert that the window was _not_ cleared.

Done when every declaration in the lane has a mark and an evidence line.

## 4. Layer plan per lane

Treat the per-test ledger as input, not as the edit list. A second read-only pass, starting from the ledger, looks for the redundant **layer**, such as several suites replaying the same shared component through one mocked collaborator around stronger real-stream or recorded-network suites. Name the **keeper** suite for each contract. Prefer the real transport boundary with a fake network over a mocked collaborator. Correct any ledger errors this pass finds.

Done when each lane plan names its retired files, its keeper per contract, the assertions to carry into keepers, and the test-only production seams unlocked.

## 5. Cutover

Edit lane by lane. Serialize changes to shared harnesses and support files through one owner. With each lane, remove the test-only production seams it unlocks: injection parameters, getters, reset exports, and indirection layers. Register moved suites in any CI routing or test inventory the repository keeps, and lower any shrink-only size baselines it tracks. Propose durable test-ownership rules drawn from mistakes this campaign actually found, for the subsystem's testing policy file when one exists; otherwise list them as a follow-up.

Done when every lane plan is applied and each lane's keepers pass.

## 6. Preservation review

Before claiming completion, have independent fresh-context reviewers compare deleted coverage against the keepers, one reviewer per boundary group. They look for contracts that lost their only proof and for new assertions that cannot fail, such as a rejection row the production code never reaches. Expect real gaps; a large campaign rarely has none.

For each restored contract, make one deliberate **mutation** of the production owner and confirm the keeper goes red. Then restore the source byte for byte. When the keeper stays green, first check whether the mutation is equivalent: whether types, reachability, or how the value is consumed make the mutated code behave identically, and whether any input can tell the two apart. An equivalent mutation proves nothing either way; pick another. A mutation that times out or crashes the harness is inconclusive, not caught.

Done when every reported gap is restored or rejected with source evidence, and every restored contract has a caught mutation.

## 7. Product defects

A baseline failure that survives into a keeper is a bug report. Fix it at its owner as a separable change, its own commit when commits are authorized, and prove it through the real user flow, with a **control** run that reverts the fix and shows the old behavior. Record unrelated product discrepancies you find as follow-ups instead of fixing them in the campaign.

Done when each repaired defect has a failing control and a passing candidate on the same harness.

## 8. Reconcile and hand off

Campaigns outlive many main-branch commits. When integration is authorized, integrate main under the repository's policy; for a long, many-commit campaign, prefer merging main over rebasing unless that policy says otherwise. When main modified a file the campaign deleted, re-evaluate the deletion against the new change: when it still holds, port the new contract into the keeper and confirm every new regression main added still has a home. Rerun the whole subsystem suite and repeat live proof on the integrated head.

Review tooling may see a truncated file list on a diff this large; give reviewers the lane plans as a map. Record maintainer decisions about generic compatibility flags in the change evidence rather than editing gates.

Hand off with the [test audit](test-audit.md#handoff) report, plus:

- baseline and final test/support line counts, with production counted separately;
- lanes, retired layers, and keepers;
- preservation gaps found and their mutations;
- product defects with control and candidate proof.
