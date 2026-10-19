<!-- x9-context-files-generator:documentation:start -->
## Documentation discipline

Shared rules from the `x9-context-files-generator` template. Edit only Local, which takes precedence; the rest is replaced when the template changes.

- Keep accepted decisions, proposals, dated research, and archives visibly distinct. Do not silently modernize historical evidence.
- Keep README files navigational, requirements and architecture contractual, and research and evidence historical.
- Keep executable setup and verification details in scripts or CI. Add a command to `AGENTS.md` only when a non-inferable caveat changes how it must be run; otherwise link to its owner.
- Do not copy current delivery status into README, requirements, architecture, research, or this file; link to where the state lives.
- A documentation-only change needs no code check unless that check examines documentation, as Local states. At minimum run `git diff --check` and verify repository-relative Markdown links, plus the documentation checks in Local.
- Keep a tool's artifacts under the root that tool's configuration names; do not create a parallel artifact directory.

### Local

- <code checks that also examine documentation, such as a docs-site build, and documentation checks beyond the minimum, such as the OKF scope check>
- <tool artifact roots and the files that configure them>
<!-- x9-context-files-generator:documentation:end -->
