# Story 2 — Changelog Entry and Version Bump

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

As a **Writ maintainer**, I want the changelog and version updated so that this behavioral improvement is documented and shipped as a proper release.

## Acceptance Criteria

- [ ] **Given** the prime directive has been inlined (Story 1), **when** this story is complete, **then** `CHANGELOG.md` has a new entry under `## [0.7.0]` documenting the change.
- [ ] **Given** the current version is `0.6.1`, **when** this story is complete, **then** `VERSION` reads `0.7.0`.
- [ ] **Given** the changelog entry, **when** reading it, **then** it describes the prime directive addition and the phantom reference removal in user-facing language.

## Implementation Tasks

- [ ] Write the changelog entry: Added section for prime directive, note about phantom reference fix
- [ ] Prepend entry to `CHANGELOG.md` after the header, before existing entries
- [ ] Update `VERSION` file from `0.6.1` to `0.7.0`
- [ ] Verify changelog follows Keep a Changelog format
- [ ] Verify version string is clean (no trailing newline issues)

## Notes

- **Version bump rationale:** Minor version (0.7.0) because this adds new behavioral content to the system instructions — it's a feature addition (new Prime Directive section), not a bug fix. It doesn't break anything but meaningfully changes agent behavior.
- The changelog entry should reference the research document for users who want the background.

## Definition of Done

- [ ] `CHANGELOG.md` has the new entry in correct format
- [ ] `VERSION` reads `0.7.0`
- [ ] Both files are well-formed
