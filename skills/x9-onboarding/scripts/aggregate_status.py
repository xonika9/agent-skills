#!/usr/bin/env python3
"""List the requirements to check for selected skills, then aggregate their statuses.

Usage:
  aggregate_status.py --skills-root <skills-root> --runtime <runtime> <skill>...
  aggregate_status.py --skills-root <skills-root> --runtime <runtime> --facts <file|-> <skill>...

Without --facts, print the applicable requirements per skill. With --facts, read a JSON
object {skill: {requirement-id: {"coverage": ..., "readiness": ...}}} holding one
individual status per applicable requirement (other ids are ignored), and print group and
skill statuses.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_onboarding import RUNTIMES, TARGET_SKILL_RE, inspect_declaration, load_declaration


# Individual requirement statuses: coverage maps to the readiness values it can carry.
PAIRS = {
    "COMPLETE": {"READY", "NEEDS_SETUP", "PENDING_RESTART"},
    "PARTIAL": {"BLOCKED"},
    "EXPLICIT": {"USER_ACTION"},
}
# Group readiness when no member is READY, most significant first.
GROUP_READINESS_ORDER = ("PENDING_RESTART", "NEEDS_SETUP", "USER_ACTION", "BLOCKED")
# Skill base readiness, most significant first.
SKILL_READINESS_ORDER = ("BLOCKED", "USER_ACTION", "PENDING_RESTART", "NEEDS_SETUP", "READY")


def group_status(members: list[dict[str, str]]) -> dict[str, str]:
    if any(m["coverage"] == "COMPLETE" and m["readiness"] == "READY" for m in members):
        return {"coverage": "COMPLETE", "readiness": "READY"}
    readiness = next(r for r in GROUP_READINESS_ORDER if any(m["readiness"] == r for m in members))
    coverages = {m["coverage"] for m in members}
    coverage = "PARTIAL" if "PARTIAL" in coverages else "EXPLICIT" if "EXPLICIT" in coverages else "COMPLETE"
    return {"coverage": coverage, "readiness": readiness}


def skill_status(required_units: list[dict[str, str]], all_units: list[dict[str, str]]) -> dict[str, Any]:
    """Coverage spans every unit; base readiness spans required units only."""
    coverages = {u["coverage"] for u in all_units}
    coverage = "PARTIAL" if "PARTIAL" in coverages else "EXPLICIT" if "EXPLICIT" in coverages else "COMPLETE"
    readinesses = {u["readiness"] for u in required_units}
    readiness = next((r for r in SKILL_READINESS_ORDER if r in readinesses), "READY")
    return {"coverage": coverage, "readiness": readiness, "overall_ready": readiness == "READY" and coverage == "COMPLETE"}


def resolve_skill(skills_root: Path, skill: str, runtime: str) -> dict[str, Any]:
    """Resolve a skill to a fixed outcome, or to the requirements applicable in the runtime."""
    result: dict[str, Any] = {"skill": skill}
    declaration, problem = inspect_declaration(skills_root / skill)
    if problem is not None:
        return {**result, "declaration": "invalid", "coverage": "PARTIAL", "readiness": "BLOCKED", "errors": [problem]}
    if declaration is None:
        return {**result, "declaration": "missing", "coverage": "COMPLETE", "readiness": "READY"}
    data, errors = load_declaration(declaration, skills_root)
    if data is None:
        return {**result, "declaration": "invalid", "coverage": "PARTIAL", "readiness": "BLOCKED", "errors": errors}
    supported = data.get("supported_runtimes")
    if supported is not None and runtime not in supported:
        return {**result, "declaration": "restricted", "coverage": "COMPLETE", "readiness": "BLOCKED"}
    applicable = [r for r in data["requirements"] if runtime in r.get("runtimes", RUNTIMES)]
    return {**result, "declaration": "checked", "requirements": applicable}


def aggregate(resolved: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    requirements = resolved["requirements"]
    units: dict[str, dict[str, str]] = {}
    for requirement in requirements:
        fact = facts.get(requirement["id"])
        if not isinstance(fact, dict) or set(fact) != {"coverage", "readiness"}:
            raise ValueError(f"{resolved['skill']}: {requirement['id']}: fact must hold exactly coverage and readiness")
        coverage, readiness = fact["coverage"], fact["readiness"]
        if not (isinstance(coverage, str) and isinstance(readiness, str) and readiness in PAIRS.get(coverage, ())):
            raise ValueError(f"{resolved['skill']}: {requirement['id']}: unsupported coverage and readiness pair")
        units[requirement["id"]] = {"coverage": coverage, "readiness": readiness}

    members_by_group: dict[str, list[str]] = {}
    for requirement in requirements:
        if "group" in requirement:
            members_by_group.setdefault(requirement["group"], []).append(requirement["id"])
    groups = {g: group_status([units[i] for i in ids]) for g, ids in members_by_group.items()}

    rows = []
    for requirement in requirements:
        unit = units[requirement["id"]]
        group = requirement.get("group")
        group_ready = group is not None and groups[group]["readiness"] == "READY"
        rows.append({
            "id": requirement["id"],
            "level": requirement["level"],
            **({"group": group} if group else {}),
            **unit,
            "needs_guidance": unit["readiness"] != "READY" and not group_ready,
        })

    ungrouped = [units[r["id"]] for r in requirements if "group" not in r]
    group_units = list(groups.values())
    required_ungrouped = [units[r["id"]] for r in requirements if "group" not in r and r["level"] == "required"]
    summary = skill_status(required_ungrouped + group_units, ungrouped + group_units)
    return {
        "skill": resolved["skill"],
        "declaration": "checked",
        **summary,
        "groups": [{"group": g, **status} for g, status in groups.items()],
        "requirements": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skills-root", type=Path, required=True)
    parser.add_argument("--runtime", choices=sorted(RUNTIMES), required=True)
    parser.add_argument("--facts", help="JSON file with individual statuses, or - for stdin")
    parser.add_argument("skills", nargs="+")
    args = parser.parse_args()
    skills_root = args.skills_root.resolve()
    if not skills_root.is_dir():
        print("ERROR: skills root is not a directory", file=sys.stderr)
        return 2
    if any(not TARGET_SKILL_RE.fullmatch(name) for name in args.skills):
        print("ERROR: skill names must use x9- lowercase hyphen-case", file=sys.stderr)
        return 2

    facts_by_skill: dict[str, Any] | None = None
    if args.facts is not None:
        try:
            raw = sys.stdin.read() if args.facts == "-" else Path(args.facts).read_text(encoding="utf-8")
            facts_by_skill = json.loads(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            print("ERROR: facts are not readable JSON", file=sys.stderr)
            return 2
        if not isinstance(facts_by_skill, dict):
            print("ERROR: facts must be a JSON object keyed by skill", file=sys.stderr)
            return 2

    output = []
    for skill in args.skills:
        resolved = resolve_skill(skills_root, skill, args.runtime)
        if facts_by_skill is None or resolved["declaration"] != "checked":
            output.append(resolved)
            continue
        try:
            skill_facts = facts_by_skill.get(skill)
            if not isinstance(skill_facts, dict):
                raise ValueError(f"{skill}: facts are missing for this skill")
            output.append(aggregate(resolved, skill_facts))
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
