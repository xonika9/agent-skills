# Feasibility Admission For Unproven Platform Paths

Use this admission before broad delivery when an outcome depends on a new
external platform, custom protocol client, new launch or isolation context, or
target-only behavior that local substitutes cannot prove. The architecture gate
separately decides whether the platform commitment is acceptable.

## Evidence Applicability

Evidence admits broad delivery only when it exercises the same product-path
artifact that will perform the behavior through the same load-bearing protocol
and target boundary. Match the relevant version, identity, launch, isolation,
security, and source fingerprints.

A CLI, mock, local substitute, different client, or standalone library demo
does not prove the product path merely because it reaches the same platform. If
the product path adds a helper process, IPC contract, packaging change,
privilege transition, cancellation path, or restart semantics, those boundaries
also need evidence.

Record one of:

- `NOT_APPLICABLE — <current matching product artifact and boundary evidence>`;
- `EXPERIMENT_ONLY — <primary falsifiable assumption and authority boundary>`;
- `IMPLEMENTATION_READY — <matching product-path evidence reference>`.

Missing, stale, or mismatched evidence is never `NOT_APPLICABLE`.

## Reuse Challenge

Before owning a commodity protocol, platform client, parser, SDK surface,
runtime helper, or infrastructure control plane, compare maintained candidates
with the custom path. Record the result as `reuse_decision`: the product
capability needed, viable candidates,
their integration and operating boundaries, the cheapest local falsifier, and
the evidence for the chosen path. An untested promising candidate remains
`NOT_PROVEN` rather than selected.

This is a proportionate decision input, not a separate task lifecycle.

## Admission Behavior

When matching evidence is absent, admit only the named bounded experiment inside
the established authority. Its first live request should be the smallest
path-killing use of the actual product artifact, with exact readback and cleanup.
Do not require a full qualification harness before resolving the primary
assumption, and do not treat preparation evidence as target proof.

Documentation, compilation, dependency inspection, deterministic fakes, and a
disposable local target may eliminate candidates before an expensive or
externally mutating attempt. They do not replace product-path evidence or grant
new authority.
