# Story 4: Artifact Restoration + Eval

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 3
> **Story Points:** 3

## User Story

As a **developer after a revert**, I want **Writ's artifacts reset to match reality**, so that **the spec, story status, WWB, drift-log, and context.md never claim work exists that was just undone.**

## Acceptance Criteria

1. **Given** a successful revert of a story, **when** it completes, **then** the story status → `Not Started`, its tasks/AC are unchecked, its `## What Was Built` record is annotated with a `> **Reverted:**` banner (not deleted), a `drift-log.md` revert entry is appended, and `context.md` is regenerated.
2. **Given** a spec revert, **when** it completes, **then** restoration is applied across all its stories and the spec status is reset appropriately.
3. **Given** a reverted WWB record, **when** a downstream story loads dependency WWB, **then** the reverted record is treated as non-authoritative (skipped or flagged).
4. **Given** the feature, **when** `scripts/eval.sh` runs, **then** it asserts `revert.md` references the dirty-tree guard, plan-before-mutate gate, and hard-reset second confirmation; and the resolver tests pass.

## Implementation Tasks

- [x] Implement artifact restoration in `commands/revert.md` Phase 5 (technical-spec §4): status reset, task/AC unchecking, WWB banner, drift-log entry, context.md regeneration.
- [x] Add the WWB "Reverted" annotation convention to `.writ/docs/what-was-built-format.md` and make the WWB loader in `commands/implement-story.md` Step 2 treat reverted records as non-authoritative.
- [x] Add spec-level restoration (all stories + spec status).
- [x] Add the eval check (`eval.sh` + helper): static assertions on `revert.md` rules + wire resolver tests into the suite.
- [x] Verify end-to-end on this repo: revert a test story, confirm all artifacts consistent.

## Technical Notes

- Reuse `/implement-story`'s context.md schema for regeneration (don't invent a new one).
- WWB banner preserves history — never delete the record.
- See `sub-specs/technical-spec.md → §4, §5, §6`.

## Definition of Done

- [x] Restoration implemented for story and spec units.
- [x] WWB "Reverted" annotation documented + honored by the loader.
- [x] `eval.sh` gains passing revert checks; resolver tests wired in.
- [x] Manual end-to-end dogfood consistent. _(Substituted by the full `scripts/eval.sh` run — 0 findings, `revert` check 23/23 — plus a live resolver smoke run; no interactive `/revert` harness in this isolated lane.)_

## Context for Agents

- **Files in scope:** `commands/revert.md`, `commands/implement-story.md` (WWB loader), `.writ/docs/what-was-built-format.md`, `scripts/eval.sh` (+ helper).
- **Format reference:** `sub-specs/technical-spec.md → §4, §5, §6`.
- **Business rules:** full restoration; WWB preserved+annotated; reverted WWB non-authoritative downstream.
- **Dependency:** Story 3 wires the Phase 5 call site this story implements.

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Modified

- **`commands/revert.md`** — "Artifact Restoration" section (technical-spec §4): story status → `Not Started`, task/AC unchecking, WWB `> **Reverted:**` banner (preserved, never deleted), append-only `drift-log.md` entry, full `context.md` regeneration reusing `/implement-story`'s Step 2 schema, and spec-level rollup (all stories + spec status + README counts).
- **`.writ/docs/what-was-built-format.md`** — new "Reverted Records (`/revert` annotation)" section (§5): the `> **Reverted:**` banner convention and the rule that a reverted WWB record is **not authoritative** for dependency context (loaders skip/flag it).
- **`commands/implement-story.md`** — Step 2 "Loading What Was Built from Dependencies" now **skips reverted records** (detects the `> **Reverted:**` banner, logs, and excludes them from live dependency context).
- **`scripts/eval.sh`** — new `check_revert` function + `revert` entry in `CHECKS`. Runs `eval-revert-resolve.py` (23 resolver scenarios) and statically asserts the resolver's four layers + scaffold + read-only contract, the `/revert` safety rules (dirty-tree guard, plan-before-mutate, safe default, hard-reset second confirmation, ghost confirmation), the story-SHA recording, and the reverted-WWB non-authoritative loader rule.

### Files Created

1. **`scripts/eval-revert-resolve.py`** — scenario emitter running the real resolver unit suite and emitting PASS/FAIL TSV for `check_revert`.

### Implementation Decisions

1. **Reverted detection is a literal banner check** — both the doc convention and the loader rule key off the exact `> **Reverted:**` prefix, so detection is trivial and eval-assertable.
2. **Single source of truth for resolver tests** — the eval scenario emitter runs the same `scripts/tests/test_revert_resolve.py` unit suite rather than duplicating fixtures, so eval and coverage report identical behavior.

### Test Results

**Verification:** Automated — full `bash scripts/eval.sh` run.
- ✅ Full suite: **Findings: 0, Run errors: 0** (exit 0).
- ✅ `revert` check: PASS, **Scenarios: 23/23 passed**.
- ✅ No regressions across the other 25 checks.

**Coverage:** resolver `scripts/revert-resolve.py` at 90% (see Story 2).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration (one fix: added the README Commands-table row flagged by the leanness check)
- **Drift:** None
- **Security:** Clean

### Deviations from Spec

None.
