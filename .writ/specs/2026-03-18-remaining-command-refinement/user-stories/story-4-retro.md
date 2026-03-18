# Story 4: retro.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine retro.md to A-grade quality
**So that** every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake — with no redundant filler

## Acceptance Criteria

1. **Given** the refined retro.md, **when** an AI agent executes the command, **then** session detection heuristics (2-hour gap threshold, single-commit exclusion, bot/CI filtering, merge commit handling), streak calculation, and pattern detection guidance remain fully intact.

2. **Given** the refined file, **when** applying the litmus test to every line, **then** each line either teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake — with no filler.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~220 ±10% (198–242 lines), down from 455.

4. **Given** the refined file, **when** checking for removed sections, **then** the following are cut entirely: JSON schema templates for snapshot and trends (~75 lines), output markdown templates (~60 lines), detailed bash commands (~35 lines), test file pattern list, session statistics table.

5. **Given** the refined file, **when** reviewing preserved content, **then** Ship of the Week selection heuristic, tweetable forcing function, spec-scoping, and compare mode remain intact.

## Implementation Tasks

1. **Read the current file** — Verify line numbers for JSON schemas, output templates, bash blocks. Confirm session detection, streak calculation, Writ context, Ship of the Week, patterns, tweetable, compare mode, spec-scoping.

2. **Cut JSON schema templates** — Remove full snapshot schema (lines 287–337, ~50 lines) and trends schema (lines 341–376, ~36 lines). Replace with principles: "Persist snapshot as JSON in .writ/retros/YYYY-MM-DD.json with: period dates, branch, timezone, git metrics (commits, lines added/removed/net, files touched, test ratio), session metrics (count, avg duration, longest, time distribution), streak metrics (current, longest, active days, pct), writ context (specs/stories completed, drift counts), and ship of the week. Maintain trends.json with rolling averages over 6-week window."

3. **Cut output markdown template** — Remove Step 7 template (lines 203–248, ~45 lines) and compare mode template (lines 392–407, ~15 lines). Replace with principles about what each section should contain and its quality bar (metrics table with Δ vs last, Ship of the Week anchored to commits, 2–3 opinionated patterns, Writ integration summary, tweetable summary).

4. **Cut bash commands and pattern lists** — Remove git metric collection bash (lines 62–96, ~35 lines), test file pattern matching (lines 90–95), session statistics definitions table (lines 130–136). The AI knows git and can identify test files. State what to collect, not how.

5. **Compress session detection** — Express the algorithm as heuristic principles rather than step-by-step pseudocode. Keep: 2-hour gap threshold, single-commit sessions excluded from averages, bot/CI commits filtered by author, merge commits included in sessions but not volume metrics, "err toward fewer larger sessions."

6. **Compress remaining sections** — Auto-detect environment: concept (timezone, default branch, period) as principle. Streak calculation: concept + "acknowledge ≥5 days" quality bar. Writ context: what to collect + "gracefully skip missing artifacts." Error handling: 2–3 sentences about graceful failure modes.

7. **Verify and tighten** — Apply the litmus test to every remaining line. Preserve: session heuristics, Ship of the Week selection, pattern detection guidance (test discipline, session clustering, velocity change, streak significance, cleanup signal, test debt), tweetable forcing function, spec-scoping, compare mode. Ensure line count within target.

## Notes

- **Technical:** The session detection heuristics are the crown jewel — genuinely non-obvious algorithmic judgment that the AI would get wrong without guidance. The 2-hour gap, single-commit exclusion, bot filtering, and "err toward fewer larger sessions" are all non-obvious.

- **Risk:** Cutting the JSON schemas could make snapshot/trends output inconsistent across retro runs. Mitigate by clearly stating the required fields as principles. The AI can write consistent JSON from a field list.

- **Watch for:** The pattern type table (test discipline, session clustering, velocity change, streak significance, cleanup signal, test debt) with signal and example columns is high-value guidance. It looks like a template but it's actually teaching the AI what opinionated analysis means. Keep it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~220 ±10%)
- [ ] Session detection heuristics and pattern guidance preserved
- [ ] No JSON schemas or markdown templates remain — all expressed as principles
