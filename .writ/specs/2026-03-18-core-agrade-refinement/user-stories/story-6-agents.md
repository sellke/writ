# Story 6: Agent Refinement (5 agents to A)

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user whose code passes through the agent pipeline
**I want** each agent to receive focused, principle-based instructions
**So that** agents spend context on reviewing/writing code, not processing framework detection recipes and 31-item checklists

## Acceptance Criteria

- [x] Given review-agent.md, when the review checklist is examined, then 31 individual items have been replaced with ~5 categorized principles covering the same areas (acceptance criteria, code quality, security, test coverage, integration)
- [x] Given review-agent.md, when examples are counted, then PASS-no-drift and PASS-medium-drift examples are removed, leaving PASS-with-drift and FAIL (~70 lines of examples total)
- [x] Given review-agent.md, when line count is checked, then it is approximately 280 lines (±15%)
- [x] Given coding-agent.md, when the prototype scope detection section is examined, then 50 lines have been replaced with a single conditional principle (~5 lines)
- [x] Given coding-agent.md, when line count is checked, then it is approximately 200 lines (±15%)
- [x] Given documentation-agent.md, when the file structure is reviewed, then "no framework detected" is the primary (first) path, not buried after 5 framework sections
- [x] Given documentation-agent.md, when framework-specific sections are reviewed, then 5 detailed sections have been replaced with one brief conditional
- [x] Given documentation-agent.md, when line count is checked, then it is approximately 180 lines (±15%)
- [x] Given architecture-check-agent.md, when examples are reviewed, then they are ~20% shorter with redundant commentary removed
- [x] Given testing-agent.md, when test runner detection is reviewed, then explicit detection recipes are removed (AI can detect vitest vs jest), while coverage thresholds and failure analysis table are preserved

## Implementation Tasks

- [x] 6.1 Rewrite review-agent.md: replace 31-item checklist with categorized principles, condense examples
- [x] 6.2 Rewrite coding-agent.md: extract prototype scope detection to single conditional principle
- [x] 6.3 Restructure documentation-agent.md: default-first, compress framework sections
- [x] 6.4 Compress architecture-check-agent.md examples (~20% reduction)
- [x] 6.5 Compress testing-agent.md: remove detection recipes, keep thresholds and failure analysis
- [x] 6.6 Run litmus test on every section of all 5 agent files
- [x] 6.7 Verify line counts for all 5 agents are in target ranges

## Notes

- Review agent is the biggest lift — the checklist → principles rewrite requires preserving the non-obvious items (swallowed errors, vacuous assertions, debug artifacts, "security is never Minor") while removing the items the AI already knows
- Coding agent change is surgical — keep everything except the prototype scope detection section
- Documentation agent restructure: the "no framework" path is what 90%+ of projects need. Make it the first thing the agent reads.
- Architecture check and testing agents are already close to A — these are polish, not rewrites
- The review agent's drift analysis section and change surface weighting should be preserved — these encode non-obvious judgment

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] All 5 agent files pass litmus test on every section
