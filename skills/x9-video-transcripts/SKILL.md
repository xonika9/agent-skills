---
name: x9-video-transcripts
description: Use when the user wants offline, timestamped transcripts of their own local video or audio files, from one file to a whole folder, or wants to find where something was said in recordings already transcribed this way — «расшифруй ролики», «сделай субтитры к видео», «где в роликах я говорил про…», "transcribe these videos with timestamps". Do not use for online video links, a quick summary of what a video is about, live dictation, or translation.
---

# Video transcripts

Turn local recordings into timestamped transcripts with whisper.cpp on the user's machine, and find moments in them later. A script does the recognition, so a batch costs the agent progress lines and a JSON summary, never the transcript text.

The [onboarding declaration](references/onboarding.json) is the machine-readable onboarding contract.

## Storage

Each source `<name>.<ext>` gets two files beside it:

- `<name>.transcript.srt` — standard subtitles for players and video editors;
- `<name>.transcript.txt` — `# source:` and `# language:` headers, then one `[hh:mm:ss] text` line per segment; search reads this file.

The `.transcript` suffix leaves the user's own `<name>.srt` untouched. Nothing central is created: a folder of 50 videos gains 100 small files next to them, and a source counts as current while both of its outputs are newer than it. `--out DIR` mirrors the same names under `DIR`, relative to the widest folder argument that contains each source; use it when the source location is read-only, short on synced space, or the user wants a separate library.

Sources whose outputs would share a name, such as `clip.mp4` and `Clip.MOV`, are listed under `collisions` instead of overwriting each other; only renaming one of them or giving them separate `--out` runs resolves that, not a rerun.

## Transcribe

```bash
python3 <skill-directory>/scripts/transcripts.py run <file-or-folder>... [--lang ru] [--out DIR] [--force] [--model FILE]
```

- Pass `--lang` whenever the spoken language is known; auto-detection misfires on short or music-heavy recordings.
- Folders are scanned recursively for common audio and video extensions, skipping hidden entries and without following folder symlinks; a file named explicitly is passed to ffmpeg whatever its extension.
- Runtime grows with audio length. For long recordings or more than a few files, run the command in the background and wait for it to exit instead of polling; progress goes to stderr, the summary to stdout. If the runtime stops the command before it exits, run the same command again: current files are skipped.
- Use `--force` only when the user asks to redo existing transcripts, for example with another model or language.

Read the summary's `status`:

- `ok` (exit 0) — nothing failed. Files in `no_speech` were transcribed but contain no recognized speech; tell the user which ones.
- `partial` (exit 1) — report each `failed` and `collisions` entry with its reason. Rerunning retries the failed files once their cause is fixed.
- `aborted` (exit 1) — the same `whisper-cli` error hit consecutive files, so `not_attempted` were left for later. Report the error; it usually means a broken model file or a `whisper-cli` build without `--vad`.
- `setup_required`, `no_media`, or a missing path (exit 2) — nothing was transcribed. See [Setup](#setup) or correct the paths.

Never delete, move, or re-encode source media.

## Setup

`transcripts.py check` reports `ffmpeg`, `whisper-cli`, and the two model files; `check --download` fetches missing default models, about 875 MB, into `$X9_TRANSCRIPTS_MODELS` or `~/.cache/x9-video-transcripts/models`. A transcription request authorizes that download; state its size when starting it. Installing `ffmpeg` or whisper.cpp changes the system, so give the install command (with Homebrew: `brew install ffmpeg whisper-cpp`) and wait for the user's go-ahead. Set `X9_WHISPER_CLI` when `whisper-cli` is not on `PATH`.

## Find a moment

```bash
python3 <skill-directory>/scripts/transcripts.py search "<words>" <folder-or-transcript>... [--max 50]
```

Matching ignores case, treats ё as е, and drops the last letters of longer words so inflected forms match; every word must occur in one segment or across two adjacent ones. Each hit prints the source path and timestamp. Exit 2 means no transcripts exist under the given paths, which is not evidence that the words were never said. Answer from the hits, and read transcript lines into context only to quote, summarize, or check a hit's surroundings.

Recognition misspells rare names and terms, so when a name finds nothing, search for a distinctive ordinary word from the same passage or a likely alternative spelling.

## Quality limits

- Proper names, brand and game terms, and anglicisms carry most errors.
- Speech over loud music can be dropped, and the surrounding segment stretched, so timestamps near such passages may be off by many seconds.
- For a different accuracy or speed trade-off, read [references/models.md](references/models.md).

## Done

The last `run` summary has `status: ok`, or every entry in its `failed`, `collisions`, `no_speech`, and `not_attempted` lists has been reported to the user with its reason.
