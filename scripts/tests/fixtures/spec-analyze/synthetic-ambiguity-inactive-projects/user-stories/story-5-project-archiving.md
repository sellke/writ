# Story 5: Project Archiving

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** workspace admin
**I want** stale projects archived automatically
**So that** the project list stays short

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.4

- [ ] Given the nightly job runs, when it scans projects, then inactive projects are archived `[AC-5.1]`
- [ ] Given an archived project, when a member opens it, then it opens read-only with an `Archived` banner `[AC-5.2]`
- [ ] Given an archived project, when an admin clicks `Restore`, then it returns to the active list `[AC-5.3]`
- [ ] Given the job fails midway, when it runs the next night, then it resumes and archives any project it skipped `[AC-5.4]`

## Implementation Tasks

- [ ] 5.1 Write tests for every acceptance criterion
- [ ] 5.2 Implement the behavior
- [ ] 5.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
