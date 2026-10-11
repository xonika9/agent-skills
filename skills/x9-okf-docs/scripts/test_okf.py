#!/usr/bin/env python3
"""Regression checks for the x9 OKF contract and its byte-preserving writers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
INSERT = HERE / "insert_frontmatter.py"
VALIDATE = HERE / "validate_okf.py"
DEPENDENCIES = HERE / "check_dependencies.py"
BOM = b"\xef\xbb\xbf"


def run(*args):
    return subprocess.run(
        [sys.executable, "-B", *map(str, args)],
        capture_output=True,
        text=True,
    )


def expect(label: str, condition: bool, result=None):
    if not condition:
        detail = "" if result is None else result.stdout + result.stderr
        raise AssertionError(f"{label}\n{detail}")


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def doc(type_="Note", description="A test document", extra=""):
    return f'---\ntype: "{type_}"\ndescription: "{description}"\n{extra}---\n# Body\n'


def fails_with(root: Path, text: str, *args):
    result = run(VALIDATE, root, *args)
    return result.returncode != 0 and text in result.stdout, result


def writer_checks():
    import insert_frontmatter

    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        first, second = temp / "first.md", temp / "second.md"
        first.write_bytes(b"one\n")
        second.write_bytes(b"two\n")
        try:
            insert_frontmatter.atomic_replace_many([("first.md", first, b"stale\n", b"new\n")])
            raise AssertionError("a file changed during the run must block the write")
        except SystemExit as exc:
            expect("a concurrent change blocks the write", "changed during the run" in str(exc) and first.read_bytes() == b"one\n")

        real_replace = insert_frontmatter.os.replace
        calls = []

        def failing_replace(source, target):
            calls.append(target)
            if len(calls) == 2:
                raise OSError("simulated failure")
            return real_replace(source, target)

        insert_frontmatter.os.replace = failing_replace
        try:
            insert_frontmatter.atomic_replace_many([
                ("first.md", first, b"one\n", b"new one\n"),
                ("second.md", second, b"two\n", b"new two\n"),
            ])
            raise AssertionError("a failed replacement must raise")
        except OSError:
            pass
        finally:
            insert_frontmatter.os.replace = real_replace
        expect(
            "a failed write rolls back files already replaced",
            first.read_bytes() == b"one\n" and second.read_bytes() == b"two\n"
            and sorted(path.name for path in temp.iterdir()) == ["first.md", "second.md"],
        )


def main():
    deps = run(DEPENDENCIES)
    expect("dependency check passes on this machine", deps.returncode == 0 and "PASS: Ruby Psych" in deps.stdout, deps)

    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)

        # Field contract.
        fields = temp / "fields"
        write(fields / "minimal.md", doc())
        write(fields / "full.md", doc(description="Full", extra='title: "Full"\ntags: ["health", "video-ideas"]\n'))
        write(fields / "extra.md", doc(description="Extra", extra="state: active\ncreated: 2024-01-05\nwhen: 2024-01-05 10:00:00\ngenerated: { by: \"human:x\", at: \"2026-01-01T00:00:00Z\" }\n"))
        ok = run(VALIDATE, fields)
        expect("type and description suffice; unknown fields and dates are accepted", ok.returncode == 0 and "problems: 0" in ok.stdout, ok)

        cases = {
            "no-description.md": ('---\ntype: "Note"\n---\n# Body\n', "missing description"),
            "no-type.md": ('---\ndescription: "No type"\n---\n# Body\n', "missing type"),
            "no-header.md": ("# Body\n", "no frontmatter"),
            "russian-tags.md": (doc(description="Ru", extra="tags: [здоровье]\n"), "English kebab-case"),
            "many-tags.md": (doc(description="Many", extra="tags: [a, b, c, d, e, f]\n"), "at most 5"),
            "empty-title.md": (doc(description="Empty", extra='title: ""\n'), "title must be a non-empty string"),
            "duplicate.md": ('---\ntype: Note\ntype: Other\ndescription: "Dup"\n---\n', "duplicate key"),
            "multiline.md": ('---\ntype: Note\ndescription: |\n  one\n  two\n---\n', "one line"),
        }
        for name, (text, message) in cases.items():
            case_root = temp / "case" / name.replace(".md", "")
            write(case_root / name, text)
            failed, result = fails_with(case_root, message)
            expect(f"validator rejects {name}", failed, result)

        flow = temp / "flow"
        write(flow / "colon.md", doc(extra="generated: { by: human:sample, at: 2026-01-01T00:00:00Z }\n"))
        flow_result = run(VALIDATE, flow)
        expect(
            "an unreadable flow value is reported, never a traceback",
            "Traceback" not in flow_result.stderr
            and (flow_result.returncode == 0 or "quote that value" in flow_result.stdout),
            flow_result,
        )

        same = temp / "same"
        write(same / "a.md", doc(description="Same"))
        write(same / "b.md", doc(description="Same"))
        same_result = run(VALIDATE, same)
        expect("a repeated description is a warning", same_result.returncode == 0 and "WARN" in same_result.stdout, same_result)

        reserved = temp / "reserved"
        write(reserved / "index.md", '---\nokf_version: "0.2"\n---\n# Sections\n')
        write(reserved / "topic" / "log.md", "# Log\n\n## 2026-07-29\n- Current.\n\n## 2026-07-28\n- Started.\n")
        write(reserved / "topic" / "note.md", doc())
        expect("index and log files follow their own rules", run(VALIDATE, reserved).returncode == 0)
        write(reserved / "topic" / "index.md", '---\ntype: Index\n---\n# Notes\n')
        failed, result = fails_with(reserved, "nested index.md")
        expect("a nested index.md must not have frontmatter", failed, result)
        (reserved / "topic" / "index.md").unlink()
        write(reserved / "index.md", "---\nokf_version: 0.2\n---\n# Sections\n")
        failed, result = fails_with(reserved, "quoted string")
        expect("an unquoted okf_version is explained", failed, result)
        write(reserved / "index.md", "# Sections\n")
        write(reserved / "topic" / "log.md", "---\ntype: Log\n---\n## 2026-07-28\n\n## 2026-07-29\n")
        failed, result = fails_with(reserved, "must not have frontmatter")
        expect("log.md frontmatter is rejected", failed and "newest first" in result.stdout, result)

        # Scope.
        scope = temp / "scope"
        write(scope / "AGENTS.md", "# Instructions\n")
        write(scope / "CLAUDE.md", "@AGENTS.md\n")
        write(scope / "README.md", "# Readme\n")
        write(scope / "Входящее" / "idea.md", "# Idea\n")
        write(scope / "Система" / "Шаблоны" / "Тема.md", "# Template\n")
        write(scope / "Система" / "Правила.md", "# Rules\n")
        write(scope / ".obsidian" / "hidden.md", "# Hidden\n")
        write(scope / "raw" / "dump.md", "# Raw\n")
        nfd_dir = unicodedata.normalize("NFD", "Архив")
        write(scope / nfd_dir / "old.md", "# Old\n")
        outside = temp / "outside"
        write(outside / "external.md", "# External\n")
        (scope / "Диск").symlink_to(outside, target_is_directory=True)
        (scope / "linked.md").symlink_to(outside / "external.md")
        listed = run(VALIDATE, scope, "--missing").stdout.split()
        expect(
            "defaults skip instruction files, README, hidden, raw, and links",
            "Система/Правила.md" in listed
            and "Входящее/idea.md" in listed
            and not any(item in listed for item in ("AGENTS.md", "CLAUDE.md", "README.md", "linked.md"))
            and not any(item.startswith((".obsidian", "raw/", "Диск/")) for item in listed),
            listed,
        )
        (scope / ".x9-okf.json").write_text(
            json.dumps({"exclude": ["входящее", "Система/Шаблоны", "Архив"], "include_readme": True}, ensure_ascii=False),
            encoding="utf-8",
        )
        listed = run(VALIDATE, scope, "--missing").stdout.split()
        expect(
            "policy file adds exclusions by name or path, ignoring case and Unicode form",
            "README.md" in listed
            and "Система/Правила.md" in listed
            and not any("Входящее" in item or "Шаблоны" in item or "old.md" in item for item in listed),
            listed,
        )
        (scope / ".x9-okf.json").write_text('{"exclude": "raw"}', encoding="utf-8")
        bad_policy = run(VALIDATE, scope)
        expect("a malformed policy is refused clearly", bad_policy.returncode != 0 and "must be a list" in bad_policy.stderr, bad_policy)
        (scope / ".x9-okf.json").unlink()

        # Adoption through inventory and manifest.
        root = temp / "docs"
        body = b"# Body\r\n\r\nKeep bytes.\r\n"
        (root).mkdir()
        (root / "plain.md").write_bytes(BOM + body)
        os.chmod(root / "plain.md", 0o640)
        custom_body = "# Custom\r".encode("utf-8")
        (root / "custom.md").write_bytes(
            "---\rcustom: |\r  before\r  ---\r  after\rвладелец: Алекс\rtitle: Old title\rtags: [здоровье, спорт]\r---\r".encode("utf-8")
            + custom_body
        )
        write(root / "kept.md", '---\ntype: Note\ntitle: Mine\ndescription: "Mine"\n---\n# Kept\n')
        nfd_name = unicodedata.normalize("NFD", "Йога.md")
        write(root / nfd_name, "# Yoga\n")
        write(root / "Входящее" / "idea.md", "# Idea\n")
        (root / ".x9-okf.json").write_text('{"exclude": ["Входящее"]}', encoding="utf-8")
        inventory_path = temp / "inventory.json"
        made = run(INSERT, root, "--inventory-out", inventory_path)
        expect("inventory written", made.returncode == 0 and inventory_path.exists(), made)

        manifest = temp / "manifest.json"
        manifest.write_text(json.dumps({
            "plain.md": {"type": "Note", "description": "Plain document", "title": "Plain", "confidence": "high"},
            "custom.md": {"type": "Note", "description": "Custom document", "title": "New title", "tags": ["health", "sport"]},
            "kept.md": {"type": "Note", "description": "Mine", "title": "Other"},
            unicodedata.normalize("NFC", "Йога.md"): {"type": "Note", "description": "Yoga"},
        }, ensure_ascii=False), encoding="utf-8")
        before = {path: path.read_bytes() for path in root.rglob("*.md")}
        dry = run(INSERT, root, "--manifest", manifest, "--inventory", inventory_path, "--dry-run")
        expect(
            "dry run reports replacements and writes nothing",
            dry.returncode == 0
            and 'replaced: custom.md tags: ["здоровье", "спорт"] -> ["health", "sport"]' in dry.stdout
            and "kept existing: custom.md title" in dry.stdout
            and "kept existing: kept.md title" in dry.stdout
            and all(path.read_bytes() == data for path, data in before.items()),
            dry,
        )
        applied = run(INSERT, root, "--manifest", manifest, "--inventory", inventory_path)
        expect("manifest applied", applied.returncode == 0, applied)
        plain = (root / "plain.md").read_bytes()
        expect("BOM and CRLF body preserved", plain.startswith(BOM + b"---\r\n") and plain.endswith(body), plain)
        expect("file mode preserved", (root / "plain.md").stat().st_mode & 0o777 == 0o640)
        custom = (root / "custom.md").read_bytes()
        expect(
            "unknown fields stay byte-identical, CR endings kept, invalid tags replaced, valid title kept",
            custom.endswith(b"---\r" + custom_body)
            and "владелец: Алекс\r".encode("utf-8") in custom
            and b"  ---\r" in custom
            and b"\n" not in custom
            and b'tags: ["health", "sport"]' in custom
            and b'title: "Old title"' in custom,
            custom,
        )
        expect("an unchanged valid header is left alone", (root / "kept.md").read_bytes() == before[root / "kept.md"])
        expect("a manifest key in another Unicode form reaches the file", b'description: "Yoga"' in (root / nfd_name).read_bytes())
        checked = run(VALIDATE, root, "--inventory", inventory_path)
        expect("adopted folder passes and bodies match the inventory", checked.returncode == 0, checked)

        replace_inventory = temp / "replace-inventory.json"
        run(INSERT, root, "--inventory-out", replace_inventory)
        manifest.write_text(json.dumps({"kept.md": {"type": "Note", "description": "Mine", "title": "Other"}}), encoding="utf-8")
        replaced = run(INSERT, root, "--manifest", manifest, "--inventory", replace_inventory, "--replace-existing")
        expect(
            "--replace-existing replaces valid values and names the old one",
            replaced.returncode == 0
            and 'replaced: kept.md title: "Mine" -> "Other"' in replaced.stdout
            and b'title: "Other"' in (root / "kept.md").read_bytes(),
            replaced,
        )

        refusals = {
            "extra field": ({"plain.md": {"type": "Note", "description": "x", "generated": {"by": "human:x"}}}, "may set only"),
            "out of scope": ({"Входящее/idea.md": {"type": "Note", "description": "x"}}, "not an OKF document in scope"),
            "bad value": ({"plain.md": {"type": "Note", "description": "x", "tags": ["Здоровье"]}}, "English kebab-case"),
        }
        fresh_inventory = temp / "fresh-inventory.json"
        run(INSERT, root, "--inventory-out", fresh_inventory)
        for label, (entries, message) in refusals.items():
            manifest.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
            result = run(INSERT, root, "--manifest", manifest, "--inventory", fresh_inventory)
            expect(f"manifest refused: {label}", result.returncode != 0 and message in result.stderr, result)

        atomic = temp / "atomic"
        write(atomic / "a.md", "# A\n")
        write(atomic / "b.md", "# B\n")
        atomic_inventory = temp / "atomic-inventory.json"
        run(INSERT, atomic, "--inventory-out", atomic_inventory)
        write(atomic / "b.md", "# B edited\n")
        manifest.write_text(json.dumps({
            "a.md": {"type": "Note", "description": "A"},
            "b.md": {"type": "Note", "description": "B"},
        }), encoding="utf-8")
        drift = run(INSERT, atomic, "--manifest", manifest, "--inventory", atomic_inventory)
        expect(
            "an edit after the inventory blocks the whole batch",
            drift.returncode != 0
            and "changed since the inventory" in drift.stderr
            and (atomic / "a.md").read_text(encoding="utf-8") == "# A\n",
            drift,
        )

        # Removing retired fields.
        retired = temp / "retired"
        write(retired / "a.md", '---\ntype: Note\ngenerated:\n  by: "human:x"\n  at: 2026-01-01T00:00:00Z\ndescription: "A"\ntimestamp: 2026-01-01T00:00:00Z\nstate: active\n---\n# A\n')
        write(retired / "b.md", "---\ngenerated: {by: \"human:x\", at: \"2026-01-01T00:00:00Z\"}\n---\n# B\n")
        write(retired / "c.md", '---\ntype: Note\ndescription: "C"\ntimestamp: 2026-01-01T00:00:00Z\n---\n# C\n')
        protected = run(INSERT, retired, "--remove-fields", "description")
        expect("required fields cannot be removed", protected.returncode != 0 and "cannot be removed" in protected.stderr, protected)
        limited = run(INSERT, retired, "--remove-fields", "timestamp", "--paths", "c.md")
        expect(
            "--paths limits removal",
            limited.returncode == 0
            and "timestamp" not in (retired / "c.md").read_text(encoding="utf-8")
            and "timestamp" in (retired / "a.md").read_text(encoding="utf-8"),
            limited,
        )
        removed = run(INSERT, retired, "--remove-fields", "generated", "timestamp")
        expect(
            "retired fields removed, other fields and bodies kept, empty header dropped",
            removed.returncode == 0
            and (retired / "a.md").read_text(encoding="utf-8") == '---\ntype: Note\ndescription: "A"\nstate: active\n---\n# A\n'
            and (retired / "b.md").read_text(encoding="utf-8") == "# B\n",
            removed,
        )

        # Headers that cannot be cut by lines are refused, never mangled.
        unsafe = temp / "unsafe"
        write(unsafe / "flow.md", '---\n{type: Note, description: "D", foo: z}\n---\n# Flow\n')
        write(unsafe / "sep.md", '---\ntype: Note\ndescription: "a\u2028b"\nstate: x\n# one\n# two\n---\n# Sep\n')
        unsafe_before = {path: path.read_bytes() for path in unsafe.iterdir()}
        for name, message in (("flow.md", "{ } style"), ("sep.md", "would not match")):
            refused = run(INSERT, unsafe, "--remove-fields", "foo", "state", "--paths", name)
            expect(
                f"an unsafe header is refused unchanged: {name}",
                refused.returncode != 0
                and message in refused.stderr
                and all(path.read_bytes() == data for path, data in unsafe_before.items()),
                refused,
            )

        comments = temp / "comments"
        write(comments / "c.md", "---\n# lead comment\ntype: Note\ngenerated:\n  by: x\n# about state below\nstate: x\ndescription: \"C\"\ntimestamp: 1\n# tail comment\n---\n# C\n")
        dry = run(INSERT, comments, "--remove-fields", "generated", "timestamp", "--dry-run")
        expect("removal dry run writes nothing", dry.returncode == 0 and "would change: c.md" in dry.stdout and "generated" in (comments / "c.md").read_text(encoding="utf-8"), dry)
        cleaned = run(INSERT, comments, "--remove-fields", "generated", "timestamp")
        expect(
            "comments around removed fields stay",
            cleaned.returncode == 0
            and (comments / "c.md").read_text(encoding="utf-8")
            == "---\n# lead comment\ntype: Note\n# about state below\nstate: x\ndescription: \"C\"\n# tail comment\n---\n# C\n",
            cleaned,
        )

        mixed = temp / "mixed"
        (mixed).mkdir()
        (mixed / "m.md").write_bytes(b"---\r\nstate: active\r\n---\r\n# Body\n\nLF body.\n")
        mixed_inventory = temp / "mixed-inventory.json"
        run(INSERT, mixed, "--inventory-out", mixed_inventory)
        manifest.write_text(json.dumps({"m.md": {"type": "Note", "description": "Mixed"}}), encoding="utf-8")
        mixed_apply = run(INSERT, mixed, "--manifest", manifest, "--inventory", mixed_inventory)
        mixed_bytes = (mixed / "m.md").read_bytes()
        expect(
            "header line endings come from the header, body bytes stay",
            mixed_apply.returncode == 0
            and b"state: active\r\n" in mixed_bytes
            and b'description: "Mixed"\r\n' in mixed_bytes
            and mixed_bytes.endswith(b"---\r\n# Body\n\nLF body.\n"),
            mixed_apply,
        )

        manifest.write_text(json.dumps([
            {"path": "m.md", "type": "Note", "description": "One"},
            {"path": "m.md", "type": "Note", "description": "Two"},
        ]), encoding="utf-8")
        repeated = run(INSERT, mixed, "--manifest", manifest, "--inventory", mixed_inventory)
        expect("a repeated manifest path is refused", repeated.returncode != 0 and "twice" in repeated.stderr, repeated)

        for label, text, message in (
            ("duplicate tags", doc(description="Dup tags", extra="tags: [health, health]\n"), "unique"),
            ("boolean tag", doc(description="Bool tag", extra="tags: [on, health]\n"), "true or false"),
        ):
            tag_root = temp / "tag" / label.replace(" ", "-")
            write(tag_root / "t.md", text)
            failed, result = fails_with(tag_root, message)
            expect(f"validator rejects {label}", failed, result)

        oddities = temp / "oddities"
        write(oddities / "symbol.md", doc(description="Symbol", extra="alias: :foo\n"))
        write(oddities / "agents.md", "# lower-case instructions\n")
        write(oddities / "readme.md", "# lower-case readme\n")
        odd = run(VALIDATE, oddities)
        expect("symbols are readable and instruction names ignore case", odd.returncode == 0 and "checked: 1 documents" in odd.stdout, odd)
        write(oddities / "empty.md", "---\n---\n# Empty\n")
        odd_inventory = temp / "odd-inventory.json"
        run(INSERT, oddities, "--inventory-out", odd_inventory)
        manifest.write_text(json.dumps({"empty.md": {"type": "Note", "description": "Empty header"}}), encoding="utf-8")
        empty_apply = run(INSERT, oddities, "--manifest", manifest, "--inventory", odd_inventory)
        expect("an empty header can be filled", empty_apply.returncode == 0 and b'type: "Note"' in (oddities / "empty.md").read_bytes(), empty_apply)

        linked_policy = temp / "linked-policy"
        write(linked_policy / "a.md", doc())
        write(temp / "policy-target.json", '{"exclude": ["Private"]}')
        (linked_policy / ".x9-okf.json").symlink_to(temp / "policy-target.json")
        linked = run(VALIDATE, linked_policy)
        expect("a linked policy file is refused", linked.returncode != 0 and "not a link" in linked.stderr, linked)

        anchored = temp / "anchored"
        write(anchored / "Архив" / "top.md", "# Top\n")
        write(anchored / "a" / "Архив" / "nested.md", "# Nested\n")
        (anchored / ".x9-okf.json").write_text('{"exclude": ["Архив/"]}', encoding="utf-8")
        listed = run(VALIDATE, anchored, "--missing").stdout.split()
        expect("an entry with / is a path from the root", listed == ["a/Архив/nested.md"], listed)

        broken = run(INSERT, root, "--inventory-out", temp / "no-such-dir" / "inventory.json")
        expect("an unwritable inventory path is explained", broken.returncode != 0 and "Traceback" not in broken.stderr and "cannot write inventory" in broken.stderr, broken)
        (temp / "bad-inventory.json").write_text('{"version": 5, "files": []}', encoding="utf-8")
        bad = run(INSERT, root, "--manifest", manifest, "--inventory", temp / "bad-inventory.json")
        bad_validate = run(VALIDATE, root, "--inventory", temp / "bad-inventory.json")
        expect(
            "a malformed inventory is explained",
            "Traceback" not in bad.stderr + bad_validate.stderr
            and "unsupported inventory" in bad.stderr
            and "unsupported inventory" in bad_validate.stderr,
            bad,
        )

        single = temp / "single"
        write(single / "new.md", doc(description="New"))
        write(single / "other.md", "# No header\n")
        one = run(VALIDATE, single, "--paths", "new.md")
        expect("--paths checks only the named document", one.returncode == 0 and "checked: 1 documents" in one.stdout, one)
        absolute = run(VALIDATE, single, "--paths", single / "new.md")
        expect("--paths accepts an absolute path inside the root", absolute.returncode == 0, absolute)
        new_inventory = temp / "single-inventory.json"
        run(INSERT, single, "--inventory-out", new_inventory)
        write(single / "later.md", doc(description="Later"))
        later = run(VALIDATE, single, "--paths", "new.md", "later.md", "--inventory", new_inventory)
        expect("a document created after the inventory is a warning", later.returncode == 0 and "new since the inventory" in later.stdout, later)

    writer_checks()
    print("PASS: x9 OKF contract, scope, adoption, and cleanup scenarios")


if __name__ == "__main__":
    main()
