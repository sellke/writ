# Story 2: Command Reference Migration

> **Status:** Completed ✅
> **Completed:** 2026-04-28
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ command user
**I want to** see command instructions reference `@sellke/writ`
**So that** date and timestamp guidance points at the package Writ actually owns and can publish.

## Acceptance Criteria

- [x] Given active command files reference `@devobsessed/writ`, when this story is complete, then those active references are replaced with `@sellke/writ`.
- [x] Given a command should not fail hard on timestamp helper availability, when its date guidance is updated, then it includes local system date fallback wording.
- [x] Given historical completed specs mention the old package, when migration is complete, then only historical/archive references remain or they are explicitly left untouched.
- [x] Given the migration is complete, when searching active command files, then no active execution instruction points at `@devobsessed/writ`.

## Implementation Tasks

- [x] 2.1 Search active product files for `@devobsessed/writ`, `@sellke/writ`, and timestamp/date helper language.
- [x] 2.2 Update `commands/create-spec.md` to use `npx @sellke/writ date` for spec folder naming.
- [x] 2.3 Update `commands/research.md` and `commands/create-adr.md` to use `@sellke/writ` with fallback wording where appropriate.
- [x] 2.4 Update `commands/knowledge.md` to prefer `@sellke/writ` and keep its local-date fallback.
- [x] 2.5 Review adjacent docs or generated examples that new users are likely to copy.
- [x] 2.6 Run a static search and capture the remaining reference rationale.

## Notes

- Do not rewrite historical validation reports just to erase the old string. The goal is to fix current executable guidance.
- If a command needs a filesystem-safe timestamp rather than a date, use `npx @sellke/writ timestamp --compact`.
- Keep command language adapter-neutral. The package is a helper, not a platform-specific hook.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** Execute Writ command before publish; Command docs
- **Shadow paths:** Command docs
- **Business rules:** Fallback rule; package scope; markdown-first Writ identity
- **Experience:** Moment of truth is no command referencing a nonexistent package; error experience allows local fallback

---

## What Was Built

**Implementation Date:** 2026-04-28

### Files Created

[None created]

### Files Modified

- **`commands/create-spec.md`** (Step 2.2 date guidance)
  - Replaced the unpublished package reference with `npx @sellke/writ date` and added local system date fallback wording.
- **`commands/research.md`** (Output date guidance)
  - Replaced the date helper reference and added local system date fallback wording.
- **`commands/create-adr.md`** (Step 4 ADR preparation)
  - Replaced the date helper command and added a fallback sentence for local system date.
- **`commands/knowledge.md`** (Step 5 entry creation)
  - Replaced the package reference while preserving the existing local-date fallback.

### Implementation Decisions

1. **Active commands only** — Left historical `.writ/specs/` references intact because they document past validation and story context rather than current executable instructions.
2. **Fallback everywhere date capture is non-critical** — Added local system date fallback wording to prevent unpublished-package or transient npm failures from blocking methodology work.

### Test Results

**Verification:** Static command-reference checks and lints passed.
- ✅ `rg "@devobsessed/writ" commands`: no matches.
- ✅ `rg "@devobsessed/writ|@sellke/writ" commands`: only expected `@sellke/writ` references in active command files.
- ✅ ReadLints: no errors in modified command files.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Compliant; changes were limited to the four active command docs.

### Deviations from Spec

None
