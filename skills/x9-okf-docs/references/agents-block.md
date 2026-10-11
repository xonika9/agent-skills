# The OKF block in AGENTS.md

The block gives every agent in the repository the same OKF rules, word for word, so documentation stays consistent whether or not this skill is invoked. This skill owns the content between the markers; the rest of `AGENTS.md` belongs to the repository and `x9-context-files-generator`.

## Template

Copy the shared part exactly. Fill only the Local part, and drop a Local line with nothing to say.

```markdown
<!-- x9-okf-docs:start -->
## Document metadata (OKF)

Markdown documents in scope start with a YAML header so an agent can pick the right document without opening it. Local rules take precedence over the shared rules. Edit only the Local part; the rest is replaced when the x9-okf-docs template changes.

- The header holds four required fields: `type` (a value from Local), `title`, `description` (one line: what the document holds and what it is for), and `tags` (1–5 English kebab-case words). Quote string values.
- Write the header when you create a document. After a substantive edit, correct the fields that no longer match the content.
- In a document you are working on anyway, add a missing header and delete the retired fields `generated`, `timestamp`, `verified`, `status`, `stale_after`, `sources`, `usage_window`, and `resource`; keep every other field. Leave documents you are not working on as they are: a repository-wide pass runs only on request, through `x9-okf-docs`.
- Reading, fixing links, and formatting never change a header.
- Not documents, never given a header: `AGENTS.md`, `CLAUDE.md`, `index.md`, `log.md`, and everything outside the scope in `.x9-okf.json`. A `log.md` uses `## YYYY-MM-DD` headings, newest first.
- After writing a header, run the `x9-okf-docs` check when that skill is available.

### Local

- `type` values: <the list, or where it lives, such as each area's README>.
- Language of `title` and `description`: <language>.
- <fields this repository keeps or owns, such as OKF `status` (`draft`, `stable`, `deprecated`) or its own fields; an own field never reuses an OKF field name>
- <files another tool owns, excluded in `.x9-okf.json`, such as Compound Engineering plans and brainstorms>
- <another local convention about these documents, such as which folders keep a log.md>
<!-- x9-okf-docs:end -->
```

The scope itself lives only in `.x9-okf.json` (see [the contract](okf-format.md#scope)), because the scripts read it there.

## Writing and updating

Install or refresh the block whenever this skill writes metadata in a repository:

- **Block present.** If its shared part differs from the template, replace the shared part and keep Local unchanged. Otherwise leave it.
- **An older OKF section outside the markers.** Replace it with the block. Move its folder scope and exemptions into `.x9-okf.json`, and its local conventions about these documents into Local. Rules about other workflows stay where they are, outside the block.
- **Fields and files with another owner.** Before writing Local, look at the headers in scope. A retired OKF field the repository still relies on, such as `status` marking deprecated decisions, is kept through a Local line. A tool that writes its own header with OKF field names, such as Compound Engineering with `type: feat`, owns those files: exclude their folders or files in `.x9-okf.json` and name the tool in Local.
- **Nothing about OKF.** Insert the block after the file's opening summary. With no `AGENTS.md`, create one holding a one-line title and the block, plus a `CLAUDE.md` containing `@AGENTS.md` when none exists.
- **The repository says it does not use OKF.** Change nothing and stop; that decision is the user's.

Never change text between another skill's markers. A rule outside the block that conflicts with one inside is the user's decision: report it and keep both until they choose. Load `x9-agent-instructions` before writing Local lines, because they are agent-facing prose.

## Done

The shared part matches the template exactly, every Local line states a fact of this repository, `.x9-okf.json` holds the scope the old section described, and nothing outside the block changed except the replaced OKF section or the agreed insertion point.
