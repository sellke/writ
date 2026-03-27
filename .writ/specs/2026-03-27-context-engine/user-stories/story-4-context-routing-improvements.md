# Story 4: Context Routing Improvements

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 1, 2, 3

## User Story

**As a** pipeline orchestrator running /implement-story
**I want** to parse context hints, fetch referenced content, and route agent-specific spec sections
**So that** each agent receives targeted, relevant context throughout the pipeline

## Acceptance Criteria

- [ ] **Given** a story file with context hints, **when** /implement-story Step 2 runs, **then** the orchestrator parses hints and fetches referenced content from spec.md and technical-spec.md
- [ ] **Given** agent-specific spec-lite sections, **when** any agent is invoked (arch-check, coding, review, testing, documentation), **then** it receives only its relevant section (e.g., coding agent gets "## For Coding Agents")
- [ ] **Given** completed dependency stories with "What Was Built" records, **when** coding agent is invoked, **then** it receives those records in addition to story content and spec context
- [ ] **Given** a context hint that references missing content, **when** the orchestrator fetches it, **then** it logs a warning and skips that hint gracefully (doesn't fail the pipeline)
- [ ] **Given** the updated orchestrator, **when** measured, **then** agent prompt lengths stay ≤105% of baseline (better context, not more context)

## Implementation Tasks

- [ ] 4.1 Write tests for context hint parsing (given story file with hints, extract error map rows, shadow paths, business rules, experience elements)
- [ ] 4.2 Update `commands/implement-story.md` Step 2 (Load Context) to parse "## Context for Agents" section from story file
- [ ] 4.3 Add content fetching logic (given hint references, read spec.md and technical-spec.md, extract referenced sections)
- [ ] 4.4 Add graceful degradation for missing content (log warning, skip hint, continue with available context)
- [ ] 4.5 Update all 5 agent invocations to receive agent-specific spec-lite section instead of full file (arch-check, coding, review, testing, documentation)
- [ ] 4.6 Update coding agent invocations to receive "What Was Built" records from completed dependency stories
- [ ] 4.7 Test full pipeline with Context Engine (run /implement-story on a story with hints, verify agents receive targeted content)
- [ ] 4.8 Measure prompt length vs baseline (should be ≤105%)
- [ ] 4.9 Verify all acceptance criteria are met and tests pass

## Notes

**Technical considerations:**

- Orchestrator logic lives in `/implement-story` Step 2 and agent invocation blocks
- Context hint parsing: extract references from "## Context for Agents" section (simple markdown parsing)
- Content fetching: read spec.md and technical-spec.md, search for referenced error map rows, shadow paths, business rules
- Agent-specific routing: pass `spec_lite_section = spec_lite_content["## For Coding Agents"]` to coding agent
- "What Was Built" routing: read dependency stories, extract "## What Was Built", pass to coding agent
- Validation: if hint references "error map row: Create session" but that row doesn't exist in technical-spec.md, log warning and skip

**Integration points:**

- All agent invocations (Gates 0, 2, 3, 4, 5) receive updated context
- Step 2 (Load Context) becomes the central routing hub
- This story completes the Context Engine — everything works together after this

**Risks:**

- Complexity spike in orchestrator logic — mitigation: keep parsing simple, fail gracefully
- Prompt length could increase despite targeting — mitigation: measure and enforce ≤105% threshold

## Definition of Done

- [ ] All tasks completed
- [ ] Step 2 parses context hints and fetches content
- [ ] All 5 agents receive agent-specific spec-lite sections
- [ ] Coding agent receives "What Was Built" from dependencies
- [ ] Graceful degradation for missing content
- [ ] Tests passing for parsing, fetching, routing
- [ ] Prompt length measurement ≤105% of baseline
- [ ] Full pipeline test with Context Engine
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Context hint points to missing content]
- **Shadow paths:** [Happy path: parse hints → fetch content → route to agents]
- **Business rules:** [No prompt length increase — better context, not more context]
- **Experience:** [Context Engine works invisibly, agents just work better]
