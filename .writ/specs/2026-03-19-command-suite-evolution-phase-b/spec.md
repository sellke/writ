# Command Suite Evolution — Phase B Specification

> Created: 2026-03-19
> Status: Complete
> Contract Locked: ✅
> Phase: B of 2 (dependent extensions)
> Phase A (prerequisite): `.writ/specs/2026-03-19-command-suite-evolution/`

---

## Contract Summary

**Prerequisite:** Phase A must be complete before any Phase B story begins. Phase B extends `status.md`, the agent context system, and the issue pipeline — all of which depend on the config layer and status rewrite established in Phase A.

**Deliverable:** Three extensions that connect previously disconnected systems: context auto-loading into agents, issue → spec promotion pipeline, and cross-session learning via `/refresh-command --batch`.

**Hardest Constraint:** All three stories touch `status.md` and must run sequentially: Story 5 → Story 7 → Story 9.

---

## Background

Phase A establishes the structural foundation: config persistence, iteration caps, spec-lite integrity, a rewritten status command, prototype escalation, and ADR unification. Phase B builds on that foundation to close three remaining gaps:

4. **Orphaned product context** — `mission-lite.md` and `spec-lite.md` exist but nothing automatically loads them into agents
2. **Dead-end issue system** — `create-issue` produces files with no automated path into the pipeline (spec_ref field and --from-issue promotion added here)
9. **Single-session learning loop** — `/refresh-command` optimizes from one session; batch analysis makes improvement compound across sessions

---

## Experience Design

**Agent initialization (after Phase B):** Every agent receives `.writ/context.md` as the first item in its context package. It knows the product mission, current spec, recent drift. It doesn't need the orchestrator to manually inject this.

**Issue triage (after Phase B):** A bug found in QA gets captured with `/create-issue`. When it's time to fix it properly, `/create-spec --from-issue` pre-populates the discovery contract from the issue. No manual translation. `/status` surfaces stale untriaged issues automatically.

**Learning loop (after Phase B):** `/refresh-command --batch` detects patterns across runs, not just within a single session. Recurrence-weighted proposals surface friction that repeats, not noise from one bad run.

---

## Business Rules

- **Context.md is regenerated, not amended:** Every write to `.writ/context.md` is a full regeneration from current state — no incremental patching that could accumulate drift
- **Issue promotion is additive:** Promoting an issue to a spec writes `spec_ref` back into the issue file and does not modify or delete the issue
- **status.md edits are sequential:** Stories 5, 7, and 9 each extend `status.md` in order — never in parallel

---

## Implementation Approach

All three changes are edits to markdown command and agent files. No build step, no CLI, no runtime code.

### Dependency Graph

```
[Phase A complete] ──→ Story 5 (context auto-loading)
                              │
                              ↓
                        Story 7 (issue → spec)
                              │
                              ↓
                        Story 9 (batch refresh)
```

Phase B is fully sequential: Story 5 → Story 7 → Story 9. All three touch `status.md`.

### Execution Batches

**Batch 1 (after Phase A):** Story 5 — context auto-loading
**Batch 2 (after Story 5):** Story 7 — issue → spec promotion
**Batch 3 (after Story 7):** Story 9 — batch refresh

---

## User Stories

### Story 5 — `.writ/context.md` Auto-Loading
**Effort: S** | **Priority: Medium** | **Dependencies: Phase A Stories 1 + 4**

Define `.writ/context.md` format and regeneration convention. Update `implement-story.md`, `implement-spec.md`, and `status.md` to write it. Update `coding-agent.md`, `review-agent.md`, and `architecture-check-agent.md` to load it as the first context item.

**Files:** `commands/implement-story.md`, `commands/implement-spec.md`, `commands/status.md`, `agents/coding-agent.md`, `agents/review-agent.md`, `agents/architecture-check-agent.md`

### Story 7 — Issue → Spec Promotion Pipeline
**Effort: S** | **Priority: Medium** | **Dependencies: Phase A Story 4, Phase B Story 5**

Add `--from-issue [path]` mode to `create-spec.md` that pre-populates the discovery contract from the issue file. Update `create-issue.md` to include `spec_ref` field in the issue template. Update `status.md` to surface untriaged issues (older than 7 days, no `spec_ref`).

**Files:** `commands/create-spec.md`, `commands/create-issue.md`, `commands/status.md`

### Story 9 — `/refresh-command` Batch Analysis
**Effort: M** | **Priority: Low** | **Dependencies: Phase B Story 7**

Add `--batch` mode to `refresh-command.md`: ingest last N transcripts for a given command, detect patterns appearing across multiple sessions, weight amendments by recurrence frequency, auto-trigger suggestion when a command accumulates 3+ new transcripts since last refresh.

**Files:** `commands/refresh-command.md`, `commands/status.md`

---

## Success Criteria

- Issues can be promoted to specs in one command with pre-populated discovery context
- Every agent run starts with `.writ/context.md` loaded — no manual mission/spec injection needed
- `/status` surfaces untriaged issues older than 7 days automatically
- The learning loop compounds: `/refresh-command --batch` detects patterns across runs, not just within a single session

## Scope Boundaries

**Included (Phase B):**
- Stories 5, 7, 9
- New file: `.writ/context.md` format definition (in commands or this spec)
- `--from-issue` mode added to `create-spec.md`
- `--batch` mode added to `refresh-command.md`

**Excluded:**
- GitHub/GitLab issue tracker sync — issue pipeline is `.writ/issues/` only
- Runtime code, CLI changes, or anything requiring a build step
