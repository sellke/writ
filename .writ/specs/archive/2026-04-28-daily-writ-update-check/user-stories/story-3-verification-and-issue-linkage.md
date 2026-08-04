# Story 3: Verification and Issue Linkage

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Stories 1 and 2

## User Story

As a developer or future implementation/review agent, I want clear manual and static verification guidance for the daily Writ update check so that startup update discovery can be proven correct without mutating Writ or expanding the runtime helper.

## Acceptance Criteria

1. [x] **Given** Stories 1 and 2 have updated startup instructions and the cache/detection contract, **when** reviewers verify the feature, **then** the verification guidance covers fresh cache, same-day cache, stale cache, malformed cache, offline/upstream error, unsupported install, source repo, and linked install behavior.
2. [x] **Given** an update appears available for a copied Writ installation, **when** the startup behavior is reviewed, **then** the only user-facing action is a concise non-blocking pointer to `/update-writ`, and no update application work happens during startup.
3. [x] **Given** Writ is current, recently checked, offline, unsupported, running from the source repo, or installed through links, **when** the startup behavior is reviewed, **then** the expected result is quiet continuation of the user's original task with no misleading `/update-writ` prompt.
4. [x] **Given** `system-instructions.md` and `cursor/writ.mdc` duplicate startup behavior, **when** verification is complete, **then** the relevant update-check instructions are confirmed behaviorally synchronized across both surfaces.
5. [x] **Given** this spec was promoted from `.writ/issues/features/2026-04-28-daily-session-update-check.md`, **when** the story is completed, **then** that issue retains its original file and contains a `spec_ref` line pointing to `.writ/specs/2026-04-28-daily-writ-update-check/spec.md`.

## Implementation Tasks

1. [x] Create a manual/static verification checklist or review fixture notes for the update-check paths: no cache, same-day cache, stale cache, malformed cache, offline/upstream error, unsupported install, source repo, and linked install.
2. [x] Add verification guidance that confirms startup update discovery writes only under `.writ/state/` and never applies updates, overwrites Writ files, edits manifests, installs packages, or creates commits.
3. [x] Add a mirror-parity review step for `system-instructions.md` and `cursor/writ.mdc`, focused on the startup update-check sequence and quiet-state behavior.
4. [x] Add a runtime-boundary review step confirming `@sellke/writ` remains timestamp-only and no `update-check` command, CLI entry, package script, or runtime helper is introduced.
5. [x] Update the promoted source issue `.writ/issues/features/2026-04-28-daily-session-update-check.md` with a `spec_ref` pointing to `.writ/specs/2026-04-28-daily-writ-update-check/spec.md`, preserving the issue file rather than moving or deleting it.
6. [x] Perform final static/manual verification that `/update-writ` remains the only documented update application path and that the story's verification checklist covers every required state.

## Notes

- This story should not add application tests unless a later implementation story explicitly introduces scripts. Writ has no application test suite, so verification should stay markdown/static/manual.
- The goal is evidence, not new behavior. Stories 1 and 2 define the startup protocol and cache/detection contract; this story proves those instructions are reviewable and linked back to their source issue.
- Same-day cache and upstream failure cases should be treated as quiet paths so startup does not retry network work or interrupt the user's original request.
- Source repo and linked-install cases are especially important because recommending `/update-writ` there would send users toward a command that is intentionally inappropriate for those environments.

## Verification Checklist

Use this checklist for manual/static review of the completed startup update awareness instructions:

### Startup State Fixtures

- [x] **No cache:** Verify startup reads `.writ/state/writ-update-check.json` only if present, treats missing state as no same-day cache, and creates `.writ/state/` only when recording a result.
- [x] **Same-day cache:** Verify `last_checked_date` equal to today's local `YYYY-MM-DD` skips upstream network work and continues silently.
- [x] **Stale cache:** Verify an older `last_checked_date` allows one new lightweight upstream probe for the local day.
- [x] **Malformed cache:** Verify malformed JSON or missing `last_checked_date` is treated as no valid same-day cache, then continues through conservative eligibility checks.
- [x] **Copied install, update available:** Verify usable manifest/source metadata plus newer upstream content records `update_available` and shows only: "Writ update available. Run `/update-writ` when you are ready."
- [x] **Copied install, current:** Verify no newer upstream content records `current` and stays quiet.
- [x] **Offline/upstream error:** Verify network, timeout, auth, or upstream probe failure records `upstream_error` for the day and stays quiet.
- [x] **Unsupported install:** Verify missing manifest/source metadata, uncertain comparison, or unsupported installation shape records or skips as `skipped_unsupported` and stays quiet.
- [x] **Source repo:** Verify Writ source repo detection records or skips as `skipped_source_repo` and never recommends `/update-writ`.
- [x] **Linked install:** Verify linked installation detection records or skips as `skipped_linked_install` and never recommends `/update-writ`.

### Static Review Steps

- [x] **Mirror parity:** Compare `system-instructions.md` and `cursor/writ.mdc` `## Startup Update Awareness` sections for behavioral parity.
- [x] **Write boundary:** Confirm startup update discovery writes only under `.writ/state/` and does not commit a generated `.writ/state/writ-update-check.json` fixture.
- [x] **No mutation:** Confirm instructions forbid applying updates, overwriting Writ files, editing manifests, installing packages, cloning/pulling repositories, and creating commits.
- [x] **Runtime boundary:** Search `package.json` and `bin/writ.js` for any new update-check command, package script, or runtime helper; expected result is no runtime expansion.
- [x] **Update ownership:** Confirm `/update-writ` remains the only documented workflow that applies Writ updates and startup only points there when a copied-install update appears available.
- [x] **Issue linkage:** Confirm `.writ/issues/features/2026-04-28-daily-session-update-check.md` remains in place and contains `spec_ref: .writ/specs/2026-04-28-daily-writ-update-check/spec.md`.

## Definition of Done

- Verification guidance covers fresh cache, same-day cache, stale cache, malformed cache, offline/upstream error, unsupported install, source repo, linked install, copied-install update available, mirror parity, and runtime boundary.
- Review guidance confirms update discovery is read-only except for the daily cache under `.writ/state/`.
- Static review guidance confirms no runtime update-check command or `@sellke/writ` scope expansion was introduced.
- The promoted issue contains the correct `spec_ref` for this spec package and remains in `.writ/issues/features/`.
- The completed story gives implementation and review agents enough evidence to validate startup update discovery without running a product build or test suite.

## Context for Agents

- `spec.md` -> `Specification Contract`, `Experience Design`, and `Business Rules` define the expected startup behavior, quiet states, no-mutation rule, source-repo behavior, linked-install behavior, and `/update-writ` notification boundary.
- `spec.md` -> `Success Criteria`, `Scope Boundaries`, `Technical Concerns`, and `Recommendations` define the verification obligations for daily rate limiting, mirror parity, runtime scope, and failure-tolerant probing.
- `spec.md` -> `Relevant Files` identifies `system-instructions.md`, `cursor/writ.mdc`, `commands/update-writ.md`, `.writ/state/`, and the promoted source issue as the main review surfaces.
- `technical-spec.md` -> `Technical Strategy`, `State File Contract`, and `Detection Rules` define the ordered startup sequence, preferred cache path, allowed statuses, and decision table that verification should inspect.
- `technical-spec.md` -> `Error & Rescue Map`, `Shadow Paths`, `Interaction Edge Cases`, `File Impact Matrix`, and `Verification Plan` provide the manual/static review matrix this story should preserve.

---

## What Was Built

**Implementation Date:** 2026-04-28

### Files Created

[None created]

### Files Modified

- **`.writ/specs/2026-04-28-daily-writ-update-check/user-stories/story-3-verification-and-issue-linkage.md`** (`## Verification Checklist`)
  - Added manual/static verification coverage for cache states, copied-install behavior, quiet paths, mirror parity, write boundaries, runtime boundary, update ownership, and issue linkage.

### Implementation Decisions

1. **Verification lives in the story artifact** — The checklist was added to Story 3 rather than creating a separate ad-hoc verification file.
2. **Issue linkage was preserved** — The source issue already contained the correct `spec_ref`, so it was verified and left in place without unnecessary churn.
3. **Manual/static evidence matches repo shape** — Writ has no application test suite for this instruction-only feature, so verification relies on static searches, mirror review, and documented fixture paths.

### Test Results

**Verification:** Static/manual verification passed.
- Confirmed both instruction mirrors contain startup update awareness, cache contract, detection rules, and the exact update-available note.
- Confirmed `package.json` and `bin/writ.js` contain no update-check runtime expansion.
- Confirmed `.writ/state/writ-update-check.json` was not created.
- Confirmed the source issue contains `spec_ref: .writ/specs/2026-04-28-daily-writ-update-check/spec.md`.
- Confirmed linter diagnostics report no issues for the modified story and instruction files.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** The owned story artifact was updated; issue, runtime, instruction, and state surfaces were read only for final verification.

### Deviations from Spec

None
