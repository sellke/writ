#!/usr/bin/env python3
"""Post-sweep regression guard for the real dogfood archival (Story 6).

Unlike every other eval-*.py in this spec, this scenario deliberately runs
against THIS repo's real `.writ/specs/` tree — not a disposable fixture — to
prove the shipped mechanism behaves correctly against production data, not
just synthetic cases. It is read-only: it never calls `archive-sweep.py
sweep` (which mutates), only `scan` and direct glob/path assertions.

Covers Story 6 Acceptance Criterion 4: after `.writ/specs/archive/` is
populated by the real sweep, `/status`'s active-spec detection,
`create-spec`'s overlap scan, `implement-spec`'s spec listing, and
`verify-spec --all`'s folder enumeration must all keep excluding archived
specs via the single-level glob alone — no regression, no misclassification.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = PROJECT_ROOT / ".writ" / "specs"
KNOWLEDGE_DIR = PROJECT_ROOT / ".writ" / "knowledge"
ARCHIVE_DIR = SPECS_DIR / "archive"

# The three specs this story's real dogfood run archived — see
# .writ/specs/archive/LEDGER.md and story-6-dogfood-sweep.md "What Was Built".
EXPECTED_ARCHIVED = {
    "2026-03-27-context-engine",
    "2026-04-24-phase4-production-grade-substrate",
    "2026-07-18-artifact-integrity-handshake",
}

passed = 0
failed = 0


def emit(name: str, ok: bool, detail: object = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS\t{name}")
    else:
        failed += 1
        safe = str(detail).replace("\n", "\\n").replace("\t", " ")
        print(f"FAIL\t{name}\t{safe}")


def scenario_archived_specs_exist_and_are_readable() -> None:
    for spec_id in sorted(EXPECTED_ARCHIVED):
        spec_file = ARCHIVE_DIR / spec_id / "spec.md"
        emit(
            f"archived-spec-readable:{spec_id}",
            spec_file.is_file() and len(spec_file.read_text(encoding="utf-8")) > 0,
            str(spec_file),
        )


def scenario_ledger_has_one_line_per_archived_spec() -> None:
    ledger = ARCHIVE_DIR / "LEDGER.md"
    if not ledger.is_file():
        emit("ledger-exists", False, str(ledger))
        return
    text = ledger.read_text(encoding="utf-8")
    for spec_id in sorted(EXPECTED_ARCHIVED):
        emit(f"ledger-cites:{spec_id}", text.count(f"`{spec_id}`") == 1, text)


def scenario_spec_status_scan_excludes_archived_specs() -> None:
    proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "spec-status.py"), "scan", "--specs-dir", str(SPECS_DIR)],
        capture_output=True,
        text=True,
    )
    emit("spec-status-scan-exits-zero", proc.returncode == 0, proc.stdout + proc.stderr)
    if proc.returncode != 0:
        return
    payload = json.loads(proc.stdout)
    found = {r["spec"] for r in payload["results"]}
    emit(
        "spec-status-scan-excludes-all-archived",
        found.isdisjoint(EXPECTED_ARCHIVED),
        sorted(found & EXPECTED_ARCHIVED),
    )
    emit("spec-status-scan-excludes-archive-folder-itself", "archive" not in found, sorted(found))


def scenario_archive_sweep_rescan_is_idempotent() -> None:
    """A second `scan` (never `sweep`) must not report any of the three as
    newly eligible-and-active — they're gone from the active corpus entirely,
    which is a stronger guarantee than merely being ineligible again."""
    proc = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "archive-sweep.py"),
            "scan",
            "--specs-dir",
            str(SPECS_DIR),
            "--knowledge-dir",
            str(KNOWLEDGE_DIR),
        ],
        capture_output=True,
        text=True,
    )
    emit("archive-sweep-rescan-exits-zero", proc.returncode == 0, proc.stdout + proc.stderr)
    if proc.returncode != 0:
        return
    payload = json.loads(proc.stdout)
    found = {r["spec"] for r in payload["results"]}
    emit(
        "archive-sweep-rescan-no-longer-sees-archived-specs",
        found.isdisjoint(EXPECTED_ARCHIVED),
        sorted(found & EXPECTED_ARCHIVED),
    )


def scenario_verify_spec_glob_shape_excludes_archive_on_real_tree() -> None:
    """Mirrors verify-spec.md Step 1.1's documented enumeration contract
    (.writ/specs/*/ folders containing spec.md) directly against the real,
    now-populated tree — not a fixture."""
    folder_matches = {p.name for p in SPECS_DIR.glob("*/") if p.is_dir()}
    emit(
        "verify-spec-shape-archive-is-a-plain-sibling-folder",
        "archive" in folder_matches,
        sorted(folder_matches),
    )
    spec_md_matches = {p.parent.name for p in SPECS_DIR.glob("*/spec.md")}
    emit(
        "verify-spec-shape-excludes-archived-specs-from-spec-md-matches",
        spec_md_matches.isdisjoint(EXPECTED_ARCHIVED),
        sorted(spec_md_matches & EXPECTED_ARCHIVED),
    )
    emit(
        "verify-spec-shape-archive-folder-has-no-direct-spec-md",
        not (SPECS_DIR / "archive" / "spec.md").exists(),
        str(SPECS_DIR / "archive" / "spec.md"),
    )


def scenario_git_status_shows_renames_not_delete_add() -> None:
    """The dogfood commit must have moved files as renames (history-preserving),
    not as delete+add pairs — checked against the commit's own diff stat."""
    proc = subprocess.run(
        ["git", "log", "--find-renames", "--diff-filter=R", "-1", "--stat", "--", str(SPECS_DIR)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    emit(
        "dogfood-commit-recorded-as-renames",
        proc.returncode == 0 and "=>" in proc.stdout and "archive" in proc.stdout,
        proc.stdout + proc.stderr,
    )


def main() -> int:
    if not ARCHIVE_DIR.is_dir():
        emit(
            "archive-dir-exists",
            False,
            f"{ARCHIVE_DIR} not found — has the Story 6 dogfood sweep been run yet?",
        )
        return 1
    scenario_archived_specs_exist_and_are_readable()
    scenario_ledger_has_one_line_per_archived_spec()
    scenario_spec_status_scan_excludes_archived_specs()
    scenario_archive_sweep_rescan_is_idempotent()
    scenario_verify_spec_glob_shape_excludes_archive_on_real_tree()
    scenario_git_status_shows_renames_not_delete_add()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
