# Story 1: Reframe the Boundary

> **Status:** Completed ✅
> **Commit:** e651e95f878333e2f476e0c2b2f4abe4b4d190d4
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer reading command files and completion output to decide the next lifecycle step
**I want to** see `/verify-spec --product` framed as a post-implementation check whose findings feed `/plan-product --reconcile`, and `--reconcile` hand back to delivery instead of to verification
**So that** the lifecycle reads in one direction (verification surfaces drift, realignment acts on it, delivery follows) and no planning step sends me to a verification step

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `commands/verify-spec.md`, `commands/verify-spec.lean.md`, and `commands/plan-product.md`, when each is searched for the direction sentence, then each contains "Verification surfaces drift after implementation; `/plan-product --reconcile` realigns the baseline when it does." verbatim, and none still contains "a lint you run before deciding anything", "consistency lint (before)", or the `/assess-spec` analogy in its boundary text `[AC-1.1]`
- [x] Given `commands/verify-spec.md`, when its frontmatter `description:` and the `--product` Modes row are read, then the description names product docs as a second scope checked after implementation and the Modes row frames `--product` as run after specs ship `[AC-1.2]`
- [x] Given `commands/plan-product.md`, when `rg -n "verify-spec --product"` runs against it, then only the Step R2 lines that consume findings match, Step R4's closing paragraph suggests `/create-spec` for the next roadmap item and keeps its roadmap-revision note, and the Reconcile boundary paragraph no longer says "(before)" `[AC-1.3]`
- [x] Given `scripts/eval.sh` with a registered `check_product_check_direction`, when each of its pins is mutated in turn (direction sentence removed from one file, or a forbidden literal reinserted), then that mutation alone makes the check report a finding, and with the edits in place `bash scripts/eval.sh` reports Findings 0 `[AC-1.4]`
- [x] Given the byte-budget ratchet entry `10898` for `commands/verify-spec.md` in `scripts/tests/test_governor_enforcement.py` and the lean heading parity in `scripts/tests/test_lean_commands.py`, when `uv run pytest` runs after the rewording, then both pass with the ratchet entry unchanged, `verify-spec.md` at or below its prior byte count, and every lean-twin section heading identical to before `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Add `check_product_check_direction` to `scripts/eval.sh`, registered with the other `check_*` functions: `require_literal` the direction sentence in all three files, `forbid_literal` "suggest `/verify-spec --product` to confirm" in `plan-product.md`, and `forbid_literal` "a lint you run before deciding anything" and "consistency lint (before)" in `verify-spec.md` and `verify-spec.lean.md`; run it and confirm it fails against the current files; record `wc -c commands/verify-spec.md` as the byte baseline `[AC-1.1, AC-1.3, AC-1.4]`
- [x] 1.2 Rewrite `commands/verify-spec.md`: frontmatter `description:`, the `--product` Modes row (line 35), the callout (line 37), and the Product Consistency "Boundary (critical)" paragraph (lines 625–631), writing the direction sentence and dropping the `/assess-spec` analogy; trim within the same section so net bytes stay at or below the baseline `[AC-1.1, AC-1.2, AC-1.5]`
- [x] 1.3 Mirror the same wording in `commands/verify-spec.lean.md` at lines 33–35 and 295, leaving every section heading untouched `[AC-1.1, AC-1.5]`
- [x] 1.4 Rewrite `commands/plan-product.md`: the Reconcile "Boundary (critical)" paragraph (lines 37–45) gets the direction sentence and loses "(before)" and the `/assess-spec` analogy; the Step R4 closing paragraph (line 106) replaces the `/verify-spec --product` suggestion with "suggest `/create-spec` for the next roadmap item" and keeps the roadmap-revision note; Step R2 lines 66 and 74 stay `[AC-1.1, AC-1.3]`
- [x] 1.5 Prove each pin bites: for each `require_literal` and `forbid_literal` in `check_product_check_direction`, apply one mutation (delete the sentence from one file, or reinsert one forbidden literal), confirm `bash scripts/eval.sh --check=product_check_direction` reports a finding, then revert `[AC-1.4]`
- [x] 1.6 Verify the acceptance criteria: `rg -n "verify-spec --product" commands/plan-product.md` shows only Step R2 lines; `rg -n "assess-spec|\(before\)" commands/verify-spec.md commands/verify-spec.lean.md commands/plan-product.md` shows no boundary-text hits; `wc -c commands/verify-spec.md` is at or below the baseline `[AC-1.1, AC-1.2, AC-1.3, AC-1.5]`
- [x] 1.7 Verify all tests pass: `uv run pytest` (including `test_governor_enforcement.py` and `test_lean_commands.py`) and `bash scripts/eval.sh` reporting Findings 0, run outside the sandbox `[AC-1.4, AC-1.5]`

## Notes

- **Byte ratchet is the hard constraint.** `verify-spec.md` is a recorded violator (entry `10898`); the ratchet is one-way, so the rewrite must not grow the file. Removing the `/assess-spec` analogy and the "(before)/(after)" phrasing frees bytes; spend them on the direction sentence and the description change. Do not touch the ratchet entry in this story.
- **Line numbers are hints, not anchors.** Locate each edit by its text ("Boundary (critical)", the `--product` Modes row, Step R4's closing paragraph) before editing; earlier edits in the same file shift later line numbers.
- **Rewording only.** Checks P1–P4, their dispositions, auto-fix scope, `--product --check`, and the report path must be unchanged in substance.
- **Step R2 is not a violation.** Its references read verification findings, which Business Rule 2 allows. The `forbid_literal` targets only the R4 "to confirm" suggestion, so R2 survives the pin.
- **`commands/retro.md:170` is the model wording** and must not change.
- **Eval pins and backticks.** The direction sentence and the forbidden R4 literal both contain backticks; quote them so the `require_literal`/`forbid_literal` arguments match the file bytes exactly. Step 1.5's mutation proof is what catches a quoting mistake that leaves a pin unable to fail.
- **Integration with Story 2.** Story 2 depends on this story and adds its own pins to the same `check_product_check_direction` function, so name it and register it so Story 2 can extend it without restructuring.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [] — technical-spec.md → Error & Rescue Map marks this not applicable
- **Shadow paths:** [Happy path (reconcile hands back to `/create-spec`), Reconcile run with no prior verification (R2 unchanged, R4 ends with delivery hand-back)] — from technical-spec.md → Shadow Paths
- **Business rules:** [Rule 1 (One direction: no `/plan-product` mode points to verification as its next action), Rule 2 (Consumption is allowed: Step R2 may read findings), Rule 3 (No behavior change to the lint)] — from spec.md → Business Rules
- **Experience:** [Moment of truth (no verification step suggested right after a planning step), Happy path step 3 (reconcile points back to `/create-spec`)] — from spec.md → Experience Design
- **Technical spec:** [Files and Edits rows for `verify-spec.md`, `verify-spec.lean.md`, `plan-product.md`, `scripts/eval.sh`; The Direction Sentence; Eval Pins (Story 1)] — from technical-spec.md
- **Contract:** [Hardest Constraint (ratchet on `verify-spec.md`), ⚠️ Technical Concerns, 💡 Recommendations (write the sentence once, reuse verbatim)] — from spec.md → Specification Contract; [Detailed Requirements → `commands/verify-spec.md`, `commands/verify-spec.lean.md`, `commands/plan-product.md`] — from spec.md

---

## What Was Built

**Implementation Date:** 2026-10-02

### Files Created

None.

### Files Modified

- **`commands/verify-spec.md`** (description, `--product` Modes row, callout, Product Consistency Boundary, Integration row)
  - The direction sentence replaces the before/after framing and the `/assess-spec` analogy; 35858 -> 35778 bytes.
- **`commands/verify-spec.lean.md`** (description, Modes row, callout, Product Consistency intro)
  - Same wording as the default; every section heading unchanged.
- **`commands/plan-product.md`** (Reconcile Boundary, Step R4 closing)
  - Boundary carries the direction sentence; Step R4 suggests `/create-spec` for the next roadmap item and keeps the roadmap-revision note. `verify-spec --product` now appears only in Step R2.
- **`scripts/eval.sh`** (`check_product_check_direction`, registered as `product-check-direction`)
  - `require_literal` the direction sentence in all three files; `forbid_literal` three old phrasings in both verify-spec files and the R4 "to confirm" suggestion in `plan-product.md`.
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET`)
  - `verify-spec.md` 10898 -> 10818 with a dated comment (DEV-002).
- **`scripts/tests/test_lean_commands.py`** (`DEFAULT_SHA256`)
  - `verify-spec` hash re-pinned with a dated comment (DEV-003).

### Implementation Decisions

1. **Re-pin the ratchet down rather than pad the file** — the exact `total_overage` assertion made "unchanged" and "smaller" incompatible; padding 80 bytes of prose to keep a number would fight the constraint it serves.
2. **Pin the lean twin's real old wording** — review found the specified forbid pins could never match `lints (before a decision)`, so `lints (before` was added.

### Test Results

**Verification:** Automated
- ✅ `bash scripts/eval.sh --check=product-check-direction` red before the edits (6 findings), green after
- ✅ Each of the 10 pins proven by one mutation (Findings: 1 each), then reverted
- ✅ `uv run pytest`: 2265 passed, 2 skipped
- ✅ `bash scripts/eval.sh`: Findings 0, Run errors 0; bash suite all pass

**Coverage:** N/A (markdown and shell pins; `test-integrity.py coverage` unverifiable, no coverage report)

### Review Outcome

- **Gate 3:** `review-agent` PASS. Review panel: GPT FAIL on AC-1.5 (the re-pin), Grok PASS, Gemini PASS; `tally` advisory, 0 consensus findings.
- **Iteration count:** 1
- **Drift:** Medium overall (DEV-001, DEV-003–DEV-005 Small; DEV-002 Medium) — see [`drift-log.md`](../drift-log.md)
