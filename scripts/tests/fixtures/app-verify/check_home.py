#!/usr/bin/env python3
"""Fixture check: GET / on 127.0.0.1:$PORT and assert the body. Exit 0 pass, 1 fail.

Saves the body to $APP_VERIFY_EVIDENCE_DIR/home-body.txt when that is set.
"""

from __future__ import annotations

import os
import sys
import urllib.request

EXPECTED = "app-verify fixture: home"


def main() -> int:
    port = int(os.environ.get("PORT", "8765"))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://127.0.0.1:{port}/", timeout=5) as response:
            body = response.read().decode("utf-8", "replace")
    except OSError as exc:
        print(f"check_home: request failed: {exc}", file=sys.stderr)
        return 1
    evidence = os.environ.get("APP_VERIFY_EVIDENCE_DIR")
    if evidence:
        with open(os.path.join(evidence, "home-body.txt"), "w", encoding="utf-8") as handle:
            handle.write(body)
    if EXPECTED not in body:
        print(f"check_home: unexpected body {body!r}", file=sys.stderr)
        return 1
    print("check_home: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
