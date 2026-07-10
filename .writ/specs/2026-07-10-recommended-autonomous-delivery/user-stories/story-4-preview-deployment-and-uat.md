# Story 4: PR Preview Deployment and Staged UAT

> **Status:** Completed ✅ (2026-07-10)
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** Writ user/reviewer
**I want to** review an auditable PR, successful required CI, an existing preview deployment, and enriched UAT evidence before giving one explicit production approval
**So that** merge and release are authorized only for the exact validated PR head SHA without bypassing provider protections or provisioning infrastructure

## Acceptance Criteria

- [x] Given Story 3 has completed verified implementation, when recommended delivery enters staging, then it uses `/ship --test` semantics to create or recover one PR by branch, persists the PR identifier and head SHA, and records the evidence-based commit grouping in the recommendation log.
- [x] Given the PR is open, when Writ discovers its required checks, then it waits until every required check succeeds and preserves an actionable resumable state on failure, timeout, authentication failure, or interruption without merging the PR.
- [x] Given required CI has succeeded, when Writ discovers preview evidence, then it consumes an existing configured project or provider deployment, persists its URL and identifiers, and pauses with setup guidance if no preview capability exists without provisioning hosting or bypassing protection.
- [x] Given the completed implementation and preview are available, when staged UAT is prepared, then `uat-plan.md` derives scenarios from the completed implementation and is enriched with the preview URL, validation instructions, CI result, and material warnings.
- [x] Given the PR, successful CI, preview URL, UAT plan, recommended version bump, and release consequences are presented, when the user explicitly approves production, then approval is persisted for that exact PR head SHA and any later head change invalidates it and returns the workflow to CI, preview, and UAT validation.

## Implementation Tasks

- [x] 4.1 Write eval fixtures in `scripts/eval.sh` for successful PR-to-approval staging, failed or timed-out CI, missing preview capability, interrupted resume, duplicate PR prevention, approval rejection, and approval invalidation after a PR head change.
- [x] 4.2 Extend `commands/ship.md` so recommended delivery uses test semantics, selects and logs commit grouping, creates or recovers the PR idempotently by branch, and returns the persisted PR identifier and head SHA without merging.
- [x] 4.3 Add provider-neutral required-check discovery, durable waiting, terminal-success enforcement, and safe blocker/resume outcomes to `commands/implement-spec.md`, with equivalent capability mappings in `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/codex.md`.
- [x] 4.4 Implement existing preview deployment discovery and persistence through configured project conventions or provider metadata, including actionable no-preview guidance and explicit prohibitions on provisioning infrastructure or bypassing provider policy.
- [x] 4.5 Update `commands/create-uat-plan.md` and the recommended orchestration path to derive scenarios from completed implementation, enrich `uat-plan.md` with preview and CI evidence, and collect one explicit production approval bound to the current PR head SHA.
- [x] 4.6 Verify all acceptance criteria, state transitions, audit entries, blocker messages, and cross-platform semantics against the locked specification.
- [x] 4.7 Verify all eval fixtures and applicable dry-run/manual validation pass, including resume and duplicate-prevention paths.

## Notes

- Story 3 supplies the active recommendation mode, verified implementation outcome, durable execution state, and recommendation log. This story must extend those artifacts rather than introduce a second staging state machine.
- `/ship` currently creates but does not merge a PR. Preserve that boundary here: Story 4 ends with production approval, while Story 5 owns merge and release.
- `commands/create-uat-plan.md` must continue deriving scenarios from completed implementation; preview URL, CI evidence, validation instructions, and warnings enrich that output rather than replacing implementation-derived coverage.
- Provider integrations are capability adapters, not infrastructure managers. Writ may discover an existing preview deployment but must never create hosting accounts, projects, secrets, or environments, and must never bypass branch protection or platform approval.
- External waits and mutations need durable provider identifiers, preflight lookups, and reconciliation on resume. Stale or contradictory PR, check, deployment, or SHA evidence must stop safely.
- Approval is a production authorization, not a CI result or timeout default. Rejection or requested changes returns to implementation with recommendation mode retained; a changed head SHA always invalidates prior approval.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [No preview deployment — `spec.md` → `## Experience Design` → `### Error Experience`; CI failure — `spec.md` → `## Experience Design` → `### Error Experience`; Interrupted session — `spec.md` → `## Experience Design` → `### Error Experience`; Critical ambiguity — `spec.md` → `## Experience Design` → `### Error Experience`]
- **Shadow paths:** [PR open → Waiting for CI → Preview ready → Awaiting approval — `spec.md` → `## Experience Design` → `### State Catalog`; Commit → open PR → await CI → discover preview → await approval — `spec.md` → `## Implementation Approach` → `### Explicit State Machine`]
- **Business rules:** [Reuse existing preview/stage integration; do not provision infrastructure — `spec.md` → `## Specification Contract` → `### Business Rules` rules 6–7; Production approval must be explicit — `spec.md` → `## Specification Contract` → `### Business Rules` rule 8; Never bypass platform approvals or branch protections — `spec.md` → `## Specification Contract` → `### Business Rules` rule 12; Enforce idempotent PR, successful required checks, and existing preview discovery — `spec.md` → `## Detailed Requirements` → `### R5 — PR, CI, and Preview Validation`; Bind approval to the exact reviewed PR head SHA and invalidate it on change — `spec.md` → `## Detailed Requirements` → `### R6 — Production Approval`]
- **Experience:** [Moment of truth: inspect the working preview and decision history before production authorization — `spec.md` → `## Specification Contract` → `### Experience Design`; Preview and approval feedback states — `spec.md` → `## Experience Design` → `### State Catalog`; Approval prompt contents and consequences — `spec.md` → `## Detailed Requirements` → `### R6 — Production Approval`]

---

## What Was Built

**Implementation Date:** 2026-07-10

### Files Created

1. **`scripts/eval-recommend-stage.py`** — Provider-fake staging scenarios for PR, CI, preview, UAT, and approval.

### Files Modified

- **`scripts/recommend-state.py`** — Activated v1 staging fields; added at-most-once PR mutation/audit, authenticated-check enforcement, provenance consistency, implementation-derived UAT derivation, freshness-validated approval.
- **`commands/ship.md`** — Internal recommended branch: mandatory test semantics, evidence-based commit grouping, idempotent PR find/create.
- **`commands/implement-spec.md`** — Staging continuation; provider-neutral check discovery and durable wait; pre-approval reconciliation; structured `production_approved` return.
- **`commands/create-uat-plan.md`** — Internal recommended branch: derive from completed implementation; enrich with preview/CI/warnings; approval prompt wiring.
- **`adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`** — Concrete PR/check/preview/approval capability mappings.
- **`.writ/docs/config-format.md`** — Added Delivery Provider/Remote, Preview Provider/Project/Evidence Source/URL Pattern, Required Checks, CI/Preview Wait Timeout.
- **`.writ/docs/recommended-delivery-state-format.md`** — Activated staging state tokens; result schema updated with `production_approved` and staging resume states.
- **`scripts/eval.sh`**, **`.writ/manifest.yaml`**, **`SKILL.md`** — Catalog and static assertions.

### Implementation Decisions

1. **Single v1 state machine** — Activated reserved staging fields; no second state file.
2. **Provider-neutral local reducer** — All provider I/O in adapters; reducer enforces normalized evidence only.
3. **Audit sequencing** — No staging transition may occur while a mutation audit entry is pending.
4. **Strict SHA binding** — PR, checks, preview, UAT, and approval all bind to one full immutable head SHA.

### Test Results

**Verification:** 60/60 Story 4 staging scenarios, 50/50 Story 3 adversarial regressions, all syntax/compile/diff checks passed.

- ✅ All 6 adversarial false-positive regressions blocked.
- ✅ Pending audit, stale timestamp, unauthenticated checks, provenance contradiction, unbound commit SHAs all block.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iterations
- **Drift:** None
- **Security:** Low risk; no real provider calls
- **Boundary Compliance:** Compliant; no merge/release/version/tag/npm/provisioning

### Deviations from Spec

None
