# Story 3: `/retro` product-drift nudge

> **Status:** Completed ✅
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

As a **Writ user**, I want `/retro` to nudge me when my product docs look like
they're drifting, so that reconciliation happens at a natural reflection point
instead of only when I happen to notice.

## Acceptance Criteria

1. **Given** `retro.md`, **then** it gains a read-only product-drift nudge step
   modeled on Step 5.5 (Knowledge Consolidation Nudge) — mutates nothing, never
   blocks or slows the retro.
2. **Given** a drift signal (a roadmap phase completed after `mission.md`'s Last
   Updated, or a mission phase label contradicting roadmap status), **when**
   `/retro` runs, **then** it prints a one-line advisory pointing to
   `/verify-spec --product` or `/plan-product --reconcile`.
3. **Given** product docs are consistent (no signal), **when** `/retro` runs,
   **then** the nudge prints nothing.
4. **Given** no `.writ/product/` directory, **when** `/retro` runs, **then** the
   nudge skips silently with no error.

## Implementation Tasks

- [x] 3.1 Add the product-drift nudge step to `retro.md`, mirroring Step 5.5's
      read-only, skip-gracefully contract.
- [x] 3.2 Define the cheap drift signal (date comparison + phase-label mismatch).
- [x] 3.3 Write the one-line advisory copy pointing to the two remedy commands.
- [x] 3.4 Specify silent-skip behavior for no-signal and no-product-docs cases.

## Technical Notes

- Only suggest commands on the `/status` allowlist — `/verify-spec` and
  `/plan-product` already qualify.
- The signal must be cheap and observable (file dates + phase labels); do not
  parse deeply or run anything mutating.

## Definition of Done

- [x] All acceptance criteria pass.
- [x] Nudge is read-only and mirrors Step 5.5.
- [x] Silent with no signal and when product docs are absent.
