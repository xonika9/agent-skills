#!/usr/bin/env python3
"""Validate the shared Claude Code and Codex plugin package metadata."""

from __future__ import annotations

import json
from pathlib import Path
import re


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


def validate_codex_interface(codex: dict) -> None:
    interface = codex.get("interface")
    require(isinstance(interface, dict), ".codex-plugin/plugin.json.interface is required")
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category", "websiteURL"):
        require(isinstance(interface.get(field), str) and interface[field], f"Codex interface.{field} is required")
    require(bool(HEX_COLOR.fullmatch(interface.get("brandColor", ""))), "Codex interface.brandColor must use #RRGGBB")

    prompts = interface.get("defaultPrompt")
    require(isinstance(prompts, list) and 1 <= len(prompts) <= 3, "Codex interface.defaultPrompt must contain 1-3 prompts")
    require(all(isinstance(prompt, str) and 1 <= len(prompt) <= 128 for prompt in prompts), "Codex default prompts must be non-empty and at most 128 characters")

    for field in ("composerIcon", "logo", "logoDark"):
        asset = package_path(interface.get(field), f"Codex interface.{field}")
        require(asset.suffix.lower() == ".png", f"Codex interface.{field} must point to a PNG")


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

    print("PASS: Claude Code and Codex plugin metadata agree")


if __name__ == "__main__":
    main()
