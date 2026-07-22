#!/usr/bin/env python3
"""Validate the shared Claude Code and Codex plugin package metadata."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "x9-agent-skills"
MARKETPLACE_NAME = "xonika9"


def load_json(relative_path: str) -> dict:
    path = ROOT / relative_path
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    claude = load_json(".claude-plugin/plugin.json")
    codex = load_json(".codex-plugin/plugin.json")
    claude_marketplace = load_json(".claude-plugin/marketplace.json")
    codex_marketplace = load_json(".agents/plugins/marketplace.json")

    assert claude["name"] == codex["name"] == PLUGIN_NAME
    assert claude["version"] == codex["version"]
    assert claude["skills"] == codex["skills"] == "./skills/"
    assert (ROOT / "skills").is_dir()

    assert claude_marketplace["name"] == MARKETPLACE_NAME
    assert claude_marketplace["plugins"][0]["name"] == PLUGIN_NAME
    assert claude_marketplace["plugins"][0]["source"] == "./"

    assert codex_marketplace["name"] == MARKETPLACE_NAME
    assert codex_marketplace["plugins"][0]["name"] == PLUGIN_NAME
    assert codex_marketplace["plugins"][0]["source"] == {
        "source": "local",
        "path": "./",
    }

    print("PASS: Claude Code and Codex plugin metadata agree")


if __name__ == "__main__":
    main()
