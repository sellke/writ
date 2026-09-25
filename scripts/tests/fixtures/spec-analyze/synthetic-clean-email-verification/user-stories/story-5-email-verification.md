# Story 5: Email Verification

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** new user who just signed up
**I want** to verify my email address
**So that** I can receive password resets and receipts

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.6

- [ ] Given a new signup, when the account is created, then a verification email with a single-use link is sent to the signup address `[AC-5.1]`
- [ ] Given an unused link less than 24 hours old, when the user opens it, then the account is marked verified and the page shows `Email verified` `[AC-5.2]`
- [ ] Given a link older than 24 hours, when the user opens it, then the page shows `This link has expired` and a `Send a new link` button `[AC-5.3]`
- [ ] Given a link that was already used, when the user opens it, then the page shows `Your email is already verified` `[AC-5.4]`
- [ ] Given a link whose token is unknown or malformed, when the user opens it, then the page shows `This link is not valid` and no account changes `[AC-5.5]`
- [ ] Given the email provider rejects the send, when the user clicks `Send a new link`, then the page shows `We could not send the email, try again` and no new link is issued `[AC-5.6]`

## Implementation Tasks

- [ ] 5.1 Write tests for every acceptance criterion
- [ ] 5.2 Implement the behavior
- [ ] 5.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
