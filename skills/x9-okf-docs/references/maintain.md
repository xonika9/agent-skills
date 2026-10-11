# Write and maintain documents

## Repository instructions

If the repository's instructions say it does not use OKF or exclude this skill, write no metadata and stop. Otherwise bring the `AGENTS.md` block in line with [the block template](agents-block.md) as part of this task.

## Documents

[The contract](okf-format.md) defines the header. Which documents to touch:

- **A document you create** gets the full header as you write it.
- **A document you work on anyway**, editing or extending its content, leaves this task with a valid header: add a missing one, fill missing fields, correct fields the edit made wrong, and delete retired OKF fields. Keep every field the contract does not name, such as a repository's own `state`.
- **Every other document** stays as it is, even when its header is missing or old. A repository-wide pass happens only when the user asks; it follows [adapt](adapt.md).
- Reading a document, fixing a link, or formatting never changes its header.

Then check what you wrote:

```bash
python3 <skill-directory>/scripts/validate_okf.py <root> --paths <path> [<path> ...]
```

## Completion

Only the documents this task worked on changed, plus the `AGENTS.md` block and `.x9-okf.json` when they needed it, and the check passes for those documents.
