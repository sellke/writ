#!/usr/bin/env python3
"""Stateless fixture app for `scripts/app-verify.py` (spec
`2026-10-01-behavioral-verification`, Story 3).

Serves `GET /` on 127.0.0.1:$PORT. `--never-ready` sleeps without binding,
for the not-ready recipe. When `APP_VERIFY_FIXTURE_PIDFILE` is set, the app
writes its own PID there so tests can prove cleanup left nothing behind.
"""

from __future__ import annotations

import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

BODY = b"app-verify fixture: home\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server naming
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(BODY)))
            self.end_headers()
            self.wfile.write(BODY)
        else:
            self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        sys.stderr.write("fixture: " + (format % args) + "\n")


def main() -> int:
    pidfile = os.environ.get("APP_VERIFY_FIXTURE_PIDFILE")
    if pidfile:
        with open(pidfile, "a", encoding="utf-8") as handle:
            handle.write(f"{os.getpid()}\n")
    if "--never-ready" in sys.argv:
        while True:
            time.sleep(1)
    port = int(os.environ.get("PORT", "8765"))
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"fixture: serving on 127.0.0.1:{port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
