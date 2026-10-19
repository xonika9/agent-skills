<!-- x9-context-files-generator:execution:start -->
## Execution discipline

Shared rules from the `x9-context-files-generator` template. Edit only Local, which takes precedence; the rest is replaced when the template changes.

- After a task merges into the main branch, the integrating agent removes the task's worktree once no active work uses it. Preserve required evidence and unique local data first. Never force removal; if cleanup is unsafe, keep the worktree and report why.
- Before building or substantially expanding verification tooling, creating a dedicated verification environment, repeatedly repairing that environment, or scheduling an expensive full acceptance rerun, stop the dependent work and ask the owner whether this verification is needed, even when an accepted plan requires the check. This applies to every agent, including delegated ones, before implementation, delegation, or execution. Present the user-visible property it checks, the existing evidence, the simplest alternative, the expected effort, and the consequence of simplifying or removing it, with a recommendation. Approval of a product outcome or a plan does not authorize extra verification infrastructure or budget.
- Routine focused checks with existing tooling, and verification within an explicitly approved scope and budget, continue without asking. Ask again when the scope or budget materially expands; a newly discovered technical prerequisite does not itself authorize further work. Leave an unproven condition unproven until the owner changes the requirement or approves the proposed verification.
- Do not add code comments by default. Keep a needed comment minimal and limited to a non-obvious reason, invariant, or workaround; do not narrate code or test steps or restate plans and acceptance criteria. Preserve license notices and public API documentation.
- A mandatory input is any file, directory, bundle, or document that the plan or the repository canon tells the executor to read or use. When one is missing, stop the unit that needs it and report the missing input; do not substitute an earlier note, a reconstruction, or an assumption.
- An acceptance check stays valid on every later tree that keeps the accepted behavior, so it can be rerun after merges and follow-up commits. Do not compare a diff or a changed-file list against a fixed base commit, and do not fail on changes outside the work's own files; scope belongs to code review.
- After a long multi-step acceptance fails, run the failing check and the checks its fix affects before repeating earlier passing checks. Reuse a passing result only with its recorded command, source revision, and evidence that it still applies after the change; rerun the check when that cannot be established. If an accepted plan requires every check afresh, amend that plan before using earlier results in its final acceptance.
- Keep long-running checks observable across session loss: record the current step and the final exit status, inspect them until the process finishes, and report a failure when it occurs. A detached process or a quiet log does not establish success.

### Local

- <the single pre-merge or acceptance command, and when an earlier result for the same tree may be reused>
- <where machine-local files such as `.env` live when worktrees are used, and that a worktree reads them there instead of copying>
- <another repository fact these rules depend on>
<!-- x9-context-files-generator:execution:end -->
