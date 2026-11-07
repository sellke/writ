# Story 2: Health counts given sources; Goal emit leaves the phase

> **Status:** Completed ✅ (2026-11-07)
> **Commit:** fe022193131671686b32ed05b0d7f323d1a9300f
> **Priority:** Normal
> **Dependencies:** Story 1

## User Story

**As a** developer reading a phase report
**I want to** `health` to judge only the evidence the phase produced, and the phase to stop emitting Goal files
**So that** a clean phase reads `Healthy` instead of a permanent `Warning`, and the command does only phase work

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [x] Given `phase-state.py health` is called with no `--eval`, `--verification` or `--drift` flag and the state reconciles, when it runs, then each omitted source reads `not_requested` and the category is `Healthy` `[AC-2.1]`
- [x] Given `health` is called with a `--verification` or `--drift` path that does not exist, when it runs, then that source reads `missing` and the category is `Warning` `[AC-2.2]`
- [x] Given `commands/implement-phase.md`, when Story 2 is complete, then Step 1.4 is gone, Step 4.1c passes only the sources the phase produced and no `--verification`, and `commands/status.md` passes only the sources it has `[AC-2.3]`
- [x] Given the goal-emit tests and the agent CLI contract, when Story 2 is complete, then `test_goal_emit_command_hooks.sh` asserts only the `/create-goal` emit and the `goal-emit.py` row in `.writ/docs/agent-cli-contract.md` no longer lists `commands/implement-phase.md` `[AC-2.4]`

## Implementation Tasks

- [x] 2.1 Write failing tests in `scripts/tests/test_phase_state.py` for `health` with omitted flags (`not_requested`, `Healthy`) and with passed missing paths (`missing`, `Warning`) `[AC-2.1, AC-2.2]`
- [x] 2.2 Change `cmd_health` and `_artifact_status` in `scripts/phase-state.py` so an omitted flag yields `not_requested`, including `--drift` `[AC-2.1, AC-2.2]`
- [x] 2.3 Edit Step 4.1c in `commands/implement-phase.md` and the `health` call in `commands/status.md` to pass only produced sources; delete Step 1.4 `[AC-2.3]`
- [x] 2.4 Update `scripts/tests/test_goal_emit_command_hooks.sh`, `scripts/tests/test_goal_emit.py` and the `goal-emit.py` row in `.writ/docs/agent-cli-contract.md`; check `scripts/eval.sh` for an implement-phase goal-emit assertion `[AC-2.4]`
- [x] 2.5 Run `python3 scripts/gen-platform-trees.py`; add a dated `KNOWN_OVER_BUDGET` entry if a byte size changed `[AC-2.3]`
- [x] 2.6 Verify acceptance criteria: run `test_phase_state.py`, `test_goal_emit.py`, `test_agent_cli_contract.py`, `test_governor_enforcement.py` on Python 3.9, `bash scripts/tests/test_goal_emit_command_hooks.sh`, and `bash scripts/eval.sh --check=phase-health --report=<scratch path>` and `--check=goal-emit` (not while pytest runs) `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

## Notes

- **Retro F22:** Step 4.1c asks for a verification report no step produces, so `health` always reads `Warning`. `--verification` stays in the CLI for other callers.
- **Behavior change for `--drift`:** today an omitted `--drift` is `missing`. After this story it is `not_requested`. `/status` must pass its drift log explicitly if it has one.
- **Business Rule 5:** `/create-goal` already runs `goal-emit.py emit` after save. Nothing else is lost.
- **Test runs:** run pytest alone; full suites at spec end.

## Context for Agents

- **Error map rows:** [`health` (Story 2), Goal emit removal (Story 2)] — from technical-spec.md error map
- **Shadow paths:** []
- **Business rules:** [4, 5] — from spec.md → Specification Contract → 📋 Business Rules
- **Experience:** [Feedback model] — from spec.md → 🎯 Experience Design

## What Was Built

**Implementation Date:** 2026-11-07

### Files Created

[None created]

### Files Modified

- **`scripts/phase-state.py`** (`health`: an omitted `--eval`/`--verification`/`--drift` is `not_requested`; a passed missing path is `missing`; `--drift` repeats)
- **`commands/implement-phase.md`** (Step 1.4 Goal emit deleted; Step 4.1c passes `[--eval] [--drift ...]`, never `--verification`; 373 → 358 lines)
- **`commands/status.md`** (`health` call passes only the sources it has)
- **`.writ/docs/agent-cli-contract.md`** (`goal-emit.py` row drops `commands/implement-phase.md`)
- **`.writ/docs/phase-execution-state-format.md`**, **`.writ/docs/quality-signal-classification.md`** (Health wording: only passed sources can be missing)
- **`adapters/claude-code.md`** (Goal emit clause names only `/create-goal`)
- **`scripts/eval-phase-health.py`** (two scenarios pass a nonexistent path instead of omitting the flag)
- **`scripts/tests/test_phase_state.py`** (`HealthGivenSourcesTests`, 6 tests)
- **`scripts/tests/test_goal_emit_command_hooks.sh`** (implement-phase emit block removed; new check that `/create-goal` is the only emit caller)
- **`scripts/tests/test_exit_criteria.py`** (Step 1.3 slice ends at `### Phase 2:`; no assertion changed)
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET` for `implement-phase.md` 10297 → 9825, dated)
- **`cursor/plugin/commands/{implement-phase,status}.md`, `plugins/writ/commands/{implement-phase,status}.md`, `plugins/writ/scripts/phase-state.py`** (generated)

### Implementation Decisions

1. **`None` default tells an omitted flag from a given empty path** — `--drift ""` still reads `missing`, as before.
2. **`--drift` repeats** — Step 4.1c passes one log per merged spec; any material log wins, then any missing one (DEV-003).
3. **Post-review doc fixes by the orchestrator** — the state-format Health section, a stale eval comment, and one line in `quality-signal-classification.md` were updated so no doc still says an omitted source is a Warning.

### Test Results

**Verification:** Automated

- ✅ Orchestrator's recorded run (Python 3.9): 868 passed across 11 files; `test_goal_emit_command_hooks.sh` all PASS
- ✅ `eval.sh` checks `phase-health` 8/8, `phase-closure` 39/39, `goal-emit`, `command-structure` 44/44, `size-pins`, `exit-criteria` 18/18 (coder and reviewer runs)
- ✅ `gen-platform-trees.py --check`: pass
- Full suite and `eval.sh`: run once at spec end

**Coverage:** N/A — `test-integrity.py coverage` unverifiable (no coverage report in this repo)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Gate 3 route:** `review-agent` (cross-component; 9 boundary crossings: generated copies and direct consequences of Business Rules 4 and 5)
- **Drift:** Small
- **Security:** Clean
- **Safety fact:** measured `tested` (claimed `tested`)
- **Review file:** the reviewer numbered its drift entry DEV-001; the orchestrator renumbered it DEV-003 in the saved review to match the spec-wide drift log

### Deviations from Spec

See `drift-log.md` Story 2: DEV-003 (Small, auto-amended in spec-lite).

### Lessons Learned

1. **A flag that silently keeps only its last value hides data** — Step 4.1c's "one `--drift` per spec" would have judged only the last log without `action="append"`.

### Next Story

Story 3: Lane result file and shipped brief template.
