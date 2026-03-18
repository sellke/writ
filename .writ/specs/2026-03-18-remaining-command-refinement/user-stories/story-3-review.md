# Story 3: review.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine review.md to A-grade quality
**So that** every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake — with no redundant filler

## Acceptance Criteria

1. **Given** the refined review.md, **when** an AI agent executes the command, **then** all 5 review techniques (Error & Rescue Map, Shadow Path Tracing, Interaction Edge Cases, Failure Modes Registry, Architecture Diagram) remain fully intact with their tables, severity classifications, and judgment guidance.

2. **Given** the refined file, **when** applying the litmus test to every line, **then** each line either teaches something non-obvious, sets a quality bar, or prevents a specific mistake — with no filler.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~200 ±10% (180–220 lines), down from 292.

4. **Given** the refined file, **when** checking for removed sections, **then** the following are cut: pipeline comparison table (lines 11-19), error handling section (lines 254-282), "When to Use" command routing table (lines 283-292).

5. **Given** the refined file, **when** reviewing the recommendation section and /ship integration, **then** the "Recommendation is the soul" quality bar and /ship integration are preserved.

## Implementation Tasks

1. **Read the current file** — Verify line numbers for sections to cut/compress. Confirm 5 techniques, severity classification, invocation table, ship integration, spec comparison note.

2. **Cut pipeline comparison and routing** — Remove "How /review differs from pipeline review" table (lines 11-19, context for readers not the executing AI), error handling section (lines 254-282, obvious messages), and "When to Use /review vs Other Commands" table (lines 283-292, generic routing).

3. **Compress Step 2 (Scan the Diff)** — The 4 categories (data flows vs UI vs infrastructure, trust boundaries, external dependencies, what's absent) are good but wordy. Tighten to a principle about building a mental model of the diff.

4. **Tighten technique introductions** — Each technique has introductory prose before its table. Where the table is self-explanatory, cut the intro. Preserve the "I recommend" judgment calls (these set quality bars the AI wouldn't reach alone: "starting with external I/O methods", "tracing at most 5 critical flows", "addressing all Critical and High before shipping").

5. **Compress Architecture Diagram guidance** — Keep the when-to-include/skip criteria (3+ files in chain, multiple failure points, non-obvious relationships → include; single file, pure utility, test-only → skip). Slightly compress the example.

6. **Verify and tighten** — Apply the litmus test to every remaining line. Preserve: all 5 technique tables, severity classification, "Recommendation is the soul" quality bar, trust boundary focus, /ship integration, spec comparison note. Ensure line count within target.

## Notes

- **Technical:** This is the lightest refinement — /review is already well-structured. The 5 techniques are the organizing spine and genuinely non-obvious. The risk is over-cutting: removing "I recommend" judgment calls or severity classifications that seem like filler but actually encode expert review methodology.

- **Risk:** The severity classification table (Critical/High/Medium/Low criteria) looks like it could be cut because the AI "knows" severity. But the specific criteria (e.g., "RESCUED=No + TEST=No = Critical") encode a specific methodology. Preserve it.

- **Watch for:** The shared table format note linking review's error map to create-spec's error mapping is a cross-reference that enables plan-vs-actual comparison. Don't cut it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~200 ±10%)
- [ ] All 5 techniques preserved with tables and judgment guidance
- [ ] "Recommendation is the soul" quality bar intact
