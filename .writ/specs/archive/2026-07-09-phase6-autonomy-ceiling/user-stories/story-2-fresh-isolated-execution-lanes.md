# Story 2: Fresh Isolated Execution Lanes

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer executing a roadmap phase
**I want to** run each spec in a fresh artifact-seeded subagent within its own branch and worktree lane
**So that** only independently verified spec work reaches the phase branch without accumulated conversational context or failed-lane changes

## Acceptance Criteria

- [x] Given an eligible spec and a clean phase branch, when `/implement-phase` starts the spec, then it creates `writ/phase/{phase-id}/{spec-id}` and a dedicated worktree from the current phase branch before launching a fresh subagent that receives the D3 artifact-path payload and no prior conversational transcript.
- [x] Given a fresh subagent running `/implement-spec`, when execution ends, then it returns a `phase-spec-result-v1` result containing the required status, story counts, verification evidence, changed files, commit, failure, and challenge fields.
- [x] Given a `succeeded` result with a commit and passing verification evidence, when the orchestrator validates the lane, then it merges the lane into the phase branch, records the merge and lane evidence in phase state, removes the successful worktree, and proceeds to UAT generation.
- [x] Given a missing, malformed, non-successful, or unverifiable result, when the orchestrator evaluates the lane, then it does not merge or alter the phase branch and preserves the lane for Story 4 to classify, quarantine, and recover.
- [x] Given the platform-neutral fresh-subagent contract, when a maintainer consults the adapters, then `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/codex.md` each document the native launch, fresh-context, artifact-seeding, run-identifier, structured-result, and isolated-worktree mapping.

## Implementation Tasks

- [x] 2.1 Write contract-first disposable-repository tests for the lane lifecycle in `commands/implement-phase.md` and the result contract in `commands/implement-spec.md`, covering creation before launch, transcript exclusion, verified merge, malformed or unverifiable results, and parent-checkout isolation.
- [x] 2.2 Update `commands/implement-phase.md` to create and own per-spec branches/worktrees, seed a fresh subagent from repository artifact paths, validate `phase-spec-result-v1`, merge only verified success, remove successful worktrees, and hand non-successful preserved lanes to Story 4 without implementing quarantine.
- [x] 2.3 Update `commands/implement-spec.md` to execute only inside the supplied lane and return the complete `phase-spec-result-v1` structured result without mutating the parent checkout or making orchestration decisions.
- [x] 2.4 Create `.writ/docs/phase-execution-state-format.md` with the Story 2 lane, agent-run, result-evidence, merge-commit, and atomic-update fields needed to record fresh execution and verified success.
- [x] 2.5 Document the native fresh isolated execution mappings in `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/codex.md`, while keeping `commands/implement-phase.md` platform-neutral.
- [x] 2.6 Run the Story 2 contract tests against `commands/implement-phase.md`, `commands/implement-spec.md`, `.writ/docs/phase-execution-state-format.md`, and all three adapter files; verify failed or invalid lanes remain unmerged and preserved for Story 4.
- [x] 2.7 Verify every acceptance criterion, confirm the parent checkout stays untouched during lane execution, and review `commands/implement-phase.md` for consistency with Story 1 dependency ordering and the locked R2/D2/D3 contracts.

## Notes

- Isolation must begin before implementation: creating a branch after a failure cannot prove that the phase branch remained clean.
- The lane starts at the current phase-branch head. Dirty-base and ambiguous branch/worktree ownership conditions must stop before subagent launch rather than being guessed around.
- Freshness means a new subagent context seeded only with the named repository artifacts and execution metadata; accumulated parent-session conversation is not forwarded.
- The orchestrator owns lane creation, result validation, merge, state, and UAT handoff. The nested `/implement-spec` run owns implementation and reports evidence through the structured result.
- This story preserves any non-successful lane and keeps it off the phase branch. Retry classification, branch renaming to `writ/quarantine/{spec-id}`, dependent blocking, and resumable recovery belong to Story 4.
- Story 1 supplies the authoritative eligible-spec order consumed before this story creates a lane.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Create lane branch`, `Create worktree`, `Spawn fresh subagent`, `Validate successful lane`, `Merge successful lane`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Fresh spec execution`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 6 (fresh artifact-derived subagents return structured results), `spec.md` → `### Business Rules` → Rule 7 (quarantine follows bounded retry; preserve the boundary for Story 4)]
- **Experience:** [`spec.md` → `### Primary User Journey` → Steps 3–5 (create lane, launch fresh subagent, merge verified success), `spec.md` → `### State Catalog` → `Ready` and `Executing` rows, `technical-spec.md` → `### D2 — Isolation Begins Before Work`, `### D3 — Fresh Subagent Contract`, and `### D4 — State Is the Resume Boundary`]
