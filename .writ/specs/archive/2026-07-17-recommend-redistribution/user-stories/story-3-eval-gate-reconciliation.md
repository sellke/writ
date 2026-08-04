# Story 3: Eval Falsifiability-Gate Reconciliation

> **Status:** Completed ✅

## User Story

As a Writ maintainer, I want `scripts/eval.sh` to assert the revised policy
rather than the superseded single-spec / production flow, so that the
falsifiability gate protects the *current* contract and `/release` can pass.

## Acceptance Criteria

- [x] Given `autonomy-governance`, then it asserts the revised policy's canonical literals on live surfaces (roadmap/mission/mission-lite/system) and `forbid_literal`-guards the old wording there, while the deferred production-approval design stays preserved in ADR-013 + the locked delivery spec.
- [x] Given `recommended-spec-implementation`, then its static assertions reflect the two-command model — no active-surface expectation of `implement-spec --recommend` or the single-spec nested-execution contract.
- [x] Given `recommended-staging`, then it is redirected to guard only the **dormant** machinery (`scripts/recommend-state.py`, `.writ/docs/recommended-delivery-state-format.md`, `config-format.md`) plus the adapter merge-forbid — not active `ship`/`create-uat-plan`/adapter provider surfaces.
- [x] Given `bash scripts/eval.sh`, then it exits 0 with 0 findings (including `commands/_preamble.md` ≤ 80 lines).

## Implementation Tasks

- [x] 3.1 `autonomy-governance`: repoint 4 live-surface literals + add 3 regression `forbid_literal`s — **PASS**
- [x] 3.2 `recommended-spec-implementation`: reconciled static assertions to the two-command model. Python #1 now validates only create-spec's live matrix/normal-branch/terminal-scope + the dormant state-format doc; retired the `implement-spec --recommend` matrix, `delivery_context` propagation, worktree-adoption, required-answer, and adapter delivery-context assertions. Behavioral scenarios still 162/162; static 16/16. **PASS**
- [x] 3.3 `recommended-staging`: **redirected** (option 1). Dropped active-surface assertions on `create-spec`/`implement-spec`/`ship`/`create-uat-plan`/adapter provider ops; kept the reducer ops, state-format doc, config-format doc, reducer forbids, and an adapter `mergePullRequest` forbid. Scenarios 60/60. **PASS**
- [x] 3.4 Trimmed `commands/_preamble.md` to 79 lines; full `scripts/eval.sh` → **0 findings**

## Definition of Done

- [x] Full eval suite green (0 findings)
- [x] No eval assertion demands the deferred production flow on an active surface
- [x] Dormant machinery still has a guard (redirected `recommended-staging` + the state-format assertions retained in `recommended-spec-implementation`)
- [x] `spec.md` deliverables checklist fully checked

## Resolved Decision

`recommended-staging` was **redirected** (not retired). Its scenarios and the
`recommend-state.py` reducer / state-format / config-format `require_literal`s
remain, so the deferred staging → PR → production design stays falsifiable via
its dormant machinery. The active-surface provider-orchestration assertions were
removed because ADR-013 (revised 2026-07-17) defers that flow; the new
phase-lane worktree model is covered by `check_phase_lanes`. Re-add the
active-surface assertions when the "bigger loops" staging→production work resumes.
