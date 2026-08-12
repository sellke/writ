# Story 2: The `close-spec` Subcommand

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1
> **Estimated Tasks:** 7

## User Story

**As** `/implement-phase`, deciding at decomposition time or mid-run that a spec will
never be built,
**I want** a reducer subcommand that records that decision as a terminal status with
its reason,
**So that** the phase state says "closed by decision" instead of lying with `pending`,
and any partial lane work is preserved without being mislabelled a failure.

## Context

Story 1 made the vocabulary enforceable and admitted `closed_unimplemented`. Nothing
writes it yet. This story adds the write path.

The design mirrors `cmd_quarantine` (`scripts/phase-state.py:458`) — worktree removal,
phase-branch-clean assertion, transitive dependent blocking — with one deliberate
subtraction and one deliberate addition:

- **Subtracted:** the `writ/quarantine/{spec}` rename. Nothing failed, so the lane keeps
  its original `writ/phase/{phase}/{spec}` name.
- **Added:** a required, non-empty reason, because the phase report is contractually
  obliged to print it (BR-6).

## Acceptance Criteria

**AC-1: A pending spec closes cleanly with its reason recorded**
```
Given a phase state with spec "spec-a" at status pending and no lane
When `phase-state.py close-spec --state S --repo R --spec spec-a --reason "superseded by measured evidence"` runs
Then spec-a's status is "closed_unimplemented"
And spec-a carries closure {reason: "superseded by measured evidence", closedAt: <ISO8601 Z>}
And no git branch, worktree, or ref was created, renamed, or deleted
And `progress` reports closed_unimplemented: 1 and pending: 0
```

**AC-2: A closure without a reason is refused before any mutation**
```
Given a phase state with spec "spec-a" at status pending
When close-spec runs with --reason omitted, empty, or whitespace-only
Then a ContractError with code "invalid_closure" is raised
And spec-a's status is still "pending"
And the state file's bytes are unchanged
```

**AC-3: Mid-run closure frees the worktree and keeps the branch**
```
Given spec-a is "implementing" with a lane branch and a worktree on disk
And the phase branch head is H
When close-spec runs with a valid reason
Then the worktree is removed and worktreePath is null
And laneBranch still names writ/phase/{phase}/spec-a, and that branch still exists in git
And the phase branch head is still exactly H
And the result reports phaseBranchClean: true
```

**AC-4: Dependents cascade to skipped_blocked with the cause recorded**
```
Given spec-b depends on spec-a, and spec-c depends on spec-b
When close-spec closes spec-a
Then spec-b and spec-c are both "skipped_blocked"
And each blockedBy list contains its upstream spec
And `progress` reports, per blocked spec, that its blocker was closed — not quarantined
And a dependent already at "integrated" is NOT downgraded
```

**AC-5: A phase containing closed specs reconciles as consistent**
```
Given a phase state where spec-a is closed_unimplemented with a retained lane branch
When `phase-state.py reconcile --state S --repo R` runs
Then it returns status "consistent" with attention: false
And `health` returns no Attention attributable to the closure
But if the retained lane branch has since been deleted from git
Then reconcile reports that named mismatch, symmetric with quarantine handling
```

## Implementation Tasks

- [ ] **Write the scenarios first.** Append AC-1..AC-5 scenarios to
      `scripts/eval-phase-closure.py`, using its `new_repo()` helper for the git-backed
      cases (AC-3, AC-5). They fail — `close-spec` does not exist.
- [ ] Implement `cmd_close_spec` in `scripts/phase-state.py`: validate the reason
      first (raise `ContractError("invalid_closure", ...)` on missing/blank **before**
      loading or touching git), resolve the record via `_spec_record`, capture the
      phase-branch head.
- [ ] Handle the lane: remove the worktree via
      `_git(repo, "worktree", "remove", "--force", ...)` when `worktreePath` exists,
      null `worktreePath`, and **retain** `laneBranch` unchanged. Perform no branch
      rename and no branch deletion.
- [ ] Write the closure record: `_set_status(record, "closed_unimplemented")`,
      `record["closure"] = {"reason": reason, "closedAt": _now()}`, and append
      `f"closed:{reason}"` to `evidence`. Re-read the phase head and report
      `phaseBranchClean`.
- [ ] Cascade dependents: reuse `_transitive_dependents(state, spec)`; for each, set
      `skipped_blocked` via `_set_status` and append the closed spec to `blockedBy` —
      **skipping any dependent already in `TERMINAL_SPEC_STATUSES`** so finished work is
      never downgraded (AC-4).
- [ ] Wire the CLI: register the `close-spec` subparser in `main()` with `--state`,
      `--repo`, `--spec`, `--reason` (all required), alongside the existing
      `quarantine` parser. Extend `cmd_reconcile` with the `closed_unimplemented`
      branch from AC-5, and extend `cmd_progress` with the per-blocked-spec cause
      breakdown.
- [ ] **Verify:** run `bash scripts/eval.sh --check=phase-closure`, then
      `--check=phase-lanes`, `--check=phase-challenges`, `--check=phase-quarantine`,
      `--check=phase-health` to prove the shared reducer still satisfies its siblings.

## Technical Notes

- **Reason validation must precede every side effect.** AC-2 requires the state file's
  bytes to be unchanged on rejection, so validate the argument before `_load`, before
  any `_git` call, and certainly before `_atomic_write`.
- **`--repo` is required even for the no-lane case.** A `pending` spec needs no git
  work, but the phase-branch-clean assertion (AC-3) needs the repo, and a uniform
  signature keeps the caller in `/implement-phase` simple. In the no-lane path, the
  head is read twice and compared; no mutation occurs.
- **The terminal-status skip in the cascade is not optional.** Without it, closing a
  spec would flip an already-`integrated` dependent to `skipped_blocked` and silently
  discard a recorded merge commit. `TERMINAL_SPEC_STATUSES` from Story 1 is the guard.
- **`blockedBy` now means two things.** After this story it reads "upstream reached a
  terminal state without delivering" — quarantine *or* closure. `progress` must
  distinguish them (AC-4) or a `/status` reader will hunt for a quarantine branch that
  was never created. Story 3 documents the widening; this story implements the
  distinction.
- **Idempotency is a decision, not an accident.** Closing an already-closed spec must
  either be a clean no-op returning the existing closure, or an explicit
  `ContractError`. Pick one, implement it, and cover it with a scenario.
- `phase-spec-result-v1` stays untouched (BR-9). Closure is an orchestrator decision;
  a subagent has no vocabulary for "do not build this."

## Definition of Done

- [ ] `cmd_close_spec` exists with a registered `close-spec` subparser
- [ ] A blank or missing reason raises `invalid_closure` with the state file untouched
- [ ] Mid-run closure removes the worktree, retains the lane branch, and proves
      `phaseBranchClean`
- [ ] Transitive dependents cascade to `skipped_blocked`; terminal dependents are skipped
- [ ] `progress` distinguishes closure-caused from quarantine-caused blocking
- [ ] `reconcile` returns `consistent` for closed specs and flags a missing retained lane
- [ ] Repeat-closure behavior is decided, implemented, and covered by a scenario
- [ ] `bash scripts/eval.sh --check=phase-closure` and the four sibling phase checks
      report zero findings

## Context for Agents

- **Business rules:** BR-1 (terminal), BR-2 (reason required), BR-3 (worktree freed,
  branch kept), BR-4 (cascade and the widened `blockedBy`), BR-5 (health path stays
  clean), BR-9 (result schema unchanged) — `spec.md → ## Business Rules`
- **Reference implementation:** `cmd_quarantine` at `scripts/phase-state.py:458` — copy
  its shape, drop the `_quarantine_name` rename, add the reason gate.
- **Dependent traversal:** `_transitive_dependents` at `scripts/phase-state.py:445`
  already exists; reuse it rather than rewriting the walk.
- **Edge cases:** closing a spec with no lane; closing an already-closed spec; a
  dependent already `integrated`; cascade depth > 1 — `spec-lite.md → ## For Testing
  Agents → Edge Cases`
- **Shadow paths:** nil reason, empty reason, worktree path recorded but already gone —
  `spec-lite.md → ## For Testing Agents → Shadow Paths to Verify`
- **Do not** touch the docs or command files here. Story 3 owns every contract surface.
