from __future__ import annotations

import pathlib
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
EXECUTION = SKILL_ROOT / "references" / "execution-mode.md"
QUALIFICATION = SKILL_ROOT / "tests" / "startup_delivery_qualification.md"


class OperatingGuardrailContractTests(unittest.TestCase):
    def setUp(self):
        self.execution = " ".join(EXECUTION.read_text(encoding="utf-8").split())
        self.qualification = " ".join(
            QUALIFICATION.read_text(encoding="utf-8").split()
        )

    def test_one_user_outcome_front_owns_parallel_dispatch(self):
        self.assertIn("one active user-outcome front", self.execution)
        self.assertIn("moves its nearest acceptance barrier", self.execution)
        self.assertIn("demonstrably independent preparation", self.execution)
        self.assertIn(
            "one capacity slot for integration and urgent continuation",
            self.execution,
        )
        self.assertIn("creates no tracker field or parallel status record", self.execution)

    def test_costly_direction_preregisters_its_stop_condition(self):
        self.assertIn(
            "Before an expensive or hard-to-reverse direction begins",
            self.execution,
        )
        self.assertIn("direction-killing result", self.execution)
        self.assertIn("bounded experiment budget", self.execution)
        self.assertIn("one named new fact changes the prior conclusion", self.execution)
        self.assertIn("do not invent a time estimate", self.execution)

    def test_stop_conditions_use_defined_terms(self):
        self.assertIn("The path is `PROVEN` only when", self.execution)
        self.assertIn("the only delivery budget", self.execution)
        self.assertNotIn("checkpoint budget", self.execution)
        self.assertNotIn("structured `next_action`", self.execution)

    def test_owner_progress_projects_the_nearest_barrier(self):
        self.assertIn("A repository-specific status integration", self.execution)
        for field in (
            "nearest observable acceptance barrier",
            "current state",
            "last material change",
            "one action capable of changing that barrier",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.execution)
        self.assertIn("Activity is context, not progress", self.execution)

    def test_failed_work_compiles_to_a_bounded_continuation(self):
        for field in (
            "exact unproved gap",
            "already accepted evidence",
            "current source fingerprint",
            "allowed change surface",
            "required evidence, input, or method delta",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.execution)
        self.assertIn("The owner does not relay this technical context", self.execution)

    def test_large_dispatch_checks_only_three_contract_seams(self):
        for seam in (
            "plan against acceptance",
            "decision against authority",
            "evidence against claim",
        ):
            with self.subTest(seam=seam):
                self.assertIn(seam, self.execution)
        self.assertIn("creates no separate checklist or durable status", self.execution)

    def test_risky_acceptance_can_disprove_a_false_pass(self):
        self.assertIn("one safe disposable negative control", self.execution)
        self.assertIn("must change `pass` to `fail` or `NOT_PROVEN`", self.execution)
        self.assertIn("may inherit", self.execution)
        self.assertIn("must prove again", self.execution)
        self.assertIn("Do not impose this on every acceptance row", self.execution)

    def test_closeout_removes_only_scope_created_proof_helpers(self):
        self.assertIn("proof-support artifact created by this outcome", self.execution)
        self.assertIn("recurring acceptance, safety, or diagnosis", self.execution)
        self.assertIn("remove it before final acceptance", self.execution)
        self.assertIn(
            "Never delete historical evidence or unrelated user work",
            self.execution,
        )

    def test_behavioral_scenarios_cover_all_seven_guardrails(self):
        for scenario in (
            "Pre-registered stop condition",
            "Nearest-barrier owner update",
            "Single user-outcome front",
            "False-pass negative control",
            "Compiled continuation",
            "Three-seam preflight",
            "Proof-helper deletion review",
        ):
            with self.subTest(scenario=scenario):
                self.assertIn(scenario, self.qualification)


if __name__ == "__main__":
    unittest.main()
