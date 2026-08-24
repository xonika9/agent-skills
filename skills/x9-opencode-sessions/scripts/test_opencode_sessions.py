#!/usr/bin/env python3
"""Unit tests for the deterministic OpenCode V2 Sessions API wrapper."""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import opencode_sessions


class Result:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


class OpenCodeSessionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state_directory = tempfile.TemporaryDirectory()
        self.environment = patch.dict(
            os.environ,
            {"X9_OPENCODE_SESSIONS_STATE_DIR": self.state_directory.name},
        )
        self.environment.start()

    def tearDown(self) -> None:
        self.environment.stop()
        self.state_directory.cleanup()

    def run_main(self, args: list[str]) -> tuple[int, dict]:
        output = io.StringIO()
        with redirect_stdout(output):
            code = opencode_sessions.main(args)
        return code, json.loads(output.getvalue())

    def test_list_passes_filters_and_normalizes_envelope(self) -> None:
        calls: list[list[str]] = []

        def runner(command, **kwargs):
            calls.append(command)
            return Result('{"data":[{"id":"ses_1","title":"Billing","subpath":"packages/api","location":{"directory":"/work","workspaceID":"wrk_1"},"nested":{"secret":"no"}}],"cursor":{"previous":null,"next":"next-page"}}')

        with patch.object(opencode_sessions.subprocess, "run", runner):
            code, output = self.run_main([
                "list", "--roots", "--search", "billing", "--project", "demo",
                "--directory", "/work", "--order", "desc", "--limit", "7",
            ])

        self.assertEqual(code, 0)
        self.assertEqual(output, {"cursor": {"next": "next-page", "previous": None}, "sessions": [{"id": "ses_1", "location": {"directory": "/work", "workspaceID": "wrk_1"}, "subpath": "packages/api", "title": "Billing"}]})
        self.assertEqual(calls[0][:4], ["opencode2", "api", "GET", "/api/session?parentID=null&search=billing&project=demo&directory=%2Fwork&order=desc&limit=7"])

    def test_messages_only_expose_text_parts(self) -> None:
        payload = {
            "data": [
                {
                    "id": "m1",
                    "type": "assistant",
                    "reasoning": "Also hidden when it is not in content",
                    "content": [
                        {"type": "text", "text": "Visible"},
                        {"type": "reasoning", "text": "Hidden chain"},
                        {"type": "tool", "input": {"token": "hidden"}},
                    ],
                }
            ]
        }

        with patch.object(opencode_sessions.subprocess, "run", return_value=Result(json.dumps(payload))):
            code, output = self.run_main(["messages", "ses_1"])

        self.assertEqual(code, 0)
        self.assertEqual(output, {"cursor": None, "messages": [{"id": "m1", "text": ["Visible"], "type": "assistant"}]})

    def test_messages_expose_direct_user_text_and_pagination(self) -> None:
        calls: list[list[str]] = []

        def runner(command, **kwargs):
            calls.append(command)
            return Result(json.dumps({
                "data": [{"id": "msg_user", "type": "user", "text": "Question", "time": {"created": 123}}],
                "cursor": {"previous": "older", "next": None},
            }))

        with patch.object(opencode_sessions.subprocess, "run", runner):
            code, output = self.run_main(["messages", "ses_1", "--cursor", "page-2", "--limit", "5"])

        self.assertEqual(code, 0)
        self.assertEqual(output, {
            "cursor": {"next": None, "previous": "older"},
            "messages": [{"id": "msg_user", "text": ["Question"], "time": {"created": 123}, "type": "user"}],
        })
        self.assertEqual(calls[0][:4], ["opencode2", "api", "GET", "/api/session/ses_1/message?limit=5&cursor=page-2"])

    def test_messages_hide_internal_skill_text(self) -> None:
        payload = {
            "data": [{
                "id": "msg_skill",
                "type": "skill",
                "text": "Private skill body",
                "content": [{"type": "text", "text": "Private content"}],
            }],
            "cursor": {"previous": None, "next": None},
        }
        with patch.object(opencode_sessions.subprocess, "run", return_value=Result(json.dumps(payload))):
            code, output = self.run_main(["messages", "ses_1"])

        self.assertEqual(code, 0)
        self.assertEqual(output["messages"], [{"id": "msg_skill", "text": [], "type": "skill"}])

    def test_active_normalizes_session_map(self) -> None:
        payload = {"data": {"ses_1": {"type": "running"}, "ses_2": {"type": "running"}}}
        with patch.object(opencode_sessions.subprocess, "run", return_value=Result(json.dumps(payload))):
            code, output = self.run_main(["active"])

        self.assertEqual(code, 0)
        self.assertEqual(output, {"sessions": [
            {"id": "ses_1", "status": "running"},
            {"id": "ses_2", "status": "running"},
        ]})

    def test_message_path_escapes_identifiers(self) -> None:
        self.assertEqual(
            opencode_sessions.session_path("session/a", "message/b"),
            "/api/session/session%2Fa/message/message%2Fb",
        )

    def test_prompt_is_preview_without_apply(self) -> None:
        with patch.object(opencode_sessions.subprocess, "run") as runner:
            code, output = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1"])

        self.assertEqual(code, 0)
        self.assertEqual(output, {"message_id": "msg_1", "session_id": "ses_1", "status": "preview", "would_dispatch": True})
        runner.assert_not_called()

    def test_prompt_generates_valid_message_id(self) -> None:
        with patch.object(opencode_sessions.subprocess, "run") as runner:
            code, output = self.run_main(["prompt", "ses_1", "hello"])

        self.assertEqual(code, 0)
        self.assertRegex(output["message_id"], r"^msg_[0-9a-f]{32}$")
        runner.assert_not_called()

    def test_prompt_apply_dispatches_exact_preview_id(self) -> None:
        calls: list[tuple[list[str], dict]] = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return Result('{"data":{"id":"msg_1","sessionID":"ses_1","timeCreated":123,"type":"user","payload":{"text":"hello"},"delivery":{"type":"immediate"}}}')

        with patch.object(opencode_sessions.subprocess, "run", runner):
            preview_code, _ = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1"])
            code, output = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1", "--apply"])

        self.assertEqual(preview_code, 0)
        self.assertEqual(code, 0)
        self.assertEqual(output["message_id"], "msg_1")
        self.assertEqual(output["status"], "confirmed")
        self.assertEqual(output["receipt"]["sessionID"], "ses_1")
        self.assertEqual(calls[0][0][:4], ["opencode2", "api", "POST", "/api/session/ses_1/prompt"])
        self.assertEqual(json.loads(calls[0][0][5]), {"id": "msg_1", "text": "hello"})

        with patch.object(opencode_sessions.subprocess, "run") as retry_runner:
            retry_code, retry_output = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1"])
        self.assertEqual(retry_code, 2)
        self.assertEqual(retry_output["error"], "preview-id-already-exists")
        retry_runner.assert_not_called()

    def test_prompt_unconfirmed_receipt_requires_reconciliation(self) -> None:
        payload = '{"data":{"id":"msg_other","sessionID":"ses_1","type":"user"}}'
        with patch.object(opencode_sessions.subprocess, "run", return_value=Result(payload)):
            self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1"])
            code, output = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1", "--apply"])

        self.assertEqual(code, 2)
        self.assertEqual(output["status"], "unknown")
        self.assertEqual(output["error"], "unconfirmed-receipt")
        self.assertEqual(output["message_id"], "msg_1")

    def test_prompt_apply_rejects_unknown_preview(self) -> None:
        with patch.object(opencode_sessions.subprocess, "run") as runner:
            code, output = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1", "--apply"])

        self.assertEqual(code, 2)
        self.assertEqual(output["error"], "preview-not-found-or-used")
        runner.assert_not_called()

    def test_prompt_apply_rejects_changed_text(self) -> None:
        with patch.object(opencode_sessions.subprocess, "run") as runner:
            self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1"])
            code, output = self.run_main(["prompt", "ses_1", "changed", "--message-id", "msg_1", "--apply"])

        self.assertEqual(code, 2)
        self.assertEqual(output["error"], "preview-mismatch")
        runner.assert_not_called()

    def test_prompt_apply_requires_a_preview_id(self) -> None:
        with patch.object(opencode_sessions.subprocess, "run") as runner:
            code, output = self.run_main(["prompt", "ses_1", "hello", "--apply"])

        self.assertEqual(code, 2)
        self.assertEqual(output["error"], "preview-message-id-required")
        runner.assert_not_called()

    def test_unknown_prompt_outcome_includes_reconciliation_id(self) -> None:
        with patch.object(opencode_sessions.subprocess, "run", side_effect=subprocess.TimeoutExpired("opencode2", 1)):
            preview_code, _ = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1"])
            code, output = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1", "--apply", "--timeout", "1"])

        self.assertEqual(preview_code, 0)
        self.assertEqual(code, 2)
        self.assertEqual(output["status"], "unknown")
        self.assertEqual(output["message_id"], "msg_1")
        self.assertEqual(output["reconcile"], "message <session-id> <message-id>")

        with patch.object(opencode_sessions.subprocess, "run") as runner:
            retry_code, retry_output = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1", "--apply"])
        self.assertEqual(retry_code, 2)
        self.assertEqual(retry_output["error"], "preview-not-found-or-used")
        runner.assert_not_called()

        with patch.object(opencode_sessions.subprocess, "run") as preview_runner:
            preview_code, preview_output = self.run_main(["prompt", "ses_1", "hello", "--message-id", "msg_1"])
        self.assertEqual(preview_code, 2)
        self.assertEqual(preview_output["error"], "preview-id-already-exists")
        preview_runner.assert_not_called()

    def test_wait_accepts_empty_successful_response(self) -> None:
        with patch.object(opencode_sessions.subprocess, "run", return_value=Result()):
            code, output = self.run_main(["wait", "ses_1"])

        self.assertEqual(code, 0)
        self.assertEqual(output, {"response": [], "session_id": "ses_1", "status": "complete"})

    def test_wait_service_unavailable_is_blocked(self) -> None:
        with patch.object(opencode_sessions.subprocess, "run", return_value=Result(returncode=1)):
            code, output = self.run_main(["wait", "ses_1"])

        self.assertEqual(code, 2)
        self.assertEqual(output["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
