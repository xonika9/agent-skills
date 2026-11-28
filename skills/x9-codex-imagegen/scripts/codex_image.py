#!/usr/bin/env python3
"""Generate one or more images with Codex's built-in image tool and verify each PNG.

Runs `codex exec` turns (one image per call, or a parallel batch via --batch).
By default Codex receives a brief and shapes the prompt with its own imagegen
skill; with --verbatim it passes the given prompt to the image tool unchanged.
Image validity is decided by the file, not by Codex's reply: the PNG signature,
chunk checksums, and raster layout are verified on disk. When Codex generated an
image but did not save it, the newest PNG from that thread's generated_images
folder is recovered instead of generating again.

Prints one JSON object. Exit code 0 only when status is "ok"; a verified PNG
without its final prompt is "incomplete" and remains available at --out.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
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
import threading
import time
import zlib
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
DEFAULT_PARALLEL = 3
JOB_KEYS = frozenset({
    "out",
    "brief",
    "brief_file",
    "images",
    "root",
    "verbatim",
    "overwrite",
    "effort",
    "timeout",
    "log_dir",
})

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


@dataclass(frozen=True)
class JobSpec:
    out: Path
    root: Path
    log_dir: Path
    text: str
    images: tuple[Path, ...]
    verbatim: bool
    overwrite: bool
    effort: str
    timeout: float


class BatchCoordinator:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.stop_signal: str | None = None
        self.active: set[subprocess.Popen] = set()


def png_info(path: Path) -> tuple[int, int, bool] | None:
    """Validate PNG chunks, checksums and raster layout without another dependency."""
    try:
        data = path.read_bytes()
        if data[:8] != PNG_SIGNATURE:
            return None
        offset, header, compressed, palette, ended = 8, None, bytearray(), False, False
        while offset < len(data):
            if offset + 12 > len(data):
                return None
            size = struct.unpack(">I", data[offset:offset + 4])[0]
            kind = data[offset + 4:offset + 8]
            end = offset + 12 + size
            if end > len(data):
                return None
            content = data[offset + 8:end - 4]
            if zlib.crc32(kind + content) != struct.unpack(">I", data[end - 4:end])[0]:
                return None
            if header is None and kind != b"IHDR":
                return None
            if kind == b"IHDR":
                if header is not None or size != 13:
                    return None
                header = struct.unpack(">IIBBBBB", content)
            elif kind == b"PLTE":
                if not size or size % 3 or size > 768:
                    return None
                palette = True
            elif kind == b"IDAT":
                compressed.extend(content)
            elif kind == b"IEND":
                if size or end != len(data):
                    return None
                ended = True
                break
            offset = end
        if not header or not compressed or not ended:
            return None
        width, height, depth, color, compression, filtering, interlace = header
        depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8),
                  4: (8, 16), 6: (8, 16)}
        if (not width or not height or depth not in depths.get(color, ()) or compression
                or filtering or interlace not in (0, 1) or (color == 3 and not palette)):
            return None
        decoder = zlib.decompressobj()
        raw = decoder.decompress(bytes(compressed)) + decoder.flush()
        if not decoder.eof or decoder.unused_data:
            return None
        channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
        passes = ((0, 0, 1, 1),) if interlace == 0 else (
            (0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
            (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))
        position = 0
        for x, y, dx, dy in passes:
            columns = max(0, (width - x + dx - 1) // dx)
            rows = max(0, (height - y + dy - 1) // dy)
            if not columns or not rows:
                continue
            row_size = (columns * channels * depth + 7) // 8 + 1
            for _ in range(rows):
                if position + row_size > len(raw) or raw[position] > 4:
                    return None
                position += row_size
        return (width, height, color in (4, 6)) if position == len(raw) else None
    except (OSError, struct.error, zlib.error):
        return None


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


def displayed_proxy(url: str) -> str:
    """Keep proxy credentials in the child environment, outside JSON and logs."""
    return re.sub(r"(://)[^/]*@", r"\1", url, count=1)


def proxy_problem(url: str) -> str | None:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as error:
        return f"invalid proxy URL: {error}"
    if parts.scheme != "http" or not parts.hostname or not port:
        return "expected http://host:port"
    try:
        socket.create_connection((parts.hostname, port), timeout=5).close()
    except OSError as error:
        return f"not reachable ({error})"
    return None


STOP_SIGNALS = [getattr(signal, name) for name in ("SIGTERM", "SIGINT", "SIGHUP") if hasattr(signal, name)]


class Interrupted(Exception):
    pass


def raise_interrupted(signum: int, _frame: object) -> None:
    raise Interrupted(signal.Signals(signum).name)


def ignore_stop_signals() -> None:
    for sig in STOP_SIGNALS:
        signal.signal(sig, signal.SIG_IGN)


def stop_group(proc: subprocess.Popen) -> None:
    """Stop Codex with everything it started; the npm `codex` wrapper cannot forward SIGKILL."""
    if not hasattr(os, "killpg"):
        proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=10)
        except (ProcessLookupError, PermissionError, subprocess.TimeoutExpired):
            pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # whatever ignored SIGTERM or outlived the leader
        except (ProcessLookupError, PermissionError):
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


def resolve_proxy() -> tuple[dict[str, str] | None, str | None, str | None]:
    proxy = os.environ.get(PROXY_ENV, "").strip()
    if not proxy:
        return None, None, None
    problem = proxy_problem(proxy)
    shown = displayed_proxy(proxy)
    if problem:
        return None, shown, f"{PROXY_ENV}={shown}: {problem}"
    return dict(os.environ, HTTPS_PROXY=proxy, HTTP_PROXY=proxy), shown, None


def validate_job(
    *,
    out_raw: Path,
    root_raw: Path | None,
    log_dir: Path,
    brief_file: Path | None,
    brief_inline: str | None,
    images_raw: list[Path],
    verbatim: bool,
    overwrite: bool,
    effort: str,
    timeout: float,
    label: str = "",
) -> tuple[JobSpec | None, str | None]:
    prefix = f"{label}: " if label else ""
    out = out_raw.expanduser().resolve()
    root = root_raw.expanduser().resolve() if root_raw else out.parent
    if out.suffix.lower() != ".png":
        return None, f"{prefix}--out must end with .png"
    if not out.is_relative_to(root):
        return None, f"{prefix}--out must be inside --root, or workspace-write cannot copy it"
    if out.exists() and not overwrite:
        return None, f"{prefix}--out already exists; pass --overwrite only if replacing it was requested"
    if not isinstance(effort, str) or not effort.strip():
        return None, f"{prefix}effort must be a non-empty string"
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        return None, f"{prefix}timeout must be a positive number"

    if (brief_file is None) == (brief_inline is None):
        return None, f"{prefix}provide exactly one of brief or brief_file"
    if brief_file is not None:
        try:
            text = brief_file.expanduser().read_bytes().decode("utf-8")
        except (OSError, UnicodeError) as error:
            return None, f"{prefix}cannot read brief: {error}"
    else:
        if not isinstance(brief_inline, str):
            return None, f"{prefix}brief must be a string"
        text = brief_inline
    if not verbatim:
        text = text.strip()

    marker = "PROMPT>>>" if verbatim else "BRIEF>>>"
    if not text.strip() or marker in text:
        return None, f"{prefix}brief is empty or contains the {marker} marker"

    images: list[Path] = []
    for image in images_raw:
        resolved = image.expanduser().resolve()
        if not resolved.is_file():
            return None, f"{prefix}reference image not found: {image}"
        images.append(resolved)

    return JobSpec(
        out=out,
        root=root,
        log_dir=log_dir.expanduser().resolve(),
        text=text,
        images=tuple(images),
        verbatim=verbatim,
        overwrite=overwrite,
        effort=effort.strip(),
        timeout=float(timeout),
    ), None


def run_job(
    job: JobSpec,
    *,
    codex_bin: str,
    env: dict[str, str] | None,
    proxy_display: str | None,
    coordinator: BatchCoordinator | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "out": str(job.out),
        "root": str(job.root),
        "log_dir": str(job.log_dir),
    }
    if proxy_display:
        result["proxy"] = proxy_display

    def make(status: str, **extra: object) -> dict[str, object]:
        result.update(status=status, **extra)
        return result

    job.out.parent.mkdir(parents=True, exist_ok=True)
    job.log_dir.mkdir(parents=True, exist_ok=True)
    command = [
        codex_bin, "exec", "--skip-git-repo-check", "-C", str(job.root), "-s", "workspace-write",
        "-c", f'model_reasoning_effort="{job.effort}"', "--ephemeral", "--json",
    ]
    for image in job.images:
        command += ["-i", str(image)]
    command.append("-")

    replace = "Replacing the existing file there is explicitly requested. " if job.out.exists() else ""
    task = (VERBATIM_TASK if job.verbatim else BRIEF_TASK).format(out=job.out, replace=replace, text=job.text)
    original_stat = job.out.stat() if job.out.exists() else None
    original_signature = (original_stat.st_ino, original_stat.st_size,
                          original_stat.st_mtime_ns, original_stat.st_ctime_ns) if original_stat else None
    started = time.time()
    timed_out = False
    proc: subprocess.Popen | None = None
    with (job.log_dir / "run.jsonl").open("w") as stdout, (job.log_dir / "run.err").open("w") as stderr:
        if coordinator is not None:
            with coordinator.lock:
                if coordinator.stop_event.is_set():
                    sig_name = coordinator.stop_signal or "stop signal"
                    return make("interrupted", elapsed_seconds=0.0,
                                error=f"not started; batch stopped by {sig_name}")
                try:
                    proc = subprocess.Popen(
                        command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True,
                        env=env, start_new_session=hasattr(os, "killpg"),
                    )
                except FileNotFoundError:
                    return make("failed", error=f"codex executable not found: {codex_bin}")
                except OSError as error:
                    return make("failed", error=f"cannot start codex executable {codex_bin}: {error}")
                coordinator.active.add(proc)
            try:
                proc.communicate(task, timeout=job.timeout)
                exit_code: int | None = proc.returncode
            except subprocess.TimeoutExpired:
                stop_group(proc)
                exit_code, timed_out = None, True
            finally:
                with coordinator.lock:
                    coordinator.active.discard(proc)
            if coordinator.stop_event.is_set():
                sig_name = coordinator.stop_signal or "stop signal"
                return make("interrupted", elapsed_seconds=round(time.time() - started, 1),
                            error=f"stopped by {sig_name}; the whole Codex run was terminated")
        else:
            try:
                proc = subprocess.Popen(
                    command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True,
                    env=env, start_new_session=hasattr(os, "killpg"),
                )
            except FileNotFoundError:
                return make("failed", error=f"codex executable not found: {codex_bin}")
            except OSError as error:
                return make("failed", error=f"cannot start codex executable {codex_bin}: {error}")
            # Codex runs in its own process group, so a caller's stop signal must be passed on here.
            previous = {sig: signal.signal(sig, raise_interrupted) for sig in STOP_SIGNALS}
            try:
                proc.communicate(task, timeout=job.timeout)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                ignore_stop_signals()
                stop_group(proc)
                exit_code, timed_out = None, True
            except Interrupted as stop:
                ignore_stop_signals()
                stop_group(proc)
                return make("interrupted", elapsed_seconds=round(time.time() - started, 1),
                            error=f"stopped by {stop}; the whole Codex run was terminated")
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
    elapsed = round(time.time() - started, 1)

    thread_id, messages, errors = parse_events((job.log_dir / "run.jsonl").read_text(errors="replace"))
    last = messages[-1] if messages else None
    final_prompt = FINAL_PROMPT.search(last or "")
    if job.verbatim:
        final_prompt_text: str | None = job.text  # exactly what the image tool received
    else:
        final_prompt_text = final_prompt.group(1).strip() if final_prompt else None
    result.update(elapsed_seconds=elapsed, thread_id=thread_id, codex_exit=exit_code, last_message=last,
                  final_prompt=final_prompt_text)

    def output_was_written() -> bool:
        try:
            current = job.out.stat()
        except OSError:
            return False
        signature = (current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns)
        return current.st_mtime >= started - 1 and signature != original_signature

    def fresh_png() -> tuple[int, int, bool] | None:
        return png_info(job.out) if output_was_written() else None

    source = "codex-copy"
    if fresh_png() is None:
        if output_was_written():
            return make("failed", error="Codex wrote a file at --out that is not a PNG")
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        recovered = recover(codex_home, thread_id, started, job.out)
        source = f"recovered:{recovered}" if recovered else ""
    info = fresh_png()
    if info:
        if not final_prompt_text:
            return make("incomplete", source=source, width=info[0], height=info[1], has_alpha=info[2],
                        error="PNG produced, but final prompt is unavailable; deliver it without generating again")
        return make("ok", source=source, width=info[0], height=info[1], has_alpha=info[2])

    if timed_out:
        return make("failed", error=f"timed out after {job.timeout:g}s")
    tool_errors = list(dict.fromkeys(IMAGE_TOOL_ERROR.findall((job.log_dir / "run.err").read_text(errors="replace"))))
    failure_text = "\n".join(errors + messages + tool_errors).strip()
    status = classify(failure_text)
    if status == "network_error":
        result["idle_cut_suspected"] = elapsed >= IDLE_CUT_AFTER
    return make(status, error=failure_text or f"no image produced; see {job.log_dir / 'run.err'}")


def parse_batch_jobs(
    batch_path: Path,
    *,
    batch_log_dir: Path,
    default_root: Path | None,
    default_verbatim: bool,
    default_overwrite: bool,
    default_effort: str,
    default_timeout: float,
) -> tuple[list[JobSpec] | None, str | None]:
    try:
        raw = json.loads(batch_path.expanduser().read_bytes().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, f"cannot read --batch manifest: {error}"
    if not isinstance(raw, list) or not raw:
        return None, "--batch manifest must be a non-empty JSON array of job objects"

    jobs: list[JobSpec] = []
    seen_outs: dict[Path, int] = {}
    for index, item in enumerate(raw):
        label = f"job[{index}]"
        if not isinstance(item, dict):
            return None, f"{label}: must be a JSON object"
        unknown = sorted(set(item) - JOB_KEYS)
        if unknown:
            return None, f"{label}: unknown key(s): {', '.join(unknown)}"
        out_val = item.get("out")
        if not isinstance(out_val, str) or not out_val.strip():
            return None, f"{label}: out must be a non-empty path string"

        brief_inline = item.get("brief")
        brief_file_val = item.get("brief_file")
        if brief_file_val is not None and (not isinstance(brief_file_val, str) or not brief_file_val.strip()):
            return None, f"{label}: brief_file must be a non-empty path string"

        images_val = item.get("images", [])
        if not isinstance(images_val, list) or any(not isinstance(p, str) or not p.strip() for p in images_val):
            return None, f"{label}: images must be an array of non-empty path strings"

        root_val = item.get("root")
        if root_val is not None and (not isinstance(root_val, str) or not root_val.strip()):
            return None, f"{label}: root must be a non-empty path string"

        verbatim = item.get("verbatim", default_verbatim)
        if not isinstance(verbatim, bool):
            return None, f"{label}: verbatim must be a boolean"

        overwrite = item.get("overwrite", default_overwrite)
        if not isinstance(overwrite, bool):
            return None, f"{label}: overwrite must be a boolean"

        effort = item.get("effort", default_effort)
        timeout = item.get("timeout", default_timeout)

        log_dir_val = item.get("log_dir")
        if log_dir_val is not None and (not isinstance(log_dir_val, str) or not log_dir_val.strip()):
            return None, f"{label}: log_dir must be a non-empty path string"
        item_log_dir = Path(log_dir_val) if log_dir_val is not None else batch_log_dir / f"job-{index + 1:02d}"

        job, error = validate_job(
            out_raw=Path(out_val),
            root_raw=Path(root_val) if root_val is not None else default_root,
            log_dir=item_log_dir,
            brief_file=Path(brief_file_val) if brief_file_val is not None else None,
            brief_inline=brief_inline,
            images_raw=[Path(p) for p in images_val],
            verbatim=verbatim,
            overwrite=overwrite,
            effort=effort,
            timeout=timeout,
            label=label,
        )
        if error or job is None:
            return None, error
        if job.out in seen_outs:
            return None, f"{label}: duplicate out path {job.out} (already used by job[{seen_outs[job.out]}])"
        seen_outs[job.out] = index
        jobs.append(job)
    return jobs, None


def run_batch(args: argparse.Namespace) -> int:
    batch_log_dir = (
        args.log_dir.expanduser().resolve()
        if args.log_dir
        else Path(tempfile.mkdtemp(prefix="codex-image-batch-"))
    )
    summary: dict[str, object] = {"log_dir": str(batch_log_dir), "parallel": args.parallel}

    def finish(status: str, **extra: object) -> int:
        summary.update(status=status, **extra)
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if status == "ok" else 1

    if args.brief_file or args.out or args.image:
        return finish("usage_error", error="--batch cannot be combined with --brief-file, --out, or --image")
    if args.parallel < 1:
        return finish("usage_error", error="--parallel must be at least 1")

    jobs, error = parse_batch_jobs(
        args.batch,
        batch_log_dir=batch_log_dir,
        default_root=args.root,
        default_verbatim=args.verbatim,
        default_overwrite=args.overwrite,
        default_effort=args.effort,
        default_timeout=args.timeout,
    )
    if error or jobs is None:
        return finish("usage_error", error=error)

    env, proxy_display, proxy_err = resolve_proxy()
    if proxy_err:
        return finish("proxy_unreachable", error=proxy_err)
    if proxy_display:
        summary["proxy"] = proxy_display

    batch_log_dir.mkdir(parents=True, exist_ok=True)
    workers = min(args.parallel, len(jobs))
    coordinator = BatchCoordinator()
    results: list[dict[str, object] | None] = [None] * len(jobs)
    started = time.time()
    interrupted_msg: str | None = None

    previous = {sig: signal.signal(sig, raise_interrupted) for sig in STOP_SIGNALS}
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    run_job,
                    job,
                    codex_bin=args.codex,
                    env=env,
                    proxy_display=proxy_display,
                    coordinator=coordinator,
                )
                for job in jobs
            ]
            try:
                for index, future in enumerate(futures):
                    results[index] = future.result()
            except Interrupted as stop:
                ignore_stop_signals()
                interrupted_msg = f"stopped by {stop}; active Codex runs were terminated"
                with coordinator.lock:
                    coordinator.stop_signal = str(stop)
                    coordinator.stop_event.set()
                    running = list(coordinator.active)
                for future in futures:
                    future.cancel()
                for proc in running:
                    stop_group(proc)
                for index, future in enumerate(futures):
                    if results[index] is not None:
                        continue
                    if future.cancelled():
                        job = jobs[index]
                        item_result: dict[str, object] = {
                            "out": str(job.out),
                            "root": str(job.root),
                            "log_dir": str(job.log_dir),
                            "status": "interrupted",
                            "elapsed_seconds": 0.0,
                            "error": f"not started; batch stopped by {stop}",
                        }
                        if proxy_display:
                            item_result["proxy"] = proxy_display
                        results[index] = item_result
                    else:
                        results[index] = future.result()
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)

    elapsed = round(time.time() - started, 1)
    final_results = [r for r in results if r is not None]
    counts: dict[str, int] = {}
    for item in final_results:
        item_status = str(item.get("status", "failed"))
        counts[item_status] = counts.get(item_status, 0) + 1

    if interrupted_msg:
        return finish("interrupted", elapsed_seconds=elapsed, counts=counts, results=final_results,
                      error=interrupted_msg)
    if counts.get("ok", 0) == len(final_results):
        return finish("ok", elapsed_seconds=elapsed, counts=counts, results=final_results)
    if counts.get("ok", 0) > 0 or counts.get("incomplete", 0) > 0:
        return finish("partial", elapsed_seconds=elapsed, counts=counts, results=final_results)
    return finish("failed", elapsed_seconds=elapsed, counts=counts, results=final_results)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brief-file", type=Path,
                        help="what to create; Codex shapes the prompt unless --verbatim")
    parser.add_argument("--verbatim", action="store_true", help="pass the brief/prompt to the image tool unchanged")
    parser.add_argument("--out", type=Path, help="destination .png path")
    parser.add_argument("--root", type=Path, help="Codex working root; must contain --out (default: its folder)")
    parser.add_argument("--image", action="append", default=[], type=Path, help="reference image (repeatable)")
    parser.add_argument("--batch", type=Path, help="JSON array of job objects to run in parallel")
    parser.add_argument("--parallel", type=int, default=DEFAULT_PARALLEL,
                        help=f"maximum concurrent Codex runs in --batch mode (default: {DEFAULT_PARALLEL})")
    parser.add_argument("--effort", default="medium", help="model_reasoning_effort for the Codex turn")
    parser.add_argument("--timeout", type=float, default=900.0, help="seconds before a run is stopped")
    parser.add_argument("--log-dir", type=Path, help="where run.jsonl and run.err go (default: new temp dir)")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing an existing --out file")
    parser.add_argument("--codex", default="codex", help="codex executable")
    args = parser.parse_args()

    if args.batch is not None:
        return run_batch(args)

    if args.brief_file is None or args.out is None:
        print(json.dumps({"status": "usage_error",
                          "error": "pass --brief-file and --out for one image, or --batch for a parallel batch"},
                         ensure_ascii=False))
        return 1

    out = args.out.expanduser().resolve()
    root = args.root.expanduser().resolve() if args.root else out.parent
    log_dir = args.log_dir.expanduser().resolve() if args.log_dir else Path(tempfile.mkdtemp(prefix="codex-image-"))

    def finish(status: str, **extra: object) -> int:
        payload: dict[str, object] = {"out": str(out), "root": str(root), "log_dir": str(log_dir),
                                      "status": status, **extra}
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if status == "ok" else 1

    job, error = validate_job(
        out_raw=args.out,
        root_raw=args.root,
        log_dir=log_dir,
        brief_file=args.brief_file,
        brief_inline=None,
        images_raw=args.image,
        verbatim=args.verbatim,
        overwrite=args.overwrite,
        effort=args.effort,
        timeout=args.timeout,
    )
    if error or job is None:
        return finish("usage_error", error=error)

    env, proxy_display, proxy_err = resolve_proxy()
    if proxy_err:
        return finish("proxy_unreachable", error=proxy_err)

    result = run_job(job, codex_bin=args.codex, env=env, proxy_display=proxy_display)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
