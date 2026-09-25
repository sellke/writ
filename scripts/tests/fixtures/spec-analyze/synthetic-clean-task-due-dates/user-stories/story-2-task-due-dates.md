# Story 2: Task Due Dates

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** project member
**I want** to set a due date on a task
**So that** I know what to work on first

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given a task, when the member picks today or a later date, then the date is saved and shown on the task card as `Due <Mon D>` `[AC-2.1]`
- [ ] Given a task with a due date, when the member clicks `Clear`, then the due date is removed and the card shows no date `[AC-2.2]`
- [ ] Given a task, when the member types a date before today, then the picker shows `Due date must be today or later` and nothing is saved `[AC-2.3]`
- [ ] Given a task, when the member types text that is not a date, then the picker shows `Enter a date as YYYY-MM-DD` and nothing is saved `[AC-2.4]`
- [ ] Given a project where no task has a due date, when the member opens the `Due soon` view, then it shows `No tasks have due dates` `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write tests for every acceptance criterion
- [ ] 2.2 Implement the behavior
- [ ] 2.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
