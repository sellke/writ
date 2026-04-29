# Story 3: Release and Verification

> **Status:** Completed ✅
> **Completed:** 2026-04-28
> **Priority:** Medium
> **Dependencies:** Stories 1 and 2

## User Story

**As a** Writ maintainer
**I want to** verify and publish `@sellke/writ` safely
**So that** command users can run `npx @sellke/writ date` with confidence and the package does not accidentally expand Writ's runtime surface.

## Acceptance Criteria

- [x] Given the package is ready, when release verification runs, then tests, direct CLI smoke checks, and `npm pack --dry-run` all pass.
- [x] Given the package is scoped, when publish instructions are followed, then they account for `npm publish --access public`.
- [x] Given the changelog is updated, when users read the release note, then it describes a runtime timestamp helper rather than a general Writ CLI.
- [x] Given the release is complete, when `npx @sellke/writ date` is run from a clean environment, then it resolves and prints the expected date format.

## Implementation Tasks

- [x] 3.1 Add or update release documentation for testing, packing, and publishing `@sellke/writ`.
- [x] 3.2 Add package release checklist items to the relevant release/changelog workflow.
- [x] 3.3 Verify npm scope/auth requirements are documented without hardcoding private credentials or tokens.
- [x] 3.4 Run tests, CLI smoke checks, and `npm pack --dry-run`.
- [x] 3.5 Publish the package when credentials are available.
- [x] 3.6 Smoke test `npx @sellke/writ date`, `timestamp`, and compact timestamp after publish.

## Notes

- Publishing may require a human with npm access to the `@sellke` scope. The implementation should prepare everything up to that gate and make the remaining manual step explicit.
- Keep credentials out of the repo. Use npm's normal authentication flow.
- If the package publish fails because the scope is unavailable, stop and report the exact blocker.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** Publish package; Execute Writ command before publish
- **Shadow paths:** Release; CLI invocation
- **Business rules:** Publish under `@sellke/writ`; package remains timestamp-only; no credentials in source
- **Experience:** First-use via npx; concise release language; fallback guidance until package is available

---

## What Was Built

**Implementation Date:** 2026-04-28

### Files Created

[None created]

### Files Modified

- **`commands/release.md`** (release gate and publish workflow)
  - Added conditional `@sellke/writ` package preflight checks, scoped public publish guidance, npm auth/2FA handling, and post-publish `npx` smoke checks.
- **`CHANGELOG.md`** (Unreleased entry)
  - Added release notes describing the package as a runtime timestamp helper and documenting the active command reference migration.

### Implementation Decisions

1. **Publish as a conditional release step** — Kept npm publishing scoped to repos whose root `package.json` is `@sellke/writ` instead of turning `/release` into a general npm publishing framework.
2. **Human npm auth gate** — Documented `npm whoami`, 2FA, and `npm publish --access public` without storing credentials or tokens in source.
3. **Registry smoke from clean context** — Verified `npx` resolution from a temporary directory so the checks used the published package rather than local files.

### Test Results

**Verification:** Local release checks, publish, and post-publish smoke checks passed.
- ✅ `npm test`: 5/5 tests passed.
- ✅ Direct CLI smoke checks passed for `date`, `timestamp`, and `timestamp --compact`.
- ✅ `npm pack --dry-run`: package contents were `LICENSE`, `README.md`, `bin/writ.js`, and `package.json`.
- ✅ `npm view @sellke/writ version`: returned `0.14.0`.
- ✅ Clean `npx --yes @sellke/writ date`: printed `2026-04-28`.
- ✅ Clean `npx --yes @sellke/writ timestamp`: printed a UTC timestamp without milliseconds.
- ✅ Clean `npx --yes @sellke/writ timestamp --compact`: printed a filesystem-safe compact timestamp.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Compliant; no credentials were added and the package remains timestamp-only.

### Deviations from Spec

None
