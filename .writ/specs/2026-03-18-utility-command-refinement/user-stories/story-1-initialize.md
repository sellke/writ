# Story 1: initialize.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine initialize.md to A-grade quality
**So that** every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake — with no redundant filler

## Acceptance Criteria

1. **Given** the refined initialize.md, **when** an AI agent executes the command, **then** the greenfield/brownfield detection logic (classification heuristic) and two-workflow structure remain fully intact and executable without loss of capability.

2. **Given** the refined file, **when** applying the litmus test to every line, **then** each line either teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake — with no filler.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~170 ±10% (153–187 lines), down from 398.

4. **Given** the refined file, **when** checking for removed sections, **then** the following are cut entirely: both JSON todo_write blocks (lines 31–63, 138–168), tech-stack.md template (lines 179–208), code-style.md template (lines 211–236), Tool Integration (lines 291–297), Output Locations & File Structure (lines 299–337), Todo Integration with example JSON (lines 339–370), File Creation Verification checklist (lines 372–398).

5. **Given** the refined file, **when** checking for deduplication, **then** next-steps guidance appears exactly once — the three instances (greenfield Phase 4, brownfield Phase 4, CRITICAL section) are collapsed to a single authoritative instance that recommends plan-product as the next step.

## Implementation Tasks

1. **Read the current file** — Open `commands/initialize.md` and verify line numbers for sections to cut/compress. Confirm the detection logic (lines 10–22), greenfield phases 1–4, brownfield phases 1–4, gap analysis concept, and plan-product recommendation.

2. **Cut both JSON todo_write blocks** — Remove lines 31–63 (greenfield) and 138–168 (brownfield). The AI knows how to track todos; these add no new guidance.

3. **Replace template blocks with principle statements** — Replace tech-stack.md template (lines 179–208) with a statement of what it should contain (languages, frameworks, infrastructure, dev tools, architecture pattern). Replace code-style.md template (lines 211–236) with a statement of what it should capture (file organization, naming conventions, code patterns, testing patterns, documentation style).

4. **Collapse next-steps to one instance** — Remove duplicate next-steps from greenfield Phase 4 (lines 107–130) and brownfield Phase 4 (lines 238–261). Keep the CRITICAL section (lines 268–286) as the single authoritative instance. Ensure plan-product is prominently recommended as the first next step.

5. **Cut Implementation Notes sections** — Remove Tool Integration (lines 291–297), Output Locations & File Structure (lines 299–337), Todo Integration with example (lines 339–370), and File Creation Verification (lines 372–398). These duplicate process steps or describe tool usage the AI already knows.

6. **Compress phase descriptions** — For greenfield: state what each phase accomplishes and its quality bar, not step-by-step procedures. For brownfield Phase 2: state what each doc should capture rather than full templates. For brownfield Phase 3 gap analysis: keep concept + compressed categories (missing docs, inconsistent patterns, tech debt, testing gaps, workflow improvements, architecture opportunities).

7. **Verify and tighten** — Apply the litmus test to every remaining line. Preserve the detection heuristic (package.json, source dirs, git, config files → greenfield vs brownfield), gap analysis concept, and plan-product recommendation. Ensure line count within target (~170 ±10%).

## Notes

- **Technical:** The detection logic (lines 10–22) is non-obvious — the classification heuristic (empty/minimal vs established structure) encodes judgment the AI might not infer. Preserve it verbatim.

- **Risk:** Over-compression could remove the gap analysis categories (brownfield Phase 3) or the greenfield tech recommendation categories (Phase 2). These encode structure the AI uses to produce consistent outputs.

- **Watch for:** The `.writ/` directory structure mention (lines 85–89) may be redundant with what the install script creates. Consider a single sentence: "`.writ/` exists from installation; create docs within `.writ/docs/`."

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~170 ±10%)
- [ ] Detection logic and two-workflow structure preserved
- [ ] Plan-product recommendation appears once, prominently
