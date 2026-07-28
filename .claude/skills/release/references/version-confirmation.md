# Structured version confirmation

Use the runtime's structured user-input tool:

- Codex: `request_user_input`;
- Claude Code: `AskUserQuestion`.

Discover the live tool schema before constructing the question. Present the recommended `X.Y.Z`, the strongest changes that determine its bump, and a way to confirm, reject, or supply another version. Wait for an affirmative structured response before editing the changelog heading or either manifest version.

If the maintainer supplies another version, validate it against the complete candidate. When it understates the required semantic bump or conflicts with an existing release, explain the conflict and issue another structured question; do not accept it silently or fall back to chat.

If the structured question tool is unavailable or its call fails, mark release preparation `BLOCKED`. Report the missing gate without asking for confirmation in plain chat and leave release versions unchanged.
