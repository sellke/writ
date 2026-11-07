# Story 2: Health counts given sources; Goal emit leaves the phase

> **Status:** Not Started
> **Priority:** Normal
> **Dependencies:** Story 1

## User Story

**As a** developer reading a phase report
**I want to** `health` to judge only the evidence the phase produced, and the phase to stop emitting Goal files
**So that** a clean phase reads `Healthy` instead of a permanent `Warning`, and the command does only phase work

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given `phase-state.py health` is called with no `--eval`, `--verification` or `--drift` flag and the state reconciles, when it runs, then each omitted source reads `not_requested` and the category is `Healthy` `[AC-2.1]`
- [ ] Given `health` is called with a `--verification` or `--drift` path that does not exist, when it runs, then that source reads `missing` and the category is `Warning` `[AC-2.2]`
- [ ] Given `commands/implement-phase.md`, when Story 2 is complete, then Step 1.4 is gone, Step 4.1c passes only the sources the phase produced and no `--verification`, and `commands/status.md` passes only the sources it has `[AC-2.3]`
- [ ] Given the goal-emit tests and the agent CLI contract, when Story 2 is complete, then `test_goal_emit_command_hooks.sh` asserts only the `/create-goal` emit and the `goal-emit.py` row in `.writ/docs/agent-cli-contract.md` no longer lists `commands/implement-phase.md` `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write failing tests in `scripts/tests/test_phase_state.py` for `health` with omitted flags (`not_requested`, `Healthy`) and with passed missing paths (`missing`, `Warning`) `[AC-2.1, AC-2.2]`
- [ ] 2.2 Change `cmd_health` and `_artifact_status` in `scripts/phase-state.py` so an omitted flag yields `not_requested`, including `--drift` `[AC-2.1, AC-2.2]`
- [ ] 2.3 Edit Step 4.1c in `commands/implement-phase.md` and the `health` call in `commands/status.md` to pass only produced sources; delete Step 1.4 `[AC-2.3]`
- [ ] 2.4 Update `scripts/tests/test_goal_emit_command_hooks.sh`, `scripts/tests/test_goal_emit.py` and the `goal-emit.py` row in `.writ/docs/agent-cli-contract.md`; check `scripts/eval.sh` for an implement-phase goal-emit assertion `[AC-2.4]`
- [ ] 2.5 Run `python3 scripts/gen-platform-trees.py`; add a dated `KNOWN_OVER_BUDGET` entry if a byte size changed `[AC-2.3]`
- [ ] 2.6 Verify acceptance criteria: run `test_phase_state.py`, `test_goal_emit.py`, `test_agent_cli_contract.py`, `test_governor_enforcement.py` on Python 3.9, `bash scripts/tests/test_goal_emit_command_hooks.sh`, and `bash scripts/eval.sh --check=phase-health --report=<scratch path>` and `--check=goal-emit` (not while pytest runs) `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`

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
