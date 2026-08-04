# Story 1 — Config Persistence Layer

> Status: Completed ✅
> Priority: High
> Dependencies: None

## User Story

As a developer using Writ, I want project conventions (default branch, test runner, merge strategy, version file locations, and related settings) read from a single shared store first, with detection only as a fallback, so that `/ship`, `/release`, `/status`, and `/initialize` stop re-deriving the same facts on every run and stay consistent across commands.

## Acceptance Criteria

**Given** the spec and command docs describe `.writ/config.md`
**When** a maintainer reads the format section
**Then** the file’s purpose, location, simple markdown key–value shape, and which keys are supported are defined and easy to follow.

**Given** `commands/ship.md`, `commands/release.md`, and `commands/status.md` after this story
**When** an agent runs any of those commands
**Then** it loads values from `.writ/config.md` when present before running shell/git detection for the same conventions.

**Given** `commands/initialize.md` after greenfield setup completes successfully
**When** the initialize flow finishes
**Then** the command instructs creation or update of `.writ/config.md` with the conventions established during setup (aligned with the shared schema).

**Given** `.writ/config.md` is missing or incomplete for a needed key
**When** detection produces values for that run
**Then** the agent is instructed to ask once: “Save to .writ/config.md? (y/n)” and only writes the file if the user confirms — never auto-saves without offering.

## Implementation Tasks

- [x] Define an AC verification checklist (expected read order, keys, prompt text, and “no auto-save”) and use it as the gate before merging — treat it as the test plan for these markdown-only changes.
- [x] Author `.writ/config.md` as a documented template (or dedicated doc section) specifying supported keys, markdown key–value layout, and examples; reference it from affected commands.
- [x] Update `commands/ship.md` to read `.writ/config.md` first, then detect, then offer persist on first successful detection per session or first missing config.
- [x] Update `commands/release.md` with the same read → detect → offer-to-persist flow for overlapping convention keys.
- [x] Update `commands/status.md` with the same read → detect → offer-to-persist flow for overlapping convention keys.
- [x] Update `commands/initialize.md` so post-setup steps write or merge into `.writ/config.md` using the shared schema (no silent overwrite of user-edited values without clear guidance).
- [x] Walk the verification checklist against all four command files and the config format doc; confirm every AC passes and wording is consistent.

## Technical Notes

- Scope is **markdown instruction files only** (no runtime code in this story): behavior is specified for the AI agent executing the commands.
- **Read order:** parse `.writ/config.md` first; for any required key still unset, run existing detection (shell commands, git queries); after detection, if the file was missing or keys were filled only by detection, prompt **Save to .writ/config.md? (y/n)** — on **y**, write or merge using the documented markdown key–value format; on **n**, continue without writing.
- Keep the config format **human-editable**: plain markdown, one key per line or a small table, with stable key names shared across `ship`, `release`, `status`, and `initialize`.
- Align keys with what commands already infer today (default branch, test command, merge strategy, version/changelog paths, etc.) so one file removes duplicated detection logic across sessions.
- **initialize** is the natural place to **seed** the file after greenfield setup; **ship** / **release** / **status** should **consume** it the same way to close the systemic gap described in the contract summary.

## Definition of Done

- [x] All tasks complete
- [x] All AC verified
- [x] Tests passing
- [x] Code reviewed
- [x] Docs updated if needed
