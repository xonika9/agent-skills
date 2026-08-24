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

After a successful `wait`, fetch that selected session's `messages` to collect its answer.
The endpoint may return `503` when waiting is unavailable; report that as blocked and use
`active` plus paginated `messages` rather than treating the session as complete.

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
messages. Reasoning and tool state remain excluded.

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
receipt before the network call, so a timeout cannot be retried or re-previewed with the
same ID. A send is confirmed only when the
server receipt repeats both that message ID and the selected session ID. `wait` calls
`POST /api/session/{sessionID}/wait`, where a `204`
response is successful completion and `503` means waiting is unavailable. A timeout or
non-confirming dispatch has unknown outcome. The only recovery is the targeted message
lookup above; never resend automatically.
