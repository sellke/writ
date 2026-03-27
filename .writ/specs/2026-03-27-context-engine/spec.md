# Context Engine Specification

> **Status:** Complete
> **Created:** 2026-03-27
> **Priority:** High
> **Phase:** 3a

## Contract Summary

**Deliverable:** Context Engine — intelligent spec context routing to pipeline agents so that code quality is determined by spec quality, not context window luck

**Must Include:** Per-story context hints, "What Was Built" records for cross-story continuity, agent-specific spec views, and UAT plan generation for human validation

**Hardest Constraint:** Maintaining <100 line spec-lite budget while delivering targeted context to three different agent roles

## Background

Writ's `/create-spec` command produces rich specification packages: full spec contracts, experience design, business rules, technical sub-specs with error maps, shadow paths, and interaction edge cases. User stories contain detailed acceptance criteria and implementation tasks.

However, analysis revealed a **context delivery gap** between what specs capture and what agents receive:

| Artifact | What It Contains | Current Delivery | Problem |
|---|---|---|---|
| `spec.md` | Full contract, experience design, business rules | Not passed to any agent | Rich context captured but never delivered |
| `spec-lite.md` | Compressed version (<100 lines) | Passed to all agents identically | One-size-fits-all; different agents need different context |
| `technical-spec.md` | Error maps, shadow paths, edge cases | Summarized as `technical_spec_summary` | Tables may not survive summarization |
| `story-N.md` | Acceptance criteria, tasks | Passed to coding/review agents | No indexing — agents don't know which spec parts are relevant |
| Previous stories | What was actually built | Not passed | Story 3 doesn't know what Stories 1-2 produced |

**The result:** Coding agents produce code that works in isolation but misses error cases described in specs. Review agents don't catch business rule violations that are specified but weren't implemented. Story 3 doesn't build correctly on Stories 1-2 because it has no record of what they actually produced.

## 🎯 Experience Design

### Entry Point
Developers use `/create-spec` as normal. Context hints are generated automatically by the `user-story-generator` agent during story file creation — no additional ceremony.

### Happy Path Flow
1. Developer runs `/create-spec` to create a new specification
2. During story generation, `user-story-generator` analyzes the contract and technical specs
3. For each story, it generates a `## Context for Agents` section that indexes into the full spec
4. Developer runs `/implement-story` on Story 1
5. Orchestrator reads context hints, fetches targeted content from spec, delivers to agents
6. Coding agent receives only the error map rows and business rules relevant to Story 1
7. After Story 1 completes, review agent's output is used to generate "What Was Built" record
8. Developer runs `/implement-story` on Story 2 (which depends on Story 1)
9. Story 2's coding agent receives Story 1's "What Was Built" record for cross-story continuity
10. Better code quality achieved without developer noticing any workflow change

### Moment of Truth
- Coding agent handles edge case described in error map without explicit reminder in prompt
- Review agent flags business rule violation that spec captured but code missed
- Story 3's implementation correctly integrates with what Stories 1-2 built (no "rebuild what you thought was there" friction)

### Feedback Model
Success is **silent** — agents just work better. Validation happens through success criteria measurement:
- Review agent catch rate for business rule violations improves >30%
- Coding agents handle error cases without explicit prompting
- Cross-story continuity verified (Story 3 builds correctly on 1-2)

### Error Experience
- If context hint points to nonexistent spec content, orchestrator logs warning and skips that hint gracefully
- If "What Was Built" record is incomplete, downstream stories proceed with whatever context is available (degraded but not blocked)
- UAT plan generation failure doesn't block shipping (plan is for human validation, not CI gating)

### State Catalog
- **Empty state:** New spec just created — context hints present but untested until first `/implement-story` run
- **First story complete:** "What Was Built" record exists, second story can use it for continuity
- **All stories complete:** Full cross-story continuity chain established, UAT plan ready for generation
- **Error state:** Context hint points to missing content — logged, skipped, falls back to spec-lite section

## 📋 Business Rules

### Spec Modification Rules
- **Only spec-lite.md is auto-modified** — full spec.md remains the human-approved contract (existing rule, preserved)
- Small drift from review agent can amend spec-lite sections; full spec stays stable

### Context Sourcing Rules
- **"What Was Built" records sourced from review agent** — third-party verification, not coding agent self-reporting
- Review agent output at Gate 3 is canonical source for what was actually implemented
- Coding agent self-reports are not trusted for cross-story context

### Line Budget Rules
- **Agent-specific spec views must stay <100 lines total** — enforce per-section limits:
  - Coding agents: 35 lines max
  - Review agents: 35 lines max
  - Testing agents: 30 lines max
- If content exceeds limits, prioritize most critical items (error maps over nice-to-haves)

### UAT Generation Rules
- **UAT plans generated after story completion** — not during spec creation
- UAT reflects actual implementation, not spec intentions
- Generated from acceptance criteria, error maps, shadow paths, and edge cases
- Format: preconditions, steps, expected result, pass/fail checkbox
- Lives at `.writ/specs/{spec}/uat-plan.md`

### Context Hint Requirements
- **Context hints are mandatory** — all new specs generated by `/create-spec` must include them
- Hints must reference actual content from spec.md and technical-spec.md
- Invalid hints (point to missing content) are logged and skipped, not errors

## Implementation Approach

### Architecture
Three-part context engine working together:

1. **Per-story context hints** — Story files get `## Context for Agents` section during `/create-spec`
   - Section indexes into full spec: "For this story, agents need error map rows X and Y, shadow path Z, business rules A and B"
   - Story file doesn't duplicate content — it points to it
   - Orchestrator pulls referenced content and delivers to agents

2. **"What Was Built" records** — After story completes Gate 5 (documentation), append `## What Was Built` section to story file
   - Structure: files created/modified, implementation decisions, error handling, test count
   - Sourced from review agent output (Gate 3)
   - Subsequent stories' coding agents receive these from completed dependency stories

3. **Agent-specific spec views** — Restructure `spec-lite.md` with labeled sections
   - `## For Coding Agents` — implementation approach, error maps, files in scope
   - `## For Review Agents` — acceptance criteria, business rules, experience design
   - `## For Testing Agents` — success criteria, shadow paths, edge cases
   - Same <100 line budget, better targeting per agent role
   - Orchestrator passes relevant section to each agent

### Integration Points

**With `/create-spec`:**
- `user-story-generator` agent prompt template updated to generate context hints
- Spec-lite generation updated to create agent-specific sections
- No change to full spec.md format

**With `/implement-story`:**
- Step 2 (Load Context) updated to parse context hints from story file
- Orchestrator fetches referenced content from spec.md and technical-spec.md
- Gate 3.5 (Drift Response) updated to generate "What Was Built" record
- All agent invocations updated to receive agent-specific spec-lite section
- Coding agent invocations updated to receive "What Was Built" from dependency stories

**With `/create-uat-plan` (new command):**
- Reads spec folder and all completed story files
- Extracts acceptance criteria, error maps, shadow paths, edge cases
- Generates human-readable test scenarios
- Outputs to `.writ/specs/{spec}/uat-plan.md`

### Files in Scope

**Modified:**
- `commands/create-spec.md` — update spec-lite generation, pass context to user-story-generator
- `commands/implement-story.md` — parse context hints, fetch content, route to agents
- `agents/user-story-generator.md` — add context hint generation to prompt template
- `agents/architecture-check-agent.md` — receive agent-specific spec-lite section
- `agents/coding-agent.md` — receive agent-specific spec-lite section + "What Was Built" from dependencies
- `agents/review-agent.md` — receive agent-specific spec-lite section, output structured for "What Was Built"
- `agents/testing-agent.md` — receive agent-specific spec-lite section
- `agents/documentation-agent.md` — receive agent-specific spec-lite section

**Created:**
- `commands/create-uat-plan.md` — new command for UAT plan generation
- `.writ/docs/context-hint-format.md` — reference for context hint syntax
- `.writ/docs/what-was-built-format.md` — reference for "What Was Built" record structure

### Technical Decisions

**Context hint format:**
```markdown
## Context for Agents

- Error map rows: [Create session, Validate input, Handle Redis failure]
- Shadow paths: [User registration flow]
- Business rules: [Free tier limits (3 projects max), Admin-only workspace deletion]
- Experience: [Error feedback model (inline + toast), Empty state (onboarding prompt)]
```

**"What Was Built" record format:**
```markdown
## What Was Built

> Completed: 2026-03-27 at Gate 5

**Files Created:**
- `src/auth/session.ts` — Session management with Redis backing

**Files Modified:**
- `src/middleware/auth.ts` — Added session validation (lines 42-68)

**Implementation Decisions:**
- Error handling: Retry 3x on Redis failure, return 503 with retry prompt
- Rate limiting: 10 requests/min per IP at middleware layer
- Session expiry: 7 days regular, 30 days "remember me"

**Tests Added:**
- 12 unit tests (session creation, validation, expiry, failures)
- 2 integration tests (full login flow, session refresh)
- All passing, 94% coverage on new code

**Review Notes:**
- PASS on first iteration
- Security: JWT signing key properly externalized
- No drift from spec contract
```

**Agent-specific spec-lite format:**
```markdown
# Spec-Lite: [Feature Name]

> Source: spec.md | For: AI agent context windows

## For Coding Agents

**Deliverable:** [One sentence]

**Implementation Approach:**
- [Key technical decisions]
- [Patterns to follow]
- [Files in scope]

**Error Handling:**
[Relevant error map rows]

---

## For Review Agents

**Acceptance Criteria:**
[Full list from all stories]

**Business Rules:**
- [Permissions and access control]
- [Validation rules and limits]

**Experience Design:**
- Entry point: [How users reach this]
- Error feedback: [What users see when things fail]

---

## For Testing Agents

**Success Criteria:**
[How we know it's working]

**Shadow Paths to Verify:**
[Happy path, nil input, empty input, upstream error]

**Edge Cases:**
[Double-click, stale state, etc.]
```

## Success Criteria

1. **Error case handling** — Coding agents produce code that handles error cases described in specs without explicit reminders (measured via spot-check of 5 stories)

2. **Business rule enforcement** — Review agents catch business rule violations that are specified but weren't implemented (catch rate improves >30% vs baseline)

3. **Cross-story continuity** — Story 3's implementation correctly builds on what Stories 1-2 actually produced, not assumptions (validated via integration test pass rate)

4. **No prompt length increase** — Better context, not more context (measure: agent prompt character counts stay ≤current)

5. **UAT validation** — UAT plans enable human validation without reading implementation code (validated via manual UAT execution on 2 features)

## Validation Plan

1. **Baseline measurement** (before Context Engine):
   - Run 3 specs through current pipeline
   - Measure: review agent catch rate for business rule violations
   - Measure: coding agent error handling coverage vs spec
   - Measure: cross-story integration issues (Story 3 fails due to bad assumptions about 1-2)
   - Measure: average agent prompt length

2. **Context Engine measurement** (after implementation):
   - Run 3 specs through Context Engine pipeline
   - Measure same metrics
   - Compare: catch rate improvement, error handling coverage, integration issues, prompt length

3. **UAT validation**:
   - Generate UAT plan for 2 completed features
   - Execute UAT manually without reading code
   - Measure: scenario clarity, coverage of edge cases, false positive rate

4. **Success threshold:**
   - Review catch rate: +30% minimum
   - Error handling: 80%+ of spec error maps implemented without explicit prompting
   - Cross-story continuity: zero integration failures due to bad assumptions
   - Prompt length: ≤105% of baseline (allowing for 5% buffer)
   - UAT clarity: 90%+ of scenarios executable without code reading

## Risks and Mitigations

### Risk: Context hints point to wrong content
**Impact:** Agents receive irrelevant context, quality doesn't improve

**Mitigation:**
- Hints generated during `/create-spec` when spec is fresh in memory
- Orchestrator validates hints — if content not found, log and skip gracefully
- Story 1 dogfooding validates hint accuracy before broader rollout

### Risk: "What Was Built" records are incomplete
**Impact:** Downstream stories get bad cross-story context

**Mitigation:**
- Source from review agent (third-party verification), not coding agent (self-reporting)
- Include structured template with mandatory fields
- Validation step: orchestrator checks for required fields before appending

### Risk: Agent-specific spec views exceed line budget
**Impact:** Prompt pressure increases, undermining "better not more" goal

**Mitigation:**
- Enforce hard per-section limits (35/35/30)
- Prioritization logic: error maps and business rules first, nice-to-haves last
- Validation: `/create-spec` checks line counts and truncates if needed

### Risk: UAT plan quality varies widely
**Impact:** Human validation becomes unreliable

**Mitigation:**
- Generate from structured inputs (acceptance criteria, error maps, shadow paths)
- Standard scenario template (preconditions, steps, expected result, checkbox)
- Dogfood on 2 features before broader rollout

### Risk: No measurable quality improvement
**Impact:** Context Engine adds complexity without value

**Mitigation:**
- Clear success criteria with thresholds (+30% catch rate, 80%+ error handling)
- Baseline measurement before implementation
- If thresholds not met, pause and reassess before Phase 3b

## Dependencies

- Phase 1 and Phase 2 dogfooding complete — real context pain points inform design
- At least one full spec run on a real project to validate context flow gaps
- All existing specs in this repo are already implemented (no backward compatibility needed)

## Out of Scope

- Cross-project learning corpus (Phase 4+)
- Self-improving context routing (Phase 4+)
- Autonomous execution with Ralph loop (Phase 3b)
- Changes to full spec.md format (remains stable)
- Integration with `/ship` for UAT sign-off (Phase 3b consideration)
