---
name: x9-codex-imagegen
description: Use when a raster image should be generated or edited from a reference with Codex's built-in image tool, including from Claude Code or OpenCode through `codex exec` — «сгенерируй картинку через Codex», «нарисуй иллюстрацию», "generate an image with Codex". Do not use for editable diagrams, local edits of existing images, or delegating non-image work to Codex.
---

# Generate images through Codex

Codex can generate images with its built-in tool under the user's ChatGPT login; no `OPENAI_API_KEY` is needed. One image is one `codex exec` turn, and success is a verified PNG on disk, never Codex's reply.

The [onboarding declaration](references/onboarding.json) is the machine-readable onboarding contract.

This lets an agent on any model use a Codex subscription for images: in Claude Code, OpenCode, or another runtime with a shell, run `scripts/codex_image.py`. Inside a Codex session, Codex's own `imagegen` skill owns the workflow; the network gate and failure handling below still apply there, and success is still the PNG on disk.

## Network gate

The image tool waits 1–3 minutes for a result while no data flows. Some VPN clients drop such silent connections after about 30 seconds; then complex images never arrive and retries cannot help. Before the first generation in a session, run:

```bash
python3 <skill-directory>/scripts/check_idle_connection.py
```

It takes about 90 seconds and prints one JSON object:

- `OK` — generate.
- `CUT` — do not generate. Tell the user that the current VPN or proxy drops idle connections after `after_seconds` and that they need a route that keeps them open (another VPN client or mode, or no VPN), then rerun the check.
- `ERROR` — the probe host is unreachable, so the gate is not proven. Retry with `--host` set to another SMTP submission server; if none is reachable, generate, treating a later suspected idle cut as `CUT`.

## Generate

Write the prompt to a file following [references/prompting.md](references/prompting.md), then run:

```bash
python3 <skill-directory>/scripts/codex_image.py --prompt-file <prompt.txt> --out <absolute/path.png> [--image <reference.png>] [--root <dir>]
```

- The tool has no size parameter: the prompt states the aspect ratio; compare the reported `width` and `height` with the requested proportions and crop or scale a copy when they differ.
- `--out` must lie inside `--root`, which defaults to the destination folder; Codex can write only inside that root.
- The script refuses to replace an existing file. Pass `--overwrite` only when the user asked to replace it.
- Up to 3 runs may proceed in parallel, each with its own `--out`. After network failures in more than one parallel run, continue sequentially.

Each run spends the user's Codex usage, so generate only the images and variants that were requested. Never substitute an image drawn another way (SVG, code, a local library) for a failed generation.

## Handle the result

The script prints JSON with `status`, `elapsed_seconds`, `thread_id`, `log_dir`, and `error`.

- `ok` — the PNG signature, dimensions, and `has_alpha` were read from disk; a requested transparent background needs `has_alpha: true`. `source` is `codex-copy`, or `recovered:<path>` when Codex generated the image but did not copy it.
- `network_error` with `idle_cut_suspected: true` — the failure landed 2.5–3.5 minutes in, the signature of a VPN idle cut. Do not retry; run the network gate.
- `network_error` otherwise — a transient fault. Retry up to 4 attempts in total, waiting 60, 120, then 240 seconds. Before each retry, check that the server answers:

  ```bash
  curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://chatgpt.com/backend-api/codex/responses
  ```

  `405` means reachable; `000` or a timeout means the network is down, so keep waiting. A `405` does not prove that silent connections survive; only the network gate does.
- `failed` — read `error`. A content-policy refusal is not retried with the same prompt: rewrite it while keeping the user's intent, say what changed, and stop when the intent itself is refused. Report any other error exactly, together with `log_dir`.
- `usage_error` — fix the arguments; nothing was generated.

Stop and report when the same cause repeats or the retry budget is spent.

## Done

- Each requested image exists at its destination with status `ok`, and its dimensions match the requested proportions or the adjustment is reported.
- Every image that was not produced is reported with its status, exact error, and `log_dir`.
