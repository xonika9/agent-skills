#!/usr/bin/env python3
"""Regression checks for OKF inventory, insertion, and validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
INSERT = HERE / "insert_frontmatter.py"
VALIDATE = HERE / "validate_okf.py"
BOM = b"\xef\xbb\xbf"


def run(*args):
    return subprocess.run([sys.executable, "-B", *map(str, args)], capture_output=True, text=True)


def meta(title: str, description: str):
    return {
        "type": "Research Note",
        "title": title,
        "description": description,
        "tags": ["okf-test", "metadata"],
        "timestamp": "2026-07-15T12:00:00+03:00",
    }


def expect(label: str, condition: bool, result=None):
    if not condition:
        detail = "" if result is None else result.stdout + result.stderr
        raise AssertionError(f"{label}\n{detail}")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        atomic_root = Path(tmp) / "atomic"
        atomic_root.mkdir()
        atomic_file = atomic_root / "a.md"
        atomic_file.write_text("# A\n", encoding="utf-8")
        atomic_inventory = Path(tmp) / "atomic-inventory.json"
        expect("atomic inventory created", run(INSERT, atomic_root, "--inventory-out", atomic_inventory).returncode == 0)
        atomic_manifest = Path(tmp) / "atomic-manifest.json"
        atomic_manifest.write_text(json.dumps({"a.md": meta("A", "Atomic preflight fixture"), "missing.md": meta("Missing", "Invalid late manifest fixture")}), encoding="utf-8")
        atomic_before = atomic_file.read_bytes()
        atomic_apply = run(INSERT, atomic_root, "--manifest", atomic_manifest, "--inventory", atomic_inventory)
        expect("preflight failure writes no earlier files", atomic_apply.returncode != 0 and atomic_file.read_bytes() == atomic_before, atomic_apply)

        invalid_manifest = Path(tmp) / "invalid-metadata-manifest.json"
        invalid = meta("A", "Invalid semantic metadata fixture")
        invalid["tags"] = ["Not Kebab"]
        invalid["timestamp"] = "yesterday"
        invalid_manifest.write_text(json.dumps({"a.md": invalid}), encoding="utf-8")
        invalid_apply = run(INSERT, atomic_root, "--manifest", invalid_manifest, "--inventory", atomic_inventory)
        expect("invalid metadata writes nothing", invalid_apply.returncode != 0 and atomic_file.read_bytes() == atomic_before, invalid_apply)

        drift_root = Path(tmp) / "drift"
        drift_root.mkdir()
        drift_file = drift_root / "edit.md"
        drift_file.write_text("""---
type: Analysis
title: Before
description: Header edit protection fixture
tags:
  - okf-test
  - drift
timestamp: '2026-07-15T12:00:00+03:00'
---
# Edit
""", encoding="utf-8")
        drift_inventory = Path(tmp) / "drift-inventory.json"
        expect("drift inventory created", run(INSERT, drift_root, "--inventory-out", drift_inventory).returncode == 0)
        drift_file.write_text(drift_file.read_text(encoding="utf-8").replace("title: Before", "title: User edit"), encoding="utf-8")
        drift_manifest = Path(tmp) / "drift-manifest.json"
        drift_manifest.write_text(json.dumps({"edit.md": meta("Manifest title", "Header edit protection fixture")}), encoding="utf-8")
        drift_apply = run(INSERT, drift_root, "--manifest", drift_manifest, "--inventory", drift_inventory)
        expect("post-inventory header edit blocks apply", drift_apply.returncode != 0 and "title: User edit" in drift_file.read_text(encoding="utf-8"), drift_apply)

        bom_root = Path(tmp) / "bom-drift"
        bom_root.mkdir()
        bom_file = bom_root / "bom.md"
        bom_file.write_bytes(BOM + b"# BOM\n")
        bom_inventory = Path(tmp) / "bom-inventory.json"
        expect("BOM inventory created", run(INSERT, bom_root, "--inventory-out", bom_inventory).returncode == 0)
        bom_file.write_bytes(b"# BOM\n")
        bom_manifest = Path(tmp) / "bom-manifest.json"
        bom_manifest.write_text(json.dumps({"bom.md": meta("BOM", "BOM drift protection fixture")}), encoding="utf-8")
        bom_apply = run(INSERT, bom_root, "--manifest", bom_manifest, "--inventory", bom_inventory)
        expect("post-inventory BOM drift blocks apply", bom_apply.returncode != 0 and not bom_file.read_bytes().startswith(BOM), bom_apply)

        root = Path(tmp) / "docs"
        root.mkdir()
        body = b"# Body\r\n\r\nKeep bytes.\r\n"
        (root / "doc.md").write_bytes(BOM + body)
        (root / "partial.md").write_bytes(b"---\ntype: Analysis\n---\n# Partial\n")
        (root / "AGENTS.md").write_text("# Config\n", encoding="utf-8")
        (root / "README.md").write_text("# Onboarding\n", encoding="utf-8")

        missing = run(VALIDATE, root, "--missing")
        expect("partial and absent headers enter worklist", missing.returncode == 0 and "doc.md" in missing.stdout and "partial.md" in missing.stdout and "README.md" not in missing.stdout, missing)

        included = run(VALIDATE, root, "--missing", "--include-readme")
        expect("README requires explicit inclusion", "README.md" in included.stdout, included)

        inventory = Path(tmp) / "inventory.json"
        created = run(INSERT, root, "--inventory-out", inventory)
        expect("inventory created", created.returncode == 0 and inventory.exists(), created)

        manifest = Path(tmp) / "manifest.json"
        manifest.write_text(json.dumps({
            "doc.md": meta("Body", "Primary byte-preservation fixture"),
            "partial.md": meta("Partial", "Partial-header repair fixture"),
        }), encoding="utf-8")
        applied = run(INSERT, root, "--manifest", manifest, "--inventory", inventory)
        expect("manifest applied", applied.returncode == 0, applied)
        expect("BOM and CRLF body preserved", (root / "doc.md").read_bytes().startswith(BOM) and (root / "doc.md").read_bytes().endswith(body))

        valid = run(VALIDATE, root, "--inventory", inventory)
        expect("complete OKF validates", valid.returncode == 0, valid)

        custom = root / "custom.md"
        custom.write_bytes("---\r\ncustom: |\r\n  before\r\n  ---\r\n  after\r\nowner: Alex\r\nвладелец: Алекс\r\ntimestamp: 2026-07-15T12:00:00+03:00\r\n---\r# Custom\r".encode("utf-8"))
        custom_inventory = Path(tmp) / "custom-inventory.json"
        expect("custom inventory created", run(INSERT, root, "--inventory-out", custom_inventory).returncode == 0)
        custom_manifest = Path(tmp) / "custom-manifest.json"
        custom_manifest.write_text(json.dumps({"custom.md": meta("Custom", "Unknown-field preservation fixture")}), encoding="utf-8")
        custom_applied = run(INSERT, root, "--manifest", custom_manifest, "--inventory", custom_inventory)
        expect("custom field apply succeeds", custom_applied.returncode == 0, custom_applied)
        custom_bytes = custom.read_bytes()
        expect("unknown fields, Unicode key, scalar delimiter, and CR endings preserved", b"owner: Alex\r" in custom_bytes and "владелец: Алекс\r".encode("utf-8") in custom_bytes and b"  ---\r" in custom_bytes and b"  after\r" in custom_bytes and b"\n" not in custom_bytes, custom_applied)

        unquoted = root / "unquoted.md"
        unquoted.write_text("""---
type: Reference
title: Unquoted time
description: Ruby timestamp parsing fixture
tags:
  - okf-test
  - timestamp
timestamp: 2026-07-15T12:00:00+03:00
---
# Time
""", encoding="utf-8")
        unquoted_time = run(VALIDATE, root)
        expect("unquoted ISO timestamp is accepted", unquoted_time.returncode == 0, unquoted_time)

        nozone = root / "nozone.md"
        nozone.write_text(unquoted.read_text(encoding="utf-8").replace("2026-07-15T12:00:00+03:00", "2026-07-15T12:00:00").replace("Unquoted time", "No-zone time").replace("Ruby timestamp parsing fixture", "Missing timezone rejection fixture"), encoding="utf-8")
        nozone_result = run(VALIDATE, root)
        expect("unquoted timestamp without timezone is rejected", nozone_result.returncode != 0 and "timestamp must be ISO 8601 with timezone" in nozone_result.stdout, nozone_result)
        nozone.unlink()

        nested_duplicate = root / "nested-duplicate.md"
        nested_duplicate.write_text("""---
type: Reference
title: Duplicate
description: Nested duplicate detection fixture
tags:
  - okf-test
  - duplicate
timestamp: '2026-07-15T12:00:00+03:00'
custom:
  - - owner: first
      owner: second
---
# Duplicate
""", encoding="utf-8")
        duplicate_result = run(VALIDATE, root)
        expect("nested duplicate YAML key is rejected", duplicate_result.returncode != 0 and "duplicate key" in duplicate_result.stdout, duplicate_result)

        (root / "partial.md").unlink()
        deleted = run(VALIDATE, root, "--inventory", inventory)
        expect("deleted inventoried file detected", deleted.returncode != 0 and "file missing after pre-edit inventory" in deleted.stdout, deleted)

        (root / "doc.md").write_bytes((root / "doc.md").read_bytes() + b"mutation\r\n")
        mutated = run(VALIDATE, root, "--inventory", inventory)
        expect("body mutation detected", mutated.returncode != 0 and "body_sha256 changed" in mutated.stdout, mutated)

    print("PASS: OKF regression scenarios")


if __name__ == "__main__":
    main()
