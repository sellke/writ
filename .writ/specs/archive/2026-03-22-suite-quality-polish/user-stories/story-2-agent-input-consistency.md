# Story 2: Add `context_md_content` to Testing and Documentation Agents

> **Status:** Completed ✅ (2026-03-22)
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ pipeline orchestrator
**I want to** pass `context_md_content` to all five pipeline agents consistently
**So that** testing and documentation agents have the same product mission and spec state context as the other agents

## Acceptance Criteria

- [x] Given the Testing Agent file, when I read the Input Requirements table, then `context_md_content` is listed as the first parameter with the standard description
- [x] Given the Documentation Agent file, when I read the Input Requirements table, then `context_md_content` is listed as the first parameter with the standard description
- [x] Given both agent prompt templates, when I read them, then they include a `## Project Context` section with `{context_md_content}` injection, matching the pattern in architecture-check, coding, and review agents

## Implementation Tasks

- [x] 2.1 Add `context_md_content` row to the Input Requirements table in `agents/testing-agent.md` — first row, with description: "**First context item.** Contents of `.writ/context.md` if present — product mission, active spec state, recent drift. Pass empty string if file doesn't exist yet."
- [x] 2.2 Add `## Project Context\n\n{context_md_content}\n\n---` block to the Testing Agent's prompt template, immediately after the opening instruction line and before `## Your Mission`
- [x] 2.3 Add `context_md_content` row to the Input Requirements table in `agents/documentation-agent.md` — first row, same description
- [x] 2.4 Add `## Project Context\n\n{context_md_content}\n\n---` block to the Documentation Agent's prompt template, immediately after the opening instruction line and before `## Your Mission`
- [x] 2.5 Verify all five pipeline agents (architecture-check, coding, review, testing, documentation) now have consistent `context_md_content` as their first input parameter

## Notes

- This is a surgical two-line-per-file change — input table row + prompt template injection
- Match the exact pattern used in `agents/coding-agent.md` lines 27-28 (input table) and lines 47-51 (prompt template)
- The `---` separator after the Project Context block is important — it visually separates context from mission

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] All five pipeline agents have consistent input contracts
