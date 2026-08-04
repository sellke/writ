#!/usr/bin/env python3
"""CLI-contract scenario for the supersession write-back helper (Story 5).

Complements scripts/tests/test_supersession_writeback.py (which exercises the
Python functions directly) by proving the same round trip through the actual
`scan`/`apply` CLI subcommands invoked by commands/create-spec.md Step 2.4b
and commands/edit-spec.md Step 2.2.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HELPER = PROJECT_ROOT / "scripts" / "supersession-writeback.py"

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


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True,
        text=True,
    )


def make_spec(specs_dir: Path, folder: str, header_lines: list[str]) -> Path:
    d = specs_dir / folder
    d.mkdir(parents=True)
    lines = [f"# Spec: {folder}", *header_lines, "", "## Contract (Locked)", "Body.\n"]
    path = d / "spec.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def scenario_cli_scan_and_apply_round_trip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        specs_dir = Path(tmp) / ".writ" / "specs"
        older = make_spec(specs_dir, "older-spec", ["> **Status:** Complete"])
        newer = make_spec(
            specs_dir, "newer-spec", ["> **Amends:** [older-spec](../older-spec/spec.md)"]
        )

        scan_result = run("scan", "--new-spec-file", str(newer))
        emit(
            "cli-scan-exits-zero",
            scan_result.returncode == 0,
            scan_result.stdout + scan_result.stderr,
        )
        scan_payload = json.loads(scan_result.stdout) if scan_result.returncode == 0 else {}
        emit(
            "cli-scan-reports-resolvable-target",
            scan_payload.get("resolvable_count") == 1,
            scan_payload,
        )

        apply_result = run("apply", "--new-spec-file", str(newer))
        emit(
            "cli-apply-exits-zero",
            apply_result.returncode == 0,
            apply_result.stdout + apply_result.stderr,
        )
        apply_payload = json.loads(apply_result.stdout) if apply_result.returncode == 0 else {}
        emit(
            "cli-apply-writes-target",
            apply_payload.get("written") == [str(older.resolve())],
            apply_payload,
        )

        older_text = older.read_text(encoding="utf-8")
        emit(
            "cli-apply-preserves-status-line",
            "> **Status:** Complete" in older_text,
            older_text,
        )
        emit(
            "cli-apply-writes-superseded-by",
            "> **Superseded by:** [newer-spec](../newer-spec/spec.md)" in older_text,
            older_text,
        )


def scenario_cli_missing_file_is_a_contract_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "nope" / "spec.md"
        result = run("scan", "--new-spec-file", str(missing))
        emit(
            "cli-missing-file-exits-nonzero",
            result.returncode != 0,
            result.stdout + result.stderr,
        )
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
        emit(
            "cli-missing-file-reports-blocker-code",
            payload.get("blocker", {}).get("code") == "missing_spec",
            payload,
        )


def main() -> int:
    if not HELPER.is_file():
        emit("helper-present", False, f"missing {HELPER}")
        return 1
    scenario_cli_scan_and_apply_round_trip()
    scenario_cli_missing_file_is_a_contract_error()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
