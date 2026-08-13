# Story 5: Command Wiring

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** Medium
> **Dependencies:** Story 3

## User Story

**As a** maintainer reading a completion report
**I want** the checker's verdict to appear in the report itself, with its per-criterion evidence
**So that** the honest completion report is backed by an independent read of disk rather than by the same run that produced it

## Acceptance Criteria

- [x] Given `/implement-phase` reaching Step 4.2, when the completion report is produced, then it carries the checker's overall verdict and each criterion's verdict with evidence, and the report's terminal status agrees with `terminalStatus` in phase state.
- [x] Given a checker verdict of `impossible`, when the report is produced, then it names which trigger fired and the phase does **not** report a terminal status — matching the existing `halt_reported` behavior rather than overriding it.
- [x] Given `/implement-spec` reaching its completion step, when the post-batch verification finishes, then the checker runs and its verdict is reported alongside the story counts.
- [x] Given the checker disagrees with the run's own account — for example the run believes it is COMPLETE but a criterion reads `unmet` — when the report is produced, then the **checker's verdict governs** and the disagreement is stated rather than reconciled silently.
- [x] Given both command files, when `bash scripts/eval.sh` runs, then every governor-enforced contract field (`problem`, `outcome`, `exit_criteria`, `loop:`, `## Completion`) is intact and the suite is green.

## Implementation Tasks

- [x] 5.1 Add the checker invocation to `commands/implement-phase.md` Step 4.1c, beside the existing `progress` and `health` calls that already run there
- [x] 5.2 Extend the Step 4.2 report template with the verdict block
- [x] 5.3 Add the checker invocation and verdict reporting to `commands/implement-spec.md`'s completion step
- [x] 5.4 Record the Design Principle 4 rationale in `commands/implement-phase.md` as a one-line pointer to `spec.md` § On Design Principle 4 — the reasoning lives in the spec, not duplicated in the command
- [x] 5.5 State the checker-governs rule explicitly in both commands
- [x] 5.6 Run `bash scripts/eval.sh` and confirm green

## Notes

**Technical considerations:** Step 4.1c of `commands/implement-phase.md` already
runs `phase-state.py progress` and `health` and carries both into the report. The
checker call belongs in the same block and the same report section — a third
evidence source in an established pattern, not a new phase.

**Risks:** Both files carry blocking `structural` governor checks and
`implement-phase.md` is the suite's largest command. Additions must be terse.
Adding a report section is cheap; adding a *step* is not — resist the pull to
create Step 4.4.

**The checker-governs rule (AC 4) is the load-bearing one.** If the run's own
account can override the checker on disagreement, the checker is decoration. State
which wins, in the command file, where a future run will read it.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Code reviewed

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

[None]

### Files Modified

- **`commands/implement-phase.md`** — Step 4.1c now runs `scripts/exit-criteria.py check --command implement-phase ...` alongside the existing `phase-state.py progress`/`health` calls, plus a one-line pointer to `spec.md § On Design Principle 4`. Step 4.2's report template gained a `Checker verdict:` block (overall + per-criterion id/verdict/evidence) and an explicit checker-governs conditional: `impossible` → name the fired trigger, skip `set-terminal-status` entirely; `unmet` → terminal status cannot be `COMPLETE`, disagreement stated explicitly; `met` → run's own determination stands.
- **`commands/implement-spec.md`** — Step 4.1 states explicitly that the checker runs only after `postRun` is written (sequencing rationale in prose). Step 4.2's report template gained the same `Checker verdict:` block, and a conditional gating the `✅ Specification Complete` banner itself — since implement-spec has no `terminalStatus` field to defer to.

### Implementation Decisions

1. **Checker-governs rule implemented as a real conditional, not a report line** — Gate 0 architecture review flagged this as the load-bearing acceptance criterion (AC4) and the easiest one to satisfy in prose while missing in effect. Both files' branches control an actual invocation/output: `implement-phase.md` gates whether `set-terminal-status` is called at all and which status is legal; `implement-spec.md` gates the literal completion-banner string.
2. **Insertion at Step 4.1c, not the literal "Step 4.1"** — Gate 0 review caught that the story's task text named the wrong step; Step 4.1 runs an unrelated per-roadmap-criterion loop. Followed the story's own Notes, which correctly named 4.1c.
3. **No new Step 4.4** — extended the existing evidence block and report template only, per the story's explicit warning against adding a step for cheap additions.

### Test Results

**Verification:** `bash scripts/eval.sh` — Findings: 0, Run errors: 0, both before and after edits. No test runner applies to markdown command files (per `CLAUDE.md`).
- ✅ Frontmatter (`problem`/`outcome`/`exit_criteria`/`loop:`) and literal `## Completion` heading untouched in both files
- ✅ Checker-governs branch verified as real control flow (not decoration) — enumerated conditional in prose, controls whether `set-terminal-status` is called/what status, and the `implement-spec.md` completion banner substitution

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean — markdown-only diff, shell snippet matches the checker's real CLI, read-only, no injection surface.

### Deviations from Spec

None. `implement-phase.md`'s pre-existing, non-blocking byte-budget WARNING grew slightly (ADR-023 permanently demoted this check — not a design constraint at any threshold).
