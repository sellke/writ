#!/usr/bin/env python3
"""Scenarios for phase progress and categorical health (Story 6).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_phase_health.
Exercises scripts/phase-state.py progress/health to prove D7:

  - progress reports phase, current spec/lane, counts, and quarantine branches
  - Healthy only when current available evidence passes and state is consistent
  - Warning when required evidence is missing/stale (never called a failure)
  - Attention on a current failure, material drift, or state/git mismatch
  - mixed-age evidence cannot exceed Warning without a current failure signal
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


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def new_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "eval@writ.test")
    git(repo, "config", "user.name", "Writ Eval")
    git(repo, "checkout", "-q", "-b", "phase/6")
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "base")
    return repo


def init(tmp: Path, repo: Path) -> Path:
    state = tmp / "state.json"
    helper("init", "--state", str(state), "--repo", str(repo), "--phase", "6",
           "--phase-branch", "phase/6", "--spec-order", "a,b")
    return state


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        repo = new_repo(tmp)
        state = init(tmp, repo)
        # Put spec a into a lane, spec b quarantined.
        _, lane = helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", "a")
        wt = Path(lane["worktreePath"])
        (wt / "x.txt").write_text("x\n", encoding="utf-8")
        git(wt, "add", "-A"); git(wt, "commit", "-q", "-m", "x")

        _, prog = helper("progress", "--state", str(state))
        emit("progress-reports-phase-and-current",
             prog.get("phase") == "6" and prog.get("current", {}).get("spec") == "a", prog)

        # quarantine b
        _, lane_b = helper("create-lane", "--state", str(state), "--repo", str(repo), "--spec", "b")
        wtb = Path(lane_b["worktreePath"])
        (wtb / "y.txt").write_text("y\n", encoding="utf-8")
        git(wtb, "add", "-A"); git(wtb, "commit", "-q", "-m", "y")
        helper("quarantine", "--state", str(state), "--repo", str(repo), "--spec", "b")
        _, prog = helper("progress", "--state", str(state))
        emit("progress-reports-quarantine",
             "writ/quarantine/b" in prog.get("quarantineBranches", [])
             and prog["counts"]["quarantined"] == 1, prog)

        good_eval = write(tmp / "eval.md", "# Report\n\n- Findings: 0\n")
        bad_eval = write(tmp / "evalbad.md", "# Report\n\n- Findings: 3\n")
        good_verify = write(tmp / "ver.md", "# Verification\n\n- Findings: 0\n")

        # Healthy: passing eval + verification, consistent state, no drift... but
        # drift missing would make it Warning, so pass a clean drift file.
        clean_drift = write(tmp / "drift.md", "# Drift\n\nAll resolved.\n")

    # Fresh consistent repo/state for health category tests (no active lane).
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        repo = new_repo(tmp)
        state = init(tmp, repo)
        good_eval = write(tmp / "eval.md", "# Report\n\n- Findings: 0\n")
        bad_eval = write(tmp / "evalbad.md", "# Report\n\n- Findings: 3\n")
        good_verify = write(tmp / "ver.md", "# Verification\n\n- Findings: 0\n")
        clean_drift = write(tmp / "drift.md", "# Drift\n\nAll resolved.\n")
        material_drift = write(tmp / "driftbad.md", "# Drift\n\nunresolved material issue\n")

        code, out = helper("health", "--state", str(state), "--repo", str(repo),
                           "--eval", str(good_eval), "--verification", str(good_verify),
                           "--drift", str(clean_drift))
        emit("healthy-when-all-pass", out.get("category") == "Healthy", out)

        code, out = helper("health", "--state", str(state), "--repo", str(repo),
                           "--eval", str(good_eval), "--verification", str(good_verify))
        emit("warning-when-drift-missing",
             out.get("category") == "Warning" and "drift log" in out.get("unavailable", []), out)

        code, out = helper("health", "--state", str(state), "--repo", str(repo),
                           "--eval", str(bad_eval), "--verification", str(good_verify),
                           "--drift", str(clean_drift))
        emit("attention-on-eval-failure",
             out.get("category") == "Attention"
             and "eval findings present" in out.get("failures", []), out)

        code, out = helper("health", "--state", str(state), "--repo", str(repo),
                           "--eval", str(good_eval), "--verification", str(good_verify),
                           "--drift", str(material_drift))
        emit("attention-on-material-drift", out.get("category") == "Attention", out)

        # mixed-age: eval missing (Warning input) + passing verification cannot exceed Warning
        code, out = helper("health", "--state", str(state), "--repo", str(repo),
                           "--verification", str(good_verify), "--drift", str(clean_drift))
        emit("mixed-age-cannot-exceed-warning",
             out.get("category") == "Warning" and "eval summary" in out.get("unavailable", []), out)

        # state/git mismatch -> Attention even with passing artifacts
        git(repo, "branch", "-m", "phase/6", "phase-6-renamed")  # break the recorded phase branch
        code, out = helper("health", "--state", str(state), "--repo", str(repo),
                           "--eval", str(good_eval), "--verification", str(good_verify),
                           "--drift", str(clean_drift))
        emit("attention-on-state-git-mismatch",
             out.get("category") == "Attention"
             and "phase-state/git mismatch" in out.get("failures", []), out)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
