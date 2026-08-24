#!/usr/bin/env python3
"""Regression tests for changelog coverage rules."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import prepare_release


EMPTY = """## Unreleased

### Highlights

### Install / update

### Compatibility

### Breaking changes

## 1.0.0 - 2026-01-01
"""

WITH_ENTRY = EMPTY.replace(
    "### Compatibility\n\n",
    "### Compatibility\n\n- Clarified runtime support.\n\n",
)


def expect_failure(changelog: str, paths: list[str]) -> None:
    try:
        prepare_release.validate_development_changelog(changelog, paths)
    except SystemExit:
        return
    raise AssertionError("expected changelog coverage failure")


def test_changed_paths_include_both_sides_of_move() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@users.noreply.github.com"],
            cwd=root,
            check=True,
        )
        source = root / "skills" / "example" / "SKILL.md"
        source.parent.mkdir(parents=True)
        source.write_text("example\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
        subprocess.run(["git", "tag", "v1.0.0"], cwd=root, check=True)

        destination = root / "internal" / "SKILL.md"
        destination.parent.mkdir()
        subprocess.run(
            ["git", "mv", str(source.relative_to(root)), str(destination.relative_to(root))],
            cwd=root,
            check=True,
        )
        asset = root / "assets" / "new.png"
        asset.parent.mkdir()
        asset.write_bytes(b"png")

        changed = prepare_release.changed_paths_since("v1.0.0", root)
        assert "skills/example/SKILL.md" in changed
        assert "internal/SKILL.md" in changed
        assert "assets/new.png" in changed


def main() -> None:
    assert not prepare_release.has_unreleased_entries(EMPTY)
    assert prepare_release.has_unreleased_entries(WITH_ENTRY)
    assert prepare_release.is_release_relevant("skills/x9-research/SKILL.md")
    assert prepare_release.is_release_relevant("README.md")
    assert prepare_release.is_release_relevant("scripts/check_public.py")
    assert prepare_release.is_release_relevant(".github/workflows/validate.yml")
    assert prepare_release.is_release_relevant(".claude/skills/release/SKILL.md")
    assert prepare_release.is_release_relevant(".claude/skills/release/references/version-confirmation.md")
    assert not prepare_release.is_release_relevant("scripts/test_check_package.py")
    assert not prepare_release.is_release_relevant(".claude/skills/release/references/notes.md")

    expect_failure(EMPTY, ["skills/x9-research/SKILL.md"])
    prepare_release.validate_development_changelog(
        WITH_ENTRY,
        ["skills/x9-research/SKILL.md"],
    )
    expect_failure(EMPTY, ["scripts/check_public.py"])
    test_changed_paths_include_both_sides_of_move()
    print("PASS: changelog coverage regression scenarios")


if __name__ == "__main__":
    main()
