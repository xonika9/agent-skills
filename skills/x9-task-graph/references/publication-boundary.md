# Publication boundary

Load this reference only after the user asks to save the task-graph draft locally or publish it to an external tracker. Chat delivery is the default and changes nothing.

## Local save

Save locally only on an explicit request that names the destination path. Re-read an existing target immediately before changing it, preserve user-owned content, and report the written path. A request to "break down the plan" or "make a graph" is not permission to create a file.

## External publication gate

Publish only when the user explicitly requests publication and names the target tracker, project, list, or equivalent destination. Before any tracker request, generate one opaque correlation ID for this publication attempt and keep it in the draft and preview.

Freshly read the named target through a reachable connector, MCP tool, API, or documented CLI. Do not bundle, assume, or fabricate a client for any tracker. If no reachable interface can read the target, produce `DEGRADED` with the missing interface and do not mutate the tracker.

After the fresh read, show a preview of the exact creates and updates: destination,
correlation ID, proposed tracker fields, source work-item IDs, selected recovery route,
and every intended mutation. Do not write until the user has explicitly authorized that
preview's mutations.

## Idempotency and reconciliation

Before a write, establish one safe recovery route:

- use the correlation ID as the tracker interface's native idempotency key, after
  confirming that its documented contract permits the exact request to be repeated with
  that key and that the target can be read afterward for reconciliation; or
- embed a searchable correlation marker in each created or updated object and confirm that the interface can search the target for that marker.

An interface that cannot satisfy every condition of its selected route is `BLOCKED` after preview. Do not attempt the write or guess whether it succeeded.

When a write's outcome is uncertain, use only the recovery route included in the
authorized preview:

- For native idempotency, repeat the exact request through the documented retry contract
  with the same correlation ID as its idempotency key. Then freshly read the target and
  reconcile the observed objects against the preview.
- For an embedded marker, do not repeat the write. Search the freshly scoped target by
  that marker and reconcile the found objects against the preview.

Report the result as reconciled, still uncertain, or conflicting. An unavailable
reconciliation read, a conflict, or a result that remains uncertain is `BLOCKED` until
the user directs the next safe action. Any changed mutation requires a new preview and
explicit authorization.

Treat live publication and live reconciliation as `NOT_PROVEN` unless a separately authorized integration run produced their evidence. Never expose credentials, alter unrelated tracker state, or publish to an unnamed destination.
