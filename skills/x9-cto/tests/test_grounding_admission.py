from __future__ import annotations

import pathlib
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = SKILL_ROOT / "SKILL.md"
ARCHITECTURE_GATE = SKILL_ROOT / "references" / "architecture-decision-gate.md"
GROUNDING = SKILL_ROOT / "references" / "grounding.md"
EXECUTION = SKILL_ROOT / "references" / "execution-mode.md"


class GroundingAdmissionContractTests(unittest.TestCase):
    def setUp(self):
        self.skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.architecture_gate = " ".join(
            ARCHITECTURE_GATE.read_text(encoding="utf-8").split()
        )
        self.grounding = " ".join(GROUNDING.read_text(encoding="utf-8").split())
        self.execution = " ".join(EXECUTION.read_text(encoding="utf-8").split())

    def test_day_zero_incus_platform_direction_uses_canonical_gate(self):
        self.assertIn("new platform or continuing operating cost", self.skill)
        self.assertIn("remains the sole owner of the full decision packet", self.skill)
        self.assertIn("invoke and present the canonical decision packet", self.grounding)
        self.assertIn("without naming the proposed mechanism", self.architecture_gate)
        self.assertIn("Open source, vendor maintenance, or prior investment", self.architecture_gate)
        self.assertIn("operation, upgrades, recovery, observability, exit", self.architecture_gate)
        self.assertIn("mandatory user step", self.architecture_gate)

    def test_small_near_miss_stays_lightweight(self):
        self.assertIn("small change that stays within an accepted surface", self.grounding)
        self.assertIn("not elevated to a full architecture packet", self.grounding)
        self.assertIn("ordinary request to compare or improve options remains", self.skill)
        self.assertIn("unless it explicitly requests this fail-closed challenge", self.skill)

    def test_active_delivery_drift_freezes_until_the_user_resumes(self):
        self.assertIn("active-delivery drift control", self.grounding)
        self.assertIn("Choose the context from the actual delivery state", self.grounding)
        self.assertIn("freeze it first", self.grounding)
        self.assertIn("stop new implementation dispatches and broad mutation", self.grounding)
        self.assertIn("only the user can resume work", self.grounding)
        self.assertIn("including `AWAITING_CRITIQUE`", self.grounding)

    def test_independent_critic_boundary_is_not_x9_idea_critic_by_default(self):
        self.assertIn("fresh internal subagent", self.architecture_gate)
        self.assertIn("If the user explicitly invokes `x9-idea-critic`", self.architecture_gate)
        self.assertIn("supplies generic sealed-packet criticism only", self.architecture_gate)
        self.assertIn("cannot grant authority or resume work", self.architecture_gate)
        self.assertIn("cannot supply the dissent", self.architecture_gate)
        self.assertIn("unresolved critique that invalidates", self.architecture_gate)

    def test_blocking_unknown_and_weak_reuse_comparison_cannot_admit_implementation(self):
        self.assertIn("could invalidate the selected class of solution blocks", self.architecture_gate)
        self.assertIn("Simpler credible alternatives must be rejected", self.architecture_gate)
        self.assertIn("can disprove its necessity", self.architecture_gate)

    def test_minimal_ownership_ladder_stops_before_custom_infrastructure(self):
        rungs = [
            "do not build or defer the capability",
            "use an existing project capability",
            "use the standard library or native platform",
            "use an already-installed dependency",
            "consume a maintained component through a thin integration",
            "add the smallest bounded custom component",
            "own a custom infrastructure subsystem",
        ]
        positions = [self.architecture_gate.index(rung) for rung in rungs]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("order of proof, not an automatic ranking", self.architecture_gate)

    def test_deliberate_simplification_has_a_ceiling_and_revisit_signal(self):
        self.assertIn("deliberately accepts a known ceiling", self.architecture_gate)
        self.assertIn("observable signal that requires reconsideration", self.architecture_gate)
        self.assertIn("next credible option", self.architecture_gate)
        self.assertIn("does not create a code-comment convention", self.architecture_gate)
        self.assertIn("Do not prebuild its fallback", self.execution)
        self.assertIn("existing strategy reassessment", self.execution)

    def test_preimplementation_output_is_owner_readable(self):
        self.assertIn("owner-readable view", self.grounding)
        self.assertIn("mechanism-free user action and observed problem", self.grounding)
        self.assertIn("what the project would operate continuously", self.grounding)

    def test_bounded_experiment_returns_through_grounding_without_admission(self):
        self.assertIn("exactly one named bounded reversible experiment", self.architecture_gate)
        self.assertIn("result returns through Grounding", self.architecture_gate)
        self.assertIn("never automatically admits implementation", self.architecture_gate)
        self.assertNotIn("cannot automatically become implementation admission", self.grounding)


if __name__ == "__main__":
    unittest.main()
