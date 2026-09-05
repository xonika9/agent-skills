#!/usr/bin/env python3
"""Regression tests for byte-exact shared-core extraction."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from check_globals import extract


START = b"<!-- BEGIN SHARED PERSONAL CORE -->"
END = b"<!-- END SHARED PERSONAL CORE -->"
SKILL_FILE = Path(__file__).parent.parent / "SKILL.md"
CONTEXT_SKILL_FILE = SKILL_FILE.parent.parent / "x9-context-files-generator" / "SKILL.md"
PUBLISHED_GLOBAL_FILES = (
    SKILL_FILE.parents[2] / "global-files/opencode/AGENTS.md",
    SKILL_FILE.parents[2] / "global-files/claude/CLAUDE.md",
    SKILL_FILE.parents[2] / "global-files/codex/AGENTS.md",
)
WORKER_BRIEF_RULE = b"Include the goal, non-derivable context, scope and authority, required evidence, and expected output"
SCOPE_FIDELITY_RULE = b"Avoid unrequested features, abstractions, and adjacent cleanup."
SPECIALIST_OWNER_RULE = b"preserve load-bearing source wording and the active skill's specialist prompt and output contract"
WORKER_LANGUAGE_RULE = b"Write worker briefs in English"
USER_LANGUAGE_RULE = b"user-facing results in the user's language."


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
        cls.context_skill = CONTEXT_SKILL_FILE.read_text(encoding="utf-8")

    def test_review_is_report_first_and_approval_continues(self):
        self.assertIn("The first pass is report-only", self.skill)
        self.assertIn("After the user explicitly approves", self.skill)
        self.assertIn("without requesting another approval", self.skill)

    def test_review_explains_changes_before_complete_diff(self):
        self.assertIn("Why these changes help", self.skill)
        self.assertIn("no more than two short sentences", self.skill)
        self.assertIn("smallest complete proposed diff", self.skill)
        self.assertIn("actual diff, changed-file summary", self.skill)

    def test_skill_creator_can_load_subordinate_rubric(self):
        self.assertIn("primary workflow for", self.skill)
        self.assertIn("subordinate instruction-quality rubric", self.skill)

    def test_all_published_shared_cores_define_worker_brief_quality(self):
        shared_cores = [extract(path) for path in PUBLISHED_GLOBAL_FILES]
        self.assertTrue(all(core == shared_cores[0] for core in shared_cores[1:]))
        for path, shared_core in zip(PUBLISHED_GLOBAL_FILES, shared_cores):
            self.assertIn(WORKER_BRIEF_RULE, shared_core, path)
            self.assertIn(SCOPE_FIDELITY_RULE, shared_core, path)
            self.assertIn(SPECIALIST_OWNER_RULE, shared_core, path)
            self.assertIn(WORKER_LANGUAGE_RULE, shared_core, path)
            self.assertIn(USER_LANGUAGE_RULE, shared_core, path)

    def test_installed_skills_use_names_not_machine_paths(self):
        self.assertIn("Name an installed skill by its discoverable name", self.skill)
        self.assertIn("never by a machine-specific `SKILL.md` path", self.skill)
        self.assertIn("use a project-relative path and say why", self.skill)
        self.assertIn("when the target runtime loads it automatically", self.skill)

    def test_shared_policy_defaults_to_primary_execution_with_scoped_authority(self):
        for path in PUBLISHED_GLOBAL_FILES:
            core = extract(path)
            self.assertIn(b"Do substantive work in the primary session by default.", core, path)
            self.assertIn(b"nested delegation is explicitly required", core, path)
            self.assertIn(b"Continue already-authorized fixes, reruns, and explicitly scoped external actions", core, path)
            self.assertIn(b"newly discovered risk materially changes the agreed scope", core, path)
            self.assertIn(b"Intermediate checks do not replace the requested end-to-end result", core, path)
            self.assertNotIn(b"configured lower-cost subagents execute", core, path)

    def test_codex_and_opencode_inherit_models_for_substantive_delegation(self):
        opencode = PUBLISHED_GLOBAL_FILES[0].read_text(encoding="utf-8")
        codex = PUBLISHED_GLOBAL_FILES[2].read_text(encoding="utf-8")
        self.assertIn("Use `inherit` for substantive delegated work", opencode)
        self.assertIn("Inherit the primary session's model and reasoning effort", codex)
        for text in (opencode, codex):
            self.assertIn("only for bounded search and fact extraction", text)
            self.assertIn("not complex diagnosis, implementation, or final acceptance", text)
        self.assertIn("stop or archive them only when that cleanup is explicitly authorized", codex)

    def test_context_creator_uses_one_bounded_instruction_rubric(self):
        self.assertIn("load and apply `x9-agent-instructions`", self.context_skill)
        self.assertIn("subordinate instruction-quality rubric", self.context_skill)
        self.assertIn("single report and approval gate", self.context_skill)
        self.assertIn("instruction rubric as `degraded`", self.context_skill)
        self.assertIn("README-only work records it as `not applicable`", self.context_skill)

    def test_global_contract_includes_all_three_harnesses(self):
        self.assertIn("`~/.config/opencode/AGENTS.md`", self.skill)
        self.assertIn("`~/.claude/CLAUDE.md`", self.skill)
        self.assertIn("`~/.codex/AGENTS.md`", self.skill)
        self.assertIn("byte-identical in all three", self.skill)


if __name__ == "__main__":
    unittest.main()
