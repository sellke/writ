# Story 2: Executable Checkpoint in `safe-refactor-loop`

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** coding agent running the safe-refactor loop
**I want to** the checkpoint step to capture a HEAD SHA and assert the tree is clean
**So that** "note the current clean git state" is something I do rather than something the skill assumes

## Acceptance Criteria

- [ ] Given `skills/safe-refactor-loop/SKILL.md` step 1, when it is read, then it instructs capturing the current HEAD SHA and asserting `git status --porcelain` is empty, rather than assuming a clean state.
- [ ] Given `bash scripts/lint-skill.sh skills/safe-refactor-loop/SKILL.md`, when it runs, then it exits clean and the skill's lifecycle fields are unchanged.
- [ ] Given the full suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0`.

## Implementation Tasks

- [ ] 2.1 Rewrite step 1's Checkpoint line as an executable instruction (capture HEAD, assert clean)
- [ ] 2.2 Verify `lint-skill.sh` clean and lifecycle fields untouched
- [ ] 2.3 Run `bash scripts/eval.sh` to `Findings: 0`

## Notes

**Technical considerations:** `lint-skill.sh:52` forbids `Read skills/` inside a skill — do not add one. Keep the skill's `status: candidate` and evidence fields as they are.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Code reviewed
