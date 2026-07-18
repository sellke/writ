# Story 2: Policy + Product-Layer Reconciliation

> **Status:** Completed ✅

## User Story

As an agent orienting on any Writ run, I want the policy surfaces and product
docs to describe the redistributed `--recommend` accurately, so that I never act
on the superseded single-spec / production-approval framing.

## Acceptance Criteria

- [x] Given `system-instructions.md` and `cursor/writ.mdc`, then both describe `--recommend` on exactly two commands and the human production boundary (no merge/PR/release).
- [x] Given `commands/_preamble.md`, then the Narrow Recommended-Delivery Exception matches the revised policy.
- [x] Given the adapters, then none map the retired single-command production flow onto active surfaces (codex/claude-code describe the two-command path).
- [x] Given `mission.md`, `mission-lite.md`, `roadmap.md`, then the autonomy language matches the revised policy and `roadmap` records the direction change.
- [x] Given `.writ/context.md`, then it is regenerated to current reality (branch, version, active work).
- [x] Given ADR-013, then the 2026-07-17 revision states the redistributed policy directly, with the original single-spec shape recorded in Rejected Alternatives and Revision History.

## Implementation Tasks

- [x] 2.1 `system-instructions.md` + `cursor/writ.mdc` recommended-delivery section
- [x] 2.2 `commands/_preamble.md` exception text
- [x] 2.3 Adapters (`cursor`, `claude-code`, `codex`, `openclaw`)
- [x] 2.4 Product layer: `mission.md`, `mission-lite.md`, `roadmap.md` (+ Recommend Redistribution entry), `.writ/context.md`
- [x] 2.5 ADR-013 revision (2026-07-17)
- [x] 2.6 `/verify-spec --product` passes (P1–P4 green, 2026-07-17)

## Definition of Done

- [x] All policy + product surfaces consistent with the revised policy
- [x] `/verify-spec --product` clean
- [x] No superseded framing on active surfaces
