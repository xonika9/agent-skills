#!/usr/bin/env python3
"""Validate the shared plugin package metadata and the skills' runtime claims."""

from __future__ import annotations

import json
from pathlib import Path
import re
import struct


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "x9-agent-skills"
MARKETPLACE_NAME = "xonika9"
CLAUDE_CATEGORY = "productivity"
CODEX_CATEGORY = "Productivity"
SHARED_MANIFEST_FIELDS = (
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "skills",
)
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
RUNTIME_NAMES = {"opencode": "OpenCode", "claude": "Claude Code", "codex": "Codex"}
# Skills run in every runtime by default; support is never listed in SKILL.md prose.
RUNTIME_CLAIM = re.compile(
    r"model-invoked\b[^.\n]*\bin\b|portable claim|\bsupports (?:OpenCode|Claude Code|Codex)\b|"
    r"^\s*(?:works|runs|работает)\s+(?:only\s+|только\s+)?(?:in|в)\s+(?:OpenCode|Claude Code|Codex)\b",
    re.IGNORECASE | re.MULTILINE,
)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(relative_path: str) -> dict:
    path = ROOT / relative_path
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot read {relative_path}: {error}")
    require(isinstance(value, dict), f"{relative_path} must contain a JSON object")
    return value


def package_path(relative_path: str, field: str) -> Path:
    require(
        isinstance(relative_path, str) and relative_path.startswith("./"),
        f"{field} must be a relative './' path",
    )
    resolved = (ROOT / relative_path[2:]).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        fail(f"{field} escapes the plugin root")
    require(resolved.is_file(), f"{field} points to missing file {relative_path}")
    return resolved


def validate_manifest(manifest: dict, source: str) -> None:
    for field in ("name", "version", "description", "homepage", "repository", "license", "skills"):
        require(isinstance(manifest.get(field), str) and manifest[field], f"{source}.{field} is required")
    require(manifest["name"] == PLUGIN_NAME, f"{source}.name must be {PLUGIN_NAME}")
    require(bool(SEMVER.fullmatch(manifest["version"])), f"{source}.version must use strict semver")
    require(manifest["skills"] == "./skills/", f"{source}.skills must be ./skills/")
    require(isinstance(manifest.get("author"), dict), f"{source}.author is required")
    require(bool(manifest["author"].get("name")), f"{source}.author.name is required")
    require(
        isinstance(manifest.get("keywords"), list)
        and bool(manifest["keywords"])
        and all(isinstance(keyword, str) and keyword for keyword in manifest["keywords"]),
        f"{source}.keywords must contain non-empty strings",
    )


def validate_shared_metadata(claude: dict, codex: dict) -> None:
    for field in SHARED_MANIFEST_FIELDS:
        require(
            claude.get(field) == codex.get(field),
            f"Claude Code and Codex plugin {field} differ",
        )


def validate_png_asset(asset: Path, field: str) -> None:
    data = asset.read_bytes()
    require(len(data) <= 5 * 1024 * 1024, f"{field} must be at most 5 MiB")
    require(
        len(data) >= 33
        and data[:8] == b"\x89PNG\r\n\x1a\n"
        and data[8:16] == b"\x00\x00\x00\rIHDR",
        f"{field} must have a PNG header",
    )
    width, height = struct.unpack(">II", data[16:24])
    require(
        width == height and 48 <= width <= 4096,
        f"{field} must be square and between 48 and 4096 pixels",
    )


def validate_codex_interface(codex: dict) -> None:
    interface = codex.get("interface")
    require(isinstance(interface, dict), ".codex-plugin/plugin.json.interface is required")
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category", "websiteURL"):
        require(isinstance(interface.get(field), str) and interface[field], f"Codex interface.{field} is required")
    require(bool(HEX_COLOR.fullmatch(interface.get("brandColor", ""))), "Codex interface.brandColor must use #RRGGBB")

    capabilities = interface.get("capabilities")
    require(
        isinstance(capabilities, list)
        and all(isinstance(item, str) and item for item in capabilities),
        "Codex interface.capabilities must be an array of non-empty strings",
    )

    prompts = interface.get("defaultPrompt")
    require(isinstance(prompts, list) and 1 <= len(prompts) <= 3, "Codex interface.defaultPrompt must contain 1-3 prompts")
    require(all(isinstance(prompt, str) and 1 <= len(prompt) <= 128 for prompt in prompts), "Codex default prompts must be non-empty and at most 128 characters")

    for field in ("composerIcon", "logo", "logoDark"):
        asset = package_path(interface.get(field), f"Codex interface.{field}")
        require(asset.suffix.lower() == ".png", f"Codex interface.{field} must point to a PNG")
        validate_png_asset(asset, f"Codex interface.{field}")


def runtime_claim_errors(name: str, skill_text: str, declaration: dict | None) -> list[str]:
    """Runtime support lives in references/onboarding.json, not in SKILL.md prose."""
    match = FRONTMATTER.match(skill_text)
    if not match:
        return [f"{name}: SKILL.md has no frontmatter"]
    frontmatter, body = match.groups()
    fields = dict(re.findall(r"^(description|compatibility):[ \t]*(.*)$", frontmatter, re.MULTILINE))
    errors = []
    for source, text in (("compatibility", fields.get("compatibility", "")), ("body", body)):
        claim = RUNTIME_CLAIM.search(text)
        if claim:
            errors.append(
                f"{name}: SKILL.md {source} lists supported runtimes ({claim.group(0).strip()!r}); "
                "skills run everywhere by default and record a restriction in references/onboarding.json"
            )
    supported = (declaration or {}).get("supported_runtimes")
    if isinstance(supported, list):
        description = fields.get("description", "")
        for runtime in supported:
            label = RUNTIME_NAMES.get(runtime, str(runtime))
            if label not in description:
                errors.append(f"{name}: restricted to {', '.join(supported)} but the description does not name {label}")
    return errors


def validate_runtime_claims() -> None:
    errors = []
    for skill in sorted((ROOT / "skills").iterdir()):
        skill_file = skill / "SKILL.md"
        if not skill_file.is_file():
            continue
        declaration_file = skill / "references" / "onboarding.json"
        declaration = None
        if declaration_file.is_file():
            declaration = load_json(str(declaration_file.relative_to(ROOT)))
        errors.extend(runtime_claim_errors(skill.name, skill_file.read_text(encoding="utf-8"), declaration))
    require(not errors, "runtime claims:\n- " + "\n- ".join(errors))


def main() -> None:
    claude = load_json(".claude-plugin/plugin.json")
    codex = load_json(".codex-plugin/plugin.json")
    claude_marketplace = load_json(".claude-plugin/marketplace.json")
    codex_marketplace = load_json(".agents/plugins/marketplace.json")

    validate_manifest(claude, ".claude-plugin/plugin.json")
    validate_manifest(codex, ".codex-plugin/plugin.json")
    validate_codex_interface(codex)

    validate_shared_metadata(claude, codex)
    require((ROOT / "skills").is_dir(), "skills/ is missing")
    validate_runtime_claims()

    require(claude_marketplace.get("name") == MARKETPLACE_NAME, "Claude marketplace name differs")
    claude_plugins = claude_marketplace.get("plugins")
    require(isinstance(claude_plugins, list) and len(claude_plugins) == 1, "Claude marketplace must contain one plugin")
    require(claude_plugins[0].get("name") == PLUGIN_NAME, "Claude marketplace plugin name differs")
    require(claude_plugins[0].get("source") == "./", "Claude marketplace source must be ./")
    require(claude_plugins[0].get("category") == CLAUDE_CATEGORY, f"Claude marketplace category must be {CLAUDE_CATEGORY}")

    require(codex_marketplace.get("name") == MARKETPLACE_NAME, "Codex marketplace name differs")
    codex_plugins = codex_marketplace.get("plugins")
    require(isinstance(codex_plugins, list) and len(codex_plugins) == 1, "Codex marketplace must contain one plugin")
    entry = codex_plugins[0]
    require(entry.get("name") == PLUGIN_NAME, "Codex marketplace plugin name differs")
    require(entry.get("source") == {"source": "local", "path": "./"}, "Codex marketplace source differs")
    require(entry.get("policy") == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "Codex marketplace policy differs")
    require(codex["interface"]["category"] == CODEX_CATEGORY, f"Codex interface category must be {CODEX_CATEGORY}")
    require(entry.get("category") == codex["interface"]["category"], "Codex marketplace category differs")

    print("PASS: Claude Code and Codex plugin metadata agree; skill runtime claims follow the declarations")


if __name__ == "__main__":
    main()
