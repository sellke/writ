# Story 1: Coding Agent Self-Check

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ pipeline operator
**I want** the coding agent to verify its own work (tests + typecheck) before handing off
**So that** obvious failures are caught with warm context, reducing pipeline round-trips and review iterations

## Acceptance Criteria

- [x] Given the coding agent completes implementation, when it finishes all tasks, then it runs the project's test suite and typecheck before reporting completion
- [x] Given tests fail during self-check, when the coding agent detects the failure, then it attempts to fix the issue itself with its current context
- [x] Given the coding agent self-check passes, when it reports output, then the structured summary includes a `### Self-Check Results` section with pass/fail counts
- [x] Given the coding agent self-check finds unfixable issues, when it reports output, then it flags the issues clearly so the pipeline knows what to expect at Gate 2

## Implementation Tasks

- [x] 1.1 Read current `agents/coding-agent.md` and identify where the self-check step should be added (after implementation, before output)
- [x] 1.2 Add a "Self-Verification" section to the agent's process instructions — run tests, run typecheck, fix any failures, re-run
- [x] 1.3 Update the Output Format section to include `### Self-Check Results` with test count, pass/fail, typecheck status, and any issues self-fixed
- [x] 1.4 Update the Resume Template (for review failures) to also include self-check after fixes
- [x] 1.5 Verify the updated agent prompt is coherent — self-check doesn't conflict with TDD instructions or scope detection

## Notes

- The coding agent already follows TDD (write tests first, then implement). Self-check is the natural completion of that loop — verify the tests you wrote actually pass.
- The self-check should use auto-detected test runners (same detection logic as the testing agent: vitest, jest, pytest, cargo test, go test).
- This is the highest-leverage change in the spec — it reduces the NUMBER of pipeline iterations, not just the speed.
- Keep the self-check lightweight: run tests + typecheck. Don't add coverage analysis or lint — those are Gate 2's job.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `agents/coding-agent.md` updated with self-check process and output format
- [x] No conflicts with existing agent instructions (TDD, scope detection, prototype mode)
