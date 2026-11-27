#!/usr/bin/env python3
"""Regression checks for codex_image.py against a fake codex executable."""

from __future__ import annotations

import json
import os
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

SCRIPT = Path(__file__).with_name("codex_image.py")
sys.path.insert(0, str(SCRIPT.parent))
from codex_image import classify  # noqa: E402

THREAD = "01a11ac5-b216-7f52-97b8-4d5fa1683b73"


def png_bytes(width: int, height: int, color_type: int = 0) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    raw = b"".join(b"\x00" + b"\x00" * width * channels for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


FAKE = f"""#!{sys.executable}
import json, os, re, sys
from pathlib import Path
task = sys.stdin.read()
out = re.search(r"Save the final image as a PNG at (.+?)\\. ", task).group(1)
png = bytes.fromhex({png_bytes(30, 20).hex()!r})
alpha_png = bytes.fromhex({png_bytes(30, 20, 6).hex()!r})
print(json.dumps({{"type": "thread.started", "thread_id": {THREAD!r}}}))
mode = os.environ["FAKE_MODE"]
if mode == "copy":
    Path(out).write_bytes(png)
    kind = "verbatim" if "verbatim" in task.splitlines()[0] else "brief"
    proxy = os.environ.get("HTTPS_PROXY", "")
    reply = f"Saved ({{kind}}) proxy=[{{proxy}}]."
    if kind == "brief":  # like Codex: only the brief task asks for a FINAL_PROMPT line
        reply += "\\nFINAL_PROMPT: a red square, landscape 3:2"
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": reply}}}}))
elif mode == "alpha":
    Path(out).write_bytes(alpha_png)
elif mode in ("recover", "recover_no_prompt"):
    folder = Path(os.environ["CODEX_HOME"]) / "generated_images" / {THREAD!r}
    folder.mkdir(parents=True)
    (folder / "exec-1.png").write_bytes(png)
elif mode in ("missing_prompt", "empty_prompt"):
    Path(out).write_bytes(png)
    if mode == "empty_prompt":
        print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": "FINAL_PROMPT:   "}}}}))
elif mode == "truncated":
    Path(out).write_bytes(png[:26])
elif mode == "nonpng":
    Path(out).write_text("not an image")
elif mode == "network":
    text = "FAILED=network error: error sending request"
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": text}}}}))
elif mode == "policy":
    text = "FAILED=request rejected by the safety system"
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": text}}}}))
elif mode == "stderr_network":
    text = "Using the imagegen skill."
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": text}}}}))
    print("ERROR codex_core::tools::router: error=image generation failed: network error: error sending request",
          file=sys.stderr)
elif mode == "policy_noise":
    text = "FAILED=request rejected by the safety system"
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": text}}}}))
    print("ERROR rmcp::transport::worker: error sending request for url (https://mcp.example/mcp)", file=sys.stderr)
elif mode == "hang":
    # Like the npm wrapper: a child keeps running if only this process is killed.
    import subprocess, time
    late = "import time, pathlib; time.sleep(4); pathlib.Path(%r).write_bytes(%r)" % (out, png)
    subprocess.Popen([sys.executable, "-c", late])
    sys.stdout.flush()
    time.sleep(60)
elif mode == "batch_parallel":
    import fcntl, time
    tracker = Path(os.environ["BATCH_TRACKER"])
    def update(delta: int) -> None:
        with tracker.open("a+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            fh.seek(0)
            raw = fh.read().strip()
            cur, peak = (int(x) for x in raw.split()) if raw else (0, 0)
            cur += delta
            peak = max(peak, cur)
            fh.seek(0)
            fh.truncate()
            fh.write(f"{{cur}} {{peak}}")
            fh.flush()
            fcntl.flock(fh, fcntl.LOCK_UN)
    update(1)
    try:
        time.sleep(0.4)
        Path(out).write_bytes(png)
    finally:
        update(-1)
    kind = "verbatim" if "verbatim" in task.splitlines()[0] else "brief"
    reply = f"Saved ({{kind}}) for {{Path(out).name}}"
    if kind == "brief":
        reply += f"\\nFINAL_PROMPT: prompt for {{Path(out).name}}"
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": reply}}}}))
elif mode == "batch_mixed":
    stem = Path(out).stem
    if stem == "ok":
        Path(out).write_bytes(png)
        print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": "FINAL_PROMPT: ok prompt"}}}}))
    elif stem == "incomplete":
        Path(out).write_bytes(png)
    else:
        print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": "FAILED=request rejected by the safety system"}}}}))
if mode in ("alpha", "recover"):
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": "FINAL_PROMPT: a red square, landscape 3:2"}}}}))
"""


def run(tmp: Path, mode: str, out: Path, *extra: str, proxy: str = "") -> tuple[int, dict]:
    env = dict(os.environ, FAKE_MODE=mode, CODEX_HOME=str(tmp / f"home-{mode}"), X9_CODEX_IMAGE_PROXY=proxy)
    env.pop("HTTPS_PROXY", None)
    brief = tmp / "brief.txt"
    brief.write_text("a red square, landscape 3:2")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--brief-file", str(brief), "--out", str(out),
                           "--codex", str(tmp / "codex"), "--log-dir", str(tmp / f"logs-{mode}"), *extra],
                          capture_output=True, text=True, env=env)
    return proc.returncode, json.loads(proc.stdout)


def run_batch(tmp: Path, mode: str, jobs: object, *extra: str, proxy: str = "",
              extra_env: dict[str, str] | None = None) -> tuple[int, dict]:
    env = dict(os.environ, FAKE_MODE=mode, CODEX_HOME=str(tmp / f"home-batch-{mode}"), X9_CODEX_IMAGE_PROXY=proxy)
    env.pop("HTTPS_PROXY", None)
    if extra_env:
        env.update(extra_env)
    manifest = tmp / f"jobs-{mode}-{time.time_ns()}.json"
    manifest.write_text(json.dumps(jobs))
    proc = subprocess.run([sys.executable, str(SCRIPT), "--batch", str(manifest),
                           "--codex", str(tmp / "codex"), "--log-dir", str(tmp / f"logs-batch-{mode}"), *extra],
                          capture_output=True, text=True, env=env)
    return proc.returncode, json.loads(proc.stdout)


def main() -> None:
    assert classify("FAILED=network error: error sending request") == "network_error"
    assert classify("FAILED=content policy") == "failed"

    with tempfile.TemporaryDirectory() as name:
        tmp = Path(name)
        (tmp / "codex").write_text(FAKE)
        (tmp / "codex").chmod(0o755)

        code, result = run(tmp, "copy", tmp / "a.png")
        assert code == 0 and result["status"] == "ok", result
        assert (result["width"], result["height"]) == (30, 20) and result["source"] == "codex-copy", result
        assert result["thread_id"] == THREAD and result["has_alpha"] is False, result
        assert result["final_prompt"] == "a red square, landscape 3:2", result
        assert "(brief)" in result["last_message"], result

        for mode in ("missing_prompt", "empty_prompt", "recover_no_prompt"):
            destination = tmp / f"{mode}.png"
            code, result = run(tmp, mode, destination)
            assert code == 1 and result["status"] == "incomplete", result
            assert not result["final_prompt"] and "prompt" in result["error"], result
            assert destination.read_bytes() == png_bytes(30, 20), "deliver the PNG without generating again"
            assert (result["width"], result["height"]) == (30, 20), result

        code, result = run(tmp, "copy", tmp / "v.png", "--verbatim")
        assert code == 0 and "(verbatim)" in result["last_message"], result
        assert result["final_prompt"] == "a red square, landscape 3:2", "verbatim reports the prompt it sent"

        exact = tmp / "exact.txt"
        exact.write_bytes(b"  a red square\r\n\r\n")
        code, result = run(tmp, "copy", tmp / "exact.png", "--verbatim", "--brief-file", str(exact))
        assert code == 0 and result["final_prompt"] == "  a red square\r\n\r\n", result

        code, result = run(tmp, "alpha", tmp / "alpha.png")
        assert code == 0 and result["has_alpha"] is True, result

        code, result = run(tmp, "copy", tmp / "a.png")
        assert code == 1 and result["status"] == "usage_error", "existing file must not be overwritten"

        code, result = run(tmp, "recover", tmp / "b.png")
        assert code == 0 and result["source"].startswith("recovered:"), result

        code, result = run(tmp, "nonpng", tmp / "c.png")
        assert code == 1 and result["status"] == "failed" and "not a PNG" in result["error"], result

        code, result = run(tmp, "truncated", tmp / "truncated.png")
        assert code == 1 and result["status"] == "failed" and "not a PNG" in result["error"], result

        code, result = run(tmp, "network", tmp / "d.png")
        assert code == 1 and result["status"] == "network_error", result
        assert result["idle_cut_suspected"] is False, "a fast network failure is transient"

        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        proxy = f"http://127.0.0.1:{listener.getsockname()[1]}"
        code, result = run(tmp, "copy", tmp / "p.png", proxy=proxy)
        assert code == 0 and f"proxy=[{proxy}]" in result["last_message"], result
        listener.close()
        code, result = run(tmp, "copy", tmp / "q.png", proxy=proxy)
        assert code == 1 and result["status"] == "proxy_unreachable", result
        assert not (tmp / "q.png").exists(), "no run may start behind a dead proxy"
        credentialed = proxy.replace("http://", "http://synthetic-user:synthetic-password@")
        code, result = run(tmp, "copy", tmp / "secret-proxy.png", proxy=credentialed)
        assert code == 1 and result["status"] == "proxy_unreachable", result
        assert "synthetic-password" not in json.dumps(result), result
        assert "synthetic-user" not in json.dumps(result), result
        code, result = run(tmp, "copy", tmp / "r.png", proxy="socks5h://127.0.0.1:1")
        assert code == 1 and result["status"] == "proxy_unreachable", result
        code, result = run(tmp, "copy", tmp / "bad-proxy.png", proxy="http://localhost:bad")
        assert code == 1 and result["status"] == "proxy_unreachable", result
        code, result = run(tmp, "copy", tmp / "missing-brief.png", "--brief-file", str(tmp / "missing.txt"))
        assert code == 1 and result["status"] == "usage_error", result
        code, result = run(tmp, "copy", tmp / "s.png")
        assert code == 0 and "proxy=[]" in result["last_message"], "no proxy unless configured"

        code, result = run(tmp, "policy", tmp / "e.png")
        assert code == 1 and result["status"] == "failed" and "safety" in result["error"], result

        code, result = run(tmp, "stderr_network", tmp / "h.png")
        assert code == 1 and result["status"] == "network_error", "image tool errors in stderr count"
        assert "image generation failed" in result["error"], result

        code, result = run(tmp, "policy_noise", tmp / "i.png")
        assert code == 1 and result["status"] == "failed", "other connections' errors must not mask a refusal"

        code, result = run(tmp, "hang", tmp / "j.png", "--timeout", "2")
        assert code == 1 and "timed out" in result["error"], result
        time.sleep(4)
        assert not (tmp / "j.png").exists(), "a timed-out run must not leave a process that writes the image"

        # A stop signal to the script must take the whole Codex run down with it.
        env = dict(os.environ, FAKE_MODE="hang", CODEX_HOME=str(tmp / "home-int"), X9_CODEX_IMAGE_PROXY="")
        (tmp / "brief.txt").write_text("a red square, landscape 3:2")
        proc = subprocess.Popen([sys.executable, str(SCRIPT), "--brief-file", str(tmp / "brief.txt"),
                                 "--out", str(tmp / "k.png"), "--codex", str(tmp / "codex"),
                                 "--log-dir", str(tmp / "logs-int")], stdout=subprocess.PIPE, text=True, env=env)
        time.sleep(1.5)
        proc.send_signal(signal.SIGTERM)
        result = json.loads(proc.communicate(timeout=30)[0])
        assert proc.returncode == 1 and result["status"] == "interrupted", result
        time.sleep(4)
        assert not (tmp / "k.png").exists(), "an interrupted run must not leave a process that writes the image"

        (tmp / "broken").write_text("not a program")
        (tmp / "broken").chmod(0o755)
        brief = tmp / "brief.txt"
        proc = subprocess.run([sys.executable, str(SCRIPT), "--brief-file", str(brief), "--out", str(tmp / "l.png"),
                               "--codex", str(tmp / "broken"), "--log-dir", str(tmp / "logs-broken")],
                              capture_output=True, text=True)
        result = json.loads(proc.stdout)
        assert result["status"] == "failed" and "cannot start" in result["error"], result

        code, result = run(tmp, "copy", tmp / "f.png", "--root", str(tmp / "elsewhere"))
        assert code == 1 and result["status"] == "usage_error", result

        # A recently created existing PNG is not evidence that this run wrote it.
        recent = tmp / "recent.png"
        recent.write_bytes(png_bytes(5, 5))
        before = recent.read_bytes()
        code, result = run(tmp, "network", recent, "--overwrite")
        assert code == 1 and result["status"] == "network_error", result
        assert recent.read_bytes() == before

        # A stale PNG at --out must not count as a new result.
        (tmp / "g.png").write_bytes(png_bytes(5, 5))
        os.utime(tmp / "g.png", (0, 0))
        code, result = run(tmp, "network", tmp / "g.png", "--overwrite")
        assert code == 1 and result["status"] == "network_error", result

        # Batch parallel mode: runs concurrently up to --parallel, preserves order, supports inline brief + brief_file + images + verbatim.
        tracker = tmp / "concurrency.txt"
        ref_img = tmp / "ref.png"
        ref_img.write_bytes(png_bytes(10, 10))
        file_brief = tmp / "batch-brief.txt"
        file_brief.write_text("brief from file")
        batch_jobs = [
            {"brief": "first image", "out": str(tmp / "batch-1.png")},
            {"brief_file": str(file_brief), "out": str(tmp / "batch-2.png"), "images": [str(ref_img)]},
            {"brief": "  exact verbatim  ", "out": str(tmp / "batch-3.png"), "verbatim": True},
            {"brief": "fourth image", "out": str(tmp / "batch-4.png")},
        ]
        code, result = run_batch(tmp, "batch_parallel", batch_jobs, "--parallel", "2",
                                 extra_env={"BATCH_TRACKER": str(tracker)})
        assert code == 0 and result["status"] == "ok", result
        assert result["parallel"] == 2 and result["counts"] == {"ok": 4}, result
        assert [Path(r["out"]).name for r in result["results"]] == [
            "batch-1.png", "batch-2.png", "batch-3.png", "batch-4.png",
        ], result
        assert result["results"][2]["final_prompt"] == "  exact verbatim  ", result
        cur, peak = (int(x) for x in tracker.read_text().split())
        assert cur == 0 and peak == 2, f"expected peak concurrency 2, got cur={cur} peak={peak}"

        # Batch partial and all-failed statuses.
        mixed_jobs = [
            {"brief": "one", "out": str(tmp / "ok.png")},
            {"brief": "two", "out": str(tmp / "incomplete.png")},
            {"brief": "three", "out": str(tmp / "refused.png")},
        ]
        code, result = run_batch(tmp, "batch_mixed", mixed_jobs)
        assert code == 1 and result["status"] == "partial", result
        assert result["counts"] == {"ok": 1, "incomplete": 1, "failed": 1}, result
        assert [r["status"] for r in result["results"]] == ["ok", "incomplete", "failed"], result

        code, result = run_batch(tmp, "policy", [
            {"brief": "one", "out": str(tmp / "fail-1.png")},
            {"brief": "two", "out": str(tmp / "fail-2.png")},
        ])
        assert code == 1 and result["status"] == "failed", result
        assert result["counts"] == {"failed": 2}, result

        # Batch pre-flight validation fails before starting any Codex run.
        code, result = run_batch(tmp, "copy", [
            {"brief": "one", "out": str(tmp / "dup.png")},
            {"brief": "two", "out": str(tmp / "dup.png")},
        ])
        assert code == 1 and result["status"] == "usage_error" and "duplicate" in result["error"], result
        assert not (tmp / "dup.png").exists()

        code, result = run_batch(tmp, "copy", [
            {"brief": "one", "out": str(tmp / "bad-key.png"), "image": str(ref_img)},
        ])
        assert code == 1 and result["status"] == "usage_error" and "unknown key" in result["error"], result
        assert not (tmp / "bad-key.png").exists()

        code, result = run_batch(tmp, "copy", [])
        assert code == 1 and result["status"] == "usage_error", result

        code, result = run_batch(tmp, "copy", [{"brief": "one", "out": str(tmp / "p0.png")}], "--parallel", "0")
        assert code == 1 and result["status"] == "usage_error", result

        code, result = run_batch(tmp, "copy", [{"brief": "one", "out": str(tmp / "combo.png")}],
                                 "--out", str(tmp / "other.png"))
        assert code == 1 and result["status"] == "usage_error", result

        # Dead proxy in batch mode fails before starting any run.
        code, result = run_batch(tmp, "copy", [
            {"brief": "one", "out": str(tmp / "bp-1.png")},
            {"brief": "two", "out": str(tmp / "bp-2.png")},
        ], proxy="http://127.0.0.1:1")
        assert code == 1 and result["status"] == "proxy_unreachable", result
        assert not (tmp / "bp-1.png").exists() and not (tmp / "bp-2.png").exists()

        # SIGTERM during a running batch terminates all active Codex process groups and leaves no late files.
        hang_manifest = tmp / "hang-batch.json"
        hang_manifest.write_text(json.dumps([
            {"brief": "one", "out": str(tmp / "bh-1.png")},
            {"brief": "two", "out": str(tmp / "bh-2.png")},
            {"brief": "three", "out": str(tmp / "bh-3.png")},
        ]))
        env = dict(os.environ, FAKE_MODE="hang", CODEX_HOME=str(tmp / "home-batch-int"), X9_CODEX_IMAGE_PROXY="")
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPT), "--batch", str(hang_manifest), "--parallel", "2",
             "--codex", str(tmp / "codex"), "--log-dir", str(tmp / "logs-batch-int")],
            stdout=subprocess.PIPE, text=True, env=env,
        )
        time.sleep(1.5)
        proc.send_signal(signal.SIGTERM)
        result = json.loads(proc.communicate(timeout=30)[0])
        assert proc.returncode == 1 and result["status"] == "interrupted", result
        assert all(r["status"] == "interrupted" for r in result["results"]), result
        time.sleep(4)
        for idx in (1, 2, 3):
            assert not (tmp / f"bh-{idx}.png").exists(), "an interrupted batch must not leave a process that writes files"

    print("ok")


if __name__ == "__main__":
    main()
