#!/usr/bin/env python3
"""Local timestamped transcripts for video and audio files (ffmpeg + whisper.cpp).

Subcommands:
  check   [--download]                     report dependencies; fetch missing default models
  run     PATH... [--out DIR] [--lang L] [--force] [--model FILE]
  search  QUERY PATH... [--max N]

Outputs per source `<stem>.<ext>`: `<stem>.transcript.srt` and `<stem>.transcript.txt`,
next to the source or mirrored under --out. Only stdlib is used.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

# Extensions picked up when scanning folders; files named explicitly are passed to ffmpeg as-is.
MEDIA_EXT = {
    ".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mts", ".m2ts", ".ts", ".mpg", ".mpeg",
    ".wmv", ".flv", ".3gp", ".mp3", ".m4a", ".wav", ".flac", ".ogg", ".oga", ".opus", ".aac",
    ".wma", ".aif", ".aiff", ".amr",
}
SRT_SUFFIX = ".transcript.srt"
TXT_SUFFIX = ".transcript.txt"
MODELS = {
    "whisper": (
        "ggml-large-v3-turbo-q8_0.bin",
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q8_0.bin",
    ),
    "vad": (
        "ggml-silero-v6.2.0.bin",
        "https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v6.2.0.bin",
    ),
}
TIME_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d+):(\d{2}):(\d{2})[,.](\d{3})")
LANG_RE = re.compile(r"auto-detected language:\s*([a-z]{2,3})")
MIN_TIMEOUT = 900  # seconds per file, raised to 3x the audio length for long recordings


def models_dir() -> Path:
    env = os.environ.get("X9_TRANSCRIPTS_MODELS")
    return Path(env).expanduser() if env else Path.home() / ".cache" / "x9-video-transcripts" / "models"


def whisper_cli() -> str | None:
    return os.environ.get("X9_WHISPER_CLI") or shutil.which("whisper-cli")


# ---------- pure helpers (unit-tested) ----------

def parse_srt(text: str) -> list[tuple[float, float, str]]:
    segs: list[tuple[float, float, str]] = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = [l.strip() for l in block.strip().splitlines()]
        for k, line in enumerate(lines):
            m = TIME_RE.search(line)
            if not m:
                continue
            g = [int(x) for x in m.groups()]
            body = " ".join(l for l in lines[k + 1:] if l).strip()
            if body:
                segs.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
                             g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, body))
            break
    return segs


def hms(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def srt_to_txt(srt_text: str, source: Path, lang: str) -> str:
    lines = [f"# source: {source}", f"# language: {lang}"]
    lines += [f"[{hms(s)}] {t}" for s, _e, t in parse_srt(srt_text)]
    return "\n".join(lines) + "\n"


def _walk(folder: Path):
    """Media files under folder; hidden entries are skipped and folder symlinks are not followed."""
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            f = Path(dirpath) / name
            if not name.startswith(".") and f.suffix.lower() in MEDIA_EXT and f.is_file():
                yield f


def discover(paths: list[Path]) -> list[tuple[Path, Path]]:
    """Return (source, root) pairs; root is the widest folder argument containing the source."""
    args = [Path(os.path.abspath(p.expanduser())) for p in paths]
    missing = [str(p) for p in args if not p.exists()]
    if missing:
        raise FileNotFoundError(", ".join(missing))
    folders = sorted((p for p in args if p.is_dir()), key=lambda p: len(p.parts))
    sources: list[Path] = []
    for p in args:
        sources += list(_walk(p)) if p.is_dir() else [p]
    found: dict[Path, Path] = {}
    for f in sources:
        root = next((d for d in folders if f.parent == d or d in f.parents), f.parent)
        found.setdefault(f, root)
    return list(found.items())


def output_base(source: Path, root: Path, out: Path | None) -> Path:
    stem = source.name[: -len(source.suffix)] if source.suffix else source.name
    if out is None:
        return source.parent / stem
    return Path(os.path.abspath(out.expanduser())) / source.parent.relative_to(root) / stem


def output_key(base: Path) -> str:
    # macOS and Windows volumes are usually case-insensitive: Clip.MP4 and clip.mov share outputs.
    return str(base).casefold()


def is_current(source: Path, base: Path) -> bool:
    srt, txt = Path(str(base) + SRT_SUFFIX), Path(str(base) + TXT_SUFFIX)
    if not (srt.exists() and txt.exists()):
        return False
    src_m = source.stat().st_mtime
    return srt.stat().st_mtime >= src_m and txt.stat().st_mtime >= src_m


def normalize(s: str) -> str:
    return s.casefold().replace("ё", "е")


def stem(term: str) -> str:
    """Drop a likely inflectional ending so «загородный» also finds «загородном»."""
    if len(term) >= 6:
        return term[:-2]
    if len(term) == 5:
        return term[:-1]
    return term


def search_lines(lines: list[str], query: str) -> list[int]:
    """Indexes of timestamped lines that contain every query term.

    A phrase split across a segment boundary matches at the first of the two lines,
    unless the next line alone already contains every term.
    """
    terms = [stem(w) for w in normalize(query).split()]
    rows = [i for i, l in enumerate(lines) if l.startswith("[")]
    hits: list[int] = []
    for k, i in enumerate(rows):
        cur = normalize(lines[i])
        nxt = normalize(lines[rows[k + 1]]) if k + 1 < len(rows) else ""
        if all(t in cur for t in terms) or (
            all(t in cur + " " + nxt for t in terms) and not all(t in nxt for t in terms)
        ):
            hits.append(i)
    return hits


# ---------- side-effecting commands ----------

def check(download: bool) -> int:
    report: dict = {"ffmpeg": shutil.which("ffmpeg"), "whisper_cli": whisper_cli(), "models_dir": str(models_dir())}
    for key, (name, url) in MODELS.items():
        path = models_dir() / name
        if not path.exists() and download:
            try:
                fetch(url, path)
            except Exception as e:  # report instead of a traceback
                report[f"{key}_download_error"] = str(e)
        report[f"{key}_model"] = str(path) if path.exists() else None
    missing = [k for k in ("ffmpeg", "whisper_cli", "whisper_model", "vad_model") if report[k] is None]
    report["status"] = "ok" if not missing else "missing"
    report["missing"] = missing
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if not missing else 2


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    print(f"downloading {url}", file=sys.stderr)
    with urllib.request.urlopen(url, timeout=60) as r, open(part, "wb") as f:
        expected = int(r.headers.get("Content-Length") or 0)
        shutil.copyfileobj(r, f, length=1 << 20)
    if expected and part.stat().st_size != expected:
        part.unlink()
        raise RuntimeError(f"incomplete download: {url}")
    os.replace(part, dest)


def duration(path: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True, timeout=120,
        )
        return float(r.stdout.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return 0.0


class WhisperError(RuntimeError):
    """A recognizer failure; the same message on consecutive files aborts the batch."""


def _last_line(text: str, fallback: str) -> str:
    return (text.strip().splitlines() or [fallback])[-1]


def transcribe_one(source: Path, base: Path, lang: str, model: Path, vad: Path, cli: str, seconds: float) -> int:
    """Write both outputs atomically; return the number of transcript segments."""
    timeout = max(MIN_TIMEOUT, 3 * seconds)
    with tempfile.TemporaryDirectory(prefix="x9-transcripts-") as tmp:
        wav = Path(tmp) / "audio.wav"
        try:
            r = subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-i", str(source), "-vn", "-ar", "16000", "-ac", "1",
                 "-c:a", "pcm_s16le", str(wav)],
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"ffmpeg: no result after {timeout:.0f}s")
        if r.returncode != 0 or not wav.exists():
            raise RuntimeError("ffmpeg: " + _last_line(r.stderr, "no audio stream"))
        cmd = [cli, "-m", str(model), "-l", lang, "--vad", "-vm", str(vad), "-f", str(wav),
               "-osrt", "-of", str(Path(tmp) / "out")]  # stdout/stderr are captured; stderr names the detected language
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise WhisperError(f"whisper-cli: no result after {timeout:.0f}s")
        produced = Path(tmp) / "out.srt"
        if r.returncode != 0 or not produced.exists():
            raise WhisperError("whisper-cli: " + _last_line(r.stderr, "no output"))
        detected = LANG_RE.search(r.stderr or "")
        srt_text = produced.read_text(encoding="utf-8", errors="replace")
        srt, txt = Path(str(base) + SRT_SUFFIX), Path(str(base) + TXT_SUFFIX)
        for dest, content in ((srt, srt_text),
                              (txt, srt_to_txt(srt_text, source, detected.group(1) if detected else lang))):
            part = dest.with_name(dest.name + ".part")
            try:
                part.write_text(content, encoding="utf-8")
                os.replace(part, dest)
            finally:
                part.unlink(missing_ok=True)
        return len(parse_srt(srt_text))


def run(paths: list[Path], out: Path | None, lang: str, force: bool, model: Path | None) -> int:
    cli = whisper_cli()
    model = model or models_dir() / MODELS["whisper"][0]
    vad = models_dir() / MODELS["vad"][0]
    problems = [n for n, ok in (("ffmpeg", shutil.which("ffmpeg")), ("whisper-cli", cli),
                                (f"model {model}", model.exists()), (f"vad model {vad}", vad.exists())) if not ok]
    if problems:
        print(json.dumps({"status": "setup_required", "missing": problems}, ensure_ascii=False))
        return 2
    try:
        items = discover(paths)
    except FileNotFoundError as e:
        print(json.dumps({"status": "failed", "error": f"not found: {e}"}, ensure_ascii=False))
        return 2
    if not items:
        print(json.dumps({"status": "no_media", "error": "no audio or video files found"}, ensure_ascii=False))
        return 2
    planned: dict[str, Path] = {}
    summary: dict = {"files": len(items), "done": 0, "skipped": 0, "failed": [], "collisions": [],
                     "no_speech": [], "audio_seconds": 0.0}
    started = time.time()
    last_whisper_error = None
    for n, (source, root) in enumerate(items, 1):
        base = output_base(source, root, out)
        label = f"[{n}/{len(items)}] {source}"
        key = output_key(base)
        if key in planned:
            summary["collisions"].append({"file": str(source), "same_output_as": str(planned[key])})
            print(f"{label}: output name collides with {planned[key]}", file=sys.stderr)
            continue
        planned[key] = source
        if not force and is_current(source, base):
            summary["skipped"] += 1
            print(f"{label}: up to date", file=sys.stderr)
            continue
        try:
            base.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            summary["failed"].append({"file": str(source), "error": f"cannot create output folder: {e}"})
            print(f"{label}: FAILED cannot create output folder", file=sys.stderr)
            continue
        if not os.access(base.parent, os.W_OK):
            summary["failed"].append({"file": str(source), "error": f"output folder is not writable: {base.parent}"})
            print(f"{label}: FAILED output folder is not writable", file=sys.stderr)
            continue
        secs = duration(source)
        t0 = time.time()
        try:
            segments = transcribe_one(source, base, lang, model, vad, cli, secs)  # type: ignore[arg-type]
        except WhisperError as e:
            summary["failed"].append({"file": str(source), "error": str(e)})
            print(f"{label}: FAILED {e}", file=sys.stderr)
            if str(e) == last_whisper_error:
                summary["status"] = "aborted"
                summary["not_attempted"] = [str(s) for s, _r in items[n:]]
                summary["error"] = "the same whisper-cli error repeated on consecutive files"
                break
            last_whisper_error = str(e)
            continue
        except Exception as e:  # report and continue with the batch
            summary["failed"].append({"file": str(source), "error": str(e)})
            print(f"{label}: FAILED {e}", file=sys.stderr)
            continue
        last_whisper_error = None
        summary["done"] += 1
        summary["audio_seconds"] += secs
        if segments == 0:
            summary["no_speech"].append(str(source))
        print(f"{label}: done ({hms(secs)} audio in {time.time() - t0:.0f}s, {segments} segments)", file=sys.stderr)
    summary["elapsed_seconds"] = round(time.time() - started, 1)
    summary["audio_seconds"] = round(summary["audio_seconds"], 1)
    if "status" not in summary:
        summary["status"] = "ok" if not (summary["failed"] or summary["collisions"]) else "partial"
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if summary["status"] == "ok" else 1


def search(query: str, paths: list[Path], limit: int) -> int:
    files: list[Path] = []
    for p in paths:
        p = p.expanduser()
        if not p.exists():
            print(f"not found: {p}")
            return 2
        files += [p] if p.is_file() else sorted(p.rglob("*" + TXT_SUFFIX))
    if not files:
        print("no transcripts found; run the run command first")
        return 2
    shown = 0
    for f in files:
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        src = next((l[len("# source: "):] for l in lines[:3] if l.startswith("# source: ")), str(f))
        for i in search_lines(lines, query):
            if shown >= limit:
                print("... more matches; raise --max to see them")
                return 0
            print(f"{src}\t{lines[i]}")
            shown += 1
    if not shown:
        print(f"no matches in {len(files)} transcripts")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--download", action="store_true", help="download missing default models")
    r = sub.add_parser("run")
    r.add_argument("paths", nargs="+", type=Path)
    r.add_argument("--out", type=Path, help="mirror outputs under this directory instead of next to sources")
    r.add_argument("--lang", default="auto", help="spoken language code, e.g. ru; default auto-detect")
    r.add_argument("--force", action="store_true", help="re-transcribe even when outputs are current")
    r.add_argument("--model", type=Path, help="path to another ggml Whisper model")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("paths", nargs="+", type=Path)
    s.add_argument("--max", type=int, default=50)
    a = ap.parse_args(argv)
    if a.cmd == "check":
        return check(a.download)
    if a.cmd == "run":
        return run(a.paths, a.out, a.lang, a.force, a.model)
    return search(a.query, a.paths, a.max)


if __name__ == "__main__":
    sys.exit(main())
