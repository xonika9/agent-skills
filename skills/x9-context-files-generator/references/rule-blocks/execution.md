<!-- x9-context-files-generator:execution:start -->
## Execution discipline

Shared defaults from the `x9-context-files-generator` template. Repository-specific instructions outside this block take precedence. Local contains optional pointers to existing project resources.

- Use the project's existing verification tools. Do not build a separate acceptance framework merely to verify a routine change.
- After a check fails, run the failing check and checks affected by its fix. Repeat a previously passing check when the change could invalidate its result or the project requires a fresh run.
- Keep code comments focused on non-obvious reasons, invariants, and workarounds. Preserve license notices and useful API documentation; avoid narrating the code.

### Local

- <existing verification entry point, only when an explicit pointer is useful>
<!-- x9-context-files-generator:execution:end -->
