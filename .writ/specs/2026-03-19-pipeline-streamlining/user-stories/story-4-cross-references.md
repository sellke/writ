# Story 4: Update Cross-References Across Pipeline Commands

> **Status:** Completed ✅
> **Priority:** Low
> **Dependencies:** Stories 1, 2, 3

## User Story

**As a** developer using Writ
**I want to** have consistent integration tables and recommended flows across all pipeline commands
**So that** no command references a workflow that no longer exists (like "run verify-spec --pre-deploy before releasing")

## Acceptance Criteria

1. **Given** all three commands are rewritten, **when** searching all command files for `verify-spec --pre-deploy`, **then** zero matches are found.

2. **Given** all three commands are rewritten, **when** searching all command files for `Trello` or `--sync-trello`, **then** zero matches are found.

3. **Given** the updated integration tables, **when** reviewing ship.md's integration section, **then** it references `/release` as the next step (not verify-spec).

4. **Given** the updated integration tables, **when** reviewing release.md's integration section, **then** the recommended flow is `/release --dry-run` then `/release` — no multi-command ceremony.

5. **Given** the updated integration tables, **when** reviewing verify-spec.md's integration section, **then** it describes itself as an independent diagnostic, not a pipeline prerequisite.

## Implementation Tasks

- [x] 4.1 Audit all command files for stale references — search `commands/*.md` for references to `verify-spec --pre-deploy`, `--sync-trello`, Trello, and the old 5-command release ceremony. List all locations.

- [x] 4.2 Update verify-spec.md integration table — reframe as independent diagnostic. Remove "run before releasing" language. Point to `/release` for release gating.

- [x] 4.3 Update release.md integration table — remove `verify-spec --pre-deploy` as prerequisite. New recommended flow: `/release --dry-run` then `/release`. Keep `/status` as optional context.

- [x] 4.4 Update ship.md integration section — ensure "When to Use" table and integration references point to `/release` as the natural next step after ship, not verify-spec.

- [x] 4.5 Check implement-spec.md and security-audit.md for stale references — these commands reference the old flow in their integration tables. Update if needed.

## Notes

- **Scope boundary:** This story only updates integration tables and cross-references. It does NOT change any command's core behavior — that's stories 1-3.

- **Risk:** Low. These are documentation cross-references, not behavioral changes. The risk is missing a reference, not breaking anything.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Zero stale references to --pre-deploy, Trello, or old ceremony across all command files
- [x] Integration tables are consistent across ship, release, and verify-spec
