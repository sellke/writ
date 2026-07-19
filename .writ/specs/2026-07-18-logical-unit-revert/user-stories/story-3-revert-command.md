# Story 3: `/revert` Command — Selection, Plan Gate, Strategies

> **Status:** Not Started
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

- [ ] Author `commands/revert.md` with the five-phase flow (technical-spec §3).
- [ ] Phase 1 selection: direct arg or guided AskQuestion menu (in-progress first).
- [ ] Phase 2 resolve: invoke `revert-resolve.py`; AskQuestion-confirm each ghost substitution.
- [ ] Phase 3 plan gate: dirty-tree guard FIRST; then present plan + strategy AskQuestion (Safe [Recommended] | Hard | Cancel).
- [ ] Phase 4 execute: safe revert loop with conflict halt; hard reset with second destructive confirmation.
- [ ] Reference `_preamble.md` and Prime Directive; wire into command catalog/manifest as needed.

## Technical Notes

- Artifact restoration itself is Story 4 — this story wires the call site but Story 4 owns the restoration logic + docs.
- Do not mutate before the plan gate confirmation (hard rule).
- See `sub-specs/technical-spec.md → §3`.

## Definition of Done

- [ ] `commands/revert.md` exists with all five phases + guards + strategy choices.
- [ ] Ghost substitution + dirty-tree guard + hard-reset double-confirm all present.
- [ ] Manual dogfood: `/revert` a completed test story via safe strategy on this repo.

## Context for Agents

- **Files in scope:** `commands/revert.md` (new); command registration (manifest/catalog) if required.
- **Format reference:** `sub-specs/technical-spec.md → §3`.
- **Business rules:** plan-before-mutate; dirty-tree guard; safe default; hard-reset second confirmation; ghost confirmation.
- **Experience:** guided menu → plan → confirm+strategy → execute.
- **Dependency:** Story 2's `revert-resolve.py` provides the commit list + ghost candidates.
