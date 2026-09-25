# Story 2: Rename Workspace

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** workspace admin
**I want** to rename my workspace
**So that** the name matches our team after a reorg

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given an admin enters a name of 1 to 60 characters, when they click `Save`, then the new name is stored and shown in the header `[AC-2.1]`
- [ ] Given an admin submits an empty name, when they click `Save`, then the form shows `Name is required` and the stored name is unchanged `[AC-2.2]`
- [ ] Given an admin enters a name longer than 60 characters, when they click `Save`, then the form shows `Name must be 60 characters or fewer` and the stored name is unchanged `[AC-2.3]`
- [ ] Given a member who is not an admin, when they submit a rename request, then the response is 403 and the stored name is unchanged `[AC-2.4]`
- [ ] Given the database write fails, when the admin clicks `Save`, then the form shows `Could not save, try again` and the stored name is unchanged `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write tests for every acceptance criterion
- [ ] 2.2 Implement the behavior
- [ ] 2.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
