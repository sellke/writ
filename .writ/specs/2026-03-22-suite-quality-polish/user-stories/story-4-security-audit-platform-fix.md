# Story 4: Remove Platform-Specific Example from `/security-audit`

> **Status:** Completed ✅ (2026-03-22)
> **Priority:** Low
> **Dependencies:** None

## User Story

**As a** Writ user on any AI platform
**I want to** see platform-agnostic guidance in all core commands
**So that** the framework doesn't assume I'm using a specific platform

## Acceptance Criteria

- [x] Given the security-audit command, when I search for "openclaw" or "OpenClaw", then no results are found
- [x] Given the security-audit scheduling section, when I read it, then it provides platform-agnostic guidance about scheduling periodic audits

## Implementation Tasks

- [x] 4.1 In `commands/security-audit.md`, replace the "Cron integration (OpenClaw)" subsection (~lines 492-501) with a platform-agnostic scheduling note
- [x] 4.2 Keep the "Recommended cadence" section as-is (it's already platform-agnostic)
- [x] 4.3 Verify no other OpenClaw-specific references exist in the file

## Notes

- The replacement should be brief — something like "Schedule periodic audits using your platform's task scheduling (cron, CI pipeline, or platform-native scheduling). Run `--quick` weekly and full audit monthly."
- Don't add examples for every platform — just state the principle

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] No platform-specific tool references in the command
