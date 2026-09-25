# Story 3: Guest Cart at Login

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** shopper who added items before signing in
**I want** my cart to survive signing in
**So that** I do not have to add the items again

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given a guest cart and an account with an empty cart, when the shopper signs in, then the guest items move into the account cart `[AC-3.1]`
- [ ] Given a guest cart and an account cart that both hold items, when the shopper signs in, then the shopper sees the right cart `[AC-3.2]`
- [ ] Given a guest cart item that is out of stock, when it moves to the account, then it is shown with an `Out of stock` label and excluded from the total `[AC-3.3]`
- [ ] Given sign-in fails, when the shopper returns to the store, then the guest cart is unchanged `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write tests for every acceptance criterion
- [ ] 3.2 Implement the behavior
- [ ] 3.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
