# Story 5: Account Deletion

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** user leaving the product
**I want** to delete my account and my data
**So that** nothing about me stays behind

## Acceptance Criteria

> **AC IDs assigned through:** AC-5.4

- [ ] Given a user confirms deletion, when the deletion job completes, then no row in any table contains that user's `user_id` `[AC-5.1]`
- [ ] Given a deleted account, when an admin opens the audit log, then every login event for that user is listed with the user's `user_id` `[AC-5.2]`
- [ ] Given a user who has not confirmed the deletion email, when 24 hours pass, then the request is cancelled and the account is unchanged `[AC-5.3]`
- [ ] Given the deletion job fails partway, when it is retried, then it resumes and finishes without creating duplicate audit entries `[AC-5.4]`

## Implementation Tasks

- [ ] 5.1 Write tests for every acceptance criterion
- [ ] 5.2 Implement the behavior
- [ ] 5.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
