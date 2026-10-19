<!-- x9-context-files-generator:interface-references:start -->
## Interface references

Shared rules from the `x9-context-files-generator` template. Edit only Local, which takes precedence; the rest is replaced when the template changes.

- Design, plan, and verify every user-interface change for all target form factors in Local together.
- The reference products in Local show how a behavior should work. No single reference is binding, and differing from one is not a defect when the work's requirements hold on every target form factor.
- Before proposing, comparing, or planning a behavior a reference already has, inspect how the reference does it and cite what you found; inventing behavior a reference already has is a defect. This covers screens, states, transitions, and error recovery, and also the mechanisms behind them, such as how data reaches the server, and holds in research, bake-offs, and planning, not only in implementation.
- A reference's source shows how it does something; measured values, visual states, and user transitions come from observing the running reference. When neither settles a question, mark the conclusion `NOT_PROVEN`. Never label an unobserved transition as observed.
- When a plan assigns reference analysis, record the observed screens, states, transitions, and error and recovery behavior in neutral form in the research note.
- Reproduce reference behavior with your own code. Generic UI labels are allowed; never copy a reference's code, assets, icons, fonts, media, branding, internal identifiers, or non-trivial copy.
- When a needed screen on a target form factor cannot be observed, ask the owner for a narrated screen recording.

### Local

- Target form factors: <such as desktop and phone browsers>
- References per form factor: <products>
- How to inspect each reference: <public source repository, a local bundle named by an environment variable, or a logged-in web version, and what the agent may do there>
- Where the owner puts screen recordings: <path>
<!-- x9-context-files-generator:interface-references:end -->
