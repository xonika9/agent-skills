#!/usr/bin/env python3
"""Report the state of x9-context-files-generator rule blocks in an AGENTS.md file."""

import argparse
import difflib
import re
import sys
from pathlib import Path

SKILL = "x9-context-files-generator"
TEMPLATES = Path(__file__).resolve().parent.parent / "references" / "rule-blocks"
ORDER = [
    "execution",
    "sources-of-truth",
    "documentation",
    "dependency-updates",
    "interface-references",
    "compound-engineering",
]
PREDECESSORS = {"compound-engineering": "COMPOUND ENGINEERING POLICY"}
START = re.compile(r"^<!-- (?:(\S+):start|BEGIN (.+?)) -->$")
END = re.compile(r"^<!-- (?:(\S+):end|END (.+?)) -->$")


def shared_part(lines):
    for index, line in enumerate(lines):
        if line == "### Local":
            lines = lines[:index]
            break
    else:
        lines = lines[:-1]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


def marked_regions(lines):
    regions, stack, fence, code = [], [], None, set()
    list_indents = []
    paragraph = None
    for number, line in enumerate(lines, 1):
        line = line.expandtabs(4)
        indent = len(line) - len(line.lstrip(" "))
        if fence:
            char, length, margin = fence
            if not line.strip() or indent >= margin:
                code.add(number)
                if re.fullmatch(r" {0,3}" + re.escape(char) + r"{" + str(length) + r",} *", line[margin:]):
                    fence = None
                continue
            fence = None
        if not line.strip():
            paragraph = None
            continue
        while list_indents and indent < list_indents[-1]:
            list_indents.pop()
        base = list_indents[-1] if list_indents else 0
        context = tuple(list_indents)
        continuing = paragraph == context
        # Four columns beyond a list's content margin are code, not list rules.
        if indent >= base + 4 and not continuing:
            code.add(number)
            paragraph = None
            continue
        line = line[base:]
        if continuing and re.fullmatch(r" {0,3}(?:-+|=+) *", line):
            paragraph = None
            continue
        if re.fullmatch(r" {0,3}(?:(?:- *){3,}|(?:\* *){3,}|(?:_ *){3,})", line):
            paragraph = None
            continue
        item = re.match(r"^ {0,3}([-+*]|[0-9]{1,9}[.)])( +|$)", line)
        if item and continuing and (
            not line[item.end():].strip()
            or (item[1][0].isdigit() and int(item[1][:-1]) != 1)
        ):
            item = None
        if item:
            paragraph = None
            padding = len(item[2])
            content = item.end() - (padding - 1 if padding > 4 else 0)
            if not padding:
                content += 1
            list_indents.append(base + content)
            line = line[content:]
            if len(line) - len(line.lstrip(" ")) >= 4:
                code.add(number)
                continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if opening and not (opening[1][0] == "`" and "`" in opening[2]):
            fence = (opening[1][0], len(opening[1]), list_indents[-1] if list_indents else 0)
            code.add(number)
            paragraph = None
            continue
        start, end = START.match(line.strip()), END.match(line.strip())
        if start:
            stack.append((start.group(1) or start.group(2), number))
        elif end and stack and (end.group(1) or end.group(2)) == stack[-1][0]:
            name, opened = stack.pop()
            regions.append((name, opened, number))
        if not line.strip() or re.match(r"^ {0,3}(?:#{1,6}(?: |$)|>|<)", line):
            paragraph = None
        else:
            paragraph = tuple(list_indents)
    return sorted(regions, key=lambda region: region[1]), stack, code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agents_file", type=Path)
    parser.add_argument("--diff", action="store_true", help="print the shared-part diff of outdated blocks")
    args = parser.parse_args()

    try:
        lines = args.agents_file.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        sys.exit(f"cannot read {args.agents_file}: {error.strerror}")
    regions, unclosed, code = marked_regions(lines)
    failed = False
    for name, opened in unclosed:
        print(f"unclosed marker {name!r} at line {opened}")
        failed = failed or name.startswith(f"{SKILL}:")

    outer = [r for r in regions if not any(o[1] < r[1] and r[2] < o[2] for o in regions)]
    inside = code | {n for _, start, end in outer for n in range(start, end + 1)}

    for block in ORDER:
        template = (TEMPLATES / f"{block}.md").read_text(encoding="utf-8").splitlines()
        heading = template[1]
        found = [r for r in regions if r[0] == f"{SKILL}:{block}"]
        if len(found) > 1:
            print(f"{block}: duplicate (lines {', '.join(f'{s}-{e}' for _, s, e in found)})")
            failed = True
            continue
        if not found:
            notes = [f"section {heading!r} at line {n}" for n, line in enumerate(lines, 1)
                     if n not in code and line == heading]
            predecessor = PREDECESSORS.get(block)
            notes += [f"predecessor {name!r} at line {s}" for name, s, _ in regions if name == predecessor]
            print(f"{block}: absent" + (f" ({'; '.join(notes)})" if notes else ""))
            continue
        _, start, end = found[0]
        current = shared_part(lines[start - 1:end])
        expected = shared_part(template)
        if current == expected:
            print(f"{block}: current (lines {start}-{end})")
            continue
        print(f"{block}: outdated (lines {start}-{end})")
        if args.diff:
            for line in difflib.unified_diff(current, expected, "file", "template", lineterm=""):
                print(line)

    if outer:
        first_block = outer[0][1]
        late = [n for n, line in enumerate(lines, 1) if n > first_block and n not in inside and line.startswith("#")]
        if late:
            print(f"order: repository sections after the first marked block at lines {', '.join(map(str, late))}")
        own = [r[1] for r in outer if r[0].startswith(f"{SKILL}:")]
        foreign_after = [r[1] for r in outer if not r[0].startswith(f"{SKILL}:") and own and r[1] > min(own)]
        if foreign_after:
            print(f"order: other marked blocks after this skill's blocks at lines {', '.join(map(str, foreign_after))}")
        if not late and not foreign_after:
            print("order: repository rules precede marked blocks")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
