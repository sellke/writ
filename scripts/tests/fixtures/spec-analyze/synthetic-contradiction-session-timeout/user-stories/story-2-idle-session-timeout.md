# Story 2: Idle Session Timeout

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As an** account owner on a shared computer
**I want** idle sessions to end on their own
**So that** someone who sits down after me cannot act as me

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given a signed-in user with no activity, when 15 minutes pass, then the session ends and the next request redirects to `/login` `[AC-2.1]`
- [ ] Given a signed-in user editing a draft with no activity, when 30 minutes pass, then the session is still active and the draft autosaves every 5 minutes `[AC-2.2]`
- [ ] Given a session that has ended, when the user signs in again, then the last autosaved draft opens `[AC-2.3]`
- [ ] Given the session store is unreachable, when a request checks the session, then the request is treated as signed out and redirects to `/login` `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write tests for every acceptance criterion
- [ ] 2.2 Implement the behavior
- [ ] 2.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
