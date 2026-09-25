# Story 4: API Rate Limit

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** platform operator
**I want** a per-key rate limit on the public API
**So that** one client cannot starve the others

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given a valid API key, when it makes its 1st through 100th request within a calendar minute, then no request receives a `429` response `[AC-4.1]`
- [ ] Given a valid API key, when it makes a 101st request within the same calendar minute, then the response is 429 with a `Retry-After` header giving the seconds until the next minute `[AC-4.2]`
- [ ] Given a request with no API key, when it arrives, then the response is 401 with `missing_api_key` and it does not count toward any limit `[AC-4.3]`
- [ ] Given a request with an unknown or revoked API key, when it arrives, then the response is 401 with `invalid_api_key` `[AC-4.4]`
- [ ] Given the rate-limit counter store is unreachable, when a request arrives, then the request is served and a `rate_limit_store_down` warning is logged `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write tests for every acceptance criterion
- [ ] 4.2 Implement the behavior
- [ ] 4.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
