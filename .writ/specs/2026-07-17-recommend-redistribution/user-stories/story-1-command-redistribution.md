# Story 1: `--recommend` Command Redistribution

> **Status:** Completed ✅

## User Story

As a Writ maintainer, I want `--recommend` confined to authoring
(`create-spec`) and the end-to-end phase loop (`implement-phase`), so that each
command's responsibility stays legible and no single command drives autonomously
to production.

## Acceptance Criteria

- [x] Given `/create-spec --recommend`, when invoked, then it authors + locks a spec package from evidence and stops without implementing.
- [x] Given `/implement-phase --recommend`, when invoked, then it auto-authors missing specs and runs `implement-spec` per spec, ending at the completion report + manual UAT handoff.
- [x] Given `/implement-spec`, when invoked, then it runs the plan as a plain execute command with no `--recommend` flag and no confirmation gate.
- [x] Given `ship` or `create-uat-plan`, when inspected, then neither exposes a `--recommend` flag.
- [x] Given the redistribution, then no recommended flow merges, opens PRs, or releases.

## Implementation Tasks

- [x] 1.1 `create-spec.md` — recommend-mode authoring branch (author + stop)
- [x] 1.2 `implement-phase.md` — end-to-end recommend loop delegating to `create-spec --recommend` + `implement-spec`
- [x] 1.3 `implement-spec.md` — remove `--recommend`; plain execute, no gate
- [x] 1.4 `ship.md` / `create-uat-plan.md` — remove `--recommend`
- [x] 1.5 Verify scenarios (`recommended-spec-implementation` 162/162, `recommended-staging` 60/60 scenario suites pass)

## Definition of Done

- [x] Five command files reflect the two-command model
- [x] Eval scenario suites (behavioral) pass
- [x] Behavior matches ADR-013 (revised 2026-07-17)
