# Story 2: User Profile Endpoint

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** mobile client developer
**I want** a `GET /users/{id}` endpoint
**So that** the app can show a user's profile screen

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.3

- [ ] Given an existing user id, when the client calls `GET /users/{id}`, then the response is 200 with `id`, `display_name`, and `avatar_url` `[AC-2.1]`
- [ ] Given a user with no avatar, when their profile is fetched, then `avatar_url` is `null` `[AC-2.2]`
- [ ] Given the same id is requested twice within 60 seconds, when the second request arrives, then it is served from cache `[AC-2.3]`

## Implementation Tasks

- [ ] 2.1 Write tests for every acceptance criterion
- [ ] 2.2 Implement the behavior
- [ ] 2.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
