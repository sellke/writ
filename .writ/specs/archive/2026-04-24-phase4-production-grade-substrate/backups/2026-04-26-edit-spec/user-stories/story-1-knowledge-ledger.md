# Story 1: Knowledge Ledger v1

> **Status:** In Progress
> **Priority:** High
> **Effort:** S–M (~2–4 days per ADR-005 budget)
> **Dependencies:** None (Phase 1 dogfood completion is the phase-level entry condition, not a story-level dependency)
> **Anchored ADR:** [ADR-005](../../../decision-records/adr-005-knowledge-substrate-markdown-over-database.md)

## User Story

**As a** Writ maintainer (today: solo; tomorrow: small team)
**I want** a plain-text directory that holds the cross-cutting accumulated knowledge a project produces (conventions, lessons, glossary, small decisions) and is loaded by agents at task start
**So that** knowledge survives sessions and contributors, agents don't re-derive context every task, and a returning future-self (or new contributor) can orient on a project in under 30 minutes

## Acceptance Criteria

- [x] Given the spec ships, when I inspect the repo, then `.writ/knowledge/{decisions,conventions,glossary,lessons}/` exists with a `README.md` containing the "what goes where" decision tree (specs vs ADRs vs research vs knowledge)
- [x] Given a maintainer runs `/knowledge "summary"`, when the command completes (<60s for capture flow), then a frontmatter-conformant entry exists at the correct subdirectory path with required fields (`category`, `tags`, `created`, `related_artifacts`) populated
- [ ] Given an agent (coding, architecture-check, or review) starts a task on a follow-up feature after Story 1 ships, when the orchestrator runs Step 2 (Context Loading), then the agent receives a `knowledge_context` parameter populated from grep matches against `.writ/knowledge/`, without the maintainer mentioning the directory in the prompt _(Implementation complete; future follow-up dogfood validation still pending.)_
- [x] Given the spec is declared done, when I list `.writ/knowledge/`, then ≥5 backfilled entries exist across ≥2 categories (per ADR-005 success criteria)
- [x] Given an entry's frontmatter is malformed (missing required field), when `/knowledge` validates it, then the command refuses to write the entry and surfaces the missing field

## Implementation Tasks

- [x] 1.1 Write a manual verification checklist for the schema and decision tree (no test framework — markdown project); commit as `.writ/specs/.../user-stories/story-1-verification.md`
- [x] 1.2 Create `.writ/knowledge/` with empty subdirectories (`decisions/`, `conventions/`, `glossary/`, `lessons/`) and `.gitkeep` placeholders
- [x] 1.3 Author `.writ/knowledge/README.md` containing the decision tree, frontmatter schema, filename conventions, and authoring rules (text form per `sub-specs/technical-spec.md` → Story 1 → README)
- [x] 1.4 Author `commands/knowledge.md` modeled on `/create-issue` voice (terse, single-purpose, <2-min capture); supports `/knowledge "summary"`, `--category=X`, `--list [category]`, `--read <slug>`
- [x] 1.5 Add knowledge-loading hook to `commands/implement-story.md` Step 2 (extract keywords from story title + `## Context for Agents` block + files in scope; grep `.writ/knowledge/`; assemble `knowledge_context` ≤2KB by relevance score); update `agents/coding-agent.md`, `agents/architecture-check-agent.md`, `agents/review-agent.md` input-parameter tables to accept `knowledge_context`
- [x] 1.6 Backfill ≥5 entries across ≥2 categories from candidates in `sub-specs/technical-spec.md` → Story 1 → "Backfill candidates" table
- [x] 1.7 Update `adapters/{cursor,claude-code,openclaw}.md` with a short note on the knowledge-loading hook
- [x] 1.8 Verify all acceptance criteria via the verification checklist; capture results in `## What Was Built` _(AC3 implementation verified; future follow-up dogfood remains pending.)_

## Notes

**Dual-use justification (per ADR-007):** Solo dev: agents stop re-deriving context; future-self orients in <30 min. Team-readiness: shared knowledge substrate is the foundation any team-collab feature depends on (per ADR-005 → ADR-008 chain).

**Technical considerations:**
- Boundaries with ADRs/research/specs are the named risk in ADR-005. The README's decision tree is the primary mitigation; eval Tier 1 (Story 5) adds a check for frontmatter conformance.
- Selection mechanism is grep-based at v1. False-positive load is preferred over false-negative skip (per spec.md → Implementation Approach).
- `glossary/` deviates from date-prefix filename convention (terms are stable identifiers, not events).
- Ledger entries that should have been ADRs are a real failure mode; the README's decision tree is the line of defense, and `/knowledge` should suggest "this might be an ADR — see `commands/create-adr.md`" if the summary contains words like "architecture," "substrate," "trade-off."

**Risks:**
- **Junk-drawer drift** (ADR-005 named risk): mitigated by enforced schema + decision tree + 90-day review trigger.
- **Entries written but never loaded** (ADR-005 named risk): mitigated by self-dogfood validation in AC3 (subsequent feature work loads a backfilled entry without prompt-side mention).
- **`/knowledge` voice diverges from `/create-issue`**: mitigated by reading `commands/create-issue.md` before writing `commands/knowledge.md` and matching tone and section structure.

**Integration points:**
- Reads from existing `## Context for Agents` blocks (Phase 3a / Context Engine output)
- Loaded by orchestrator before Story 4 (preamble) is needed; ordering is independent
- Entries authored manually until `/lessons` ships in Phase 5

## Definition of Done

- [x] All tasks completed
- [ ] All 5 acceptance criteria verified via checklist _(4/5 verified now; AC3 requires a post-ship follow-up task.)_
- [x] `.writ/knowledge/README.md` reviewed for clarity (a contributor unfamiliar with Writ can read it in <10 minutes and answer "where does X belong?")
- [ ] At least one follow-up task in this same PR or a follow-up PR demonstrates the knowledge-loading hook firing without prompt-side mention (dogfood validation)
- [x] Drift log entries (if any) recorded in `drift-log.md` _(No drift entries required; only pending validation is explicitly noted here.)_
- [x] `## What Was Built` section appended (sourced from review-agent output per Context Engine convention)

## Context for Agents

- **Error map rows:** `/knowledge` outside `.writ/` project; malformed frontmatter; knowledge-loading hook with no matches (`spec.md → 🎯 Experience Design → Error experience`)
- **Shadow paths:** Happy path: `/knowledge "X"` → conformant entry → agent loads on follow-up task without prompt mention (`spec.md → 🎯 Experience Design → Happy path` step 1+2)
- **Business rules:** Plain-text + git only; knowledge boundaries (ADRs/research/specs/knowledge); frontmatter schema is required; filename convention `YYYY-MM-DD-slug.md` except `glossary/` (`spec.md → 📋 Business Rules`)
- **Experience:** Entry point for new contributor (clones repo, reads `.writ/knowledge/`, orients in <30 min); `/knowledge` voice matches `/create-issue` (terse, back-to-work) (`spec.md → 🎯 Experience Design`)
- **Technical reference:** `sub-specs/technical-spec.md → Story 1` (directory layout, frontmatter schema, README decision tree, `/knowledge` command behavior, agent context-loading hook, backfill candidates)
- **Anchored ADR:** `.writ/decision-records/adr-005-knowledge-substrate-markdown-over-database.md` (success criteria, recorded dissent, 90-day review trigger)

---

## What Was Built

**Implementation Date:** 2026-04-24

### Files Created

1. **`.writ/knowledge/README.md`**
   - Added the ledger overview, what-goes-where decision tree, frontmatter schema, filename conventions, and authoring rules.
2. **`.writ/knowledge/decisions/2026-04-24-adapter-neutrality.md`**
   - Backfilled the adapter-neutrality decision.
3. **`.writ/knowledge/decisions/2026-04-24-markdown-as-instructions.md`**
   - Backfilled the markdown-as-instructions decision.
4. **`.writ/knowledge/conventions/2026-04-24-date-prefixed-slugs.md`**
   - Backfilled the date-prefixed filename convention.
5. **`.writ/knowledge/conventions/2026-04-24-self-dogfooding-symlinks.md`**
   - Backfilled the self-dogfooding symlink convention.
6. **`.writ/knowledge/glossary/dual-use-test.md`**
   - Backfilled the Phase 4 dual-use test term.
7. **`.writ/knowledge/glossary/context-hint.md`**
   - Backfilled the context hint term.
8. **`.writ/knowledge/lessons/2026-04-24-story-overlap-needs-boundaries.md`**
   - Backfilled the story-overlap boundary lesson.
9. **`.writ/knowledge/{decisions,conventions,glossary,lessons}/.gitkeep`**
   - Added placeholders so category directories stay present before future entries exist.
10. **`commands/knowledge.md`**
    - Added the `/knowledge` command contract, including write, category override, list, read, inference, validation, and terse confirmation behavior.
11. **`.writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-1-verification.md`**
    - Added the manual verification checklist for this markdown-only story.

### Files Modified

- **`commands/implement-story.md`**
  - Added Step 2 knowledge loading: keyword extraction from story title, `## Context for Agents`, and files in scope; grep-based `.writ/knowledge/` retrieval; relevance scoring; ~2KB `knowledge_context` cap; routing to architecture-check, coding, and review agents.
- **`agents/coding-agent.md`**
  - Added optional `knowledge_context` input and prompt section.
- **`agents/architecture-check-agent.md`**
  - Added optional `knowledge_context` input and prompt section.
- **`agents/review-agent.md`**
  - Added optional `knowledge_context` input and prompt section.
- **`adapters/cursor.md`**
  - Documented that Cursor receives knowledge context through orchestrator prompt assembly.
- **`adapters/claude-code.md`**
  - Documented that Claude Code uses orchestrator-collected `knowledge_context`, not a separate hook.
- **`adapters/openclaw.md`**
  - Documented the OpenClaw equivalent: use `rg`, cap the block, and include it in relevant sub-agent prompts.
- **`.writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/README.md`**
  - Updated Story 1 and total task progress.
- **`.writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-1-knowledge-ledger.md`**
  - Marked completed implementation tasks, verified ACs, and pending dogfood validation honestly.

### Implementation Decisions

1. **Knowledge loading is orchestrator-owned** — The hook lives in `/implement-story` Step 2 and passes plain markdown to agents, preserving adapter neutrality.
2. **False positives are preferred over false negatives** — The grep flow favors loading a small amount of extra context over missing relevant project knowledge.
3. **Dogfood validation remains explicit** — The hook implementation is complete, but the follow-up task proving prompt-free loading after ship is still pending and remains unchecked.

### Test Results

**Verification:** Manual markdown verification.

- ✅ Knowledge directory exists with all four categories.
- ✅ README includes the decision tree, schema, filename rules, and authoring rules.
- ✅ `/knowledge` command documents summary capture, `--category`, `--list`, `--read`, category inference, validation, and confirmation.
- ✅ Seven backfilled entries exist across four categories with required frontmatter.
- ✅ `implement-story`, architecture-check, coding, and review agent docs route optional `knowledge_context`.
- ⚠️ Follow-up dogfood validation for AC3 remains pending by design.

### Review Outcome

**Result:** PASS with pending validation note

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** All changes stayed within Story 1-owned files and Story 1 progress metadata.

### Deviations from Spec

None. The future dogfood requirement is not a deviation; it is the explicitly pending part of AC3 and the Definition of Done.
