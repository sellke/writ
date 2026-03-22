# Story 5: Move Project-Specific Commands to `contrib/`

> **Status:** Completed ✅ (2026-03-22)
> **Priority:** Low
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** separate project-specific utility commands from the core command suite
**So that** the core suite only contains universally applicable commands

## Acceptance Criteria

- [x] Given the `contrib/` directory, when I list its contents, then `prisma-migration.md` and `test-database.md` are present
- [x] Given the `commands/` directory, when I list its contents, then `prisma-migration.md` and `test-database.md` are absent
- [x] Given the `/status` command allowlist, when I read it, then `prisma-migration` and `test-database` are removed from both allowlist locations
- [x] Given `commands/migrate.md`, when I check its location, then it remains in `commands/` (not moved)

## Implementation Tasks

- [x] 5.1 Create `contrib/` directory at the project root
- [x] 5.2 Move `commands/prisma-migration.md` to `contrib/prisma-migration.md`
- [x] 5.3 Move `commands/test-database.md` to `contrib/test-database.md`
- [x] 5.4 Remove `prisma-migration` and `test-database` from both command allowlist locations in `commands/status.md` (Step 9 and Maintainer Note)
- [x] 5.5 Scan all command files for cross-references to these two commands and update or remove references

## Notes

- Use `git mv` for the moves so git tracks the rename
- `/migrate` stays in `commands/` — it's part of the install/onboarding story for Code Captain users
- The `contrib/` directory signals "useful examples, not core suite"
- Check if `SKILL.md` or any adapter files reference these commands

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `commands/` contains only universally applicable commands
- [x] No broken cross-references
