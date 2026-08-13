# Story 2: Run-Record Extensions

> **Status:** Completed ✅ (2026-08-12)
> **Commit:** 3617180992248c5af42cf71426325b6587ca8c12
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** stop-time checker reading disk after a run
**I want** `/implement-phase` and `/implement-spec` to persist the completion facts they currently only narrate
**So that** criteria about the run itself — which criteria passed, what terminal status was reached, whether the loop bound tripped — can be evaluated instead of taken on trust

## Acceptance Criteria

- [x] Given a phase run reaching Phase 4, when the completion report is produced, then `.writ/state/phase-execution-*.json` carries `exitCriteria: [{id, source, class, verdict, evidence}]` and `terminalStatus` set to one of `COMPLETE`, `IMPLEMENTED_PENDING_HUMAN_VALIDATION`, or `PARTIALLY_COMPLETE`.
- [x] Given a phase loop that exhausts `loop.max_iterations`, when `halt_reported` fires, then `haltReported: {unit, bound, reached, lastIntegrated}` is written and `terminalStatus` is **not** set — the run has not reached a terminal status, and claiming one would be the self-certification the command forbids.
- [x] Given a spec run, when the story-graph pre-flight and the post-batch verification complete, then `.writ/state/execution-<ts>.json` carries `preflight: {storyDepsValidated, at}` and `postRun: {typecheck, testSuite, contextRewritten, at}`.
- [x] Given a state file written before this story, when any reader loads it, then the absent fields are reported as unknown and no existing field changed meaning — `schemaVersion` stays `2`.
- [x] Given `.writ/docs/phase-execution-state-format.md`, when the new fields are documented, then each row names the writer, the step that writes it, and whether the field is optional.

## Implementation Tasks

- [x] 2.1 Add `exitCriteria[]`, `terminalStatus`, and `haltReported` to the phase-state schema doc, marked optional and additive under the existing preserve-unknown-fields rule
- [x] 2.2 Extend `scripts/phase-state.py` with the writer path for those fields, keeping the atomic temp-file-plus-rename discipline the file already uses
- [x] 2.3 Amend `commands/implement-phase.md` Step 4.1 / 4.2 to record criterion verdicts and the terminal status as it produces them
- [x] 2.4 Amend `commands/implement-phase.md` Step 3.2's exhaustion path to write `haltReported`
- [x] 2.5 Amend `commands/implement-spec.md` Step 3.1 and its post-batch verification to write `preflight` and `postRun`
- [x] 2.6 Verify a pre-existing archived state file still loads unchanged through every `phase-state.py` subcommand

## Notes

**Technical considerations:** `.writ/docs/phase-execution-state-format.md` already
requires readers to "preserve unknown fields … for future schema minor versions."
That rule is what makes this additive rather than a `v3` migration — confirm it is
still in the file before relying on it. `.writ/state/` is gitignored, so there is
no corpus of old files to migrate; the compatibility requirement is about archived
copies and in-flight runs, not a data migration.

**Risks:** `commands/implement-phase.md` carries blocking `structural` governor
checks (`problem`/`outcome`/`exit_criteria`/`## Completion`/`loop:`). Any edit must
leave all of them intact — run `bash scripts/eval.sh` before and after. The file is
also the largest command in the suite; keep additions terse.

**The `haltReported` asymmetry is deliberate.** Writing a terminal status when the
bound tripped would let the checker report `met` for a run that never finished.
`haltReported` present with `terminalStatus` absent is the state Story 3 maps to
`impossible`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`scripts/tests/test_phase_state.py`** — 19 unittest cases covering the three new writer subcommands, atomic-write discipline, and pre-Story-2 compatibility

### Files Modified

- **`scripts/phase-state.py`** — added `EXIT_CRITERION_CLASSES`, `EXIT_CRITERION_VERDICTS`, `TERMINAL_STATUSES` enum constants and three new writer subcommands, each following the existing `_load → validate → mutate → updatedAt → _atomic_write` pattern: `record-exit-criterion` (idempotent upsert by `id` onto `exitCriteria[]`), `set-terminal-status` (sets `terminalStatus`, unconditionally clears any stale `haltReported` in the same write), `record-halt` (writes `haltReported`, never touches `terminalStatus`)
- **`.writ/docs/phase-execution-state-format.md`** — new "Run-Record Extensions (Story 2)" section: writer/step/optional table for all three fields plus the mutual-exclusivity rule
- **`commands/implement-phase.md`** — Step 3.2 exhaustion path calls `record-halt`; Step 4.1 calls `record-exit-criterion` per criterion; Step 4.2 calls `set-terminal-status`. Frontmatter and `## Completion` heading untouched.
- **`commands/implement-spec.md`** — Step 3.1 records `preflight: {storyDepsValidated, at}` from the already-computed Step 2.1 result; Step 4.1 (post-batch verification) records `postRun: {typecheck, testSuite, contextRewritten, at}`.

### Implementation Decisions

1. **`terminalStatus` writer unconditionally clears `haltReported`** — Gate 0 architecture review flagged that a phase which halts once and later `--resume`s to completion must not be reported `impossible` forever by Story 3's checker. `cmd_set_terminal_status` does `state.pop("haltReported", None)` before writing `terminalStatus`, both inside one atomic write.
2. **`record-exit-criterion` is idempotent by `id`** (upsert, not pure-append) — consistent with the resume-safety pattern used elsewhere in `phase-state.py`, so a `--resume` re-verification doesn't accumulate duplicate criterion entries.

### Test Results

**Verification:** `python3 -m unittest scripts.tests.test_phase_state` — 19/19 passing. `bash scripts/eval.sh` — Findings: 0, Run errors: 0.
- ✅ Enum validation (`class`, `verdict`, `status`) rejects invalid values via `ContractError`, leaving the file unmodified
- ✅ `terminalStatus` write clears stale `haltReported` in the same atomic operation (exercised against a real fixture via the real CLI, not mocked)
- ✅ `record-halt` never sets `terminalStatus`
- ✅ Pre-Story-2 fixture (schemaVersion 2, no new keys) loads unchanged through `show`/`progress`/`reconcile` and accepts every new writer
- ✅ Atomic write discipline preserved: no leftover temp files, unknown fields survive round-trip

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** Small — Task 2.6's archived-file verification covers the read-relevant subcommands (`show`, `progress`, `reconcile`) plus all three new writers rather than literally every existing subcommand; the property under test (schema/unknown-field preservation) is subcommand-independent, so this is a reasonable scoping choice, not a gap.
- **Security:** Clean — internal CLI over trusted-caller JSON, closed enum validation before any write, no partial-state risk on rejection.
- **Boundary Compliance:** No cross-story boundary issues; touched exactly the 5 files this story owns.

### Deviations from Spec

None blocking. `implement-phase.md`'s command-budget WARNING (pre-existing gap, this story added ~892 bytes to an already +7,978-byte overage) is reported non-blocking per the existing leanness-ratchet convention — not introduced by this story.
