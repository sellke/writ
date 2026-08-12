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
SCHEMA_VALIDATE = "spec-status-validate-v1"

# Bold or unbold "Status:" label inside a leading blockquote header line.
STATUS_LINE = re.compile(r"^>\s*(\*\*)?Status:(\*\*)?\s*(?P<value>.+?)\s*$")

# Complete-family values (Business Rule 8 / technical-spec.md "Detection Logic").
# Checked as a prefix so "Completed ✅" matches via "Complete" and
# "Closed — Abandoned" matches via "Closed" without duplicating alternatives.
COMPLETE_FAMILY_PREFIXES = ("Complete", "Closed")

# --- Canonical vocabulary -------------------------------------------------
#
# The prefix match above is deliberately loose: real status values carry
# free-form trailing detail ("Complete (integrated via Phase 8 lane merge
# f88c6f8)"), and that detail is worth keeping. But matching "Closed" as a
# BARE prefix admits any subtype at all, which is how "Closed — Not
# Implemented" entered five specs while `.writ/docs/spec-lifecycle.md`
# still declared that no fourth prefix existed. Nothing compared the two.
#
# So the vocabulary is declared here as canonical *heads*. Detection stays
# tolerant — `is_complete` behaviour is unchanged and no existing spec is
# silently reclassified — while `validate` reports any value whose head is
# not one of these. Drift becomes visible rather than fatal, matching this
# script's best-effort contract.
ACTIVE_STATUS_HEADS = ("Not Started", "In Progress")
COMPLETED_STATUS_HEADS = ("Completed", "Complete")
CLOSED_STATUS_HEADS = (
    "Closed — Abandoned",
    "Closed — Cancelled",
    "Closed — Not Implemented",
)
CANONICAL_STATUS_HEADS = (
    ACTIVE_STATUS_HEADS + COMPLETED_STATUS_HEADS + CLOSED_STATUS_HEADS
)


def _normalize_dashes(value: str) -> str:
    """Treat em dash, en dash, and hyphen as one separator when matching.

    Authors type whichever their editor produces; the vocabulary should not
    hinge on which dash character landed in the file.
    """
    return value.replace("—", "-").replace("–", "-").replace(" - ", " - ")


def canonical_head(value: str) -> str | None:
    """Return the canonical head this status value declares, or None.

    Longest head first, so "Closed — Not Implemented" is not shadowed by a
    shorter head, and "Completed" is not shadowed by "Complete".
    """
    probe = _normalize_dashes(value.strip())
    for head in sorted(CANONICAL_STATUS_HEADS, key=len, reverse=True):
        if probe.startswith(_normalize_dashes(head)):
            return head
    return None

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
    # `canonical_head` is reported, never enforced here: classification must
    # stay tolerant so an off-vocabulary value is still detected correctly.
    # `validate` is where a non-canonical head becomes a finding.
    return {"complete": complete, "matched_value": value,
            "canonical_head": canonical_head(value), "header_line": header_line}


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


def validate_dir(specs_dir: Path, include_archive: bool = True) -> dict[str, Any]:
    """Report every spec whose status head is not in the canonical vocabulary.

    Unlike `scan`, this deliberately reaches into `archive/` as well: an
    archived spec's status is the permanent record of *how* it ended, so a
    non-canonical value there is exactly as much drift as one in an active
    spec — and archived specs are the majority of the corpus.

    Never mutates. A missing status header is reported separately from an
    off-vocabulary one: the former is a documented, intentional state
    (conservatively not-complete), the latter is drift.
    """
    if not specs_dir.is_dir():
        raise ContractError("missing_specs_dir", f"specs directory not found: {specs_dir}")

    paths = sorted(specs_dir.glob("*/spec.md"))
    if include_archive and (specs_dir / "archive").is_dir():
        paths += sorted((specs_dir / "archive").glob("*/spec.md"))

    off_vocabulary: list[dict[str, Any]] = []
    missing_header: list[str] = []
    heads_in_use: dict[str, int] = {}

    for spec_file in paths:
        spec_id = spec_file.parent.name
        classification = classify(spec_file.read_text(encoding="utf-8"))
        value = classification["matched_value"]
        if value is None:
            missing_header.append(spec_id)
            continue
        head = classification["canonical_head"]
        if head is None:
            off_vocabulary.append({"spec": spec_id, "value": value,
                                   "path": str(spec_file)})
        else:
            heads_in_use[head] = heads_in_use.get(head, 0) + 1

    return {
        "schema": SCHEMA_VALIDATE,
        "specs_dir": str(specs_dir),
        "scanned": len(paths),
        "canonical_heads": list(CANONICAL_STATUS_HEADS),
        "heads_in_use": dict(sorted(heads_in_use.items())),
        "off_vocabulary": off_vocabulary,
        "missing_header": missing_header,
        "ok": not off_vocabulary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_one = sub.add_parser("is-complete", help="classify one spec.md")
    p_one.add_argument("--file", required=True, type=Path)

    p_scan = sub.add_parser("scan", help="classify every spec under a specs dir")
    p_scan.add_argument("--specs-dir", required=True, type=Path)

    p_val = sub.add_parser(
        "validate", help="report specs whose status head is not canonical")
    p_val.add_argument("--specs-dir", required=True, type=Path)
    p_val.add_argument("--no-archive", action="store_true",
                       help="skip archive/ (default: archived specs are validated too)")

    args = parser.parse_args(argv)

    try:
        if args.command == "is-complete":
            print(json.dumps(is_complete_file(args.file)))
        elif args.command == "scan":
            print(json.dumps(scan_dir(args.specs_dir)))
        elif args.command == "validate":
            print(json.dumps(validate_dir(args.specs_dir,
                                          include_archive=not args.no_archive)))
    except ContractError as err:
        _fail(err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
