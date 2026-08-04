# Context Engine — Technical Specification

> **Spec:** `.writ/specs/2026-03-27-context-engine/`
> **Created:** 2026-03-27
> **Related Stories:** All (1-5)

## Architecture Overview

The Context Engine is a three-part system that enhances how specification content flows to pipeline agents:

```
┌─────────────────────────────────────────────────────────────────┐
│                      /create-spec                                │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │ user-story-gen   │ → generates "## Context for Agents"        │
│  │ agent (Story 1)  │    (indexes into spec, not duplication)    │
│  └──────────────────┘                                            │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │ spec-lite.md gen │ → creates agent-specific sections          │
│  │ (Story 2)        │    (For Coding / Review / Testing)         │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    /implement-story                              │
│                                                                   │
│  Step 2: Load Context (Story 4)                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Parse context hints → fetch from spec.md/technical-spec  │   │
│  │ Read spec-lite.md → extract agent-specific section       │   │
│  │ Read dependency stories → extract "What Was Built"       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                ↓                                  │
│  Gates 0-5: Agent Invocations                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Pass agent-specific spec section + context hint content  │   │
│  │ Pass "What Was Built" from dependencies (coding agent)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                ↓                                  │
│  Gate 3.5: Drift Response (Story 3)                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Extract from review agent output → generate record        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                ↓                                  │
│  Gate 5: Documentation Complete (Story 3)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Append "## What Was Built" to story file                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                 /create-uat-plan (Story 5)                       │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Read completed stories (acceptance criteria + "What Was   │   │
│  │ Built" records)                                           │   │
│  │ Read spec.md and technical-spec.md (error maps, shadow    │   │
│  │ paths, edge cases)                                        │   │
│  │ Generate human-readable scenarios → uat-plan.md           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Context Hints (Story 1)

**Format:**
```markdown
## Context for Agents

- Error map rows: [Create session, Validate input, Handle Redis failure]
- Shadow paths: [User registration flow]
- Business rules: [Free tier limits (3 projects max), Admin-only workspace deletion]
- Experience: [Error feedback model (inline + toast), Empty state (onboarding prompt)]
```

**Generation:**
- `user-story-generator` agent reads full `spec.md` and `technical-spec.md`
- Identifies which error map rows, shadow paths, business rules, and experience elements are relevant to this story
- Outputs indexes (references), not content duplication
- Generated during `/create-spec` Step 2.6 (parallel story generation)

**Parsing:**
- `/implement-story` Step 2 reads "## Context for Agents" section
- Extracts hint categories (error map rows, shadow paths, business rules, experience)
- For each hint, fetches referenced content from source files
- Graceful degradation: if content not found, log warning and skip

**Storage:**
- Lives in each story file (e.g., `story-1-context-hints.md`)
- Part of story creation, not separate file

### 2. Agent-Specific Spec Views (Story 2)

**Format:**
```markdown
# Spec-Lite: [Feature Name]

> Source: spec.md | For: AI agent context windows

## For Coding Agents

**Deliverable:** [One sentence]
**Implementation Approach:**
**Error Handling:**
**Integration Points:**

---

## For Review Agents

**Acceptance Criteria:**
**Business Rules:**
**Experience Design:**

---

## For Testing Agents

**Success Criteria:**
**Shadow Paths to Verify:**
**Edge Cases:**
**Coverage Requirements:**
```

**Line Budget Enforcement:**
- Total: <100 lines (hard limit)
- Coding section: 35 lines max
- Review section: 35 lines max
- Testing section: 30 lines max
- If content exceeds limits, truncate and log which items were dropped
- Prioritization: error maps and business rules first, nice-to-haves last

**Generation:**
- `/create-spec` Step 2.4 generates spec-lite.md with agent-specific sections
- Pulls content from full `spec.md`:
  - Coding: implementation approach, error maps, files in scope
  - Review: acceptance criteria, business rules, experience design
  - Testing: success criteria, shadow paths, edge cases

**Routing:**
- `/implement-story` agent invocations pass only relevant section
- Architecture check agent → `spec_lite_content["## For Coding Agents"]`
- Coding agent → `spec_lite_content["## For Coding Agents"]`
- Review agent → `spec_lite_content["## For Review Agents"]`
- Testing agent → `spec_lite_content["## For Testing Agents"]`
- Documentation agent → `spec_lite_content["## For Review Agents"]` (needs acceptance criteria)

### 3. "What Was Built" Records (Story 3)

**Format:**
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

**Tests Added:**
- 12 unit tests (session creation, validation, expiry, failures)
- All passing, 94% coverage on new code

**Review Notes:**
- PASS on first iteration
- No drift from spec contract
```

**Generation:**
- Source: Review agent output from Gate 3
- Extraction point: Gate 3.5 (Drift Response Handling)
- Append point: Gate 5 (after documentation agent completes)
- Validation: check for required fields (files, decisions, tests, review notes)
- Graceful degradation: if fields missing, use partial data and log warning

**Usage:**
- `/implement-story` Step 2 reads "## What Was Built" from completed dependency stories
- Passes to coding agent as additional context
- Enables cross-story continuity (Story 3 knows what Stories 1-2 built)

**Storage:**
- Appended to story file (e.g., `story-1-context-hints.md` gets record after completion)
- Part of story file, not separate file

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Parse context hints | Hint references nonexistent content | Log warning, skip that hint, continue with available content | Unit test: malformed hints → graceful skip |
| Fetch spec content | Referenced error map row doesn't exist in technical-spec.md | Log warning, skip that row, continue | Integration test: hint points to missing row |
| Generate spec-lite sections | Content exceeds line budget | Truncate, prioritize critical items, log dropped items | Unit test: oversized content → truncated to limits |
| Extract "What Was Built" | Review agent output missing required fields | Use partial data, log validation warning | Unit test: incomplete review output → partial record |
| Route agent-specific section | spec-lite.md lacks agent-specific sections (old format) | Fall back to passing full spec-lite (not applicable for Phase 3a — no backward compat needed) | N/A — all new specs use new format |
| Read dependency "What Was Built" | Dependency story file missing record | Continue without cross-story context, log warning | Integration test: Story 3 depends on Story 1 with missing record |
| Generate UAT scenarios | No completed stories in spec | Generate empty plan with note "No completed stories" | Unit test: spec with all Not Started stories |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Context hint generation | Story created with hints referencing error maps, rules, experience | user-story-generator receives empty spec.md → generates story with no hints | Story has hints section but all lists empty → valid, orchestrator skips | spec.md read fails → user-story-generator fails (acceptable — can't create story without spec) |
| Spec-lite section routing | Agent receives targeted section matching its role | Agent invoked without spec-lite path → error (should never happen, orchestrator bug) | spec-lite.md is empty file → agent receives empty string (acceptable for testing) | spec-lite.md read fails → orchestrator logs error, agent receives empty context |
| "What Was Built" generation | Review agent output complete, record appended to story | Review agent output is nil → validation warning, append partial record with "incomplete data" note | Review agent output is empty string → same as nil | Review agent fails at Gate 3 → no record generated (story doesn't reach Gate 5) |
| Cross-story context passing | Story 3 depends on Story 1, receives Story 1's "What Was Built" | Story 3 depends on Story 1 but Story 1 has no record → log warning, continue without cross-story context | Story 3 has no dependencies → orchestrator doesn't look for records | Story 1 file read fails → log error, continue without cross-story context |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Multiple context hints reference same content | Fetch once, deduplicate before passing to agent (optimization, not required for Phase 3a) |
| Story depends on multiple upstream stories | Pass all "What Was Built" records to coding agent (concatenate with separators) |
| "What Was Built" record appended while story file is being read | Not applicable — records appended at Gate 5 after all gates complete, no concurrent access |
| Spec-lite section exceeds line budget mid-generation | Truncate during generation, prioritize error maps and business rules, log dropped items |
| Context hint uses old format (different syntax) | Not applicable — all new specs use new format (no backward compat needed) |
| UAT plan generated while stories still in progress | Generate scenarios only for completed stories, note which are pending at top of uat-plan.md |

## Integration Points

### With `/create-spec`

**Modified:**
- Step 2.4 (Generate Core Documents) — spec-lite.md generation updated to create agent-specific sections
- Step 2.6 (Generate User Stories in Parallel) — user-story-generator agents receive full spec.md and technical-spec.md content

**Input changes:**
- user-story-generator agent prompt receives `spec_md_content` and `technical_spec_md_content` parameters

**Output changes:**
- spec-lite.md uses new format with three labeled sections
- Story files include "## Context for Agents" section

### With `/implement-story`

**Modified:**
- Step 2 (Load Context) — parse context hints, fetch content, read spec-lite sections, read "What Was Built"
- Gate 0 (Architecture Check) invocation — receives agent-specific spec-lite section
- Gate 2 (Coding Agent) invocation — receives agent-specific spec-lite section + "What Was Built" from dependencies
- Gate 3 (Review Agent) invocation — receives agent-specific spec-lite section
- Gate 3.5 (Drift Response Handling) — extract "What Was Built" from review agent output
- Gate 4 (Testing Agent) invocation — receives agent-specific spec-lite section
- Gate 5 (Documentation Agent) — append "What Was Built" record to story file after completion

**Input changes to agents:**
- All agents: `spec_lite_content` parameter now receives agent-specific section, not full file
- Coding agent: new `dependency_context` parameter with "What Was Built" records from upstream stories
- Coding agent: new `context_hint_content` parameter with fetched content from hints

**Output changes:**
- Story files gain "## What Was Built" section after completion
- Drift-log entries reference agent-specific spec sections

### With `/create-uat-plan` (new command)

**Reads:**
- `.writ/specs/{spec}/spec.md` — acceptance criteria reference
- `.writ/specs/{spec}/technical-spec.md` — error maps, shadow paths, edge cases
- `.writ/specs/{spec}/user-stories/story-*.md` — acceptance criteria, "What Was Built" records
- Only reads stories with "Status: Completed"

**Writes:**
- `.writ/specs/{spec}/uat-plan.md` — human-readable test scenarios

**Scenario sources:**
- Acceptance criteria → happy path scenarios
- Error maps → error handling scenarios
- Shadow paths → nil/empty/upstream error scenarios
- Edge cases → interaction pattern scenarios
- "What Was Built" records → concrete details (file names, endpoints, components)

## File Format Changes

### spec-lite.md (Story 2)

**Before:**
```markdown
# Spec-Lite: Feature Name

## What We're Building
[compressed summary]

## Key Changes
[list of changes]

## Success Criteria
[criteria list]

## Files in Scope
[file list]
```

**After:**
```markdown
# Spec-Lite: Feature Name

> Source: spec.md | For: AI agent context windows

## For Coding Agents

**Deliverable:** [one sentence]
**Implementation Approach:** [key decisions]
**Error Handling:** [error map rows]
**Integration Points:** [dependencies]

---

## For Review Agents

**Acceptance Criteria:** [full list]
**Business Rules:** [permissions, validation, state transitions]
**Experience Design:** [entry, feedback, errors]

---

## For Testing Agents

**Success Criteria:** [how we know it works]
**Shadow Paths to Verify:** [happy, nil, empty, upstream]
**Edge Cases:** [interaction patterns]
**Coverage Requirements:** [thresholds]
```

### Story files (Story 1)

**Added section:**
```markdown
## Context for Agents

- Error map rows: [row names from technical-spec.md]
- Shadow paths: [path names from technical-spec.md]
- Business rules: [rule summaries from spec.md]
- Experience: [design elements from spec.md]
```

### Story files (Story 3)

**Added section (after completion):**
```markdown
## What Was Built

> Completed: YYYY-MM-DD at Gate 5

**Files Created:**
- [file path] — [description]

**Files Modified:**
- [file path] — [description of changes]

**Implementation Decisions:**
- [decision 1]
- [decision 2]

**Tests Added:**
- [count] unit tests ([categories])
- [count] integration tests ([categories])
- All passing, [percent]% coverage

**Review Notes:**
- [PASS/FAIL on iteration X]
- [Security notes]
- [Drift notes]
```

## Performance Considerations

### Prompt Length

**Baseline (current):**
- Coding agent receives: context.md + story content + full spec-lite (~150 lines) + technical_spec_summary
- Review agent receives: context.md + story content + full spec-lite (~150 lines) + coding agent output
- Testing agent receives: context.md + story content + acceptance criteria

**With Context Engine:**
- Coding agent receives: context.md + story content + coding section (~35 lines) + context hint content (~50 lines) + "What Was Built" (~30 lines per dependency) + technical_spec_summary
- Review agent receives: context.md + story content + review section (~35 lines) + coding agent output
- Testing agent receives: context.md + story content + testing section (~30 lines)

**Expected change:**
- Coding agent: +50-80 lines (context hints + "What Was Built"), offset by -115 lines (full spec-lite → section)
- Review agent: -115 lines (full spec-lite → section)
- Testing agent: -115 lines (full spec-lite → section, currently doesn't receive it)

**Target:** ≤105% of baseline

### File I/O

**Additional reads per /implement-story run:**
- Step 2: Read dependency story files for "What Was Built" (1 read per dependency)
- Step 2: Read spec.md and technical-spec.md for context hint content (already read for spec-lite, no additional I/O)
- Step 2: Parse spec-lite.md sections (already read for current spec-lite, minimal overhead)

**Additional writes per /implement-story run:**
- Gate 5: Append "What Was Built" to story file (1 write per story completion)

**Impact:** Negligible (1-2 additional file reads per story with dependencies)

## Testing Strategy

### Unit Tests

- Context hint parsing (given story file, extract hints)
- Context hint content fetching (given hint references, fetch from spec files)
- Spec-lite section generation (given spec.md, generate agent-specific sections within line limits)
- Line budget enforcement (given oversized content, truncate to limits)
- "What Was Built" extraction (given review agent output, generate structured record)
- UAT scenario generation (given acceptance criteria + error maps, generate scenarios)

### Integration Tests

- Full /create-spec → /implement-story flow with Context Engine
- Cross-story continuity (Story 2 depends on Story 1, verify coding agent receives Story 1's record)
- Graceful degradation (context hint points to missing content, verify log and skip)
- UAT plan generation on completed spec

### Comparison Tests

- Run same spec through current pipeline (baseline)
- Run same spec through Context Engine pipeline
- Measure: review catch rate, error handling coverage, integration issues, prompt length
- Validate: catch rate +30%, error handling 80%+, zero integration failures, prompt length ≤105%

### Dogfood Tests

- Use Context Engine to build Context Engine (self-dogfooding)
- This spec should be the first spec run through Context Engine
- Stories 1-5 should validate the system as they implement it

## Validation Metrics

### Success Thresholds

| Metric | Baseline | Target | Measurement Method |
|---|---|---|---|
| Review agent catch rate | TBD (3 specs) | +30% | Count business rule violations caught by review agent |
| Error handling coverage | TBD (3 specs) | 80%+ | Spot-check: do coding agents implement error map rows without explicit prompting? |
| Cross-story integration | TBD (3 specs) | Zero failures | Count integration test failures due to bad assumptions about upstream stories |
| Prompt length | TBD (current) | ≤105% | Measure character count of agent prompts (coding, review, testing) |
| UAT scenario clarity | N/A | 90%+ | Manual execution: can human follow scenarios without reading code? |

### Baseline Collection

**Before implementing Context Engine:**
1. Run 3 specs through current pipeline (choose specs with error maps, cross-story dependencies)
2. For each spec, measure:
   - How many business rule violations were in the spec but missed by review agent?
   - How many error map rows were in the spec but not implemented by coding agent?
   - How many integration failures occurred due to Story 3 making bad assumptions about Stories 1-2?
   - What were the character counts of coding agent, review agent, and testing agent prompts?

**After implementing Context Engine:**
1. Run the same 3 specs through Context Engine pipeline
2. Measure same metrics
3. Compare and validate thresholds

### Post-Deployment Monitoring

- Track drift-log entries: are agent-specific sections causing more small drift? (auto-amended changes)
- Track "What Was Built" record completeness: how often are required fields missing?
- Track context hint accuracy: how often do hints point to missing content? (logged warnings)
- Track UAT plan quality: user feedback on scenario clarity

## Rollout Plan

### Phase 3a Implementation Order

1. **Story 1 (Context Hints)** — establish format, update user-story-generator
2. **Story 2 (Agent-Specific Views)** — restructure spec-lite, enforce line budgets
3. **Story 3 ("What Was Built" Records)** — cross-story continuity
4. **Story 4 (Context Routing)** — tie everything together in orchestrator
5. **Story 5 (UAT Plan)** — human validation scenarios

### Validation Gates

- After Story 1: Dogfood on Story 2 (verify hints are generated)
- After Story 2: Dogfood on Story 3 (verify spec-lite has agent-specific sections)
- After Story 3: Dogfood on Story 4 (verify "What Was Built" is appended after completion)
- After Story 4: Full pipeline test (verify context routing works end-to-end)
- After Story 5: Generate UAT plan for Context Engine spec itself

### Success Criteria Review

- If baselines show <10% gap to target, thresholds may be too easy (reassess)
- If Story 4 reveals fundamental issues with context delivery, pause before Story 5
- If UAT plans are unusable, reconsider integration with /ship for Phase 3b
