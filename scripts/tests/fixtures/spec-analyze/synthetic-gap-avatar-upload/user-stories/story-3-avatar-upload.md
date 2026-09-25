# Story 3: Avatar Upload

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** member of a team workspace
**I want** to upload a profile picture
**So that** teammates can recognize me in comment threads

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.3

- [ ] Given a PNG or JPEG file under 5 MB, when the user uploads it, then the avatar is replaced and shown at 128x128 pixels `[AC-3.1]`
- [ ] Given an image file larger than 5 MB, when the user uploads it, then the upload is rejected with `File must be 5 MB or smaller` and the old avatar stays `[AC-3.2]`
- [ ] Given a user with no uploaded avatar, when their profile renders, then their initials are shown in a colored circle `[AC-3.3]`

## Implementation Tasks

- [ ] 3.1 Write tests for every acceptance criterion
- [ ] 3.2 Implement the behavior
- [ ] 3.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
