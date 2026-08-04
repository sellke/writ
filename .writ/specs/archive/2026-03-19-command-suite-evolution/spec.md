# Command Suite Evolution — Phase A Specification

> Created: 2026-03-19
> Status: Complete
> Contract Locked: ✅
> Phase: A of 2 (foundation + independent changes)
> Phase B: `.writ/specs/2026-03-19-command-suite-evolution-phase-b/`

---

## Contract Summary

**Deliverable:** Six targeted improvements to the Writ command/agent suite forming the structural foundation — config layer, iteration caps, spec-lite integrity, status rewrite, prototype escalation, and ADR unification. All changes are edits to existing markdown files, zero runtime code.

**Phase A must include:** Stories 1–4, 6, 8. Stories 1 and 4 are structural prerequisites that unlock Phase B (context auto-loading, issue promotion, batch refresh).

**Hardest Constraint:** `status.md` is touched by Story 1 (config read) and Story 4 (full rewrite) in this phase — these must be sequenced, not parallelized.

**Phase B dependency:** Phase B stories (5, 7, 9) require Phase A to be complete before starting. They extend `status.md` and the agent context system built here.

---

## Background

A strategic audit of the full Writ command and agent suite revealed nine systemic gaps. The audit was grounded in six dimensions: efficiency, intelligence, context, separation, delegation, and automation. The findings are documented in `.cursor/plans/command_suite_audit_6ec0e1f9.plan.md`.

Six cross-cutting structural problems affect the whole suite:

1. **No shared config layer** — `/ship`, `/release`, `/status` re-detect conventions (branch name, test runner, merge strategy) independently on every run
2. **Dead-end issue system** — `create-issue` produces files with no automated path into the pipeline
3. **Silent context drift** — `spec-lite.md` gets auto-amended by `implement-story` but no command checks whether it has diverged from `spec.md`
4. **Orphaned product context** — `mission-lite.md` and `spec-lite.md` exist but nothing automatically loads them into agents
5. **Phantom commands in `/status`** — five commands referenced in example output that don't exist
6. **decisions.md vs. ADR overlap** — two formats serving the same purpose with no guidance on which to use

Phase A addresses items 1, 3, 5, and 6 directly, and creates the foundation for items 2 and 4 (addressed in Phase B).

---

## Experience Design

### Developer Experience

**Session start (current state):** Developer opens chat, `/status` re-detects branch, test runner, merge strategy. If in the middle of a spec, has to manually load context. Agents start cold — no product mission, no active spec summary, no drift history.

**Session start (after Phase A):** `/status` reads `.writ/config.md` immediately, no repeated convention detection. Five phantom command references gone — output is trustworthy. Under 10 seconds. No questions asked.

**Prototype → spec gap (after Phase A):** When `/prototype` escalates, the user sees a clear offer: "This grew beyond prototype scope. Want to formalize it? I'll create a spec with this work as Story 1 (already complete)."

### Feedback Model

- When a command saves conventions to `.writ/config.md`: one-liner confirmation inline
- When an agent hits iteration cap: `STATUS: BLOCKED` with specific failure context — orchestrator surfaces repair decision to user
- When spec-lite has drifted: `verify-spec` flags it with a diff summary and offers `--fix`
- When `.writ/config.md` is missing: commands fall back to detection, never hard-fail, offer to save

---

## Business Rules

- **Config precedence:** Commands read `.writ/config.md` first, fall back to detection, offer to persist — never override existing config without explicit user consent
- **Iteration caps are hard limits:** `MAX_SELF_FIX_ITERATIONS = 3` in coding-agent and testing-agent. After 3 attempts, `STATUS: BLOCKED` — no exceptions, no "try one more time"
- **Spec-lite drift threshold:** Check 9 in `verify-spec` flags divergence when spec-lite sections differ materially from spec.md. The `--fix` flag regenerates spec-lite from spec.md (non-destructive: spec.md is always the source of truth)
- **Prototype Story 1 is auto-complete:** When `create-spec --from-prototype` creates a spec, Story 1 (the prototype work) is marked `Status: Completed ✅` immediately — it already exists in the codebase
- **decisions.md deprecation is soft:** Existing `decisions.md` files are not migrated. New `plan-product` runs output ADRs instead. No migration story for old files.

---

## Implementation Approach

All six Phase A changes are edits to markdown command and agent files. No build step, no CLI, no runtime code.

### Dependency Graph

```
Story 1 (config)  ──→ Story 4 (status rewrite)
Story 2 (iteration caps)       [independent]
Story 3 (spec-lite check)      [independent]
Story 6 (prototype escalation) [independent]
Story 8 (ADR unification)      [independent]
```

Stories 2, 3, 6, 8 are independent of each other and of Story 1. Story 4 depends on Story 1.

### Execution Batches

**Batch 1 (parallel):** Stories 1, 2, 3, 6, 8 — all independent, XS–S effort
**Batch 2 (sequential after Story 1):** Story 4 — status rewrite needs config layer in place

**Phase B begins after Story 4 completes.**

---

## User Stories

### Story 1 — Config Persistence Layer
**Effort: XS** | **Priority: High** | **Dependencies: None**

Introduce `.writ/config.md` as the shared convention store. Update `/ship`, `/release`, `/status`, and `/initialize` to read from it first, fall back to detection, and offer to persist detected values.

**Files:** `commands/ship.md`, `commands/release.md`, `commands/status.md`, `commands/initialize.md`

### Story 2 — Agent Iteration Caps
**Effort: XS** | **Priority: High** | **Dependencies: None**

Add `MAX_SELF_FIX_ITERATIONS = 3` to `coding-agent.md` and `testing-agent.md`. Define `STATUS: BLOCKED` output format. Update `implement-story.md` to handle BLOCKED escalation with a user-facing repair decision (retry/skip/abort).

**Files:** `agents/coding-agent.md`, `agents/testing-agent.md`, `commands/implement-story.md`

### Story 3 — Spec-Lite Integrity Check
**Effort: XS** | **Priority: High** | **Dependencies: None**

Add Check 9 to `verify-spec.md`: compare key spec-lite sections against corresponding spec.md sections, flag material divergence, add `--fix` flag that regenerates spec-lite from spec.md.

**Files:** `commands/verify-spec.md`

### Story 4 — `/status` North Star Rewrite
**Effort: XS** | **Priority: High** | **Dependencies: Story 1**

Rewrite `status.md` to: read from `.writ/config.md`, check `.writ/state/execution-*.json` for in-flight batch jobs, surface pending `/refresh-command` opportunities, remove all phantom command references, replace with only real commands.

**Files:** `commands/status.md`

### Story 6 — Prototype → Spec Escalation Path
**Effort: S** | **Priority: Medium** | **Dependencies: None**

Add a post-escalation step to `prototype.md`: when scope escalation signals fire, offer `create-spec --from-prototype`. Add `--from-prototype` mode to `create-spec.md` that reads the current diff + implementation summary and pre-populates the discovery contract, with Story 1 pre-marked complete.

**Files:** `commands/prototype.md`, `commands/create-spec.md`

### Story 8 — ADR Unification
**Effort: S** | **Priority: Medium** | **Dependencies: None**

Update `plan-product.md` Phase 2 to output foundational decisions as numbered ADR files (ADR-000, ADR-001, etc.) rather than `decisions.md`. Update `create-adr.md` to note that product-level ADRs are seeded by `plan-product`. Add migration note: existing `decisions.md` files are not affected.

**Files:** `commands/plan-product.md`, `commands/create-adr.md`

---

## Success Criteria (Phase A)

- `/status` produces useful orientation with zero convention-detection questions on second+ run
- Agents never spiral: coding and testing agents surface `STATUS: BLOCKED` cleanly after 3 attempts, orchestrator presents repair decision
- `spec-lite.md` drift is detectable and fixable: `verify-spec` flags divergence, `--fix` regenerates
- A prototype triggering escalation signals has a clear one-command path into the structured pipeline
- `plan-product` produces ADRs, not `decisions.md` — no ambiguity about which format to use
- Phase B can begin: `.writ/config.md` format defined, status rewrite complete, iteration cap contract established

## Scope Boundaries

**Included (Phase A):**
- Stories 1, 2, 3, 4, 6, 8
- New file: `.writ/config.md` format definition (in technical spec or inline in commands)
- `--from-prototype` mode added to `create-spec.md`
- `--fix` flag added to `verify-spec.md`

**In Phase B:**
- `.writ/context.md` auto-loading (Story 5)
- Issue → spec promotion pipeline (Story 7)
- `/refresh-command` batch analysis (Story 9)

**Excluded from both phases:**
- GitHub/GitLab issue tracker sync
- Migration of existing `decisions.md` files
- Runtime code, CLI changes, or anything requiring a build step
- Changes to `user-story-generator.md` or `visual-qa-agent.md` (already A-grade, not in scope)
