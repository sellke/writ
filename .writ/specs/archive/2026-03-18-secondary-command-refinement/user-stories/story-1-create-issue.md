# Story 1: create-issue.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine create-issue.md to A-grade quality
**So that** every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake — with no redundant filler

## Acceptance Criteria

1. **Given** the refined create-issue.md, **when** an AI agent executes the command, **then** the core process (Steps 1-6) remains fully intact and executable without loss of capability.

2. **Given** the refined file, **when** applying the litmus test to every line, **then** each line either teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake — with no filler.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~140 ±10% (126–154 lines), down from 307.

4. **Given** the refined file, **when** checking for removed sections, **then** the following are cut entirely: AI Implementation Prompt (lines 149–204), Integration Notes (lines 273–281), Folder Structure (lines 283–296), Future Enhancements (lines 298–307).

5. **Given** the refined file, **when** reviewing examples, **then** only one example remains — the clarification case (Example 2, lines 222–240) — demonstrating when to ask vs skip.

## Implementation Tasks

1. **Read the current file** — Open `commands/create-issue.md` and verify line numbers for sections to cut/compress. Confirm the core process (Steps 1–6), question triggers, skip-if-obvious logic, related issues check, and section omission rules.

2. **Cut the AI Implementation Prompt** — Remove lines 149–204 entirely. This 56-line block restates the command process verbatim and adds no new guidance.

3. **Merge Core Rules into process steps** — Inline the 6 Core Rules (lines 142–147) into the relevant Steps 1–6 as inline guidance. Avoid duplication; each rule should appear once where it naturally belongs.

4. **Compress examples to one** — Remove Examples 1, 3, and 4. Keep only Example 2 (clarification case, lines 222–240) — it shows judgment: when to ask vs skip.

5. **Cut Integration Notes, Folder Structure, Future Enhancements** — Remove lines 273–281 (Integration Notes), 283–296 (Folder Structure), 298–307 (Future Enhancements). These duplicate Step 5 or describe tool usage/product roadmap already known to the AI.

6. **Verify and tighten** — Apply the litmus test to every remaining line. Trim any line that doesn't teach, set a bar, or prevent a mistake. Ensure "speed over completeness" philosophy, question triggers, and section omission rules are preserved.

7. **Verification** — Confirm line count within target (~140 ±10%), run a quick mental execution of the command to ensure no functional capability is lost, and that the AI agent can still perform the full workflow from the refined spec.

## Notes

- **Technical:** The Core Rules merge is the most delicate — ensure "Speed over completeness" and "Under 2 minutes" land in Step 1 or 2; "Defaults are fine" in Step 2; "Max 3 files" in Steps 3 and 5; "Bullet points over paragraphs" in Step 5; "Conversational, not robotic" in Step 2.

- **Risk:** Over-compression could remove nuance (e.g., skip-if-obvious triggers). Preserve the question triggers and their skip conditions — they encode judgment the AI might not infer.

- **Watch for:** The TL;DR and section structure in Step 5 are dense but essential. Don't collapse the markdown template; it's the output contract. Consider compressing the template if it repeats Step 5 prose.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~140 ±10%)
- [ ] No functional capability lost
