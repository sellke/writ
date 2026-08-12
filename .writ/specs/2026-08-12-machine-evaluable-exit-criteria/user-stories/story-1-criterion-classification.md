# Story 1: Criterion Classification

> **Status:** Completed ✅ (2026-08-12)
> **Commit:** 48d73f52c8abd64ddbd832cd648e0026c4891b6d
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer about to build a stop-time gate
**I want** every exit criterion of the three implement commands sorted into evaluable-now, needs-run-record, or structurally-unobservable, each with the evidence for the call
**So that** the checker implements a recorded classification rather than whatever its author found convenient to check

## Acceptance Criteria

- [x] Given the 10 `exit_criteria` across `commands/implement-phase.md` (4), `commands/implement-spec.md` (3), and `commands/implement-story.md` (3), when the classification is written, then each criterion appears exactly once under exactly one of the three buckets with its verbatim text and the evidence for its bucket.
- [x] Given a criterion placed in **structurally-unobservable**, when the entry is written, then it names *why* it cannot be observed post-hoc — temporal, before/after, report-only, or interaction — and that reason is the string the checker will later return as `unknown`'s reason.
- [x] Given `/implement-story` is out of scope, when its three criteria are classified, then each carries a `Scope: excluded` marker and the entry records the four reasons from `spec.md` § Excluded rather than silently omitting the command.
- [x] Given the classification is complete, when `.writ/docs/exit-criteria-classification.md` is read, then every criterion in the needs-run-record bucket names the exact field Story 2 must add and the file it lands in.

## Implementation Tasks

- [x] 1.1 Extract the 10 criteria verbatim from the three command frontmatter blocks — do not paraphrase; the text is the contract Story 3 binds against
- [x] 1.2 Classify `implement-phase` c1–c4 against `.writ/state/phase-execution-*.json`, spec folders, and git
- [x] 1.3 Classify `implement-spec` c1–c3, noting c1's temporal clause ("before the first story ran") and c3's post-batch clause
- [x] 1.4 Classify `implement-story` c1–c3 as `Scope: excluded`, recording the `## What Was Built` best-effort conflict
- [x] 1.5 Write `.writ/docs/exit-criteria-classification.md` with a bucket table plus one entry per criterion
- [x] 1.6 Cross-check the needs-run-record bucket against Story 2's field list — a gap in either direction is a defect in this story

## Notes

**Technical considerations:** The classification is a *docs* deliverable that
functions as a *specification* for Story 3. Its identifiers (`implement-phase.c1`
and so on) become the `id` values in the checker's JSON output, so pick them here
and do not renumber later.

**Risks:** The temptation is to classify a hard criterion as evaluable because a
partial predicate exists. Resist it — a predicate that checks 60% of a criterion
and reports `met` is worse than one that reports `unknown`, because it launders a
gap into a pass. When a criterion splits, record it as split rather than rounding.

**Why this is a story and not planning:** it produces a durable artifact that
outlives this spec, and it is the only place the unobservable set is written down.
Without it that set exists only as absence, which is exactly how it stayed
invisible until now.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`.writ/docs/exit-criteria-classification.md`** (345 lines)
   - Bucket table plus one full entry per criterion for all 10 `exit_criteria`
     across `implement-phase` (4), `implement-spec` (3), and `implement-story`
     (3, all excluded)
   - Bucket counts: evaluable-now 3, needs-run-record 3,
     structurally-unobservable 1, excluded 3

### Files Modified

[None]

### Implementation Decisions

1. **`implement-phase.c4` classified structurally-unobservable (report-only), not needs-run-record** — Gate 0 architecture review caught that both `spec.md` § Verdict Contract and `technical-spec.md` § CLI Surface already show this exact criterion returning `{"verdict": "unknown", "reason": "declared unobservable: report is transcript-only"}`. `terminalStatus` exists to support rollup/`impossible`-trigger logic, not to directly evidence c4.
2. **`implement-phase.c2` recorded as a split entry** — bundles a presence check (evaluable-now, trivial file read) with an ordering claim ("generated after"), resolved via git-log timestamp comparison rather than rounded to just the presence half.

### Test Results

**Verification:** N/A — documentation-only deliverable, no executable code touched.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** Small (one imprecise closing sentence, corrected inline post-review; no contract deviation)
- **Security:** Clean

### Deviations from Spec

None.
