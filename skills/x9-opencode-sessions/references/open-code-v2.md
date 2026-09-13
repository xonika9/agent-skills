# OpenCode V2 API

The wrapper owns the volatile `opencode2 api` syntax. It calls the current verified
OpenCode V2 Sessions API and normalizes `{data, cursor?}` envelopes before printing JSON.
Do not substitute a browser, an undocumented database, or another harness's session API.

## Inspect

```bash
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py list --search "billing"
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py list --roots --limit 10
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py list --parent-id <session-id>
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py show <session-id>
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py active
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py messages <session-id>
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py message <session-id> <message-id>
```

The inspection routes return JSON. An empty response body from any of them is an
`empty-response` failure; an empty collection is represented by a JSON envelope whose
`data` field is empty. `list` and `messages` require a data array, `active` requires a
data object, and `show` and `message` require one non-empty data object. A missing `data`
field or the wrong data shape is an `invalid-envelope` failure. Session records require
a string `id`, message records require string `id` and `type` fields, and every `active`
status requires a string `type`.

`list` accepts `--parent-id`, `--roots`, `--search`, `--workspace`, `--project`,
`--directory`, `--subpath`, `--order`, `--limit`, and `--cursor`. `--roots` sends
`parentID=null`. `messages` accepts `--limit` and either `--order` or `--cursor`. The
default limit is 20; pagination is explicit through the returned cursor object's `next`
and `previous` values. A list result is metadata, not authority to infer identity from a
similar title. Read messages only after choosing the session needed for the user's request.

The API routes are `GET /api/session`, `GET /api/session/{sessionID}`, `GET
/api/session/{sessionID}/message`, `GET /api/session/{sessionID}/message/{messageID}`, and
`GET /api/session/active`. Message output includes top-level `text` from user, synthetic,
and system messages, plus only `content` entries whose type is `text` from assistant
messages. Internal skill text, reasoning, and tool state remain excluded. Session metadata
preserves `location.directory`, `location.workspaceID`, and `subpath` so similarly titled
sessions can be distinguished safely.

## Send, wait, reconcile

```bash
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py prompt <session-id> "Please return the final result."
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py prompt <session-id> "Please return the final result." --message-id <preview-message-id> --apply
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py wait <session-id>
python3 skills/x9-opencode-sessions/scripts/opencode_sessions.py message <session-id> <message-id>
```

The prompt route is `POST /api/session/{sessionID}/prompt` with `text` and a caller-supplied
`id` matching `^msg_`; the wrapper generates that ID during preview and reuses it for
dispatch. Preview permanently reserves the ID and stores a one-use local receipt with the
session ID and SHA-256 of the text, not the text itself. Apply atomically consumes that
receipt before the network call. A send response is confirmed only when the server
receipt repeats both that message ID and the selected session ID; an empty body does not
confirm dispatch. `wait` calls `POST /api/session/{sessionID}/wait`, where a bodyless
`204` response is successful completion and `503` means waiting is unavailable. The
[main skill](../SKILL.md#sending-and-waiting) owns the recovery decisions for a timeout,
non-confirming dispatch, or unavailable wait.
