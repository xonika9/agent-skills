#!/usr/bin/env python3
"""Validate read-only onboarding declarations below a package skills root.

Usage: validate_onboarding.py <skills-root>
"""

from __future__ import annotations

import argparse
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any


RUNTIMES = {"opencode", "claude", "codex"}
KINDS = {"skill", "command", "agent", "mcp", "runtime-feature", "user-action"}
LEVELS = {"required", "optional"}
CHECK_TYPES = {
    "skill-present",
    "command-present",
    "runtime-component",
    "runtime-feature",
    "manual",
}
FEATURE_IDS = {"active-skill-catalog", "browser-control", "native-subagents"}
GUIDANCE_BY_KIND = {
    "skill": "install-skill",
    "command": "install-command",
    "agent": "create-agent",
    "mcp": "configure-mcp",
    "runtime-feature": "enable-runtime-feature",
    "user-action": "complete-user-action",
}
CHECK_BY_KIND = {
    "skill": "skill-present",
    "command": "command-present",
    "agent": "runtime-component",
    "mcp": "runtime-component",
    "runtime-feature": "runtime-feature",
    "user-action": "manual",
}

TOP_LEVEL_FIELDS = {"version", "supported_runtimes", "requirements"}
REQUIREMENT_FIELDS = {
    "id",
    "runtimes",
    "kind",
    "level",
    "needed_for",
    "check",
    "guidance_id",
}
OPTIONAL_REQUIREMENT_FIELDS = {"group"}
CHECK_FIELDS = {
    "skill-present": {"type", "target_skill"},
    "command-present": {"type", "command"},
    "runtime-component": {"type", "component_id"},
    "runtime-feature": {"type", "feature_id"},
    "manual": {"type"},
}
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TARGET_SKILL_RE = re.compile(r"^x9(?:-[a-z0-9]+)+$")
COMMAND_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
COMPONENT_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.:-][a-z0-9]+)*$")
SECRET_NAME_RE = re.compile(
    r"(?i)(?:api[_-]?key|authorization|credential|cookie|password|secret|token)"
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(?:\b(?:api[_-]?key|authorization|credential|cookie|password|secret|token)\b\s*(?:=|:)|"
    r"\bbearer\s+[A-Za-z0-9._-]+|\bghp_[A-Za-z0-9_-]{8,}|\bsk(?:-proj)?-[A-Za-z0-9_-]{8,}|"
    r"\bsk_[A-Za-z0-9_-]{8,})"
)
URL_RE = re.compile(r"(?i)(?:[a-z][a-z0-9+.-]*://|(?:data|mailto):|www\.)")
PATH_RE = re.compile(r"(?:^/|^~(?:/|$)|(?:^|\s)\.\.?/|\\)")
SHELL_RE = re.compile(r"[|&;`$<>*{}]")


class DuplicateKeyError(ValueError):
    """Raised when JSON contains duplicate object keys."""


def no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def error(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def is_safe_text(value: str) -> bool:
    return (
        bool(value)
        and value == value.strip()
        and len(value) <= 160
        and all(char.isalnum() or char in " ,.:!?()'-" for char in value)
    )


def scan_unsafe(value: Any, path: str, errors: list[str]) -> None:
    """Reject data that could become an instruction, a location, or a secret."""
    pending = [(value, path)]
    while pending:
        current, current_path = pending.pop()
        if isinstance(current, dict):
            children = []
            for key, child in current.items():
                key_path = f"{current_path}.{key}" if current_path else key
                if not isinstance(key, str):
                    error(errors, key_path, "field name must be a string")
                elif SECRET_NAME_RE.search(key):
                    error(errors, key_path, "secret-like field name is not allowed")
                children.append((child, key_path))
            pending.extend(reversed(children))
        elif isinstance(current, list):
            pending.extend(
                (child, f"{current_path}[{index}]")
                for index, child in reversed(list(enumerate(current)))
            )
        elif isinstance(current, str):
            if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in current):
                error(errors, current_path, "control characters are not allowed")
            if SECRET_VALUE_RE.search(current):
                error(errors, current_path, "secret-like value is not allowed")
            if URL_RE.search(current):
                error(errors, current_path, "URLs are not allowed")
            if PATH_RE.search(current):
                error(errors, current_path, "paths are not allowed")
            if SHELL_RE.search(current):
                error(errors, current_path, "shell syntax is not allowed")


def require_object(value: Any, path: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        error(errors, path, "must be an object")
        return None
    return value


def require_string(value: Any, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str):
        error(errors, path, "must be a string")
        return None
    return value


def validate_fields(
    value: dict[str, Any],
    allowed: set[str],
    path: str,
    errors: list[str],
    required: set[str] | None = None,
) -> None:
    required = allowed if required is None else required
    for field in sorted(set(value) - allowed):
        error(errors, f"{path}.{field}" if path else field, "unknown field")
    for field in sorted(required - set(value)):
        error(errors, f"{path}.{field}" if path else field, "required field is missing")


def validate_runtimes(value: Any, path: str, errors: list[str]) -> set[str] | None:
    if not isinstance(value, list):
        error(errors, path, "must be a non-empty array")
        return None
    if not value:
        error(errors, path, "must not be empty")
        return None
    seen: set[str] = set()
    valid = True
    for index, runtime in enumerate(value):
        runtime_path = f"{path}[{index}]"
        if not isinstance(runtime, str):
            error(errors, runtime_path, "must be a string")
            valid = False
        elif runtime not in RUNTIMES:
            error(errors, runtime_path, "unknown runtime")
            valid = False
        elif runtime in seen:
            error(errors, runtime_path, "duplicates an earlier runtime")
            valid = False
        else:
            seen.add(runtime)
    return seen if valid else None


def validate_check(value: Any, path: str, errors: list[str]) -> str | None:
    check = require_object(value, path, errors)
    if check is None:
        return None
    check_type = require_string(check.get("type"), f"{path}.type", errors)
    if check_type not in CHECK_TYPES:
        if check_type is not None:
            error(errors, f"{path}.type", "unknown check type")
        return check_type
    validate_fields(check, CHECK_FIELDS[check_type], path, errors)

    if check_type == "skill-present":
        target_skill = require_string(check.get("target_skill"), f"{path}.target_skill", errors)
        if target_skill is not None and not TARGET_SKILL_RE.fullmatch(target_skill):
            error(errors, f"{path}.target_skill", "must use x9- lowercase hyphen-case")
    elif check_type == "command-present":
        command = require_string(check.get("command"), f"{path}.command", errors)
        if command is not None and not COMMAND_RE.fullmatch(command):
            error(errors, f"{path}.command", "must be one command name without a path or arguments")
    elif check_type == "runtime-component":
        component_id = require_string(check.get("component_id"), f"{path}.component_id", errors)
        if component_id is not None and not COMPONENT_ID_RE.fullmatch(component_id):
            error(errors, f"{path}.component_id", "must be a safe lowercase component identifier")
    elif check_type == "runtime-feature":
        feature_id = require_string(check.get("feature_id"), f"{path}.feature_id", errors)
        if feature_id is not None and feature_id not in FEATURE_IDS:
            error(errors, f"{path}.feature_id", "unknown runtime feature")
    return check_type


def validate_requirement(
    value: Any,
    path: str,
    skills_root: Path,
    supported_runtimes: set[str] | None,
    seen_ids: set[str],
    errors: list[str],
) -> None:
    requirement = require_object(value, path, errors)
    if requirement is None:
        return
    validate_fields(
        requirement,
        REQUIREMENT_FIELDS | OPTIONAL_REQUIREMENT_FIELDS,
        path,
        errors,
        REQUIREMENT_FIELDS,
    )

    identifier = require_string(requirement.get("id"), f"{path}.id", errors)
    if identifier is not None:
        if not IDENTIFIER_RE.fullmatch(identifier):
            error(errors, f"{path}.id", "must use lowercase hyphen-case")
        elif identifier in seen_ids:
            error(errors, f"{path}.id", "duplicates an earlier requirement id")
        else:
            seen_ids.add(identifier)

    runtimes = requirement.get("runtimes")
    validate_runtimes(runtimes, f"{path}.runtimes", errors)
    if isinstance(runtimes, list):
        for index, runtime in enumerate(runtimes):
            if (
                isinstance(runtime, str)
                and runtime in RUNTIMES
                and supported_runtimes is not None
                and runtime not in supported_runtimes
            ):
                error(
                    errors,
                    f"{path}.runtimes[{index}]",
                    "runtime is not declared in supported_runtimes",
                )

    kind = require_string(requirement.get("kind"), f"{path}.kind", errors)
    if kind is not None and kind not in KINDS:
        error(errors, f"{path}.kind", "unknown kind")
    level = require_string(requirement.get("level"), f"{path}.level", errors)
    if level is not None and level not in LEVELS:
        error(errors, f"{path}.level", "unknown level")
    if "group" in requirement:
        group = require_string(requirement.get("group"), f"{path}.group", errors)
        if group is not None and not IDENTIFIER_RE.fullmatch(group):
            error(errors, f"{path}.group", "must use lowercase hyphen-case")
        if level is not None and level != "required":
            error(errors, f"{path}.level", "alternative group members must be required")
    needed_for = require_string(requirement.get("needed_for"), f"{path}.needed_for", errors)
    if needed_for is not None and not is_safe_text(needed_for):
        error(errors, f"{path}.needed_for", "must be one safe display string of at most 160 characters")
    guidance_id = require_string(requirement.get("guidance_id"), f"{path}.guidance_id", errors)
    if guidance_id is not None and not IDENTIFIER_RE.fullmatch(guidance_id):
        error(errors, f"{path}.guidance_id", "must use lowercase hyphen-case")

    check_type = validate_check(requirement.get("check"), f"{path}.check", errors)
    if kind in CHECK_BY_KIND and check_type is not None and check_type != CHECK_BY_KIND[kind]:
        error(errors, f"{path}.check.type", f"must be {CHECK_BY_KIND[kind]} for kind {kind}")
    if kind in GUIDANCE_BY_KIND and guidance_id is not None and guidance_id != GUIDANCE_BY_KIND[kind]:
        error(errors, f"{path}.guidance_id", f"must be {GUIDANCE_BY_KIND[kind]} for kind {kind}")
    if check_type == "skill-present" and isinstance(requirement.get("check"), dict):
        target_skill = requirement["check"].get("target_skill")
        if isinstance(target_skill, str) and TARGET_SKILL_RE.fullmatch(target_skill):
            target_path = skills_root / target_skill
            try:
                target_mode = target_path.lstat().st_mode
            except OSError:
                error(errors, f"{path}.check.target_skill", "target skill does not exist below the skills root")
            else:
                if stat.S_ISLNK(target_mode):
                    error(errors, f"{path}.check.target_skill", "target skill must not be a symbolic link")
                elif not stat.S_ISDIR(target_mode):
                    error(errors, f"{path}.check.target_skill", "target skill does not exist below the skills root")


def validate_declaration(path: Path, skills_root: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, RecursionError) as exc:
        return [f"JSON: {exc}"]

    errors: list[str] = []
    scan_unsafe(data, "", errors)
    declaration = require_object(data, "declaration", errors)
    if declaration is None:
        return errors
    validate_fields(declaration, TOP_LEVEL_FIELDS, "", errors)
    version = declaration.get("version")
    if type(version) is not int:
        error(errors, "version", "must be the integer 1")
    elif version != 1:
        error(errors, "version", "must be 1")
    supported_runtimes = validate_runtimes(
        declaration.get("supported_runtimes"), "supported_runtimes", errors
    )
    requirements = declaration.get("requirements")
    if not isinstance(requirements, list):
        error(errors, "requirements", "must be a non-empty array")
        return errors
    if not requirements:
        error(errors, "requirements", "must not be empty")
    seen_ids: set[str] = set()
    for index, requirement in enumerate(requirements):
        validate_requirement(
            requirement,
            f"requirements[{index}]",
            skills_root,
            supported_runtimes,
            seen_ids,
            errors,
        )
    groups: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, requirement in enumerate(requirements):
        if isinstance(requirement, dict) and isinstance(requirement.get("group"), str):
            groups.setdefault(requirement["group"], []).append((index, requirement))
    for members in groups.values():
        if len(members) < 2:
            index, _ = members[0]
            error(errors, f"requirements[{index}].group", "alternative group must have at least two members")
            continue
        expected_runtimes = members[0][1].get("runtimes")
        for index, member in members[1:]:
            if member.get("runtimes") != expected_runtimes:
                error(errors, f"requirements[{index}].runtimes", "alternative group members must use identical runtimes")
    return errors


def declaration_files(skills_root: Path) -> tuple[list[Path], list[str]]:
    files = []
    errors = []
    for skill_dir in sorted(skills_root.iterdir()):
        if skill_dir.is_symlink():
            errors.append(f"{skill_dir.name}: skill directory must not be a symbolic link")
            continue
        if not skill_dir.is_dir():
            continue
        references = skill_dir / "references"
        if references.is_symlink():
            errors.append(f"{skill_dir.name}/references: directory must not be a symbolic link")
            continue
        declaration = references / "onboarding.json"
        try:
            declaration_mode = declaration.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"{skill_dir.name}/references/onboarding.json: cannot inspect file: {exc}")
            continue
        if stat.S_ISLNK(declaration_mode):
            errors.append(f"{skill_dir.name}/references/onboarding.json: file must not be a symbolic link")
        elif stat.S_ISREG(declaration_mode):
            files.append(declaration)
        else:
            errors.append(f"{skill_dir.name}/references/onboarding.json: must be a regular file")
    return files, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skills_root", type=Path, help="package skills root to validate")
    args = parser.parse_args()
    skills_root = args.skills_root.resolve()
    if not skills_root.is_dir():
        print(f"ERROR: skills root is not a directory: {args.skills_root}")
        return 1

    files, errors = declaration_files(skills_root)
    for path in files:
        relative_path = path.relative_to(skills_root)
        for detail in validate_declaration(path, skills_root):
            errors.append(f"{relative_path}: {detail}")
    if errors:
        for detail in errors:
            print(f"ERROR: {detail}")
        return 1
    print(f"PASS: {len(files)} declaration file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
