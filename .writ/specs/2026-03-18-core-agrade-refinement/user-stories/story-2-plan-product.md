# Story 2: plan-product.md Refinement (B- → A)

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user running /plan-product
**I want** tighter, principle-based command instructions
**So that** the AI focuses on product discovery instead of processing templates

## Acceptance Criteria

- [x] Given plan-product.md, when Phase 1 discovery (posture selection, premise challenge, dream state mapping, conversation rules, pushback format) is reviewed, then it is intact and unchanged from the pre-cleanup version
- [x] Given plan-product.md Phase 2, when the file creation section is reviewed, then it contains ~40 lines of principles (not markdown templates) describing what mission.md, roadmap.md, decisions.md, and mission-lite.md should contain
- [x] Given plan-product.md, when the contract format section is reviewed, then the mandatory architecture diagram requirement is removed and the Critical Failure Surfaces is expressed as a concept not an exact table
- [x] Given plan-product.md, when the contract decision section is reviewed, then it uses natural language instead of exact AskQuestion JSON
- [x] Given the complete file, when every section is tested against the litmus test (teaches non-obvious, sets quality bar, prevents mistake), then every section passes
- [x] Given plan-product.md, when line count is checked, then it is approximately 280 lines (±15%)

## Implementation Tasks

- [x] 2.1 Read the current plan-product.md (post Story 1 cleanup) and identify all remaining sections
- [x] 2.2 Simplify the contract format: remove mandatory architecture diagram, compress Critical Failure Surfaces to concept
- [x] 2.3 Rewrite contract decision from exact AskQuestion JSON to natural language guidance
- [x] 2.4 Replace Phase 2 file creation templates (~265 lines) with ~40 lines of principles for each output file
- [x] 2.5 Run litmus test on every remaining section — cut anything that fails
- [x] 2.6 Verify line count is in target range (~280 ±15%)

## Notes

- Phase 1 discovery is the crown jewel — do not touch it beyond the SwitchMode removal from Story 1
- The key insight for Phase 2: the AI can create excellent mission.md, roadmap.md, etc. from a locked contract + brief guidance about what each file should contain. It doesn't need a line-by-line template.
- The contract format itself (§1.4) is mostly good — the structure is sound, just needs the architecture diagram mandate removed and failure surfaces compressed

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] File passes litmus test on every section
