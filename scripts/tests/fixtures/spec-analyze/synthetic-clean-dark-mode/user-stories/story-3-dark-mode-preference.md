# Story 3: Dark Mode Preference

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** None

## User Story

**As a** user who works late
**I want** a dark mode toggle that remembers my choice
**So that** the app does not glare at night

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [ ] Given the toggle is off, when the user turns it on, then the dark theme applies immediately and `theme=dark` is saved to their profile `[AC-3.1]`
- [ ] Given the toggle is on, when the user turns it off, then the light theme applies immediately and `theme=light` is saved to their profile `[AC-3.2]`
- [ ] Given a saved `theme` preference, when the user loads the app on any device, then that theme applies before the first paint `[AC-3.3]`
- [ ] Given a user with no saved preference, when the app loads, then the theme follows the operating system setting `[AC-3.4]`
- [ ] Given saving the preference fails, when the user turns the toggle on, then the dark theme still applies for the current session and a `Preference not saved` notice is shown `[AC-3.5]`

## Implementation Tasks

- [ ] 3.1 Write tests for every acceptance criterion
- [ ] 3.2 Implement the behavior
- [ ] 3.3 Verify all acceptance criteria are met

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
