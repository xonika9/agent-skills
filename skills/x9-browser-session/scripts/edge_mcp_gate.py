#!/usr/bin/env python3
"""Run chrome-devtools-mcp while Edge may not be running yet, and fail closed per tool call.

Usage: edge_mcp_gate.py <controller> [controller arguments...]
Install next to agent_edge.py, which supplies the profile verification.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_edge  # noqa: E402


def binding_error(port, profile):
    """Return None when the listener on the port is the expected Edge profile."""
    try:
        result = subprocess.run(['lsof', '-nP', f'-tiTCP:{port}', '-sTCP:LISTEN'],
                                capture_output=True, text=True, timeout=3)
        pids = set(result.stdout.split())
        if not pids:
            return f'Microsoft Edge (Agent) is not running on port {port}; start it with its launcher and retry.'
        if len(pids) != 1 or not all(pid.isdecimal() and int(pid) > 0 for pid in pids):
            return f'The listener on port {port} is ambiguous; no browser command was dispatched.'
        agent_edge.verify_profile(agent_edge.process_argv(int(pids.pop())), profile, port)
    except (OSError, ValueError, subprocess.SubprocessError):
        return f'Port {port} does not belong to the Edge agent profile; no browser command was dispatched.'
    return None


def main():
    controller, *arguments = sys.argv[1:] or ['']
    if not controller:
        print('usage: edge_mcp_gate.py <controller> [arguments...]', file=sys.stderr)
        return 2
    port = int(os.environ.get('EDGE_AGENT_PORT', agent_edge.PORT))
    profile = os.environ.get('EDGE_AGENT_PROFILE') or str(agent_edge.profile_path())
    child = subprocess.Popen([controller, *arguments], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out_lock = threading.Lock()

    def emit(raw):
        with out_lock:
            sys.stdout.buffer.write(raw)
            sys.stdout.buffer.flush()

    def pump():
        for line in child.stdout:
            emit(line)

    pump_thread = threading.Thread(target=pump, daemon=True)
    pump_thread.start()
    try:
        for line in sys.stdin.buffer:
            try:
                message = json.loads(line)
            except ValueError:
                message = None
            if isinstance(message, dict) and message.get('method') == 'tools/call' and 'id' in message:
                error = binding_error(port, profile)
                if error:
                    reply = {'jsonrpc': '2.0', 'id': message['id'],
                             'result': {'content': [{'type': 'text', 'text': error}], 'isError': True}}
                    emit(json.dumps(reply).encode() + b'\n')
                    continue
            child.stdin.write(line)
            child.stdin.flush()
    except BrokenPipeError:
        pass
    finally:
        try:
            child.stdin.close()
        except OSError:
            pass
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.terminate()
        pump_thread.join(timeout=2)
    return child.returncode or 0


if __name__ == '__main__':
    raise SystemExit(main())
