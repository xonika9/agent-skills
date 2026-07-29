#!/usr/bin/env python3
"""Regression checks for OKF v0.2 adaptation and v0.1 compatibility."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
INSERT = HERE / "insert_frontmatter.py"
VALIDATE = HERE / "validate_okf.py"
BOM = b"\xef\xbb\xbf"
ACTOR = "x9-okf-docs/test"


def run(*args):
    return subprocess.run(
        [sys.executable, "-B", *map(str, args)],
        capture_output=True,
        text=True,
    )


def meta(title: str, description: str, concept_type: str = "Research Note"):
    return {
        "type": concept_type,
        "title": title,
        "description": description,
        "tags": ["okf-test", "metadata"],
    }


def expect(label: str, condition: bool, result=None):
    if not condition:
        detail = "" if result is None else result.stdout + result.stderr
        raise AssertionError(f"{label}\n{detail}")


def write_manifest(path: Path, entries: dict):
    path.write_text(json.dumps(entries), encoding="utf-8")


def inventory(root: Path, destination: Path, *extra):
    result = run(INSERT, root, "--inventory-out", destination, *extra)
    expect("inventory created", result.returncode == 0 and destination.exists(), result)
    return json.loads(destination.read_text(encoding="utf-8"))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)

        git_root = temp / "git-source"
        git_docs = git_root / "nested" / "docs"
        git_docs.mkdir(parents=True)
        git_file = git_docs / "history.md"
        git_file.write_text("# Git history\n", encoding="utf-8")
        expect("temporary Git repository initialized", subprocess.run(["git", "init", "-q", git_root]).returncode == 0)
        expect("temporary Git identity configured", subprocess.run(["git", "-C", git_root, "config", "user.email", "okf-test"]).returncode == 0)
        expect("temporary Git name configured", subprocess.run(["git", "-C", git_root, "config", "user.name", "OKF Test"]).returncode == 0)
        expect("Git fixture staged", subprocess.run(["git", "-C", git_root, "add", "nested/docs/history.md"]).returncode == 0)
        commit_env = {
            **os.environ,
            "GIT_AUTHOR_DATE": "2020-01-02T03:04:05+00:00",
            "GIT_COMMITTER_DATE": "2020-01-02T03:04:05+00:00",
        }
        expect("Git fixture committed", subprocess.run(["git", "-C", git_root, "commit", "-q", "-m", "fixture"], env=commit_env).returncode == 0)
        git_file.touch()
        git_inventory = inventory(git_docs, temp / "git-inventory.json")
        suggested = git_inventory["files"]["history.md"]["suggested_generated_at"]
        expect(
            "Git history wins over filesystem mtime",
            datetime.fromisoformat(suggested.replace("Z", "+00:00"))
            == datetime.fromisoformat("2020-01-02T03:04:05+00:00"),
        )
        expect(
            "Git freshness records its non-degraded source",
            git_inventory["files"]["history.md"]["freshness_source"] == "git"
            and git_inventory["files"]["history.md"]["freshness_degraded"] is False,
        )
        fallback = temp / "freshness-fallback"
        fallback.mkdir()
        (fallback / "note.md").write_text("# Freshness\n", encoding="utf-8")
        fallback_inventory = inventory(fallback, temp / "fallback-inventory.json")
        expect(
            "filesystem freshness fallback is explicitly degraded",
            fallback_inventory["files"]["note.md"]["freshness_source"] == "filesystem_mtime"
            and fallback_inventory["files"]["note.md"]["freshness_degraded"] is True,
        )

        official = temp / "official"
        official.mkdir()
        (official / "minimal.md").write_text("---\ntype: Unknown Domain Type\n---\n# Minimal\n", encoding="utf-8")
        (official / "one-tag.md").write_text("---\ntype: Metric\ntags: [finance]\n---\n# Metric\n", encoding="utf-8")
        official_result = run(VALIDATE, official, "--profile", "okf")
        expect("official v0.2 accepts unknown types and optional fields", official_result.returncode == 0, official_result)
        curated_result = run(VALIDATE, official)
        expect("curated profile remains explicitly stricter", curated_result.returncode != 0 and "missing curated fields" in curated_result.stdout, curated_result)
        (official / "bad-tags.md").write_text("---\ntype: Note\ntags: 42\n---\n# Bad tags\n", encoding="utf-8")
        bad_tags = run(VALIDATE, official)
        expect("invalid curated tags report an issue instead of crashing", bad_tags.returncode != 0 and "tags must be a list" in bad_tags.stdout and "Traceback" not in bad_tags.stderr, bad_tags)
        (official / "bad-tags.md").unlink()
        typed_result = run(VALIDATE, official, "--profile", "okf", "--types", "Metric")
        expect("type catalogs are explicit local policy", typed_result.returncode != 0 and "outside local profile catalog" in typed_result.stdout, typed_result)

        computation = official / "calculation.md"
        computation.write_text("---\ntype: Attested Computation\n---\n# Computation\n", encoding="utf-8")
        computation_invalid = run(VALIDATE, official, "--profile", "okf")
        expect("Attested Computation requires runtime", computation_invalid.returncode != 0 and "runtime is required" in computation_invalid.stdout, computation_invalid)
        computation.write_text("---\ntype: Attested Computation\nruntime: python\n---\n# Computation\n", encoding="utf-8")
        expect("Attested Computation with runtime passes", run(VALIDATE, official, "--profile", "okf").returncode == 0)

        reserved = temp / "reserved"
        nested = reserved / "topic"
        nested.mkdir(parents=True)
        (reserved / "index.md").write_text(
            "---\nokf_version: \"0.2\"\n---\n# Sections\n\n* [Topic](topic/) - Topic documents.\n",
            encoding="utf-8",
        )
        (nested / "index.md").write_text("# Notes\n\n* [Note](note.md) - A note.\n", encoding="utf-8")
        (nested / "log.md").write_text("# Log\n\n## 2026-07-29\n* **Update**: Current.\n\n## 2026-07-28\n* **Creation**: Started.\n", encoding="utf-8")
        (nested / "note.md").write_text("---\ntype: Note\n---\n# Note\n", encoding="utf-8")
        reserved_result = run(VALIDATE, reserved, "--profile", "okf", "--whole-bundle")
        expect("reserved index and log files use their own validation", reserved_result.returncode == 0 and "checked: 1 concepts" in reserved_result.stdout, reserved_result)
        root_index = reserved / "index.md"
        root_index.write_text(
            "---\nokf_version: \"0.1\"\n---\n# Sections\n\n* [Topic](topic/) - Topic documents.\n",
            encoding="utf-8",
        )
        declaration_before = root_index.read_bytes()
        dry_declared = run(
            INSERT,
            reserved,
            "--declare-version",
            "0.2",
            "--whole-bundle",
            "--apply",
            "--dry-run",
        )
        expect(
            "declaration dry-run reports without writing",
            dry_declared.returncode == 0
            and "would update" in dry_declared.stdout
            and root_index.read_bytes() == declaration_before,
            dry_declared,
        )
        declared = run(
            INSERT,
            reserved,
            "--declare-version",
            "0.2",
            "--whole-bundle",
            "--apply",
        )
        expect(
            "version declaration runs only after whole-bundle validation",
            declared.returncode == 0 and 'okf_version: "0.2"' in root_index.read_text(encoding="utf-8"),
            declared,
        )
        nested_index_before = (nested / "index.md").read_bytes()
        reserved_inventory = inventory(reserved, temp / "reserved-inventory.json", "--whole-bundle")
        expect("reserved files are excluded from concept inventory", set(reserved_inventory["files"]) == {"topic/note.md"})
        expect("inventory leaves reserved files untouched", (nested / "index.md").read_bytes() == nested_index_before)
        (nested / "index.md").write_text("---\ntype: Index\n---\n# Notes\n\n* [Note](note.md) - A note.\n", encoding="utf-8")
        nested_invalid = run(VALIDATE, reserved, "--profile", "okf", "--whole-bundle")
        expect("nested index frontmatter is rejected", nested_invalid.returncode != 0 and "must not contain frontmatter" in nested_invalid.stdout, nested_invalid)

        root = temp / "docs"
        root.mkdir()
        body = b"# Body\r\n\r\nKeep bytes.\r\n"
        (root / "doc.md").write_bytes(BOM + body)
        os.chmod(root / "doc.md", 0o640)
        (root / "partial.md").write_bytes(b"---\ntype: Analysis\n---\n# Partial\n")
        preserved_file = root / "preserved.md"
        preserved_file.write_text(
            f'---\ntype: Research Note\ntitle: Original\ndescription: Original description\ntags: [original, metadata]\n'
            f'generated: {{"by": "{ACTOR}", "at": "2020-01-01T00:00:00+00:00"}}\n---\n# Preserved\n',
            encoding="utf-8",
        )
        (root / "AGENTS.md").write_text("# Config\n", encoding="utf-8")
        (root / "README.md").write_text("# Onboarding\n", encoding="utf-8")
        archive = root / "archive"
        archive.mkdir()
        (archive / "historical.md").write_text("# Historical\n", encoding="utf-8")

        missing = run(VALIDATE, root, "--missing")
        expect("curated worklist excludes onboarding by default", missing.returncode == 0 and "doc.md" in missing.stdout and "partial.md" in missing.stdout and "README.md" not in missing.stdout, missing)
        included = run(VALIDATE, root, "--missing", "--include-readme")
        repeated_default = run(VALIDATE, root, "--missing")
        expect("include-readme does not mutate later selection", "README.md" in included.stdout and "README.md" not in repeated_default.stdout, repeated_default)
        whole_missing = run(VALIDATE, root, "--missing", "--whole-bundle")
        expect(
            "whole-bundle includes normally excluded content but never onboarding",
            "README.md" not in whole_missing.stdout
            and "AGENTS.md" not in whole_missing.stdout
            and "archive/historical.md" in whole_missing.stdout,
            whole_missing,
        )
        explicitly_excluded = run(
            VALIDATE,
            root,
            "--missing",
            "--whole-bundle",
            "--exclude",
            "archive",
        )
        expect(
            "explicit exclusions still narrow ordinary whole-bundle inspection",
            "archive/historical.md" not in explicitly_excluded.stdout,
            explicitly_excluded,
        )

        root_inventory_path = temp / "inventory.json"
        root_inventory = inventory(root, root_inventory_path)
        manifest = temp / "manifest.json"
        write_manifest(manifest, {
            "doc.md": meta("Body", "Primary byte-preservation fixture"),
            "partial.md": meta("Partial", "Partial-header repair fixture", "Analysis"),
            "preserved.md": meta("Replacement", "Replacement fixture"),
        })
        self_declared_manifest = temp / "self-declared-manifest.json"
        forged_meta = meta("Body", "Forged provenance fixture")
        forged_meta["generated"] = {"by": ACTOR, "at": "2020-01-01T00:00:00+00:00"}
        write_manifest(self_declared_manifest, {"doc.md": forged_meta})
        no_actor_manifest = run(
            INSERT,
            root,
            "--manifest",
            self_declared_manifest,
            "--inventory",
            root_inventory_path,
        )
        expect(
            "curated v0.2 rejects self-declared provenance without actor",
            no_actor_manifest.returncode != 0
            and "--actor is required" in no_actor_manifest.stdout + no_actor_manifest.stderr,
            no_actor_manifest,
        )
        applied = run(
            INSERT,
            root,
            "--manifest",
            manifest,
            "--inventory",
            root_inventory_path,
            "--actor",
            ACTOR,
        )
        expect("native v0.2 manifest applied", applied.returncode == 0, applied)
        doc_bytes = (root / "doc.md").read_bytes()
        expect("BOM and CRLF body preserved", doc_bytes.startswith(BOM) and doc_bytes.endswith(body))
        expect("atomic replacement preserves file mode", (root / "doc.md").stat().st_mode & 0o777 == 0o640)
        expect("generated actor inserted", f'"by": "{ACTOR}"' in (root / "doc.md").read_text(encoding="utf-8-sig"))
        expect("legacy timestamp is not created for new v0.2 documents", "timestamp:" not in (root / "doc.md").read_text(encoding="utf-8-sig"))
        partial_text = (root / "partial.md").read_text(encoding="utf-8")
        expect(
            "meaning-changing repair records operation provenance even without prior generated",
            '"by": "x9-okf-docs/test"' in partial_text and '"at":' in partial_text,
        )
        expect(
            "valid existing semantic metadata and provenance are preserved by default",
            'title: "Original"' in preserved_file.read_text(encoding="utf-8")
            and "2020-01-01T00:00:00+00:00" in preserved_file.read_text(encoding="utf-8"),
        )
        expect("curated v0.2 validates after insertion", run(VALIDATE, root, "--inventory", root_inventory_path).returncode == 0)

        replacement_inventory_path = temp / "replacement-inventory.json"
        inventory(root, replacement_inventory_path)
        replacement_manifest = temp / "replacement-manifest.json"
        write_manifest(replacement_manifest, {"preserved.md": meta("Replacement", "Replacement fixture")})
        replaced = run(
            INSERT,
            root,
            "--manifest",
            replacement_manifest,
            "--inventory",
            replacement_inventory_path,
            "--actor",
            ACTOR,
            "--replace-existing-metadata",
        )
        replaced_text = preserved_file.read_text(encoding="utf-8")
        expect(
            "explicit replacement changes meaning and replaces operation provenance",
            replaced.returncode == 0
            and 'title: "Replacement"' in replaced_text
            and 'description: "Replacement fixture"' in replaced_text
            and "2020-01-01T00:00:00+00:00" not in replaced_text,
            replaced,
        )

        custom = root / "custom.md"
        custom.write_bytes("---\r\ncustom: |\r\n  before\r\n  ---\r\n  after\r\nowner: Alex\r\nвладелец: Алекс\r\n---\r# Custom\r".encode("utf-8"))
        custom_inventory_path = temp / "custom-inventory.json"
        inventory(root, custom_inventory_path)
        custom_manifest = temp / "custom-manifest.json"
        write_manifest(custom_manifest, {"custom.md": meta("Custom", "Unknown-field preservation fixture")})
        custom_applied = run(
            INSERT,
            root,
            "--manifest",
            custom_manifest,
            "--inventory",
            custom_inventory_path,
            "--actor",
            ACTOR,
        )
        custom_bytes = custom.read_bytes()
        expect(
            "unknown raw fields and CR endings are preserved",
            custom_applied.returncode == 0
            and b"owner: Alex\r" in custom_bytes
            and "владелец: Алекс\r".encode("utf-8") in custom_bytes
            and b"  ---\r" in custom_bytes
            and b"\n" not in custom_bytes,
            custom_applied,
        )

        atomic = temp / "atomic"
        atomic.mkdir()
        atomic_file = atomic / "a.md"
        atomic_file.write_text("# A\n", encoding="utf-8")
        atomic_inventory_path = temp / "atomic-inventory.json"
        inventory(atomic, atomic_inventory_path)
        atomic_manifest = temp / "atomic-manifest.json"
        write_manifest(atomic_manifest, {
            "a.md": meta("A", "Atomic fixture"),
            "missing.md": meta("Missing", "Missing path fixture"),
        })
        atomic_before = atomic_file.read_bytes()
        atomic_apply = run(
            INSERT,
            atomic,
            "--manifest",
            atomic_manifest,
            "--inventory",
            atomic_inventory_path,
            "--actor",
            ACTOR,
        )
        expect("manifest preflight failure is atomic", atomic_apply.returncode != 0 and atomic_file.read_bytes() == atomic_before, atomic_apply)
        v3_inventory = json.loads(atomic_inventory_path.read_text(encoding="utf-8"))
        v3_inventory["version"] = 3
        v3_path = temp / "v3-inventory.json"
        v3_path.write_text(json.dumps(v3_inventory), encoding="utf-8")
        v3_apply = run(
            INSERT,
            atomic,
            "--manifest",
            atomic_manifest,
            "--inventory",
            v3_path,
            "--actor",
            ACTOR,
        )
        expect(
            "v3 inventory is refused cleanly",
            v3_apply.returncode != 0
            and "format v4" in v3_apply.stdout + v3_apply.stderr
            and "Traceback" not in v3_apply.stderr,
            v3_apply,
        )

        legacy = temp / "legacy"
        legacy.mkdir()
        legacy_body = b"# Legacy\r\n\r\nUnchanged.\r\n"
        legacy_file = legacy / "legacy.md"
        legacy_file.write_bytes(
            b"---\r\ntype: Research Note\r\ntitle: Legacy\r\ndescription: Legacy migration fixture\r\ntags: [legacy, migration]\r\ntimestamp: 2026-07-15T12:00:00+03:00\r\n---\r\n"
            + legacy_body
        )
        minimal_file = legacy / "minimal.md"
        minimal_file.write_text("---\ntype: Note\n---\n# Minimal\n", encoding="utf-8")
        native_file = legacy / "native.md"
        native_file.write_text(
            f'---\ntype: Note\ngenerated: {{"by": "{ACTOR}", "at": "2026-07-15T12:00:00+03:00"}}\n---\n# Native\n',
            encoding="utf-8",
        )
        legacy_before = legacy_file.read_bytes()
        audit = run(INSERT, legacy, "--migrate-v01", "--profile", "okf")
        expect("v0.1 migration defaults to read-only audit", audit.returncode == 0 and "WOULD MIGRATE legacy.md" in audit.stdout and legacy_file.read_bytes() == legacy_before, audit)
        no_actor = run(INSERT, legacy, "--migrate-v01", "--apply")
        expect("migration apply requires a truthful actor", no_actor.returncode != 0 and "--actor is required" in no_actor.stderr + no_actor.stdout, no_actor)
        legacy_inventory_path = temp / "legacy-inventory.json"
        legacy_inventory = inventory(legacy, legacy_inventory_path)
        expect(
            "unquoted legacy timestamp drives freshness",
            legacy_inventory["files"]["legacy.md"]["suggested_generated_at"]
            == "2026-07-15T12:00:00+03:00",
        )
        dry_migrated = run(
            INSERT,
            legacy,
            "--migrate-v01",
            "--apply",
            "--profile",
            "okf",
            "--actor",
            "process:okf-migration",
            "--inventory",
            legacy_inventory_path,
            "--dry-run",
        )
        expect(
            "migration dry-run performs checks without writing",
            dry_migrated.returncode == 0
            and "would update: legacy.md" in dry_migrated.stdout
            and legacy_file.read_bytes() == legacy_before,
            dry_migrated,
        )
        migrated = run(
            INSERT,
            legacy,
            "--migrate-v01",
            "--apply",
            "--actor",
            "process:okf-migration",
            "--inventory",
            legacy_inventory_path,
            "--profile",
            "okf",
        )
        migrated_text = legacy_file.read_text(encoding="utf-8")
        expect(
            "migration adds generated and keeps timestamp for compatibility",
            migrated.returncode == 0
            and "generated:" in migrated_text
            and "process:okf-migration" in migrated_text
            and "timestamp:" in migrated_text
            and legacy_file.read_bytes().endswith(legacy_body),
            migrated,
        )
        expect("minimal and native v0.2 documents stay unchanged", "generated:" not in minimal_file.read_text(encoding="utf-8") and native_file.read_text(encoding="utf-8").count("generated:") == 1)
        expect("migrated repository passes official v0.2", run(VALIDATE, legacy, "--profile", "okf").returncode == 0)

        touch = temp / "touch"
        touch.mkdir()
        touched_body = b"# Touched\r\n\r\nBody stays byte-identical.\r\n"
        touched_legacy = touch / "legacy.md"
        touched_legacy.write_bytes(
            b"---\r\ntype: Research Note\r\ntitle: Touched legacy\r\n"
            b"description: Lazy migration fixture\r\ntags: [lazy-migration, okf]\r\n"
            b"timestamp: 2025-01-01T00:00:00+00:00\r\n---\r\n"
            + touched_body
        )
        touched_native = touch / "native.md"
        touched_native.write_text(
            "---\ntype: Analysis\ntitle: Native\ndescription: Native refresh fixture\n"
            f"tags: [native-refresh, okf]\ngenerated: {{\"by\": \"{ACTOR}\", "
            "\"at\": \"2025-01-01T00:00:00+00:00\"}\n---\n# Native\n",
            encoding="utf-8",
        )
        touch_before = touched_legacy.read_bytes()
        touch_no_actor = run(INSERT, touch, "--touch", "legacy.md")
        expect(
            "touch requires a truthful actor",
            touch_no_actor.returncode != 0 and touched_legacy.read_bytes() == touch_before,
            touch_no_actor,
        )
        touch_dry = run(
            INSERT,
            touch,
            "--touch",
            "legacy.md",
            "native.md",
            "--actor",
            ACTOR,
            "--dry-run",
        )
        expect(
            "touch dry-run previews lazy migration without writing",
            touch_dry.returncode == 0
            and "would migrate: legacy.md" in touch_dry.stdout
            and "would refresh: native.md" in touch_dry.stdout
            and touched_legacy.read_bytes() == touch_before,
            touch_dry,
        )
        touched = run(
            INSERT,
            touch,
            "--touch",
            "legacy.md",
            "native.md",
            "--actor",
            ACTOR,
        )
        touched_text = touched_legacy.read_text(encoding="utf-8")
        expect(
            "touch migrates only named legacy files and refreshes native files",
            touched.returncode == 0
            and "migrated: legacy.md" in touched.stdout
            and "refreshed: native.md" in touched.stdout
            and f'"by": "{ACTOR}"' in touched_text
            and "timestamp:" in touched_text
            and "2025-01-01T00:00:00+00:00" not in touched_text
            and touched_legacy.read_bytes().endswith(touched_body)
            and run(VALIDATE, touch).returncode == 0,
            touched,
        )

        touch_readme = touch / "README.md"
        touch_readme.write_text(
            "---\ntype: Dossier\ntitle: Entry\ndescription: Explicit README fixture\n"
            "tags: [entry-point, okf]\ntimestamp: 2025-01-01T00:00:00+00:00\n"
            "---\n# Entry\n",
            encoding="utf-8",
        )
        touched_readme = run(
            INSERT,
            touch,
            "--touch",
            "README.md",
            "--actor",
            ACTOR,
        )
        expect(
            "an explicitly named README can migrate lazily",
            touched_readme.returncode == 0
            and "generated:" in touch_readme.read_text(encoding="utf-8"),
            touched_readme,
        )
        touch_agents = touch / "AGENTS.md"
        touch_agents.write_text("# Instructions\n", encoding="utf-8")
        blocked_agents = run(
            INSERT,
            touch,
            "--touch",
            "AGENTS.md",
            "--actor",
            ACTOR,
            "--profile",
            "okf",
        )
        expect(
            "touch never treats repository instructions as concepts",
            blocked_agents.returncode != 0
            and "instruction files" in blocked_agents.stdout + blocked_agents.stderr,
            blocked_agents,
        )

        touch_atomic = temp / "touch-atomic"
        touch_atomic.mkdir()
        touch_good = touch_atomic / "good.md"
        touch_good.write_text(
            "---\ntype: Note\ntimestamp: 2025-01-01T00:00:00+00:00\n---\n# Good\n",
            encoding="utf-8",
        )
        (touch_atomic / "bad.md").write_text("# Missing frontmatter\n", encoding="utf-8")
        touch_good_before = touch_good.read_bytes()
        touch_blocked = run(
            INSERT,
            touch_atomic,
            "--touch",
            "good.md",
            "bad.md",
            "--actor",
            ACTOR,
            "--profile",
            "okf",
        )
        expect(
            "touch validates every named file before writing any file",
            touch_blocked.returncode != 0 and touch_good.read_bytes() == touch_good_before,
            touch_blocked,
        )

        drop = temp / "drop-legacy"
        drop.mkdir()
        drop_file = drop / "drop.md"
        drop_file.write_text("---\ntype: Note\ntimestamp: '2026-01-01T00:00:00+00:00'\n---\n# Drop\n", encoding="utf-8")
        drop_inventory_path = temp / "drop-inventory.json"
        inventory(drop, drop_inventory_path)
        dropped = run(
            INSERT,
            drop,
            "--migrate-v01",
            "--apply",
            "--actor",
            "process:okf-migration",
            "--inventory",
            drop_inventory_path,
            "--drop-legacy-timestamp",
            "--profile",
            "okf",
        )
        expect("dropping legacy timestamp requires an explicit flag", dropped.returncode == 0 and "timestamp:" not in drop_file.read_text(encoding="utf-8"), dropped)

        duplicate = temp / "duplicate"
        duplicate.mkdir()
        (duplicate / "duplicate.md").write_text(
            "---\ntype: Reference\ncustom:\n  - owner: first\n    owner: second\n---\n# Duplicate\n",
            encoding="utf-8",
        )
        duplicate_result = run(VALIDATE, duplicate, "--profile", "okf")
        expect("nested duplicate YAML key is rejected", duplicate_result.returncode != 0 and "duplicate key" in duplicate_result.stdout, duplicate_result)

        drift = temp / "drift"
        drift.mkdir()
        drift_file = drift / "edit.md"
        drift_file.write_text("# Edit\n", encoding="utf-8")
        drift_inventory_path = temp / "drift-inventory.json"
        inventory(drift, drift_inventory_path)
        drift_file.write_text("# User edit\n", encoding="utf-8")
        drift_manifest = temp / "drift-manifest.json"
        write_manifest(drift_manifest, {"edit.md": meta("Edit", "Drift fixture")})
        drift_apply = run(
            INSERT,
            drift,
            "--manifest",
            drift_manifest,
            "--inventory",
            drift_inventory_path,
            "--actor",
            ACTOR,
        )
        expect("post-inventory body drift blocks apply", drift_apply.returncode != 0 and "# User edit" in drift_file.read_text(encoding="utf-8"), drift_apply)
        deleted = temp / "deleted"
        deleted.mkdir()
        deleted_file = deleted / "gone.md"
        deleted_file.write_text("# Gone\n", encoding="utf-8")
        deleted_inventory = temp / "deleted-inventory.json"
        inventory(deleted, deleted_inventory)
        deleted_file.unlink()
        deleted_manifest = temp / "deleted-manifest.json"
        write_manifest(deleted_manifest, {"gone.md": meta("Gone", "Deleted fixture")})
        deleted_apply = run(
            INSERT,
            deleted,
            "--manifest",
            deleted_manifest,
            "--inventory",
            deleted_inventory,
            "--actor",
            ACTOR,
        )
        expect(
            "deleted inventory targets fail cleanly",
            deleted_apply.returncode != 0 and "outside concept scope" in deleted_apply.stdout + deleted_apply.stderr,
            deleted_apply,
        )

        stale_migration = temp / "stale-migration"
        stale_migration.mkdir()
        stale_file = stale_migration / "legacy.md"
        stale_file.write_text(
            "---\ntype: Note\ntimestamp: 2026-01-01T00:00:00+00:00\n---\n# Legacy\n",
            encoding="utf-8",
        )
        stale_inventory = temp / "stale-migration-inventory.json"
        inventory(stale_migration, stale_inventory)
        stale_file.write_text(
            "---\ntype: Note\ntimestamp: 2026-01-02T00:00:00+00:00\n---\n# Legacy\n",
            encoding="utf-8",
        )
        stale_apply = run(
            INSERT,
            stale_migration,
            "--migrate-v01",
            "--apply",
            "--profile",
            "okf",
            "--actor",
            ACTOR,
            "--inventory",
            stale_inventory,
        )
        expect(
            "migration rejects stale inventory without overwriting current content",
            stale_apply.returncode != 0
            and "frontmatter changed since inventory" in stale_apply.stdout + stale_apply.stderr
            and "2026-01-02" in stale_file.read_text(encoding="utf-8"),
            stale_apply,
        )

        plain = temp / "plain-migration"
        plain.mkdir()
        plain_file = plain / "plain.md"
        plain_file.write_text("# Plain\n", encoding="utf-8")
        plain_audit = run(INSERT, plain, "--migrate-v01", "--profile", "okf")
        expect(
            "frontmatter-less Markdown is a visible migration skip",
            plain_audit.returncode == 0 and "SKIP plain.md: no frontmatter" in plain_audit.stdout,
            plain_audit,
        )
        plain_inventory = temp / "plain-inventory.json"
        inventory(plain, plain_inventory)
        plain_apply = run(
            INSERT,
            plain,
            "--migrate-v01",
            "--apply",
            "--profile",
            "okf",
            "--actor",
            ACTOR,
            "--inventory",
            plain_inventory,
        )
        expect(
            "apply does not claim a skipped bundle was migrated",
            plain_apply.returncode != 0
            and "migration incomplete" in plain_apply.stdout + plain_apply.stderr
            and plain_file.read_text(encoding="utf-8") == "# Plain\n",
            plain_apply,
        )

        invalid_migration = temp / "invalid-migration"
        invalid_migration.mkdir()
        (invalid_migration / "bad.md").write_text(
            "---\ntype: Note\ntimestamp: yesterday\ngenerated:\n  by: forged\n  at: never\n---\n# Bad\n",
            encoding="utf-8",
        )
        invalid_audit = run(INSERT, invalid_migration, "--migrate-v01", "--profile", "okf")
        expect(
            "migration audit validates present v0.1 and v0.2 metadata",
            invalid_audit.returncode != 0
            and "timestamp must be ISO 8601" in invalid_audit.stdout
            and "generated.by" in invalid_audit.stdout,
            invalid_audit,
        )

        symlink_root = temp / "symlink"
        symlink_root.mkdir()
        outside = temp / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        linked = symlink_root / "linked.md"
        linked.symlink_to(outside)
        symlink_inventory = temp / "symlink-inventory.json"
        inventory(symlink_root, symlink_inventory)
        symlink_manifest = temp / "symlink-manifest.json"
        write_manifest(symlink_manifest, {"linked.md": meta("Linked", "Symlink fixture")})
        symlink_apply = run(
            INSERT,
            symlink_root,
            "--manifest",
            symlink_manifest,
            "--inventory",
            symlink_inventory,
            "--actor",
            ACTOR,
        )
        expect(
            "manifest mutation rejects actual symlink targets",
            symlink_apply.returncode != 0
            and "symlink" in symlink_apply.stdout + symlink_apply.stderr
            and outside.read_text(encoding="utf-8") == "# Outside\n",
            symlink_apply,
        )
        forged_inventory_data = json.loads(symlink_inventory.read_text(encoding="utf-8"))
        forged_inventory_data["files"]["../outside.md"] = forged_inventory_data["files"]["linked.md"]
        forged_inventory_path = temp / "forged-inventory.json"
        forged_inventory_path.write_text(json.dumps(forged_inventory_data), encoding="utf-8")
        forged_manifest = temp / "forged-manifest.json"
        write_manifest(forged_manifest, {"../outside.md": meta("Outside", "Forged path fixture")})
        forged_apply = run(
            INSERT,
            symlink_root,
            "--manifest",
            forged_manifest,
            "--inventory",
            forged_inventory_path,
            "--actor",
            ACTOR,
        )
        expect(
            "forged outside-root inventory paths cannot authorize mutation",
            forged_apply.returncode != 0
            and "outside concept scope" in forged_apply.stdout + forged_apply.stderr
            and outside.read_text(encoding="utf-8") == "# Outside\n",
            forged_apply,
        )

        hidden_bundle = temp / "hidden-bundle"
        hidden_bundle.mkdir()
        hidden_index = hidden_bundle / "index.md"
        hidden_index.write_text("# Sections\n\n* [Visible](visible.md) - Visible.\n", encoding="utf-8")
        (hidden_bundle / "visible.md").write_text("---\ntype: Note\n---\n# Visible\n", encoding="utf-8")
        (hidden_bundle / ".hidden.md").write_text("# Hidden invalid\n", encoding="utf-8")
        hidden_before = hidden_index.read_bytes()
        hidden_declare = run(
            INSERT,
            hidden_bundle,
            "--declare-version",
            "0.2",
            "--whole-bundle",
            "--apply",
        )
        expect(
            "hidden invalid concept blocks full-bundle declaration unchanged",
            hidden_declare.returncode != 0 and hidden_index.read_bytes() == hidden_before,
            hidden_declare,
        )
        excluded_declare = run(
            INSERT,
            hidden_bundle,
            "--declare-version",
            "0.2",
            "--whole-bundle",
            "--apply",
            "--exclude",
            ".hidden.md",
        )
        expect(
            "declaration rejects exclusions instead of skipping a subtree",
            excluded_declare.returncode != 0
            and "rejects --exclude" in excluded_declare.stdout + excluded_declare.stderr
            and hidden_index.read_bytes() == hidden_before,
            excluded_declare,
        )

        symlink_index_bundle = temp / "symlink-index"
        symlink_index_bundle.mkdir()
        real_index = temp / "real-index.md"
        real_index.write_text("# Sections\n\n* [Note](note.md) - Note.\n", encoding="utf-8")
        (symlink_index_bundle / "index.md").symlink_to(real_index)
        (symlink_index_bundle / "note.md").write_text("---\ntype: Note\n---\n# Note\n", encoding="utf-8")
        index_link_declare = run(
            INSERT,
            symlink_index_bundle,
            "--declare-version",
            "0.2",
            "--whole-bundle",
            "--apply",
        )
        expect(
            "root index mutation rejects symlinks",
            index_link_declare.returncode != 0
            and "symlink" in index_link_declare.stdout + index_link_declare.stderr
            and real_index.read_text(encoding="utf-8").startswith("# Sections"),
            index_link_declare,
        )

    print("PASS: OKF v0.2 and v0.1 compatibility regression scenarios")


if __name__ == "__main__":
    main()
