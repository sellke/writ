"""Fixture tests for the mechanical roadmap-sync script (`/release`'s
"is this spec recorded anywhere" gap for inter-phase infrastructure).

Covers `check`'s read-only detection (full name, date-stripped slug, missing
file), `append_row`'s idempotent mutation (row insertion, revision-log
insertion, Last-Updated bump, already-recorded no-op, missing-marker
graceful failure), and CLI smoke tests. Imported by path, same recipe as
`test_resolve_spec_reference.py` (hyphenated filename).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "roadmap-sync.py"
SPEC = importlib.util.spec_from_file_location("roadmap_sync", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
roadmap_sync_mod = importlib.util.module_from_spec(SPEC)
sys.modules["roadmap_sync"] = roadmap_sync_mod
SPEC.loader.exec_module(roadmap_sync_mod)

check = roadmap_sync_mod.check
append_row = roadmap_sync_mod.append_row
is_recorded = roadmap_sync_mod.is_recorded

FIXTURE_ROADMAP = """\
# Writ — Product Roadmap

> Based on Product Contract: 2026-02-27
> Last Updated: 2026-08-12
> Cadence: Steady

### Revision Log

| Date | Change |
|---|---|
| 2026-08-12 | Some prior change. |

---

## Shipped Phases (condensed history)

| Phase | Delivered | Version |
|---|---|---|
| **1 — Foundation** | Some feature | v0.5-0.8 |
| **— Existing inter-phase item** | 2026-01-01-existing-spec landed | v0.30.0 |

> Rows below the phase rows are inter-phase infrastructure — shipped through the normal spec pipeline between roadmap phases, recorded here so no Complete spec lacks a roadmap home (added 2026-08-12 reconcile pass).

---

## Phase 1: Foundation — Complete
"""


def write_fixture(tmp_path: Path) -> Path:
    roadmap = tmp_path / "roadmap.md"
    roadmap.write_text(FIXTURE_ROADMAP, encoding="utf-8")
    return roadmap


# ---------- is_recorded / check ----------


def test_is_recorded_true_for_full_folder_name() -> None:
    assert is_recorded(FIXTURE_ROADMAP, "2026-01-01-existing-spec") is True


def test_is_recorded_true_for_date_stripped_slug() -> None:
    text = "Completed the existing-spec work in this cycle."
    assert is_recorded(text, "2026-01-01-existing-spec") is True


def test_is_recorded_false_when_absent() -> None:
    assert is_recorded(FIXTURE_ROADMAP, "2026-08-12-unrelated-spec") is False


def test_check_reports_already_recorded(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)
    result = check(roadmap, "2026-01-01-existing-spec")
    assert result["already_recorded"] is True
    assert result["spec"] == "2026-01-01-existing-spec"


def test_check_reports_not_recorded(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)
    result = check(roadmap, "2026-08-13-brand-new-spec")
    assert result["already_recorded"] is False


def test_check_missing_roadmap_degrades_to_not_recorded(tmp_path: Path) -> None:
    result = check(tmp_path / "does-not-exist.md", "2026-08-13-anything")
    assert result["already_recorded"] is False


# ---------- append_row ----------


def test_append_row_inserts_before_marker_and_after_last_row(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)

    result = append_row(
        roadmap,
        spec_name="2026-08-13-brand-new-spec",
        title="Brand New Spec",
        description="Fixed a real bug in the thing.",
        version="0.31.1",
    )

    assert result["status"] == "appended"
    text = roadmap.read_text(encoding="utf-8")
    lines = text.splitlines()
    marker_idx = next(i for i, l in enumerate(lines) if "Rows below the phase rows" in l)
    new_row_idx = next(i for i, l in enumerate(lines) if "Brand New Spec" in l)
    existing_row_idx = next(
        i for i, l in enumerate(lines) if "Existing inter-phase item" in l
    )
    # New row lands after the existing last row and before the marker.
    assert existing_row_idx < new_row_idx < marker_idx
    assert (
        "| **— Brand New Spec** <!-- 2026-08-13-brand-new-spec --> | "
        "Fixed a real bug in the thing. | v0.31.1 |" in text
    )


def test_append_row_embeds_invisible_marker_so_a_later_check_finds_it(tmp_path: Path) -> None:
    """The whole point of the marker: a human-authored title never reliably
    substring-matches its own spec's dated folder name (real bug found
    dogfooding this script against the actual roadmap.md — "Machine-evaluable
    exit criteria" does not contain "machine-evaluable-exit-criteria"). The
    row this script writes must be self-detecting on a later `check` call."""
    roadmap = write_fixture(tmp_path)

    append_row(
        roadmap,
        spec_name="2026-08-13-brand-new-spec",
        title="Totally Different Wording Entirely",
        description="desc",
        version="0.31.1",
    )

    result = check(roadmap, "2026-08-13-brand-new-spec")
    assert result["already_recorded"] is True


def test_append_row_adds_revision_log_row_after_header_separator(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)

    append_row(
        roadmap,
        spec_name="2026-08-13-brand-new-spec",
        title="Brand New Spec",
        description="Fixed a real bug in the thing.",
        version="0.31.1",
    )

    lines = roadmap.read_text(encoding="utf-8").splitlines()
    sep_idx = next(i for i, l in enumerate(lines) if l.strip().startswith("|---"))
    new_row_idx = next(
        i for i, l in enumerate(lines) if "brand-new-spec" in l and l.startswith("|")
    )
    prior_row_idx = next(i for i, l in enumerate(lines) if "Some prior change." in l)
    # New revision-log row sits immediately after the separator, above the prior entry.
    assert sep_idx < new_row_idx < prior_row_idx


def test_append_row_bumps_last_updated(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)

    append_row(
        roadmap,
        spec_name="2026-08-13-brand-new-spec",
        title="Brand New Spec",
        description="Fixed a real bug in the thing.",
        version="0.31.1",
    )

    text = roadmap.read_text(encoding="utf-8")
    assert "> Last Updated: 2026-08-12" not in text
    assert "> Last Updated: " in text


def test_append_row_is_idempotent_no_duplicate_on_second_call(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)

    first = append_row(
        roadmap,
        spec_name="2026-08-13-brand-new-spec",
        title="Brand New Spec",
        description="Fixed a real bug in the thing.",
        version="0.31.1",
    )
    second = append_row(
        roadmap,
        spec_name="2026-08-13-brand-new-spec",
        title="Brand New Spec (renamed)",
        description="Different description.",
        version="0.31.2",
    )

    assert first["status"] == "appended"
    assert second["status"] == "already_recorded"
    text = roadmap.read_text(encoding="utf-8")
    assert text.count("Brand New Spec") == 1
    assert "renamed" not in text


def test_append_row_skips_specs_already_recorded_before_first_call(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)

    result = append_row(
        roadmap,
        spec_name="2026-01-01-existing-spec",
        title="Should Not Land",
        description="This must not be inserted.",
        version="0.31.1",
    )

    assert result["status"] == "already_recorded"
    text = roadmap.read_text(encoding="utf-8")
    assert "Should Not Land" not in text


def test_append_row_missing_marker_reports_marker_not_found(tmp_path: Path) -> None:
    roadmap = tmp_path / "roadmap.md"
    roadmap.write_text("# Roadmap\n\nNo marker paragraph here.\n", encoding="utf-8")

    result = append_row(
        roadmap,
        spec_name="2026-08-13-brand-new-spec",
        title="Brand New Spec",
        description="desc",
        version="0.31.1",
    )

    assert result["status"] == "marker_not_found"
    # No mutation on failure.
    assert roadmap.read_text(encoding="utf-8") == "# Roadmap\n\nNo marker paragraph here.\n"


def test_append_row_missing_roadmap_file_reports_not_found(tmp_path: Path) -> None:
    result = append_row(
        tmp_path / "does-not-exist.md",
        spec_name="2026-08-13-brand-new-spec",
        title="Brand New Spec",
        description="desc",
        version="0.31.1",
    )

    assert result["status"] == "roadmap_not_found"


def test_append_row_custom_revision_note_used_verbatim(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)

    append_row(
        roadmap,
        spec_name="2026-08-13-brand-new-spec",
        title="Brand New Spec",
        description="desc",
        version="0.31.1",
        revision_note="Custom note for this release.",
    )

    text = roadmap.read_text(encoding="utf-8")
    assert "Custom note for this release." in text


# ---------- CLI smoke tests ----------


def test_cli_check_smoke_invocation(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "check",
            "--roadmap",
            str(roadmap),
            "--spec-name",
            "2026-01-01-existing-spec",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert '"already_recorded": true' in proc.stdout


def test_cli_append_row_smoke_invocation(tmp_path: Path) -> None:
    roadmap = write_fixture(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "append-row",
            "--roadmap",
            str(roadmap),
            "--spec-name",
            "2026-08-13-brand-new-spec",
            "--title",
            "Brand New Spec",
            "--description",
            "desc",
            "--version",
            "0.31.1",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert '"status": "appended"' in proc.stdout


def test_cli_resolve_help_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, str(MODULE_PATH), "append-row", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "--spec-name" in proc.stdout


def test_cli_never_raises_on_nonexistent_roadmap(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "check",
            "--roadmap",
            str(tmp_path / "nope.md"),
            "--spec-name",
            "anything",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert '"already_recorded": false' in proc.stdout
