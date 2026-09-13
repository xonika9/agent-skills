#!/usr/bin/env python3
"""Validate the public runtime profiles bundled with x9-onboarding."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Any


PROFILE_FILES = {
    "codex": "codex.toml",
    "opencode": "opencode.json",
    "claude": "claude.json",
}
ALLOWED_LEAF_PATHS = {
    "codex": frozenset(
        """
        agents.max_depth approval_policy desktop.appearanceLightChromeTheme.accent
        desktop.appearanceLightChromeTheme.contrast
        desktop.appearanceLightChromeTheme.fonts.code
        desktop.appearanceLightChromeTheme.fonts.ui
        desktop.appearanceLightChromeTheme.ink
        desktop.appearanceLightChromeTheme.opaqueWindows
        desktop.appearanceLightChromeTheme.semanticColors.diffAdded
        desktop.appearanceLightChromeTheme.semanticColors.diffRemoved
        desktop.appearanceLightChromeTheme.semanticColors.skill
        desktop.appearanceLightChromeTheme.surface desktop.appearanceLightCodeThemeId
        desktop.codeFontSize desktop.conversationDetailMode desktop.dock-icon-preference
        desktop.followUpQueueMode desktop.git-branch-prefix
        desktop.keepRemoteControlAwakeWhilePluggedIn desktop.mac-menu-bar-enabled
        desktop.preventSleepWhileRunning desktop.realtimeVoiceScreenContextEnabled
        desktop.sansFontSize desktop.show-context-window-usage desktop.usePointerCursors
        features.code_mode.enabled features.context_management.experimental_mode
        features.default_mode_request_user_input features.goals features.hooks
        features.multi_agent features.multi_agent_v2.default_wait_timeout_ms
        features.multi_agent_v2.enabled features.multi_agent_v2.hide_spawn_agent_metadata
        features.multi_agent_v2.max_concurrent_threads_per_session
        features.multi_agent_v2.tool_namespace model model_reasoning_effort personality
        sandbox_mode suppress_unstable_features_warning tui.notification_condition
        """.split()
    ),
    "opencode": frozenset(
        """
        $schema agents.astra-high.description agents.astra-high.mode
        agents.astra-high.model agents.deepseek-high.description agents.deepseek-high.mode
        agents.deepseek-high.model agents.deepseek-max.description agents.deepseek-max.mode
        agents.deepseek-max.model agents.explore.model
        agents.explore.permissions[].action agents.explore.permissions[].effect
        agents.explore.permissions[].resource agents.general.disabled
        agents.inherit.description agents.inherit.mode agents.sol-fast-high.description
        agents.sol-fast-high.mode agents.sol-fast-high.model agents.sol-high.description
        agents.sol-high.mode agents.sol-high.model agents.sol-medium.description
        agents.sol-medium.mode agents.sol-medium.model agents.terra-fast-high.description
        agents.terra-fast-high.mode agents.terra-fast-high.model
        agents.terra-high.description agents.terra-high.mode agents.terra-high.model
        agents.terra-max.description agents.terra-max.mode agents.terra-max.model
        agents.terra-medium.description agents.terra-medium.mode agents.terra-medium.model
        agents.terra-xhigh.description agents.terra-xhigh.mode agents.terra-xhigh.model
        agents.title.model experimental.subagent_depth
        mcp.servers.chrome-devtools.command[] mcp.servers.chrome-devtools.disabled
        mcp.servers.chrome-devtools.timeout.catalog
        mcp.servers.chrome-devtools.timeout.execution mcp.servers.chrome-devtools.type
        mcp.servers.exa.disabled mcp.servers.exa.headers.x-api-key
        mcp.servers.exa.oauth mcp.servers.exa.type mcp.servers.exa.url model
        permissions[].action permissions[].effect permissions[].resource
        providers.openai.models.gpt-6-astra.settings.reasoningEffort websearch.provider
        """.split()
    ),
    "claude": frozenset(
        """
        autoCompactEnabled effortLevel enabledPlugins.codex@openai-codex
        enabledPlugins.compound-engineering@compound-engineering-plugin
        env.CLAUDE_CODE_AUTO_COMPACT_WINDOW model
        modelSettings.claude-opus-5.effortLevel permissions.defaultMode
        skipDangerousModePermissionPrompt skipWorkflowUsageWarning
        """.split()
    ),
}
REQUIRED_RISK_SETTINGS = {
    "codex": {
        "approval_policy": "never",
        "desktop.realtimeVoiceScreenContextEnabled": True,
        "sandbox_mode": "danger-full-access",
    },
    "opencode": {
        "permissions": [{"action": "*", "effect": "allow", "resource": "*"}]
    },
    "claude": {
        "permissions.defaultMode": "bypassPermissions",
        "skipDangerousModePermissionPrompt": True,
    },
}
REQUIRED_PROFILE_SETTINGS = {
    "codex": {},
    "opencode": {},
    "claude": {
        "enabledPlugins.codex@openai-codex": True,
        "enabledPlugins.compound-engineering@compound-engineering-plugin": True,
        "env.CLAUDE_CODE_AUTO_COMPACT_WINDOW": "375000",
    },
}
ALLOWED_CLAUDE_ENV = {"CLAUDE_CODE_AUTO_COMPACT_WINDOW"}
ALLOWED_CLAUDE_PLUGINS = {
    "codex@openai-codex",
    "compound-engineering@compound-engineering-plugin",
}
ALLOWED_URLS = {
    "https://opencode.ai/config.json",
    "http://127.0.0.1:9223",
    "https://mcp.exa.ai/mcp",
}
PERSONAL_RE = re.compile(
    r"(?i)(?:/Users/|/home/|[A-Z]:\\Users\\|\.ssh(?:/|\\)|xonika)"
)
SECRET_KEY_RE = re.compile(
    r"(?i)(?:api[_-]?key|authorization|cookie|credential|password|secret|token)"
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(?:\bbearer\s+\S+|\bghp_[A-Za-z0-9_-]{8,}|"
    r"\bsk(?:-proj)?-[A-Za-z0-9_-]{8,}|\bsk_[A-Za-z0-9_-]{8,})"
)
ENV_REFERENCE_RE = re.compile(r"^\{env:[A-Z][A-Z0-9_]*\}$")
URL_RE = re.compile(r"[a-z][a-z0-9+.-]*://[^\"'\s,\]\[(){}]+", re.IGNORECASE)


class DuplicateKeyError(ValueError):
    pass


def no_duplicate_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key}")
        result[key] = value
    return result


def load_profile(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        if path.suffix == ".toml":
            value = tomllib.load(handle)
        else:
            value = json.loads(
                handle.read().decode("utf-8"), object_pairs_hook=no_duplicate_object
            )
    if not isinstance(value, dict):
        raise ValueError("profile root must be an object or table")
    return value


def get_path(value: dict[str, Any], dotted_path: str) -> Any:
    current: Any = value
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


def leaf_paths(value: Any, path: str = "") -> set[str]:
    if isinstance(value, dict):
        if not value:
            return {path}
        result: set[str] = set()
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            result.update(leaf_paths(child, child_path))
        return result
    if isinstance(value, list):
        if not value:
            return {path}
        result = set()
        for child in value:
            result.update(leaf_paths(child, f"{path}[]"))
        return result
    return {path}


def scan(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if SECRET_KEY_RE.search(key):
                if not isinstance(child, str) or not ENV_REFERENCE_RE.fullmatch(child):
                    errors.append(
                        f"{child_path}: secret-like fields must use an environment reference"
                    )
            scan(child, child_path, errors)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            scan(child, f"{path}[{index}]", errors)
        return
    if not isinstance(value, str):
        return
    if PERSONAL_RE.search(value):
        errors.append(f"{path}: personal path or identifier is not allowed")
    if SECRET_VALUE_RE.search(value):
        errors.append(f"{path}: literal secret-like value is not allowed")
    for match in URL_RE.finditer(value):
        if match.group(0) not in ALLOWED_URLS:
            errors.append(f"{path}: URL is not allowlisted")


def validate_profile(runtime: str, path: Path) -> list[str]:
    errors: list[str] = []
    try:
        profile = load_profile(path)
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        return [f"{path.name}: cannot parse profile: {type(error).__name__}"]

    unknown = sorted(leaf_paths(profile) - ALLOWED_LEAF_PATHS[runtime])
    for key in unknown:
        errors.append(f"{path.name}.{key}: profile path is not allowed")
    for dotted_path, expected in REQUIRED_RISK_SETTINGS[runtime].items():
        try:
            actual = get_path(profile, dotted_path)
        except KeyError:
            errors.append(
                f"{path.name}.{dotted_path}: documented elevated-risk setting is missing"
            )
        else:
            if actual != expected:
                errors.append(
                    f"{path.name}.{dotted_path}: value no longer matches its documented elevated-risk behavior"
                )
    for dotted_path, expected in REQUIRED_PROFILE_SETTINGS[runtime].items():
        try:
            actual = get_path(profile, dotted_path)
        except KeyError:
            errors.append(f"{path.name}.{dotted_path}: required profile setting is missing")
        else:
            if actual != expected:
                errors.append(
                    f"{path.name}.{dotted_path}: value no longer matches the curated profile"
                )
    if runtime == "claude":
        env = profile.get("env", {})
        if not isinstance(env, dict):
            errors.append(f"{path.name}.env: must be an object")
        else:
            for key in sorted(set(env) - ALLOWED_CLAUDE_ENV):
                errors.append(f"{path.name}.env.{key}: environment field is not allowed")
        plugins = profile.get("enabledPlugins", {})
        if not isinstance(plugins, dict):
            errors.append(f"{path.name}.enabledPlugins: must be an object")
        else:
            for key in sorted(set(plugins) - ALLOWED_CLAUDE_PLUGINS):
                errors.append(f"{path.name}.enabledPlugins.{key}: plugin is not allowlisted")
    scan(profile, path.name, errors)
    return errors


def validate_profiles(profiles_root: Path) -> list[str]:
    errors: list[str] = []
    expected = set(PROFILE_FILES.values())
    try:
        actual = {path.name for path in profiles_root.iterdir() if path.is_file()}
    except OSError as error:
        return [f"profiles: cannot read directory: {type(error).__name__}"]
    for name in sorted(actual - expected):
        errors.append(f"{name}: unexpected profile file")
    for runtime, name in PROFILE_FILES.items():
        path = profiles_root / name
        if not path.is_file():
            errors.append(f"{name}: required profile is missing")
            continue
        errors.extend(validate_profile(runtime, path))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "profiles_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "profiles",
    )
    args = parser.parse_args()
    errors = validate_profiles(args.profiles_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("PASS: 3 sanitized runtime profiles")


if __name__ == "__main__":
    main()
