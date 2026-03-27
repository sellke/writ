# Context Engine — User Stories

> **Spec:** `.writ/specs/2026-03-27-context-engine/`
> **Total Stories:** 5
> **Status:** Not Started

## Stories Overview

| # | Story | Status | Priority | Tasks | Progress |
|---|-------|--------|----------|-------|----------|
| 1 | [Per-Story Context Hints](story-1-per-story-context-hints.md) | Completed ✅ | High | 7 | 7/7 |
| 2 | [Agent-Specific Spec Views](story-2-agent-specific-spec-views.md) | Not Started | High | 7 | 0/7 |
| 3 | ["What Was Built" Records](story-3-what-was-built-records.md) | Not Started | High | 8 | 0/8 |
| 4 | [Context Routing Improvements](story-4-context-routing-improvements.md) | Not Started | High | 9 | 0/9 |
| 5 | [UAT Plan Generation](story-5-uat-plan-generation.md) | Not Started | Medium | 9 | 0/9 |

**Total Tasks:** 40 (7 complete, 33 remaining)

## Dependencies

```
Story 1 (Context Hints)        Story 2 (Agent-Specific Views)
        ↓                               ↓
        └───────────→ Story 3 (What Was Built) ←────┘
                             ↓
                     Story 4 (Context Routing) ←────┘
                             ↓
                     Story 5 (UAT Plan)
```

- **Story 1** and **Story 2** can run in parallel (no dependencies)
- **Story 3** depends on Story 2 (needs agent-specific routing to work)
- **Story 4** depends on Stories 1, 2, and 3 (ties everything together)
- **Story 5** depends on Story 3 (benefits from "What Was Built" records)

## Story Descriptions

### Story 1: Per-Story Context Hints
Add context hint generation to user-story-generator agent so each story file indexes into the full spec for targeted context delivery. Updates user-story-generator agent prompt template and create-spec command to pass full spec context.

**Key deliverables:**
- `.writ/docs/context-hint-format.md` documentation
- Updated user-story-generator agent
- Context hint generation in create-spec

### Story 2: Agent-Specific Spec Views
Restructure spec-lite.md with labeled sections (For Coding Agents, For Review Agents, For Testing Agents) so each agent role receives targeted content within the <100 line budget.

**Key deliverables:**
- New spec-lite.md format with agent-specific sections
- Line budget enforcement (35/35/30)
- Updated spec-lite generation in create-spec

### Story 3: "What Was Built" Records
After story completion, append a "What Was Built" record sourced from review agent output so downstream stories know what upstream stories actually produced (cross-story continuity).

**Key deliverables:**
- `.writ/docs/what-was-built-format.md` documentation
- Gate 3.5 extraction from review agent output
- Gate 5 append to story file
- Step 2 reads and passes to downstream coding agents

### Story 4: Context Routing Improvements
Update orchestrator logic to parse context hints, fetch referenced content from spec.md/technical-spec.md, and route agent-specific spec sections to all 5 pipeline agents.

**Key deliverables:**
- Step 2 hint parsing and content fetching
- Agent-specific section routing to all 5 agents
- "What Was Built" routing to coding agents
- Graceful degradation for missing content

### Story 5: UAT Plan Generation
Create `/create-uat-plan` command that reads completed stories and generates human-readable test scenarios for manual validation, bridging "AI says it works" and "human confirmed it works."

**Key deliverables:**
- New `/create-uat-plan` command
- Scenario generation from acceptance criteria, error maps, shadow paths, edge cases
- "What Was Built" integration for concrete details
- Output to `.writ/specs/{spec}/uat-plan.md`

## Implementation Notes

### Recommended Order
1. **Story 1** and **Story 2** in parallel (foundation layer)
2. **Story 3** after Story 2 completes
3. **Story 4** after Stories 1, 2, and 3 complete (integration layer)
4. **Story 5** after Story 3 completes (can run parallel with Story 4)

### Success Criteria
- Coding agents handle error cases from specs without explicit reminders (80%+ coverage)
- Review agents catch business rule violations (catch rate +30% vs baseline)
- Story 3 builds correctly on Stories 1-2 (zero integration failures from bad assumptions)
- No prompt length increase (≤105% of baseline)
- UAT plans enable validation without code reading (90%+ scenarios executable)

### Validation Plan
- Baseline measurement before Context Engine (3 specs through current pipeline)
- Context Engine measurement after implementation (same 3 specs)
- Compare: catch rate improvement, error handling coverage, integration issues, prompt length
- Manual UAT execution on 2 features to validate scenario clarity
