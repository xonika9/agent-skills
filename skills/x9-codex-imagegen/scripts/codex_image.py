#!/usr/bin/env python3
"""Generate one image with Codex's built-in image tool and verify the PNG.

Runs one `codex exec` turn that calls the image tool once and copies the result
to --out. Success is decided by the file, not by Codex's reply: the PNG
signature and IHDR dimensions are read from disk. When Codex generated an image
but did not copy it, the newest PNG from that thread's generated_images folder
is recovered instead of generating again.

Prints one JSON object. Exit code 0 only for status "ok".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
NETWORK_ERROR = re.compile(r"error sending request|network error|stream disconnected", re.I)
# A VPN that drops idle connections after ~30 s makes the image tool fail
# after several reconnects, which lands in this window of total run time.
IDLE_CUT_WINDOW = (150.0, 210.0)

TASK = """Call your built-in image generation tool exactly once with the prompt between the markers, verbatim.
Then copy the generated PNG to {out}. Do not edit any other file.
If the tool fails, reply FAILED=<exact error> and do nothing else; never draw the image another way.
<<<PROMPT
{prompt}
PROMPT>>>
"""


def png_info(path: Path) -> tuple[int, int, bool] | None:
    """Return (width, height, has_alpha_channel) from the PNG header."""
    try:
        with path.open("rb") as handle:
            head = handle.read(26)
    except OSError:
        return None
    if len(head) < 26 or head[:8] != PNG_SIGNATURE or head[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", head[16:24])
    return width, height, head[25] in (4, 6)


def parse_events(jsonl: str) -> tuple[str | None, list[str], list[str]]:
    thread_id, messages, errors = None, [], []
    for line in jsonl.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "thread.started":
            thread_id = event.get("thread_id")
        elif kind == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                messages.append(item["text"])
            elif item.get("type") == "error" and item.get("message"):
                errors.append(item["message"])
        elif kind in ("error", "turn.failed"):
            detail = event.get("message") or (event.get("error") or {}).get("message")
            errors.append(str(detail or event))
    return thread_id, messages, errors


def classify(text: str, elapsed: float) -> tuple[str, bool]:
    """Return (status, idle_cut_suspected) for a run that produced no image."""
    if NETWORK_ERROR.search(text):
        low, high = IDLE_CUT_WINDOW
        return "network_error", low <= elapsed <= high
    return "failed", False


def recover(codex_home: Path, thread_id: str | None, started: float, out: Path) -> Path | None:
    if not thread_id:
        return None
    folder = codex_home / "generated_images" / thread_id
    candidates = [p for p in folder.glob("*.png") if p.stat().st_mtime >= started - 1]
    if not candidates:
        return None
    source = max(candidates, key=lambda p: p.stat().st_mtime)
    shutil.copyfile(source, out)
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="destination .png path")
    parser.add_argument("--root", type=Path, help="Codex working root; must contain --out (default: its folder)")
    parser.add_argument("--image", action="append", default=[], type=Path, help="reference image (repeatable)")
    parser.add_argument("--effort", default="low", help="model_reasoning_effort for the Codex turn")
    parser.add_argument("--timeout", type=float, default=600.0, help="seconds before the run is stopped")
    parser.add_argument("--log-dir", type=Path, help="where run.jsonl and run.err go (default: new temp dir)")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing an existing --out file")
    parser.add_argument("--codex", default="codex", help="codex executable")
    args = parser.parse_args()

    out = args.out.expanduser().resolve()
    root = (args.root.expanduser().resolve() if args.root else out.parent)
    log_dir = args.log_dir.expanduser().resolve() if args.log_dir else Path(tempfile.mkdtemp(prefix="codex-image-"))
    result: dict[str, object] = {"out": str(out), "root": str(root), "log_dir": str(log_dir)}

    def finish(status: str, **extra: object) -> int:
        result.update(status=status, **extra)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if status == "ok" else 1

    if out.suffix.lower() != ".png":
        return finish("usage_error", error="--out must end with .png")
    if not out.is_relative_to(root):
        return finish("usage_error", error="--out must be inside --root, or workspace-write cannot copy it")
    if out.exists() and not args.overwrite:
        return finish("usage_error", error="--out already exists; pass --overwrite only if replacing it was requested")
    prompt = args.prompt_file.read_text(encoding="utf-8").strip()
    if not prompt or "PROMPT>>>" in prompt:
        return finish("usage_error", error="prompt is empty or contains the PROMPT>>> marker")
    for image in args.image:
        if not image.is_file():
            return finish("usage_error", error=f"reference image not found: {image}")

    out.parent.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    command = [args.codex, "exec", "--skip-git-repo-check", "-C", str(root), "-s", "workspace-write",
               "-c", f'model_reasoning_effort="{args.effort}"', "--ephemeral", "--json"]
    for image in args.image:
        command += ["-i", str(image.expanduser().resolve())]
    command.append("-")

    started = time.time()
    timed_out = False
    with (log_dir / "run.jsonl").open("w") as stdout, (log_dir / "run.err").open("w") as stderr:
        try:
            proc = subprocess.run(command, input=TASK.format(out=out, prompt=prompt), text=True,
                                  stdout=stdout, stderr=stderr, timeout=args.timeout)
            exit_code: int | None = proc.returncode
        except FileNotFoundError:
            return finish("failed", error=f"codex executable not found: {args.codex}")
        except subprocess.TimeoutExpired:
            exit_code, timed_out = None, True
    elapsed = round(time.time() - started, 1)

    thread_id, messages, errors = parse_events((log_dir / "run.jsonl").read_text(errors="replace"))
    result.update(elapsed_seconds=elapsed, thread_id=thread_id, codex_exit=exit_code,
                  last_message=messages[-1] if messages else None)

    def fresh_png() -> tuple[int, int, bool] | None:
        info = png_info(out)
        return info if info and out.stat().st_mtime >= started - 1 else None

    source = "codex-copy"
    if fresh_png() is None:
        if out.exists() and out.stat().st_mtime >= started - 1:
            return finish("failed", error="Codex wrote a file at --out that is not a PNG")
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        recovered = recover(codex_home, thread_id, started, out)
        source = f"recovered:{recovered}" if recovered else ""
    info = fresh_png()
    if info:
        return finish("ok", source=source, width=info[0], height=info[1], has_alpha=info[2])

    failure_text = "\n".join(errors + messages)
    if timed_out:
        return finish("failed", error=f"timed out after {args.timeout:g}s")
    stderr_text = (log_dir / "run.err").read_text(errors="replace")
    status, idle_cut = classify(failure_text or stderr_text, elapsed)
    return finish(status, idle_cut_suspected=idle_cut,
                  error=failure_text.strip() or f"no image produced; see {log_dir / 'run.err'}")


if __name__ == "__main__":
    sys.exit(main())
