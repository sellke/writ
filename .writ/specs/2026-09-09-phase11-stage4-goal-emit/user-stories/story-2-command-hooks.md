# Story 2: Hooks — create-goal After Save and implement-phase Origin Emit

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer running `/create-goal` or `/implement-phase`
**I want** `python3 scripts/goal-emit.py emit` invoked after a `loop: yes` card save and when a phase origin resolves to a Goal Card path
**So that** `GOAL.md` / `VERIFY.md` and the printed invoke line appear without registering a `/goal` hook, changing `/implement-story` spawn, or failing the command on `loop: no` or a missing origin

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `/create-goal` Phase 3 has just saved a `loop: yes` card at `.writ/issues/goals/<YYYY-MM-DD>-<slug>.md`, when the command continues, then it runs `python3 scripts/goal-emit.py emit --card <path>`, prints the invoke line the helper emits, and Core Rule 4 still holds (never registers a `/goal` hook, never iterates, never calls `/create-spec`). `[AC-2.1]`
- [ ] Given Phase 3 saves a `loop: no` card, when the command would emit, then it does not create an emit dir, records `unverifiable` `loop_no` via `add_note`, and the save confirmation still succeeds. `[AC-2.2]`
- [ ] Given `/implement-phase` can resolve a Goal Card path from spec `Origin:` or issue `spec_ref`, when that path is known, then it runs the same `emit --card` CLI and prints the invoke line; when no origin path exists, then it records an `unverifiable` note and the phase continues (not fail). `[AC-2.3]`
- [ ] Given an emit run from either command, when the helper prints `pass`, `fail`, or `unverifiable`, then the command uses `add_note` and does not AskQuestion on emit notes; `add_finding` is used only if `scripts/goal-emit.py` is missing or exits 2; neither command calls `/goal`; `commands/implement-story.md` spawn is unchanged; no new agent file is added; `adapters/claude-code.md` three-way disjunction is not rewritten (Story 3 owns the paste sentence). `[AC-2.4]`
- [ ] Given a command-body / eval-wiring test in the Stage 3 / `scripts/tests/test_spec_analyze_command_hooks.sh` pin shape (temp tree, no mutation of the real repo), when it runs, then `commands/create-goal.md` and `commands/implement-phase.md` name `python3 scripts/goal-emit.py emit`, a helper `fail` or `unverifiable` is notes-only for the command contract, and helper-missing / exit 2 is a finding. `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write `scripts/tests/test_goal_emit_command_hooks.sh` (bash, Stage 3 hook-test shape: temp tree, no mutation of the real repo) that greps `commands/create-goal.md` for Phase 3 save plus `python3 scripts/goal-emit.py emit --card`, greps `commands/implement-phase.md` for the same CLI when origin resolves, asserts `loop: no` / missing origin are notes-only, and asserts missing helper or exit 2 is `add_finding` `[AC-2.1, AC-2.2, AC-2.3, AC-2.5]`
- [ ] 2.2 After Phase 3 save in `commands/create-goal.md`, run emit on `loop: yes` (`--card` = the saved path); print the invoke line; keep Core Rule 4 (no hook registration, no iterate, no `/create-spec`) `[AC-2.1]`
- [ ] 2.3 On `loop: no` in `commands/create-goal.md`, skip emit, `add_note` `unverifiable` `loop_no`, and leave the save confirmation unchanged `[AC-2.2]`
- [ ] 2.4 In `commands/implement-phase.md`, when origin resolves to a Goal Card path (spec `Origin:` / issue `spec_ref`), run the same emit and print the invoke line; missing origin → `add_note` unverifiable and continue `[AC-2.3]`
- [ ] 2.5 Document `add_note` for emit verdicts and `add_finding` only if the helper is missing or exits 2 in both command bodies; confirm no `/goal` registration, no edit to `commands/implement-story.md`, no new file under `agents/`, and no rewrite of the `adapters/claude-code.md` three-way disjunction `[AC-2.4]`
- [ ] 2.6 Verify acceptance criteria: `bash scripts/tests/test_goal_emit_command_hooks.sh` green; create-goal Core Rule 4 intact; implement-phase continues without origin; closing commit appends `{date} stage-4a:` for hooks only `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

**Depends on Story 1.** The CLI (`emit --card`, verdict table, invoke line on stdout after summary) must already exist. This story only names that CLI in command bodies and prints a line.

**create-goal Core Rule 4 stays.** The card is not a runner. Emit writes files and prints the invoke line. Do not register a `/goal` hook, do not iterate, do not call `/create-spec`.

**implement-phase origin.** Resolve from spec `Origin:` or issue `spec_ref` back to a Goal Card. No path → unverifiable note, not fail. Do not invent a card.

**Advisory.** Emit `pass` / `fail` / `unverifiable` never fail `/create-goal` save or `/implement-phase` progress. `add_finding` is reserved for helper missing or exit 2. No AskQuestion on emit notes.

**Out of scope.** No new agent file. Do not edit `commands/implement-story.md`. Do not rewrite `adapters/claude-code.md` clauses (a)/(b)/(c) — Story 3 owns the paste sentence and `eval.sh` `CHECKS` registration. This story’s bash test is command-body / notes-vs-finding wiring.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [eval.sh live, Helper missing]
- **Shadow paths:** [Upstream]
- **Business rules:** [Rule 1 (Emit is not register — Core Rule 4 stays), Rule 2 (`loop: no` does not emit — unverifiable `loop_no`), Rule 5 (Single-slot reminder stays in the adapter; emitter does not register hooks), Rule 8 (Advisory for helper health only — loop:no / missing card are notes; missing helper / exit 2 is a finding)]
- **Experience:** [Entry point (/create-goal loop:yes save; /implement-phase with Goal Card origin), Happy path (emit after save; print invoke), Feedback model (add_note vs add_finding), Error experience (loop:no and missing origin are notes; helper missing / exit 2 is a finding; no AskQuestion on emit notes)]
