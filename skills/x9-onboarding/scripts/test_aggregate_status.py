#!/usr/bin/env python3
"""Regression checks for onboarding status aggregation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("aggregate_status.py")

READY = {"coverage": "COMPLETE", "readiness": "READY"}
SETUP = {"coverage": "COMPLETE", "readiness": "NEEDS_SETUP"}
RESTART = {"coverage": "COMPLETE", "readiness": "PENDING_RESTART"}
BLOCKED = {"coverage": "PARTIAL", "readiness": "BLOCKED"}
USER = {"coverage": "EXPLICIT", "readiness": "USER_ACTION"}


def requirement(identifier: str, level: str = "required", group: str | None = None,
                runtimes: list[str] | None = None) -> dict[str, object]:
    data: dict[str, object] = {
        "id": identifier,
        "kind": "command",
        "level": level,
        "needed_for": "Checking the local command line tool.",
        "check": {"type": "command-present", "command": "toolctl"},
        "guidance_id": "install-command",
    }
    if group:
        data["group"] = group
    if runtimes:
        data["runtimes"] = runtimes
    return data


def make_root(tmp: str, declarations: dict[str, object]) -> Path:
    root = Path(tmp) / "skills"
    root.mkdir()
    for name, data in declarations.items():
        path = root / name / "references" / "onboarding.json"
        path.parent.mkdir(parents=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return root


def run(root: Path, skills: list[str], facts: object | None = None,
        runtime: str = "claude") -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), "--skills-root", str(root), "--runtime", runtime]
    if facts is not None:
        command += ["--facts", "-"]
    result = subprocess.run(command + skills, input=json.dumps(facts) if facts is not None else None,
                            capture_output=True, text=True)
    return result


def expect(label: str, condition: bool, output: str = "") -> None:
    if not condition:
        raise AssertionError(f"{label}\n{output}")


def aggregate(requirements: list[object], facts: dict[str, object]) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        root = make_root(tmp, {"x9-demo": {"version": 1, "requirements": requirements}})
        result = run(root, ["x9-demo"], {"x9-demo": facts})
        expect("aggregation runs", result.returncode == 0, result.stdout + result.stderr)
        return json.loads(result.stdout)[0]


def check_status(label: str, requirements: list[object], facts: dict[str, object],
                 coverage: str, readiness: str, overall: bool) -> dict[str, object]:
    out = aggregate(requirements, facts)
    expect(label, (out["coverage"], out["readiness"], out["overall_ready"]) == (coverage, readiness, overall), json.dumps(out))
    return out


def test_group_collapsing() -> None:
    group = [requirement("a", group="g"), requirement("b", group="g"), requirement("c", group="g")]
    out = check_status("ready member hides unresolved alternatives", group,
                       {"a": READY, "b": BLOCKED, "c": USER}, "COMPLETE", "READY", True)
    expect("unused alternatives need no guidance", not any(r["needs_guidance"] for r in out["requirements"]), json.dumps(out))
    expect("group row is reported", out["groups"] == [{"group": "g", **READY}], json.dumps(out))

    cases = [
        ("pending restart outranks setup", {"a": SETUP, "b": RESTART, "c": BLOCKED}, "PENDING_RESTART"),
        ("setup outranks user action", {"a": SETUP, "b": USER, "c": BLOCKED}, "NEEDS_SETUP"),
        ("user action outranks blocked", {"a": USER, "b": BLOCKED, "c": BLOCKED}, "USER_ACTION"),
        ("blocked alone", {"a": BLOCKED, "b": BLOCKED, "c": BLOCKED}, "BLOCKED"),
    ]
    for label, facts, readiness in cases:
        out = aggregate(group, facts)
        expect(label, out["groups"][0]["readiness"] == readiness, json.dumps(out))

    coverage_cases = [
        ("partial member makes group partial", {"a": SETUP, "b": USER, "c": BLOCKED}, "PARTIAL"),
        ("explicit member without partial", {"a": SETUP, "b": USER, "c": SETUP}, "EXPLICIT"),
        ("all complete", {"a": SETUP, "b": RESTART, "c": SETUP}, "COMPLETE"),
    ]
    for label, facts, coverage in coverage_cases:
        out = aggregate(group, facts)
        expect(label, out["groups"][0]["coverage"] == coverage, json.dumps(out))

    out = aggregate(group, {"a": SETUP, "b": BLOCKED, "c": BLOCKED})
    expect("members of an unready group keep guidance", all(r["needs_guidance"] for r in out["requirements"]), json.dumps(out))


def test_skill_precedence() -> None:
    reqs = [requirement("a"), requirement("b")]
    check_status("blocked outranks everything", reqs, {"a": BLOCKED, "b": USER}, "PARTIAL", "BLOCKED", False)
    check_status("user action outranks restart", reqs, {"a": USER, "b": RESTART}, "EXPLICIT", "USER_ACTION", False)
    check_status("restart outranks setup", reqs, {"a": RESTART, "b": SETUP}, "COMPLETE", "PENDING_RESTART", False)
    check_status("setup outranks ready", reqs, {"a": SETUP, "b": READY}, "COMPLETE", "NEEDS_SETUP", False)
    check_status("all ready", reqs, {"a": READY, "b": READY}, "COMPLETE", "READY", True)
    check_status("partial coverage is never overall ready", [requirement("a"), requirement("b", level="optional")],
                 {"a": READY, "b": BLOCKED}, "PARTIAL", "READY", False)
    check_status("explicit coverage is never overall ready", [requirement("a"), requirement("b", level="optional")],
                 {"a": READY, "b": USER}, "EXPLICIT", "READY", False)


def test_optional_and_groups_together() -> None:
    reqs = [requirement("opt", level="optional"), requirement("a", group="g"), requirement("b", group="g")]
    out = check_status("optional rows affect coverage only", reqs, {"opt": SETUP, "a": READY, "b": USER},
                       "COMPLETE", "READY", True)
    expect("optional row keeps its guidance", out["requirements"][0]["needs_guidance"], json.dumps(out))
    check_status("group coverage reaches the skill", reqs, {"opt": READY, "a": SETUP, "b": USER},
                 "EXPLICIT", "NEEDS_SETUP", False)


def test_runtime_filtering_and_skill_outcomes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = make_root(tmp, {
            "x9-plain": {"version": 1, "requirements": [requirement("a"), requirement("only-codex", runtimes=["codex"])]},
            "x9-limited": {"version": 1, "supported_runtimes": ["codex"], "requirements": []},
            "x9-broken": "{",
        })
        (root / "x9-nodecl").mkdir()
        result = run(root, ["x9-plain", "x9-limited", "x9-broken", "x9-nodecl"])
        expect("plan runs", result.returncode == 0, result.stdout + result.stderr)
        plain, limited, broken, nodecl = json.loads(result.stdout)
        expect("requirements are filtered by runtime", [r["id"] for r in plain["requirements"]] == ["a"], result.stdout)
        expect("excluded runtime is complete and blocked",
               (limited["coverage"], limited["readiness"]) == ("COMPLETE", "BLOCKED"), result.stdout)
        expect("invalid declaration is partial and blocked",
               (broken["coverage"], broken["readiness"]) == ("PARTIAL", "BLOCKED") and broken["declaration"] == "invalid", result.stdout)
        expect("missing declaration is complete and ready",
               (nodecl["coverage"], nodecl["readiness"]) == ("COMPLETE", "READY"), result.stdout)

        result = run(root, ["x9-plain", "x9-limited", "x9-broken", "x9-nodecl"],
                     {"x9-plain": {"a": READY, "only-codex": BLOCKED}}, runtime="claude")
        expect("facts for other runtimes are ignored", result.returncode == 0 and json.loads(result.stdout)[0]["overall_ready"], result.stdout + result.stderr)
        codex = run(root, ["x9-plain"], {"x9-plain": {"a": READY, "only-codex": SETUP}}, runtime="codex")
        expect("runtime-specific requirement applies", json.loads(codex.stdout)[0]["readiness"] == "NEEDS_SETUP", codex.stdout + codex.stderr)


def test_declaration_symlink_is_untrusted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = make_root(tmp, {"x9-real": {"version": 1, "requirements": [requirement("a")]}})
        link = root / "x9-link"
        link.mkdir()
        (link / "references").symlink_to(root / "x9-real" / "references")
        out = json.loads(run(root, ["x9-link"]).stdout)[0]
        expect("symlinked references are blocked", (out["coverage"], out["readiness"]) == ("PARTIAL", "BLOCKED"), json.dumps(out))


def test_bad_input_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = make_root(tmp, {"x9-demo": {"version": 1, "requirements": [requirement("a")]}})
        bad = [
            ("missing fact", {"x9-demo": {}}),
            ("missing skill", {}),
            ("extra field", {"x9-demo": {"a": {**READY, "note": "x"}}}),
            ("inconsistent pair", {"x9-demo": {"a": {"coverage": "COMPLETE", "readiness": "BLOCKED"}}}),
            ("unknown value", {"x9-demo": {"a": {"coverage": "SOME", "readiness": "READY"}}}),
            ("unhashable coverage", {"x9-demo": {"a": {"coverage": ["COMPLETE"], "readiness": "READY"}}}),
            ("unhashable readiness", {"x9-demo": {"a": {"coverage": "COMPLETE", "readiness": ["READY"]}}}),
        ]
        for label, facts in bad:
            result = run(root, ["x9-demo"], facts)
            expect(label, result.returncode == 2 and not result.stdout, result.stdout + result.stderr)
        result = run(root, ["../x9-demo"])
        expect("unsafe skill name", result.returncode == 2, result.stdout + result.stderr)


def test_repository_plan() -> None:
    repository_skills = Path(__file__).resolve().parents[2]
    result = run(repository_skills, ["x9-onboarding"])
    out = json.loads(result.stdout)[0]
    expect("repository skill plan", result.returncode == 0 and [r["id"] for r in out["requirements"]] == ["python-runtime"], result.stdout + result.stderr)


def main() -> None:
    test_group_collapsing()
    test_skill_precedence()
    test_optional_and_groups_together()
    test_runtime_filtering_and_skill_outcomes()
    test_declaration_symlink_is_untrusted()
    test_bad_input_is_rejected()
    test_repository_plan()
    print("PASS: onboarding status aggregation regression scenarios")


if __name__ == "__main__":
    main()
