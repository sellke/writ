# Story 5: /retro — Output, Persistence & Trends

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 4 (/retro git analysis & metrics)

## User Story

**As a** developer who has collected git metrics for a period
**I want to** see an opinionated summary with trends, highlights, and persistent snapshots
**So that** I can track my momentum over time and share wins

## Acceptance Criteria

- [x] Given metrics are collected from Story 4, when the output is formatted, then it includes a metrics table with Δ vs Last column showing changes from the previous period
- [x] Given a retro completes, when persistence runs, then a JSON snapshot is saved to `.writ/retros/YYYY-MM-DD.json` with all raw metrics
- [x] Given previous snapshots exist, when `/retro --compare` is run, then it shows side-by-side comparison with the previous period
- [x] Given the period had significant work, when Ship of the Week is selected, then it highlights the most impactful commit/change with hash and description
- [x] Given the retro output is generated, when the tweetable summary is written, then it distills the period into one compelling sentence

## Implementation Tasks

- [x] 5.1 Define the markdown output template — period header, metrics table (with Δ column), Ship of the Week, Patterns, Writ Integration, and Tweetable sections
- [x] 5.2 Implement Ship of the Week selection — heuristic for identifying the most significant change (LOC impact, file breadth, commit message keywords, spec completion)
- [x] 5.3 Implement Patterns section — opinionated observations derived from the data (test ratio trends, session clustering, streak significance, velocity changes)
- [x] 5.4 Define JSON snapshot schema — all metrics, period boundaries, branch, timezone; write to `.writ/retros/YYYY-MM-DD.json`
- [x] 5.5 Implement trend comparison — read previous snapshot, compute deltas for the Δ vs Last column, support `--compare` flag for side-by-side output
- [x] 5.6 Implement trends.json rolling averages — maintain 6-week rolling window of key metrics for long-term trend tracking
- [x] 5.7 Verify complete output matches the spec example, JSON persistence works, and the command embodies Design Principle 6 (opinionated — "Your biggest win was X, your biggest risk is Y")

## Notes

- The Patterns section should be genuinely opinionated, not just restating numbers — "Test ratio hit 0.38, highest in 6 weeks" is better than "Test ratio: 0.38"
- Ship of the Week should highlight effort, not just volume — a tricky 50-line fix can be more significant than 500 lines of boilerplate
- Tweetable summary is a forcing function for distillation, not literally for Twitter — it captures the period's essence in one sentence
- JSON schema should be forward-compatible — include a version field so future retro versions can handle old snapshots

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/retro.md` is complete with both analysis (Story 4) and output (Story 5) sections
- [x] JSON snapshot schema documented
- [x] Trend comparison works with --compare flag
- [x] Output is opinionated and actionable, not just metrics dumps

## What Was Built

**Implemented:** 2026-03-15
**Files:** 0 created, 1 modified (commands/retro.md — added Steps 7-10)

**Key decisions made during implementation:**
- Ship of the Week heuristic prioritizes effort and impact over volume: spec completion > commit breadth > LOC. A tricky 50-line fix outranks 500 lines of boilerplate.
- Patterns section limited to 2-3 observations per retro to avoid diluting the signal. Includes a reference table of pattern types to look for.
- JSON snapshot schema includes `version: 1` for forward compatibility — future retro versions can handle old snapshots
- `trends.json` is gitignore-safe (computed from snapshots), while individual snapshots should be committed for historical record
- Compare mode produces a side-by-side table with trend arrows and opinionated "What Changed" analysis
- Rolling averages use a 6-week window (configurable) for Patterns context ("highest in 6 weeks")

**Deviations from plan:** None
