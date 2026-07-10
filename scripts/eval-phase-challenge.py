#!/usr/bin/env python3
"""Scenarios for contract-preserving User Challenges (Story 3).

Emits PASS/FAIL TSV lines consumed by scripts/eval.sh check_phase_challenges.
Exercises scripts/phase-state.py to prove the D5 User Challenge contract:

  - a valid four-part challenge validates and can be recorded
  - an audited (decided) challenge persists as resolved
  - an unresolved challenge blocks the challenged decision and survives resume
  - resolving records the selected option and a decision timestamp
  - a malformed challenge (missing part, bad trigger, no options) is a
    contract error, not a User Challenge and not an ordinary failure
  - challenge_required result validation requires a well-formed challenge
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


def write_json(path: Path, value) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def valid_challenge(decision=None) -> dict:
    payload = {
        "trigger": "scope_degradation",
        "roadmap_or_spec_said": "ship feature X for all users",
        "recommendation": "ship for authenticated users only",
        "possibly_missing_context": "anonymous usage share unknown",
        "cost_if_wrong": "anonymous users silently lose X",
        "options": [
            {"id": "auth-only", "label": "Ship authenticated-only"},
            {"id": "pause", "label": "Pause for human decision"},
        ],
    }
    if decision is not None:
        payload["decision"] = decision
    return payload


def init_state(tmp: Path) -> Path:
    state = tmp / "state.json"
    repo = tmp / "repo"
    repo.mkdir()
    helper("init", "--state", str(state), "--repo", str(repo),
           "--phase", "6", "--phase-branch", "phase/6", "--spec-order", "spec-a")
    return state


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)

        good = write_json(tmp / "good.json", valid_challenge())
        code, out = helper("validate-challenge", "--input", str(good))
        emit("valid-four-part-challenge-accepted",
             code == 0 and out.get("resolved") is False, out)

        for name, mutate in (
            ("missing-part", lambda v: v.pop("cost_if_wrong")),
            ("bad-trigger", lambda v: v.update(trigger="uncertainty")),
            ("no-options", lambda v: v.update(options=[])),
            ("blank-part", lambda v: v.update(recommendation="   ")),
        ):
            value = valid_challenge()
            mutate(value)
            path = write_json(tmp / f"{name}.json", value)
            code, out = helper("validate-challenge", "--input", str(path))
            emit(f"malformed-{name}-is-contract-error",
                 code != 0 and out.get("blocker", {}).get("code") == "invalid_challenge", out)

        # Unresolved challenge blocks the decision and persists.
        state = init_state(tmp)
        code, out = helper("record-challenge", "--state", str(state),
                           "--spec", "spec-a", "--input", str(good))
        emit("unresolved-challenge-blocks-decision",
             code == 0 and out.get("blocked") is True and out.get("status") == "unresolved", out)
        _, shown = helper("show", "--state", str(state))
        emit("unresolved-challenge-persisted",
             len(shown.get("challenges", [])) == 1
             and shown["challenges"][0]["status"] == "unresolved"
             and shown["specs"]["spec-a"]["status"] == "challenge_required", shown)

        # Resolving records selected option + timestamp (survives resume as state).
        chal_id = shown["challenges"][0]["id"]
        code, out = helper("resolve-challenge", "--state", str(state),
                           "--challenge-id", chal_id, "--option", "auth-only")
        emit("resolve-records-selection", code == 0 and out.get("selected") == "auth-only", out)
        _, shown2 = helper("show", "--state", str(state))
        entry = shown2["challenges"][0]
        emit("resolved-challenge-has-decision",
             entry["status"] == "resolved"
             and entry["challenge"]["decision"]["option_id"] == "auth-only"
             and entry["challenge"]["decision"]["decided_at"], entry)

        # Resolving an option not offered is rejected.
        code, out = helper("resolve-challenge", "--state", str(state),
                           "--challenge-id", chal_id, "--option", "ghost")
        emit("resolve-rejects-unknown-option",
             code != 0 and out.get("blocker", {}).get("code") == "invalid_challenge", out)

        # An audited (pre-decided) challenge records as resolved immediately.
        decided = write_json(tmp / "decided.json", valid_challenge(
            decision={"option_id": "auth-only", "decided_at": "2026-07-10T21:00:00Z"}))
        state3 = tmp / "state3.json"
        repo3 = tmp / "repo3"
        repo3.mkdir()
        helper("init", "--state", str(state3), "--repo", str(repo3),
               "--phase", "6", "--phase-branch", "phase/6", "--spec-order", "spec-a")
        code, out = helper("record-challenge", "--state", str(state3),
                           "--spec", "spec-a", "--input", str(decided))
        emit("audited-selection-records-resolved",
             code == 0 and out.get("status") == "resolved" and out.get("blocked") is False, out)

        # challenge_required result must carry a well-formed challenge.
        bad_result = write_json(tmp / "badres.json", {
            "spec_id": "spec-a", "status": "challenge_required",
            "stories_completed": 0, "stories_total": 1,
            "verification": {"summary": "", "evidence": []},
            "files_changed": [], "commit": None, "failure": None,
            "challenge": {"trigger": "scope_degradation"},
        })
        code, out = helper("validate-result", "--input", str(bad_result))
        emit("challenge-required-needs-valid-challenge",
             code != 0 and out.get("blocker", {}).get("code") == "invalid_challenge", out)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
