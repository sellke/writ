# Story 3: The Checker

> **Status:** Completed ✅ (2026-08-12)
> **Commit:** 2333e8673963b6e8df1c924202e3f20d17f3d434
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As an** orchestrator deciding whether a run may stop
**I want** a read-only command that returns `met`, `unmet`, or `impossible` with per-criterion evidence
**So that** the decision rests on repository evidence rather than on the model's own account of what it just did

## Acceptance Criteria

- [x] Given `--command implement-phase --state <path>`, when the checker runs, then it emits JSON carrying `verdict`, `command`, and a `criteria[]` array with one entry per classified criterion, each holding `id`, `verdict`, and either `evidence` (on `met`) or `reason` (on `unmet` / `unknown`).
- [x] Given a mix of criterion verdicts, when the rollup runs, then precedence is `impossible` > `unmet` > `met`, a declared `unknown` never blocks, and exit codes are `0` met, `1` unmet, `2` impossible.
- [x] Given a missing, unparseable, or unreadable input — including a predicate raising — when the checker runs, then the result is `impossible` naming the input, never `unknown` and never `unmet`.
- [x] Given a state file written before Story 2, when a criterion's field is absent, then that criterion is `unknown` with reason `record predates exit-criteria instrumentation`, and the overall verdict is not `unmet` on its account.
- [x] Given any of the four `impossible` triggers in `spec.md` — `haltReported` present, unresolved `challenge_required`, a criterion recorded unachievable, or a `reconcile` state/git mismatch — when the checker runs, then the verdict is `impossible` and the reason names which trigger fired.

## Implementation Tasks

- [x] 3.1 Write `scripts/exit-criteria.py` with a `check` subcommand taking `--command`, `--state`, and `--spec`, following the argparse-plus-`cmd_*` shape of `scripts/phase-state.py`
- [x] 3.2 Implement one predicate per criterion the Story 1 classification marked evaluable, each carrying its criterion text as a module constant
- [x] 3.3 Implement the four `impossible` triggers as a pre-pass that short-circuits before any criterion predicate runs
- [x] 3.4 Implement the rollup and exit-code mapping
- [x] 3.5 Delegate to `scripts/phase-state.py` `cmd_progress`, `scripts/spec-status.py`, and `scripts/story-deps.py` rather than re-reading state — `recommend-state.py` is the precedent for importing a shared validator
- [x] 3.6 Write `scripts/tests/test_exit_criteria.py` covering every predicate, the rollup precedence table, and one fixture per `impossible` trigger

## Notes

**Technical considerations:** `cmd_progress` already returns a dict with per-status
spec counts, quarantine branches, closures, and `blockedBy` causes — most of
`implement-phase.c1` is a read of that structure, not new logic. Import it; do not
reimplement. `scripts/recommend-state.py` importing `story_deps.validate_graph` is
the house pattern, and `scripts/eval.sh` asserts that delegation with
`require_literal`, so a fresh copy would be caught anyway.

**Risks:** The rollup is where this story can quietly go wrong. `unknown` not
blocking is correct *only* because Story 1 declared which criteria may be unknown;
if the checker accepts `unknown` from an unclassified criterion, every unimplemented
predicate silently becomes a pass. Validate criterion IDs against the classification
at load time and treat an unrecognized ID as `impossible`.

**Read-only is a contract, not a convention.** No `open(..., 'w')`, no `subprocess`
call that mutates. Git reads are `git branch --list` / `git log` only.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`scripts/exit-criteria.py`** (853 lines)
   - Classification-doc parser (parses `.writ/docs/exit-criteria-classification.md`'s Bucket Table into an id→bucket registry at load time; an id absent from the registry resolves to `impossible`, never `unknown`)
   - 4-trigger `impossible` pre-pass (checked before any criterion predicate runs)
   - 7 predicates: 3 evaluable-now (`implement-phase.c1`, `.c2`, `implement-spec.c2`), 3 needs-run-record (`implement-phase.c3`, `implement-spec.c1`, `.c3`), 1 structurally-unobservable (`implement-phase.c4`, always `unknown`/report-only)
   - Rollup + exit-code mapping (0 met, 1 unmet, 2 impossible)
2. **`scripts/tests/test_exit_criteria.py`** (859 lines, 52 tests)

### Files Modified

[None]

### Implementation Decisions

1. **"merged" (prose) mapped to `"integrated"` (code)** — Gate 0 architecture review caught that the exit-criterion prose says specs reach "merged," but `phase-state.py`'s actual `TERMINAL_SPEC_STATUSES` vocabulary uses `"integrated"`. Predicate checks against the real enum, not the prose string; without this every phase would report `unmet` forever with no visible symptom.
2. **`cmd_progress`/`cmd_reconcile` called via a fabricated `argparse.Namespace`** — both take `args`, not plain parameters; confirmed exact attribute reads (`args.state`, `args.repo`) before calling.
3. **Hyphenated modules imported via `importlib.util.spec_from_file_location`**, matching `recommend-state.py`'s existing shim, applied to all three dependency scripts.
4. **`implement-spec.c1` reads `preflight.storyDepsValidated`/`.at` only** — `story-deps.py validate_graph` is never called to re-derive c1's verdict (re-running it would only prove current validity, not that it ran before dispatch); it's imported solely for `c2`'s empty-batch vacuous-pass guard, with that scoping made visible in the code via a dedicated function and docstring warning.
5. **Dotted string ids** (`"implement-phase.c1"` etc.) used throughout, matching the classification doc and technical-spec.md's CLI Surface example — `spec.md`'s bare-integer worked example is stale and documented as such in a code comment.
6. **Classification-doc parser tested against the real file on disk**, not a fixture copy, so drift between the doc and the code is caught by the suite itself.

### Test Results

**Verification:** `python3 -m unittest scripts.tests.test_exit_criteria scripts.tests.test_phase_state` — 71/71 passing (52 new + 19 pre-existing, unaffected). `bash scripts/eval.sh` — Findings: 0, Run errors: 0.
- ✅ All 7 predicates, full rollup precedence table, all 4 `impossible` triggers plus a negative (resolved-challenge) case
- ✅ Fault injection on a raising predicate → `impossible` naming the exception
- ✅ Pre-Story-2 unknown path for all 3 needs-run-record criteria
- ✅ Read-only contract: no file mtime changes anywhere in the repo across a checker run
- ✅ End-to-end replay against all 3 archived `.writ/state/phase-execution-*.json` files (see Known Limitation below)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** Small — deliberate, disclosed id-format correction (dotted strings over `spec.md`'s stale positional-int example); no undisclosed scope change.
- **Security:** Clean — no writes anywhere in the module (empirically verified via grep + mtime diff), all git invocations read-only and argv-based (no shell injection surface).

### Deviations from Spec

None in the implementation itself. One **disclosed, evidence-backed limitation** surfaced by the end-to-end replay, not a code defect:

- **[DEV-KNOWN-1] `.writ/state/phase-execution-20260812-0200.json` (Phase 10, PARTIALLY COMPLETE) replays to `unmet`, not the `impossible` spec.md's Success Criterion 2 names.** This archived file predates Story 2's instrumentation entirely (no `exitCriteria[]`/`haltReported`/`terminalStatus`), so none of the 4 `impossible` triggers can fire on it — confirmed this is inherent, not a bug: Story 2's file ownership is additive/forward-looking (Business Rule 2) and never included backfilling historical `.writ/state/*.json` artifacts. Separately, criterion `implement-phase.c2` (uat-plan.md presence, evaluable-now — no dependency on Story 2 fields) genuinely fails: `.writ/specs/archive/2026-08-12-governor-enforcement/` really has no `uat-plan.md` file (confirmed via direct filesystem check). Gate 3 review independently confirmed this is a real tension between two of `spec.md`'s own rules (Business Rule 2 vs. Success Criterion 2) rather than an implementation defect, and recommended one of: (a) rescope Success Criterion 2's wording to a post-Story-2 fixture (the unit suite already demonstrates the trigger working correctly whenever the field is present), or (b) a deliberate, disclosed one-time retroactive edit to the archived file if the historical unachievable criterion can be truthfully reconstructed. Left unresolved here — flagged for the spec owner at Story 4 or spec-level `/verify-spec`; not fixed by rewriting the criterion or the checker, per Business Rule 5.
- **[DEV-KNOWN-2] (non-blocking, informational)** The two older archived phase files (phase 9, phase 10-component-contract) both correctly replay to `impossible` because their phase branches have since been deleted by normal git housekeeping, tripping `reconcile`'s branch-existence check — the 4th trigger working as specified. Means any sufficiently old archived phase whose branch was cleaned up post-merge reads `impossible` regardless of actual outcome; worth a note for whoever owns long-term archival semantics of `reconcile`, out of this story's file scope.
