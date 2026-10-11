#!/usr/bin/env python3
"""Regression tests for apply_plan.py."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_plan  # noqa: E402


class ApplyPlanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(os.path.realpath(self.tmp.name))
        self.vault = root / "vault"
        self.outside = root / "other"
        self.vault.mkdir()
        (self.outside / "Сценарии").mkdir(parents=True)
        (self.outside / "Сценарии" / "кофе.md").write_text("сценарий", encoding="utf-8")
        (self.outside / "Сценарии" / "вложено").mkdir()
        (self.outside / "Сценарии" / "вложено" / "заметка.txt").write_text("x", encoding="utf-8")
        (self.vault / "старое.md").write_text("старая заметка", encoding="utf-8")
        self.manifest_path = root / "manifest.json"

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = apply_plan.main([str(a) for a in args])
        return code, json.loads(out.getvalue())

    def manifest(self, operations):
        self.manifest_path.write_text(
            json.dumps({"vault": str(self.vault), "operations": operations}, ensure_ascii=False),
            encoding="utf-8",
        )
        return self.manifest_path

    def standard_ops(self):
        return [
            {"op": "mkdir", "path": "Темы/Видеоблог"},
            {"op": "copy", "from": str(self.outside / "Сценарии"), "to": "Темы/Видеоблог/Сценарии"},
            {"op": "move", "from": "старое.md", "to": "Темы/Видеоблог/старое.md"},
            {"op": "symlink", "target": "/Volumes/Missing/Проекты", "path": "Темы/Видеоблог/Проекты"},
        ]

    def test_dry_run_changes_nothing(self):
        code, result = self.run_main(self.manifest(self.standard_ops()))
        self.assertEqual(code, 0)
        self.assertEqual(len(result["would_apply"]), 4)
        self.assertFalse((self.vault / "Темы").exists())
        self.assertTrue((self.vault / "старое.md").exists())

    def test_apply_then_undo_restores_original_state(self):
        code, result = self.run_main(self.manifest(self.standard_ops()), "--apply")
        self.assertEqual(code, 0, result)
        area = self.vault / "Темы" / "Видеоблог"
        self.assertEqual((area / "Сценарии" / "кофе.md").read_text(encoding="utf-8"), "сценарий")
        self.assertTrue((area / "Сценарии" / "вложено" / "заметка.txt").is_file())
        self.assertFalse((self.vault / "старое.md").exists())
        self.assertTrue((area / "Проекты").is_symlink())
        self.assertTrue((self.outside / "Сценарии" / "кофе.md").exists(), "copy keeps the original")

        code, undone = self.run_main("--undo", result["journal"])
        self.assertEqual(code, 0, undone)
        self.assertFalse((self.vault / "Темы").exists())
        self.assertEqual((self.vault / "старое.md").read_text(encoding="utf-8"), "старая заметка")

    def test_move_across_devices_verifies_and_undoes(self):
        source = self.outside / "Сценарии"
        with mock.patch.object(apply_plan, "same_device", return_value=False):
            code, result = self.run_main(
                self.manifest([{"op": "move", "from": str(source), "to": "Сценарии"}]), "--apply"
            )
        self.assertEqual(code, 0, result)
        self.assertFalse(source.exists())
        self.assertTrue((self.vault / "Сценарии" / "вложено" / "заметка.txt").is_file())

        code, undone = self.run_main("--undo", result["journal"])
        self.assertEqual(code, 0, undone)
        self.assertEqual((source / "кофе.md").read_text(encoding="utf-8"), "сценарий")
        self.assertFalse((self.vault / "Сценарии").exists())

    def test_refuses_existing_destination(self):
        (self.vault / "занято.md").write_text("моё", encoding="utf-8")
        code, result = self.run_main(
            self.manifest([{"op": "move", "from": "старое.md", "to": "занято.md"}]), "--apply"
        )
        self.assertEqual(code, 1)
        self.assertIn("already exists", result["error"])
        self.assertEqual((self.vault / "занято.md").read_text(encoding="utf-8"), "моё")

    def test_refuses_destination_outside_vault(self):
        code, result = self.run_main(
            self.manifest([{"op": "copy", "from": "старое.md", "to": "../утечка.md"}]), "--apply"
        )
        self.assertEqual(code, 1)
        self.assertIn("leaves the vault", result["error"])

    def test_validation_failure_changes_nothing(self):
        ops = self.standard_ops() + [{"op": "move", "from": "нет-такого.md", "to": "x.md"}]
        code, result = self.run_main(self.manifest(ops), "--apply")
        self.assertEqual(code, 1)
        self.assertFalse((self.vault / "Темы").exists())
        self.assertFalse((self.vault / apply_plan.JOURNAL_DIR).exists())

    def test_refuses_cloud_placeholder(self):
        with mock.patch.object(apply_plan, "is_placeholder", return_value=True):
            code, result = self.run_main(
                self.manifest([{"op": "copy", "from": str(self.outside / "Сценарии"), "to": "Сценарии"}])
            )
        self.assertEqual(code, 1)
        self.assertIn("cloud placeholder", result["error"])

    def test_remove_requires_identical_copy(self):
        source = self.outside / "Сценарии"
        self.run_main(self.manifest([{"op": "copy", "from": str(source), "to": "Сценарии"}]), "--apply")
        (self.vault / "Сценарии" / "кофе.md").write_text("изменено", encoding="utf-8")
        remove = [{"op": "remove", "path": str(source), "verified_copy": "Сценарии"}]
        code, result = self.run_main(self.manifest(remove), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("differs", result["error"])
        self.assertTrue(source.exists())

        (self.vault / "Сценарии" / "кофе.md").write_text("сценарий", encoding="utf-8")
        code, result = self.run_main(self.manifest(remove), "--apply")
        self.assertEqual(code, 0, result)
        self.assertFalse(source.exists())

        code, undone = self.run_main("--undo", result["journal"])
        self.assertEqual(code, 2)
        self.assertIn("cannot be restored", undone["skipped"][0])

    def test_undo_keeps_copy_changed_after_apply(self):
        code, result = self.run_main(
            self.manifest([{"op": "copy", "from": str(self.outside / "Сценарии"), "to": "Сценарии"}]), "--apply"
        )
        (self.vault / "Сценарии" / "новое.md").write_text("добавлено позже", encoding="utf-8")
        code, undone = self.run_main("--undo", result["journal"])
        self.assertEqual(code, 2)
        self.assertTrue((self.vault / "Сценарии" / "новое.md").exists())

    def test_failed_copy_leaves_no_partial_destination(self):
        original = apply_plan.copy_tree
        calls = {"n": 0}

        def flaky(src, dst, created):
            calls["n"] += 1
            if calls["n"] == 3:
                raise OSError("disk full")
            return original(src, dst, created)

        with mock.patch.object(apply_plan, "copy_tree", side_effect=flaky):
            code, result = self.run_main(
                self.manifest([{"op": "copy", "from": str(self.outside / "Сценарии"), "to": "Сценарии"}]), "--apply"
            )
        self.assertEqual(code, 1)
        self.assertIn("undo with --undo", result["error"])
        self.assertFalse((self.vault / "Сценарии").exists())

    # Regression scenarios from the 2026-10-11 audit.

    def test_case_variant_destinations_in_one_manifest_are_refused(self):
        (self.vault / "two.md").write_text("second", encoding="utf-8")
        ops = [
            {"op": "move", "from": "старое.md", "to": "Note.md"},
            {"op": "move", "from": "two.md", "to": "note.md"},
        ]
        code, result = self.run_main(self.manifest(ops), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("already exists", result["error"])
        self.assertTrue((self.vault / "старое.md").exists())

    def test_existing_case_or_unicode_variant_is_refused(self):
        import unicodedata

        (self.vault / "Заметка.md").write_text("моё", encoding="utf-8")
        nfd = unicodedata.normalize("NFD", "й.md")
        (self.vault / nfd).write_text("нфд", encoding="utf-8")
        for target in ("заметка.md", unicodedata.normalize("NFC", "й.md")):
            code, result = self.run_main(
                self.manifest([{"op": "copy", "from": "старое.md", "to": target}]), "--apply"
            )
            self.assertEqual(code, 1, target)
            self.assertIn("already exists", result["error"])
        self.assertEqual((self.vault / "Заметка.md").read_text(encoding="utf-8"), "моё")

    def test_remove_refuses_same_object_or_dependent_copy(self):
        (self.vault / "ценное.md").write_text("ценное", encoding="utf-8")
        os.symlink(self.vault / "ценное.md", self.vault / "ссылка.md")
        for copy in ("ценное.md", "Ценное.md", "ссылка.md"):
            code, result = self.run_main(
                self.manifest([{"op": "remove", "path": "ценное.md", "verified_copy": copy}]), "--apply"
            )
            self.assertEqual(code, 1, copy)
        self.assertTrue((self.vault / "ценное.md").exists())

    def test_remove_refuses_cross_removal_and_mixed_manifest(self):
        (self.vault / "A").mkdir()
        (self.vault / "A" / "f.md").write_text("x", encoding="utf-8")
        (self.vault / "B").mkdir()
        (self.vault / "B" / "f.md").write_text("x", encoding="utf-8")
        cross = [
            {"op": "remove", "path": "A", "verified_copy": "B"},
            {"op": "remove", "path": "B", "verified_copy": "A"},
        ]
        code, result = self.run_main(self.manifest(cross), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("verified copy", result["error"])
        mixed = [{"op": "mkdir", "path": "C"}, {"op": "remove", "path": "A", "verified_copy": "B"}]
        code, result = self.run_main(self.manifest(mixed), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("manifest of their own", result["error"])
        self.assertTrue((self.vault / "A" / "f.md").exists() and (self.vault / "B" / "f.md").exists())

    def test_nothing_is_written_through_a_link(self):
        external = self.outside / "disk"
        external.mkdir()
        ops = [
            {"op": "symlink", "target": str(external), "path": "Проекты"},
            {"op": "move", "from": "старое.md", "to": "Проекты/старое.md"},
        ]
        code, result = self.run_main(self.manifest(ops), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("link", result["error"])
        os.symlink(external, self.vault / "Диск")
        (external / "проект.txt").write_text("p", encoding="utf-8")
        for ops in (
            [{"op": "mkdir", "path": "Диск/новое"}],
            [{"op": "move", "from": "Диск/проект.txt", "to": "проект.txt"}],
        ):
            code, result = self.run_main(self.manifest(ops), "--apply")
            self.assertEqual(code, 1, ops)
            self.assertIn("link", result["error"])
        self.assertEqual(sorted(p.name for p in external.iterdir()), ["проект.txt"])

    def test_interrupted_cross_device_move_is_restored(self):
        source = self.outside / "Сценарии"
        original_remove = apply_plan.remove_tree

        def half_remove(path):
            (Path(path) / "кофе.md").unlink()
            raise OSError("interrupted")

        with mock.patch.object(apply_plan, "same_device", return_value=False), \
                mock.patch.object(apply_plan, "remove_tree", side_effect=half_remove):
            code, result = self.run_main(
                self.manifest([{"op": "move", "from": str(source), "to": "Сценарии"}]), "--apply"
            )
        self.assertEqual(code, 1)
        journal = result["error"].split("--undo ")[-1]
        self.assertFalse((source / "кофе.md").exists())
        with mock.patch.object(apply_plan, "remove_tree", side_effect=original_remove):
            code, undone = self.run_main("--undo", journal)
        self.assertEqual(code, 0, undone)
        self.assertEqual((source / "кофе.md").read_text(encoding="utf-8"), "сценарий")
        self.assertFalse((self.vault / "Сценарии").exists())
        code, again = self.run_main("--undo", journal)
        self.assertEqual(code, 1)
        self.assertIn("already undone", again["error"])

    @unittest.skipUnless(sys.platform == "darwin", "Finder metadata exists on macOS only")
    def test_copy_keeps_finder_metadata(self):
        import subprocess

        note = self.outside / "Сценарии" / "кофе.md"
        subprocess.run(["xattr", "-w", "com.apple.metadata:kMDItemComment", "важно", str(note)], check=True)
        code, result = self.run_main(
            self.manifest([{"op": "copy", "from": str(note), "to": "кофе.md"}]), "--apply"
        )
        self.assertEqual(code, 0, result)
        names = subprocess.run(["xattr", str(self.vault / "кофе.md")], capture_output=True, text=True).stdout
        self.assertIn("kMDItemComment", names)

    def test_dataless_flag_marks_placeholder(self):
        from types import SimpleNamespace

        with mock.patch.object(apply_plan.os, "lstat", return_value=SimpleNamespace(st_flags=apply_plan.SF_DATALESS)):
            self.assertTrue(apply_plan.is_placeholder(Path("x")))
        with mock.patch.object(apply_plan.os, "lstat", return_value=SimpleNamespace(st_flags=0)):
            self.assertFalse(apply_plan.is_placeholder(Path("x")))


if __name__ == "__main__":
    unittest.main()
