# Story 4: Alert Bursts

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As an** on-call engineer
**I want** alert bursts to be managed
**So that** a flapping check does not flood my phone

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.4

- [ ] Given a single alert, when it fires, then one push notification is sent within 10 seconds `[AC-4.1]`
- [ ] Given more than 10 alerts for the same check within one minute, when the eleventh arrives, then notifications for that check are handled appropriately `[AC-4.2]`
- [ ] Given an alert that resolves, when the check passes, then a `resolved` notification is sent `[AC-4.3]`
- [ ] Given the push provider returns an error, when a notification is sent, then it is retried once and then sent by SMS `[AC-4.4]`

## Implementation Tasks

- [ ] 4.1 Write tests for every acceptance criterion
- [ ] 4.2 Implement the behavior
- [ ] 4.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
