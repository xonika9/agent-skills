# Behavioral evaluation

Structural lint cannot prove that a skill triggers correctly or produces the promised result. Evaluate behavior in a clean context against explicit assertions.

Use this reference when behavioral evidence is explicitly selected or when a stable/shared/high-risk claim needs runtime proof. Static evidence may defer these runs and report that boundary without treating it as a defect.

## Minimal matrix

1. **Positive trigger:** a realistic request that should load the skill.
2. **Near-miss:** an adjacent request that another skill or ordinary reasoning should own.
3. **Ambiguity/authority:** a case where the skill must ask, preserve state, or refuse to expand scope.
4. **Tool failure:** when tools are part of the contract, simulate an unavailable or cancelled call and assert an honest degraded result.
5. **Completion:** inspect the real artifact, diff, source trace, or command output promised by Done.

## Comparative evaluation

For a new or materially changed skill, run the same prompts:

- with the candidate skill and without it, or
- against the old and new versions in separate clean contexts.

Keep model/runtime/settings constant. Change one instruction class at a time when diagnosing why behavior changed.

## Assertions

Write assertions before judging, for example:

- skill loaded / did not load;
- no file changed before authority;
- exact required fields exist;
- failed retrieval is reported;
- test command exits 0;
- body hash is unchanged;
- status is `DEGRADED` rather than `COMPLETE` when a route is missing.

Capture evidence paths or output excerpts. A judge's general preference is not a behavioral result.

## Scale

- Small wording change: trigger + near-miss + focused completion assertion.
- Tool or authority change: full minimal matrix.
- Fragile, shared, or high-stakes skill: comparative runs plus an independent fresh-context reviewer.

If a runtime cannot execute the scenario, record the missing capability and mark the evaluation `DEGRADED`.
