# Story 1: /prototype Command

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** solo developer using Writ
**I want to** execute small-to-medium code changes through a lightweight prototype pipeline
**So that** I can ship work without the overhead of creating a full spec when the ceremony exceeds the value of the change

## Acceptance Criteria

- [ ] **AC1:** Given I invoke `/prototype` with no arguments, when the command runs, then I am prompted with a quick contract (2-3 questions: what's the change, what files are involved, any constraints) via AskQuestion before any coding begins.
- [ ] **AC2:** Given I invoke `/prototype "add dark mode toggle to settings"`, when the command runs, then the description is pre-filled and the first question is skipped; I proceed directly to files/constraints questions.
- [ ] **AC3:** Given I have completed the quick contract, when the coding phase runs, then a coding agent (TDD approach) is spawned via Task with `subagent_type: "generalPurpose"` and implements the change; lint and typecheck run automatically after implementation.
- [ ] **AC4:** Given the prototype completes successfully, when the command finishes, then I receive a summary of changes, a list of files modified, and lint/typecheck pass confirmation.
- [ ] **AC5:** Given the coding agent detects complexity (e.g., >5 files, schema changes, core architecture), when the prototype completes, then the output includes an optional escalation recommendation: "This change grew beyond prototype scope — consider running `/create-spec` to formalize it."

## Implementation Tasks

- [ ] 1.1 Write tests for the prototype command flow — mock AskQuestion responses, verify contract questions are asked in correct order, verify pre-filled description skips first question.
- [ ] 1.2 Create `commands/prototype.md` — document the full command process: invocation modes, quick contract (2-3 AskQuestion rounds), pipeline stages (contract → coding agent → lint/typecheck → summary), escape hatch logic, and output format.
- [ ] 1.3 Implement the prototype orchestration logic — parse invocation args, run AskQuestion for quick contract (or use pre-filled description), spawn coding agent Task with contract context, run lint/typecheck, produce summary with files modified and optional escalation recommendation.
- [ ] 1.4 Add scope detection heuristic to the coding agent prompt — instruct agent to flag when >5 files, schema changes, core architecture, low test coverage, or incomplete dependencies are detected; include escalation recommendation in output when flagged.
- [ ] 1.5 Copy `commands/prototype.md` to `.cursor/commands/prototype.md` for Cursor command discovery.
- [ ] 1.6 Verify end-to-end: run `/prototype "add a simple utility function"` and confirm contract → coding → lint → summary flow; run `/prototype` interactive and confirm AskQuestion flow.
- [ ] 1.7 Update `.writ/docs/` or README with `/prototype` command documentation and when to use it vs `/create-spec` + `/implement-story`.

## Notes

**Technical considerations:**
- The coding agent for prototype uses the same `agents/coding-agent.md` but receives a lightweight "contract" (description + files + constraints) instead of a full story file. May need a variant prompt or parameterized input.
- Lint/typecheck: reuse the same mechanism as `implement-story` (Gate 2) — typically `npm run lint` and `npm run typecheck` or equivalent.
- No spec file is created; the contract lives in conversation context only.

**Risks:**
- Scope detection heuristic may be noisy (false positives) or miss real complexity (false negatives). Start conservative; iterate based on usage.
- Pre-filled description parsing: ensure quoted strings with special characters are handled correctly across adapters.

**Integration points:**
- `commands/` and `.cursor/commands/` — command discovery
- `agents/coding-agent.md` — shared implementation agent
- `implement-story` Gate 2 — lint/typecheck pattern to reuse
- `create-spec` — escalation target when prototype scope is exceeded

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated
