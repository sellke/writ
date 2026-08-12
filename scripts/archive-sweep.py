#!/usr/bin/env python3
"""Status-alone archive sweep for complete-family specs (Story 2 of spec-lifecycle-archival).

Moves specs that are complete-family per `scripts/spec-status.py`'s
format-tolerant detector from `.writ/specs/<name>/` to
`.writ/specs/archive/<name>/` via a plain `git mv`. Knowledge-ledger
citation (at least one `.writ/knowledge/` entry's `related_artifacts`
frontmatter referencing the spec's folder-name component) is still looked
up and recorded on the ledger line as enrichment, but it no longer gates
eligibility (Amendment 2026-08-04 to Business Rule 1 — see spec.md
Technical Concerns for the full rationale: the original two-signal gate
left 36 of 39 real Complete specs in this repo stranded, and reversible
`git mv` + a committed ledger already substitutes for a per-spec
confirmation prompt without requiring proof of knowledge extraction).

Archived specs live one path segment deeper than active specs
(`.writ/specs/archive/<name>/spec.md` vs. `.writ/specs/<name>/spec.md`), so
every existing single-level `.writ/specs/*/spec.md` glob used elsewhere in the
command suite excludes them automatically (Business Rule 5) — the move itself
is also the idempotency mechanism: a spec already under `archive/` no longer
appears in the next sweep's scan at all.

`archive_one()` (Story 2 of post-merge-archival-hook) is a single-spec-scoped
sibling of `sweep()` for exactly one named spec, used by `/release`'s
merged-PR archival hook. It reuses the same `_classify_specs()` eligibility
check and the same `_git_mv()` + `_append_ledger()` move mechanism `sweep()`
already uses — not a parallel implementation. Its one added risk, deliberately
accepted rather than engineered away: if `git mv` succeeds but the subsequent
`LEDGER.md` append raises, the result is reported as `"archived_unlogged"`
rather than silently folded into `"archived"` (which would imply a ledger
line exists) or `"git_mv_failed"` (which would misreport that the move never
happened). This is accepted, not rolled back, because a `git mv` is a
working-tree rename already tracked by git — an uncommitted, unlogged move
is visible and recoverable via `git status` — and a ledger write failing on a
small tracked markdown file immediately after a successful rename is
exceedingly rare and independent of the move itself.

Subcommands:
  scan  --specs-dir DIR --knowledge-dir DIR
    Report eligibility for every spec under DIR without mutating anything.
  sweep --specs-dir DIR --knowledge-dir DIR [--repo-root DIR]
    Perform the real `git mv` + ledger-append sweep. Per-spec destination
    collisions or `git mv` failures are skipped and reported; the sweep
    continues for the remaining specs rather than aborting (Business Rule 1's
    sibling operational rule — see spec.md Error / Edge Experience table).
  archive-one --specs-dir DIR --knowledge-dir DIR [--repo-root DIR]
              --spec-name NAME [--pr-number N]
    Archive exactly one named spec if (and only if) it is complete-family and
    not already archived. Idempotent and non-blocking, matching `sweep()`'s
    philosophy for a single spec instead of a full scan.

Every subcommand always prints one JSON object and exits 0 — this is a
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
SCHEMA_ARCHIVE_ONE = "archive-sweep-archive-one-v1"

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
    """Report eligibility for every spec under `specs_dir` — no mutation.

    Eligibility is complete-family status alone (Amendment 2026-08-04).
    `evidence` is still computed and reported for every complete-family spec
    so the sweep can record it as ledger enrichment, but an empty list no
    longer affects `eligible`.
    """
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
                "eligible": complete,
                "matched_value": row.get("matched_value"),
            }
        )
    return {
        "schema": SCHEMA_SCAN,
        "specs_dir": str(specs_dir),
        "knowledge_dir": str(knowledge_dir),
        "results": results,
        "eligible_count": sum(1 for r in results if r["eligible"]),
    }


def _git_mv(repo_root: Path, src: Path, dest: Path) -> subprocess.CompletedProcess[str]:
    """Shared `git mv` subprocess call for `sweep()` and `archive_one()` —
    keeping this in one place is what makes "same move mechanism" a fact
    rather than an aspiration between the batch and single-spec paths."""
    return subprocess.run(
        ["git", "mv", str(src), str(dest)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )


def _append_ledger(
    ledger_path: Path,
    spec_id: str,
    evidence: list[str],
    timestamp: str,
    pr_number: int | None = None,
    note: str | None = None,
) -> str:
    """Append one archive-audit line to `LEDGER.md`, creating it with its
    header on first write. Returns the exact line written (including its
    trailing newline) so callers can report it without re-deriving the
    format.

    `pr_number` is trailing and optional — every existing call site (the
    batch `sweep()` path) omits it, leaving that path's output byte-for-byte
    unchanged. When supplied, it appends a `, via PR #N` clause inside the
    existing evidence parenthetical rather than restructuring the line, so a
    future reader only ever needs to treat it as one optional trailing
    clause (spec.md Ledger annotation format).

    `note` is the second such clause, added 2026-08-12 on the same terms. It
    carries a spec's terminal status when that status is not a plain
    completion — `spec-status.py`'s COMPLETE_FAMILY_PREFIXES deliberately
    admits `Closed`, so a spec that was terminated without ever being built is
    complete-family and archives like any other. `LEDGER.md` is the one place a
    reader scans without opening every spec, and an unannotated line there
    reports "deliberately not built" exactly like "shipped". Omitted for plain
    completions, so every pre-existing line keeps its byte-for-byte format.
    """
    is_new = not ledger_path.exists()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_str = ", ".join(f"`{e}`" for e in evidence) if evidence else "no knowledge evidence yet"
    if pr_number is not None:
        evidence_str += f", via PR #{pr_number}"
    if note:
        evidence_str += f", {note}"
    line = f"- {timestamp} — `{spec_id}` archived (evidence: {evidence_str})\n"
    with ledger_path.open("a", encoding="utf-8") as fh:
        if is_new:
            fh.write("# Archive Ledger\n\n")
            fh.write(
                "Committed, append-only audit trail for `/status --archive`. "
                "One line per archived spec — never edit or reorder existing lines.\n\n"
            )
        fh.write(line)
    return line


def sweep(repo_root: Path, specs_dir: Path, knowledge_dir: Path) -> dict[str, Any]:
    """Perform the real git-mv + ledger-append sweep.

    Eligibility is complete-family status alone (Amendment 2026-08-04) — a
    spec is no longer skipped for lacking knowledge evidence; evidence, when
    present, is only recorded on the ledger line. Never raises for a
    per-spec failure: destination collisions and `git mv` failures are
    recorded and skipped, and the sweep continues with the remaining
    eligible specs (spec.md Error / Edge Experience table).
    """
    archive_dir = specs_dir / "archive"
    ledger_path = archive_dir / "LEDGER.md"
    scanned = scan(specs_dir, knowledge_dir)

    archived: list[dict[str, Any]] = []
    collisions: list[str] = []
    move_failures: list[dict[str, str]] = []

    for row in scanned["results"]:
        if not row["complete"]:
            continue

        spec_id = row["spec"]
        src = specs_dir / spec_id
        dest = archive_dir / spec_id

        if dest.exists():
            collisions.append(spec_id)
            continue

        archive_dir.mkdir(parents=True, exist_ok=True)
        proc = _git_mv(repo_root, src, dest)
        if proc.returncode != 0:
            move_failures.append({"spec": spec_id, "reason": proc.stderr.strip() or proc.stdout.strip()})
            continue

        timestamp = _now_iso()
        # Annotate only a non-plain terminal status. `Closed` is complete-family
        # by design, so the move is correct — the ledger line just has to say
        # the spec was never built rather than implying it shipped.
        matched = (row.get("matched_value") or "").strip()
        note = matched if matched.startswith("Closed") else None
        _append_ledger(ledger_path, spec_id, row["evidence"], timestamp, note=note)
        archived.append({"spec": spec_id, "evidence": row["evidence"], "timestamp": timestamp})

    summary = f"{len(archived)} specs archived"
    if collisions:
        summary += f", {len(collisions)} destination collision(s) skipped"
    if move_failures:
        summary += f", {len(move_failures)} git mv failure(s) skipped"
    if not collisions and not move_failures:
        summary += ", 0 skipped"

    return {
        "schema": SCHEMA_SWEEP,
        "archived": archived,
        "collisions": collisions,
        "move_failures": move_failures,
        "summary": summary,
    }


def archive_one(
    repo_root: Path,
    specs_dir: Path,
    knowledge_dir: Path,
    spec_name: str,
    pr_number: int | None = None,
) -> dict[str, Any]:
    """Archive exactly one named spec if (and only if) it is eligible.

    Single-spec-scoped sibling of `sweep()`, sharing its `_classify_specs()`
    eligibility check and its `_git_mv()` + `_append_ledger()` move
    mechanism rather than reimplementing either. Idempotent: an
    already-archived spec is a clean no-op, never an error; a not-yet
    complete-family spec is skipped even when named explicitly (Business
    Rule 1 — trigger is whole-spec status, never story-level). Never raises
    for a per-spec failure — `git mv` and ledger-append failures are
    reported via `status`, not propagated (Business Rule 7).

    Check ordering (arch-check CAUTION, cheapest first, no subprocess until
    eligibility is confirmed):
      1. Source/destination existence — distinguishes a clean prior archive
         (source absent, destination present -> `already_archived`) from a
         true collision (source present AND destination present ->
         `collision`, hard stop, matching `sweep()`'s collision philosophy).
      2. Only when the source exists and the destination does not: consult
         `_classify_specs()` for complete-family status. A name absent from
         both `specs_dir` and the archive (never existed, or a typo) falls
         through this same branch to `not_eligible` rather than crashing.
    """
    archive_dir = specs_dir / "archive"
    ledger_path = archive_dir / "LEDGER.md"
    src = specs_dir / spec_name
    dest = archive_dir / spec_name

    src_exists = src.exists()
    dest_exists = dest.exists()

    if not src_exists and dest_exists:
        return {
            "schema": SCHEMA_ARCHIVE_ONE,
            "status": "already_archived",
            "spec": spec_name,
            "ledger_line": None,
        }

    if src_exists and dest_exists:
        return {
            "schema": SCHEMA_ARCHIVE_ONE,
            "status": "collision",
            "spec": spec_name,
            "ledger_line": None,
        }

    if not src_exists:
        # Absent from both specs_dir and archive_dir — never existed (or a
        # typo). Falls through naturally rather than raising.
        return {
            "schema": SCHEMA_ARCHIVE_ONE,
            "status": "not_eligible",
            "spec": spec_name,
            "ledger_line": None,
        }

    rows = {row["spec"]: row for row in _classify_specs(specs_dir)}
    row = rows.get(spec_name)
    if row is None or not row["complete"]:
        return {
            "schema": SCHEMA_ARCHIVE_ONE,
            "status": "not_eligible",
            "spec": spec_name,
            "ledger_line": None,
        }

    evidence = find_knowledge_evidence(knowledge_dir, spec_name)

    archive_dir.mkdir(parents=True, exist_ok=True)
    proc = _git_mv(repo_root, src, dest)
    if proc.returncode != 0:
        return {
            "schema": SCHEMA_ARCHIVE_ONE,
            "status": "git_mv_failed",
            "spec": spec_name,
            "ledger_line": None,
            "reason": proc.stderr.strip() or proc.stdout.strip(),
        }

    timestamp = _now_iso()
    try:
        ledger_line = _append_ledger(ledger_path, spec_name, evidence, timestamp, pr_number)
    except Exception:
        # Move already succeeded — accepted rare risk, see module docstring.
        # Business Rule 7: never raise uncaught, never block a release.
        return {
            "schema": SCHEMA_ARCHIVE_ONE,
            "status": "archived_unlogged",
            "spec": spec_name,
            "ledger_line": None,
        }

    return {
        "schema": SCHEMA_ARCHIVE_ONE,
        "status": "archived",
        "spec": spec_name,
        "ledger_line": ledger_line,
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

    p_archive_one = sub.add_parser(
        "archive-one", help="archive exactly one named spec, if eligible"
    )
    p_archive_one.add_argument("--specs-dir", required=True, type=Path)
    p_archive_one.add_argument("--knowledge-dir", required=True, type=Path)
    p_archive_one.add_argument("--repo-root", default=Path("."), type=Path)
    p_archive_one.add_argument("--spec-name", required=True)
    p_archive_one.add_argument("--pr-number", default=None, type=int)

    args = parser.parse_args(argv)

    if args.command == "scan":
        print(json.dumps(scan(args.specs_dir, args.knowledge_dir)))
    elif args.command == "sweep":
        print(json.dumps(sweep(args.repo_root, args.specs_dir, args.knowledge_dir)))
    elif args.command == "archive-one":
        print(
            json.dumps(
                archive_one(
                    args.repo_root,
                    args.specs_dir,
                    args.knowledge_dir,
                    args.spec_name,
                    args.pr_number,
                )
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
