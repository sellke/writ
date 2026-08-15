# Story 1: ID Grammar and Emitter

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None
> **Commit:** 08612c2650b926aaad4ab24327021946b36d215b

## User Story

**As a** maintainer authoring a spec whose criteria a checker will later verify
**I want** one written grammar for criterion IDs, and `/create-spec` emitting it by default
**So that** the checker implements a recorded contract rather than re-deriving one, and every
new spec is addressable below story granularity without anyone remembering to opt in

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.4

- [x] Given `.writ/docs/acceptance-criteria-ids.md`, when it is read, then it specifies the ID form, the high-water-mark rule, all seven finding codes with their severities, and the test-shaped path patterns — precisely enough that Story 2 implements it without deciding anything new. `[AC-1.1]`
- [x] Given a story file produced by `agents/user-story-generator.md` after this change, when it is inspected, then every criterion carries a trailing `` `[AC-N.M]` `` tag, the marker equals the highest ID present, and every criterion ID is cited by at least one implementation task. `[AC-1.2]`
- [x] Given a criterion line carrying a trailing tag, when `recommend-state.py`'s two anchored regexes are run against it directly, then both still match — suffix non-breakage is demonstrated, not assumed. `[AC-1.3]`
- [x] Given `spec-lite.md` generation in `/create-spec` Step 2.4, when the Review-agent section's acceptance criteria are written, then each cites its criterion ID so the condensed context is addressable too. `[AC-1.4]`

## Implementation Tasks

- [x] 1.1 Write a regex-level check that a trailing-tag criterion line matches both `recommend-state.py` patterns (`^- \[([ xX])\] Given ` at line 378 and `(?m)^- \[x\] (Given .+)$` at line 2981) — do this first; if it fails, the whole placement decision is wrong and the spec must stop `[AC-1.3]`
- [x] 1.2 Write `.writ/docs/acceptance-criteria-ids.md`: ID form, marker rule and worked insert/delete example, the seven finding codes with severity and reasoning, test-shaped path patterns, marker-exclusion requirement `[AC-1.1]`
- [x] 1.3 Update `agents/user-story-generator.md` prompt template — emit the marker line, criterion tags, and task tags; add the "every criterion cited by ≥1 task" rule to its `exit_criteria` `[AC-1.2]`
- [x] 1.4 Update `commands/create-spec.md` Step 2.6 story contract and Step 2.4 `spec-lite.md` format to carry criterion IDs `[AC-1.2, AC-1.4]`
- [x] 1.5 Point `.writ/docs/spec-format.md` at the new grammar doc `[AC-1.1]`
- [x] 1.6 Verify acceptance criteria are met — generate one throwaway story through the updated emitter and confirm the shape by inspection `[AC-1.2, AC-1.4]`
- [x] 1.7 Verify all tests pass (`scripts/tests/`, and the regex check from 1.1) `[AC-1.3]`

## Notes

**Technical considerations:** This story produces a *docs* deliverable that functions as a
*specification* for Story 2 — the same relationship `.writ/docs/exit-criteria-classification.md`
has to `scripts/exit-criteria.py`. The finding codes and severities chosen here become the
strings the checker emits, so they are decided here and not renumbered or renamed later.

**Risks:** Task 1.1 is ordered first deliberately. Suffix placement is the load-bearing
assumption of the entire spec — it is what keeps `recommend-state.py` and its two eval
fixture sets out of scope. If the regexes do not in fact tolerate a trailing tag, the correct
response is to stop and re-contract, not to quietly move the tag to a prefix and absorb three
extra files.

**Why the emitter and the grammar are one story:** a grammar with no emitter is a document
nobody follows, and an emitter with no written grammar is a convention that drifts the first
time two people edit it. Splitting them would produce a story whose only deliverable is prose.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** Finding vocabulary and severity reasoning (all seven codes) — from
  spec.md → ## 📋 Business Rules; suffix-placement rationale and the two regex sites — from
  spec.md → ## 📐 The Grammar → ### Why suffix placement
- **Experience:** Marker exclusion requirement (a marker must not satisfy its own ID) — from
  spec.md → ## Implementation Approach → ### Marker exclusion
- **Precedent to mirror:** `.writ/docs/exit-criteria-classification.md` — a doc that
  specifies a checker criterion by criterion; `scripts/exit-criteria.py`'s `CRITERION_TEXT`
  block for how verbatim text is bound to a dotted ID

---

## What Was Built

**Implementation Date:** 2026-08-13

### Files Created

1. **`.writ/docs/acceptance-criteria-ids.md`** (259 lines)
   - The grammar doc: ID form (`AC-<story>.<n>` trailing tag), the end-anchored `TAG` reference
     regex, definition/citation/prose-mention/cross-story rules, the high-water-mark rule with
     worked insert *and* delete examples, all seven finding codes with severity and reasoning,
     test-shaped path patterns, scan bounds, and legacy/archive posture. Structured to mirror
     `.writ/docs/exit-criteria-classification.md`'s relationship to its checker.
2. **`scripts/tests/test_recommend_state_ac_tag_compat.py`** (43 lines)
   - Regression guard for task 1.1: pins that a trailing `[AC-N.M]` tag matches both of
     `recommend-state.py`'s anchored regexes (line 378, line 2981) unchanged, and that a
     *prefixed* ID would break the first — so the suffix-placement decision stays verified by
     the suite, not resting on a one-time manual check. Added after review flagged the original
     verification as prose-only with no persisted check.

### Files Modified

- **`agents/user-story-generator.md`**
  - Prompt template now emits the `> **AC IDs assigned through:** AC-{story_number}.N` marker
    beneath `## Acceptance Criteria`, a trailing `[AC-N.M]` tag on every criterion line, and a
    trailing `[AC-N.M, ...]` tag on every task line citing the criteria it satisfies. Added an
    `exit_criteria` entry requiring full tag/marker/citation coverage. Existing 3-5 AC / 5-7
    task count bounds left untouched.
- **`commands/create-spec.md`**
  - Step 2.6: added a note requiring the marker/tags per the new grammar doc (pointing at the
    literal template in `agents/user-story-generator.md`, not duplicating it).
  - New **Step 2.6b** (between 2.6 and 2.7): closes the sequencing gap where Step 2.4 writes
    `spec-lite.md`'s Review-agent acceptance-criteria bullets *before* Step 2.6 generates the
    story files that assign per-story AC IDs. Step 2.6b reads the generated stories' criteria
    and appends matching `[AC-N.M]` tags onto the already-written spec-lite.md bullets, with an
    explicit "leave untagged rather than guess" escape hatch.
- **`.writ/docs/spec-format.md`**
  - Added a one-line pointer to the new grammar doc; no duplication of its content.
- **`scripts/tests/test_governor_enforcement.py`**
  - `KNOWN_OVER_BUDGET["commands/create-spec.md"]` updated 21463 → 24036 bytes with a dated
    disclosure comment, following that file's own established precedent for recording
    deliberate, disclosed byte-budget increases. Required because the Step 2.6/2.6b edits
    pushed the file further over its pre-existing recorded overage.

### Implementation Decisions

1. **Step 2.6b as a new step, not a Step 2.4 rewrite** — spec-lite.md's Review-agent criteria
   are written before story-level AC IDs exist (Step 2.4 precedes Step 2.5/2.6). Reordering the
   whole flow was rejected in favor of a small, explicitly-documented patch step immediately
   after Step 2.6, so the sequencing rationale is recorded rather than implied.
2. **Content-matching, not ID pre-assignment** — Step 2.6b matches spec-lite.md's existing
   condensed bullets to story criteria by content after the fact, rather than having the
   orchestrator pre-assign ordinals before Step 2.6's subagents run. Keeps the per-story ordinal
   decision inside the story-generation step that already owns it.
3. **Persisted regression test added post-review** — the reviewer flagged that task 1.1's
   suffix-safety claim was demonstrated only as a prose assertion with no surviving check. Added
   `test_recommend_state_ac_tag_compat.py` rather than leaving the verification one-time.

### Test Results

**Verification:** `python3 -m pytest scripts/tests/ -q`
**Coverage:** N/A — docs/prompt-template story; the one new test file covers its own regex
assertions at 100%, no application code was added.
- ✅ 468/468 passing (464 pre-existing + 4 new in `test_recommend_state_ac_tag_compat.py`)
- ✅ Task 1.1's regex check re-run directly and confirmed: trailing tag matches both
  `recommend-state.py` anchored patterns unchanged; a prefixed ID would break the first
- ✅ Task 1.6 hand-simulation of the updated template (3 criteria / 5 tasks, throwaway story
  number, not committed) produced the correct marker/tag/citation shape

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** Small (see Deviations)
- **Security:** Clean — docs/prompt-template + one numeric-constant test update; no code
  execution path, no auth/secrets surface touched
- **Boundary Compliance:** 3 of 4 declared Owned files touched as expected; one file outside
  the Owned list (`test_governor_enforcement.py`) touched as a disclosed, precedented,
  arithmetically-verified byte-count correction forced by a pre-existing regression gate, not
  scope creep

### Deviations from Spec

- **[DEV-1] Step 2.6b addition to `create-spec.md`** — Severity: Small
  - Spec said: "carry criterion IDs into spec-lite.md's Review-agent acceptance criteria" (Task
    1.4), without specifying the mechanism.
  - Reality: added a new step between Step 2.6 and 2.7, since the existing step order made the
    literal Task 1.4 instruction impossible to satisfy at Step 2.4 time.
  - Resolution: accepted as the correct closure of a real sequencing gap; documented inline in
    `create-spec.md` with rationale so it isn't relitigated.
- **[DEV-2] `scripts/tests/test_governor_enforcement.py` edit (outside declared Owned scope)**
  — Severity: Small
  - Spec said: Owned files were `.writ/docs/acceptance-criteria-ids.md`,
    `agents/user-story-generator.md`, `commands/create-spec.md`, `.writ/docs/spec-format.md`.
  - Reality: `create-spec.md`'s Step 2.6/2.6b edits pushed it further past its already-recorded
    byte-budget overage, tripping an existing regression gate unrelated to this story's intent.
  - Resolution: updated the recorded overage with a dated disclosure comment, following that
    file's own established pattern for prior disclosed increases. Reviewer independently
    verified the byte arithmetic exactly matches (old: 46423 - 24960 = 21463; new: 48996 - 24960
    = 24036).
