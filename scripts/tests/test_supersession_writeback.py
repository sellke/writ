"""Round-trip tests for the supersession reverse-pointer write-back (Story 5).

Covers: single-target write-back, idempotent re-run, multi-target lines
(spec + ADR), pre-existing `Superseded by:` update-in-place, and graceful
handling of a broken/missing reference.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "supersession-writeback.py"
SPEC = importlib.util.spec_from_file_location("supersession_writeback", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
writeback = importlib.util.module_from_spec(SPEC)
sys.modules["supersession_writeback"] = writeback
SPEC.loader.exec_module(writeback)


def make_spec(specs_dir: Path, folder_name: str, header_lines: list[str], body: str = "Body.\n") -> Path:
    folder = specs_dir / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    lines = [f"# Spec: {folder_name}", *header_lines, "", "## Contract (Locked)", body]
    spec_path = folder / "spec.md"
    spec_path.write_text("\n".join(lines), encoding="utf-8")
    return spec_path


def test_amends_writes_superseded_by_onto_older_spec(tmp_path: Path) -> None:
    specs_dir = tmp_path / ".writ" / "specs"
    older = make_spec(specs_dir, "2026-07-11-leanness-guardian", ["> **Status:** Complete"])
    newer = make_spec(
        specs_dir,
        "2026-07-26-leanness-instrumentation",
        [
            "> **Status:** Completed ✅",
            "> **Amends:** [2026-07-11-leanness-guardian](../2026-07-11-leanness-guardian/spec.md)",
        ],
    )

    result = writeback.apply(newer)

    assert result["written"] == [str(older)]
    assert result["broken"] == []
    assert result["skipped_other"] == []

    older_text = older.read_text(encoding="utf-8")
    assert "> **Superseded by:** [2026-07-26-leanness-instrumentation](../2026-07-26-leanness-instrumentation/spec.md)" in older_text
    # The older spec's own Status: line is untouched — never rewritten.
    assert "> **Status:** Complete" in older_text
    assert older_text.count("Superseded by:") == 1


def test_write_back_is_idempotent_on_rerun(tmp_path: Path) -> None:
    specs_dir = tmp_path / ".writ" / "specs"
    older = make_spec(specs_dir, "older-spec", ["> **Status:** Complete"])
    newer = make_spec(
        specs_dir, "newer-spec", ["> **Status:** Not Started", "> **Amends:** [older-spec](../older-spec/spec.md)"]
    )

    first = writeback.apply(newer)
    assert first["written"] == [str(older)]

    second = writeback.apply(newer)
    assert second["written"] == []
    assert second["unchanged"] == [str(older)]
    assert older.read_text(encoding="utf-8").count("Superseded by:") == 1


def test_multi_target_line_only_writes_back_to_the_spec_target(tmp_path: Path) -> None:
    """Amends: may reference a spec AND an ADR — only the spec gets a reverse pointer."""
    specs_dir = tmp_path / ".writ" / "specs"
    decisions_dir = tmp_path / ".writ" / "decision-records"
    decisions_dir.mkdir(parents=True)
    adr = decisions_dir / "adr-015-leanness-self-governance.md"
    adr.write_text("# ADR-015\n", encoding="utf-8")

    older = make_spec(specs_dir, "2026-07-11-leanness-guardian", ["> **Status:** Complete"])
    newer = make_spec(
        specs_dir,
        "2026-07-26-leanness-instrumentation",
        [
            "> **Status:** Completed ✅",
            "> **Amends:** [2026-07-11-leanness-guardian](../2026-07-11-leanness-guardian/spec.md) / "
            "[ADR-015](../../decision-records/adr-015-leanness-self-governance.md)",
        ],
    )

    result = writeback.apply(newer)

    assert result["written"] == [str(older)]
    assert result["skipped_other"] == ["../../decision-records/adr-015-leanness-self-governance.md"]
    assert result["broken"] == []
    # The ADR file itself must never be modified — forward-only, no reverse pointer.
    assert adr.read_text(encoding="utf-8") == "# ADR-015\n"


def test_existing_superseded_by_is_replaced_not_duplicated(tmp_path: Path) -> None:
    specs_dir = tmp_path / ".writ" / "specs"
    older = make_spec(
        specs_dir,
        "older-spec",
        ["> **Status:** Complete", "> **Superseded by:** [some-stale-spec](../some-stale-spec/spec.md)"],
    )
    newer = make_spec(specs_dir, "newer-spec", ["> **Amends:** [older-spec](../older-spec/spec.md)"])

    result = writeback.apply(newer)

    assert result["written"] == [str(older)]
    older_text = older.read_text(encoding="utf-8")
    assert older_text.count("Superseded by:") == 1
    assert "newer-spec" in older_text
    assert "some-stale-spec" not in older_text
    assert "> **Status:** Complete" in older_text


def test_broken_reference_is_skipped_without_raising_or_corrupting(tmp_path: Path) -> None:
    specs_dir = tmp_path / ".writ" / "specs"
    newer = make_spec(
        specs_dir,
        "newer-spec",
        ["> **Amends:** [nonexistent-spec](../nonexistent-spec/spec.md)"],
    )

    result = writeback.apply(newer)

    assert result["broken"] == ["../nonexistent-spec/spec.md"]
    assert result["written"] == []
    # The new spec's own file is never touched by a broken reference either.
    assert "Superseded by:" not in newer.read_text(encoding="utf-8")


def test_extends_field_also_triggers_write_back(tmp_path: Path) -> None:
    specs_dir = tmp_path / ".writ" / "specs"
    older = make_spec(specs_dir, "older-spec", ["> **Status:** Complete"])
    newer = make_spec(specs_dir, "newer-spec", ["> **Extends:** [older-spec](../older-spec/spec.md)"])

    result = writeback.apply(newer)

    assert result["written"] == [str(older)]
    assert "> **Superseded by:** [newer-spec](../newer-spec/spec.md)" in older.read_text(encoding="utf-8")


def test_no_supersession_line_is_a_clean_no_op(tmp_path: Path) -> None:
    specs_dir = tmp_path / ".writ" / "specs"
    newer = make_spec(specs_dir, "standalone-spec", ["> **Status:** Not Started"])

    scanned = writeback.scan(newer)
    assert scanned["targets"] == []

    result = writeback.apply(newer)
    assert result["written"] == []
    assert result["broken"] == []
    assert result["skipped_other"] == []


def test_missing_new_spec_file_is_a_contract_error(tmp_path: Path) -> None:
    with pytest.raises(writeback.ContractError) as exc_info:
        writeback.scan(tmp_path / "nope" / "spec.md")
    assert exc_info.value.code == "missing_spec"
