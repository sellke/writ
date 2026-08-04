"""Fixture tests for the format-tolerant spec-status detector (Story 1).

Covers the five real-world header variants from spec.md's "Why This Exists"
audit table, plus an explicit not-complete case and the conservative
missing-header default.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "spec-status.py"
SPEC = importlib.util.spec_from_file_location("spec_status", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
spec_status = importlib.util.module_from_spec(SPEC)
sys.modules["spec_status"] = spec_status
SPEC.loader.exec_module(spec_status)


def make_spec(tmp_path: Path, header: str | None, body: str = "") -> Path:
    folder = tmp_path / "2026-01-01-fixture-spec"
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["# Spec: Fixture"]
    if header is not None:
        lines.append(header)
    lines.append("")
    lines.append("## Contract (Locked)")
    lines.append(body)
    spec_path = folder / "spec.md"
    spec_path.write_text("\n".join(lines), encoding="utf-8")
    return spec_path


@pytest.mark.parametrize(
    "header,expected",
    [
        ("> **Status:** Complete", True),
        ("> **Status:** Completed ✅", True),
        ("> Status: Complete", True),
        ("> Status: Closed — Abandoned (2026-07-18). Never executed.", True),
        ("> **Status:** Not Started", False),
    ],
    ids=[
        "bold-complete",
        "bold-completed-emoji",
        "unbold-complete",
        "unbold-closed-abandoned",
        "bold-not-started",
    ],
)
def test_header_variants(tmp_path: Path, header: str, expected: bool) -> None:
    spec_path = make_spec(tmp_path, header)
    result = spec_status.is_complete_file(spec_path)
    assert result["complete"] is expected


def test_absent_header_is_conservatively_not_complete(tmp_path: Path) -> None:
    spec_path = make_spec(tmp_path, None)
    result = spec_status.is_complete_file(spec_path)
    assert result["complete"] is False
    assert result["header_line"] is None


def test_status_mentioned_in_body_is_not_a_false_positive(tmp_path: Path) -> None:
    """A stray 'Complete' in the document body must never leak into detection."""
    spec_path = make_spec(
        tmp_path,
        "> **Status:** Not Started",
        body="This work will be marked Status: Complete once shipped.",
    )
    result = spec_status.is_complete_file(spec_path)
    assert result["complete"] is False


def test_missing_file_is_a_contract_error(tmp_path: Path) -> None:
    with pytest.raises(spec_status.ContractError) as exc_info:
        spec_status.is_complete_file(tmp_path / "nope" / "spec.md")
    assert exc_info.value.code == "missing_spec"


def test_scan_single_level_glob_only(tmp_path: Path) -> None:
    make_spec(tmp_path, "> **Status:** Complete")
    nested = tmp_path / "archive" / "2026-02-02-archived"
    nested.mkdir(parents=True)
    (nested / "spec.md").write_text("> **Status:** Complete\n", encoding="utf-8")

    result = spec_status.scan_dir(tmp_path)
    spec_ids = {r["spec"] for r in result["results"]}
    assert "2026-01-01-fixture-spec" in spec_ids
    assert "archive" not in spec_ids
    assert result["complete_count"] == 1


def test_scan_missing_dir_is_a_contract_error(tmp_path: Path) -> None:
    with pytest.raises(spec_status.ContractError) as exc_info:
        spec_status.scan_dir(tmp_path / "nonexistent")
    assert exc_info.value.code == "missing_specs_dir"
