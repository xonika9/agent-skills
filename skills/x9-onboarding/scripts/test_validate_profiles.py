#!/usr/bin/env python3
"""Regression checks for the public runtime-profile validator."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from validate_profiles import validate_profiles


PROFILES = Path(__file__).resolve().parents[1] / "profiles"


def expect(label: str, condition: bool, errors: list[str]) -> None:
    if not condition:
        raise AssertionError(f"{label}\n" + "\n".join(errors))


def copied_profiles(tmp: str) -> Path:
    target = Path(tmp) / "profiles"
    shutil.copytree(PROFILES, target)
    return target


def main() -> None:
    errors = validate_profiles(PROFILES)
    expect("repository profiles", not errors, errors)

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "claude.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["hooks"] = {}
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect("forbidden top-level field", any("hooks" in item for item in errors), errors)

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "codex.toml"
        path.write_text(
            path.read_text(encoding="utf-8")
            + '\n[desktop.privateHelper]\ncommand = ["sh", "-c", "upload auth file"]\n',
            encoding="utf-8",
        )
        errors = validate_profiles(root)
        expect(
            "forbidden nested profile path",
            any("profile path is not allowed" in item for item in errors),
            errors,
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "claude.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["env"]["ANTHROPIC_API_KEY"] = "literal-value"
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect(
            "forbidden Claude environment field",
            any("environment field is not allowed" in item for item in errors),
            errors,
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "claude.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["enabledPlugins"]["frontend-design@claude-plugins-official"] = False
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect(
            "unapproved Claude plugin",
            any("plugin is not allowlisted" in item for item in errors),
            errors,
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "claude.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        del value["enabledPlugins"]["codex@openai-codex"]
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect(
            "missing core Claude plugin",
            any("required profile setting is missing" in item for item in errors),
            errors,
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "opencode.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["mcp"]["servers"]["exa"]["headers"]["x-api-key"] = "literal-value"
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect(
            "literal credential",
            any("environment reference" in item for item in errors),
            errors,
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "opencode.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["mcp"]["servers"]["exa"]["url"] = "https://private.example.test"
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect("unlisted URL", any("URL is not allowlisted" in item for item in errors), errors)

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "opencode.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["mcp"]["servers"]["chrome-devtools"]["command"].append(
            "--browserUrl=https://private.example.test"
        )
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect(
            "embedded unlisted URL",
            any("URL is not allowlisted" in item for item in errors),
            errors,
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "claude.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["enabledPlugins"] = []
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect(
            "invalid Claude plugin shape",
            any("must be an object" in item for item in errors),
            errors,
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "codex.toml"
        personal_path = "/" + "Users/person/bin/notify"
        path.write_text(
            path.read_text(encoding="utf-8")
            + f'\nnotify = ["{personal_path}"]\n',
            encoding="utf-8",
        )
        errors = validate_profiles(root)
        expect("personal path", any("personal path" in item for item in errors), errors)

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "claude.json"
        path.write_text('{"model":"one","model":"two"}', encoding="utf-8")
        errors = validate_profiles(root)
        expect("duplicate JSON key", any("cannot parse" in item for item in errors), errors)

    with tempfile.TemporaryDirectory() as tmp:
        root = copied_profiles(tmp)
        path = root / "claude.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["permissions"]["defaultMode"] = "default"
        path.write_text(json.dumps(value), encoding="utf-8")
        errors = validate_profiles(root)
        expect(
            "risk documentation drift",
            any("elevated-risk behavior" in item for item in errors),
            errors,
        )

    print("PASS: runtime profile validator regression scenarios")


if __name__ == "__main__":
    main()
