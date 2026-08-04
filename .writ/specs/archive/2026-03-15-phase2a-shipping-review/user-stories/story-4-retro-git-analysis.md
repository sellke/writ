# Story 4: /retro — Git Analysis & Metrics

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** developer reflecting on a period of work
**I want to** see data-driven metrics from my git history and Writ usage
**So that** I can identify patterns, celebrate wins, and spot areas for improvement

## Acceptance Criteria

- [x] Given I run `/retro` on a repository, when the analysis runs, then it collects commits, LOC, files changed, test ratio, sessions, and streaks from git history for the specified period
- [x] Given commits are clustered with gaps > 2 hours, when session detection runs, then it correctly identifies separate sessions with duration and commit count
- [x] Given a Writ project with drift-log.md and spec folders, when Writ context is collected, then the retro includes specs completed, stories completed, and drift incidents
- [x] Given I run `/retro --spec .writ/specs/...`, when the analysis runs, then it scopes metrics to the time range of that spec's lifetime (creation date to now or completion date)
- [x] Given no configuration exists, when auto-detection runs, then timezone and default branch are detected automatically without hardcoded values

## Implementation Tasks

- [x] 4.1 Create `commands/retro.md` with command header, purpose section, and design philosophy (opinionated about what matters: shipping velocity, quality signals, developer momentum)
- [x] 4.2 Implement git metric collection — instructions for the AI to run git log/diff/shortstat commands to collect commits, LOC (net and gross), files touched, and test file ratio for the period
- [x] 4.3 Implement session detection algorithm — gap-based clustering with configurable threshold (default 2 hours), producing session count, average duration, and time-of-day distribution
- [x] 4.4 Implement streak tracking — consecutive days with at least one commit, current streak and longest streak in period
- [x] 4.5 Implement Writ context collection — scan .writ/specs/ for completed specs, count completed stories, read drift-log.md files for drift incidents, read refresh-log.md for command refreshes
- [x] 4.6 Implement auto-detection — timezone via system commands, default branch via git remote, period scoping for --spec flag (read spec creation date)
- [x] 4.7 Write invocation table documenting all flags: default (7 days), --period N, --spec path, --compare, --all-branches

## Notes

- Session detection is heuristic — edge cases exist (e.g., auto-commits, CI commits, timezone changes). Err on the side of fewer, larger sessions.
- Writ context collection should be graceful when Writ artifacts don't exist (not all projects use Writ pipeline)
- Test file detection heuristic: files matching `*test*`, `*spec*`, `*.test.*`, `*.spec.*`, `__tests__/`, `tests/`
- The --spec flag should detect the spec's creation date from the file header and scope accordingly

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/retro.md` exists with metric collection and session detection fully specified
- [x] Auto-detection documented with fallback chains
- [x] All invocation flags documented
- [x] Writ context collection handles missing artifacts gracefully

## What Was Built

**Implemented:** 2026-03-15
**Files:** 1 created

**Key decisions made during implementation:**
- Session detection explicitly handles edge cases: single-commit sessions excluded from averages, bot commits filtered, merge commits counted for sessions but not volume metrics
- Test file ratio includes interpretation benchmarks (≥0.30 strong, 0.15–0.29 adequate, <0.15 neglected) so the patterns section has opinionated thresholds
- Streak tracking includes a nuance: acknowledge streaks ≥5 days but also flag if sessions are very short (might indicate interrupt-driven work, not deep work)
- Writ context collection is fully graceful — every artifact check has a "doesn't exist" path with clean messaging
- Step 7 (output) left as a clear stub for Story 5

**Deviations from plan:** None
