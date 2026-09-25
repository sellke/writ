# Story 3: Contact CSV Import

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** sales rep moving from a spreadsheet
**I want** to import my contacts from a CSV file
**So that** I do not have to retype them

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.3

- [ ] Given a CSV with `name` and `email` columns, when the rep imports it, then one contact is created per row `[AC-3.1]`
- [ ] Given a row whose email matches an existing contact, when the import runs, then that contact's name is updated instead of creating a duplicate `[AC-3.2]`
- [ ] Given an import finishes, when the summary appears, then it shows the number of contacts created and updated `[AC-3.3]`

## Implementation Tasks

- [ ] 3.1 Write tests for every acceptance criterion
- [ ] 3.2 Implement the behavior
- [ ] 3.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
