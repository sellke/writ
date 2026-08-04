# Secondary Command Refinement — Spec Lite

> Source: spec.md
> Purpose: Efficient AI context for implementation

## What We're Building

Refine 3 secondary Writ commands (create-issue, design, prototype) from mixed B-/B+ to all-A by applying the same litmus test used in the core refinement: every line must teach the AI something non-obvious, set a quality bar, or prevent a specific mistake. Templates become principles. ~47% line reduction, zero capability lost.

## The Litmus Test

For every line in every file: (1) teaches something non-obvious, (2) sets a quality bar the AI wouldn't reach alone, (3) prevents a specific mistake — or it gets cut.

## Key Changes

- **create-issue:** Cut redundant "AI Implementation Prompt" (restates process), 3 of 4 examples, Integration Notes, Future Enhancements. Merge Core Rules into process. 307 → ~140 lines.
- **design:** Cut Excalidraw JSON schema, component primitives, Tool Integration. Replace 3 markdown templates (component-inventory, mockups/README, design-system) with principles. Compress Mode C/D. Keep modal structure and wireframe conventions. 377 → ~200 lines.
- **prototype:** Rewrite 80-line agent prompt to ~25 lines of principles. Consolidate 3 output format sections. Merge error handling into pipeline. Keep pipeline diagram, visual preview, scope escalation, experience gaps. 358 → ~210 lines.

## Files in Scope

commands/create-issue.md, commands/design.md, commands/prototype.md

## Key Constraints

- Same litmus test and simplification principle as core refinement spec
- Design command's four modes are the organizing spine — compress within modes, not across
- Prototype's six scope escalation flags are non-obvious — keep as explicit list
- Create-issue's speed philosophy must stay prominent — this command should feel fast

## Success Criteria

- All sections pass the litmus test
- ~550 total lines (from ~1,042)
- No cross-reference breakage (prototype → coding-agent, design → visual-qa-agent)
- Zero functional capability lost
- Consistent voice and density with already-refined commands
