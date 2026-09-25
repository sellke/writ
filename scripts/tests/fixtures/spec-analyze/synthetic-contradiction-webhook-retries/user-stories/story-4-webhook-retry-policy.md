# Story 4: Webhook Retry Policy

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As an** integration developer
**I want** failed webhook deliveries to be retried
**So that** a brief outage on my server does not lose events

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given a webhook delivery that returns a 5xx status, when it fails, then it is retried at most 3 times with 1, 4, and 16 minute delays `[AC-4.1]`
- [ ] Given a delivery that has failed 5 times, when the fifth retry also fails, then the delivery is marked `dead` and an email goes to the endpoint owner `[AC-4.2]`
- [ ] Given a delivery that returns 2xx on any attempt, when the response arrives, then no further retries are scheduled `[AC-4.3]`
- [ ] Given an endpoint URL that does not resolve, when a delivery is attempted, then the attempt counts as a failure and follows the same retry schedule `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write tests for every acceptance criterion
- [ ] 4.2 Implement the behavior
- [ ] 4.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
