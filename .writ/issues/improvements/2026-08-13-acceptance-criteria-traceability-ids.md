# Per-Criterion Traceability IDs and an Orphan Check

> **Type:** Improvement
> **Priority:** High
> **Effort:** Small
> **Created:** 2026-08-13
> **spec_ref:** .writ/specs/2026-08-13-acceptance-criteria-traceability-ids/spec.md

## TL;DR

Give every acceptance criterion a stable ID and have `/verify-spec` flag orphans — criteria nothing implements or tests, and tests citing criteria that no longer exist.

## Current State

- Acceptance criteria in `user-stories/story-*.md` are anonymous bullets (`- [ ] Given... When... Then...`). Nothing addresses an individual criterion.
- `/verify-spec` Check 3a only counts checkboxes: "all criteria checked?" It cannot tell whether a checked criterion corresponds to anything real.
- Implementation tasks, tests, and commits reference stories at best, never a specific criterion — so a criterion can be silently dropped mid-build while the story still reports Completed ✅.
- The precedent already exists one level up: `scripts/exit-criteria.py` uses dotted IDs (`implement-phase.c1`) bound to verbatim criterion text. Story-level criteria never got the same treatment.

## Expected Outcome

- `/create-spec` emits a stable ID per acceptance criterion (e.g. `AC-3.2` = story 3, criterion 2), assigned once and never renumbered on edit.
- Implementation tasks and their tests cite the criterion IDs they satisfy.
- `/verify-spec` gains an orphan check, reporting both directions:
  - **Uncovered criterion** — an ID no task or test references.
  - **Dangling reference** — a task/test citing an ID that doesn't exist (renamed, deleted, or typo'd).
- Checked-but-uncovered criteria are a completion-integrity failure, not a warning — same class as Check 3a's false completion.

## Relevant Files

- `commands/create-spec.md` - emits the acceptance criteria; ID assignment lands here (see line ~634, ~749)
- `commands/verify-spec.md` - Check 3 Completion Integrity; orphan check lands here (line ~184)
- `scripts/exit-criteria.py` - existing dotted-ID + verbatim-text-binding pattern to mirror

## Related Issues

- [2026-08-12-phase-execution-closed-unimplemented-status](2026-08-12-phase-execution-closed-unimplemented-status.md) - same failure family: a status claiming completion that verification can't contradict

## Notes

- **Why it's the moat:** requirements-to-artifact traceability is the one rigor property competing AI workflow frameworks don't have. Writ already invests in the spec contract; without per-criterion addressing, that contract is unverifiable below story granularity.
- **Evidence:** rationale rests on the one rigorous empirical study in this category — citation to be pinned down and recorded when this is promoted to a spec. Do not build on the claim without it.
- **Keep it small:** IDs plus a bidirectional orphan check. Not a coverage percentage, not a traceability matrix document, not a new command.
- **Main design risk:** ID stability under `/edit-spec`. Inserting a criterion must not renumber its siblings, or every existing reference rots.
