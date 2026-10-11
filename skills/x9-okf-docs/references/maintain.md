# Write and maintain documents

## Repository instructions

Read the applicable `AGENTS.md` once. If it says the repository does not use OKF or excludes this skill, write no metadata and stop this route.

If its OKF section pins a version, copies field rules, or names script options this skill no longer has, replace only that section with a pointer to `x9-okf-docs` through `x9-context-files-generator`, keeping the repository's scope, exclusions, and log conventions. Never edit text between another skill's markers, such as `<!-- x9-personal-vault:start -->` and its end marker; report the conflict instead. Without the companion skill, continue the document work and report the instructions as not updated.

## New document

Write the header by hand with the body, following [the contract](okf-format.md). Then check it:

```bash
python3 <skill-directory>/scripts/validate_okf.py <root> --paths <path>
```

## Edited document

After a substantive edit, reread `description`, `title`, and `tags` and correct any that no longer fit; touch nothing else in the header. Run the same check when the header changed. Reading a document, fixing a link, or formatting never changes its header.

## Completion

Only the named documents changed, plus a stale OKF section of `AGENTS.md` when one was repaired, and the check passes.
