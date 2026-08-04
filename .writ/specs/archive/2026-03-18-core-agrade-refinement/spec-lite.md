# Core A-Grade Refinement — Spec Lite

> Source: spec.md
> Purpose: Efficient AI context for implementation

## What We're Building

Refine 10 core Writ files (3 commands, 2 command+orchestrators, 5 agents) from mixed B-/B/B+/A- grades to all-A by applying one principle: every line must teach the AI something non-obvious, set a quality bar, or prevent a specific mistake. Templates become principles. Procedures become quality bars. ~37% line reduction, zero capability lost.

## The Litmus Test

For every line in every file: (1) teaches something non-obvious, (2) sets a quality bar the AI wouldn't reach alone, (3) prevents a specific mistake — or it gets cut.

## Key Changes

- **plan-product & create-spec:** Phase 1 discovery preserved intact (crown jewel). Phase 2 file-creation templates (~640 lines combined) replaced with ~100 lines of principles.
- **implement-story:** Gate 3.5 drift response rewritten from 117 procedural lines to ~40 lines of principles. Three-tier model preserved (Small/Medium/Large).
- **review-agent:** 31-item checklist replaced with 5 categorized principles. Examples condensed 50%.
- **Cross-cutting:** SwitchMode references removed (Cursor doesn't support it). Redundant "Key Improvements," "Best Practices," "Tool Integration" sections cut from all files.

## Files in Scope

commands/plan-product.md, commands/create-spec.md, commands/implement-spec.md, commands/implement-story.md, agents/review-agent.md, agents/coding-agent.md, agents/documentation-agent.md, agents/architecture-check-agent.md, agents/testing-agent.md

## Key Constraints

- Phase 1 discovery in plan-product and create-spec is untouchable — it's what makes Writ valuable
- Pipeline gate model is structurally preserved — refining instructions, not redesigning the pipeline
- Drift three-tier model (Small/Medium/Large) preserved as principles, not procedures
- No changes to user-story-generator or visual-qa-agent (already A)

## Success Criteria

- All sections pass the litmus test
- ~2,310 total lines (from ~3,675)
- No cross-reference breakage between files
- Zero functional capability lost
