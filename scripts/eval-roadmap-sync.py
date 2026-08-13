#!/usr/bin/env python3
"""Smoke-level fixture scenarios for `/release` Step 3.1b's roadmap-sync
step (mechanical inter-phase-infrastructure recording).

Deliberately narrow: the full scenario matrix (19 cases — insertion
position, revision-log placement, Last-Updated bump, idempotency, missing
marker, missing file, the invisible-marker round-trip) already lives in
`scripts/tests/test_roadmap_sync.py` and is not re-derived here. This
script's only job is confirming `scripts/roadmap-sync.py` still executes
end-to-end under `eval.sh`'s scenario-TSV harness. The check function's real
payload is the `require_literal`/`forbid_literal` prose-pinning of
`commands/release.md`'s Step 3.1b, which lives directly in
`scripts/eval.sh`'s `check_roadmap_sync()`, not in this file.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

_MODULE_PATH = Path(__file__).with_name("roadmap-sync.py")
_SPEC = importlib.util.spec_from_file_location("roadmap_sync", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_roadmap_sync = importlib.util.module_from_spec(_SPEC)
sys.modules["roadmap_sync"] = _roadmap_sync
_SPEC.loader.exec_module(_roadmap_sync)

check = _roadmap_sync.check
append_row = _roadmap_sync.append_row

FIXTURE_ROADMAP = """\
# Writ — Product Roadmap

> Last Updated: 2026-08-12

### Revision Log

| Date | Change |
|---|---|
| 2026-08-12 | Some prior change. |

## Shipped Phases (condensed history)

| Phase | Delivered | Version |
|---|---|---|
| **1 — Foundation** | Some feature | v0.5-0.8 |

> Rows below the phase rows are inter-phase infrastructure — shipped through the normal spec pipeline between roadmap phases, recorded here so no Complete spec lacks a roadmap home (added 2026-08-12 reconcile pass).
"""

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


def scenario_happy_path_append_and_self_detect() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        roadmap = Path(tmp) / "roadmap.md"
        roadmap.write_text(FIXTURE_ROADMAP, encoding="utf-8")

        result = append_row(
            roadmap,
            spec_name="2026-08-13-smoke-spec",
            title="Smoke Test Spec",
            description="Exercises the append path end to end.",
            version="0.31.1",
        )
        recheck = check(roadmap, "2026-08-13-smoke-spec")
        emit(
            "happy-path-append-then-self-detected",
            result.get("status") == "appended" and recheck.get("already_recorded") is True,
            (result, recheck),
        )


def scenario_idempotent_no_duplicate_row() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        roadmap = Path(tmp) / "roadmap.md"
        roadmap.write_text(FIXTURE_ROADMAP, encoding="utf-8")

        append_row(
            roadmap,
            spec_name="2026-08-13-smoke-spec",
            title="Smoke Test Spec",
            description="desc",
            version="0.31.1",
        )
        second = append_row(
            roadmap,
            spec_name="2026-08-13-smoke-spec",
            title="Smoke Test Spec",
            description="desc",
            version="0.31.1",
        )
        text = roadmap.read_text(encoding="utf-8")
        emit(
            "idempotent-second-call-no-duplicate",
            second.get("status") == "already_recorded" and text.count("Smoke Test Spec") == 1,
            second,
        )


def scenario_missing_marker_reports_without_mutating() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        roadmap = Path(tmp) / "roadmap.md"
        roadmap.write_text("# Roadmap\n\nNo marker here.\n", encoding="utf-8")

        result = append_row(
            roadmap,
            spec_name="2026-08-13-smoke-spec",
            title="Smoke Test Spec",
            description="desc",
            version="0.31.1",
        )
        emit(
            "missing-marker-reports-marker-not-found",
            result.get("status") == "marker_not_found"
            and roadmap.read_text(encoding="utf-8") == "# Roadmap\n\nNo marker here.\n",
            result,
        )


def main() -> int:
    scenario_happy_path_append_and_self_detect()
    scenario_idempotent_no_duplicate_row()
    scenario_missing_marker_reports_without_mutating()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
