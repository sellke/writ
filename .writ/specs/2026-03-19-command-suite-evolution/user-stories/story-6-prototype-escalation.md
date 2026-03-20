# Story 6 — Prototype → Spec Escalation Path

> Status: Completed ✅
> Priority: Medium
> Dependencies: None

## User Story

As a developer using Writ, I want `/prototype` to offer a clear path into formal spec work when scope escalation fires, so that implemented prototype work is not left in limbo and can become Story 1 (completed) while the spec pipeline picks up from Story 2 onward.

## Acceptance Criteria

**Given** `commands/prototype.md` and a run where scope escalation signals apply (e.g. touching more than five files, schema changes, core architecture changes, or external dependency additions)
**When** implementation completes and escalation is flagged
**Then** the command includes a post-escalation step that offers `/create-spec --from-prototype` as the recommended next action (not only “escalation noted” with no follow-on).

**Given** `commands/create-spec.md` documents `--from-prototype` mode
**When** a maintainer or agent reads the create-spec command
**Then** the mode is described: use current git diff plus the coding agent’s implementation summary to pre-populate the discovery contract (deliverable, files changed, approach).

**Given** `--from-prototype` mode is executed
**When** the spec contract is generated
**Then** files-in-scope and implementation approach are informed by the git diff (and summary where relevant), not invented from scratch.

**Given** `--from-prototype` mode is executed
**When** user stories are laid out in the new spec
**Then** Story 1 is pre-marked **Completed** with a description that captures the prototype work; planning starts at Story 2 for follow-on work.

**Given** `--from-prototype` mode is used
**When** the discovery conversation runs
**Then** it is shortened and focused on **what comes next** (Story 2+), not re-litigating what was already built.

## Implementation Tasks

- [x] Define an AC verification checklist (escalation post-step text, create-spec `--from-prototype` section, diff-driven fields, Story 1 completed wording, discovery focus) and use it as the test plan for these markdown-only changes.
- [x] Update `commands/prototype.md` so that after escalation completes, the flow explicitly offers `/create-spec --from-prototype` and states what the user/agent should pass in (e.g. diff + implementation summary expectations).
- [x] Update `commands/create-spec.md` to document `--from-prototype`: inputs (git diff, implementation summary), how they map to contract sections (deliverable, files changed, approach), and how Story 1 is recorded as completed prototype work.
- [x] Specify in `create-spec.md` that agents must read the working tree diff (and summary) to populate files-in-scope and approach accurately before opening discovery.
- [x] Specify the generated spec shape: Story 1 titled/description aligned to the prototype outcome, status **Completed** (e.g. with ✅ consistent with other spec docs), and subsequent stories numbered from 2 for remaining scope.
- [x] Document discovery behavior for `--from-prototype`: skip redundant “what we built” discovery; anchor questions on gaps, risks, and next deliverables for Story 2+.
- [x] Walk the verification checklist against `prototype.md` and `create-spec.md`; confirm every AC passes and cross-references between the two commands are clear.

## Technical Notes

- Scope is **markdown instruction files only** (no runtime code): behavior is specified for the AI agent executing the commands.
- **Escalation signals** (already in prototype): >5 files touched, schema changes, core architecture changes, external dependency additions — post-step applies when any of these fire after implementation still completes.
- **Gap closed:** today escalation ends with a flag only; this story adds the formalization bridge so prototype output becomes the first completed story and the spec pipeline continues cleanly.
- Align wording with the parent contract summary: nine targeted improvements across the command/agent suite; this story closes the **prototype-to-pipeline** gap specifically.

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed
