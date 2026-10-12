#!/usr/bin/env python3
"""Regression checks for the onboarding declaration validator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


VALIDATOR = Path(__file__).with_name("validate_onboarding.py")


def run(skills_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(skills_root)],
        capture_output=True,
        text=True,
    )


def write_declaration(skills_root: Path, skill_name: str, declaration: object) -> None:
    path = skills_root / skill_name / "references" / "onboarding.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(declaration), encoding="utf-8")


def declaration(
    requirements: list[object], supported_runtimes: list[str] | None = None
) -> dict[str, object]:
    data: dict[str, object] = {"version": 1, "requirements": requirements}
    if supported_runtimes is not None:
        data["supported_runtimes"] = supported_runtimes
    return data


def command_requirement() -> dict[str, object]:
    return {
        "id": "command-line-tool",
        "runtimes": ["opencode"],
        "kind": "command",
        "level": "required",
        "needed_for": "Checking the local command line tool.",
        "check": {"type": "command-present", "command": "toolctl"},
        "guidance_id": "install-command",
    }


def expect(label: str, condition: bool, output: str = "") -> None:
    if not condition:
        raise AssertionError(f"{label}\n{output}")


def expect_invalid(
    label: str, declaration_data: object, expected_path: str
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        write_declaration(skills_root, "x9-demo", declaration_data)
        result = run(skills_root)
        expect(
            label,
            result.returncode != 0 and expected_path in result.stdout,
            result.stdout + result.stderr,
        )


def test_opaque_names_stay_out_of_diagnostics() -> None:
    opaque = "abcdefghijklmnopqrstuvwx"
    cases = []
    data = declaration([command_requirement()])
    data[opaque] = True
    cases.append((json.dumps(data), "<unsafe-field>: unknown field"))
    data = declaration([command_requirement()])
    data["requirements"][0][opaque] = {opaque: {"needed_for": "https://example.test"}}
    cases.append((json.dumps(data), "requirements[0].<unsafe-field>"))
    data = declaration([command_requirement()])
    data["requirements"][0]["check"][opaque] = True
    cases.append((json.dumps(data), "requirements[0].check.<unsafe-field>"))
    cases.append(("{" + json.dumps(opaque) + ":1," + json.dumps(opaque) + ":2}", "duplicate JSON key: <unsafe-field>"))
    for raw, expected_path in cases:
        with tempfile.TemporaryDirectory() as tmp:
            skills_root = Path(tmp) / "skills"
            path = skills_root / "x9-demo" / "references" / "onboarding.json"
            path.parent.mkdir(parents=True)
            path.write_text(raw, encoding="utf-8")
            before = path.read_bytes()
            result = run(skills_root)
            output = result.stdout + result.stderr
            expect("opaque field names do not enter diagnostics", result.returncode != 0 and opaque not in output and expected_path in result.stdout, output)
            expect("invalid declaration remains unchanged", path.read_bytes() == before)


def main() -> None:
    test_opaque_names_stay_out_of_diagnostics()
    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        companion = skills_root / "x9-companion"
        companion.mkdir(parents=True)
        no_declaration = skills_root / "x9-no-declaration"
        no_declaration.mkdir(parents=True)
        companion_requirement = {
            "id": "companion-skill",
            "runtimes": ["claude", "codex"],
            "kind": "skill",
            "level": "optional",
            "needed_for": "Optional companion integration.",
            "check": {"type": "skill-present", "target_skill": "x9-companion"},
            "guidance_id": "install-skill",
        }
        agent_alternative = {
            "id": "native-agent-route",
            "group": "delegation-route",
            "runtimes": ["claude"],
            "kind": "agent",
            "level": "required",
            "needed_for": "Delegating work through a native agent.",
            "check": {"type": "runtime-component", "component_id": "codex:codex-rescue"},
            "guidance_id": "create-agent",
        }
        command_alternative = {
            "id": "command-route",
            "group": "delegation-route",
            "runtimes": ["claude"],
            "kind": "command",
            "level": "required",
            "needed_for": "Delegating work through the command line fallback.",
            "check": {"type": "command-present", "command": "codex"},
            "guidance_id": "install-command",
        }
        write_declaration(
            skills_root,
            "x9-demo",
            declaration([command_requirement(), companion_requirement, agent_alternative, command_alternative]),
        )
        result = run(skills_root)
        expect(
            "valid declarations, multiple runtimes, optional companion, and absent declaration",
            result.returncode == 0 and "PASS: 1 declaration file(s)" in result.stdout,
            result.stdout + result.stderr,
        )
        write_declaration(
            skills_root,
            "x9-subset",
            declaration([command_requirement()], ["opencode", "codex"]),
        )
        result = run(skills_root)
        expect(
            "valid requirement runtime subset",
            result.returncode == 0 and "PASS: 2 declaration file(s)" in result.stdout,
            result.stdout + result.stderr,
        )

    cases: list[tuple[str, object, str]] = []

    def add(label: str, mutate, expected_path: str) -> None:
        data = declaration([command_requirement()])
        mutate(data)
        cases.append((label, data, expected_path))

    add("unknown top-level field", lambda data: data.update({"extra": True}), "<unsafe-field>")
    add("unknown requirement field", lambda data: data["requirements"][0].update({"extra": True}), "requirements[0].<unsafe-field>")
    add("unknown check field", lambda data: data["requirements"][0]["check"].update({"extra": True}), "requirements[0].check.<unsafe-field>")
    add("unknown version", lambda data: data.update({"version": 2}), "version")
    add("unknown supported runtime", lambda data: data.update({"supported_runtimes": ["other"]}), "supported_runtimes[0]")
    add("duplicate supported runtime", lambda data: data.update({"supported_runtimes": ["claude", "claude"]}), "supported_runtimes[1]")
    add("unknown runtime", lambda data: data["requirements"][0].update({"runtimes": ["other"]}), "requirements[0].runtimes[0]")
    add("runtime outside supported set", lambda data: data.update({"supported_runtimes": ["claude"]}), "requirements[0].runtimes[0]")
    add("unknown kind", lambda data: data["requirements"][0].update({"kind": "other"}), "requirements[0].kind")
    add("unknown level", lambda data: data["requirements"][0].update({"level": "other"}), "requirements[0].level")
    add("unknown check type", lambda data: data["requirements"][0]["check"].update({"type": "other"}), "requirements[0].check.type")
    add("unsafe component", lambda data: data["requirements"][0].update({"kind": "agent", "check": {"type": "runtime-component", "component_id": "../../other"}, "guidance_id": "create-agent"}), "requirements[0].check.component_id")
    add("unknown feature", lambda data: data["requirements"][0].update({"kind": "runtime-feature", "check": {"type": "runtime-feature", "feature_id": "other"}, "guidance_id": "enable-runtime-feature"}), "requirements[0].check.feature_id")
    add("unknown guidance", lambda data: data["requirements"][0].update({"guidance_id": "other"}), "requirements[0].guidance_id")
    add("check has wrong conditional target", lambda data: data["requirements"][0]["check"].update({"target_skill": "x9-companion"}), "requirements[0].check.target_skill")
    add("check misses conditional command", lambda data: data["requirements"][0].update({"check": {"type": "command-present"}}), "requirements[0].check.command")
    add("check misses conditional target skill", lambda data: data["requirements"][0].update({"kind": "skill", "check": {"type": "skill-present"}, "guidance_id": "install-skill"}), "requirements[0].check.target_skill")
    add("check misses conditional component", lambda data: data["requirements"][0].update({"kind": "agent", "check": {"type": "runtime-component"}, "guidance_id": "create-agent"}), "requirements[0].check.component_id")
    add("check misses conditional feature", lambda data: data["requirements"][0].update({"kind": "runtime-feature", "check": {"type": "runtime-feature"}, "guidance_id": "enable-runtime-feature"}), "requirements[0].check.feature_id")
    add("manual check has parameter", lambda data: data["requirements"][0].update({"kind": "user-action", "check": {"type": "manual", "command": "toolctl"}, "guidance_id": "complete-user-action"}), "requirements[0].check.command")
    add("kind and check do not match", lambda data: data["requirements"][0].update({"kind": "skill"}), "requirements[0].check.type")
    add("kind and guidance do not match", lambda data: data["requirements"][0].update({"guidance_id": "install-skill"}), "requirements[0].guidance_id")
    add("duplicate id", lambda data: data.update({"requirements": [command_requirement(), command_requirement()]}), "requirements[1].id")
    add("missing target skill", lambda data: data["requirements"][0].update({"kind": "skill", "check": {"type": "skill-present", "target_skill": "x9-missing"}, "guidance_id": "install-skill"}), "requirements[0].check.target_skill")
    add("top-level type", lambda data: data.update({"requirements": "wrong"}), "requirements")
    add("requirement type", lambda data: data.update({"requirements": ["wrong"]}), "requirements[0]")
    add("field type", lambda data: data["requirements"][0].update({"id": 1}), "requirements[0].id")
    add("runtime type", lambda data: data["requirements"][0].update({"runtimes": "opencode"}), "requirements[0].runtimes")
    add("check type", lambda data: data["requirements"][0].update({"check": "command-present"}), "requirements[0].check")
    add("URL", lambda data: data["requirements"][0].update({"needed_for": "https://example.test"}), "requirements[0].needed_for")
    add("absolute path", lambda data: data["requirements"][0]["check"].update({"command": "/usr/bin/toolctl"}), "requirements[0].check.command")
    add("shell syntax", lambda data: data["requirements"][0]["check"].update({"command": "toolctl|other"}), "requirements[0].check.command")
    add("control character", lambda data: data["requirements"][0].update({"needed_for": "line\nbreak"}), "requirements[0].needed_for")
    add("length", lambda data: data["requirements"][0].update({"needed_for": "a" * 161}), "requirements[0].needed_for")
    add("secret-like field", lambda data: data["requirements"][0].update({"api_key": "value"}), "requirements[0].<unsafe-field>")
    add("secret-like value", lambda data: data["requirements"][0].update({"needed_for": "token=abcdef"}), "requirements[0].needed_for")
    add("hyphenated secret token", lambda data: data["requirements"][0]["check"].update({"command": "sk-proj-abcdefgh"}), "requirements[0].check.command")
    add("identifier format", lambda data: data["requirements"][0].update({"id": "Bad_Id"}), "requirements[0].id")
    add("single member alternative group", lambda data: data["requirements"][0].update({"group": "only-route"}), "requirements[0].group")
    add("optional alternative member", lambda data: data.update({"requirements": [{**command_requirement(), "group": "route"}, {**command_requirement(), "id": "second-command", "group": "route", "level": "optional"}]}), "requirements[1].level")
    add("mismatched alternative runtimes", lambda data: data.update({"requirements": [{**command_requirement(), "group": "route"}, {**command_requirement(), "id": "second-command", "group": "route", "runtimes": ["codex"]}]}), "requirements[1].runtimes")
    add("full supported runtime list", lambda data: data.update({"supported_runtimes": ["opencode", "claude", "codex"]}), "supported_runtimes")
    add("requirement runtimes repeat supported set", lambda data: data.update({"supported_runtimes": ["opencode"]}), "requirements[0].runtimes")
    add("empty declaration without restriction", lambda data: data.update({"requirements": []}), "requirements")
    add("version check for unlisted command", lambda data: data["requirements"][0].update({"check": {"type": "command-version", "command": "toolctl", "min_version": "1.0"}}), "requirements[0].check.command")
    add("version check with malformed minimum", lambda data: data["requirements"][0].update({"check": {"type": "command-version", "command": "python3", "min_version": "3.11+"}}), "requirements[0].check.min_version")
    add("version check misses minimum", lambda data: data["requirements"][0].update({"check": {"type": "command-version", "command": "python3"}}), "requirements[0].check.min_version")
    add("version check on non-command kind", lambda data: data["requirements"][0].update({"kind": "skill", "guidance_id": "install-skill", "check": {"type": "command-version", "command": "python3", "min_version": "3.11"}}), "requirements[0].check.type")

    for label, data, expected_path in cases:
        expect_invalid(label, data, expected_path)

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        write_declaration(
            skills_root,
            "x9-demo",
            declaration([command_requirement()], ["claude"]),
        )
        result = run(skills_root)
        error_lines = [line for line in result.stdout.splitlines() if line.startswith("ERROR:")]
        expect(
            "runtime outside supported set reports one subset error",
            error_lines
            == [
                "ERROR: x9-demo/references/onboarding.json: "
                "requirements[0].runtimes[0]: runtime is not declared in supported_runtimes"
            ],
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        write_declaration(
            skills_root,
            "x9-demo",
            declaration([command_requirement()], ["claude", "other"]),
        )
        result = run(skills_root)
        error_lines = [line for line in result.stdout.splitlines() if line.startswith("ERROR:")]
        expect(
            "invalid supported runtimes suppress subset errors",
            error_lines
            == [
                "ERROR: x9-demo/references/onboarding.json: "
                "supported_runtimes[1]: unknown runtime"
            ],
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        path = skills_root / "x9-demo" / "references" / "onboarding.json"
        path.parent.mkdir(parents=True)
        path.write_text('{"version":1,"version":1,"supported_runtimes":["opencode"],"requirements":[]}', encoding="utf-8")
        result = run(skills_root)
        expect(
            "duplicate JSON key",
            result.returncode != 0 and "duplicate JSON key: version" in result.stdout,
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        outside = Path(tmp) / "outside-skill"
        outside.mkdir()
        (skills_root).mkdir()
        (skills_root / "x9-linked").symlink_to(outside, target_is_directory=True)
        result = run(skills_root)
        expect(
            "external skill symlink",
            result.returncode != 0 and "x9-linked: skill directory must not be a symbolic link" in result.stdout,
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        outside = Path(tmp) / "outside.json"
        outside.write_text(json.dumps(declaration([command_requirement()])), encoding="utf-8")
        path = skills_root / "x9-demo" / "references" / "onboarding.json"
        path.parent.mkdir(parents=True)
        path.symlink_to(outside)
        result = run(skills_root)
        expect(
            "external declaration symlink",
            result.returncode != 0 and "file must not be a symbolic link" in result.stdout,
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        path = skills_root / "x9-demo" / "references" / "onboarding.json"
        path.mkdir(parents=True)
        result = run(skills_root)
        expect(
            "declaration path is not a regular file",
            result.returncode != 0 and "must be a regular file" in result.stdout,
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        outside = Path(tmp) / "outside-skill"
        outside.mkdir()
        (skills_root / "x9-demo" / "references").mkdir(parents=True)
        (skills_root / "x9-companion").symlink_to(outside, target_is_directory=True)
        companion = command_requirement()
        companion.update({"kind": "skill", "check": {"type": "skill-present", "target_skill": "x9-companion"}, "guidance_id": "install-skill"})
        write_declaration(skills_root, "x9-demo", declaration([companion]))
        result = run(skills_root)
        expect(
            "external target skill symlink",
            result.returncode != 0 and "target skill must not be a symbolic link" in result.stdout,
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        path = skills_root / "x9-demo" / "references" / "onboarding.json"
        path.parent.mkdir(parents=True)
        nested = "[" * 2000 + "0" + "]" * 2000
        path.write_text('{"version":1,"requirements":[],"extra":' + nested + "}", encoding="utf-8")
        result = run(skills_root)
        expect(
            "excessive JSON nesting fails cleanly",
            result.returncode != 0
            and "x9-demo/references/onboarding.json:" in result.stdout
            and ("<unsafe-field>: unknown field" in result.stdout or "JSON:" in result.stdout)
            and "Traceback" not in result.stderr,
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        data = declaration([command_requirement()])
        bad_key = "outside\nUNSAFE_KEY_MARKER"
        data[bad_key] = True
        write_declaration(skills_root, "x9-demo", data)
        result = run(skills_root)
        expect(
            "unsafe field names do not enter diagnostics",
            result.returncode != 0
            and "<unsafe-field>" in result.stdout
            and "UNSAFE_KEY_MARKER" not in result.stdout,
            result.stdout + result.stderr,
        )

    with tempfile.TemporaryDirectory() as tmp:
        skills_root = Path(tmp) / "skills"
        secret_key = "sk-proj-" + "SYNTHETIC" * 3
        path = skills_root / "x9-demo" / "references" / "onboarding.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({secret_key: True}), encoding="utf-8")
        result = run(skills_root)
        expect("secret-like key is redacted", result.returncode != 0 and secret_key not in result.stdout, result.stdout + result.stderr)
        path.write_text("{" + json.dumps(secret_key) + ":1," + json.dumps(secret_key) + ":2}", encoding="utf-8")
        result = run(skills_root)
        expect("duplicate secret-like key is redacted", result.returncode != 0 and secret_key not in result.stdout and "duplicate JSON key" in result.stdout, result.stdout + result.stderr)

    valid_cases = [
        ("runtime restriction without requirements", declaration([], ["claude", "codex"])),
        ("requirement for every runtime", declaration([{key: value for key, value in command_requirement().items() if key != "runtimes"}])),
        ("minimum command version", declaration([{**command_requirement(), "check": {"type": "command-version", "command": "python3", "min_version": "3.11"}}])),
    ]
    for label, data in valid_cases:
        with tempfile.TemporaryDirectory() as tmp:
            skills_root = Path(tmp) / "skills"
            write_declaration(skills_root, "x9-demo", data)
            result = run(skills_root)
            expect(label, result.returncode == 0 and "PASS" in result.stdout, result.stdout + result.stderr)

    repository_skills = Path(__file__).resolve().parents[2]
    result = run(repository_skills)
    expect("repository skills root", result.returncode == 0, result.stdout + result.stderr)

    print("PASS: onboarding declaration validator regression scenarios")


if __name__ == "__main__":
    main()
