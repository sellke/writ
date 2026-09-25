# Story 2: Workspace Invites

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** workspace admin
**I want** invite links that expire
**So that** old links forwarded around cannot add strangers to my workspace

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.4

- [ ] Given an invite link, when 7 days have passed since it was sent, then the link is expired and opening it shows `This invite has expired` `[AC-2.1]`
- [ ] Given an invite sent 10 days ago that has not been used, when the invitee opens it, then the invitee joins the workspace as a member `[AC-2.2]`
- [ ] Given an invite link that has already been used, when anyone opens it again, then the page shows `This invite was already used` `[AC-2.3]`
- [ ] Given an admin revokes an invite, when the invitee opens it, then the page shows `This invite was revoked` `[AC-2.4]`

## Implementation Tasks

- [ ] 2.1 Write tests for every acceptance criterion
- [ ] 2.2 Implement the behavior
- [ ] 2.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
