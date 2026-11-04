#!/usr/bin/env python3
"""Supersession reverse-pointer write-back (Story 5 of spec-lifecycle-archival).

When a spec's header declares `> **Amends:**` or `> **Extends:**` pointing at
another spec — signaling that the new spec replaces or builds on prior spec
work — this helper writes the matching reverse pointer onto the *referenced*
(older) spec's header:

    > **Superseded by:** [new-spec-folder](../new-spec-folder/spec.md)

inserted as a new line in the older spec's existing metadata block, alongside
`Status`, `Owner`, `Created`, etc. The older spec's own `Status:` line is
*never* replaced or rewritten — a superseded spec keeps recording its own
terminal state independently of the fact that something else now supersedes
it. `commands/create-spec.md` Step 2.4b and `commands/edit-spec.md` Step 2.2
both invoke this helper rather than hand-rolling the surgical edit.

An `Amends:`/`Extends:` line may reference more than one target (e.g. a spec
**and** an ADR, as in `2026-07-26-leanness-instrumentation`'s `Amends:` line).
Only targets that resolve to a real `.writ/specs/<folder>/spec.md` file get a
reverse pointer — ADR links (or any other target) are forward-only and are
reported separately, never written to. A broken relative path or missing
target spec is reported as `broken`, not raised as an error — a bad
supersession reference must never block the new spec's own package creation.

Subcommands:
  scan  --new-spec-file PATH
    Report every Amends:/Extends: target found on PATH's header, classified
    as `spec` (resolvable, write-back eligible), `other` (e.g. an ADR —
    forward-only), or missing entirely — without mutating anything.
  apply --new-spec-file PATH
    Perform the real write-back onto each resolvable spec target's header.
    Idempotent: re-running updates (does not duplicate) an existing
    `Superseded by:` line pointing elsewhere, and is a no-op if it already
    points at this same new spec.

Both subcommands always print one JSON object and exit 0 for a present,
readable `--new-spec-file` — a spec with no Amends:/Extends: line at all is a
clean no-op (`targets: []`), not an error. Only a missing/unreadable
`--new-spec-file` itself is a hard failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_SCAN = "supersession-writeback-scan-v1"
SCHEMA_APPLY = "supersession-writeback-apply-v1"

# Bold or unbold Amends:/Extends: header line. The value may contain one or
# more markdown links (spec and/or ADR targets).
SUPERSESSION_LINE = re.compile(r"^>\s*(\*\*)?(?P<field>Amends|Extends):(\*\*)?\s*(?P<value>.+?)\s*$")

# Markdown link syntax: [text](target)
MD_LINK = re.compile(r"\[[^\]]*\]\((?P<target>[^)]+)\)")

SUPERSEDED_BY_LINE = re.compile(r"^>\s*(\*\*)?Superseded by:(\*\*)?\s*.*$")

# Same cap as spec-status.py — the header metadata block is always near the
# top of a spec.md; capping the scan guards against accidental body matches.
HEADER_SCAN_LINES = 15


class ContractError(Exception):
    def __init__(self, code: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary


def _fail(err: ContractError) -> None:
    print(json.dumps({"blocker": {"code": err.code, "summary": err.summary}}))
    raise SystemExit(1)


def _header_end(lines: list[str]) -> int:
    """Index of the first `##` heading (or end of file) within the scan cap."""
    for i, raw in enumerate(lines[:HEADER_SCAN_LINES]):
        if raw.lstrip().startswith("##"):
            return i
    return min(len(lines), HEADER_SCAN_LINES)


def find_supersession_targets(text: str) -> list[dict[str, str]]:
    """Return every Amends:/Extends: markdown-link target in the header block."""
    lines = text.splitlines()
    targets: list[dict[str, str]] = []
    for raw in lines[: _header_end(lines)]:
        match = SUPERSESSION_LINE.match(raw)
        if not match:
            continue
        field = match.group("field")
        for link in MD_LINK.finditer(match.group("value")):
            targets.append({"field": field, "link": link.group("target").strip()})
    return targets


def _is_spec_file(resolved: Path) -> bool:
    """True if `resolved` looks like `.writ/specs/<folder>/spec.md`."""
    return resolved.name == "spec.md" and resolved.parent.parent.name == "specs"


def scan(new_spec_file: Path) -> dict[str, Any]:
    if not new_spec_file.is_file():
        raise ContractError("missing_spec", f"spec file not found: {new_spec_file}")

    text = new_spec_file.read_text(encoding="utf-8")
    targets: list[dict[str, Any]] = []
    for raw in find_supersession_targets(text):
        resolved = (new_spec_file.parent / raw["link"]).resolve()
        is_spec = _is_spec_file(resolved)
        targets.append(
            {
                "field": raw["field"],
                "link": raw["link"],
                "resolved": str(resolved),
                "kind": "spec" if is_spec else "other",
                "resolvable": is_spec and resolved.is_file(),
            }
        )
    return {
        "schema": SCHEMA_SCAN,
        "file": str(new_spec_file),
        "new_spec_folder": new_spec_file.parent.name,
        "targets": targets,
        "resolvable_count": sum(1 for t in targets if t["resolvable"]),
    }


def _upsert_superseded_by(text: str, new_spec_folder: str, new_spec_link: str) -> tuple[str, bool]:
    """Insert or update the `Superseded by:` header line.

    Never touches `Status:` or any other line. Returns (new_text, changed).
    Idempotent: re-pointing at the same new spec is a no-op.
    """
    trailing_newline = text.endswith("\n")
    lines = text.splitlines()
    end = _header_end(lines)
    new_line = f"> **Superseded by:** [{new_spec_folder}]({new_spec_link})"

    for i in range(end):
        if SUPERSEDED_BY_LINE.match(lines[i]):
            if lines[i] == new_line:
                return text, False
            lines[i] = new_line
            break
    else:
        insert_at = end
        for i in range(end - 1, -1, -1):
            if lines[i].lstrip().startswith(">"):
                insert_at = i + 1
                break
        lines.insert(insert_at, new_line)

    new_text = "\n".join(lines)
    if trailing_newline:
        new_text += "\n"
    return new_text, True


def apply(new_spec_file: Path) -> dict[str, Any]:
    """Write `Superseded by:` onto every resolvable spec target.

    Never raises for a per-target problem: unresolvable ADR/other links are
    reported as `skipped_other`, broken spec references as `broken` — the
    caller (create-spec.md Step 2.4b / edit-spec.md Step 2.2) must not fail
    or block the new/edited spec's own package because of a bad pointer.
    """
    scanned = scan(new_spec_file)
    new_spec_folder = scanned["new_spec_folder"]
    # Resolved consistently with `target["resolved"]` (scan() also resolves)
    # so os.path.relpath below never crosses a symlink boundary asymmetrically
    # (e.g. macOS's /tmp -> /private/var/... — resolving only one side would
    # otherwise produce a nonsensical, overlong relative path).
    new_spec_file_resolved = new_spec_file.resolve()

    written: list[str] = []
    unchanged: list[str] = []
    skipped_other: list[str] = []
    broken: list[str] = []

    for target in scanned["targets"]:
        if target["kind"] != "spec":
            skipped_other.append(target["link"])
            continue
        target_path = Path(target["resolved"])
        if not target_path.is_file():
            broken.append(target["link"])
            continue

        old_text = target_path.read_text(encoding="utf-8")
        rel = os.path.relpath(new_spec_file_resolved, start=target_path.parent).replace(os.sep, "/")
        new_text, changed = _upsert_superseded_by(old_text, new_spec_folder, rel)
        if changed:
            target_path.write_text(new_text, encoding="utf-8")
            written.append(str(target_path))
        else:
            unchanged.append(str(target_path))

    return {
        "schema": SCHEMA_APPLY,
        "new_spec_folder": new_spec_folder,
        "written": written,
        "unchanged": unchanged,
        "skipped_other": skipped_other,
        "broken": broken,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="report Amends:/Extends: targets without mutating anything")
    p_scan.add_argument("--new-spec-file", required=True, type=Path)

    p_apply = sub.add_parser("apply", help="write Superseded by: onto every resolvable spec target")
    p_apply.add_argument("--new-spec-file", required=True, type=Path)

    args = parser.parse_args(argv)

    try:
        if args.command == "scan":
            print(json.dumps(scan(args.new_spec_file)))
        elif args.command == "apply":
            print(json.dumps(apply(args.new_spec_file)))
    except ContractError as err:
        _fail(err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
