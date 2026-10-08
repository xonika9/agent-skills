#!/usr/bin/env python3
"""Regression checks for codex_image.py against a fake codex executable."""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

SCRIPT = Path(__file__).with_name("codex_image.py")
sys.path.insert(0, str(SCRIPT.parent))
from codex_image import classify  # noqa: E402

THREAD = "01a11ac5-b216-7f52-97b8-4d5fa1683b73"


def png_bytes(width: int, height: int, color_type: int = 0) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    raw = b"".join(b"\x00" + b"\x00" * width for _ in range(height))
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
    reply = f"Saved ({{kind}}).\\nFINAL_PROMPT: a red square, landscape 3:2"
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": reply}}}}))
elif mode == "alpha":
    Path(out).write_bytes(alpha_png)
elif mode == "recover":
    folder = Path(os.environ["CODEX_HOME"]) / "generated_images" / {THREAD!r}
    folder.mkdir(parents=True)
    (folder / "exec-1.png").write_bytes(png)
elif mode == "nonpng":
    Path(out).write_text("not an image")
elif mode == "network":
    text = "FAILED=network error: error sending request"
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": text}}}}))
elif mode == "policy":
    text = "FAILED=request rejected by the safety system"
    print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": text}}}}))
"""


def run(tmp: Path, mode: str, out: Path, *extra: str) -> tuple[int, dict]:
    env = dict(os.environ, FAKE_MODE=mode, CODEX_HOME=str(tmp / f"home-{mode}"))
    brief = tmp / "brief.txt"
    brief.write_text("a red square, landscape 3:2")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--brief-file", str(brief), "--out", str(out),
                           "--codex", str(tmp / "codex"), "--log-dir", str(tmp / f"logs-{mode}"), *extra],
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

        code, result = run(tmp, "copy", tmp / "v.png", "--verbatim")
        assert code == 0 and "(verbatim)" in result["last_message"], result

        code, result = run(tmp, "alpha", tmp / "alpha.png")
        assert code == 0 and result["has_alpha"] is True, result

        code, result = run(tmp, "copy", tmp / "a.png")
        assert code == 1 and result["status"] == "usage_error", "existing file must not be overwritten"

        code, result = run(tmp, "recover", tmp / "b.png")
        assert code == 0 and result["source"].startswith("recovered:"), result

        code, result = run(tmp, "nonpng", tmp / "c.png")
        assert code == 1 and result["status"] == "failed" and "not a PNG" in result["error"], result

        code, result = run(tmp, "network", tmp / "d.png")
        assert code == 1 and result["status"] == "network_error", result

        code, result = run(tmp, "policy", tmp / "e.png")
        assert code == 1 and result["status"] == "failed" and "safety" in result["error"], result

        code, result = run(tmp, "copy", tmp / "f.png", "--root", str(tmp / "elsewhere"))
        assert code == 1 and result["status"] == "usage_error", result

        # A stale PNG at --out must not count as a new result.
        (tmp / "g.png").write_bytes(png_bytes(5, 5))
        os.utime(tmp / "g.png", (0, 0))
        code, result = run(tmp, "network", tmp / "g.png", "--overwrite")
        assert code == 1 and result["status"] == "network_error", result

    print("ok")


if __name__ == "__main__":
    main()
