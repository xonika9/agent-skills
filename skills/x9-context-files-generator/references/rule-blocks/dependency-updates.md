<!-- x9-context-files-generator:dependency-updates:start -->
## Dependency updates

Shared rules from the `x9-context-files-generator` template. Edit only Local, which takes precedence; the rest is replaced when the template changes.

- The update bot named in Local owns updates for every active dependency. Do not add package-specific update exclusions or a parallel manual update track; related dependencies may be grouped.
- Dependency declarations use the range style in Local. Lockfiles, package-manager pins, and image digests stay exact and move in the same update pull request.
- A new nonstandard active version literal gains update-bot extraction and update-workflow coverage in the same change. A path trigger alone is not coverage: the workflow must exercise the affected runtime or service behavior.
- Historical plans, research and evidence, archives, and provenance are not update targets.
- Update pull requests may merge automatically only after their checks pass; revert the pull request if a regression escapes those checks.

### Local

- Update bot and its configuration: <such as Renovate in `renovate.json5`>
- Range style: <such as `^` ranges for npm declarations>
- Workflow that verifies update pull requests: <path>
- Check after changing dependency declarations, image references, lock generation, or update coverage: <command>
<!-- x9-context-files-generator:dependency-updates:end -->
