# Story 3: `/release` Integration — Version Rollup Note

> **Status:** Not Started
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

- [ ] Add an "Audit Rollup" step to `commands/release.md`, after the tag step, before the summary.
- [ ] Reuse `/release`'s existing "specs shipped since last tag" changelog assembly to build the rollup body.
- [ ] Compose the version rollup per `.writ/docs/git-notes-audit-format.md` §4.
- [ ] Attach via `git notes --ref=writ add -f -F <tmp> <tag-target-sha>`.
- [ ] Non-blocking error handling (warn + continue).
- [ ] Honor the `writ.auditNotes` opt-out.
- [ ] Add a confirmation line to the release summary.

## Technical Notes

- `/release` already derives the changelog from completed specs — the rollup reuses that list; do not re-scan.
- Prefer referencing per-spec digests (from Story 2) rather than duplicating their full contents.
- See `sub-specs/technical-spec.md → §4`.

## Definition of Done

- [ ] `commands/release.md` has the Audit Rollup step (compose + attach + non-blocking + opt-out).
- [ ] Manual dogfood: cut a test release locally, confirm the rollup note on the tag target.
- [ ] Opt-out verified.

## Context for Agents

- **Files in scope:** `commands/release.md`.
- **Format reference:** `sub-specs/technical-spec.md → §4`; `.writ/docs/git-notes-audit-format.md`.
- **Business rules:** dedicated ref; non-blocking; audit-only; opt-out clean.
- **Reuse:** `/release`'s existing changelog-from-completed-specs assembly.
