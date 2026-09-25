# Story 3: Orders CSV Export

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As an** operations lead
**I want** to export the orders table as CSV
**So that** I can reconcile orders in a spreadsheet

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given at least one order, when the export runs, then `orders.csv` is written in UTF-8 and its first line is the header row `id,customer,total,status` `[AC-3.1]`
- [ ] Given at least one order, when the export runs, then the first line of `orders.csv` is the oldest order's data record `[AC-3.2]`
- [ ] Given zero orders, when the export runs, then `orders.csv` contains only the header row `[AC-3.3]`
- [ ] Given the export directory is not writable, when the export runs, then no file is written and the page shows `Export failed: storage unavailable` `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write tests for every acceptance criterion
- [ ] 3.2 Implement the behavior
- [ ] 3.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
