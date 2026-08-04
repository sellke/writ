# Story 7: Quick Wins Bundle

> **Status:** Completed ✅
> **Priority:** Low
> **Dependencies:** None

## User Story

**As a** Writ user
**I want** three small but valuable improvements — faster architecture checks, auto-orientation on session start, and correct model selection
**So that** the pipeline is faster, sessions start with context, and resources are allocated efficiently

## Acceptance Criteria

- [x] Given the architecture check agent runs, when it is spawned by implement-story, then it uses `model: "fast"` instead of the default model
- [x] Given a developer starts a new Writ session without a specific command, when Writ first responds, then it provides a brief orientation: current branch, active spec (if any), and suggested next action
- [x] Given the architecture check produces a PROCEED/CAUTION/ABORT decision on fast model, when compared to the same decision on the default model, then triage quality is equivalent (no regressions on read-only analysis)

## Implementation Tasks

- [x] 7.1 Update `agents/architecture-check-agent.md` Agent Configuration — change `model: default (inherits from parent)` to `model: "fast"`
- [x] 7.2 Update `agents/architecture-check-agent.md` Prompt Template — add `model: "fast"` to the Task() invocation example
- [x] 7.3 Add auto-orientation guidance to `system-instructions.md` — when Writ is first invoked in a session and no specific command is given, surface: current git branch, most recent active spec, and suggested next action (3-line summary, not full /status)
- [x] 7.4 Review `commands/status.md` to ensure the auto-orientation in system-instructions.md doesn't duplicate or conflict with the full /status command — it should be a lightweight subset
- [x] 7.5 Verify all three changes are coherent and don't introduce conflicts with existing behavior

## Notes

- The arch check model change is literally a one-line edit in two places (config block + prompt template). Lowest-effort change in the spec.
- The auto-orientation in system-instructions.md should be a suggestion/guideline, not a hard requirement. It tells Writ "if the user hasn't given a specific command, help them get oriented." The system instructions file is at `system-instructions.md` in the repo root.
- The status auto-orientation is NOT the full `/status` command. It's: (1) what branch am I on, (2) is there an active spec, (3) what should I do next. Three lines, not a full report.
- This story bundles three trivial changes to avoid the overhead of three separate stories with 5+ tasks each.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `agents/architecture-check-agent.md` uses `model: "fast"`
- [x] `system-instructions.md` includes auto-orientation guidance
- [x] Changes are minimal and non-disruptive
