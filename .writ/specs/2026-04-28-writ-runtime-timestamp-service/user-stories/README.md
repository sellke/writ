# Writ Runtime Timestamp Service - User Stories

> **Spec:** `.writ/specs/2026-04-28-writ-runtime-timestamp-service/`
> **Total Stories:** 3
> **Status:** Completed ✅
> **Total Effort:** ~1-2 days of focused work, plus npm publish access

## Stories Overview

| # | Story | Status | Priority | Effort | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Runtime Package](story-1-runtime-package.md) | Completed ✅ | High | S (~0.5-1 day) | 6 | 6/6 |
| 2 | [Command Reference Migration](story-2-command-reference-migration.md) | Completed ✅ | High | XS-S (~1-3 hours) | 6 | 6/6 |
| 3 | [Release and Verification](story-3-release-and-verification.md) | Completed ✅ | Medium | XS-S (~1-3 hours + publish gate) | 6 | 6/6 |

**Total Tasks:** 18 / 18 complete.

## Dependencies

```
Story 1 (Runtime Package)
        ↓
Story 2 (Command Reference Migration)
        ↓
Story 3 (Release and Verification)
```

- **Story 1 is first** because command docs should not point at behavior that has not been locally verified.
- **Story 2 follows Story 1** so references migrate to a known command contract.
- **Story 3 follows both** so release verification covers runtime behavior and documentation migration together.

## Story Descriptions

### Story 1: Runtime Package

Create the minimal npm package surface for `@sellke/writ`: package metadata, bin entry, `bin/writ.js`, exact-output tests, direct smoke checks, and `npm pack --dry-run` verification.

### Story 2: Command Reference Migration

Update active Writ command files from `@devobsessed/writ` to `@sellke/writ`, keeping fallback wording where timestamp helper availability should not block documentation capture.

### Story 3: Release and Verification

Document and execute the release path: tests, pack inspection, npm scope/auth guidance, publish command, and post-publish `npx` smoke checks.

## Implementation Notes

- Keep the runtime package intentionally small. Runtime scope expansion requires a separate ADR.
- Do not replace the existing install/update shell scripts with package behavior.
- Historical completed specs may retain old package references when they are evidence of past work rather than current instructions.

## Validation Plan

- Run exact-output tests for `date`, `timestamp`, and `timestamp --compact`.
- Run invalid invocation tests for stderr and exit codes.
- Run static search for stale active `@devobsessed/writ` references.
- Run `npm pack --dry-run` before publish.
- After publish, run `npx @sellke/writ date` from a clean shell context.
