# Claude CLI Opus route

Use this route only after live `claude --help` confirms equivalents for explicit Opus-family selection, `high` effort, non-persistent print execution, text input on stdin, safe mode, disabled tools, and structured JSON output. Run with those controls explicitly; inherited model, effort, customizations, or a request for `high` inside the brief do not satisfy the contract.

Materialize only the sealed packet in an OS temporary directory created with `mktemp`, set the directory to `700` and the file to `600`, and install cleanup for exit and catchable interruption before writing it. Pass the file through stdin rather than argv, never place it in the repository or logs, and verify its deletion after the command returns.

Require a successful structured result whose `modelUsage` identifies an Opus-family canonical model. Treat rejection of any required control or absence of Opus-family usage as route failure. Record accepted model and effort selectors as control evidence; if the result does not expose effective effort separately, mark that post-run property `NOT_PROVEN` without failing the route.
