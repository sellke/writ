# Story 3: "What Was Built" Records

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** developer implementing Story 3 (which depends on Stories 1–2)
**I want** the coding agent to know what Stories 1–2 actually produced
**So that** Story 3 builds correctly on real implementation, not assumptions

## Acceptance Criteria

- [ ] Given a story that completes Gate 5 (documentation), when the orchestrator processes completion, then a "## What Was Built" section is appended to the story file
- [ ] Given a completed story with "What Was Built" record, when a downstream story depends on it, then the downstream story's coding agent receives the record in its context
- [ ] Given a review agent output from Gate 3, when "What Was Built" is generated, then it includes files created/modified, implementation decisions, test count/coverage, and review notes
- [ ] Given an incomplete review agent output, when "What Was Built" generation runs, then it uses partial data and logs a validation warning (doesn't block completion)
- [ ] Given multiple completed dependency stories, when Story 3 runs, then it receives "What Was Built" records from all dependencies

## Implementation Tasks

- [ ] 3.1 Create `.writ/docs/what-was-built-format.md` documenting the record structure and fields
- [ ] 3.2 Write tests for "What Was Built" generation (given review agent output, generate structured record)
- [ ] 3.3 Update `commands/implement-story.md` Gate 3.5 (Drift Response Handling) to extract data from review agent output
- [ ] 3.4 Add validation logic for required fields (files, decisions, tests, review notes) with graceful degradation
- [ ] 3.5 Update `commands/implement-story.md` Gate 5 (Documentation) to append "What Was Built" record after documentation agent completes
- [ ] 3.6 Update `commands/implement-story.md` Step 2 (Load Context) to read "What Was Built" from completed dependency stories and pass to coding agent
- [ ] 3.7 Test cross-story continuity (Story 2 depends on Story 1, verify Story 2's coding agent receives Story 1's record)
- [ ] 3.8 Verify all acceptance criteria are met and tests pass

## Notes

**Technical considerations:**

- Source from review agent output (Gate 3) — third-party verification, not coding agent self-reporting
- Structured format with mandatory fields: files created/modified, implementation decisions, tests, review notes
- Appended at Gate 5 after all gates complete (not mid-pipeline)
- Orchestrator reads these in Step 2 when loading dependency story context
- If review output is incomplete, use partial data (don't block completion)

**Integration points:**

- `/implement-story` Gate 3 (Review Agent) provides the source data
- `/implement-story` Gate 5 (Documentation Agent) triggers the append
- `/implement-story` Step 2 (Load Context) reads these for dependency stories
- Coding agent prompt receives "What Was Built" in addition to story content

**Risks:**

- Review agent output format changes — mitigation: parse defensively, use partial data on missing fields
- "What Was Built" records make story files long over time — acceptable (only after completion, not during planning)
- Cross-story dependency chain could be deep — mitigation: pass only direct dependencies, not transitive

## Definition of Done

- [ ] All tasks completed
- [ ] "What Was Built" format documented
- [ ] Gate 3.5 extracts data from review agent
- [ ] Gate 5 appends record to story file
- [ ] Step 2 passes records to coding agent for dependency stories
- [ ] Tests passing for generation and cross-story continuity
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** `"What Was Built" record incomplete` — orchestrator logs validation warning, uses partial data, does not block completion
- **Shadow paths:** Happy path: Gate 3 review → extract data → Gate 5 append → downstream story Step 2 reads and passes to coding agent
- **Business rules:** "What Was Built" is sourced from the review agent, not coding agent self-reports
- **Experience:** Moment of truth — a downstream story (e.g. Story 3) builds correctly on upstream stories' real output, not assumptions
