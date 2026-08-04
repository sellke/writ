#!/usr/bin/env python3
"""Fixture scenario for the spec-lifecycle documentation contract (Story 3).

Proves — independent of scripts/spec-status.py and scripts/archive-sweep.py's
own implementations — that the raw stdlib glob shape `.writ/specs/*/spec.md`
documented in `.writ/docs/spec-lifecycle.md` and `commands/verify-spec.md`
Step 1.1 genuinely excludes `.writ/specs/archive/<name>/spec.md` and
`.writ/specs/<name>/backups/<timestamp>/spec-lite.md`. This is deliberately a
second, independent proof of the glob-depth invariant (not a re-run of the
archive-sweep scenarios), guarding against a future contributor "fixing" the
glob into something recursive without re-deriving why depth matters.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

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


def scenario_single_level_glob_excludes_archive_and_backups() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        specs_dir = Path(tmp) / ".writ" / "specs"

        active = specs_dir / "2026-01-01-active-spec"
        active.mkdir(parents=True)
        (active / "spec.md").write_text("> **Status:** Not Started\n", encoding="utf-8")
        (active / "spec-lite.md").write_text("lite\n", encoding="utf-8")

        archived = specs_dir / "archive" / "2026-01-02-archived-spec"
        archived.mkdir(parents=True)
        (archived / "spec.md").write_text("> **Status:** Complete\n", encoding="utf-8")

        backup = active / "backups" / "20260101-000000"
        backup.mkdir(parents=True)
        (backup / "spec-lite.md").write_text("old lite\n", encoding="utf-8")

        spec_md_matches = {p.parent.name for p in specs_dir.glob("*/spec.md")}
        emit(
            "single-level-spec-md-glob-excludes-archive",
            spec_md_matches == {"2026-01-01-active-spec"},
            sorted(spec_md_matches),
        )

        spec_lite_matches = {p.parent.name for p in specs_dir.glob("*/spec-lite.md")}
        emit(
            "single-level-spec-lite-glob-excludes-nested-backups",
            spec_lite_matches == {"2026-01-01-active-spec"},
            sorted(spec_lite_matches),
        )

        folder_matches = {p.name for p in specs_dir.glob("*/") if p.is_dir()}
        emit(
            "single-level-folder-glob-includes-archive-as-a-sibling-not-a-spec",
            "archive" in folder_matches and "2026-01-01-active-spec" in folder_matches,
            sorted(folder_matches),
        )


def main() -> int:
    scenario_single_level_glob_excludes_archive_and_backups()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
