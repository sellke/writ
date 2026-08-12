#!/usr/bin/env python3
"""Scenarios for the canonical spec-status vocabulary (spec-vocabulary).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_spec_vocabulary.

Background: `spec-status.py` matched "Closed" as a BARE prefix, so any subtype
was silently admitted as terminal. That is how `Closed — Not Implemented`
entered five specs while `.writ/docs/spec-lifecycle.md` still declared no
fourth prefix existed — the doc and the detector were never compared. Same
class of defect as the phase layer's `SPEC_STATUSES`, which was declared and
referenced nowhere.

A validator nothing has ever seen fail is decorative in exactly that way, so
these scenarios include a **mutation proof**: an off-vocabulary value is
injected into a disposable fixture and the validator must report it. Without
that, "ok: true" on a clean repo proves nothing.

Proves:
  - the real repo's specs are all on-vocabulary (regression guard)
  - an off-vocabulary head IS reported (mutation proof — the check bites)
  - a missing status header is reported separately, not as drift
  - classification stays tolerant: an off-vocabulary "Closed — X" is still
    detected complete-family, so no existing spec is reclassified
  - the doc's vocabulary table and the script's declared heads agree
  - dash variants (em, en, hyphen) resolve to the same canonical head
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("spec-status.py")
DOC = Path(__file__).resolve().parents[1] / ".writ" / "docs" / "spec-lifecycle.md"
REPO_SPECS = Path(__file__).resolve().parents[1] / ".writ" / "specs"
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


def helper(*args: str) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, str(HELPER), *args],
                          capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"_raw": proc.stdout, "_err": proc.stderr}
    return proc.returncode, payload


def write_spec(specs_dir: Path, name: str, status: str | None) -> None:
    d = specs_dir / name
    d.mkdir(parents=True, exist_ok=True)
    header = f"> **Status:** {status}\n" if status is not None else ""
    (d / "spec.md").write_text(f"# Spec: {name}\n\n{header}> **Created:** 2026-08-12\n\n## Body\n",
                               encoding="utf-8")


def main() -> int:
    # --- regression guard: the real corpus is on-vocabulary
    code, out = helper("validate", "--specs-dir", str(REPO_SPECS))
    emit("repo-specs-all-on-vocabulary",
         code == 0 and out.get("ok") is True and not out.get("off_vocabulary"),
         out.get("off_vocabulary"))
    emit("repo-validate-covers-archive",
         out.get("scanned", 0) > 40,
         f"scanned={out.get('scanned')} (archive must be included, it is most of the corpus)")
    emit("closed-not-implemented-is-recognized",
         out.get("heads_in_use", {}).get("Closed — Not Implemented", 0) >= 5,
         out.get("heads_in_use"))

    # --- mutation proof: the validator must actually bite
    with tempfile.TemporaryDirectory() as t:
        specs = Path(t) / "specs"
        write_spec(specs, "2026-01-01-good", "Complete (shipped in v1.2.3)")
        write_spec(specs, "2026-01-02-drift", "Closed — Reticulated")
        write_spec(specs, "2026-01-03-headless", None)

        code, out = helper("validate", "--specs-dir", str(specs))
        off = {o["spec"] for o in out.get("off_vocabulary", [])}
        emit("mutation-off-vocabulary-head-is-reported",
             off == {"2026-01-02-drift"} and out.get("ok") is False,
             f"off={off} ok={out.get('ok')}")
        emit("mutation-missing-header-reported-separately",
             out.get("missing_header") == ["2026-01-03-headless"]
             and "2026-01-03-headless" not in off,
             f"missing={out.get('missing_header')} off={off}")
        emit("mutation-canonical-value-not-flagged",
             "2026-01-01-good" not in off, off)

        # Tolerance: an off-vocabulary Closed value is STILL complete-family.
        # Enforcement must not silently reclassify an existing spec.
        code, one = helper("is-complete", "--file",
                           str(specs / "2026-01-02-drift" / "spec.md"))
        emit("off-vocabulary-value-still-classified-complete",
             one.get("complete") is True and one.get("canonical_head") is None,
             one)

    # --- dash tolerance
    with tempfile.TemporaryDirectory() as t:
        specs = Path(t) / "specs"
        write_spec(specs, "2026-02-01-em", "Closed — Not Implemented")
        write_spec(specs, "2026-02-02-en", "Closed – Not Implemented")
        write_spec(specs, "2026-02-03-hy", "Closed - Not Implemented")
        code, out = helper("validate", "--specs-dir", str(specs))
        emit("dash-variants-resolve-to-one-head",
             out.get("ok") is True
             and out.get("heads_in_use", {}).get("Closed — Not Implemented") == 3,
             out.get("heads_in_use"))

    # --- doc/script agreement: the drift that started all this
    doc_text = DOC.read_text(encoding="utf-8") if DOC.is_file() else ""
    code, out = helper("validate", "--specs-dir", str(REPO_SPECS))
    declared = out.get("canonical_heads", [])
    missing_from_doc = [h for h in declared if h not in doc_text]
    emit("every-declared-head-appears-in-the-lifecycle-doc",
         not missing_from_doc, f"missing={missing_from_doc}")
    emit("doc-no-longer-forbids-a-fourth-prefix",
         "rather than introducing a fourth standalone prefix" not in doc_text,
         "the doc still forbids the prefix five specs already use")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
