# Story 3: Lane result file and shipped brief template

> **Status:** Not Started
> **Priority:** Normal
> **Dependencies:** Story 2

## User Story

**As a** phase orchestrator
**I want to** each lane to write its `phase-spec-result-v1` to a known file from a shipped brief template
**So that** a dropped or truncated reply no longer loses a lane's result, and the brief stops growing per run

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given `phase-state.py create-lane` runs for a spec, when it succeeds, then `specs.{id}.resultPath` holds an absolute path under the main checkout's `.writ/state/` named `lane-result-<phase>-<spec>.json` `[AC-3.1]`
- [ ] Given `commands/_lane-brief.md` exists with placeholders for spec path, phase state, lane branch, worktree, mode, result path and answer sources, when Step 3.2 of `implement-phase.md` and § Phase-Orchestrated Lane Mode of `implement-spec.md` are read, then both reference the template and the lane writes its result to `{result_path}` before replying `[AC-3.2]`
- [ ] Given a lane's result file is missing or does not parse as `phase-spec-result-v1`, when the orchestrator handles it, then it resumes the same lane agent once to write the file and classifies a second miss as `transient` `[AC-3.3]`
- [ ] Given the shipped-file checks, when `test_eval_shipped_refs.py` and `python3 scripts/gen-platform-trees.py --check` run, then `commands/_lane-brief.md` is shipped by `install.sh` and present in each generated tree that ships `commands/` `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write failing tests in `scripts/tests/test_phase_state.py` for `create-lane` recording `resultPath` and for `validate-result --input` reading that file `[AC-3.1, AC-3.3]`
- [ ] 3.2 Add `resultPath` to `create-lane` in `scripts/phase-state.py` and to the field contract in `.writ/docs/phase-execution-state-format.md` `[AC-3.1]`
- [ ] 3.3 Write `commands/_lane-brief.md` from the brief used in Phase 15 (retro F22), with the placeholders named in technical-spec.md → Lane result file `[AC-3.2]`
- [ ] 3.4 Edit Step 3.2 of `commands/implement-phase.md` (brief template, result file, supervisor gets the file path, one resume then `transient`) and § Phase-Orchestrated Lane Mode of `commands/implement-spec.md`; delete the truncated-result paragraph `[AC-3.2, AC-3.3]`
- [ ] 3.5 Confirm `scripts/install.sh` and `scripts/gen-platform-trees.py` ship `commands/_lane-brief.md`; add it where they list underscore files explicitly; run `python3 scripts/gen-platform-trees.py` `[AC-3.4]`
- [ ] 3.6 Verify acceptance criteria: run `test_phase_state.py`, `test_eval_shipped_refs.py`, `test_governor_enforcement.py` on Python 3.9 and `python3 scripts/gen-platform-trees.py --check` `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

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
