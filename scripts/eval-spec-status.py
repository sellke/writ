#!/usr/bin/env python3
"""Fixture scenarios for the format-tolerant spec-status contract (Story 1).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_spec_status. Every
scenario builds a disposable fixture spec.md in a temp directory and exercises
scripts/spec-status.py, asserting the authoritative contract:

  - bold `> **Status:** Complete`                    -> complete-family
  - bold `> **Status:** Completed ✅`                 -> complete-family
  - unbold `> Status: Complete`                       -> complete-family
  - unbold `> Status: Closed — Abandoned ...`          -> complete-family
  - absent header                                     -> NOT complete (conservative)
  - `> **Status:** Not Started` / `In Progress`        -> NOT complete
  - single-level glob (`scan`) excludes `archive/<name>/spec.md`
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HELPER = Path(__file__).with_name("spec-status.py")
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


def run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def make_spec(root: Path, spec_id: str, header: str | None) -> Path:
    folder = root / spec_id
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["# Spec: Fixture"]
    if header is not None:
        lines.append(header)
    lines += ["", "## Contract (Locked)", "Deliverable: fixture only."]
    spec_path = folder / "spec.md"
    spec_path.write_text("\n".join(lines), encoding="utf-8")
    return spec_path


def scenario_is_complete() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        spec = make_spec(root, "s-bold-complete", "> **Status:** Complete")
        code, payload = run("is-complete", "--file", str(spec))
        emit("bold-complete-resolves-complete-family",
             code == 0 and payload.get("complete") is True, payload)

        spec = make_spec(root, "s-bold-completed-emoji", "> **Status:** Completed ✅")
        code, payload = run("is-complete", "--file", str(spec))
        emit("bold-completed-emoji-resolves-complete-family",
             code == 0 and payload.get("complete") is True, payload)

        spec = make_spec(root, "s-unbold-complete", "> Status: Complete")
        code, payload = run("is-complete", "--file", str(spec))
        emit("unbold-complete-resolves-complete-family",
             code == 0 and payload.get("complete") is True, payload)

        spec = make_spec(
            root, "s-closed-abandoned",
            "> Status: Closed — Abandoned (2026-07-18). Never executed.",
        )
        code, payload = run("is-complete", "--file", str(spec))
        emit("closed-abandoned-resolves-complete-family",
             code == 0 and payload.get("complete") is True, payload)

        spec = make_spec(root, "s-absent", None)
        code, payload = run("is-complete", "--file", str(spec))
        emit("absent-header-conservatively-not-complete",
             code == 0 and payload.get("complete") is False
             and payload.get("header_line") is None, payload)

        spec = make_spec(root, "s-not-started", "> **Status:** Not Started")
        code, payload = run("is-complete", "--file", str(spec))
        emit("not-started-is-not-complete",
             code == 0 and payload.get("complete") is False, payload)

        spec = make_spec(root, "s-in-progress", "> Status: In Progress")
        code, payload = run("is-complete", "--file", str(spec))
        emit("in-progress-is-not-complete",
             code == 0 and payload.get("complete") is False, payload)

        code, payload = run("is-complete", "--file", str(root / "missing" / "spec.md"))
        emit("missing-file-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "missing_spec",
             payload)


def scenario_scan() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_spec(root, "active-spec", "> **Status:** Not Started")
        make_spec(root, "done-spec", "> **Status:** Complete")
        archived = root / "archive" / "archived-spec"
        archived.mkdir(parents=True)
        (archived / "spec.md").write_text("> **Status:** Complete\n", encoding="utf-8")

        code, payload = run("scan", "--specs-dir", str(root))
        spec_ids = {r["spec"] for r in payload.get("results", [])}
        emit("scan-single-level-glob-excludes-archive",
             code == 0 and "archive" not in spec_ids and "active-spec" in spec_ids
             and "done-spec" in spec_ids, payload)
        emit("scan-complete-count-correct",
             code == 0 and payload.get("complete_count") == 1
             and payload.get("not_complete_count") == 1, payload)

        code, payload = run("scan", "--specs-dir", str(root / "nonexistent"))
        emit("scan-missing-dir-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "missing_specs_dir",
             payload)


def main() -> int:
    scenario_is_complete()
    scenario_scan()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
