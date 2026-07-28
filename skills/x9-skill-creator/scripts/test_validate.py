#!/usr/bin/env python3
"""Regression checks for the strict skill validator."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

VALIDATOR = Path(__file__).with_name("validate.py")
SKILL_ROOT = Path(__file__).parent.parent
SKILL_FILE = SKILL_ROOT / "SKILL.md"
REPORTING = SKILL_ROOT / "references" / "audit-reporting.md"
BATCH_AUDIT = SKILL_ROOT / "references" / "batch-audit.md"


def run(root: Path, *runtimes: str):
    command = [sys.executable, str(VALIDATOR)]
    for runtime in runtimes:
        command.extend(["--runtime", runtime])
    command.append(str(root))
    return subprocess.run(command, capture_output=True, text=True)


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
        no_ruby = subprocess.run(
            [sys.executable, str(VALIDATOR), str(healthy)],
            capture_output=True,
            text=True,
            env={**os.environ, "PATH": ""},
        )
        expect(
            "missing Ruby/Psych is explicit",
            no_ruby.returncode != 0 and "Ruby/Psych is required" in no_ruby.stdout,
            no_ruby.stdout,
        )

        malformed = base / "malformed"
        skill(malformed, 'name: malformed\ndescription: "unterminated')
        expect("malformed YAML", run(malformed).returncode != 0, run(malformed).stdout)

        duplicate = base / "duplicate"
        skill(duplicate, "name: duplicate\nname: second\ndescription: Use when testing. Do not use otherwise.")
        expect("duplicate key", run(duplicate).returncode != 0, run(duplicate).stdout)

        indented_duplicate = base / "indented-duplicate"
        skill(
            indented_duplicate,
            " name: indented-duplicate\n name: second\n description: Use when testing. Do not use otherwise.",
        )
        result = run(indented_duplicate)
        expect(
            "indented duplicate key",
            result.returncode != 0 and "duplicate YAML key" in result.stdout,
            result.stdout,
        )

        nested_duplicate = base / "nested-duplicate"
        skill(
            nested_duplicate,
            "name: nested-duplicate\ndescription: Use when testing. Do not use otherwise.\n"
            "metadata:\n  version: one\n  version: two",
        )
        result = run(nested_duplicate)
        expect(
            "nested duplicate key",
            result.returncode != 0 and "metadata.version" in result.stdout,
            result.stdout,
        )

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

        compatibility = base / "compatibility"
        skill(
            compatibility,
            f"name: compatibility\ndescription: Use when testing. Do not use otherwise.\ncompatibility: {'x' * 501}",
        )
        result = run(compatibility)
        expect(
            "portable compatibility limit",
            result.returncode != 0 and "exceeds 500" in result.stdout,
            result.stdout,
        )

        metadata = base / "metadata"
        skill(
            metadata,
            "name: metadata\ndescription: Use when testing. Do not use otherwise.\nmetadata:\n  version: 1",
        )
        result = run(metadata)
        expect(
            "portable metadata string values",
            result.returncode != 0 and "must be strings" in result.stdout,
            result.stdout,
        )

        claude = base / "claude"
        skill(
            claude,
            "name: claude\ndescription: Use when testing. Do not use otherwise.\n"
            "context: fork\nbackground: false\nallowed-tools:\n  - Read\n  - Grep",
        )
        expect(
            "Claude extensions pass Claude profile",
            run(claude, "claude").returncode == 0,
            run(claude, "claude").stdout,
        )
        result = run(claude, "portable")
        expect(
            "Claude extensions fail portable profile",
            result.returncode != 0 and "unsupported for portable" in result.stdout,
            result.stdout,
        )

        codex = base / "codex"
        skill(codex, "description: Use when testing. Do not use otherwise.")
        expect(
            "Codex can derive a missing name",
            run(codex, "codex").returncode == 0,
            run(codex, "codex").stdout,
        )
        result = run(codex, "portable")
        expect(
            "portable profile requires name",
            result.returncode != 0 and "required for portable: name" in result.stdout,
            result.stdout,
        )

        nested = base / "nested"
        skill(
            nested,
            "name: nested\ndescription: Use when testing. Do not use otherwise.",
            "# Nested\nUse assets/template/site/index.html.\n",
        )
        nested_asset = nested / "assets" / "template" / "site"
        nested_asset.mkdir(parents=True)
        (nested_asset / "index.html").write_text("<p>ok</p>\n", encoding="utf-8")
        expect("referenced nested asset", run(nested).returncode == 0, run(nested).stdout)

        orphan_script = base / "orphan-script"
        skill(orphan_script, "name: orphan-script\ndescription: Use when testing. Do not use otherwise.")
        scripts = orphan_script / "scripts"
        scripts.mkdir()
        (scripts / "unused.py").write_text("print('unused')\n", encoding="utf-8")
        result = run(orphan_script)
        expect("orphan script", result.returncode != 0 and "orphan resource" in result.stdout, result.stdout)

        reachable_script = base / "reachable-script"
        skill(
            reachable_script,
            "name: reachable-script\ndescription: Use when testing. Do not use otherwise.",
            "# Reachable\nRun scripts/useful.py.\n",
        )
        scripts = reachable_script / "scripts"
        scripts.mkdir()
        (scripts / "useful.py").write_text("print('useful')\n", encoding="utf-8")
        expect("reachable script", run(reachable_script).returncode == 0, run(reachable_script).stdout)

        script_dependency = base / "script-dependency"
        skill(
            script_dependency,
            "name: script-dependency\ndescription: Use when testing. Do not use otherwise.",
            "# Dependency\nRun scripts/main.py.\n",
        )
        scripts = script_dependency / "scripts"
        scripts.mkdir()
        (scripts / "main.py").write_text("from helper import VALUE\nprint(VALUE)\n", encoding="utf-8")
        (scripts / "helper.py").write_text("VALUE = 'ok'\n", encoding="utf-8")
        expect("script dependency is reachable", run(script_dependency).returncode == 0, run(script_dependency).stdout)

    skill_text = SKILL_FILE.read_text(encoding="utf-8")
    reporting_text = REPORTING.read_text(encoding="utf-8")
    batch_text = BATCH_AUDIT.read_text(encoding="utf-8")
    table_header = "| Skill | Status | Severity | Area | Finding | Evidence / impact | Recommendation | Decision | Full report |"
    for label, fragment, text in (
        ("core links the audit reporting contract", "references/audit-reporting.md", skill_text),
        ("core requires the instruction rubric", "load and apply `x9-agent-instructions`", skill_text),
        ("core degrades when the instruction rubric is unavailable", "instruction rubric as `degraded`", skill_text),
        ("reporting defines the complete findings table", table_header, reporting_text),
        ("report language follows explicit user choice", "language explicitly requested by the user", reporting_text),
        ("report language falls back to request carrier language", "primary carrier language of the audit request", reporting_text),
        ("report language does not follow the target", "Never derive the report language from the audited skill", reporting_text),
        ("persistent reports record one language tag", "Report language: <tag>", reporting_text),
        ("persistent reports localize prose and labels", "Localize the human-facing labels", reporting_text),
        ("reporting accounts for clean targets", "No retained findings", reporting_text),
        ("reporting retains every severity", "Blocker, Important, and Minor", reporting_text),
        ("reporting assigns stable finding identifiers", "stable identifier such as `F1`", reporting_text),
        ("reporting explains why every change helps", "Why these changes help", reporting_text),
        ("reporting limits explanation length", "no more than two short sentences", reporting_text),
        ("degraded status has precedence", "`degraded` takes precedence", reporting_text),
        ("batch requires reading every worker report", "Read every complete worker report", batch_text),
        ("batch loads the instruction rubric", "Load and apply `x9-agent-instructions`", batch_text),
        ("batch reports instruction-rubric coverage", "Instruction rubric: applied|not applicable|degraded", batch_text),
        ("batch writes a consolidated report", "summary.md", batch_text),
        ("batch assigns one report language", "pass its exact `Report language: <tag>` to every worker", batch_text),
        ("workers must not infer another language", "Do not infer another language from the target", batch_text),
        ("worker responses return the report language", "Report language: <tag>", batch_text),
        ("orchestrator verifies report language", "Verify that every report records the assigned `Report language: <tag>`", batch_text),
        ("batch uses the canonical localized verdict block", "localized persistent-report verdict block defined by [audit reporting](audit-reporting.md)", batch_text),
        ("batch final response uses the complete table", table_header, batch_text),
    ):
        expect(label, fragment in text)

    expect("batch links the canonical judge checklist", "[quality-rubric.md](quality-rubric.md)" in batch_text)
    expect("batch does not copy judge checklist cardinality", "8-item judge checklist" not in batch_text)
    result = run(SKILL_ROOT, "portable", "claude", "codex")
    expect("creator validates for all declared runtimes", result.returncode == 0, result.stdout)

    print("PASS: validator regression scenarios")


if __name__ == "__main__":
    main()
