#!/usr/bin/env python3
"""Fixture scenarios for the cross-spec dependency contract (Story 1).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_spec_dependencies.
Every scenario builds disposable fixture spec folders in a temp directory and
exercises scripts/spec-deps.py, asserting the authoritative contract:

  - absent header  -> legacy, treated as []
  - empty []       -> declared, no dependencies
  - ordered list   -> declared order preserved
  - malformed      -> blocking malformed_dependencies
  - missing ref    -> blocking missing_reference (names the reference)
  - self-reference -> blocking self_reference
  - duplicate      -> blocking duplicate_reference
  - cycle          -> blocking dependency_cycle (names the path)
  - deterministic topological order
  - roadmap order as the independent-spec tie-break
  - story-level `Dependencies: Story N` is never conflated with spec deps
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("spec-deps.py")
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
    lines = ["# Spec", ""]
    if header is not None:
        lines.append(header)
    # Deliberately include story-level dependency prose to prove the parser
    # never conflates it with the spec-level header.
    lines += ["", "Story Plan:", "1. story-one - Dependencies: None",
              "2. story-two - Dependencies: Story 1", ""]
    (folder / "spec.md").write_text("\n".join(lines), encoding="utf-8")
    return folder / "spec.md"


def scenario_parse() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        spec = make_spec(root, "s-absent", None)
        code, payload = run("parse", "--spec", str(spec))
        emit("parse-absent-is-legacy-empty",
             code == 0 and payload.get("declared") is False
             and payload.get("dependencies") == [], payload)

        spec = make_spec(root, "s-empty", "> **Dependencies:** []")
        code, payload = run("parse", "--spec", str(spec))
        emit("parse-empty-is-declared-none",
             code == 0 and payload.get("declared") is True
             and payload.get("dependencies") == [], payload)

        spec = make_spec(root, "s-order", "> **Dependencies:** [beta, alpha]")
        code, payload = run("parse", "--spec", str(spec))
        emit("parse-declared-order-preserved",
             code == 0 and payload.get("dependencies") == ["beta", "alpha"], payload)

        spec = make_spec(root, "s-nobracket", "> **Dependencies:** alpha, beta")
        code, payload = run("parse", "--spec", str(spec))
        emit("parse-malformed-no-brackets",
             code != 0 and payload.get("blocker", {}).get("code") == "malformed_dependencies",
             payload)

        spec = make_spec(root, "s-badtoken", "> **Dependencies:** [not a folder id]")
        code, payload = run("parse", "--spec", str(spec))
        emit("parse-malformed-bad-token",
             code != 0 and payload.get("blocker", {}).get("code") == "malformed_dependencies",
             payload)

        # Story-level "Dependencies: Story 1" prose must not be read as a
        # spec-level declaration.
        spec = make_spec(root, "s-story-only", None)
        code, payload = run("parse", "--spec", str(spec))
        emit("parse-story-deps-not-conflated",
             code == 0 and payload.get("declared") is False
             and payload.get("dependencies") == [], payload)


def scenario_validate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_spec(root, "foundation", "> **Dependencies:** []")
        make_spec(root, "consumer", "> **Dependencies:** [foundation]")
        make_spec(root, "legacy", None)
        code, payload = run("validate", "--specs-dir", str(root),
                            "--roadmap-order", "legacy,foundation,consumer")
        order = payload.get("order", [])
        emit("validate-happy-topological-order",
             code == 0 and order.index("foundation") < order.index("consumer"), payload)
        emit("validate-roadmap-tiebreak-independent",
             code == 0 and order.index("legacy") < order.index("foundation"), payload)
        emit("validate-legacy-header-treated-empty",
             code == 0 and "legacy" in order, payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_spec(root, "consumer", "> **Dependencies:** [ghost]")
        code, payload = run("validate", "--specs-dir", str(root))
        emit("validate-missing-reference-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "missing_reference"
             and "ghost" in payload.get("blocker", {}).get("summary", ""), payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_spec(root, "loner", "> **Dependencies:** [loner]")
        code, payload = run("validate", "--specs-dir", str(root))
        emit("validate-self-reference-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "self_reference", payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_spec(root, "base", "> **Dependencies:** []")
        make_spec(root, "dup", "> **Dependencies:** [base, base]")
        code, payload = run("validate", "--specs-dir", str(root))
        emit("validate-duplicate-blocks",
             code != 0 and payload.get("blocker", {}).get("code") == "duplicate_reference", payload)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_spec(root, "left", "> **Dependencies:** [right]")
        make_spec(root, "right", "> **Dependencies:** [left]")
        code, payload = run("validate", "--specs-dir", str(root))
        emit("validate-cycle-blocks-with-path",
             code != 0 and payload.get("blocker", {}).get("code") == "dependency_cycle"
             and "->" in payload.get("blocker", {}).get("summary", ""), payload)


def main() -> int:
    scenario_parse()
    scenario_validate()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
