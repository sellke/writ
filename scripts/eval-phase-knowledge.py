#!/usr/bin/env python3
"""Scenarios for evidence-bound phase knowledge writeback (Story 5).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_phase_knowledge.
Exercises scripts/phase-state.py knowledge-writeback to prove D6:

  - a durable, evidence-cited, novel, sub-ADR candidate is written as a lesson
  - a one-off (does not generalize) candidate is rejected
  - an unsupported (no evidence) candidate is rejected
  - an ADR-scale candidate is rejected (belongs in an ADR)
  - a substantive duplicate of an existing entry is rejected
  - no qualifying candidate is a valid no-op that changes no file
  - a resumed writeback never writes an already-recorded lesson twice
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HELPER = Path(__file__).with_name("phase-state.py")
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


def wj(path: Path, value) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def knowledge_dir(tmp: Path) -> Path:
    kd = tmp / "knowledge"
    (kd / "lessons").mkdir(parents=True)
    return kd


def rejected_reason(out: dict, cid: str) -> str:
    for r in out.get("rejected", []):
        if r["id"] == cid:
            return r["reason"]
    return ""


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = knowledge_dir(tmp)

        cands = wj(tmp / "c.json", {"candidates": [
            {"id": "K1", "title": "Isolate lanes before work",
             "statement": "Creating the branch and worktree before implementation is the "
                          "only way to guarantee the phase branch stays clean across specs.",
             "generalizes": True, "evidence": [".writ/specs/x/drift-log.md"], "adr_scale": False},
            {"id": "K2", "title": "One off",
             "statement": "Spec b had a typo in its title on 2026-07-10.",
             "generalizes": False, "evidence": ["report"], "adr_scale": False},
            {"id": "K3", "title": "Unsupported",
             "statement": "Agents generally do better with fresh context somehow.",
             "generalizes": True, "evidence": [], "adr_scale": False},
            {"id": "K4", "title": "Architectural",
             "statement": "Adopt an entirely new plugin architecture for all adapters.",
             "generalizes": True, "evidence": ["report"], "adr_scale": True},
        ]})
        code, out = helper("knowledge-writeback", "--candidates", str(cands),
                           "--knowledge-dir", str(kd))
        emit("qualifying-lesson-written",
             code == 0 and any(w["id"] == "K1" for w in out.get("written", [])), out)
        emit("one-off-rejected", "one-off" in rejected_reason(out, "K2"), out)
        emit("unsupported-rejected", "unsupported" in rejected_reason(out, "K3"), out)
        emit("adr-scale-rejected", "adr-scale" in rejected_reason(out, "K4"), out)
        emit("lesson-file-created",
             len(list((kd / "lessons").glob("*.md"))) == 1, list((kd / "lessons").glob("*.md")))

    # duplicate detection against an existing entry
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = knowledge_dir(tmp)
        (kd / "lessons" / "2026-01-01-existing.md").write_text(
            "# Fresh context isolation\n\nCreating the branch and worktree before "
            "implementation is the only way to guarantee the phase branch stays clean "
            "across specs.\n", encoding="utf-8")
        cands = wj(tmp / "c.json", {"candidates": [
            {"id": "D1", "title": "Isolate lanes before work",
             "statement": "Creating the branch and worktree before implementation is the "
                          "only way to guarantee the phase branch stays clean across specs.",
             "generalizes": True, "evidence": ["report"], "adr_scale": False},
        ]})
        code, out = helper("knowledge-writeback", "--candidates", str(cands),
                           "--knowledge-dir", str(kd))
        emit("substantive-duplicate-rejected", "duplicate" in rejected_reason(out, "D1"), out)
        emit("duplicate-writes-no-file",
             len(list((kd / "lessons").glob("2026-0[7-9]*.md"))) == 0, out)

    # no-candidate no-op
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = knowledge_dir(tmp)
        cands = wj(tmp / "c.json", {"candidates": []})
        before = sorted(p.name for p in (kd / "lessons").glob("*.md"))
        code, out = helper("knowledge-writeback", "--candidates", str(cands),
                           "--knowledge-dir", str(kd))
        after = sorted(p.name for p in (kd / "lessons").glob("*.md"))
        emit("no-candidate-is-noop",
             code == 0 and out.get("noop") is True and before == after, out)

    # resume-safe: already-recorded lesson not written twice
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kd = knowledge_dir(tmp)
        repo = tmp / "repo"
        repo.mkdir()
        state = tmp / "state.json"
        helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
               "--phase-branch", "phase/6", "--spec-order", "a")
        cands = wj(tmp / "c.json", {"candidates": [
            {"id": "R1", "title": "Durable lesson",
             "statement": "Bounded retries plus quarantine keep partial failures recoverable "
                          "without contaminating a shared phase branch.",
             "generalizes": True, "evidence": ["drift-log"], "adr_scale": False},
        ]})
        helper("knowledge-writeback", "--candidates", str(cands),
               "--knowledge-dir", str(kd), "--state", str(state))
        count_after_first = len(list((kd / "lessons").glob("*.md")))
        code, out = helper("knowledge-writeback", "--candidates", str(cands),
                           "--knowledge-dir", str(kd), "--state", str(state))
        count_after_second = len(list((kd / "lessons").glob("*.md")))
        emit("resume-does-not-duplicate-write",
             count_after_first == 1 and count_after_second == 1 and out.get("noop") is True, out)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
