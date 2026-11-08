# Story 3: Lane result file and shipped brief template

> **Status:** Completed ✅ (2026-11-07)
> **Commit:** 57d5f63025942da324f30175f54b5d371e0dc74f
> **Priority:** Normal
> **Dependencies:** Story 2

## User Story

**As a** phase orchestrator
**I want to** each lane to write its `phase-spec-result-v1` to a known file from a shipped brief template
**So that** a dropped or truncated reply no longer loses a lane's result, and the brief stops growing per run

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [x] Given `phase-state.py create-lane` runs for a spec, when it succeeds, then `specs.{id}.resultPath` holds an absolute path under the main checkout's `.writ/state/` named `lane-result-<phase>-<spec>.json` `[AC-3.1]`
- [x] Given `commands/_lane-brief.md` exists with placeholders for spec path, phase state, lane branch, worktree, mode, result path and answer sources, when Step 3.2 of `implement-phase.md` and § Phase-Orchestrated Lane Mode of `implement-spec.md` are read, then both reference the template and the lane writes its result to `{result_path}` before replying `[AC-3.2]`
- [x] Given a lane's result file is missing or does not parse as `phase-spec-result-v1`, when the orchestrator handles it, then it resumes the same lane agent once to write the file and classifies a second miss as `transient` `[AC-3.3]`
- [x] Given the shipped-file checks, when `test_eval_shipped_refs.py` and `python3 scripts/gen-platform-trees.py --check` run, then `commands/_lane-brief.md` is shipped by `install.sh` and present in each generated tree that ships `commands/` `[AC-3.4]`

## Implementation Tasks

- [x] 3.1 Write failing tests in `scripts/tests/test_phase_state.py` for `create-lane` recording `resultPath` and for `validate-result --input` reading that file `[AC-3.1, AC-3.3]`
- [x] 3.2 Add `resultPath` to `create-lane` in `scripts/phase-state.py` and to the field contract in `.writ/docs/phase-execution-state-format.md` `[AC-3.1]`
- [x] 3.3 Write `commands/_lane-brief.md` from the brief used in Phase 15 (retro F22), with the placeholders named in technical-spec.md → Lane result file `[AC-3.2]`
- [x] 3.4 Edit Step 3.2 of `commands/implement-phase.md` (brief template, result file, supervisor gets the file path, one resume then `transient`) and § Phase-Orchestrated Lane Mode of `commands/implement-spec.md`; delete the truncated-result paragraph `[AC-3.2, AC-3.3]`
- [x] 3.5 Confirm `scripts/install.sh` and `scripts/gen-platform-trees.py` ship `commands/_lane-brief.md`; add it where they list underscore files explicitly; run `python3 scripts/gen-platform-trees.py` `[AC-3.4]`
- [x] 3.6 Verify acceptance criteria: run `test_phase_state.py`, `test_eval_shipped_refs.py`, `test_governor_enforcement.py` on Python 3.9 and `python3 scripts/gen-platform-trees.py --check` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

- **Retro F22:** results were parsed from escaped task output in 4 lanes, and one report was dropped. The brief grew from 2,962 to 6,323 characters across the run.
- **Business Rule 6:** the result path is outside the lane worktree so it survives worktree removal after merge or quarantine. `validate-result --input` already takes a path; no new subcommand.
- **Cross-spec overlap:** `2026-11-06-lean-story-pipeline` edits other sections of `commands/implement-spec.md` (Step 2.3, Step 3.3, supervisor input). Touch only § Phase-Orchestrated Lane Mode.
- **Byte budget:** add a dated `KNOWN_OVER_BUDGET` entry for each command whose size changed.
- **Test runs:** run pytest alone; full suites at spec end.

## Context for Agents

- **Error map rows:** [Lane result (Story 3)] — from technical-spec.md error map
- **Shadow paths:** []
- **Business rules:** [6, 8] — from spec.md → Specification Contract → 📋 Business Rules
- **Experience:** [Error experience] — from spec.md → 🎯 Experience Design

## What Was Built

**Implementation Date:** 2026-11-07

### Files Created

- **`commands/_lane-brief.md`** (lane brief template, 7 placeholders; the lane writes `phase-spec-result-v1` to `{result_path}` as its last action, then replies with the path)
- **`cursor/plugin/commands/_lane-brief.md`, `plugins/writ/commands/_lane-brief.md`** (generated)

### Files Modified

- **`scripts/phase-state.py`** (`create-lane` records and returns absolute `resultPath`; `resume_candidate` returns it; `validate-result --input` returns `result_missing` / `invalid_result`)
- **`commands/implement-phase.md`** (Step 3.2: fill the template, delete a stale result file, validate the file, resume once then `transient`, supervisor gets the file contents; truncated-result paragraph deleted)
- **`commands/implement-spec.md`** (§ Phase-Orchestrated Lane Mode only: template, result file, the result-file exception to the no-touch rule)
- **`.writ/docs/phase-execution-state-format.md`** (`resultPath` field, `result_path` in the brief, blocker codes)
- **`scripts/gen-platform-trees.py`** (every underscore file in `commands/` is a partial: shipped, linked from the plugin root, never a plugin command)
- **`scripts/eval-leanness.py`**, **`scripts/tests/test_eval_leanness.sh`** (the `commands` metric counts invocable files only; maintainer decision)
- **`adapters/claude-code.md`, `adapters/codex.md`, `adapters/cursor.md`** (lane result is written to the brief's result file)
- **`scripts/tests/test_phase_state.py`** (`LaneResultFileTests`, 6 tests; `LaneBriefTemplateTests`, 6 tests)
- **`scripts/tests/test_eval_shipped_refs.py`** (`LaneBriefShippedTests`, 5 tests)
- **`scripts/tests/test_plugin_distribution.py`** (helpers handle any underscore partial)
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET` for `implement-phase.md` 9825 → 10119, dated)
- **Generated:** `{cursor/plugin,plugins/writ}/commands/{implement-phase,implement-spec}.md`, `plugins/writ/scripts/phase-state.py`

### Implementation Decisions

1. **The result file lives in the main checkout's gitignored `.writ/state/`** — it survives worktree removal after merge or quarantine, and adds no dirty-tree precondition the phase-state file did not already have.
2. **Delete a stale result file before each spawn** — a retry reuses the path; without the delete, a lane that writes nothing would be read as the previous attempt's result.
3. **Supervisor gets the file contents, not the path** — the file is the lane's whole report, so `supervisor-agent`'s `report` input stays "verbatim" and the agent file is unchanged (Business Rule 8).
4. **Underscore files are partials by rule** — the plugin generator and the leanness `commands` metric both use the `_` prefix rule instead of a list.

### Test Results

**Verification:** Automated

- ✅ Orchestrator's recorded run (Python 3.9): 668 passed across 11 files; `test_eval_leanness.sh` 36/36
- ✅ After the post-review prose fixes: 798 passed across 11 files (adds the adapter and front-door tests)
- ✅ `gen-platform-trees.py --check`: pass; `eval.sh` `command-structure`, `shipped-refs`, `broken-refs`, `phase-lanes`, `size-pins`, `leanness`: exit 0
- Full suite and `eval.sh`: run once at spec end

**Coverage:** N/A — `test-integrity.py coverage` unverifiable (no coverage report in this repo)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Gate 3 route:** `review-agent` (cross-component; 10 boundary crossings: generated copies, the maintainer-approved leanness change, and plugin test helpers)
- **Drift:** Medium (DEV-004 ⚠️; DEV-005, DEV-006 Small)
- **Security:** Clean
- **Safety fact:** measured `tested` (claimed `tested`)
- **Gate 1 BLOCKED once:** the new template took the commands count to 36 (`MAX_COMMANDS` 35); the maintainer chose "count invocable only"
- **Post-review fixes by the orchestrator:** five reviewer recommendations (supervisor gets file contents; Lane Mode states the result-file exception; adapters describe the result file; fallback `resultPath` for older state files; absolute phase-state path). Not done: a test for the result file plus `integrate` on a repo that ignores `.writ/state/` (the reviewer reproduced it by hand), and keeping an invalid result file instead of overwriting it

### Deviations from Spec

See `drift-log.md` Story 3: DEV-004 (Medium, maintainer-approved), DEV-005, DEV-006 (Small, auto-amended in spec-lite). Post-review: DEV-007, DEV-008 (Small; the supervisor escalated them as unlogged, the maintainer accepted both).

### Lessons Learned

1. **A new shipped file can trip a governance cap** — a spec that adds a file under `commands/` should check `MAX_COMMANDS` before the story starts.

### Next Story

Story 4: Compress implement-phase.md to 240 lines.
