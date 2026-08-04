#!/usr/bin/env python3
"""Format-tolerant spec-status detector (Story 1 of spec-lifecycle-archival).

This helper is the executable reference for the authoritative "complete-family"
classification consumed by `/status` (active-spec detection) and `/create-spec`
Step 1.3b (cross-spec overlap check). It replaces the broken literal substring
check `grep -q "Status: Complete"`, which never matches the bold markdown form
`> **Status:** Complete` because `**` sits between the colon and the space.

Contract: a spec's header resolves to **complete-family** if its status line —
bold (`> **Status:** ...`) or unbold (`> Status: ...`) — starts with one of
`Complete`, `Completed`, or `Closed` (case-sensitive, matching this repo's
existing conventions). Trailing text (emoji, parenthetical explanations, em
dashes) after the value is ignored. A spec with no status header anywhere in
its leading metadata block is **not complete** — this is the conservative
default: undeclared status is never silently treated as done.

Only the spec's leading `>`-blockquote metadata block (before the first
heading) is scanned, so a stray mention of "Complete" in the document body
can never produce a false positive.

Subcommands:
  is-complete --file PATH
    Emit {complete, matched_value, header_line} for one spec.md.
  scan --specs-dir DIR
    Emit complete-family classification for every spec under DIR using the
    single-level glob `DIR/*/spec.md` (this is the archive-exclusion
    mechanism per Business Rule 5 — never widen this to a recursive glob).

Success prints a JSON object and exits 0. A missing file/dir prints a JSON
object with a `blocker` of {code, summary} and exits non-zero. This helper
never mutates anything.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_IS_COMPLETE = "spec-status-is-complete-v1"
SCHEMA_SCAN = "spec-status-scan-v1"

# Bold or unbold "Status:" label inside a leading blockquote header line.
STATUS_LINE = re.compile(r"^>\s*(\*\*)?Status:(\*\*)?\s*(?P<value>.+?)\s*$")

# Complete-family values (Business Rule 8 / technical-spec.md "Detection Logic").
# Checked as a prefix so "Completed ✅" matches via "Complete" and
# "Closed — Abandoned" matches via "Closed" without duplicating alternatives.
COMPLETE_FAMILY_PREFIXES = ("Complete", "Closed")

# Only scan the leading metadata block: consecutive/near-consecutive lines
# starting with ">" before the first heading. In practice this is always
# within the first ~15 lines of a spec.md, so cap the scan there for safety
# against accidental matches deep in the document body.
HEADER_SCAN_LINES = 15


class ContractError(Exception):
    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


def _fail(err: ContractError) -> None:
    print(json.dumps({"blocker": {"code": err.code, "summary": err.summary}}))
    raise SystemExit(1)


def find_status_line(text: str) -> str | None:
    """Return the raw status header line, or None if absent."""
    for raw in text.splitlines()[:HEADER_SCAN_LINES]:
        if raw.lstrip().startswith("##"):
            break
        if STATUS_LINE.match(raw):
            return raw
    return None


def classify(text: str) -> dict[str, Any]:
    """Classify one spec.md body as complete-family or not.

    Returns {complete, matched_value, header_line}. `matched_value` is the raw
    value text after "Status:" (trailing parenthetical/emoji preserved) when a
    header exists, else None.
    """
    header_line = find_status_line(text)
    if header_line is None:
        return {"complete": False, "matched_value": None, "header_line": None}

    match = STATUS_LINE.match(header_line)
    assert match is not None  # find_status_line only returns matching lines
    value = match.group("value")
    complete = value.startswith(COMPLETE_FAMILY_PREFIXES)
    return {"complete": complete, "matched_value": value, "header_line": header_line}


def is_complete_file(spec_path: Path) -> dict[str, Any]:
    if not spec_path.is_file():
        raise ContractError("missing_spec", f"spec file not found: {spec_path}")
    result = classify(spec_path.read_text(encoding="utf-8"))
    result["schema"] = SCHEMA_IS_COMPLETE
    result["file"] = str(spec_path)
    return result


def scan_dir(specs_dir: Path) -> dict[str, Any]:
    if not specs_dir.is_dir():
        raise ContractError("missing_specs_dir", f"specs directory not found: {specs_dir}")

    results: list[dict[str, Any]] = []
    # Single-level glob only — this is the archive-exclusion mechanism
    # (Business Rule 5). Never widen this to `**/spec.md`.
    for spec_file in sorted(specs_dir.glob("*/spec.md")):
        spec_id = spec_file.parent.name
        classification = classify(spec_file.read_text(encoding="utf-8"))
        results.append(
            {
                "spec": spec_id,
                "path": str(spec_file),
                "complete": classification["complete"],
                "matched_value": classification["matched_value"],
            }
        )
    return {
        "schema": SCHEMA_SCAN,
        "specs_dir": str(specs_dir),
        "results": results,
        "complete_count": sum(1 for r in results if r["complete"]),
        "not_complete_count": sum(1 for r in results if not r["complete"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_one = sub.add_parser("is-complete", help="classify one spec.md")
    p_one.add_argument("--file", required=True, type=Path)

    p_scan = sub.add_parser("scan", help="classify every spec under a specs dir")
    p_scan.add_argument("--specs-dir", required=True, type=Path)

    args = parser.parse_args(argv)

    try:
        if args.command == "is-complete":
            print(json.dumps(is_complete_file(args.file)))
        elif args.command == "scan":
            print(json.dumps(scan_dir(args.specs_dir)))
    except ContractError as err:
        _fail(err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
