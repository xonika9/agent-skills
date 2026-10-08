#!/usr/bin/env python3
"""Check whether the current network keeps a silent TCP connection open.

An SMTP server sends a greeting and then waits for the client, so after the
greeting the connection carries no data. If the connection is closed before
the wait ends, a VPN, proxy, or router is dropping idle connections.

Prints one JSON object. Exit codes: 0 OK, 1 CUT, 2 ERROR (could not test).
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="smtp.gmail.com")
    parser.add_argument("--port", type=int, default=587)
    parser.add_argument("--seconds", type=float, default=90.0)
    args = parser.parse_args()

    def report(status: str, code: int, **extra: object) -> int:
        print(json.dumps({"status": status, "host": args.host, "port": args.port,
                          "wait_seconds": args.seconds, **extra}))
        return code

    try:
        conn = socket.create_connection((args.host, args.port), timeout=10)
    except OSError as error:
        return report("ERROR", 2, error=f"connect failed: {error}")
    with conn:
        try:
            greeting = conn.recv(256)
        except OSError as error:
            return report("ERROR", 2, error=f"no greeting: {error}")
        if not greeting:
            return report("ERROR", 2, error="server closed before greeting")
        conn.settimeout(args.seconds)
        start = time.monotonic()
        try:
            data = conn.recv(256)
        except socket.timeout:
            return report("OK", 0)
        except OSError as error:
            return report("CUT", 1, after_seconds=round(time.monotonic() - start, 1),
                          error=str(error))
        if not data:
            return report("CUT", 1, after_seconds=round(time.monotonic() - start, 1))
        # The server spoke first; the connection is still alive.
        return report("OK", 0, note="server sent data during the wait")


if __name__ == "__main__":
    sys.exit(main())
