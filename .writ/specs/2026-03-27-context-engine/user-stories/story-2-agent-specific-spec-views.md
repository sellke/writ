# Story 2: Agent-Specific Spec Views

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** pipeline agent (coding, review, or testing)
**I want** to receive only the spec content relevant to my role
**So that** I can focus on what matters for my gate without irrelevant context

## Acceptance Criteria

- [ ] Given a spec created after this story, when spec-lite.md is generated, then it contains three labeled sections: "## For Coding Agents", "## For Review Agents", "## For Testing Agents"
- [ ] Given the agent-specific sections, when measured, then the total file stays <100 lines and per-section limits are enforced (35 for coding, 35 for review, 30 for testing)
- [ ] Given a spec-lite with agent-specific sections, when coding agent is invoked, then it receives only the "For Coding Agents" section (verified via agent prompt inspection)
- [ ] Given a spec-lite with agent-specific sections, when review agent is invoked, then it receives only the "For Review Agents" section
- [ ] Given a spec-lite with agent-specific sections, when testing agent is invoked, then it receives only the "For Testing Agents" section

## Implementation Tasks

- [ ] 2.1 Write tests for spec-lite section generation (given spec.md, generate agent-specific sections within line limits)
- [ ] 2.2 Update `commands/create-spec.md` Step 2.4 to generate spec-lite.md with agent-specific sections instead of single block
- [ ] 2.3 Add line budget enforcement logic (truncate sections that exceed limits, prioritize critical content)
- [ ] 2.4 Update the spec-lite.md template in create-spec with the new format (see spec.md Technical Decisions for structure)
- [ ] 2.5 Test section routing in orchestrator (read spec-lite, extract section by agent role, pass to agent)
- [ ] 2.6 Verify section generation on dogfood (this spec's spec-lite.md follows new format)
- [ ] 2.7 Verify all acceptance criteria are met and tests pass

## Notes

**Technical considerations:**

- Same <100 line budget as current spec-lite, but better targeting
- Coding agents need: implementation approach, error maps, files in scope, integration points
- Review agents need: acceptance criteria, business rules, experience design, drift analysis format
- Testing agents need: success criteria, shadow paths, edge cases, coverage requirements
- If content exceeds limits, prioritize: error maps and business rules over nice-to-haves

**Integration points:**

- `/create-spec` Step 2.4 (Generate Core Documents) creates the new format
- `/implement-story` agent invocations (all gates) will route sections in Story 4
- This story changes the file format; Story 4 implements the routing logic

**Risks:**

- Line budget pressure if too much content — mitigation: hard limits with truncation
- Unclear which content belongs in which section — mitigation: document guidelines in create-spec

## Definition of Done

- [ ] All tasks completed
- [ ] Spec-lite generation updated with agent-specific sections
- [ ] Line budget enforcement implemented and tested
- [ ] Tests passing for section generation
- [ ] Dogfood validation: this spec's spec-lite.md uses new format
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** Spec-lite section exceeds line budget (truncation / prioritization behavior)
- **Shadow paths:** Happy path: spec-lite generated → sections created within limits → agents receive targeted content
- **Business rules:** Agent-specific spec views must stay <100 lines total; enforce per-section limits (35 / 35 / 30)
- **Experience:** Silent success; agents work better without exposing routing to the user
- **Format reference:** `spec.md` → `## Implementation Approach` → `### Technical Decisions` — agent-specific spec-lite structure
- **Files in scope:** `spec.md` → `## Implementation Approach` → `### Files in Scope` — `commands/create-spec.md`, spec-lite generation and templates, tests for section generation and budgets
