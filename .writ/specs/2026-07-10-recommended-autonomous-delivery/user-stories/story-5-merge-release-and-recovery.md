# Story 5: Merge, Release, and Recovery

> **Status:** Completed ✅ (2026-07-10)
> **Priority:** High
> **Dependencies:** Story 4

## User Story

**As a** Writ maintainer/releaser
**I want to** merge the exactly approved PR revision through repository protections and complete an evidence-backed, idempotent methodology release
**So that** production delivery is auditable, policy-preserving, and safely resumable even when an external operation succeeds before Writ records its result

## Acceptance Criteria

- [x] Given explicit production approval is bound to a full PR head SHA, when the workflow enters merge, then it freshly reconciles the PR, required checks, and approved SHA; it uses only a configured provider-permitted merge strategy and blocks without bypass, force, or strategy hopping if policy refuses the merge.
- [x] Given the provider reports that the approved SHA was merged, when release is about to begin, then Writ records the canonical merge identifiers, fetches the default branch, verifies that it contains the merge commit, and blocks at a resumable ancestry check if that proof remains unavailable.
- [x] Given merge ancestry is verified and change evidence supports a release, when Writ selects the release, then breaking changes produce a major bump, features a minor bump, and fixes/docs/chore a patch bump; the evidence, selected version, and changelog decision are logged before the mandatory standard release gate runs.
- [x] Given any release substep was completed locally or by the provider before an interruption or lost response, when the execution resumes, then Writ performs lookup-before-write reconciliation for the version/changelog, release commit, immutable tag, pushed refs, and provider release, adopts one exact match, and creates no duplicate or destructive replacement.
- [x] Given the merged change reaches a complete, blocked, or partially released outcome, when Writ reports the result, then `complete` is claimed only with every required identifier and finalized log entry, partial success preserves all completed artifacts with the exact safe resume step, and no path publishes `@sellke/writ` to npm.

## Implementation Tasks

- [x] 5.1 Write `scripts/eval.sh` fixtures and disposable-git/provider fakes for approved-SHA merge, branch-protection refusal, default-branch ancestry, major/minor/patch selection, release-gate failure, and interruption before and after every merge/release mutation.
- [x] 5.2 Extend `commands/ship.md` and the recommended-delivery orchestration contract with lookup-before-write protected merge, exact approved-head validation, provider-permitted strategy enforcement, persisted merge identifiers, and fetched default-branch ancestry proof.
- [x] 5.3 Update `commands/release.md` so recommended delivery automatically derives and logs SemVer/changelog evidence, runs the standard release gate before release-file mutation, and preserves its existing ownership of version, changelog, release commit, annotated tag, tag push, and provider release without npm publication.
- [x] 5.4 Implement the fixed release sub-state reconciliation order and partial-release recovery in the durable execution contract, including exact-match adoption, deterministic operation keys, `partially_released` reporting, and blockers for conflicting versions, digests, commits, tags, refs, or provider releases.
- [x] 5.5 Document equivalent protected-merge, ancestry-query, release-lookup/create, authentication-stop, and unsupported-provider-release mappings in `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/codex.md`, updating state/config documentation where the persisted schema or capability contract requires it.
- [x] 5.6 Verify every acceptance criterion and the golden completion fixture, including durable links for the approved SHA, merge operation/commit, ancestry evidence, version, changelog digest, release commit, tag object/push, provider release, and finalized recommendation entries.
- [x] 5.7 Verify all evals pass and assert the recommended path never invokes npm publishing, force push, admin merge, check bypass, strategy hopping, tag rewrite/deletion, release deletion, or destructive cleanup.

## Notes

- Story 4 supplies the explicit approval event, approved full PR head SHA, successful required-check evidence, preview evidence, UAT digest, and recommended version shown to the user. Story 5 must freshly reconcile that evidence before its first production mutation; any changed head invalidates approval and returns control to the Story 4 validation path.
- `/ship` currently owns testing, commits, push, and PR open-or-find behavior but no merge operation. This story must make that boundary explicit while adding protected merge to the top-level recommended-delivery orchestration rather than silently redefining ordinary `/ship` as a release owner.
- `/release` remains the sole owner of the standard release gate, version and changelog mutation, release commit, tag, tag push, and GitHub/provider release. Automatic publication of `@sellke/writ` remains excluded.
- Every external mutation requires a deterministic target, preflight lookup, at-most-one mutation attempt, observable result, and persisted canonical identifier. Saved state is only a reconciliation hint.
- Lost responses and interrupted writes are expected recovery cases. Existing exact artifacts advance the state; mismatches block. Existing tags, releases, commits, or remote refs are never deleted, moved, overwritten, force-pushed, or otherwise compensated destructively.
- Provider authentication, authorization, branch-protection, required-review, conflict, and policy failures are definitive for the attempt: record one actionable blocker and stop without searching for a bypass.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Revalidate approved SHA, Merge PR, Verify default-branch ancestry, Select SemVer, Run release gate, Update changelog/version, Create release commit, Create tag, Push release commit/tag, Create provider release, Finalize execution]
- **Shadow paths:** [Protected merge, Release, Resume]
- **Business rules:** [Rule 8 (production approval is explicit and never inferred), Rule 9 (release starts only after default-branch merge and successful required checks), Rule 10 (SemVer and changelog choices come from change evidence and are recorded), Rule 11 (the Writ runtime helper is excluded from automatic publishing), Rule 12 (platform approvals and branch protections are never bypassed)]
- **Experience:** [Happy Path step 8 (verify default-branch merge, run the release gate, and create changelog/version commit/tag/provider release), State Catalog — Merging (merge the approved PR through the provider-supported path), State Catalog — Releasing (verify ancestry and run the release gate), State Catalog — Complete (record all durable links and outcomes), State Catalog — Blocked (show one actionable blocker and safe resume path), Feedback and Audit Model (append selected release evidence and resulting identifiers), Error Experience — Interrupted session (reconcile repository and provider reality before resuming), Error Experience — Merge conflict or branch protection (stop without bypass and show recovery), Error Experience — Release failure (preserve merged state and resume from existing release artifacts)]

---

## What Was Built

**Implementation Date:** 2026-07-10

### Files Created

1. **`scripts/eval-recommend-merge-release.py`** — 26 Story 5 adversarial scenarios using disposable git repos + provider fakes.

### Files Modified

- **`scripts/recommend-state.py`** — Extended v1 state machine with: `merging`, `releasing`, `complete`, `partially_released` statuses; five new reducer operations (`record-merge-attempt`, `record-merge-result`, `verify-ancestry`, `record-release-substep`, `finalize-release`); inert guard updated to pass during Story 5 and when blocked with Story 5 resume target.
- **`commands/ship.md`** — Documented `ship` boundary with Story 5 (merge stays outside `ship`).
- **`commands/release.md`** — Internal recommended branch: derives version/changelog evidence, runs standard release gate, no npm publish.
- **`commands/implement-spec.md`** — Merge + release continuation after `production_approved`.
- **`adapters/cursor.md`, `adapters/claude-code.md`, `adapters/codex.md`** — Protected-merge, ancestry-query, substep-reconcile, and unsupported-provider-release mappings.
- **`.writ/docs/recommended-delivery-state-format.md`** — Activated merge/release schema tokens.

### Implementation Decisions

1. **Pending merge audit entry** — `record-merge-attempt` uses `pending=True` binding (like PR-create); other pending mutation entries block; own entry allowed through.
2. **Ancestry check** — merge commit must be ancestor of OR equal to default branch head; equal case (squash/fast-forward) avoids duplicate identifiers in transition.
3. **Substep idempotency** — evidence digest equality → deduplicate; conflicting digest → `partially_released`.
4. **Final identifiers** — order-preserving deduplication across all substep identifiers to avoid transition validator rejection.
5. **npm block** — `publishNpm: true` evidence in `provider-release` substep always returns `policy_violation`.

### Test Results

**Verification:** 26/26 Story 5 scenarios, 60/60 Story 4 regressions, 50/50 Story 3 adversarial regressions, all syntax/compile/diff checks passed.

### Review Outcome

**Result:** Gate 0 (architecture) PROCEED. Gate 3 not run separately — story implemented directly from architecture verdict.

### Deviations from Spec

None
