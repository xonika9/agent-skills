#!/usr/bin/env python3
"""Generate one image with Codex's built-in image tool and verify the PNG.

Runs one `codex exec` turn. By default Codex receives a brief and shapes the
prompt with its own imagegen skill; with --verbatim it passes the given prompt
to the image tool unchanged. Success is decided by the file, not by Codex's
reply: the PNG signature and IHDR header are read from disk. When Codex
generated an image but did not save it, the newest PNG from that thread's
generated_images folder is recovered instead of generating again.

Prints one JSON object. Exit code 0 only for status "ok".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
NETWORK_ERROR = re.compile(r"error sending request|network error|stream disconnected", re.I)
FINAL_PROMPT = re.compile(r"FINAL_PROMPT:\s*(.+)", re.S)
# A network that drops connections silent for ~30 s makes the image tool fail
# only after several reconnects; transient faults usually fail within seconds.
IDLE_CUT_AFTER = 150.0
# Only the image tool's own failures count from stderr: other Codex connections
# (MCP servers, analytics) log "error sending request" during the same outages.
IMAGE_TOOL_ERROR = re.compile(r"image generation failed:[^\n]*")
# The image tool cannot use a SOCKS proxy, so only an HTTP proxy is accepted.
PROXY_ENV = "X9_CODEX_IMAGE_PROXY"

BRIEF_TASK = """Use your imagegen skill with the built-in image generation tool to create the image described in the brief between the markers.
Save the final image as a PNG at {out}. {replace}Do not edit any other file.
Do not use the CLI or API fallback and never draw the image another way. If the built-in tool fails, reply FAILED=<exact error>.
End your reply with a line FINAL_PROMPT: followed by the prompt of the saved image.
<<<BRIEF
{text}
BRIEF>>>
"""

VERBATIM_TASK = """Call your built-in image generation tool exactly once with the prompt between the markers, verbatim.
Save the final image as a PNG at {out}. {replace}Do not edit any other file.
If the tool fails, reply FAILED=<exact error> and do nothing else; never draw the image another way.
<<<PROMPT
{text}
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


def classify(text: str) -> str:
    """Return the status for a run that produced no image."""
    return "network_error" if NETWORK_ERROR.search(text) else "failed"


def proxy_problem(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.scheme != "http" or not parts.hostname or not parts.port:
        return "expected http://host:port"
    try:
        socket.create_connection((parts.hostname, parts.port), timeout=5).close()
    except OSError as error:
        return f"not reachable ({error})"
    return None


def stop_group(proc: subprocess.Popen) -> None:
    """Stop Codex with everything it started; the npm `codex` wrapper cannot forward SIGKILL."""
    if not hasattr(os, "killpg"):
        proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=10)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # whatever ignored SIGTERM or outlived the leader
        except ProcessLookupError:
            pass
    proc.wait()


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
    parser.add_argument("--brief-file", required=True, type=Path,
                        help="what to create; Codex shapes the prompt unless --verbatim")
    parser.add_argument("--verbatim", action="store_true", help="pass the file to the image tool unchanged")
    parser.add_argument("--out", required=True, type=Path, help="destination .png path")
    parser.add_argument("--root", type=Path, help="Codex working root; must contain --out (default: its folder)")
    parser.add_argument("--image", action="append", default=[], type=Path, help="reference image (repeatable)")
    parser.add_argument("--effort", default="medium", help="model_reasoning_effort for the Codex turn")
    parser.add_argument("--timeout", type=float, default=900.0, help="seconds before the run is stopped")
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
    text = args.brief_file.read_text(encoding="utf-8").strip()
    marker = "PROMPT>>>" if args.verbatim else "BRIEF>>>"
    if not text or marker in text:
        return finish("usage_error", error=f"brief is empty or contains the {marker} marker")
    for image in args.image:
        if not image.is_file():
            return finish("usage_error", error=f"reference image not found: {image}")

    env = None
    proxy = os.environ.get(PROXY_ENV, "").strip()
    if proxy:
        problem = proxy_problem(proxy)
        if problem:
            return finish("proxy_unreachable", error=f"{PROXY_ENV}={proxy}: {problem}")
        env = dict(os.environ, HTTPS_PROXY=proxy, HTTP_PROXY=proxy)
        result["proxy"] = proxy

    out.parent.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    command = [args.codex, "exec", "--skip-git-repo-check", "-C", str(root), "-s", "workspace-write",
               "-c", f'model_reasoning_effort="{args.effort}"', "--ephemeral", "--json"]
    for image in args.image:
        command += ["-i", str(image.expanduser().resolve())]
    command.append("-")

    replace = "Replacing the existing file there is explicitly requested. " if out.exists() else ""
    task = (VERBATIM_TASK if args.verbatim else BRIEF_TASK).format(out=out, replace=replace, text=text)
    started = time.time()
    timed_out = False
    with (log_dir / "run.jsonl").open("w") as stdout, (log_dir / "run.err").open("w") as stderr:
        try:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True,
                                    env=env, start_new_session=hasattr(os, "killpg"))
        except FileNotFoundError:
            return finish("failed", error=f"codex executable not found: {args.codex}")
        try:
            proc.communicate(task, timeout=args.timeout)
            exit_code: int | None = proc.returncode
        except subprocess.TimeoutExpired:
            stop_group(proc)
            exit_code, timed_out = None, True
    elapsed = round(time.time() - started, 1)

    thread_id, messages, errors = parse_events((log_dir / "run.jsonl").read_text(errors="replace"))
    last = messages[-1] if messages else None
    final_prompt = FINAL_PROMPT.search(last or "")
    result.update(elapsed_seconds=elapsed, thread_id=thread_id, codex_exit=exit_code, last_message=last,
                  final_prompt=final_prompt.group(1).strip() if final_prompt else None)

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

    if timed_out:
        return finish("failed", error=f"timed out after {args.timeout:g}s")
    tool_errors = list(dict.fromkeys(IMAGE_TOOL_ERROR.findall((log_dir / "run.err").read_text(errors="replace"))))
    failure_text = "\n".join(errors + messages + tool_errors).strip()
    status = classify(failure_text)
    if status == "network_error":
        result["idle_cut_suspected"] = elapsed >= IDLE_CUT_AFTER
    return finish(status, error=failure_text or f"no image produced; see {log_dir / 'run.err'}")


if __name__ == "__main__":
    sys.exit(main())
