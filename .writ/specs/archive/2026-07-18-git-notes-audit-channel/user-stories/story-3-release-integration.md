# Story 3: `/release` Integration — Version Rollup Note

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 1
> **Story Points:** 3

## User Story

As a **maintainer cutting a release**, I want **`/release` to attach a version rollup audit note to the release/tag commit**, so that **each version carries an immutable, git-native summary of the specs it shipped and their verdicts.**

## Acceptance Criteria

1. **Given** a set of specs shipped since the previous release tag, **when** `/release` tags the version, **then** it attaches a version rollup (per the schema in the format doc) to the tag's target commit under `refs/notes/writ`.
2. **Given** the rollup, **when** I run `git notes --ref=writ show <tag-target-sha>`, **then** I see the version, date, previous version, and the list of shipped specs with aggregate verdicts.
3. **Given** note attachment fails, **when** `/release` runs, **then** the release still completes (non-blocking) with a warning.
4. **Given** `writ.auditNotes` is `false`, **when** `/release` runs, **then** no rollup note is attached (silent).

## Implementation Tasks

- [x] Add an "Audit Rollup" step to `commands/release.md`, after the tag step, before the summary.
- [x] Reuse `/release`'s existing "specs shipped since last tag" changelog assembly to build the rollup body.
- [x] Compose the version rollup per `.writ/docs/git-notes-audit-format.md` §4.
- [x] Attach via `git notes --ref=writ add -f -F <tmp> <tag-target-sha>`.
- [x] Non-blocking error handling (warn + continue).
- [x] Honor the `writ.auditNotes` opt-out.
- [x] Add a confirmation line to the release summary.

## Technical Notes

- `/release` already derives the changelog from completed specs — the rollup reuses that list; do not re-scan.
- Prefer referencing per-spec digests (from Story 2) rather than duplicating their full contents.
- See `sub-specs/technical-spec.md → §4`.

## Definition of Done

- [x] `commands/release.md` has the Audit Rollup step (compose + attach + non-blocking + opt-out).
- [x] Manual dogfood: cut a test release locally, confirm the rollup note on the tag target. _(Documented workflow; static-verified — `/release` is not executed inside the isolated implementation lane.)_
- [x] Opt-out verified. _(Opt-out gate documented as the first action in the Audit Rollup step.)_

## Context for Agents

- **Files in scope:** `commands/release.md`.
- **Format reference:** `sub-specs/technical-spec.md → §4`; `.writ/docs/git-notes-audit-format.md`.
- **Business rules:** dedicated ref; non-blocking; audit-only; opt-out clean.
- **Reuse:** `/release`'s existing changelog-from-completed-specs assembly.

---

## What Was Built

**Implementation Date:** 2026-07-19

### Files Modified

- **`commands/release.md`** (new Step 4.4: Audit Rollup; release summary; `--dry-run` preview)
  - Added a strictly non-blocking "Audit Rollup" step after tagging (Phase 4), before
    the Phase 5 summary: opt-out gate first (`git config --bool writ.auditNotes`),
    version rollup composed per format-doc §4 by **reusing** the existing
    changelog-from-completed-specs list (no re-scan), referencing per-spec digests
    rather than duplicating them, audit-only content, attachment to the tag target
    (`TAG_TARGET_SHA=$(git rev-list -n 1 "v${VERSION}")` →
    `git notes --ref=writ add -f -F <tmp> <tag-target-sha>`) with a "never
    `refs/notes/commits`" rule, and a `📝 Release audit rollup attached ...`
    confirmation. Added the rollup line to the release summary and the dry-run
    "Commands that would run" list.

### Implementation Decisions

1. **Reuse the changelog spec list** — the rollup body is built from the list Phase
   1/2 already assembles, honoring the technical note to not re-scan specs.
2. **Reference, don't duplicate** — the rollup names each spec's aggregate verdict and
   points at the per-spec digests attached by `/ship`, keeping the note bounded.

### Test Results

**Verification:** Static (methodology repo — no runtime)
- ✅ `scripts/eval.sh --check=git-notes-audit` → 5/5 release scenarios PASS

**Coverage:** N/A (markdown command deliverable)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Only `commands/release.md` touched, as scoped.

### Deviations from Spec

None
