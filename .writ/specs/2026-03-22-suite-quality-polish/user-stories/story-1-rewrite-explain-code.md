# Story 1: Rewrite `/explain-code` Command

> **Status:** Completed ✅ (2026-03-22)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ user
**I want to** have an `/explain-code` command that follows the same patterns as every other Writ command
**So that** the suite is consistent and the command actually works without referencing non-existent features

## Acceptance Criteria

- [x] Given the rewritten command, when I read it, then there is no broken markdown (no unclosed code blocks)
- [x] Given the rewritten command, when I search for sub-command references, then no non-existent commands are referenced (`/list-explanations`, `/search-explanations`, `/explanation-history`, `/refresh-explanations` are all removed)
- [x] Given the rewritten command, when I compare its structure to `/review` or `/refactor`, then it follows the same pattern: Overview, Invocation table, Command Process with steps, Integration with Writ table
- [x] Given the rewritten command, when I look for IDE-specific claims, then none exist (no hover tooltips, right-click menus, or IDE integration claims)
- [x] Given the rewritten command, when I check for aspirational sections, then there is no "Future Enhancements" or "Success Metrics" section

## Implementation Tasks

- [x] 1.1 Read the current `commands/explain-code.md` and catalog all issues (broken markdown, non-existent references, aspirational claims, structural gaps)
- [x] 1.2 Write the new `commands/explain-code.md` following established command patterns: Overview with clear purpose, Invocation table with modes, Command Process with numbered steps, output format, Integration with Writ table
- [x] 1.3 Ensure output is adaptive — diagrams when helpful for complex flows, plain explanation for simple functions — not mandated for every query
- [x] 1.4 Remove auto-save default — output goes to conversation; remove `.writ/explanations/` directory convention
- [x] 1.5 Verify no broken markdown by reviewing the complete file end-to-end

## Notes

- This is the largest change in the spec — a full rewrite, not a patch
- Use `/review` (199 lines) or `/refactor` (199 lines) as structural references — they're compact, well-structured commands
- The new command should be significantly shorter than the current 270 lines — target ~120-150 lines
- Keep it simple: explain code, show context, done. No persistence, no sub-commands, no IDE integration

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] No broken markdown in the file
- [x] Command follows established Writ patterns
- [x] No references to non-existent features
