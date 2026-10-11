#!/usr/bin/env python3
"""Regression tests for transcripts.py. Run: python3 test_transcripts.py

End-to-end cases replace ffmpeg, ffprobe, and whisper-cli with stub scripts, so no model runs.
"""
import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transcripts as t  # noqa: E402

SRT = """1
00:00:01,000 --> 00:00:04,500
Всем привет.

2
00:01:02,250 --> 00:01:05,000
Ёлка стоит
у окна.

3
01:00:00,000 --> 01:00:02,000
Финал.
"""

STUB_FFMPEG = """#!/bin/sh
# last argument is the output wav; fail for inputs named *noaudio*
case "$*" in *noaudio*) echo "Output file does not contain any stream" >&2; exit 1;; esac
for a; do out="$a"; done
printf 'RIFF' > "$out"
"""
STUB_FFPROBE = "#!/bin/sh\necho 12.5\n"
STUB_WHISPER = """#!/bin/sh
lang=""
while [ $# -gt 0 ]; do
  case "$1" in -of) base="$2"; shift;; -l) lang="$2"; shift;; esac
  shift
done
echo "$base" >> "$X9_STUB_LOG"
if [ -n "$X9_STUB_FAIL" ]; then echo "error: unknown argument --vad" >&2; exit 3; fi
[ "$lang" = auto ] && echo "auto-detected language: ru (p = 0.99)" >&2
if [ -n "$X9_STUB_EMPTY" ]; then : > "$base.srt"; exit 0; fi
cat > "$base.srt" <<'SRT'
1
00:00:00,000 --> 00:00:02,000
Пространствус пришёл.

2
00:00:02,000 --> 00:00:04,000
Конец.
SRT
"""


def write_exec(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class Pure(unittest.TestCase):
    def test_parse_srt_joins_multiline_text_and_ignores_indexes(self):
        segs = t.parse_srt(SRT)
        self.assertEqual([s[2] for s in segs], ["Всем привет.", "Ёлка стоит у окна.", "Финал."])
        self.assertAlmostEqual(segs[1][0], 62.25)
        self.assertEqual(segs[2][0], 3600.0)

    def test_txt_has_source_header_and_hour_timestamps(self):
        txt = t.srt_to_txt(SRT, Path("/v/clip.mp4"), "ru").splitlines()
        self.assertEqual(txt[0], "# source: /v/clip.mp4")
        self.assertEqual(txt[3], "[00:01:02] Ёлка стоит у окна.")
        self.assertEqual(txt[4], "[01:00:00] Финал.")

    def test_output_base_sidecar_and_mirror(self):
        root = Path("/videos")
        src = Path("/videos/2026/trip.final.mp4")
        self.assertEqual(t.output_base(src, root, None), Path("/videos/2026/trip.final"))
        self.assertEqual(t.output_base(src, root, Path("/lib")), Path("/lib/2026/trip.final"))

    def test_search_normalizes_yo_and_matches_phrase_split_across_lines(self):
        lines = t.srt_to_txt(SRT, Path("/v/a.mp4"), "ru").splitlines()
        stamps = lambda q: [lines[i][:10] for i in t.search_lines(lines, q)]
        self.assertEqual(stamps("елка"), ["[00:01:02]"])
        self.assertEqual(stamps("привет ёлка"), ["[00:00:01]"])
        self.assertEqual(stamps("отсутствует"), [])

    def test_search_finds_inflected_forms(self):
        lines = ["[00:00:05] Мы жили в загородном доме.", "[00:00:09] Потом уехали."]
        self.assertEqual(t.search_lines(lines, "загородный дом"), [0])


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        write_exec(bin_dir / "ffmpeg", STUB_FFMPEG)
        write_exec(bin_dir / "ffprobe", STUB_FFPROBE)
        write_exec(bin_dir / "whisper-cli", STUB_WHISPER)
        models = self.tmp / "models"
        models.mkdir()
        for name, _url in t.MODELS.values():
            (models / name).write_text("stub")
        self.log = self.tmp / "calls.log"
        self.env = mock_env({
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "X9_TRANSCRIPTS_MODELS": str(models),
            "X9_STUB_LOG": str(self.log),
            "X9_WHISPER_CLI": "",
        })
        self.env.__enter__()
        self.videos = self.tmp / "videos"
        (self.videos / "day2").mkdir(parents=True)
        (self.videos / ".hidden").mkdir()
        for rel in ("a.mp4", "day2/b.mov", "day2/noaudio.mp4", ".hidden/c.mp4", "notes.txt"):
            (self.videos / rel).write_text("x")

    def tearDown(self):
        self.env.__exit__(None, None, None)

    def call(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = t.main(list(argv))
        return code, out.getvalue()

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_batch_writes_sidecars_continues_after_failure_and_resumes(self):
        code, out = self.call("run", str(self.videos), "--lang", "ru")
        summary = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual((summary["files"], summary["done"], summary["skipped"]), (3, 2, 0))
        self.assertIn("noaudio.mp4", summary["failed"][0]["file"])
        txt = (self.videos / "day2" / "b.transcript.txt").read_text()
        self.assertIn("[00:00:00] Пространствус пришёл.", txt)
        self.assertTrue((self.videos / "a.transcript.srt").exists())
        self.assertFalse((self.videos / ".hidden" / "c.transcript.txt").exists())
        self.assertEqual(len(self.calls()), 2)

        code, out = self.call("run", str(self.videos))
        summary = json.loads(out)
        self.assertEqual((summary["done"], summary["skipped"], len(summary["failed"])), (0, 2, 1))
        self.assertEqual(len(self.calls()), 2, "current outputs must not be re-transcribed")

    def test_changed_source_and_force_retranscribe(self):
        self.call("run", str(self.videos / "a.mp4"))
        future = time.time() + 5
        os.utime(self.videos / "a.mp4", (future, future))
        self.call("run", str(self.videos / "a.mp4"))
        self.call("run", str(self.videos / "a.mp4"), "--force")
        self.assertEqual(len(self.calls()), 3)

    def test_out_dir_mirrors_layout_and_reports_collisions(self):
        lib = self.tmp / "lib"
        (self.tmp / "other").mkdir()
        (self.tmp / "other" / "a.mp4").write_text("x")
        code, out = self.call("run", str(self.videos / "a.mp4"), str(self.tmp / "other" / "a.mp4"), "--out", str(lib))
        summary = json.loads(out)
        self.assertEqual((code, summary["done"], summary["status"]), (1, 1, "partial"))
        self.assertEqual(len(summary["collisions"]), 1)
        self.assertTrue((lib / "a.transcript.txt").exists())
        self.assertFalse((self.videos / "a.transcript.txt").exists())

        self.call("run", str(self.videos), "--out", str(lib))
        self.assertTrue((lib / "day2" / "b.transcript.srt").exists())

    def test_symlinked_source_gets_transcript_beside_the_link(self):
        links = self.tmp / "links"
        links.mkdir()
        (links / "alias.mp4").symlink_to(self.videos / "a.mp4")
        self.call("run", str(links))
        self.assertTrue((links / "alias.transcript.txt").exists())
        self.assertFalse((self.videos / "a.transcript.txt").exists())

    def test_case_insensitive_collision_is_reported_not_skipped(self):
        d = self.tmp / "case"
        d.mkdir()
        (d / "Clip.MP4").write_text("x")
        (d / "clip.mov").write_text("x")
        code, out = self.call("run", str(d))
        summary = json.loads(out)
        self.assertEqual((code, summary["done"], summary["skipped"]), (1, 1, 0))
        self.assertEqual(len(summary["collisions"]), 1)

    def test_explicit_file_with_unlisted_extension_is_transcribed(self):
        f = self.tmp / "memo.xyz"
        f.write_text("x")
        code, out = self.call("run", str(f), "--lang", "auto")
        self.assertEqual((code, json.loads(out)["done"]), (0, 1))
        self.assertIn("# language: ru", (self.tmp / "memo.transcript.txt").read_text())

    def test_folder_without_media_is_an_error(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        code, out = self.call("run", str(empty))
        self.assertEqual((code, json.loads(out)["status"]), (2, "no_media"))

    def test_unwritable_output_fails_before_recognition(self):
        ro = self.tmp / "ro"
        ro.mkdir()
        (ro / "a.mp4").write_text("x")
        ro.chmod(0o555)
        try:
            code, out = self.call("run", str(ro))
        finally:
            ro.chmod(0o755)
        self.assertEqual(code, 1)
        self.assertIn("not writable", json.loads(out)["failed"][0]["error"])
        self.assertEqual(self.calls(), [])

    def test_repeated_recognizer_error_aborts_batch(self):
        d = self.tmp / "three"
        d.mkdir()
        for name in ("1.mp4", "2.mp4", "3.mp4"):
            (d / name).write_text("x")
        with mock_env({"X9_STUB_FAIL": "1"}):
            code, out = self.call("run", str(d))
        summary = json.loads(out)
        self.assertEqual((code, summary["status"], len(summary["failed"])), (1, "aborted", 2))
        self.assertEqual(len(summary["not_attempted"]), 1)
        self.assertEqual(len(self.calls()), 2)

    def test_no_speech_is_reported(self):
        with mock_env({"X9_STUB_EMPTY": "1"}):
            code, out = self.call("run", str(self.videos / "a.mp4"))
        summary = json.loads(out)
        self.assertEqual((code, summary["done"], len(summary["no_speech"])), (0, 1, 1))

    def test_file_inside_folder_argument_keeps_folder_layout(self):
        lib = self.tmp / "lib"
        self.call("run", str(self.videos / "day2" / "b.mov"), str(self.videos), "--out", str(lib))
        self.assertTrue((lib / "day2" / "b.transcript.txt").exists())
        self.assertFalse((lib / "b.transcript.txt").exists())

    def test_search_without_transcripts_is_an_error(self):
        code, _out = self.call("search", "что-то", str(self.videos))
        self.assertEqual(code, 2)
        code, _out = self.call("search", "что-то", str(self.tmp / "missing"))
        self.assertEqual(code, 2)

    def test_missing_dependency_stops_before_any_work(self):
        with mock_env({"X9_TRANSCRIPTS_MODELS": str(self.tmp / "nomodels")}):
            code, out = self.call("run", str(self.videos))
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["status"], "setup_required")
        self.assertEqual(self.calls(), [])

    def test_search_prints_source_and_timestamp(self):
        self.call("run", str(self.videos / "a.mp4"))
        code, out = self.call("search", "пространствус", str(self.videos))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), f"{self.videos / 'a.mp4'}\t[00:00:00] Пространствус пришёл.")


@contextlib.contextmanager
def mock_env(values):
    old = {k: os.environ.get(k) for k in values}
    os.environ.update({k: v for k, v in values.items() if v})
    for k, v in values.items():
        if not v:
            os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


if __name__ == "__main__":
    unittest.main(verbosity=1)
