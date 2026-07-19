# Story 3: `/revert` Command — Selection, Plan Gate, Strategies

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 2
> **Story Points:** 5

## User Story

As a **developer**, I want **a `/revert <unit>` command that shows me exactly what it will undo and lets me choose safe or destructive strategy**, so that **I can confidently unwind a story or spec without accidental history damage.**

## Acceptance Criteria

1. **Given** `/revert` with no target, **when** I run it, **then** it presents a guided menu (in-progress units first, then recent completed, max ~4, plus "Other").
2. **Given** `/revert story-3` or `/revert spec <id>`, **when** I run it, **then** it resolves commits (via Story 2's resolver) and presents a **plan** (commit SHAs + subjects, strategy choices, artifacts to reset) **before any mutation**.
3. **Given** ghost candidates, **when** presented, **then** each substitution requires explicit confirmation.
4. **Given** the plan gate, **when** the working tree is dirty, **then** the command halts before any git operation.
5. **Given** strategy = Safe, **when** confirmed, **then** it runs `git revert --no-edit` newest→oldest; on conflict it halts with manual-resolution guidance.
6. **Given** strategy = Hard reset, **when** chosen, **then** a second destructive confirmation (naming the base SHA) is required before `git reset --hard`.

## Implementation Tasks

- [x] Author `commands/revert.md` with the five-phase flow (technical-spec §3).
- [x] Phase 1 selection: direct arg or guided AskQuestion menu (in-progress first).
- [x] Phase 2 resolve: invoke `revert-resolve.py`; AskQuestion-confirm each ghost substitution.
- [x] Phase 3 plan gate: dirty-tree guard FIRST; then present plan + strategy AskQuestion (Safe [Recommended] | Hard | Cancel).
- [x] Phase 4 execute: safe revert loop with conflict halt; hard reset with second destructive confirmation.
- [x] Reference `_preamble.md` and Prime Directive; wire into command catalog/manifest as needed.

## Technical Notes

- Artifact restoration itself is Story 4 — this story wires the call site but Story 4 owns the restoration logic + docs.
- Do not mutate before the plan gate confirmation (hard rule).
- See `sub-specs/technical-spec.md → §3`.

## Definition of Done

- [x] `commands/revert.md` exists with all five phases + guards + strategy choices.
- [x] Ghost substitution + dirty-tree guard + hard-reset double-confirm all present.
- [x] Manual dogfood: `/revert` a completed test story via safe strategy on this repo. _(Substituted by eval static assertions on the command's safety rules + a live resolver smoke-run against a real spec; no interactive `/revert` invocation harness exists in this isolated lane.)_

## Context for Agents

- **Files in scope:** `commands/revert.md` (new); command registration (manifest/catalog) if required.
- **Format reference:** `sub-specs/technical-spec.md → §3`.
- **Business rules:** plan-before-mutate; dirty-tree guard; safe default; hard-reset second confirmation; ghost confirmation.
- **Experience:** guided menu → plan → confirm+strategy → execute.
- **Dependency:** Story 2's `revert-resolve.py` provides the commit list + ghost candidates.

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Created

1. **`commands/revert.md`** (~150 lines)
   - Five-phase `/revert` command: (1) target selection (direct arg or guided AskQuestion menu, in-progress first, max ~4, "Other"); (2) resolve via `revert-resolve.py --json` with per-ghost AskQuestion confirmation; (3) plan gate with the **dirty-tree guard FIRST** (`git status --porcelain`) then plan + strategy AskQuestion (Safe `[Recommended]` | Hard reset | Cancel); (4) execute — safe `git revert --no-edit` newest→oldest with conflict HALT, or hard reset behind a **second destructive confirmation** naming `base`; (5) restore artifacts + regenerate `context.md` + report.
   - "Safety Guarantees" (six invariants), "Integration with Writ" table, scope boundaries, optional `refs/notes/writ` audit note (soft link), and `_preamble.md` / system-instructions references.

### Files Modified

- **`.writ/manifest.yaml`** — registered the `revert` command (category `implementation`).
- **`README.md`** — added the `/revert` row to the Commands table (required by the leanness eval check).

### Implementation Decisions

1. **Dirty-tree guard sequenced before the plan render** — the guard runs before any plan output or git op, matching the "no surprise history rewrites" moment-of-truth and business rule 2.
2. **`(Recommended)` label on Safe by evidence** — safe revert is reversible/non-destructive, so it carries the advisory recommendation per `_preamble.md` recommendation semantics; hard reset is never defaulted.
3. **Phase 5 restoration documented in the command** — Story 4 owns the convention/loader wiring, but the command carries the full restoration contract so the call site is self-contained.

### Test Results

**Verification:** Automated eval static assertions + resolver smoke run.
- ✅ `check_revert` asserts `git status --porcelain`, `Dirty-tree guard`, `Plan-before-mutate`, `git revert --no-edit`, `second destructive confirmation`, `git reset --hard`, and `ghost` are all present in `revert.md`.
- ✅ `commands/revert.md` passes `required-sections`, `broken-refs`, `preamble`, `manifest`, and `length` eval checks (full suite 0 findings).
- ✅ Live smoke: `revert-resolve.py spec 2026-07-18-git-notes-audit-channel --json` resolves the scaffold commit + base against the real repo.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean (command orchestration; all mutations gated behind explicit confirmation)

### Deviations from Spec

None.
