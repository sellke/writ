# Story 4: Eval Integration

> **Status:** Completed ✅ (2026-08-12)
> **Commit:** 358e0229c62df2b3e9286e845f48be31ed298a9e
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** maintainer running the Writ eval suite
**I want** the checker's own correctness asserted alongside every other Writ instrument, with its predicates bound to the criterion prose they claim to evaluate
**So that** the checker cannot drift away from the criteria it was written against without the suite going red

## Acceptance Criteria

- [x] Given `bash scripts/eval.sh --check=exit-criteria`, when it runs against a clean tree, then it exits 0 and reports `Findings: 0`.
- [x] Given `scripts/eval-exit-criteria.py`, when it runs, then it emits PASS/FAIL TSV scenario lines in the same shape `scripts/eval-story-deps.py` emits and `check_story_deps` consumes, covering met, unmet, each of the four `impossible` triggers, and the pre-Story-2 unknown path.
- [x] Given a predicate whose cited criterion text no longer matches the command frontmatter, when the check runs, then it FAILs naming the criterion — the transcription-drift assertion `scripts/eval-loop-bounds.py` assertion 8 makes for loop bounds, applied here.
- [x] Given `scripts/eval.sh`, when the check is registered, then `exit-criteria` appears in the `CHECKS` array and no existing check function is modified.
- [x] Given the full suite, when `bash scripts/eval.sh` runs, then it is green — the Phase 10 governor checks are blocking `structural`, so any dropped contract field in the two edited command files fails the run.

## Implementation Tasks

- [x] 4.1 Write `scripts/eval-exit-criteria.py` building fixture state files in a temp dir and asserting the checker's verdict per scenario
- [x] 4.2 Add `check_exit_criteria()` to `scripts/eval.sh` following the `check_story_deps` shape at `scripts/eval.sh:2109` — scenario loop, then `require_literal` assertions
- [x] 4.3 Add `require_literal` bindings: each criterion's verbatim text present in both the command frontmatter and `scripts/exit-criteria.py`
- [x] 4.4 Add `require_literal` bindings on the rollup precedence and the four `impossible` trigger names
- [x] 4.5 Register `exit-criteria` in the `CHECKS` array
- [x] 4.6 Run the full suite and confirm green

## Notes

**Technical considerations:** `check_story_deps` is the model to copy in full —
scenario TSV consumed into `CURRENT_SCENARIOS` / `CURRENT_SCENARIOS_PASSED`,
findings via `add_finding`, then `require_literal` / `forbid_literal` pairs binding
prose to implementation. Copying its shape keeps the report format uniform.

**Risks:** `scripts/eval.sh` is ~155KB and shared by every other check. This story
appends; it must not touch an existing function or reorder `CHECKS`. Verify with
`git diff --stat scripts/eval.sh` that the only changes are additions.

**The prose binding is the point.** Without task 4.3 the criterion text lives in two
places — command frontmatter and Python — and nothing notices when they diverge.
That divergence is precisely how an instrument keeps passing while measuring
something the contract no longer says.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`scripts/eval-exit-criteria.py`** — 18 fixture scenarios building synthetic git repos + phase-execution-v2 state files in `tempfile.TemporaryDirectory()` (mirroring `test_exit_criteria.py`'s `PhaseGitFixture`), invoking the real `scripts/exit-criteria.py check` CLI via subprocess. Never touches real gitignored `.writ/state/` archives. Covers: met, unmet, pre-Story-2 unknown, all 4 `impossible` triggers, plus a determinism (repeated-run byte-identical) scenario.

### Files Modified

- **`scripts/eval.sh`** — added `check_exit_criteria()` (scenario-consumption loop, then `require_literal` bindings) and registered `exit-criteria` as the new last `CHECKS` entry. Append-only: 88 insertions, 0 deletions, confirmed via `git diff --stat`.
- **`scripts/exit-criteria.py`** — reformatted `CRITERION_TEXT`'s 7 values from multi-line-concatenated string fragments to single-line string literals so `require_literal`'s single-line grep can match the full sentence against command frontmatter. Pure formatting change — dict values verified byte-identical before/after (Gate 3 review loaded both versions as Python modules and asserted dict equality).

### Implementation Decisions

1. **`CRITERION_TEXT` reformat isolated to string literal formatting only** — Gate 0 review caught that the original multi-line-concatenated fragments couldn't be grepped as a full sentence; fixed surgically without touching predicate logic, then re-ran all 71 tests to confirm no behavior change.
2. **22 `require_literal` bindings** — 14 for the 7 criteria's verbatim prose (bound against both command frontmatter and `exit-criteria.py`), 8 for rollup precedence + the four `impossible` trigger names (bound against `technical-spec.md` via the existing `resolve_spec_path` helper, and against `exit-criteria.py`).
3. **Bonus determinism scenario** added beyond the acceptance criteria's explicit list, mirroring `eval-story-deps.py`'s determinism check at negligible cost.

### Test Results

**Verification:** `python3 -m unittest scripts.tests.test_exit_criteria scripts.tests.test_phase_state` — 71/71 passing (unchanged by the reformat). `bash scripts/eval.sh --check=exit-criteria` — Scenarios: 18/18 passed, Findings: 0. `bash scripts/eval.sh` (full suite) — Findings: 0, Run errors: 0.
- ✅ **Drift-detection gate proven real, not decorative** — both the implementing coder and the independent reviewer separately edited a criterion's text in `commands/implement-phase.md`, re-ran the check, confirmed it FAILed naming the exact criterion (`implement-phase.c1` / `implement-phase.c2` respectively), then reverted and confirmed `git diff` showed nothing and the check passed again.
- ✅ `git diff --stat scripts/eval.sh` — additions only, no existing function reordered or modified.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean — no shell injection (argument-list subprocess calls), no untrusted input, all fixture state in disposable temp dirs.

### Deviations from Spec

None.
