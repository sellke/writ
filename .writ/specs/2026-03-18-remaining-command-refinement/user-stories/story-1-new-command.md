# Story 1: new-command.md Refinement

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** refine new-command.md to A-grade quality
**So that** every line teaches the AI something non-obvious, sets a quality bar, or prevents a specific mistake — with no redundant filler

## Acceptance Criteria

1. **Given** the refined new-command.md, **when** an AI agent executes the command, **then** the contract-first workflow (Phase 1 discovery) remains fully intact and executable without loss of capability.

2. **Given** the refined file, **when** applying the litmus test to every line, **then** each line either teaches something non-obvious, sets a quality bar the AI wouldn't reach alone, or prevents a specific mistake — with no filler.

3. **Given** the refined file, **when** counting lines, **then** the total is within ~200 ±10% (180–220 lines), down from 438.

4. **Given** the refined file, **when** checking for removed sections, **then** the following are cut entirely: AI Implementation Prompt (restates process), Template Selection Logic (hardcoded line numbers), Implementation Details/Validation, Documentation Update Locations, Future Enhancements, Integration Notes, Error Handling.

5. **Given** the refined file, **when** reviewing the echo check, **then** the contract format is expressed as principles (name, purpose, unique value, execution style, workflow, inputs, outputs, concerns/recommendations) — not an exact markdown template.

## Implementation Tasks

1. **Read the current file** — Verify line numbers for sections to cut/compress. Confirm Phase 1 discovery conversation, critical analysis responsibility, pushback phrasing, echo check, Phase 2 creation.

2. **Cut AI Implementation Prompt** — The entire block (lines 247–293) restates the process above it. The AI reads the whole file; this adds nothing.

3. **Cut Template Sections and Selection Logic** — Remove per-type template scaffolding (contract style, direct execution, setup, implementation, integration), template selection logic with hardcoded line numbers, documentation update locations.

4. **Cut Implementation Details** — Command name validation regex, conflict checking bash, error handling messages, future enhancements, integration notes. All obvious.

5. **Replace echo check template with principles** — State what a command contract should cover (name, purpose, unique value, execution style, workflow, inputs, outputs, concerns/recommendations) as a principle, not an exact markdown format.

6. **Compress Phase 2 creation** — State what a good command file contains (overview, invocation table, command process, core rules, integration table) and quality bars. Cut the markdown template. Compress validation to a principle about verifying integration consistency.

7. **Verify and tighten** — Apply the litmus test to every remaining line. Preserve contract-first workflow, critical analysis, pushback phrasing, command categories concept. Ensure line count within target.

## Notes

- **Technical:** The contract-first discovery workflow follows the same pattern as create-spec — it's Writ's crown jewel interaction model. Preserve it fully.

- **Risk:** Over-compression of Phase 1 discovery could lose the critical analysis responsibility and pushback phrasing, which are what prevent the AI from being a yes-machine. These are genuinely non-obvious and should be kept verbatim.

- **Watch for:** The hardcoded line numbers in Documentation Update Locations (cc.md ~15-50, ~95-110, ~150-190; README.md ~120-140, ~400-415) break on every edit. This is the clearest litmus test failure in the file.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Line count within target range (~200 ±10%)
- [ ] Contract-first workflow and critical analysis preserved
- [ ] No hardcoded line numbers or markdown templates remain
