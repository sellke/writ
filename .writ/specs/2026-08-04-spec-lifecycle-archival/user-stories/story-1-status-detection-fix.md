# Story 1: Status Detection Fix

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None
> **Commit:** d18c45d77264132503ef7e0ba22a2507b44856a0

## User Story

**As a** Writ maintainer running `/status` or `/create-spec`
**I want to** format-tolerant spec-status detection that recognizes bold and unbold headers and all complete-family values
**So that** active-spec discovery and cross-spec overlap checks correctly classify every spec in the corpus — unblocking the archive lifecycle and every downstream story in this spec

## Acceptance Criteria

- [x] Given a `spec.md` whose header is `> **Status:** Complete` (19 specs in this repo), when the format-tolerant complete check runs, then the spec resolves as **complete-family** (not surfaced as the active spec by `/status`'s mtime scan, and skipped by `create-spec`'s Step 1.3b overlap filter).
- [x] Given a `spec.md` whose header is any of the other complete-family variants — `> **Status:** Completed ✅` (8 specs), `> Status: Complete` (8 specs, unbold), or `> Status: Closed — Abandoned...` (1 spec) — when the check runs, then each resolves as **complete-family** using the same logic as the bold-`Complete` case.
- [x] Given a `spec.md` with **no status header at all** (3 specs in this repo), when the check runs, then the spec resolves as **not complete** (conservative default — it must not be silently treated as done, even if content suggests completion).
- [x] Given the broken bash at `commands/status.md` lines 333–336 (`grep -q "Status: Complete"`), when replaced with the format-tolerant check (shared with or equivalent to the test suite), then an mtime-sorted scan of all 39 real `.writ/specs/*/spec.md` files matches the audit table in `spec.md` → `## Why This Exists` — 27 previously misclassified bold-header specs now correctly excluded from "active."
- [x] Given `commands/create-spec.md` Step 1.3b prose (~line 390, "skip specs with `Status: Complete`") and Phase 2 Step 2.4 spec.md template (~lines 560–563), when updated, then Step 1.3b instructs the same format-tolerant complete-family filter (not the literal substring), and the template documents canonical new-spec status as `> **Status:** Complete` for the complete state (with `Not Started` / in-progress values unchanged) so drift does not reaccumulate — without rewriting any of the 39 existing spec files.

## Implementation Tasks

- [x] 1.1 Write failing unit tests in `scripts/tests/test_spec_status.py` with fixtures covering all five real-world header variants from the audit table (`> **Status:** Complete`, `> **Status:** Completed ✅`, `> Status: Complete`, `> Status: Closed — Abandoned...`, and absent header), plus at least one explicit **not-complete** case (e.g. `> **Status:** Not Started`), asserting complete vs not-complete resolution for each.
- [x] 1.2 Implement a shared, testable complete-family detector — prefer `scripts/spec-status.py` with a `is-complete --file <path>` (or equivalent) CLI following the `spec-deps.py` / `story-deps.py` precedent — that tolerates bold (`**Status:**`) and unbold (`Status:`) labels and matches `Complete`, `Completed ✅`, and `Closed — Abandoned` as complete-family values while returning not-complete when no status header is present.
- [x] 1.3 Replace the broken bash snippet in `commands/status.md` lines 333–336: remove `grep -q "Status: Complete"` and invoke the shared detector (or an equivalent format-tolerant bash one-liner documented to stay in sync with the script's contract) so the "most recently modified non-complete spec" scan uses correct classification.
- [x] 1.4 Rewrite `commands/create-spec.md` Step 1.3b (~line 390): replace "skip specs with `Status: Complete`" with prose that mirrors the format-tolerant complete-family rules (bold/unbold label, three complete-family values, conservative default on missing header) and references the same detector or equivalent logic as `status.md`.
- [x] 1.5 Update `commands/create-spec.md` Phase 2 Step 2.4 spec.md template (~lines 560–563): document the canonical status vocabulary for newly generated specs — complete state uses `> **Status:** Complete` (bold header, no emoji suffix); note that detection remains tolerant of legacy spellings in existing files per Business Rule 8.
- [x] 1.6 Add an `eval.sh` check (e.g. `spec-status`) with scenario fixtures and literal assertions that `commands/status.md` and `commands/create-spec.md` no longer contain the bare `grep -q "Status: Complete"` pattern or equivalent literal-only substring filter.
- [x] 1.7 Run `python3 -m pytest scripts/tests/test_spec_status.py`, the new eval scenarios, and a dogfood pass classifying all 39 real `.writ/specs/*/spec.md` files against the audit table in `spec.md` → `## Why This Exists`; confirm both call sites behave consistently before marking this story complete.

## Notes

**Instruction-based logic, not a compiled app.** "Fixing" this story means rewriting bash snippets and command prose in `commands/status.md` and `commands/create-spec.md` — there is no runtime binary today. A shared `scripts/spec-status.py` (recommended) gives the deterministic, testable contract Writ's other validators use; if inline bash is chosen instead, the eval check must enforce parity with the test fixtures so the two call sites cannot drift.

**Conservative default is intentional.** The three headerless specs are content-complete but must remain **not complete** for machine purposes until a human adds a status header. This aligns with `spec.md` → `## Technical Concerns` and prevents silent archival in downstream stories.

**No mass rewrite.** Business Rule 8: existing files keep `Complete`, `Completed ✅`, bold/unbold — only detection changes. Template canonicalization applies to **new** specs from `create-spec` only.

**Blocks everything else.** Stories 2–6 (archive sweep, documentation, indexing ignore, supersession banners, dogfood run) all depend on trustworthy Complete/non-Complete classification. Ship this first.

**Risks:**

- Inline bash regex in two command files can drift from a shared script unless `eval.sh` guards both call sites.
- `Closed — Abandoned` matching must be prefix/substring-safe (full abandoned-family value, not accidental `Closed` elsewhere in the file body).
- Agent executing `/status` or `/create-spec` may skip the documented detector invocation (same accepted weakness as other Writ script gates).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** [Header format audit table (bold vs unbold misclassification), Missing status header (conservative not-complete default)]
- **Business rules:** [Status vocabulary detection becomes format-tolerant, not rewritten, verify-spec --all excludes archive/ by default]
- **Experience:** []

---

## What Was Built

**Implementation Date:** 2026-08-04

### Files Created

1. **`scripts/spec-status.py`** (~140 lines)
   - Shared format-tolerant complete-family detector, following the `spec-deps.py` CLI precedent. `is-complete --file PATH` classifies one spec; `scan --specs-dir DIR` classifies every spec under a single-level `DIR/*/spec.md` glob (the archive-exclusion mechanism, Business Rule 5). Scans only the leading `>`-blockquote header block (capped at 15 lines) so a stray "Complete" mention in a document body can never false-positive.
2. **`scripts/tests/test_spec_status.py`** (10 tests)
   - Fixtures for all 5 real-world header variants (bold `Complete`, bold `Completed ✅`, unbold `Complete`, unbold `Closed — Abandoned`, absent header) plus explicit not-complete, body-false-positive, missing-file, and glob-exclusion cases.
3. **`scripts/eval-spec-status.py`** (11 scenarios)
   - Eval fixture scenarios wired into `scripts/eval.sh`'s new `spec-status` check.

### Files Modified

- **`commands/status.md`** — Replaced the broken `grep -q "Status: Complete"` (lines 333–336) with an invocation of `scripts/spec-status.py is-complete`; updated the Step 3 prose to describe format-tolerant complete-family resolution instead of the literal substring.
- **`commands/create-spec.md`** — Step 1.3b now instructs the format-tolerant complete-family filter (bold/unbold label, three complete-family values, conservative missing-header default) instead of "skip specs with `Status: Complete`"; Phase 2 Step 2.4 template gained a canonical-spelling note (`> **Status:** Complete`, bold, no emoji) for newly-marked-complete specs, forward-only per Business Rule 8.
- **`scripts/eval.sh`** — Registered the `spec-status` check (CHECKS array + `check_spec_status()`), asserting the eval scenarios pass and that neither call site retains the literal substring pattern.

### Implementation Decisions

1. **Header-block scan, not whole-file grep** — `spec-status.py` only reads the first 15 lines and stops at the first `##` heading, so a false-positive substring match deep in a spec's body (e.g. "...will be marked Status: Complete once shipped") can never leak into classification. Covered by an explicit regression test.
2. **Prefix matching, not full-value enumeration** — `value.startswith(("Complete", "Closed"))` covers `Complete`, `Completed ✅`, and `Closed — Abandoned` with two prefixes instead of enumerating every trailing-text variant, matching the reference regex shape in `sub-specs/technical-spec.md`.
3. **JSON CLI contract, not plain exit-code grep** — mirrors `spec-deps.py`/`story-deps.py` precedent so both `is-complete` and `scan` are independently testable and reusable by Story 2's archive-sweep mechanism.

### Test Results

**Verification:** `python3 -m pytest scripts/tests/test_spec_status.py` + `python3 scripts/eval-spec-status.py` + real-corpus dogfood scan
**Coverage:** 100% of the 5 documented header-format variants; error paths (missing file, missing dir) both covered
- ✅ 10/10 pytest fixtures passing
- ✅ 11/11 eval scenarios passing
- ✅ Dogfood scan of all 40 real `.writ/specs/*/spec.md` files (39 pre-existing + this spec's own in-flight folder): all 39 pre-existing specs correctly resolve to complete-family regardless of bold/unbold or emoji-suffix formatting; this spec's own `Not Started` header correctly resolves not-complete
- ✅ `bash scripts/eval.sh --check=spec-status` — PASS, 0 findings
- ✅ Confirmed no regression: `bash scripts/eval.sh --check=spec-dependencies` still passes (13/13 scenarios)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean — read-only classification helper, no file mutation, no shell injection surface (subprocess argv list, no string interpolation into shell)

### Deviations from Spec

None
