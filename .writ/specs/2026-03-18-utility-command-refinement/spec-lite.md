# Utility Command Refinement — Spec Lite

> Source: spec.md
> Purpose: Efficient AI context for implementation

## What We're Building

Refine 3 utility Writ commands (initialize, research, create-adr) from mixed B-/B to all-A by applying the same litmus test used in the core and secondary refinement specs: every line must teach the AI something non-obvious, set a quality bar, or prevent a specific mistake. Templates become principles. ~57% line reduction, zero capability lost.

## The Litmus Test

For every line in every file: (1) teaches something non-obvious, (2) sets a quality bar the AI wouldn't reach alone, (3) prevents a specific mistake — or it gets cut.

## Key Changes

- **initialize:** Cut 3x duplicate next-steps blocks, 2 JSON todo blocks, tech-stack + code-style templates, Tool Integration, Output Locations, Todo Integration sections. Compress phase descriptions to principles. 398 → ~170 lines.
- **research:** Cut 86-line research document template (replace with principles), Output Structure (duplicates template), todo examples, generic Best Practices/Critical Thinking/Common Pitfalls. Keep Exa-specific tips (non-obvious). 343 → ~160 lines.
- **create-adr:** Cut 155-line ADR template (replace with principles), remove auto-execute research wiring → lightweight prerequisite gate. Cut Best Practices (34 lines), Common Pitfalls (31 lines), JSON todo block. 499 → ~200 lines.

## Files in Scope

commands/initialize.md, commands/research.md, commands/create-adr.md

## Key Constraints

- Same litmus test and simplification principle as core and secondary refinement specs
- Initialize's greenfield/brownfield detection is the organizing spine — compress within workflows, not across
- Research's Exa-specific tips are genuinely non-obvious — keep prominent
- Create-adr's research prerequisite stays as a gate, not an auto-execute
- Create-adr's decision analysis flow (context → scope → alternatives → document) is preserved

## Success Criteria

- All sections pass the litmus test
- ~530 total lines (from ~1,239)
- No cross-reference breakage (create-adr → research, initialize → plan-product)
- Zero functional capability lost
- Consistent voice and density with already-refined commands
