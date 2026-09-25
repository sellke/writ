# Story 3: Spill to file

> **Status:** Completed ✅ (2026-09-25)
> **Commit:** b0c4138b28694befb9116917a13fa2d41cc92732
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer
**I want to** spill over-budget story-context (and the lean What Was Built path) to a gitignored file under `.writ/state/` when `WRIT_HARNESS_LEAN=1`, instead of silently discarding the truncated body
**So that** flag-on baseline runs keep the full text on disk with path, size, and a short tail in the payload, while flag-off behavior and existing `enforce_budget` tests stay unchanged

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [x] Given `WRIT_HARNESS_LEAN=1` and assembled story-context bytes strictly exceeding `FETCHED_CONTEXT_BUDGET_BYTES`, when `scripts/story-context.py` returns its payload, then the full pre-truncation text is written to `.writ/state/story-context-spill-<story-id>.md`, `truncated` is true, and the payload includes `spill.path`, `spill.bytes`, and a `fetched_context` tail of at most 500 bytes for the cut category `[AC-3.1]`
- [x] Given `WRIT_HARNESS_LEAN` unset (or any non-`1` value treated as unset), when story-context exceeds the budget, then `enforce_budget` truncates as today, the payload has no `spill` field, no spill file is written under `.writ/state/`, and existing tests in `scripts/tests/test_story_context.py` still pass without the variable set `[AC-3.2]`
- [x] Given `WRIT_HARNESS_LEAN=1`, over-budget context, and a non-writable `.writ/state/`, when assemble runs, then a warning names the error and states the spill was not written, the inline payload is the current truncated form, and no spill file appears `[AC-3.3]`
- [x] Given the default `skills/dependency-context-loading/SKILL.md` truncate-by-priority wording for a “What Was Built” record over 1,000 lines, when this story lands, then that default skill text is unchanged; the lean `commands/implement-story.lean.md` path (named here, authored in Story 4) is the contract surface that points at spill instead of truncate `[AC-3.4]`

## Implementation Tasks

- [x] 3.1 Write failing tests in `scripts/tests/test_story_context.py` for flag-on over-budget spill (path, bytes, ≤500-byte tail, `truncated`), flag-unset no-spill regression against current `enforce_budget` behavior, and read-only `.writ/state/` rescue `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.2 Gate spill on `WRIT_HARNESS_LEAN=1` inside `scripts/story-context.py` (alongside the Story 1 flag reader): when over budget, write `.writ/state/story-context-spill-<story-id>.md` with the pre-truncation text before applying the inline cut `[AC-3.1]`
- [x] 3.3 Shape the over-budget payload so `truncated` stays true and `spill.path` / `spill.bytes` plus a ≤500-byte `fetched_context` tail are present only when a spill file was written `[AC-3.1]`
- [x] 3.4 On spill write failure (non-writable `.writ/state/`), keep today’s truncated inline payload, append a warning that names the error and says the spill was not written, and omit `spill` `[AC-3.3]`
- [x] 3.5 Confirm `skills/dependency-context-loading/SKILL.md` is byte-identical on the 1,000-line truncate rule, and record in Notes/What Was Built that `commands/implement-story.lean.md` (Story 4) is the lean surface that points at spill for oversized What Was Built records `[AC-3.4]`
- [x] 3.6 Verify all acceptance criteria: flag-on spill tests green, `WRIT_HARNESS_LEAN` unset leaves `scripts/tests/test_story_context.py` green with no spill artifacts, read-only state-dir case warns without writing, default skill truncate wording untouched `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

**Technical considerations.** Spill is additive and flag-gated: unset continues through `enforce_budget` alone. The spill filename is `.writ/state/story-context-spill-<story-id>.md` so it stays gitignored with the rest of `.writ/state/`. `truncated` remains the signal that the inline body is incomplete whether or not a spill file exists. Tail length is a hard ceiling of 500 bytes, not a soft target.

**Risks.** A spill the agent never opens is a quality risk; this story does not prove agents read it — Story 5’s baseline catches that. Accidentally writing spill files when the flag is unset would break existing truncate tests and the byte-identical default contract from Story 1. A partial write that leaves an empty or truncated spill file while claiming success would lie about `spill.bytes`.

**Integration.** Depends on Story 1’s `WRIT_HARNESS_LEAN` reader semantics (treat non-`1` as unset with one warning). Story 4 authors `commands/implement-story.lean.md` and is where the What Was Built spill pointer lands in lean command prose; this story only freezes the default skill truncate wording and names that lean path as the contract surface. Story 5 exercises flag-on spill during the 8-run baseline.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Spill over-budget context]
- **Shadow paths:** [Flag off assemble, Flag on assemble]
- **Business rules:** [Spill, don’t truncate, only when the flag is on (rule 4)]
- **Experience:** [State catalog → Flag set, over budget; State catalog → Flag unset]

---

## What Was Built

**Implementation Date:** 2026-09-25

### Files Created

[None created]

### Files Modified

- **`scripts/story-context.py`** (`_payload`, `assemble`, CLI, new `_harness_lean`, `_spill`, `_tail_cut_category`)
  - Constants `LEAN_ENV`, `DEFAULT_STATE_DIR`, `SPILL_TAIL_BYTES = 500`; spill and rescue handling in `_payload`; `state_dir` parameter and `--state-dir` flag; one docstring line on the flag.
- **`scripts/tests/test_story_context.py`** (14 new tests; pre-existing classes rebased)
  - `FlagClearedTestCase` base (clears the flag, redirects `DEFAULT_STATE_DIR`) for all 11 pre-existing classes; flag-free env for CLI subprocesses; SpillFlagOn (6), SpillFlagOff (4), SpillRescue (2), DefaultSkillFrozen (1), RealStateDirGuard (1). No pre-existing assertion changed.

### Implementation Decisions

1. **Flag reader copied, not imported** — same semantics as Story 1 (only `1` is on; other values warn once); keeps `story-context.py` self-contained.
2. **Spill only when a budget is passed, the payload is truncated, and the flag is `1`.**
3. **Spill file holds every category's full text** under `## <label>` headings; the first cut category's inline value becomes a UTF-8-safe tail of ≤500 bytes; later cut categories stay dropped.
4. **No success on a partial write** — the size on disk is checked; a short write is unlinked and handled as the rescue path (warning names the error, today's truncated payload, no `spill` key).
5. **What Was Built spill lives in the lean command** — `skills/dependency-context-loading/SKILL.md` is byte-identical (sha pinned); `commands/implement-story.lean.md` (Story 4) is the surface that points at spill.

### Test Results

**Verification:** Automated
- ✅ Red first: 12 of 13 new tests failed before implementation (`state_dir` keyword / `--state-dir` flag missing)
- ✅ `test_story_context.py` — 79 passed with `WRIT_HARNESS_LEAN=1` exported and with it unset
- ✅ No `story-context-spill-*` file in the real `.writ/state/` after either run
- ✅ Flag-unset CLI output byte-identical to the pre-change output (budget 21000 and budget 100)
- ✅ `test-integrity.py coverage` — pass; `scripts/story-context.py` 90% (HEAD 89%)
- ⚠️ `test-integrity.py authenticity` — `test_imports_no_source`, known checker false positive (see Story 1). Not DEGRADED.
- ⚠️ Gate 3 `review-override.py` — `fail` `dangling_reference` for `AC-3.5`, cited only by `scripts/tests/test_docs_check.py` (another spec). Cross-spec collision; evaluator PASS stands.
- Mechanical: drift-format `pass`; docs-check `unverifiable` (`no_public_exports`)

**Coverage:** 90% line coverage on `scripts/story-context.py`

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s) — cycle 1 FAIL (Major: default-path tests not isolated from an exported flag; one wrote a spill file into the real `.writ/state/`), fixed in recode
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** `scripts/story-context.py` and its test file only; default skill untouched.

### Deviations from Spec

- **[DEV-005] Spill filename uses the story file stem** — Severity: Small — Auto-amended
- **[DEV-006] Inline total can exceed the budget by up to 500 bytes under spill** — Severity: Small — Auto-amended
- **[DEV-007] `--state-dir` CLI flag and `state_dir` parameter** — Severity: Small — Auto-amended

### Known content issue (not fixed)

This story's own `## Context for Agents` hints split on commas inside bracket names ("Spill, don’t truncate, …"), so `story-context.py assemble` reports five missing-content warnings for it.
