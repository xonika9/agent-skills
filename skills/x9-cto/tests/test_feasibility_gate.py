import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
EXECUTION = ROOT / "references" / "execution-mode.md"
GATE = ROOT / "references" / "feasibility-gate.md"


class FeasibilityAdmissionContractTests(unittest.TestCase):
    def test_cto_uses_direct_evidence_without_legacy_policy(self):
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        execution = EXECUTION.read_text(encoding="utf-8")
        gate = GATE.read_text(encoding="utf-8")

        self.assertIn("[feasibility admission](references/feasibility-gate.md)", skill)
        self.assertIn("[feasibility admission](feasibility-gate.md)", execution)
        self.assertIn("records that evidence directly", skill)
        for forbidden in ("Work" " Contract", "v18_" "policy", "preplanning_feasibility_probe"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, gate)
                self.assertNotIn(forbidden, execution)

    def test_evidence_requires_the_product_artifact_and_matching_boundary(self):
        gate = " ".join(GATE.read_text(encoding="utf-8").split())
        self.assertIn("same product-path artifact that will perform the behavior", gate)
        self.assertIn("same load-bearing protocol and target boundary", gate)
        self.assertIn("A CLI, mock, local substitute, different client, or standalone library demo", gate)
        self.assertIn("helper process, IPC contract, packaging change, privilege transition", gate)

    def test_missing_evidence_admits_only_a_bounded_experiment(self):
        gate = " ".join(GATE.read_text(encoding="utf-8").split())
        self.assertIn("`EXPERIMENT_ONLY —", gate)
        self.assertIn("only the named bounded experiment", gate)
        self.assertIn("smallest path-killing use of the actual product artifact", gate)
        self.assertIn("with exact readback and cleanup", gate)

    def test_reuse_challenge_is_a_decision_input(self):
        gate = " ".join(GATE.read_text(encoding="utf-8").split())
        self.assertIn("compare maintained candidates with the custom path", gate)
        self.assertIn("cheapest local falsifier", gate)
        self.assertIn("remains `NOT_PROVEN` rather than selected", gate)
        self.assertIn("not a separate task lifecycle", gate)
        self.assertIn("Record the result as `reuse_decision`", gate)


if __name__ == "__main__":
    unittest.main()
