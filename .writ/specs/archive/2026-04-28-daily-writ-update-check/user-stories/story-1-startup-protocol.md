# Story 1: Startup Update Check Protocol

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

As a developer using Writ in Cursor or another supported AI coding environment, I want Writ to perform a quiet daily update awareness check before startup orientation or command workflows, so I can learn when an upstream Writ update is available without startup applying changes or interrupting my task.

## Acceptance Criteria

1. [x] **Given** a first Writ invocation in a session and no same-day update check cache, **when** startup behavior begins, **then** Writ checks update awareness before session auto-orientation or any command-specific workflow.
2. [x] **Given** `.writ/state/writ-update-check.json` records today's local date, **when** Writ starts again that day, **then** startup skips upstream network work and continues silently.
3. [x] **Given** a copied Writ installation with sufficient manifest/source metadata and an upstream update appears available, **when** the daily startup check runs, **then** Writ shows one concise non-blocking message pointing the user to `/update-writ`.
4. [x] **Given** Writ is current, offline, unsupported, running from the Writ source repo, running from a linked installation, or already being updated via `/update-writ`, **when** startup runs, **then** Writ produces no update prompt and continues the original user workflow.
5. [x] **Given** the startup update check runs in any state, **when** it records or skips update awareness, **then** it never applies updates, overwrites Writ files, edits manifests, installs packages, creates commits, or expands the `@sellke/writ` runtime beyond timestamp utilities.

## Implementation Tasks

1. [x] Review the current startup/session auto-orientation instructions in `system-instructions.md` and `cursor/writ.mdc`, plus `/update-writ` behavior, to identify the exact mirrored insertion point.
2. [x] Define lightweight review fixtures or manual scenarios for no cache, same-day cache, stale cache, update available, current, offline/upstream error, source repo, linked install, unsupported install, and `/update-writ` invocation.
3. [x] Add the daily startup update awareness protocol to `system-instructions.md` before session auto-orientation and command-specific workflow guidance.
4. [x] Mirror the same startup update awareness protocol in `cursor/writ.mdc`, keeping wording and behavior synchronized with `system-instructions.md`.
5. [x] Ensure the protocol specifies concise update-available messaging, quiet no-op behavior for non-actionable states, and that `.writ/state/` may be created only when recording a check result.
6. [x] Confirm the instruction text preserves the runtime boundary by avoiding any new `@sellke/writ` update-check command, manifest mutation, update application, or startup file overwrite behavior.
7. [x] Verify the mirrored startup rules, fixture coverage, quiet paths, update-available prompt, `/update-writ` ownership, and unchanged timestamp-only runtime boundary.

## Notes

- This story is instruction-only. It changes startup behavior guidance, not runtime code.
- Startup update discovery is informational and non-blocking. `/update-writ` remains the only update application workflow.
- The daily cache should live under `.writ/state/`, which is ephemeral and gitignored.
- In the Writ source repository and linked installations, startup must not recommend `/update-writ`.
- The protocol should preserve the user's original request as the main task after the update check completes or skips.

## Definition of Done

- `system-instructions.md` and `cursor/writ.mdc` contain synchronized startup update-check instructions.
- The update check runs before session auto-orientation or command-specific workflows on first Writ invocation when the daily cache permits.
- Only copied installations with an apparent upstream update receive a concise `/update-writ` note.
- Current, recently checked, offline, unsupported, source-repo, linked-install, and `/update-writ` invocation paths remain quiet.
- Startup update discovery never applies updates or mutates installed Writ files.
- Static review confirms the `@sellke/writ` runtime remains timestamp-only.

## Context for Agents

- `spec.md` lines 10-23 define the contract, required startup protocol, concise `/update-writ` messaging, quiet paths, no-mutation rule, and runtime boundary.
- `spec.md` lines 25-43 define the expected startup experience, daily cache behavior, first-use state handling, and business rules for copied, source, and linked installations.
- `spec.md` lines 60-68 list success criteria for daily limiting, quiet states, no mutation, runtime scope, and synchronized instruction surfaces.
- `spec.md` lines 119-135 recommend an instruction-only implementation approach and a small human-readable `.writ/state/` cache.
- `technical-spec.md` lines 6-18 define the startup sequence and ordering before auto-orientation or command workflows.
- `technical-spec.md` lines 20-50 define the preferred cache path, recommended fields, and allowed statuses.
- `technical-spec.md` lines 52-75 define detection rules and read-only upstream probe constraints.
- `technical-spec.md` lines 76-107 define failure handling, fixture scenarios, shadow paths, and interaction edge cases.
- `technical-spec.md` lines 108-124 identify impacted files and verification requirements.

---

## What Was Built

**Implementation Date:** 2026-04-28

### Files Created

[None created]

### Files Modified

- **`system-instructions.md`** (`## Startup Update Awareness`)
  - Added the first-in-session daily update awareness protocol before session auto-orientation, including the ordered startup sequence, quiet paths, copied-install notification, `.writ/state/` write boundary, and runtime no-mutation constraints.
- **`cursor/writ.mdc`** (`## Startup Update Awareness`)
  - Mirrored the same startup protocol and notification behavior for Cursor installations.

### Implementation Decisions

1. **Instruction-only implementation** — The startup check is expressed as Writ startup guidance rather than a new runtime command, preserving `@sellke/writ` as timestamp-only.
2. **Protocol before auto-orientation** — The new section sits immediately before `Session Auto-Orientation` so it applies to both plain startup orientation and command invocations.
3. **Quiet by default** — The only visible message is copied-install `update_available`; current, unsupported, source-repo, linked-install, offline, same-day cache, and `/update-writ` invocations continue silently.

### Test Results

**Verification:** Static/manual verification passed.
- Confirmed `system-instructions.md` and `cursor/writ.mdc` contain matching `## Startup Update Awareness` sections.
- Confirmed the update-available message points to `/update-writ`.
- Confirmed `bin/` contains no update-check runtime expansion.
- Confirmed linter diagnostics report no issues for the modified instruction files.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** All changes stayed within owned files; runtime files remained read-only for verification.

### Deviations from Spec

None
