# Story 1: Enforced Status Vocabulary

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None
> **Estimated Tasks:** 7

## User Story

**As a** maintainer reading `phase-execution-v2` state,
**I want** the spec-status vocabulary to be a load-bearing constraint rather than a
comment,
**So that** a status the reducer cannot express is refused at the moment of writing
instead of surfacing months later as a misreported phase.

## Context

`SPEC_STATUSES` is declared at `scripts/phase-state.py:52` and referenced **nowhere**
in the repository — no validation, no membership test, no lookup. It is documentation
wearing a constant's clothes. Two consequences, both live today:

1. Adding `closed_unimplemented` to the set (the issue's stated fix) would change zero
   behavior on its own.
2. The set is already wrong: `cmd_record_challenge` (`scripts/phase-state.py:316`)
   writes `status = "challenge_required"`, which is absent from the set *and* absent
   from the `cmd_progress` counts initializer.

This story makes the set real before anything is added to it. Enforcement must land
*with* `challenge_required`, or the reducer would start rejecting a write it already
performs.

## Acceptance Criteria

**AC-1: Unknown statuses are refused at the write boundary**
```
Given a phase state file with a spec record
When any reducer path attempts to set that spec's status to a value not in SPEC_STATUSES
Then a ContractError with code "invalid_status" is raised naming the rejected value
And the state file on disk is unchanged
```

**AC-2: Unknown statuses are tolerated at the read boundary**
```
Given a hand-written state file whose spec record has status "future_value"
When `phase-state.py progress --state <file>` runs
Then the command exits 0
And the counts object contains "future_value": 1 alongside the known statuses
```

**AC-3: The vocabulary admits both new values**
```
Given the reducer's SPEC_STATUSES set
When it is inspected
Then it contains "closed_unimplemented" and "challenge_required"
And `record-challenge` on an unresolved challenge still succeeds, writing
    status "challenge_required" without raising invalid_status
```

**AC-4: Progress counts cannot drift from the vocabulary**
```
Given a freshly initialized phase with two pending specs
When `phase-state.py progress` runs
Then the counts object contains a key for every value in SPEC_STATUSES
And every status with no specs reports 0 rather than being absent
```

**AC-5: The check is registered and green**
```
Given the new phase-closure eval check
When `bash scripts/eval.sh --check=phase-closure` runs at the end of this story
Then it reports zero findings
```

## Implementation Tasks

- [x] **Write the scenarios first.** Create `scripts/eval-phase-closure.py` following
      the `scripts/eval-phase-health.py` shape (module docstring, `emit()`, `helper()`,
      `new_repo()`, PASS/FAIL TSV on stdout, exit non-zero on failure). Cover AC-1
      through AC-4. They fail against the current reducer.
- [x] Register the check: add `phase-closure` to the `CHECKS` array in
      `scripts/eval.sh` (after `phase-health`) and add a `check_phase_closure()`
      function that runs the scenario file and tallies PASS/FAIL, modeled on
      `check_phase_health()` at `scripts/eval.sh:2369`. Static `require_literal`
      assertions are **not** added in this story — Story 3 adds them.
- [x] Extend `SPEC_STATUSES` in `scripts/phase-state.py` with `closed_unimplemented`
      and `challenge_required`, and add a `TERMINAL_SPEC_STATUSES` set
      (`integrated`, `quarantined`, `skipped_blocked`, `closed_unimplemented`).
- [x] Add the `_set_status(record, value)` guard that raises
      `ContractError("invalid_status", ...)` for any value outside `SPEC_STATUSES`.
- [x] Route every mutation site through it: `cmd_create_lane`, `cmd_record_challenge`,
      `cmd_integrate` (merge-conflict path **and** success path), `cmd_retry`,
      `cmd_quarantine` (rename-failure path, success path, **and** the dependent
      blocking loop). Validate `cmd_init`'s literal `"pending"` once at construction.
- [x] Seed `cmd_progress`'s counts dict from `sorted(SPEC_STATUSES)` while keeping the
      `counts.get(status, 0) + 1` accumulation, so an unrecognized status read from
      disk is still counted under its own key (AC-2).
- [x] **Verify:** `grep -n 'record\["status"\]\s*=' scripts/phase-state.py` returns
      only the line inside `_set_status`; then run `bash scripts/eval.sh
      --check=phase-closure`, plus `--check=phase-lanes`, `--check=phase-challenges`,
      `--check=phase-quarantine`, `--check=phase-health` to prove no regression.

## Technical Notes

- **Write-validate, read-tolerate is the whole design.** The schema's compatibility
  promise is "unknown fields preserved so later stories can extend it." Rejecting an
  unrecognized status on *read* would turn a state file written by a newer reducer into
  a hard failure. Guard mutation only.
- `cmd_record_challenge` is the trap. It writes `"challenge_required"` today. If
  enforcement lands without that value in the set, every unresolved challenge starts
  raising `invalid_status`. Add the value in the same commit as the guard.
- `cmd_progress` seeding from the set is what makes the two structurally unable to
  drift — it is the actual fix for the class of bug this story exists to close, not a
  cosmetic tidy.
- No `schemaVersion` bump. Adding permitted status values is minor-compatible.
- Eval scripts are excluded from the install surface automatically by
  `is_shippable_script` (`scripts/install.sh:726`, `eval-*` pattern) — no manifest
  entry needed.

## Definition of Done

- [x] `scripts/eval-phase-closure.py` exists and its AC-1..AC-4 scenarios pass
- [x] `phase-closure` is in `scripts/eval.sh` `CHECKS` with a working
      `check_phase_closure()`
- [x] `SPEC_STATUSES` contains both new values; `TERMINAL_SPEC_STATUSES` exists
- [x] `_set_status` is the only place that assigns `record["status"]`
- [x] `cmd_progress` counts are seeded from `SPEC_STATUSES` and tolerate unknown values
- [x] `bash scripts/eval.sh --check=phase-closure` reports zero findings
- [x] The four sibling phase checks still report zero findings

## Context for Agents

- **Business rules:** BR-7 (validate on write, tolerate on read) and BR-8 (schema stays
  at version 2) — `spec.md → ## Business Rules`
- **The dead-code finding:** `spec.md → ## The Defect → ### Two findings that reshape
  the fix`
- **Shadow paths:** "Unknown status on read" and the nil/empty reason cases —
  `spec-lite.md → ## For Testing Agents → Shadow Paths to Verify`. Only the read case
  applies to this story; the reason cases belong to Story 2.
- **Reference implementations:** `scripts/eval-phase-health.py` for the scenario-file
  shape; `scripts/eval.sh:2369` (`check_phase_health`) for the eval.sh wiring.
- **Do not** add `close-spec` here. This story establishes the vocabulary; Story 2
  writes the status.
