#!/usr/bin/env python3
"""Regression tests for byte-exact shared-core extraction."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from check_globals import extract


START = b"<!-- BEGIN SHARED PERSONAL CORE -->"
END = b"<!-- END SHARED PERSONAL CORE -->"
SKILL_FILE = Path(__file__).resolve().parent.parent / "SKILL.md"


class ExtractTests(unittest.TestCase):
    def write(self, directory: str, name: str, data: bytes) -> Path:
        path = Path(directory) / name
        path.write_bytes(data)
        return path

    def test_preserves_line_endings(self):
        with TemporaryDirectory() as directory:
            lf = self.write(directory, "lf.md", START + b"\nrule\n" + END)
            crlf = self.write(directory, "crlf.md", START + b"\r\nrule\r\n" + END)
            self.assertNotEqual(extract(lf), extract(crlf))

    def test_rejects_duplicate_marker_pairs(self):
        with TemporaryDirectory() as directory:
            path = self.write(directory, "duplicate.md", START + END + START + END)
            with self.assertRaises(ValueError):
                extract(path)


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL_FILE.read_text(encoding="utf-8")

    def test_review_is_report_first_and_approval_continues(self):
        self.assertIn("For an inspection-only request, the first pass is report-only", self.skill)
        self.assertIn("An explicit request to fix or update the prompt authorizes", self.skill)
        self.assertIn("without asking for the same permission again", self.skill)
        self.assertIn("After the user explicitly approves", self.skill)
        self.assertIn("without requesting another approval", self.skill)

    def test_review_explains_changes_before_complete_diff(self):
        self.assertIn("Why these changes help", self.skill)
        self.assertIn("lead with the practical improvement", self.skill)
        self.assertIn("smallest complete proposed diff", self.skill)
        self.assertIn("actual diff, changed-file summary", self.skill)

    def test_skill_creator_can_load_subordinate_rubric(self):
        self.assertIn("primary workflow for", self.skill)
        self.assertIn("subordinate instruction-quality rubric", self.skill)

    def test_installed_skills_use_names_not_machine_paths(self):
        self.assertIn("Name an installed skill by its discoverable name", self.skill)
        self.assertIn("never by a machine-specific `SKILL.md` path", self.skill)
        self.assertIn("use a project-relative path and say why", self.skill)
        self.assertIn("when the target runtime loads it automatically", self.skill)

    def test_global_contract_includes_every_harness(self):
        self.assertIn("`~/.config/opencode/AGENTS.md`", self.skill)
        self.assertIn("`~/.claude/CLAUDE.md`", self.skill)
        self.assertIn("`~/.codex/AGENTS.md`", self.skill)
        self.assertIn("`~/.pi/agent/AGENTS.md`, if it exists", self.skill)
        self.assertIn("byte-identical in every file", self.skill)


if __name__ == "__main__":
    unittest.main()
