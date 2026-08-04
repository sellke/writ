#!/usr/bin/env python3
"""Evidence-gated archive sweep for Complete specs (Story 2 of spec-lifecycle-archival).

Moves specs that are BOTH (a) complete-family per `scripts/spec-status.py`'s
format-tolerant detector and (b) cited by at least one `.writ/knowledge/`
entry's `related_artifacts` frontmatter (matched on the spec's folder-name
component) from `.writ/specs/<name>/` to `.writ/specs/archive/<name>/` via a
plain `git mv`. Time-in-Complete-status alone is never sufficient (Business
Rule 1) — the two-signal bar substitutes for a per-spec confirmation prompt.

Archived specs live one path segment deeper than active specs
(`.writ/specs/archive/<name>/spec.md` vs. `.writ/specs/<name>/spec.md`), so
every existing single-level `.writ/specs/*/spec.md` glob used elsewhere in the
command suite excludes them automatically (Business Rule 5) — the move itself
is also the idempotency mechanism: a spec already under `archive/` no longer
appears in the next sweep's scan at all.

Subcommands:
  scan  --specs-dir DIR --knowledge-dir DIR
    Report eligibility for every spec under DIR without mutating anything.
  sweep --specs-dir DIR --knowledge-dir DIR [--repo-root DIR]
    Perform the real `git mv` + ledger-append sweep. Per-spec destination
    collisions or `git mv` failures are skipped and reported; the sweep
    continues for the remaining specs rather than aborting (Business Rule 1's
    sibling operational rule — see spec.md Error / Edge Experience table).

Both subcommands always print one JSON object and exit 0 — this is a
best-effort sweep, not a fail-closed validator. Nothing is mutated by `scan`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_SCAN = "archive-sweep-scan-v1"
SCHEMA_SWEEP = "archive-sweep-v1"

SPEC_STATUS_HELPER = Path(__file__).with_name("spec-status.py")

# `related_artifacts` is scanned across these four knowledge categories only,
# per the locked eligibility contract (spec.md Detailed Requirements).
KNOWLEDGE_CATEGORIES = ("decisions", "conventions", "glossary", "lessons")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _classify_specs(specs_dir: Path) -> list[dict[str, Any]]:
    """Delegate complete-family classification to spec-status.py's `scan`.

    Graceful degradation: if the specs directory doesn't exist or the helper
    can't run, this returns an empty list rather than raising — an absent or
    empty spec corpus is a clean no-op sweep, not an error (spec-lite.md's
    "Nil input" shadow path), and archive-sweep.py never fails closed.
    """
    proc = subprocess.run(
        [sys.executable, str(SPEC_STATUS_HELPER), "scan", "--specs-dir", str(specs_dir)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return []
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return payload.get("results", [])


def _extract_related_artifacts(text: str) -> list[str]:
    """Return the raw list items under a YAML `related_artifacts:` key.

    Handles the one shape used throughout `.writ/knowledge/`: a bare
    `related_artifacts:` line followed by indented `- item` lines, ending at
    the next non-indented-list line (closing `---` or the next frontmatter
    key). Malformed/absent frontmatter yields an empty list, never an error.
    """
    items: list[str] = []
    capturing = False
    for line in text.splitlines():
        stripped = line.strip()
        if not capturing:
            if stripped == "related_artifacts:":
                capturing = True
            continue
        if line[:1].isspace() and stripped.startswith("-"):
            items.append(stripped[1:].strip())
            continue
        break
    return items


def find_knowledge_evidence(knowledge_dir: Path, spec_id: str) -> list[str]:
    """Return knowledge filenames (relative to knowledge_dir) whose
    `related_artifacts` frontmatter references `spec_id` as a substring.

    Folder-name substring match, not exact path equality — tolerates
    `related_artifacts` entries written as `.writ/specs/<name>/spec.md`,
    `.writ/specs/<name>/`, or similar drift (documented heuristic, per
    spec.md's Technical Concerns; matching the full dated slug rather than a
    bare keyword avoids cross-artifact false positives).
    """
    evidence: list[str] = []
    if not knowledge_dir.is_dir():
        return evidence
    for category in KNOWLEDGE_CATEGORIES:
        cat_dir = knowledge_dir / category
        if not cat_dir.is_dir():
            continue
        for md_file in sorted(cat_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
            items = _extract_related_artifacts(text)
            if any(spec_id in item for item in items):
                evidence.append(str(md_file.relative_to(knowledge_dir)))
    return evidence


def scan(specs_dir: Path, knowledge_dir: Path) -> dict[str, Any]:
    """Report eligibility for every spec under `specs_dir` — no mutation."""
    results: list[dict[str, Any]] = []
    for row in _classify_specs(specs_dir):
        spec_id = row["spec"]
        complete = bool(row["complete"])
        evidence = find_knowledge_evidence(knowledge_dir, spec_id) if complete else []
        results.append(
            {
                "spec": spec_id,
                "complete": complete,
                "evidence": evidence,
                "eligible": complete and bool(evidence),
            }
        )
    return {
        "schema": SCHEMA_SCAN,
        "specs_dir": str(specs_dir),
        "knowledge_dir": str(knowledge_dir),
        "results": results,
        "eligible_count": sum(1 for r in results if r["eligible"]),
    }


def _append_ledger(ledger_path: Path, spec_id: str, evidence: list[str], timestamp: str) -> None:
    is_new = not ledger_path.exists()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_str = ", ".join(f"`{e}`" for e in evidence)
    line = f"- {timestamp} — `{spec_id}` archived (evidence: {evidence_str})\n"
    with ledger_path.open("a", encoding="utf-8") as fh:
        if is_new:
            fh.write("# Archive Ledger\n\n")
            fh.write(
                "Committed, append-only audit trail for `/status --archive`. "
                "One line per archived spec — never edit or reorder existing lines.\n\n"
            )
        fh.write(line)


def sweep(repo_root: Path, specs_dir: Path, knowledge_dir: Path) -> dict[str, Any]:
    """Perform the real git-mv + ledger-append sweep.

    Never raises for a per-spec failure: destination collisions and `git mv`
    failures are recorded and skipped, and the sweep continues with the
    remaining eligible specs (spec.md Error / Edge Experience table).
    """
    archive_dir = specs_dir / "archive"
    ledger_path = archive_dir / "LEDGER.md"
    scanned = scan(specs_dir, knowledge_dir)

    archived: list[dict[str, Any]] = []
    skipped_no_evidence: list[str] = []
    collisions: list[str] = []
    move_failures: list[dict[str, str]] = []

    for row in scanned["results"]:
        if not row["complete"]:
            continue
        if not row["evidence"]:
            skipped_no_evidence.append(row["spec"])
            continue

        spec_id = row["spec"]
        src = specs_dir / spec_id
        dest = archive_dir / spec_id

        if dest.exists():
            collisions.append(spec_id)
            continue

        archive_dir.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["git", "mv", str(src), str(dest)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            move_failures.append({"spec": spec_id, "reason": proc.stderr.strip() or proc.stdout.strip()})
            continue

        timestamp = _now_iso()
        _append_ledger(ledger_path, spec_id, row["evidence"], timestamp)
        archived.append({"spec": spec_id, "evidence": row["evidence"], "timestamp": timestamp})

    summary = (
        f"{len(archived)} specs archived, "
        f"{len(skipped_no_evidence)} Complete specs skipped (no knowledge evidence yet)"
    )
    if collisions:
        summary += f", {len(collisions)} destination collision(s) skipped"
    if move_failures:
        summary += f", {len(move_failures)} git mv failure(s) skipped"

    return {
        "schema": SCHEMA_SWEEP,
        "archived": archived,
        "skipped_no_evidence": skipped_no_evidence,
        "collisions": collisions,
        "move_failures": move_failures,
        "summary": summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="report eligibility without mutating anything")
    p_scan.add_argument("--specs-dir", required=True, type=Path)
    p_scan.add_argument("--knowledge-dir", required=True, type=Path)

    p_sweep = sub.add_parser("sweep", help="perform the real git-mv + ledger sweep")
    p_sweep.add_argument("--specs-dir", required=True, type=Path)
    p_sweep.add_argument("--knowledge-dir", required=True, type=Path)
    p_sweep.add_argument("--repo-root", default=Path("."), type=Path)

    args = parser.parse_args(argv)

    if args.command == "scan":
        print(json.dumps(scan(args.specs_dir, args.knowledge_dir)))
    elif args.command == "sweep":
        print(json.dumps(sweep(args.repo_root, args.specs_dir, args.knowledge_dir)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
