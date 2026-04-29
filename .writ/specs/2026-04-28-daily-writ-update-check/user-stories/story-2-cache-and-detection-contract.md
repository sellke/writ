# Story 2: Cache and Detection Contract

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

As a developer using Writ, I want the startup update check to use a clear project-local cache and conservative detection rules, so I only see an update prompt when `/update-writ` is useful and actionable.

## Acceptance Criteria

### Scenario 1: Same-day cache prevents repeated probes

**Given** `.writ/state/writ-update-check.json` contains `last_checked_date` for today's local date  
**When** Writ starts for the first invocation in a session  
**Then** the startup protocol skips upstream network work and continues silently.

### Scenario 2: Copied installs can surface useful updates

**Given** the project is a copied Writ installation with usable manifest/source metadata  
**When** the daily check finds newer upstream content than the installed version  
**Then** the cache records `update_available` and Writ shows one concise non-blocking note pointing to `/update-writ`.

### Scenario 3: Current, unsupported, and offline states stay quiet

**Given** the daily check determines the install is current, unsupported, missing source metadata, or unable to reach upstream  
**When** Writ records or skips the result for the day  
**Then** Writ does not interrupt the user's task or show an update prompt.

### Scenario 4: Source and linked installs do not recommend update-writ

**Given** Writ is running from the Writ source repo or a linked installation  
**When** startup update detection runs  
**Then** the cache records `skipped_source_repo` or `skipped_linked_install`, or skips quietly, and does not recommend `/update-writ`.

### Scenario 5: Startup remains read-only outside state

**Given** the daily update check needs to inspect cache, installation metadata, or upstream state  
**When** it runs during startup  
**Then** it writes only the daily cache under `.writ/state/` and never applies updates, edits manifests, expands `@sellke/writ`, installs packages, or changes Writ product files.

## Implementation Tasks

1. [x] Create review fixtures or documented fixture cases for no cache, same-day cache, stale cache, malformed cache, copied install with update, copied install current, source repo, linked install, unsupported install, and upstream failure.
2. [x] Define the preferred cache path `.writ/state/writ-update-check.json`, required daily-limit field, recommended metadata fields, and allowed status values in the startup instruction contract.
3. [x] Specify the startup decision order: detect Writ eligibility, read same-day cache before probing, perform at most one lightweight upstream check, record today's result, notify only on copied-install `update_available`, then resume the original task.
4. [x] Add conservative detection rules for copied installs, source repos, linked installs, unsupported installs, malformed cache, uncertain comparisons, and upstream errors.
5. [x] Ensure the contract explicitly limits startup writes to `.writ/state/` and preserves the boundary that `@sellke/writ` remains timestamp-only with no update-check runtime helper.
6. [x] Verify the finalized contract against the fixture cases, the same-day one-check behavior, quiet no-op behavior, source-repo behavior, and static search expectations for no runtime helper expansion.

## Notes

- `.writ/state/` is ephemeral and gitignored; the cache contract should be documented but the generated cache file should not be committed as product source.
- The startup check discovers update availability only. `/update-writ` remains the workflow that applies updates and handles interactive update decisions.
- Detection should prefer quiet skips over speculative prompts when manifests, source URLs, linked-install metadata, or version comparisons are incomplete.
- Cache both successful checks and upstream failures for the current local date so offline sessions do not repeatedly attempt network work.

## Definition of Done

- The daily cache shape and allowed statuses are clear enough for implementation and manual review.
- The decision rules cover copied installs, current installs, source repos, linked installs, unsupported installs, malformed cache, and upstream failures.
- Only copied-install update availability produces a user-visible `/update-writ` prompt.
- Same-day cache behavior prevents repeated upstream probes.
- The story preserves the no-mutation and no-runtime-helper boundaries from the parent spec.

## Context for Agents

- `spec.md` -> `Specification Contract`, `Experience Design`, and `Business Rules` define the product behavior, daily limit, no-mutation rule, source-repo guard, linked-install guard, and runtime boundary.
- `spec.md` -> `Success Criteria`, `Scope Boundaries`, `Technical Concerns`, and `Implementation Approach` describe the expected quiet states, relevant files, latency concern, and suggested cache example.
- `technical-spec.md` -> `Technical Strategy` defines the startup sequence from eligibility detection through notification and continuation.
- `technical-spec.md` -> `State File Contract` defines the preferred cache path, recommended fields, and allowed status values.
- `technical-spec.md` -> `Detection Rules`, `Error & Rescue Map`, and `Shadow Paths` provide the fixture matrix and conservative behavior for unsupported, linked, source-repo, and upstream-error cases.
- `technical-spec.md` -> `Interaction Edge Cases`, `File Impact Matrix`, and `Verification Plan` constrain startup ordering, missing state handling, impacted instruction files, and manual verification expectations.

---

## What Was Built

**Implementation Date:** 2026-04-28

### Files Created

[None created]

### Files Modified

- **`system-instructions.md`** (`## Startup Update Awareness`)
  - Added explicit cache contract details, malformed-cache handling, allowed statuses, and conservative detection rules to the startup update awareness instructions.
- **`cursor/writ.mdc`** (`## Startup Update Awareness`)
  - Mirrored the same cache contract and detection rules for Cursor installations.

### Implementation Decisions

1. **Cache contract stays human-readable** — The instructions name `.writ/state/writ-update-check.json`, require only `last_checked_date`, and recommend metadata/status fields without requiring a committed cache fixture.
2. **Conservative detection before notification** — Unsupported, uncertain, source-repo, linked-install, and upstream-error cases record or skip quietly; only copied-install `update_available` produces a user note.
3. **Runtime boundary remains explicit** — The contract repeats that startup writes only under `.writ/state/` and does not add an `@sellke/writ` update-check helper.

### Test Results

**Verification:** Static/manual verification passed.
- Confirmed both instruction surfaces contain the cache contract and allowed statuses.
- Confirmed no `.writ/state/writ-update-check.json` fixture was created or committed.
- Confirmed `bin/` contains no update-check runtime expansion.
- Confirmed linter diagnostics report no issues for the modified instruction files.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** All changes stayed within owned instruction files; state and runtime files were read only.

### Deviations from Spec

None
