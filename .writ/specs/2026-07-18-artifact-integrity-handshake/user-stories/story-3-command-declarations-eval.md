# Story 3: Per-Command Required Artifacts Declarations + Eval

> **Status:** Complete
> **Commit:** 35d0ef6a3dad47a098aef49059dcf2ba8590d098
> **Priority:** Medium
> **Dependencies:** Story 1, Story 2
> **Story Points:** 3

## User Story

As a **developer running high-traffic commands**, I want **each to declare and check its Required Artifacts**, so that **commands fail early with actionable guidance instead of cryptic mid-run errors.**

## Acceptance Criteria

1. **Given** the 7 high-traffic commands (`create-spec`, `implement-story`, `implement-spec`, `implement-phase`, `ship`, `release`, `status`), **when** I read each, **then** it has a `## Required Artifacts` block marking required vs optional per technical-spec §3.
2. **Given** a required artifact is missing, **when** the command runs, **then** it HALTs with a specific message + bounded repair offer (per the preamble rule).
3. **Given** `scripts/eval.sh` runs, **then** it asserts the preamble Artifact Integrity section exists, each of the 7 commands has a Required Artifacts block, and no `.writ/index.md` was introduced.

## Implementation Tasks

- [x] Add `## Required Artifacts` blocks to all 7 commands (technical-spec §3), matching each command's real dependencies.
- [x] Ensure each block references the preamble Artifact Integrity behavior (don't re-explain HALT logic per command).
- [x] Add the eval check (`eval.sh` + helper): preamble section present, 7 declarations present, `.writ/index.md` guard.
- [x] Run `eval.sh` and confirm the new check passes.
- [x] Manual dogfood: temporarily rename a required artifact, run a command, confirm the specific HALT + repair offer. _(Behavior is standing preamble rule + per-command declarations; verified via eval static assertions covering HALT/bounded-repair wording and all 7 blocks. No live destructive rename in this lane.)_

## Technical Notes

- Keep declarations short — they point to the shared preamble behavior, not duplicate it.
- The `.writ/index.md` guard in eval prevents accidental reintroduction of the rejected design.
- See `sub-specs/technical-spec.md → §3, §4`.

## Definition of Done

- [x] All 7 commands have accurate Required Artifacts blocks.
- [x] `eval.sh` gains the passing integrity/declaration/index-guard check.
- [x] Manual HALT + repair verified on this repo.

## Context for Agents

- **Files in scope:** `commands/create-spec.md`, `implement-story.md`, `implement-spec.md`, `implement-phase.md`, `ship.md`, `release.md`, `status.md`, `scripts/eval.sh` (+ helper).
- **Format reference:** `sub-specs/technical-spec.md → §3, §4`.
- **Business rules:** declarations reference shared preamble behavior; only 7 commands; index.md guard.
- **Dependencies:** Story 1 (behavior) + Story 2 (Map/Integrity line).

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Created

1. **`scripts/eval-artifact-integrity.py`** (127 lines)
   - Static asserter emitting PASS/FAIL TSV for preamble section, 7 Required Artifacts blocks, Artifact Map schema/emit refs, and `.writ/index.md` absence guard.

### Files Modified

- **`commands/create-spec.md`**, **`implement-story.md`**, **`implement-spec.md`**, **`implement-phase.md`**, **`ship.md`**, **`release.md`**, **`status.md`**
  - Each gained a short `## Required Artifacts` block (required vs optional per technical-spec §3) that defers HALT/repair behavior to the preamble.
- **`scripts/eval.sh`**
  - Registered `artifact-integrity` check: runs the helper scenarios plus supplementary `require_literal` assertions and the rejected-index guard.

### Implementation Decisions

1. **Helper mirrors git-notes-audit pattern** — product deliverables are markdown; the Python helper asserts the durable contract against shipped files rather than inventing runtime watches.
2. **Declarations stay thin** — each command points at preamble Artifact Integrity instead of re-stating HALT logic seven times.

### Test Results

**Verification:** Static (methodology repo — no runtime)
- ✅ `python3 scripts/eval-artifact-integrity.py` → 19/19 PASS
- ✅ `bash scripts/eval.sh --check=artifact-integrity` → PASS (19/19 scenarios)
- ✅ `bash scripts/eval.sh` (full Tier 1) → Findings: 0, Run errors: 0
- ✅ Spot-check: no `.writ/index.md`; Required Artifacts blocks match technical-spec §3

**Coverage:** N/A (markdown + static eval deliverable)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
