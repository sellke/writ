# Story 6: Phase Progress and Production Health

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Stories 4, 5

## User Story

**As a** Writ maintainer monitoring phase execution and project health
**I want to** see current phase progress, isolated-lane disposition, and categorical health from the latest local evidence
**So that** I can identify failures, blocks, quarantine, and stale or inconsistent project evidence quickly without triggering heavyweight or mutating work

## Acceptance Criteria

- [ ] Given an in-flight `phase-execution-*.json` file, when `/status` runs, then it reports the phase, current spec and active lane, completed/failed/blocked counts, and quarantine branches.
- [ ] Given current passing eval and verification evidence, no unresolved material drift, and phase state consistent with named git branches, when `/status` computes health, then it reports `Healthy` and identifies the evidence used.
- [ ] Given any required local eval, verification, drift, or state-consistency evidence is missing or stale, when `/status` computes health, then it reports `Warning`, names each missing or stale input and its age when known, and does not characterize missing evidence as a failure.
- [ ] Given a current failed check, unresolved material drift, or phase-state/git mismatch, when `/status` computes health, then it reports `Attention` with the specific evidence requiring action.
- [ ] Given status is requested in any supported phase state, when `/status` gathers progress and health, then it completes within 10 seconds without invoking `/verify-spec`, builds, tests, network calls, CI APIs, or mutating commands.

## Implementation Tasks

- [ ] 6.1 Write focused fixtures and contract tests for `commands/status.md` covering active phase progress, quarantine and blocked counts, all three health categories, mixed-age evidence, missing evidence, and phase-state/git mismatch.
- [ ] 6.2 Extend `commands/status.md` to discover and read the newest relevant `phase-execution-*.json` state and render current spec, active lane, progress counts, failures, blocks, and quarantine branches.
- [ ] 6.3 Add categorical health aggregation to `commands/status.md` using the latest local eval summary, `verification-*.md` report, relevant drift entries, and phase-state consistency with named git branches, including source freshness and unavailable-input details.
- [ ] 6.4 Update `scripts/eval.sh`, `commands/verify-spec.md`, and `commands/implement-phase.md` only as needed to persist lightweight local summaries that `/status` can consume without rerunning deep diagnostics.
- [ ] 6.5 Document status-readable progress, evidence freshness, and compatible state-summary fields in `.writ/docs/phase-execution-state-format.md`, preserving unknown fields and the ephemeral `.writ/state/` boundary.
- [ ] 6.6 Verify fixture output for phase progress, `Healthy`, `Warning`, and `Attention`, including the rule that mixed-age or absent evidence cannot exceed `Warning` unless separate current failure, material drift, or state inconsistency evidence exists.
- [ ] 6.7 Verify `/status` remains under 10 seconds and does not run heavyweight, mutating, network, build, test, or `/verify-spec` operations; then run the repository's applicable contract/eval checks.

## Notes

- Health is categorical only; do not introduce a numeric score or imply precision unsupported by local artifacts.
- Missing or stale evidence is a `Warning`, not a failed check. `Attention` requires affirmative current failure, unresolved material drift, or state/git inconsistency.
- Use summaries already written by supporting producers. Status must remain read-only and must not refresh evidence by running diagnostics.
- Story 4 supplies quarantine, blocked-dependent, and resume-consistency state; Story 5 supplies phase-close evidence and drift integration points. This story consumes those contracts without redefining them.
- Artifact timestamps and relevance rules are a risk: selection must be deterministic, name the chosen or unavailable sources, and avoid treating unrelated historical artifacts as current evidence.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `Error & Rescue Map` → `Resume phase`, `Compute health`] — reconcile phase state with git without guessing, and classify missing/stale evidence as `Warning` with named unavailable inputs.
- **Shadow paths:** [`technical-spec.md` → `Shadow Paths` → `Resume`, `Status health`] — expose state mismatches safely and cover current, absent, empty-drift, and failed-artifact health paths.
- **Business rules:** [`spec.md` → `Specification Contract` → `Business Rules` → Rule 9 (`/status` never runs mutating or heavyweight checks and labels missing/stale evidence)] — enforce read-only summary behavior; [`spec.md` → `Detailed Requirements` → `R6 — Status and Health`] — report phase execution and classify the newest local eval, verification, drift, and state-consistency evidence.
- **Experience:** [`spec.md` → `Experience Design` → `State Catalog` → `Executing`, `Stale health evidence`] — show lane/progress/evidence health and explicit stale-input warnings; [`spec.md` → `Experience Design` → `Interaction and Output Rules`] — keep output concise, categorical, and clear that missing evidence differs from failing evidence; [`technical-spec.md` → `Design Decisions` → `D7 — Categorical Health`] — apply the exact inputs, category conditions, and prohibition on deep or external checks.
