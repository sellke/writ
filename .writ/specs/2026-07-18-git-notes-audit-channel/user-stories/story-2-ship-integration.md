# Story 2: `/ship` Integration — Attach Spec-Level Audit Digest

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1
> **Story Points:** 5

## User Story

As a **developer shipping a spec**, I want **`/ship` to attach an audit digest to the commit that lands on the base branch**, so that **the review verdict, coverage, and drift for that spec are permanently recorded in git on the surviving commit — not orphaned by squash-merge.**

## Acceptance Criteria

1. **Given** a spec whose stories have WWB records, **when** `/ship` lands the branch (squash, merge, or rebase), **then** Writ attaches the spec-level digest to the **landed** commit under `refs/notes/writ`, and `git log --notes=writ` shows it.
2. **Given** a squash-merge (new SHA), **when** the note is attached, **then** it is on the squash commit — never on an orphaned pre-merge story commit.
3. **Given** no WWB records exist, **when** `/ship` runs, **then** a minimal digest (spec ref + landed SHA + `git diff --stat`) is attached and a warning is logged.
4. **Given** `git notes add` fails, **when** `/ship` runs, **then** the ship still succeeds and a `⚠️ audit note not attached` warning is shown (non-blocking).
5. **Given** `writ.auditNotes` is `false`, **when** `/ship` runs, **then** no note is composed or attached (silent no-op).

## Implementation Tasks

- [ ] Add a terminal "Audit Note" step to `commands/ship.md`, after the merge/land step, before the final report.
- [ ] Resolve the landed SHA per land strategy (squash / merge commit / rebase tip) — document each case.
- [ ] Compose the spec-level digest per `.writ/docs/git-notes-audit-format.md` from the spec's story WWB records; aggregate verdict/drift/coverage/files.
- [ ] Attach via `git notes --ref=writ add -f -F <tmp> <landed-sha>`; overwrite on re-ship.
- [ ] Implement fallback minimal digest when no WWB records are found.
- [ ] Wrap attachment in non-blocking error handling (warn + continue).
- [ ] Honor the `writ.auditNotes` opt-out (skip silently when false).
- [ ] Add a one-line confirmation to `/ship`'s report: `📝 Audit note attached to <sha> (refs/notes/writ)`.

## Technical Notes

- `/ship` already tracks the branch/PR and spec context and performs the land — reuse that; only add the post-land note step.
- See `sub-specs/technical-spec.md → §2 (attach-point resolution), §3 (digest schema)`.
- Content must be audit-only (no CoT/prompts/transcripts).

## Definition of Done

- [ ] `commands/ship.md` has the Audit Note step with all four land cases + fallback + non-blocking + opt-out.
- [ ] Manual dogfood on this repo: `/ship` a spec, confirm `git log --notes=writ` shows the digest on the landed commit.
- [ ] Opt-out verified: `writ.auditNotes=false` → no note.

## Context for Agents

- **Files in scope:** `commands/ship.md`.
- **Format reference:** `sub-specs/technical-spec.md → §2, §3`; `.writ/docs/git-notes-audit-format.md` (from Story 1).
- **Business rules:** attach to surviving commit; dedicated ref; non-blocking; audit-only; opt-out clean.
- **Shadow paths:** happy (WWB → digest), nil (no WWB → minimal), upstream error (`git notes` fails → warn+continue).
- **Dependency WWB:** Story 1 defines the digest schema this story emits.
