#!/usr/bin/env python3
"""Safely inspect and coordinate OpenCode V2 sessions through ``opencode2 api``."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.parse import quote, urlencode


DEFAULT_LIMIT = 20
SESSION_FIELDS = {
    "agent",
    "id",
    "outcome",
    "parentID",
    "projectID",
    "subpath",
    "title",
}
LOCATION_FIELDS = {"directory", "workspaceID"}
MESSAGE_FIELDS = {"id", "sessionID", "timeCreated", "type"}
TIME_FIELDS = {"archived", "created", "idle", "updated", "viewed"}
DIRECT_TEXT_TYPES = {"system", "synthetic", "user"}
MESSAGE_ID_PATTERN = re.compile(r"^msg_[A-Za-z0-9_-]+$")
EMPTY_RESPONSE = object()


def json_output(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def state_directory() -> Path:
    configured = os.environ.get("X9_OPENCODE_SESSIONS_STATE_DIR")
    if configured:
        return Path(configured).expanduser()
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_home / "x9-opencode-sessions" / "previews"


def state_path(message_id: str, status: str) -> Path:
    return state_directory() / f"{message_id}.{status}.json"


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_preview(message_id: str, session_id: str, text: str) -> bool:
    directory = state_directory()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    record = {"session_id": session_id, "text_sha256": text_digest(text)}
    try:
        reservation = os.open(state_path(message_id, "reserved"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(reservation, "w", encoding="utf-8") as file:
        json.dump(record, file, sort_keys=True)
    try:
        preview = os.open(state_path(message_id, "preview"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(preview, "w", encoding="utf-8") as file:
        json.dump(record, file, sort_keys=True)
    return True


def claim_preview(message_id: str, session_id: str, text: str) -> tuple[Path | None, str | None]:
    preview = state_path(message_id, "preview")
    try:
        record = json.loads(preview.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None, "preview-not-found-or-used"
    if record != {"session_id": session_id, "text_sha256": text_digest(text)}:
        return None, "preview-mismatch"
    dispatching = state_path(message_id, "dispatching")
    try:
        preview.rename(dispatching)
    except OSError:
        return None, "preview-not-found-or-used"
    return dispatching, None


def finish_preview(dispatching: Path, status: str) -> None:
    try:
        dispatching.rename(state_path(dispatching.name.split(".", 1)[0], status))
    except OSError:
        pass


def positive_number(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def positive_limit(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def api_path(path: str, query: dict[str, Any] | None = None) -> str:
    values = {
        key: value
        for key, value in (query or {}).items()
        if value is not None
    }
    return path if not values else f"{path}?{urlencode(values)}"


def opencode_cli() -> str:
    discovered = shutil.which("opencode2")
    if discovered:
        return discovered
    user_install = Path.home() / ".local" / "bin" / "opencode2"
    if user_install.is_file() and os.access(user_install, os.X_OK):
        return str(user_install)
    return "opencode2"


def session_path(session_id: str, message_id: str | None = None) -> str:
    path = f"/api/session/{quote(session_id, safe='')}"
    if message_id is not None:
        path += f"/message/{quote(message_id, safe='')}"
    return path


def call_api(
    method: str,
    path: str,
    *,
    data: dict[str, Any] | None = None,
    empty_response_ok: bool = False,
    timeout: float | None = None,
    runner=None,
) -> tuple[bool, Any | None, str | None]:
    command = [opencode_cli(), "api", method, path]
    if data is not None:
        command.extend(["--data", json.dumps(data, ensure_ascii=False)])
    try:
        with tempfile.TemporaryFile() as stdout:
            result = (runner or subprocess.run)(
                command,
                stdout=stdout,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
            )
            output = result.stdout
            if output is None:
                stdout.seek(0)
                output = stdout.read()
    except subprocess.TimeoutExpired:
        return False, None, "timeout"
    except OSError:
        return False, None, "opencode2-unavailable"

    if result.returncode != 0:
        return False, None, f"opencode2-exit-{result.returncode}"
    if isinstance(output, bytes):
        try:
            output = output.decode("utf-8")
        except UnicodeDecodeError:
            return False, None, "non-json-response"
    output = output.strip()
    if not output:
        if empty_response_ok:
            return True, EMPTY_RESPONSE, None
        return False, None, "empty-response"
    try:
        return True, json.loads(output), None
    except json.JSONDecodeError:
        return False, None, "non-json-response"


def envelope(
    payload: Any,
    data_validator: Callable[[Any], bool],
) -> tuple[Any | None, dict[str, str | None] | None, str | None]:
    if not isinstance(payload, dict) or "data" not in payload:
        return None, None, "invalid-envelope"
    data = payload["data"]
    if not data_validator(data):
        return None, None, "invalid-envelope"
    cursor = payload.get("cursor")
    if isinstance(cursor, dict):
        normalized_cursor = {
            key: value if isinstance(value, str) else None
            for key, value in cursor.items()
            if key in {"next", "previous"}
        }
    elif isinstance(cursor, str):
        normalized_cursor = {"next": cursor, "previous": None}
    else:
        normalized_cursor = None
    return data, normalized_cursor, None


def session_record(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("id"), str) and bool(value["id"])


def message_record(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("id"), str)
        and bool(value["id"])
        and isinstance(value.get("type"), str)
        and bool(value["type"])
    )


def session_collection(value: Any) -> bool:
    return isinstance(value, list) and all(session_record(item) for item in value)


def message_collection(value: Any) -> bool:
    return isinstance(value, list) and all(message_record(item) for item in value)


def active_session_map(value: Any) -> bool:
    return isinstance(value, dict) and all(
        isinstance(session_id, str)
        and bool(session_id)
        and isinstance(status, dict)
        and isinstance(status.get("type"), str)
        and bool(status["type"])
        for session_id, status in value.items()
    )


def selected_scalars(value: Any, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        key: item
        for key, item in value.items()
        if key in fields and (isinstance(item, (str, int, float, bool)) or item is None)
    }


def normalize_session(value: Any) -> dict[str, Any]:
    session = selected_scalars(value, SESSION_FIELDS)
    time = value.get("time") if isinstance(value, dict) else None
    normalized_time = selected_scalars(time, TIME_FIELDS)
    if normalized_time:
        session["time"] = normalized_time
    location = value.get("location") if isinstance(value, dict) else None
    normalized_location = selected_scalars(location, LOCATION_FIELDS)
    if normalized_location:
        session["location"] = normalized_location
    children = value.get("children") if isinstance(value, dict) else None
    if isinstance(children, list):
        session["children"] = [normalize_session(child) for child in children]
    return session


def text_content(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    text: list[str] = []
    for part in value:
        if not isinstance(part, dict) or part.get("type") != "text":
            continue
        body = part.get("text")
        if isinstance(body, str):
            text.append(body)
    return text


def normalize_message(value: Any) -> dict[str, Any]:
    message = selected_scalars(value, MESSAGE_FIELDS)
    if not isinstance(value, dict):
        message["text"] = []
        return message
    direct_text = value.get("text")
    message_type = value.get("type")
    if message_type in DIRECT_TEXT_TYPES and isinstance(direct_text, str):
        message["text"] = [direct_text]
    elif message_type == "assistant":
        message["text"] = text_content(value.get("content"))
    else:
        message["text"] = []
    normalized_time = selected_scalars(value.get("time"), TIME_FIELDS)
    if normalized_time:
        message["time"] = normalized_time
    return message


def print_failure(operation: str, error: str, *, message_id: str | None = None) -> int:
    result: dict[str, Any] = {
        "error": error,
        "operation": operation,
        "status": "unknown" if message_id else "blocked",
    }
    if message_id:
        result["message_id"] = message_id
        result["reconcile"] = "message <session-id> <message-id>"
    json_output(result)
    return 2


def command_list(args: argparse.Namespace) -> int:
    query = {
        "parentID": "null" if args.roots else args.parent_id,
        "search": args.search,
        "workspace": args.workspace,
        "project": args.project,
        "directory": args.directory,
        "subpath": args.subpath,
        "order": args.order,
        "limit": args.limit,
        "cursor": args.cursor,
    }
    ok, payload, error = call_api("GET", api_path("/api/session", query), timeout=args.timeout)
    if not ok:
        return print_failure("list", error or "unknown")
    data, cursor, error = envelope(payload, session_collection)
    if error:
        return print_failure("list", error)
    json_output({"cursor": cursor, "sessions": [normalize_session(item) for item in data]})
    return 0


def command_show(args: argparse.Namespace) -> int:
    ok, payload, error = call_api("GET", session_path(args.session_id), timeout=args.timeout)
    if not ok:
        return print_failure("show", error or "unknown")
    data, _, error = envelope(payload, session_record)
    if error:
        return print_failure("show", error)
    json_output({"session": normalize_session(data)})
    return 0


def command_active(args: argparse.Namespace) -> int:
    ok, payload, error = call_api("GET", "/api/session/active", timeout=args.timeout)
    if not ok:
        return print_failure("active", error or "unknown")
    data, _, error = envelope(payload, active_session_map)
    if error:
        return print_failure("active", error)
    sessions = [
        {"id": session_id, "status": status.get("type")}
        for session_id, status in data.items()
        if isinstance(session_id, str) and isinstance(status, dict) and isinstance(status.get("type"), str)
    ]
    json_output({"sessions": sessions})
    return 0


def command_messages(args: argparse.Namespace) -> int:
    path = api_path(
        f"{session_path(args.session_id)}/message",
        {"limit": args.limit, "order": args.order, "cursor": args.cursor},
    )
    ok, payload, error = call_api("GET", path, timeout=args.timeout)
    if not ok:
        return print_failure("messages", error or "unknown")
    data, cursor, error = envelope(payload, message_collection)
    if error:
        return print_failure("messages", error)
    json_output({"cursor": cursor, "messages": [normalize_message(item) for item in data]})
    return 0


def command_message(args: argparse.Namespace) -> int:
    path = session_path(args.session_id, args.message_id)
    ok, payload, error = call_api("GET", path, timeout=args.timeout)
    if not ok:
        return print_failure("message", error or "unknown")
    data, _, error = envelope(payload, message_record)
    if error:
        return print_failure("message", error)
    json_output({"message": normalize_message(data)})
    return 0


def command_prompt(args: argparse.Namespace) -> int:
    if args.apply and not args.message_id:
        return print_failure("prompt", "preview-message-id-required")
    message_id = args.message_id or f"msg_{uuid.uuid4().hex}"
    if not MESSAGE_ID_PATTERN.fullmatch(message_id):
        return print_failure("prompt", "invalid-message-id")
    preview = {
        "message_id": message_id,
        "session_id": args.session_id,
        "status": "preview",
        "would_dispatch": True,
    }
    if not args.apply:
        if not create_preview(message_id, args.session_id, args.text):
            return print_failure("prompt", "preview-id-already-exists")
        json_output(preview)
        return 0

    dispatching, claim_error = claim_preview(message_id, args.session_id, args.text)
    if dispatching is None:
        return print_failure("prompt", claim_error or "preview-not-found-or-used")

    # Claiming the preview before the network call prevents retries after uncertain outcomes.
    ok, payload, error = call_api(
        "POST",
        f"{session_path(args.session_id)}/prompt",
        data={"id": message_id, "text": args.text},
        timeout=args.timeout,
    )
    if not ok:
        finish_preview(dispatching, "unknown")
        return print_failure("prompt", error or "unknown", message_id=message_id)
    # A dispatch receipt needs the two matching identities, not a full message.
    receipt, _, envelope_error = envelope(payload, lambda value: isinstance(value, dict))
    if envelope_error:
        receipt = None
    if receipt is None or receipt.get("id") != message_id or receipt.get("sessionID") != args.session_id:
        finish_preview(dispatching, "unknown")
        return print_failure("prompt", "unconfirmed-receipt", message_id=message_id)
    finish_preview(dispatching, "confirmed")
    json_output(
        {
            "message_id": message_id,
            "receipt": selected_scalars(receipt, MESSAGE_FIELDS),
            "session_id": args.session_id,
            "status": "confirmed",
        }
    )
    return 0


def command_wait(args: argparse.Namespace) -> int:
    ok, payload, error = call_api(
        "POST",
        f"{session_path(args.session_id)}/wait",
        empty_response_ok=True,
        timeout=args.timeout,
    )
    if not ok:
        return print_failure("wait", error or "unknown")
    if payload is EMPTY_RESPONSE:
        data = []
    else:
        data, _, error = envelope(payload, message_collection)
        if error:
            return print_failure("wait", error)
    json_output(
        {
            "response": [selected_scalars(item, MESSAGE_FIELDS) for item in data],
            "session_id": args.session_id,
            "status": "complete",
        }
    )
    return 0


def add_timeout(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeout", type=positive_number, default=None, help="CLI timeout in seconds")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    list_parser = commands.add_parser("list", help="List session metadata")
    parent = list_parser.add_mutually_exclusive_group()
    parent.add_argument("--parent-id")
    parent.add_argument("--roots", action="store_true", help="Set parentID=null")
    list_parser.add_argument("--search")
    list_parser.add_argument("--workspace")
    list_parser.add_argument("--project")
    list_parser.add_argument("--directory")
    list_parser.add_argument("--subpath")
    list_parser.add_argument("--order", choices=("asc", "desc"))
    list_parser.add_argument("--limit", type=positive_limit, default=DEFAULT_LIMIT)
    list_parser.add_argument("--cursor")
    add_timeout(list_parser)
    list_parser.set_defaults(handler=command_list)

    show_parser = commands.add_parser("show", help="Get one session")
    show_parser.add_argument("session_id")
    add_timeout(show_parser)
    show_parser.set_defaults(handler=command_show)

    active_parser = commands.add_parser("active", help="List active sessions")
    add_timeout(active_parser)
    active_parser.set_defaults(handler=command_active)

    messages_parser = commands.add_parser("messages", help="Get text messages")
    messages_parser.add_argument("session_id")
    message_page = messages_parser.add_mutually_exclusive_group()
    message_page.add_argument("--order", choices=("asc", "desc"))
    message_page.add_argument("--cursor")
    messages_parser.add_argument("--limit", type=positive_limit, default=DEFAULT_LIMIT)
    add_timeout(messages_parser)
    messages_parser.set_defaults(handler=command_messages)

    message_parser = commands.add_parser("message", help="Get one text message")
    message_parser.add_argument("session_id")
    message_parser.add_argument("message_id")
    add_timeout(message_parser)
    message_parser.set_defaults(handler=command_message)

    prompt_parser = commands.add_parser("prompt", help="Preview or send one prompt")
    prompt_parser.add_argument("session_id")
    prompt_parser.add_argument("text")
    prompt_parser.add_argument("--message-id")
    prompt_parser.add_argument("--apply", action="store_true")
    add_timeout(prompt_parser)
    prompt_parser.set_defaults(handler=command_prompt)

    wait_parser = commands.add_parser("wait", help="Wait for session completion")
    wait_parser.add_argument("session_id")
    add_timeout(wait_parser)
    wait_parser.set_defaults(handler=command_wait)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
