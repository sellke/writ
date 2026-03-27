# ADR-003: Context Engine Architecture

> **Status:** Accepted
> **Date:** 2026-03-27
> **Deciders:** Product owner
> **Part of:** `/plan-product` discovery for Context Engine

## Context

Writ's `/create-spec` command produces rich specification packages: full spec contract, experience design, business rules, technical sub-specs with error maps, shadow paths, and interaction edge cases. User stories contain detailed acceptance criteria and implementation tasks.

However, analysis of the implementation pipeline revealed a **context delivery gap** between what specs capture and what agents receive:

| Artifact | What It Contains | Current Delivery to Agents | Problem |
|---|---|---|---|
| `spec.md` | Full contract, experience design, business rules, scope boundaries | **Not passed to any agent** | Rich context captured but never delivered |
| `spec-lite.md` | Compressed version (<100 lines) | Passed to all agents identically | One-size-fits-all; coding agents and review agents need different context |
| `technical-spec.md` | Error maps, shadow paths, interaction edge cases | **Summarized** as `technical_spec_summary` | Error handling tables may not survive summarization |
| `story-N.md` | Acceptance criteria, implementation tasks | Passed to coding and review agents | No indexing — agents don't know which parts of full spec are relevant to *this* story |
| Previous stories | What was actually built | **Not passed** | Story 3's coding agent doesn't know what Stories 1-2 produced |

The result: Coding agents produce code that works in isolation but misses error cases described in specs. Review agents don't catch business rule violations that are specified but weren't implemented. Story 3 doesn't build correctly on Story 1 and 2 because it has no record of what they actually produced.

**The question:** How do we close this context delivery gap without increasing prompt length or adding ceremony to the spec creation process?

## Decision Drivers

1. **Targeted context beats comprehensive context** — agents perform better with exactly what they need than with everything
2. **Backward compatibility is mandatory** — existing specs must work without modification
3. **Prompt length is constrained** — we can't fix delivery by "just dump more in the prompt"
4. **Capture once, deliver many ways** — don't make spec authors write context multiple times
5. **Cross-story continuity is missing** — downstream stories need to know what upstream stories built

## Considered Options

### Option 1: Dump Everything (Naive Approach)

**Approach:** Pass the full `spec.md`, `technical-spec.md`, and all completed story files to every agent at every gate.

**Pros:**
- Simple implementation
- Agents get all available context

**Cons:**
- Token budget explosion — full specs can be 500+ lines
- Agents waste context window on irrelevant content (coding agent doesn't need acceptance criteria for unrelated stories)
- Doesn't solve "which parts matter for this story?" problem
- Makes context window pressure worse, not better

**Verdict:** Rejected — makes the problem worse

### Option 2: Better Summarization (Incremental Improvement)

**Approach:** Keep the current architecture but improve how `technical_spec_summary` is generated. Use smarter prompts to preserve error maps and shadow paths in the summary.

**Pros:**
- Minimal architectural change
- Backward compatible

**Cons:**
- Still lossy — no summary captures 100% of structured tables
- Doesn't solve cross-story continuity (Story 3 still doesn't know what Story 1 built)
- Doesn't solve one-size-fits-all spec-lite problem (coding and review agents need different context)
- Band-aid solution — doesn't address root cause (delivery model is wrong)

**Verdict:** Rejected — insufficient impact

### Option 3: Three-Part Context Engine (Chosen)

**Approach:** Three architectural changes that work together to deliver targeted context:

1. **Per-story context hints** — Story files get a new `## Context for Agents` section during `/create-spec`. This section indexes into the full spec: "For this story, agents need error map rows X and Y, shadow path Z, business rules A and B." The orchestrator pulls those specific pieces from the full spec and delivers them to agents. The story file doesn't duplicate the content — it points to it.

2. **"What Was Built" records** — After a story completes Gate 5 (documentation), append a `## What Was Built` section to the story file. Structure: files created/modified, key implementation decisions, error handling approach, test count. Sourced from the review agent's output (more reliable than coding agent self-reports). Subsequent stories' coding agents receive these sections from their completed dependency stories.

3. **Agent-specific spec views** — Restructure `spec-lite.md` with labeled sections: `## For Coding Agents`, `## For Review Agents`, `## For Testing Agents`. Same <100 line budget, but each section emphasizes what that role cares about. The orchestrator passes the relevant section to each agent instead of the whole file.

**Pros:**
- Targeted delivery — agents get exactly what they need
- No prompt length increase — better targeting within existing budget
- Cross-story continuity — downstream stories know what upstream stories built
- Backward compatible — when context hints are absent, fall back to current behavior
- Scales — as specs get richer, targeting gets more valuable

**Cons:**
- Requires changes to multiple files (story format, spec-lite format, orchestrator logic)
- `user-story-generator` agent must learn to produce context hints
- Orchestrator must learn to parse hints and fetch content

**Effort:** M (2-3 weeks across 5 stories)

**Verdict:** Accepted

## Decision

**Chosen: Option 3 — Three-Part Context Engine**

### Component 1: Per-Story Context Hints

**Story file format addition:**

```markdown
## Context for Agents

- Error map rows: [Create session, Validate input, Handle Redis failure]
- Shadow paths: [User registration flow]
- Business rules: [Free tier limits (3 projects max), Admin-only workspace deletion]
- Experience: [Error feedback model (inline + toast), Empty state (onboarding prompt)]
```

This section is **generated by the `user-story-generator` agent** during `/create-spec`. It doesn't duplicate spec content — it indexes into it. The orchestrator reads this section, pulls the referenced content from `spec.md` and `technical-spec.md`, and delivers it to agents.

**Backward compatibility:** When this section is absent (old specs), the orchestrator falls back to passing `spec-lite.md` in full (current behavior).

### Component 2: "What Was Built" Records

**Story file format addition (appended after Gate 5):**

```markdown
## What Was Built

> Completed: 2026-03-27 at Gate 5

**Files Created:**
- `src/auth/session.ts` — Session management with Redis backing
- `src/api/sessions.ts` — POST /api/sessions endpoint

**Files Modified:**
- `src/middleware/auth.ts` — Added session validation middleware (line 42-68)

**Implementation Decisions:**
- Error handling: Retry 3x on Redis failure, return 503 with retry prompt to user
- Rate limiting: 10 requests per minute per IP, enforced at middleware layer
- Session expiry: 7 days for regular users, 30 days for "remember me"

**Tests Added:**
- 12 unit tests (session creation, validation, expiry, Redis failure paths)
- 2 integration tests (full login flow, session refresh)
- All passing, 94% coverage on new code

**Review Notes:**
- PASS on first iteration
- Security: JWT signing key properly externalized to env var
- No drift from spec contract
```

**Sourced from:** Review agent output (Gate 3) + testing agent output (Gate 4) + documentation agent metadata (Gate 5). The review agent's summary is the most reliable source — it's a third-party verification, not self-reporting.

**Used by:** Subsequent stories' coding agents. When Story 3 depends on Story 1, the coding agent receives Story 1's "What Was Built" section as part of its context. This gives cross-story continuity.

**Backward compatibility:** When this section is absent (old specs, stories completed before Context Engine shipped), the orchestrator skips it — no hard failure.

### Component 3: Agent-Specific Spec Views

**spec-lite.md restructuring:**

Current format: one compressed document, passed identically to all agents.

New format: same file, same <100 line budget, but structured with labeled sections:

```markdown
# Spec-Lite: [Feature Name]

> Source: spec.md | For: AI agent context windows

## For Coding Agents

**Deliverable:** [One sentence — what's being built]

**Implementation Approach:**
- [Key technical decisions]
- [Patterns to follow from codebase]
- [Files in scope]

**Error Handling:**
[Relevant error map rows from technical-spec.md]

**Integration Points:**
- [What this connects to]
- [Dependencies]

---

## For Review Agents

**Acceptance Criteria:**
[Full list from all stories in this spec]

**Business Rules:**
- [Permissions and access control]
- [Validation rules and limits]
- [State transitions]

**Experience Design:**
- Entry point: [How users reach this]
- Error feedback: [What users see when things fail]
- Empty states: [What users see before data exists]

---

## For Testing Agents

**Success Criteria:**
[How we know it's working correctly]

**Shadow Paths to Verify:**
[From technical-spec.md — happy path, nil input, empty input, upstream error]

**Edge Cases:**
[Interaction edge cases from technical-spec.md — double-click, stale state, etc.]

**Coverage Requirements:**
- New code: ≥80%
- Critical paths: 100%
```

The orchestrator passes `spec-lite.md#for-coding-agents` to the coding agent, `spec-lite.md#for-review-agents` to the review agent, etc.

**Backward compatibility:** When spec-lite.md lacks these sections (old specs), pass the whole file (current behavior).

## Consequences

**Positive:**
- Coding agents receive error maps directly, not summarized away
- Review agents receive full business rules and acceptance criteria
- Testing agents receive structured edge cases and shadow paths
- Story 3 knows what Stories 1-2 built (cross-story continuity)
- No prompt length increase — better targeting within existing budget
- Backward compatible — old specs work, just less optimized

**Negative:**
- Spec-lite.md generation becomes more complex (must populate 3 sections)
- User-story-generator agent must learn to produce context hints (prompt template update)
- Orchestrator must parse context hints and fetch content (new logic in `implement-story`)
- "What Was Built" sections make story files longer over time (but only after completion, not during planning)

**Risks:**
- If context hints are inaccurate (point to wrong error map rows), agents get wrong context. Mitigation: hints are generated during `/create-spec` when spec is fresh in memory; if a hint points to nonexistent content, orchestrator skips it gracefully.
- If "What Was Built" records are incomplete or misleading, downstream stories get bad cross-story context. Mitigation: source from review agent (third-party verification), not coding agent (self-reporting).
- If agent-specific spec views exceed <100 line budget, prompt pressure increases. Mitigation: enforce hard per-section limits (35 lines for coding, 35 for review, 30 for testing).

**Review Triggers:**
- After 5 specs using Context Engine, measure: did review agents catch business rule violations that specs described but code missed? If catch rate doesn't improve >30%, reassess whether the problem is delivery or agent prompts.
- If "What Was Built" records are frequently inaccurate, switch source from review agent to a dedicated post-completion audit step.
- If agent-specific spec views routinely exceed line budgets, consider separate files instead of sections within one file.
