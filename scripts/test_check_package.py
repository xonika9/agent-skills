#!/usr/bin/env python3
"""Regression tests for shared plugin metadata checks."""

from copy import deepcopy
from pathlib import Path
import struct
import tempfile

import check_package

ROOT = Path(__file__).resolve().parent.parent
SHARED_CORE_START = b"<!-- BEGIN SHARED PERSONAL CORE -->"
SHARED_CORE_END = b"<!-- END SHARED PERSONAL CORE -->"
PUBLISHED_GLOBAL_FILES = (
    ROOT / "global-files/opencode/AGENTS.md",
    ROOT / "global-files/claude/CLAUDE.md",
    ROOT / "global-files/codex/AGENTS.md",
    ROOT / "global-files/pi/AGENTS.md",
    ROOT / "global-files/antigravity/AGENTS.md",
)


def manifest() -> dict:
    return {
        "name": "x9-agent-skills",
        "version": "26.10.19.1",
        "description": "Shared description",
        "author": {"name": "xonika9", "url": "https://example.com"},
        "homepage": "https://example.com",
        "repository": "https://example.com/repository",
        "license": "MIT",
        "keywords": ["agent-skills"],
        "skills": "./skills/",
    }


def expect_mismatch(field: str) -> None:
    claude = manifest()
    codex = deepcopy(claude)
    codex[field] = "different" if field != "keywords" else ["different"]
    try:
        check_package.validate_shared_metadata(claude, codex)
    except SystemExit as error:
        assert field in str(error)
        return
    raise AssertionError(f"expected {field} mismatch to fail")


def expect_interface_failure(codex: dict, field: str) -> None:
    try:
        check_package.validate_codex_interface(codex)
    except SystemExit as error:
        assert field in str(error), str(error)
        return
    raise AssertionError(f"expected invalid {field} to fail")


def test_capabilities_contract() -> None:
    original = check_package.load_json(".codex-plugin/plugin.json")
    valid_empty = deepcopy(original)
    valid_empty["interface"]["capabilities"] = []
    check_package.validate_codex_interface(valid_empty)
    absent = deepcopy(original)
    del absent["interface"]["capabilities"]
    expect_interface_failure(absent, "capabilities")
    for value in (42, "Read", [""], [42]):
        malformed = deepcopy(original)
        malformed["interface"]["capabilities"] = value
        expect_interface_failure(malformed, "capabilities")


def test_declared_png_geometry() -> None:
    valid = (check_package.ROOT / "assets/x9-icon.png").read_bytes()
    with tempfile.TemporaryDirectory() as directory:
        asset = Path(directory) / "icon.png"
        for data in (
            b"This is not a PNG.\n",
            valid[:16] + struct.pack(">II", 48, 49) + valid[24:],
            valid[:16] + struct.pack(">II", 47, 47) + valid[24:],
            valid[:16] + struct.pack(">II", 4097, 4097) + valid[24:],
            valid + b"x" * (5 * 1024 * 1024),
        ):
            asset.write_bytes(data)
            try:
                check_package.validate_png_asset(asset, "icon")
            except SystemExit as error:
                assert "icon" in str(error)
            else:
                raise AssertionError("expected invalid icon to fail")
        asset.write_bytes(valid)
        check_package.validate_png_asset(asset, "icon")


def skill(description: str, body: str, compatibility: str = "") -> str:
    extra = f"compatibility: {compatibility}\n" if compatibility else ""
    return f"---\nname: x9-demo\ndescription: {description}\n{extra}---\n\n# Demo\n\n{body}\n"


def test_runtime_claims() -> None:
    errors = check_package.runtime_claim_errors
    assert errors("x9-demo", skill("Use for demos.", "Do the work."), None) == []
    for body in (
        "This skill is model-invoked in Claude Code and Codex.",
        "Its portable claim is structural compatibility only.",
        "Работает в Claude Code и Codex.",
    ):
        assert errors("x9-demo", skill("Use for demos.", body), None), body
    assert errors("x9-demo", skill("Use for demos.", "Do it.", "Supports OpenCode and Codex."), None)
    assert errors("x9-demo", skill("Use for demos.", "In Codex, use the native worker."), None) == []
    restricted = {"version": 1, "supported_runtimes": ["claude"], "requirements": []}
    assert errors("x9-demo", skill("Claude Code only. Use for demos.", "Do it."), restricted) == []
    assert errors("x9-demo", skill("Use for demos.", "Do it."), restricted)


def shared_core(path: Path) -> bytes:
    data = path.read_bytes()
    assert data.count(SHARED_CORE_START) == 1 and data.count(SHARED_CORE_END) == 1, path
    start = data.index(SHARED_CORE_START)
    return data[start : data.index(SHARED_CORE_END, start) + len(SHARED_CORE_END)]


def test_published_shared_cores() -> None:
    cores = [shared_core(path) for path in PUBLISHED_GLOBAL_FILES]
    assert all(core == cores[0] for core in cores[1:]), "published shared cores differ"
    required = (
        b"Include the goal and completion bar, non-derivable context, scope and authority, required evidence, and expected output",
        b"Avoid unrequested features, abstractions, and adjacent cleanup.",
        b"preserve load-bearing source wording and the active skill's specialist prompt and output contract",
        b"Write worker briefs in English",
        b"user-facing results in the user's language.",
        b"Do substantive work in the primary session by default.",
        b"nested delegation is explicitly required",
        b"Continue already-authorized fixes, reruns, and explicitly scoped external actions",
        b"newly discovered risk materially changes the agreed scope",
        b"Intermediate checks do not replace the requested end-to-end result",
        b"tell me in the chat and stop that delegated work; do not switch to another model or runtime yourself.",
    )
    for path, core in zip(PUBLISHED_GLOBAL_FILES, cores):
        for phrase in required:
            assert phrase in core, f"{path}: missing {phrase!r}"
        for phrase in (b"configured lower-cost subagents execute", b"Do not use OpenCode"):
            assert phrase not in core, f"{path}: still contains {phrase!r}"
    codex = PUBLISHED_GLOBAL_FILES[2].read_text(encoding="utf-8")
    for phrase in (
        "inherit the primary session's model and reasoning effort",
        "do not configure a lower-cost subagent default",
        "stop or archive them only when that cleanup is explicitly authorized",
    ):
        assert phrase in codex, f"codex global file: missing {phrase!r}"


def test_context_creator_uses_instruction_rubric() -> None:
    skill = (ROOT / "skills/x9-context-files-generator/SKILL.md").read_text(encoding="utf-8")
    for phrase in (
        "load and apply `x9-agent-instructions`",
        "subordinate instruction-quality rubric",
        "single report and approval gate",
        "instruction rubric as `degraded`",
        "README-only work records it as `not applicable`",
    ):
        assert phrase in skill, f"x9-context-files-generator: missing {phrase!r}"


def main() -> None:
    check_package.validate_manifest(manifest(), "manifest")
    for version in ("4.1.0", "26.2.03.1", "26.02.3.1", "26.2.30.1", "26.10.19.0", "26.10.19.01"):
        invalid = manifest()
        invalid["version"] = version
        try:
            check_package.validate_manifest(invalid, "manifest")
        except SystemExit as error:
            assert "version" in str(error)
        else:
            raise AssertionError(f"expected invalid calendar version {version} to fail")
    check_package.validate_shared_metadata(manifest(), manifest())
    for field in manifest():
        expect_mismatch(field)
    test_capabilities_contract()
    test_declared_png_geometry()
    test_runtime_claims()
    test_published_shared_cores()
    test_context_creator_uses_instruction_rubric()
    print("PASS: shared plugin metadata regression scenarios")


if __name__ == "__main__":
    main()
