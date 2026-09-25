# Story 4: Checkout Payment

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** shopper with items in my cart
**I want** to pay by card at checkout
**So that** my order is placed in one step

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.3

- [ ] Given a cart and a valid card, when the shopper submits payment, then a charge is created for the cart total and the order status is `confirmed` `[AC-4.1]`
- [ ] Given a confirmed order, when the confirmation page loads, then it shows the order number and the charged amount `[AC-4.2]`
- [ ] Given a confirmed order, when payment completes, then a receipt email is sent to the shopper's address `[AC-4.3]`

## Implementation Tasks

- [ ] 4.1 Write tests for every acceptance criterion
- [ ] 4.2 Implement the behavior
- [ ] 4.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
