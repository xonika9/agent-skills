from __future__ import annotations

import pathlib
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = SKILL_ROOT / "SKILL.md"
AUTOMATIC_JUDGE = SKILL_ROOT / "references" / "automatic-judge.md"
GROUNDING = SKILL_ROOT / "references" / "grounding.md"
EXECUTION = SKILL_ROOT / "references" / "execution-mode.md"
OWNER_BRIEF = SKILL_ROOT / "references" / "owner-brief.md"
DECISION_SUPPORT = SKILL_ROOT / "references" / "decision-support.md"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


class OwnerInterfaceContractTests(unittest.TestCase):
    def setUp(self):
        self.skill = flat(SKILL)
        self.brief = flat(OWNER_BRIEF)
        self.support = flat(DECISION_SUPPORT)

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
                self.assertIn(field, self.brief)
        self.assertIn("A recommendation never expands existing authority", self.brief)
        self.assertIn("Concision must not hide a second independent blocker", self.brief)
        self.assertIn("ask for it now instead of deferring it, as one question that already proposes its ceiling", self.brief)
        self.assertIn("Quick questions, Brainstorm, Hands-on help, and progress updates do not use it", self.brief)
        self.assertIn("[owner brief](references/owner-brief.md)", self.skill)
        for reference in ("judge.md", "grounding.md", "execution-mode.md"):
            with self.subTest(reference=reference):
                self.assertIn("[owner brief](owner-brief.md)", flat(SKILL_ROOT / "references" / reference))

    def test_exact_modes_keep_their_semantics(self):
        self.assertIn("Do not wrap the exact Automatic Judge YAML", self.brief)
        self.assertIn("A Grounding freeze still requires", self.brief)
        automatic = AUTOMATIC_JUDGE.read_text(encoding="utf-8")
        self.assertIn("Return exactly one YAML block", automatic)
        grounding = " ".join(GROUNDING.read_text(encoding="utf-8").split())
        self.assertIn("Grounding never resumes implementation in the same turn", grounding)

    def test_value_drift_is_not_presented_as_ordinary_progress(self):
        self.assertIn("delivery budget is exhausted", self.brief)
        self.assertIn("do not project ordinary progress", self.brief)
        execution = " ".join(EXECUTION.read_text(encoding="utf-8").split())
        self.assertIn("Suspend broad implementation", execution)
        self.assertIn("budget is exhausted without the milestone movement", execution)

    def test_compound_decision_support_uses_one_primary_method(self):
        self.assertIn("[decision support](references/decision-support.md)", self.skill)
        self.assertIn("Use one primary method", self.support)
        self.assertIn("use `ce-pov`", self.support)
        self.assertIn("use `ce-bakeoff`", self.support)
        self.assertIn("use `ce-brainstorm` with `mode:return-to-caller`", self.support)
        self.assertIn("use `ce-ideate` only on the user's explicit request", self.support)
        self.assertIn("does not receive a routine follow-up `ce-pov`", self.support)


if __name__ == "__main__":
    unittest.main()
