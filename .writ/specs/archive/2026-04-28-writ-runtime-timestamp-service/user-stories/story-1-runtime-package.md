# Story 1: Runtime Package

> **Status:** Completed ✅
> **Completed:** 2026-04-28
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** publish a tiny `@sellke/writ` runtime helper with date and timestamp commands
**So that** Writ commands can depend on a real, stable timestamp utility instead of referencing an unpublished package.

## Acceptance Criteria

- [x] Given the runtime package exists, when `node bin/writ.js date` runs, then stdout is exactly one `YYYY-MM-DD` line and exit code is 0.
- [x] Given the runtime package exists, when `node bin/writ.js timestamp` runs, then stdout is exactly one UTC `YYYY-MM-DDTHH:MM:SSZ` line and exit code is 0.
- [x] Given the runtime package exists, when `node bin/writ.js timestamp --compact` runs, then stdout is exactly one `YYYYMMDD-HHMMSS` line and exit code is 0.
- [x] Given an invalid invocation, when the CLI runs, then it prints concise usage to stderr and exits non-zero.
- [x] Given package metadata is reviewed, when `npm pack --dry-run` runs, then only expected runtime files are included.

## Implementation Tasks

- [x] 1.1 Write CLI output contract tests for `date`, `timestamp`, compact timestamp, help, and invalid invocations.
- [x] 1.2 Add root `package.json` for `@sellke/writ` with `bin`, package metadata, publish-safe `files`, and test script.
- [x] 1.3 Implement `bin/writ.js` with zero-dependency date/timestamp formatting and concise usage behavior.
- [x] 1.4 Ensure `bin/writ.js` has the correct shebang and executable permissions.
- [x] 1.5 Run local tests and direct CLI smoke checks.
- [x] 1.6 Run `npm pack --dry-run` and verify package contents.

## Notes

- This story is the product-boundary risk point. Keep the CLI file intentionally small; adding more commands requires a separate decision.
- `date` is local by design; `timestamp` and compact timestamp are UTC by design.
- Avoid third-party dependencies unless a test-only dependency is strongly justified.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** Run `date`; Run `timestamp`; Run compact timestamp; Run invalid command
- **Shadow paths:** CLI invocation
- **Business rules:** Package scope is `@sellke/writ`; runtime scope is timestamp-only; zero runtime dependencies preferred; output stability
- **Experience:** Happy path value-only stdout; error experience usage on stderr; first-use via `npx @sellke/writ date`

---

## What Was Built

**Implementation Date:** 2026-04-28

### Files Created

1. **`package.json`** (30 lines)
   - Added npm metadata for the scoped `@sellke/writ` package, the `writ` bin entry, strict package `files`, zero runtime dependencies, and Node test/pack scripts.
2. **`bin/writ.js`** (59 lines)
   - Implemented the zero-dependency CLI for local `date`, UTC `timestamp`, UTC compact timestamp, help, and invalid invocation usage behavior.
3. **`test/cli.test.js`** (64 lines)
   - Added exact-output contract tests for success paths, help, and invalid invocations using Node's built-in test runner.

### Files Modified

[None modified]

### Implementation Decisions

1. **Single binary surface** — Kept the package to one `writ` binary so `npx @sellke/writ date` resolves naturally without introducing a broader command runner.
2. **CommonJS runtime** — Used the default Node module format to avoid unnecessary package-level module semantics.
3. **Strict pack surface** — Limited published files to `bin/`, `README.md`, and `LICENSE` via `package.json` `files`.

### Test Results

**Verification:** `npm test`, direct CLI smoke checks, and `npm pack --dry-run` passed.
- ✅ `npm test`: 5/5 tests passed.
- ✅ `node bin/writ.js date`: printed `2026-04-28`.
- ✅ `node bin/writ.js timestamp`: printed a UTC timestamp without milliseconds.
- ✅ `node bin/writ.js timestamp --compact`: printed a filesystem-safe compact timestamp.
- ✅ `npm pack --dry-run`: package contents were `LICENSE`, `README.md`, `bin/writ.js`, and `package.json`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Compliant; no command references or workflow files were modified in Story 1.

### Deviations from Spec

None
