---
name: x9-codex-imagegen
description: Use when an agent outside Codex, such as Claude Code or OpenCode on any model, should generate or edit a raster image through the user's Codex subscription — «сгенерируй картинку через Codex», «нарисуй иллюстрацию», "generate an image with Codex". Do not use inside a Codex session, where Codex's own imagegen skill applies, or for editable diagrams, crops, resizes, or other edits made locally without generation, or delegating non-image work to Codex.
---

# Generate images through Codex

Codex generates images with its built-in tool under the user's ChatGPT login; no `OPENAI_API_KEY` is needed. This skill lets an agent on any model use that route: it hands Codex a brief, Codex shapes the prompt with its own `imagegen` skill, and success is a verified PNG on disk, never Codex's reply.

The [onboarding declaration](references/onboarding.json) is the machine-readable onboarding contract.

## Brief

Codex sees nothing of the conversation, so the brief carries everything the image depends on: what to depict and what it is for, exact text to render (quoted), aspect ratio, the role of each attached image by its order (`Image 1: edit target`, `Image 2: style reference`), what must stay unchanged in an edit, a transparent background when needed, and any style or constraints the user set. Leave prompt wording to Codex.

When the user supplies a finished prompt, pass it with `--verbatim` so Codex sends it to the image tool unchanged.

## Generate

```bash
python3 <skill-directory>/scripts/codex_image.py --brief-file <brief.txt> --out <absolute/path.png> [--image <reference.png>] [--root <dir>] [--verbatim]
```

- A run takes from under a minute to several minutes, and Codex may refine the image over more than one generation. Give the command a timeout of at least 15 minutes or run it in the background and wait for it; a run stopped early looks like a failure and invites a second, duplicate generation.
- `--out` must lie inside `--root`, which defaults to the destination folder; Codex can write only inside that root.
- The script refuses to replace an existing file. Pass `--overwrite` only when the user asked to replace it.
- Up to 3 runs may proceed in parallel, each with its own `--out`.
- When `X9_CODEX_IMAGE_PROXY` is set, the script sends the Codex run through that HTTP proxy. The user sets it on a machine whose network drops connections that stay silent while an image renders; do not set or change it yourself.

Generate only the images the user asked for. Never substitute an image drawn another way (SVG, code, a local library) for a failed generation.

## Handle the result

The script prints JSON with `status`, `elapsed_seconds`, `final_prompt`, `thread_id`, `log_dir`, and `error`.

- `ok` — the PNG signature, dimensions, and `has_alpha` were read from disk; a requested transparent background needs `has_alpha: true`. `source` is `codex-copy`, or `recovered:<path>` when Codex generated the image but did not save it. Compare `width` and `height` with the requested proportions and crop or scale a copy when they differ.
- `network_error` with `idle_cut_suspected: true` — the run failed only after minutes, which a network that drops silent connections causes but a late transient fault can too. Retry once after 60 seconds; if that run is suspected again, stop and report that the image needs a route that keeps silent connections open, such as `X9_CODEX_IMAGE_PROXY`.
- `network_error` otherwise — retry at most twice, after 60 and then 120 seconds.
- `proxy_unreachable` — `X9_CODEX_IMAGE_PROXY` is set but does not answer, so nothing was started. Report `error` so the user can restore the proxy.
- `failed` — read `error`. For a content refusal, revise the brief while keeping the user's intent and say what changed; stop when the intent itself is refused. Report any other error exactly, together with `log_dir`.
- `interrupted` — the script was stopped from outside and terminated the whole Codex run, so nothing keeps generating in the background; a repeat cannot produce a duplicate.
- `usage_error` — fix the arguments; nothing was generated.

## Done

- Each requested image exists at its destination with status `ok`, its dimensions match the requested proportions or the adjustment is reported, and its `final_prompt` is available to the user.
- Every image that was not produced is reported with its status, exact error, and `log_dir`.
