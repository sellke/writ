# Story 2: Percentage Discounts

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** store owner
**I want** to offer percentage discount codes
**So that** I can run seasonal sales

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given a valid 15% code on a $9.99 item, when the cart total is computed, then the discounted price is rounded `[AC-2.1]`
- [ ] Given an expired code, when the shopper applies it, then the cart shows `This code has expired` and the total is unchanged `[AC-2.2]`
- [ ] Given a code that does not exist, when the shopper applies it, then the cart shows `Code not found` and the total is unchanged `[AC-2.3]`
- [ ] Given a valid code, when it is applied twice, then the discount is applied once `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write tests for every acceptance criterion
- [ ] 2.2 Implement the behavior
- [ ] 2.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
