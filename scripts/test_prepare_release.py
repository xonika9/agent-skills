#!/usr/bin/env python3
"""Regression tests for changelog coverage rules."""

from __future__ import annotations

from pathlib import Path
from datetime import date
import subprocess
import tempfile
from unittest.mock import patch

import prepare_release
from release_version import next_version, parse_version


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


def test_all_unreleased_sections_are_required() -> None:
    without_unreleased = "## 1.0.0 - 2026-01-01\n"
    expect_failure(without_unreleased, [])
    for heading in ("Highlights", "Install / update", "Compatibility", "Breaking changes"):
        incomplete = WITH_ENTRY.replace(f"### {heading}\n", "")
        expect_failure(incomplete, [])
        expect_failure(incomplete, ["skills/example/SKILL.md"])


def test_calendar_metadata_and_changelog_date() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        path = root / "CHANGELOG.md"
        notes = EMPTY[:EMPTY.index("## 1.0.0")]
        release = "## 26.10.19.1 - 2026-10-19\n\n### Highlights\n\n- A release.\n"
        path.write_text(notes + release, encoding="utf-8")
        with patch.object(prepare_release, "ROOT", root):
            assert "A release." in prepare_release.changelog_notes("26.10.19.1")[1]
            path.write_text(notes + release.replace("2026-10-19", "2026-10-20"), encoding="utf-8")
            try:
                prepare_release.changelog_notes("26.10.19.1")
            except SystemExit as error:
                assert "date must match" in str(error)
            else:
                raise AssertionError("a mismatched changelog date must block release")
        manifest = root / "plugin.json"
        manifest.write_text('{"version": "26.10.19.1"}', encoding="utf-8")
        assert prepare_release.load_version(manifest) == "26.10.19.1"
        manifest.write_text('{"version": "26.02.30.1"}', encoding="utf-8")
        with patch.object(prepare_release, "ROOT", root):
            try:
                prepare_release.load_version(manifest)
            except SystemExit as error:
                assert "Invalid release version" in str(error)
            else:
                raise AssertionError("an impossible calendar date must block release")


def test_new_release_must_be_newer_than_public_tags() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name in (".claude-plugin", ".codex-plugin"):
            (root / name).mkdir()
            (root / name / "plugin.json").write_text('{"version": "26.10.19.1"}', encoding="utf-8")
        template = EMPTY[:EMPTY.index("## 1.0.0")]
        release = "## 26.10.19.1 - 2026-10-19\n\n" + "\n\n".join(
            f"### {section}\n\n- Release entry." for section in prepare_release.REQUIRED_SECTIONS
        )
        (root / "CHANGELOG.md").write_text(template + release, encoding="utf-8")
        with patch.object(prepare_release, "ROOT", root), \
             patch.object(prepare_release, "tag_exists", return_value=False), \
             patch.object(prepare_release, "changed_paths_since", return_value=[]), \
             patch("sys.argv", ["prepare_release.py", "--check"]), patch("builtins.print"):
            for tag in ("v26.10.19.2", "v26.10.20.1"):
                with patch.object(prepare_release, "previous_release_tag", return_value=tag):
                    try:
                        prepare_release.main()
                    except SystemExit as error:
                        assert "must be newer" in str(error)
                    else:
                        raise AssertionError("an older calendar version must block publication")
            for tag in ("v4.1.0", "v26.10.18.10"):
                with patch.object(prepare_release, "previous_release_tag", return_value=tag):
                    prepare_release.main()


def main() -> None:
    assert parse_version("26.10.19.1") == (date(2026, 10, 19), 1)
    assert parse_version("28.02.29.1") == (date(2028, 2, 29), 1)
    assert next_version(["v4.1.0"], date(2026, 10, 19)) == "26.10.19.1"
    assert next_version(["v26.10.19.2", "v26.10.19.10", "v4.1.0"], date(2026, 10, 19)) == "26.10.19.11"
    assert next_version(["v26.10.19.11"], date(2026, 10, 20)) == "26.10.20.1"
    assert next_version(["v26.10.19.11"], date(2027, 1, 1)) == "27.01.01.1"
    try:
        next_version(["v26.10.20.1"], date(2026, 10, 19))
    except ValueError:
        pass
    else:
        raise AssertionError("a future release tag must stop version selection")
    assert not prepare_release.has_unreleased_entries(EMPTY)
    assert prepare_release.has_unreleased_entries(WITH_ENTRY)
    assert prepare_release.is_release_relevant("skills/x9-research/SKILL.md")
    assert prepare_release.is_release_relevant("README.md")
    assert prepare_release.is_release_relevant("scripts/check_public.py")
    assert prepare_release.is_release_relevant(".github/workflows/validate.yml")
    assert prepare_release.is_release_relevant(".claude/skills/release/SKILL.md")
    assert prepare_release.is_release_relevant(".claude/skills/release/references/version-confirmation.md")
    assert prepare_release.is_release_relevant(".claude/skills/release/scripts/check_skill_links.py")
    assert not prepare_release.is_release_relevant("scripts/test_check_package.py")
    assert not prepare_release.is_release_relevant(".claude/skills/release/references/notes.md")

    expect_failure(EMPTY, ["skills/x9-research/SKILL.md"])
    prepare_release.validate_development_changelog(
        WITH_ENTRY,
        ["skills/x9-research/SKILL.md"],
    )
    expect_failure(EMPTY, ["scripts/check_public.py"])
    expect_failure(EMPTY, [".claude/skills/release/scripts/check_skill_links.py"])
    test_all_unreleased_sections_are_required()
    test_calendar_metadata_and_changelog_date()
    test_new_release_must_be_newer_than_public_tags()
    test_changed_paths_include_both_sides_of_move()
    print("PASS: changelog coverage regression scenarios")


if __name__ == "__main__":
    main()
