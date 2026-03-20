# Story 9 — `/refresh-command` Batch Analysis

> Status: Completed ✅
> Priority: Low
> Dependencies: Phase B Story 7 (ensures all `status.md` edits are stable before the batch-refresh auto-trigger section lands)

## User Story

As a Writ maintainer, I want `/refresh-command` to support batch analysis over the last N agent transcripts for a command (with cross-session pattern detection and recurrence-weighted amendments) so that the learning loop compounds over time instead of optimizing from a single session in isolation.

## Acceptance Criteria

**Given** `commands/refresh-command.md` after this story
**When** a maintainer reads the CLI / invocation section
**Then** `--batch` mode is documented with an `N` parameter (default **5**) describing how many recent transcripts to include for the target command.

**Given** batch mode is used for a command
**When** the command runs its analysis phases
**Then** it ingests the last **N** transcripts (from the agent-transcripts folder, scoped to that command) and identifies friction (and related) patterns that appear in **two or more** sessions — treating one-off signals as lower priority than recurring ones.

**Given** Phase 3 (or equivalent analysis phase) runs in batch mode
**When** the analysis agent executes
**Then** it receives **all N** selected transcripts plus explicit cross-session context (not a single transcript only), so proposals reflect aggregated evidence.

**Given** batch mode produces amendment proposals
**When** each proposal is written for review or promotion
**Then** it includes recurrence frequency in plain form, e.g. **"Observed in N/M analyzed sessions"** (M = N transcripts actually analyzed, N = sessions where the pattern appeared).

**Given** promotion or confidence evaluation runs after batch analysis
**When** comparing proposed amendments
**Then** patterns with higher recurrence (e.g. **3+ of 5** sessions) are scored or described as **higher confidence** than rare patterns (e.g. **1 of 5** = low confidence); **4 of 5** maps to very high confidence in that scale.

**Given** `commands/status.md` (or documented status behavior) after this story
**When** a command has **three or more** new transcripts since the last documented `/refresh-command` run for that command
**Then** status surfaces a clear suggestion to run batch `/refresh-command` analysis (auto-trigger condition is defined and actionable).

## Implementation Tasks

- [x] Write an AC verification checklist (batch defaults, multi-transcript ingestion, 2+ session threshold, Phase 3 multi-transcript input, recurrence strings, promotion weighting, status auto-trigger) and use it as the test plan for markdown-only changes.
- [x] Update `commands/refresh-command.md` to document `--batch` and `N` (default 5): how transcripts are selected, ordering (most recent), and command scoping from transcript metadata or filenames as already used by the command.
- [x] Specify in `refresh-command.md` that batch mode feeds Phase 3 (analysis) with all N transcripts and a cross-session summary so the agent reasons across sessions, not one log.
- [x] Document cross-session pattern rules: require recurrence across **>=2** sessions for "pattern" status; map frequency to confidence (1/M low, 3+/M high, 4/M very high) and require amendment text to include **"Observed in N/M analyzed sessions."**
- [x] Update promotion-evaluation steps in `refresh-command.md` so high-frequency batch findings weigh more heavily than one-off signals when deciding what to promote.
- [x] Update `commands/status.md` (on top of Stories 4, 5, and 7) to define "new transcripts since last refresh," the **3+** threshold, and the exact user-facing suggestion to run batch `/refresh-command` (including how last refresh is recorded or inferred per the command's existing conventions).
- [x] Walk the verification checklist against `refresh-command.md` and `status.md`; confirm every AC passes and wording is consistent with the rest of the command suite.

## Technical Notes

- Scope is **markdown instruction files only** (no runtime code): behavior is specified for the AI agent executing the commands.
- Agent transcripts live as **`.jsonl`** files under the agent-transcripts folder (path conventions already referenced by `refresh-command.md`); batch mode extends selection from "one transcript" to "last N for this command."
- **Strategic intent:** single-transcript refresh is iterative; batch mode is what makes improvement **compound** by surfacing friction that repeats across sessions rather than noise from a single run.
- **Weighting rule of thumb:** recurrence count / M sessions → confidence; proposals must remain honest when M < N (e.g. missing or skipped files) by using the actual M in the denominator.
- **Story 7 dependency:** `status.md` receives three separate additions across Stories 4, 5, and 7. This story lands after all three are stable to avoid conflicts on the auto-trigger section.

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed

## What Was Built

> Implemented: 2026-03-20
> Files modified: 2 (refresh-command.md, status.md)

Added a `--batch` mode section to `refresh-command.md` documenting: N=5 default, `--n [number]` override, transcript auto-selection (last N most recent), signal frequency mapping across sessions, the 2-of-N recurrence threshold for "pattern" status, cross-session analysis prompt that feeds all N transcripts to Phase 3, recurrence-weighted proposals with mandatory "Observed in N/M analyzed sessions" strings, confidence mapping (1/M=low through 4+/M=very high), and promotion weighting. Updated `status.md` Step 6 to define "last refresh" detection via refresh-log.md, "new transcripts" counting, and to suggest `--batch` specifically when the 3+ threshold is triggered.
