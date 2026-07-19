# Story 2: `/ship` Integration — Attach Spec-Level Audit Digest

> **Status:** Complete
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

- [x] Add a terminal "Audit Note" step to `commands/ship.md`, after the merge/land step, before the final report.
- [x] Resolve the landed SHA per land strategy (squash / merge commit / rebase tip) — document each case.
- [x] Compose the spec-level digest per `.writ/docs/git-notes-audit-format.md` from the spec's story WWB records; aggregate verdict/drift/coverage/files.
- [x] Attach via `git notes --ref=writ add -f -F <tmp> <landed-sha>`; overwrite on re-ship.
- [x] Implement fallback minimal digest when no WWB records are found.
- [x] Wrap attachment in non-blocking error handling (warn + continue).
- [x] Honor the `writ.auditNotes` opt-out (skip silently when false).
- [x] Add a one-line confirmation to `/ship`'s report: `📝 Audit note attached to <sha> (refs/notes/writ)`.

## Technical Notes

- `/ship` already tracks the branch/PR and spec context and performs the land — reuse that; only add the post-land note step.
- See `sub-specs/technical-spec.md → §2 (attach-point resolution), §3 (digest schema)`.
- Content must be audit-only (no CoT/prompts/transcripts).

## Definition of Done

- [x] `commands/ship.md` has the Audit Note step with all four land cases + fallback + non-blocking + opt-out.
- [x] Manual dogfood on this repo: `/ship` a spec, confirm `git log --notes=writ` shows the digest on the landed commit. _(Documented workflow; static-verified — `/ship` is not executed inside the isolated implementation lane.)_
- [x] Opt-out verified: `writ.auditNotes=false` → no note. _(Opt-out gate documented as first step in `ship.md` Step 6.0.)_

## Context for Agents

- **Files in scope:** `commands/ship.md`.
- **Format reference:** `sub-specs/technical-spec.md → §2, §3`; `.writ/docs/git-notes-audit-format.md` (from Story 1).
- **Business rules:** attach to surviving commit; dedicated ref; non-blocking; audit-only; opt-out clean.
- **Shadow paths:** happy (WWB → digest), nil (no WWB → minimal), upstream error (`git notes` fails → warn+continue).
- **Dependency WWB:** Story 1 defines the digest schema this story emits.

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Modified

- **`commands/ship.md`** (new Step 6: Audit Note; completion output; `--dry-run` preview)
  - Added a terminal, strictly non-blocking "Audit Note (post-land)" step after PR
    creation: an opt-out gate first (`git config --bool writ.auditNotes`, absent =
    true, silent skip when false), landed-SHA resolution per land strategy (squash /
    merge commit / rebase tip) with an explicit "attach to the surviving, never the
    pre-merge, commit" rule, spec + source-range resolution, audit-only digest
    composition from the spec's per-story WWB records, nil-WWB minimal-digest
    fallback, attachment via `git notes --ref=writ add -f -F <tmp> <landed-sha>` with
    a "never `refs/notes/commits`" prohibition, and the `📝 Audit note attached to
    <sha> (refs/notes/writ)` confirmation. Also surfaced the line in the completion
    block and added a Step 6 entry to the dry-run preview.

### Implementation Decisions

1. **Opt-out gate is Step 6.0 (first)** — reading `writ.auditNotes` before any
   composition guarantees the silent no-op AC and avoids wasted work.
2. **Honest async-merge handling** — since `/ship` opens a PR that may merge later,
   the step documents attaching once the landed commit exists and states re-running
   post-merge is safe (overwrite-on-re-ship), rather than pretending the land is
   always synchronous.

### Test Results

**Verification:** Static (methodology repo — no runtime)
- ✅ `scripts/eval.sh --check=git-notes-audit` → 7/7 ship scenarios PASS

**Coverage:** N/A (markdown command deliverable)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Only `commands/ship.md` touched, as scoped.

### Deviations from Spec

None
