from __future__ import annotations

import pathlib
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = SKILL_ROOT / "SKILL.md"
EXECUTION = SKILL_ROOT / "references" / "execution-mode.md"
ARCHITECTURE_GATE = SKILL_ROOT / "references" / "architecture-decision-gate.md"
GROUNDING = SKILL_ROOT / "references" / "grounding.md"
JUDGE = SKILL_ROOT / "references" / "judge.md"
AUTOMATIC_JUDGE = SKILL_ROOT / "references" / "automatic-judge.md"
RUNTIME = SKILL_ROOT / "references" / "runtime.md"
AUTO_MODE = SKILL_ROOT / "references" / "auto-mode.md"
PROMPT_MODE = SKILL_ROOT / "references" / "prompt-mode.md"


class CtoRoutingContractTests(unittest.TestCase):
    def test_settled_implementation_does_not_select_cto_delivery(self):
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        execution = " ".join(EXECUTION.read_text(encoding="utf-8").split())

        self.assertIn(
            "Do not use merely because implementation is multi-step or uses "
            "subagents",
            skill,
        )
        self.assertIn(
            "A settled plan, multi-step implementation, or subagent use alone "
            "belongs to the applicable implementation skill",
            execution,
        )
        self.assertIn("lead such an outcome", execution)
        self.assertNotIn("asks the CTO to lead it", execution)
        self.assertIn("route it through `ce-work`", execution)

    def test_subagent_choice_requires_a_material_context_benefit(self):
        execution = " ".join(EXECUTION.read_text(encoding="utf-8").split())

        self.assertIn("separate context creates a material benefit", execution)
        self.assertIn("independent evidence", execution)
        self.assertIn("parallel work", execution)
        self.assertIn("isolated ownership", execution)
        self.assertIn("adversarial review", execution)
        self.assertNotIn(
            "when the unit can be understood from repository sources", execution
        )

    def test_architecture_challenge_can_use_an_internal_subagent(self):
        contract = " ".join(
            ARCHITECTURE_GATE.read_text(encoding="utf-8").split()
        )

        self.assertIn("fresh internal subagent", contract)
        self.assertIn("whose job is to disprove the proposed direction", contract)
        self.assertIn("If the user explicitly invokes `x9-idea-critic`", contract)

    def test_grounding_is_fail_closed_until_user_confirmation(self):
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        execution = " ".join(EXECUTION.read_text(encoding="utf-8").split())
        grounding = " ".join(GROUNDING.read_text(encoding="utf-8").split())

        self.assertIn("$x9-cto ground", RUNTIME.read_text(encoding="utf-8"))
        self.assertIn("/x9-cto ground", RUNTIME.read_text(encoding="utf-8"))
        self.assertIn(
            "| OpenCode | — | — | `/x9-cto ground` | `/x9-cto auto` | `/x9-cto prompt` |",
            RUNTIME.read_text(encoding="utf-8"),
        )
        self.assertIn("Grounding takes precedence over autonomous delivery", skill)
        self.assertIn("one top-level `first_user_path`", execution)
        self.assertIn("scope discipline does not require a new dispatch-enforcement subsystem", execution)
        self.assertIn("controls must be effective before the dependent action", execution)
        self.assertIn("it owns the freeze and the user-controlled resumption", execution)
        self.assertNotIn("Grounding never resumes broad mutation in the same turn", execution)
        self.assertIn("Wait for explicit user confirmation", grounding)

    def test_autonomous_ce_run_asks_once_then_parks(self):
        skill = SKILL.read_text(encoding="utf-8")
        auto = " ".join(AUTO_MODE.read_text(encoding="utf-8").split())

        self.assertIn("| Codex | `$x9-cto judge` | `$x9-cto auto-judge` | `$x9-cto ground` | `$x9-cto auto` |", RUNTIME.read_text(encoding="utf-8"))
        self.assertIn("matched as a whole token: `auto-judge` is a different mode", auto)
        self.assertIn("Ask them together", auto)
        self.assertIn("no blocking question tool is used until the report", auto)
        self.assertIn("never record them as `accepted`", auto)
        self.assertIn("park the dependent item", auto)
        self.assertIn("Applicable repository policy owns overrides", auto)
        self.assertIn("do not invent a registry", auto)

    def test_low_level_primitive_cannot_validate_its_own_control_plane(self):
        contract = " ".join(
            ARCHITECTURE_GATE.read_text(encoding="utf-8").split()
        )

        self.assertIn("product-level ownership map", contract)
        self.assertIn("applicable maintained complete products", contract)
        self.assertIn("none meets a named mandatory requirement", contract)
        self.assertIn("Prior investment in the custom direction is not supporting evidence", contract)

    def test_judge_prompt_exists_only_for_a_focused_continuation(self):
        contract = " ".join(JUDGE.read_text(encoding="utf-8").split())
        automatic = " ".join(AUTOMATIC_JUDGE.read_text(encoding="utf-8").split())

        self.assertIn("only for a focused continuation", contract)
        self.assertIn("For `accept and close`, stop after the explanation", contract)
        self.assertIn("needs no synthetic follow-up", contract)
        self.assertNotIn("Do not reopen accepted decisions", contract)
        self.assertIn("Without an explicit user request to edit", contract)
        self.assertIn("follow its adaptive response contract", automatic)
        self.assertNotIn("return the existing two blocks", automatic)

    def test_prompt_mode_owns_every_handoff_prompt(self):
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        judge = " ".join(JUDGE.read_text(encoding="utf-8").split())
        prompt = " ".join(PROMPT_MODE.read_text(encoding="utf-8").split())

        self.assertIn("`$x9-cto prompt`", RUNTIME.read_text(encoding="utf-8"))
        self.assertIn("[references/prompt-mode.md](references/prompt-mode.md)", skill)
        self.assertIn("(references/prompt-mode.md#shared-prompt-rules)", skill)
        self.assertIn("(prompt-mode.md#shared-prompt-rules)", judge)

    def test_automatic_judge_honors_repository_document_owner(self):
        automatic = " ".join(AUTOMATIC_JUDGE.read_text(encoding="utf-8").split())

        self.assertIn("repository-mandated document owner", automatic)
        self.assertIn("such as `x9-okf-docs`", automatic)
        self.assertIn("does not expand this mode's write set", automatic)
        self.assertIn("repository-mandated checks", automatic)
        self.assertNotIn("cr-reviewed-plan", automatic)

    def test_integration_check_does_not_assume_submodules(self):
        execution = " ".join(EXECUTION.read_text(encoding="utf-8").split())

        self.assertIn("inspect the actual diff and current working trees", execution)
        self.assertNotIn("submodule", execution.lower())



if __name__ == "__main__":
    unittest.main()
