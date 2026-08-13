#!/usr/bin/env python3
"""Mechanical roadmap-sync for specs shipped without a committed phase.

`/release` regularly ships specs that were never a roadmap parking-lot
candidate before they were built (inter-phase infrastructure — a bug fix, a
tooling gap closed mid-run, a bookkeeping amendment). Nothing previously
recorded these automatically: they accumulated silently until an occasional
manual `/plan-product --reconcile` pass swept them into `roadmap.md`'s
condensed-history table as a batch — which is exactly the "unrecorded
direction" gap two real specs sat in after v0.31.0 until a human noticed.

This script closes the mechanical half of that gap only. It does **not**
decide *what* a spec's row should say — title and description are supplied
by the caller (mirroring `archive-sweep.py archive-one`'s `--spec-name`: the
script performs safe, idempotent file surgery, never invents content). It
never touches `mission.md`'s prose, never creates an ADR, and never
classifies whether a spec represents a "direction change" — that judgment
still belongs to `/plan-product --reconcile` and `/verify-spec --product`'s
P1/P4 checks, run periodically by a human.

**Why rows carry an invisible marker.** Every existing condensed-history row
is a hand-picked, natural-language title ("Leanness instrumentation",
"Spec lifecycle & archival") with no link back to the spec folder that
shipped it — confirmed by scanning the real table, which has exactly zero
`specs/` links in that section. A title never reliably substring-matches
its spec's dated folder name (different words, different order, different
hyphenation), so `is_recorded()` cannot depend on human prose alone. Every
row this script writes therefore embeds `<!-- {spec_name} -->` — invisible
in rendered markdown, a valid GFM table-cell inline HTML comment — as the
canonical, self-authored detection signal for future idempotency checks.
Plain substring matching (folder name or its date-stripped slug appearing
anywhere in the file) still runs too, so a spec referenced the way Phase
sections already do (an actual `specs/<name>/spec.md` link) is also caught.

Subcommands:
  check --roadmap PATH --spec-name NAME
    Report whether NAME already appears anywhere in roadmap.md (full dated
    folder name, or the folder name with its leading `YYYY-MM-DD-` stripped)
    — read-only, no mutation.
  append-row --roadmap PATH --spec-name NAME --title TITLE --description DESC
             --version X.Y.Z
    Idempotently insert one row into the "Shipped Phases (condensed
    history)" table, immediately before the "Rows below the phase rows are
    inter-phase infrastructure" marker paragraph; add one Revision Log row;
    bump the file's `> Last Updated:` line. A no-op (`already_recorded`) if
    `check` would already report true for NAME — safe to call unconditionally
    from a best-effort `/release` step.

Every subcommand always prints one JSON object and exits 0 — best-effort,
matching `archive-sweep.py`'s "never fail closed" contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_CHECK = "roadmap-sync-check-v1"
SCHEMA_APPEND = "roadmap-sync-append-row-v1"

DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")

MARKER_SUBSTRING = "Rows below the phase rows are inter-phase infrastructure"
LAST_UPDATED_RE = re.compile(r"^(> Last Updated: )\d{4}-\d{2}-\d{2}$", re.MULTILINE)
REVISION_LOG_HEADER = "### Revision Log"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def is_recorded(roadmap_text: str, spec_name: str) -> bool:
    """True if `spec_name` (full or date-stripped) appears anywhere in the
    roadmap text — same substring technique as
    `resolve-spec-reference.py`'s signal 2, applied here to one file instead
    of scanning commit messages."""
    blob = roadmap_text.lower()
    folder_lower = spec_name.lower()
    slug = DATE_PREFIX.sub("", folder_lower)
    return folder_lower in blob or slug in blob


def check(roadmap_path: Path, spec_name: str) -> dict[str, Any]:
    """Read-only: is `spec_name` already recorded in `roadmap_path`?

    Graceful degradation: a missing roadmap file reports `already_recorded:
    false` rather than raising — nothing to append to yet is not this
    script's problem to solve.
    """
    try:
        text = roadmap_path.read_text(encoding="utf-8")
    except OSError:
        return {"schema": SCHEMA_CHECK, "spec": spec_name, "already_recorded": False}
    return {
        "schema": SCHEMA_CHECK,
        "spec": spec_name,
        "already_recorded": is_recorded(text, spec_name),
    }


def _insert_table_row(text: str, row: str) -> str | None:
    """Insert `row` immediately before the marker paragraph's blank-line
    boundary, i.e. right after the condensed-history table's last row.
    Returns None (not `text`) if the marker isn't found, so the caller can
    distinguish "nothing to do" from "couldn't find where to do it."
    """
    lines = text.splitlines(keepends=True)
    marker_idx = next(
        (i for i, line in enumerate(lines) if MARKER_SUBSTRING in line), None
    )
    if marker_idx is None:
        return None

    # Walk back over any blank lines to the table's last non-blank row.
    insert_at = marker_idx
    while insert_at > 0 and lines[insert_at - 1].strip() == "":
        insert_at -= 1

    newline = "\n" if (insert_at == 0 or lines[insert_at - 1].endswith("\n")) else ""
    lines.insert(insert_at, row.rstrip("\n") + "\n" if newline else row)
    return "".join(lines)


def _insert_revision_log_row(text: str, row: str) -> str:
    """Insert `row` immediately after the Revision Log table's header
    separator (`|---|---|`), so it sorts newest-first alongside the existing
    convention. A missing Revision Log section is a no-op — appending a
    section this script didn't create is out of scope; the row is simply
    not added rather than guessing at a new section's shape.
    """
    idx = text.find(REVISION_LOG_HEADER)
    if idx == -1:
        return text
    lines = text.splitlines(keepends=True)
    header_line_idx = next(
        (i for i, line in enumerate(lines) if REVISION_LOG_HEADER in line), None
    )
    if header_line_idx is None:
        return text
    # Header, blank, "| Date | Change |", "|---|---|", then rows.
    separator_idx = next(
        (
            i
            for i in range(header_line_idx, len(lines))
            if lines[i].strip().startswith("|---")
        ),
        None,
    )
    if separator_idx is None:
        return text
    lines.insert(separator_idx + 1, row.rstrip("\n") + "\n")
    return "".join(lines)


def append_row(
    roadmap_path: Path,
    spec_name: str,
    title: str,
    description: str,
    version: str,
    revision_note: str | None = None,
) -> dict[str, Any]:
    """Idempotently append one condensed-history row and one Revision Log
    row, then bump `> Last Updated:`. Never touches anything but
    `roadmap_path` — `mission.md` and `mission-lite.md` are out of scope for
    this script by design (see module docstring).
    """
    try:
        text = roadmap_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "schema": SCHEMA_APPEND,
            "status": "roadmap_not_found",
            "spec": spec_name,
            "error": str(exc),
        }

    if is_recorded(text, spec_name):
        return {"schema": SCHEMA_APPEND, "status": "already_recorded", "spec": spec_name}

    row = f"| **— {title}** <!-- {spec_name} --> | {description} | v{version} |\n"
    updated = _insert_table_row(text, row)
    if updated is None:
        return {
            "schema": SCHEMA_APPEND,
            "status": "marker_not_found",
            "spec": spec_name,
            "error": f"could not find marker paragraph containing {MARKER_SUBSTRING!r}",
        }

    today = _today()
    note = revision_note or f"Recorded `{spec_name}` as inter-phase infrastructure (v{version})."
    updated = _insert_revision_log_row(updated, f"| {today} | {note} |")

    if LAST_UPDATED_RE.search(updated):
        updated = LAST_UPDATED_RE.sub(rf"\g<1>{today}", updated, count=1)

    roadmap_path.write_text(updated, encoding="utf-8")

    return {
        "schema": SCHEMA_APPEND,
        "status": "appended",
        "spec": spec_name,
        "row": row.rstrip("\n"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="report whether a spec is already recorded")
    p_check.add_argument("--roadmap", required=True, type=Path)
    p_check.add_argument("--spec-name", required=True)

    p_append = sub.add_parser("append-row", help="idempotently append a condensed-history row")
    p_append.add_argument("--roadmap", required=True, type=Path)
    p_append.add_argument("--spec-name", required=True)
    p_append.add_argument("--title", required=True)
    p_append.add_argument("--description", required=True)
    p_append.add_argument("--version", required=True)
    p_append.add_argument("--revision-note", default=None)

    args = parser.parse_args(argv)

    try:
        if args.command == "check":
            result = check(args.roadmap, args.spec_name)
        else:
            result = append_row(
                args.roadmap,
                args.spec_name,
                args.title,
                args.description,
                args.version,
                args.revision_note,
            )
    except Exception as exc:  # best-effort — never fail closed (module docstring)
        result = {
            "schema": SCHEMA_CHECK if args.command == "check" else SCHEMA_APPEND,
            "status": "exception",
            "spec": getattr(args, "spec_name", None),
            "error": str(exc),
        }

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
