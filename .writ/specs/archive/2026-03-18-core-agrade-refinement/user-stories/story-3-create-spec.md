# Story 3: create-spec.md Refinement (B+ → A)

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user running /create-spec
**I want** the command to preserve its excellent discovery phase while trimming bloated file-creation templates
**So that** the AI spends tokens on understanding my feature, not processing markdown scaffolding

## Acceptance Criteria

- [x] Given create-spec.md, when Phase 1 discovery (experience-first ordering, pushback examples, cross-spec overlap, contract format) is reviewed, then it is intact and unchanged from the pre-cleanup version
- [x] Given create-spec.md Phase 2, when spec.md creation guidance is reviewed, then it states what the file should contain as principles, not a markdown template
- [x] Given create-spec.md, when story generation guidance is reviewed, then the parallel subagent concept is expressed in ~20 lines (not 75 lines of exact Task JSON)
- [x] Given create-spec.md, when error mapping sections are reviewed, then Error & Rescue Map, Shadow Paths, and Interaction Edge Cases each have one example row and a concept description (not full template tables)
- [x] Given create-spec.md, when examples are reviewed, then only Example 2 (full discovery flow) remains — Example 1 (simple flow) is removed
- [x] Given the complete file, when every section is tested against the litmus test, then every section passes
- [x] Given create-spec.md, when line count is checked, then it is approximately 400 lines (±15%)

## Implementation Tasks

- [x] 3.1 Read the current create-spec.md (post Story 1 cleanup) and map all remaining sections
- [x] 3.2 Rewrite Phase 2 file creation: spec.md, spec-lite.md creation as principles not templates
- [x] 3.3 Compress story generation guidance from ~75 lines to ~20 lines — keep parallel subagent concept, remove exact Task JSON
- [x] 3.4 Compress error mapping (Error & Rescue Map, Shadow Paths, Interaction Edge Cases) to concept + one example row each. Keep scope detection trigger.
- [x] 3.5 Remove Example 1 (simple flow). Keep Example 2 (full discovery flow).
- [x] 3.6 Run litmus test on every remaining section — cut anything that fails
- [x] 3.7 Verify line count is in target range (~400 ±15%)

## Notes

- The experience-first discovery ordering (experience → rules → technical) is Writ's best insight — preserve it completely
- Error mapping concepts are genuinely valuable — the [UNPLANNED] marker, the "what the user sees not what the system does" principle, the scope detection trigger. Keep the ideas, compress the format.
- The Visual References step (§1.5) is solid — trim the handling descriptions slightly but keep the feature
- Cross-spec overlap check (§1.3b) is a smart heuristic — keep as-is

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] File passes litmus test on every section
