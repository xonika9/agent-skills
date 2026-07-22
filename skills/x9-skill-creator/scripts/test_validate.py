#!/usr/bin/env python3
"""Regression checks for the strict skill validator."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

VALIDATOR = Path(__file__).with_name("validate.py")
SKILL_ROOT = Path(__file__).parent.parent
SKILL_FILE = SKILL_ROOT / "SKILL.md"
REPORTING = SKILL_ROOT / "references" / "audit-reporting.md"
BATCH_AUDIT = SKILL_ROOT / "references" / "batch-audit.md"


def run(root: Path):
    return subprocess.run([sys.executable, str(VALIDATOR), str(root)], capture_output=True, text=True)


def skill(root: Path, frontmatter: str, body: str = "# Demo\n"):
    root.mkdir(parents=True)
    (root / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")


def expect(label: str, condition: bool, output: str = ""):
    if not condition:
        raise AssertionError(f"{label}\n{output}")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        healthy = base / "healthy"
        healthy.mkdir()
        (healthy / "SKILL.md").write_bytes(
            b"---\r\nname: healthy\r\ndescription: Use when testing. Do not use otherwise.\r\n---\r\n# Healthy\r\n"
        )
        expect("valid CRLF", run(healthy).returncode == 0, run(healthy).stdout)

        malformed = base / "malformed"
        skill(malformed, 'name: malformed\ndescription: "unterminated')
        expect("malformed YAML", run(malformed).returncode != 0, run(malformed).stdout)

        duplicate = base / "duplicate"
        skill(duplicate, "name: duplicate\nname: second\ndescription: Use when testing. Do not use otherwise.")
        expect("duplicate key", run(duplicate).returncode != 0, run(duplicate).stdout)

        typo = base / "typo"
        skill(typo, "name: typo\ndescription: Use when testing. Do not use otherwise.\ndisable-model-invocatoin: true")
        expect("unknown typo", run(typo).returncode != 0, run(typo).stdout)

        wrong_type = base / "wrong-type"
        skill(wrong_type, "name: wrong-type\ndescription: [not, a, string]")
        expect("wrong type", run(wrong_type).returncode != 0, run(wrong_type).stdout)

        junk = base / "junk"
        skill(junk, "name: junk\ndescription: Use when testing. Do not use otherwise.")
        (junk / ".DS_Store").write_bytes(b"junk")
        expect("hidden junk", run(junk).returncode != 0, run(junk).stdout)

        graph = base / "graph"
        skill(graph, "name: graph\ndescription: Use when testing. Do not use otherwise.", "# Graph\n[x](references/file(name).md)\n")
        refs = graph / "references"
        refs.mkdir()
        (refs / "file(name).md").write_text("# Linked\n", encoding="utf-8")
        (refs / "a.md").write_text("# A\n[b](b.md)\n", encoding="utf-8")
        (refs / "b.md").write_text("# B\n[a](a.md)\n", encoding="utf-8")
        result = run(graph)
        expect("balanced link resolves", "file(name).md" not in result.stdout, result.stdout)
        expect("unreachable reference cycle", result.returncode != 0 and "orphan reference" in result.stdout, result.stdout)

    skill_text = SKILL_FILE.read_text(encoding="utf-8")
    reporting_text = REPORTING.read_text(encoding="utf-8")
    batch_text = BATCH_AUDIT.read_text(encoding="utf-8")
    table_header = "| Skill | Status | Severity | Area | Finding | Evidence / impact | Recommendation | Decision | Full report |"
    for label, fragment, text in (
        ("core links the audit reporting contract", "references/audit-reporting.md", skill_text),
        ("reporting defines the complete findings table", table_header, reporting_text),
        ("reporting accounts for clean targets", "No retained findings", reporting_text),
        ("reporting retains every severity", "Blocker, Important, and Minor", reporting_text),
        ("batch requires reading every worker report", "Read every complete worker report", batch_text),
        ("batch writes a consolidated report", "summary.md", batch_text),
        ("batch records filtered QA claims", "Filtered out by orchestrator QA", batch_text),
        ("batch final response uses the complete table", table_header, batch_text),
    ):
        expect(label, fragment in text)

    print("PASS: validator regression scenarios")


if __name__ == "__main__":
    main()
