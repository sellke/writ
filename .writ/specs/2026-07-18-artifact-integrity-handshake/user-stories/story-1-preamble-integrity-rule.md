# Story 1: Artifact Integrity Convention in `_preamble.md`

> **Status:** Complete
> **Priority:** High
> **Dependencies:** None
> **Story Points:** 2

## User Story

As a **Writ command author**, I want **a standing Artifact Integrity rule in the preamble**, so that **every command has one consistent, adapter-neutral way to verify its inputs and fail early with a helpful repair offer.**

## Acceptance Criteria

1. **Given** `_preamble.md`, **when** I read it, **then** it has an `## Artifact Integrity` section defining the Required Artifacts convention (required vs optional), the check-then-HALT behavior, and bounded repair (name the creating command, no auto-mutation).
2. **Given** the section, **when** a command declares required artifacts, **then** the preamble's rule tells it to HALT + offer repair on required absence and warn+degrade on optional absence.
3. **Given** the section, **when** read on any platform, **then** it uses only generic existence checks (adapter-neutral).

## Implementation Tasks

- [x] Add the `## Artifact Integrity` section to `commands/_preamble.md` per technical-spec §1 (after "File Organization").
- [x] Include the required/optional distinction, HALT + bounded-repair behavior, and the common artifact → creating-command map.
- [x] State adapter neutrality explicitly.
- [x] Ensure wording aligns with existing preamble tone and the Prime Directive (no auto-mutation without confirmation).

## Technical Notes

- This is the foundation Stories 2–3 build on; keep it concise (preamble is shared standing instructions, not a manual).
- See `sub-specs/technical-spec.md → §1`.
- Preamble length cap is 80 lines (`eval.sh` length check); Artifact Integrity lands compactly and User Challenge is densified only enough to keep the file ≤80 while retaining `four required parts` and the challenge field names.

## Definition of Done

- [x] `_preamble.md` has the Artifact Integrity section covering convention + HALT + repair + neutrality.
- [x] Tone consistent with the rest of the preamble.

## Context for Agents

- **Files in scope:** `commands/_preamble.md`.
- **Format reference:** `sub-specs/technical-spec.md → §1`.
- **Business rules:** required vs optional; bounded repair; adapter-neutral.
- **Downstream:** Stories 2 (context.md map) and 3 (declarations) depend on this convention.

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Created

[None created]

### Files Modified

- **`commands/_preamble.md`** (after File Organization; 80-line cap)
  - Added `## Artifact Integrity`: Required Artifacts convention (*required* / *optional*), HALT + bounded repair via AskQuestion (no auto-mutation), warn+degrade for optional, common artifact → creating-command map, adapter-neutral existence checks (never inspect `.writ/state/`). Densified User Challenge just enough to stay within the 80-line preamble length limit while preserving `four required parts` and field names.

### Implementation Decisions

1. **Compact preamble addition under the 80-line cap** — Artifact Integrity is load-bearing for every command, so it stays in `_preamble.md` rather than a satellite file; User Challenge was densified (not semantically weakened) to make room.
2. **Explicit `.writ/state/` exclusion** — matches technical-spec non-goals and prevents integrity checks on ephemeral gitignored state.

### Test Results

**Verification:** Static (methodology repo — no runtime)
- ✅ `python3 scripts/eval-artifact-integrity.py` → 6/6 preamble scenarios PASS
- ✅ `bash scripts/eval.sh --check=length` → PASS (80 lines, limit 80)
- ✅ `bash scripts/eval.sh --check=phase-challenges` → PASS (User Challenge contract retained)

**Coverage:** N/A (markdown command deliverable)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
