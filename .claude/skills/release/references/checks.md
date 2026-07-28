# Release checks

Run from the repository root:

```bash
for skill in skills/*; do
  python3 skills/x9-skill-creator/scripts/validate.py \
    --runtime portable --runtime claude --runtime codex "$skill"
done

python3 skills/x9-skill-creator/scripts/test_validate.py
python3 skills/x9-agent-instructions/scripts/test_check_globals.py
python3 skills/x9-excalidraw-diagrams/scripts/test_check_scene.py
python3 skills/x9-okf-adapt/scripts/test_okf.py
python3 skills/x9-research/scripts/test_validate_html.py
python3 .claude/skills/release/scripts/check_global_files.py
python3 scripts/check_package.py
python3 scripts/check_public.py
python3 scripts/test_prepare_release.py
python3 scripts/prepare_release.py --check
claude plugin validate .claude-plugin/marketplace.json
claude plugin validate .claude-plugin/plugin.json
npx skills add . --list
git diff --check
```

Confirm that root `CLAUDE.md` contains exactly `@AGENTS.md` plus a final newline.

Resolve the installed `humanizer-ru` skill and its bundled `scripts/scan.py` from the live runtime, apply the skill to the final Russian documentation at documentation-level intensity, and run:

```bash
python3 <resolved-humanizer-ru-scan.py> README.ru.md
```

Run the scanner against the complete file even when `README.ru.md` is unchanged in the candidate. Review every result against the documentation genre and correct genuine findings without altering facts, commands, identifiers, links, or supported-behavior claims. If scanner dependencies are unavailable, install them only in an ephemeral environment and run the scanner there.

Record the exact commands and outcomes. If a required executable, dependency, credential, network route, or GitHub permission is unavailable, mark the gate blocked and name the missing prerequisite; do not silently skip the check.
