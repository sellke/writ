# Story 4: Failure Quarantine and Resumable Recovery

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 2, 3

## User Story

**As a** Writ maintainer supervising autonomous phase execution
**I want to** quarantine terminally failed spec lanes, continue only eligible work, and reconcile persisted phase state with git when resuming
**So that** failed partial work remains recoverable without contaminating the phase branch or making resumed execution unsafe

## Acceptance Criteria

- [ ] Given a spec lane returns a transient failure on its first attempt, when the orchestrator retries it, then it launches one fresh subagent in the same isolated lane and records the second attempt without requesting another routine confirmation.
- [ ] Given a spec lane reaches a terminal failure or fails its permitted retry, when failure handling completes, then its work is preserved on `writ/quarantine/{spec-id}` (or the recorded deterministic collision suffix), the phase branch contains none of the failed lane's commits or working-tree changes, and phase state records the failure evidence, retry count, quarantine branch, and recovery guidance.
- [ ] Given a quarantined spec has declared dependents and unrelated remaining specs, when the scheduler selects subsequent work, then direct and transitive dependents are marked `skipped_blocked` with `blockedBy` evidence while independent eligible specs continue.
- [ ] Given `--resume` is invoked after interruption, when recorded phase state is reconciled with the phase, active lane, worktree, and quarantine branches, then execution continues from the exact safe step only if they agree; otherwise Writ reports the named mismatch and recovery command without guessing or mutating git.
- [ ] Given lane verification fails despite a nominal success result, or quarantine branch renaming fails, when the orchestrator handles the inconsistency, then it preserves recoverable lane work, records an attention-required state, and leaves the phase branch clean.

## Implementation Tasks

- [ ] 4.1 Write contract-first disposable-repository tests for bounded retry, partial-commit quarantine, dependent blocking, independent continuation, invalid-success quarantine, and state/git mismatch recovery against `commands/implement-phase.md`, `commands/implement-spec.md`, and `.writ/docs/phase-execution-state-format.md`.
- [ ] 4.2 Update `commands/implement-spec.md` to return the structured transient, terminal, invalid-result, and `challenge_required` outcomes that `commands/implement-phase.md` needs without making merge or quarantine decisions locally.
- [ ] 4.3 Implement bounded retry exhaustion, verified-lane quarantine, clean-phase-branch guarantees, `skipped_blocked` propagation, independent-spec continuation, collision-safe quarantine naming, and recovery guidance in `commands/implement-phase.md`.
- [ ] 4.4 Define atomic failure records and deterministic resume reconciliation for phase branches, active lanes, worktrees, quarantine branches, attempts, `blockedBy`, failure evidence, and attention-required discrepancies in `.writ/docs/phase-execution-state-format.md`; align the read-only recovery summary in `commands/status.md`.
- [ ] 4.5 Document the native git and fresh-subagent mechanics required by the platform-neutral quarantine and resume contract in `adapters/cursor.md`, `adapters/claude-code.md`, and `adapters/codex.md`.
- [ ] 4.6 Verify every acceptance criterion in a disposable repository, including the clean phase branch, retained partial commit, blocked dependent, successful independent lane, quarantine collision, interrupted atomic write, and branch rename/deletion mismatch cases.
- [ ] 4.7 Verify all focused contract tests pass and run `bash scripts/eval.sh`, confirming existing evaluation checks remain clean.

## Notes

- Quarantine is a terminal disposition after the existing single transient retry; ordinary scope questions continue through Story 3's User Challenge contract rather than being misclassified as failures.
- Isolation from Story 2 is a prerequisite: a branch created only after failure cannot prove that the phase branch stayed clean.
- Phase state and named git objects are joint resume evidence. State is not permission to recreate, rename, delete, merge, or otherwise “repair” branches when reality differs.
- Preserve a failed lane even when it has no partial commit so the failure record and branch disposition remain deterministic and auditable.
- Quarantine-name collisions and interrupted merge state are safety-sensitive. Surface ownership ambiguity or attention-required state before any mutation.
- This story establishes the failure and recovery data consumed by Story 5 knowledge writeback and Story 6 phase health reporting.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Execute spec — Transient pipeline failure, Execute spec — Terminal/second failure, Validate successful lane, Update phase state, Resume phase]
- **Shadow paths:** [Fresh spec execution, Quarantine, Resume]
- **Business rules:** [Rule 6 (fresh subagents exchange artifact-derived structured results), Rule 7 (quarantine only after bounded retry exhaustion)]
- **Experience:** [Terminal failure (preserve quarantine branch, block dependents, continue independent work), Interrupted (`--resume` reconstructs work from state and git reality), Error messages (name spec, lane, branch disposition, dependent impact, and one recovery path)]
