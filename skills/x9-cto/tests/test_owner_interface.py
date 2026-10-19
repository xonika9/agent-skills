from __future__ import annotations

import pathlib
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = SKILL_ROOT / "SKILL.md"
AUTOMATIC_JUDGE = SKILL_ROOT / "references" / "automatic-judge.md"
GROUNDING = SKILL_ROOT / "references" / "grounding.md"
EXECUTION = SKILL_ROOT / "references" / "execution-mode.md"


class OwnerInterfaceContractTests(unittest.TestCase):
    def setUp(self):
        self.skill = " ".join(SKILL.read_text(encoding="utf-8").split())

    def test_technical_and_owner_decisions_are_separate(self):
        self.assertIn("The CTO owns technical assessment", self.skill)
        self.assertIn("The owner decides product behavior", self.skill)
        self.assertIn(
            "Do not ask the owner to choose between technical mechanisms",
            self.skill,
        )
        self.assertIn("Owner approval cannot turn missing evidence into proof", self.skill)

    def test_owner_brief_separates_recommendation_evidence_and_authority(self):
        for field in (
            "**Recommendation**",
            "**Evidence**",
            "**Why**",
            "**Allowed now**",
            "**Owner action**",
            "**Next**",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.skill)
        self.assertIn("A recommendation never expands existing authority", self.skill)
        self.assertIn("Concision must not hide a second independent blocker", self.skill)

    def test_exact_modes_keep_their_semantics(self):
        self.assertIn("Do not wrap the exact Automatic Judge YAML", self.skill)
        self.assertIn("A Grounding freeze still requires", self.skill)
        automatic = AUTOMATIC_JUDGE.read_text(encoding="utf-8")
        self.assertIn("Return exactly one YAML block", automatic)
        grounding = " ".join(GROUNDING.read_text(encoding="utf-8").split())
        self.assertIn("Grounding never resumes implementation in the same turn", grounding)

    def test_value_drift_is_not_presented_as_ordinary_progress(self):
        self.assertIn("delivery budget is exhausted", self.skill)
        self.assertIn("do not project ordinary progress", self.skill)
        execution = " ".join(EXECUTION.read_text(encoding="utf-8").split())
        self.assertIn("Suspend broad implementation", execution)
        self.assertIn("budget is exhausted without the milestone movement", execution)

    def test_compound_decision_support_uses_one_primary_method(self):
        self.assertIn("Use one primary method", self.skill)
        self.assertIn("use `ce-pov`", self.skill)
        self.assertIn("use `ce-bakeoff`", self.skill)
        self.assertIn("use `ce-brainstorm` with `mode:return-to-caller`", self.skill)
        self.assertIn("use `ce-ideate` only on the user's explicit request", self.skill)
        self.assertIn("does not receive a routine follow-up `ce-pov`", self.skill)


if __name__ == "__main__":
    unittest.main()
