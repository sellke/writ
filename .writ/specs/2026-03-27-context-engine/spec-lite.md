# Context Engine (Lite)

> Source: .writ/specs/2026-03-27-context-engine/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Intelligent spec context routing to pipeline agents — per-story hints, cross-story continuity, and agent-specific views

**Implementation Approach:**
- Per-story context hints as indexes into full spec (don't duplicate, reference)
- "What Was Built" records appended to completed stories (sourced from review agent)
- Agent-specific sections in spec-lite.md (same budget, better targeting)
- Orchestrator parses hints, fetches content, routes to agents

**Files in Scope:**
- `commands/create-spec.md` — update spec-lite generation, context hint passing
- `commands/implement-story.md` — parse hints, fetch content, route sections
- `agents/user-story-generator.md` — generate context hints
- `agents/coding-agent.md` — receive targeted spec section + "What Was Built"
- `agents/review-agent.md` — output structured for "What Was Built" record
- `agents/testing-agent.md` — receive targeted spec section
- `agents/documentation-agent.md` — receive targeted spec section
- `agents/architecture-check-agent.md` — receive targeted spec section
- `commands/create-uat-plan.md` — new command (create file)

**Error Handling:**
- Context hint points to missing content → log warning, skip gracefully
- "What Was Built" record incomplete → proceed with available context
- Spec-lite section exceeds line budget → truncate, prioritize critical content

**Integration Points:**
- `/create-spec` generates hints during story creation
- `/implement-story` Step 2 loads and parses hints
- `/implement-story` Gate 3.5 generates "What Was Built" record
- `/create-uat-plan` reads completed stories and generates test scenarios

**Line Budget Constraints:**
- Total spec-lite: <100 lines (hard limit)
- Coding section: 35 lines max
- Review section: 35 lines max
- Testing section: 30 lines max

---

## For Review Agents

**Acceptance Criteria:**
1. Coding agents handle error cases from specs without explicit reminders (80%+ coverage)
2. Review agents catch business rule violations (catch rate +30% vs baseline)
3. Story 3 builds correctly on Stories 1-2 (zero integration failures from bad assumptions)
4. No prompt length increase (≤105% of baseline)
5. UAT plans enable validation without code reading (90%+ scenarios executable)

**Business Rules:**
- Only spec-lite.md is auto-modified (full spec.md stays stable)
- "What Was Built" sourced from review agent, not coding agent self-reports
- Context hints are mandatory for all new specs (no fallback mode)
- UAT plans generated after story completion, not during spec creation
- Agent-specific sections must stay within line budgets (35/35/30)

**Experience Design:**
- Entry: `/create-spec` as normal, context hints generated automatically
- Happy path: Context Engine works invisibly, better code quality
- Moment of truth: Agents handle spec content without explicit prompting
- Feedback: Silent success, validation via metrics measurement
- Error: Missing content logged and skipped gracefully

**Context Hint Format:**
```markdown
## Context for Agents
- Error map rows: [row names]
- Shadow paths: [path names]
- Business rules: [rule summaries]
- Experience: [design element names]
```

**"What Was Built" Record Structure:**
- Files created/modified with descriptions
- Implementation decisions (error handling, rate limiting, etc.)
- Test count and coverage
- Review notes (PASS/FAIL, security, drift)

**Drift Analysis:**
- Small: Auto-amend spec-lite, log, continue
- Medium: Flag warning, log, continue
- Large: Pause, present options, wait for decision

---

## For Testing Agents

**Success Criteria:**
1. Review agent catch rate improves by at least 30% over baseline
2. Coding agents implement 80%+ of error maps without explicit prompting
3. Cross-story integration tests pass (no failures from bad assumptions)
4. Agent prompt lengths stay ≤105% of current baseline
5. UAT scenarios executable without code reading (90%+ clarity)

**Shadow Paths to Verify:**
- **Happy path:** Context hints → orchestrator fetches → agents receive targeted content
- **Nil input:** Context hint points to missing content → log warning, skip gracefully
- **Empty input:** No context hints in story file → orchestrator skips hint parsing
- **Upstream error:** Review agent output incomplete → "What Was Built" uses partial data

**Edge Cases:**
- Context hint references nonexistent error map row → log, skip that row, continue
- "What Was Built" missing required fields → validation warning, append partial
- Spec-lite section exceeds line budget → truncate, log which items dropped
- Multiple stories complete simultaneously → "What Was Built" records don't conflict

**Coverage Requirements:**
- New code: ≥80%
- Critical paths (hint parsing, content fetching, section routing): 100%
- Error paths (missing content, malformed hints): 100%

**Test Strategy:**
- Unit tests: hint parsing, content fetching, line budget enforcement
- Integration tests: full `/create-spec` → `/implement-story` → UAT generation flow
- Comparison tests: same spec with/without Context Engine, measure quality delta
- Dogfood: run on real Writ feature (self-dogfooding validation)
