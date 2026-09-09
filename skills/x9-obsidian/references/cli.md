# CLI adapter

The [official CLI documentation](https://obsidian.md/help/cli) is the reference; the installed `obsidian help` and command-specific help decide which commands and parameters are available. Checked against official documentation on 2026-09-09; do not use this date as a substitute for live discovery.

Discover the executable through the available shell or runtime tool catalog. Distinguish a missing executable from an installed but disabled/unregistered CLI, an app connection failure, and a command absent from this version. Do not install, enable, restart, or change settings merely to make a read route work. CLI use depends on the desktop app and may launch it; if that exceeds the session's authority, use local files and report the app limitation.

After help confirms the syntax, select the verified vault explicitly: `vault=<name-or-id>` precedes the command. Use `path=<exact-vault-relative-path>` rather than `file=<basename>` or an implicit active file. Confirm the selected vault corresponds to the intended directory through available vault information; never trust focus or current working directory alone. A read-only example after resolving both values:

```text
obsidian vault="Notes" read path="Projects/Example.md"
```

Load only the command help needed for the action, such as search, properties, backlinks, unresolved links, move, or Bases queries. Do not copy a complete command catalog into a plan. Prefer Obsidian move/rename for app-aware link updates after checking the setting described in [moves.md](moves.md).

Pass note text as data through structured process arguments or correctly quoted shell arguments. JSON stringification is not shell escaping; note content can contain backticks, substitutions, quotes, and newlines. Prefer a filesystem patch for complex text if the command transport cannot preserve it safely.

A zero exit code is transport evidence. The target file and app response must establish that the intended operation occurred; empty output or a launched window is not proof. Filesystem fallback does not prove Obsidian indexing, link resolution, rendering, or remote synchronization.
