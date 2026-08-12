# `phase-execution-v2` Has No Status For A Spec Closed By Decision

> **Type:** Improvement
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-08-12
> **spec_ref:** .writ/specs/2026-08-12-phase-closure-status/spec.md

## TL;DR

`SPEC_STATUSES` in `scripts/phase-state.py` cannot express "terminated by decision, will never run", so five Phase 10 specs closed on measured evidence still report `pending` and `/status` shows a finished phase as work in flight.

## Current State

- `scripts/phase-state.py:52-55` — `SPEC_STATUSES = {"pending", "implementing", "integrated", "failed", "quarantined", "skipped_blocked"}`.
- None of the six fits a spec the maintainer deliberately chose not to build:
  - `failed` and `quarantined` imply something went wrong and preserve a lane for recovery — nothing failed here.
  - `skipped_blocked` requires a `blockedBy` upstream failure — these were not blocked.
  - `pending` means "not started yet", which is what they report today and is wrong: they will never start.
- Observed: `python3 scripts/phase-state.py progress --state .writ/state/phase-execution-20260812-0200.json` returns `{'pending': 5, 'integrated': 2, ...}` for a phase that closed 2026-08-12. Those five are `2026-08-12-disclosure-{create-spec,implement-phase,release,ship,verify-spec}`, all now archived with `Status: Closed — Not Implemented`.
- `commands/status.md` Step 4 reads these files and surfaces the counts, so the misreport is user-visible on every `/status` run while the file exists.
- Note the contrast: `scripts/spec-status.py:54` already models this correctly at the *spec* layer — `COMPLETE_FAMILY_PREFIXES = ("Complete", "Closed")` treats `Closed` as terminal. The *phase-execution* layer has no equivalent.

## Expected Outcome

- `phase-execution-v2` gains a terminal status for a spec closed by decision (e.g. `closed_unimplemented`), distinct from `failed`/`quarantined` (no recovery path implied) and from `skipped_blocked` (no upstream blocker).
- `scripts/phase-state.py` accepts it, `progress` counts it separately, and `health` does not treat it as outstanding work.
- `/implement-phase` sets it when the decomposition or a mid-run decision closes a spec rather than executing it.
- Existing state files remain readable — the reducer preserves unknown fields today, so the change should be additive.

## Why This Is Filed Rather Than Fixed

`/refresh-command` surfaced this signal during the 2026-08-12 `/implement-phase` refresh and **rejected it with reason `no evidence`** — correctly. It is a schema change to the reducer, not a command-file amendment, and `/refresh-command` amends commands. See `.writ/refresh-log.md` → *2026-08-12 — /implement-phase refreshed* → **Rejected**.

Hand-editing the JSON to make `/status` read correctly was considered and rejected: it would leave the schema unable to express the state, which is the same defect one layer down.

## Relevant Files

- `scripts/phase-state.py` — `SPEC_STATUSES`, `cmd_progress`, `cmd_health`
- `.writ/docs/phase-execution-state-format.md` — the canonical schema contract
- `commands/implement-phase.md` — Step 1.2b / Step 3.3, where a spec gets closed
- `commands/status.md` Step 4 — the consumer that misreports today
- `.writ/state/phase-execution-20260812-0200.json` — the live instance showing `pending: 5`
