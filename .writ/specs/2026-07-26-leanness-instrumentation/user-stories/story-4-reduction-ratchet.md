# Story 4: Reduction Ratchet Replaces Growth Tolerance

> **Status:** Completed ✅ (2026-07-26)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

As a **Writ maintainer enforcing the roadmap's "keep the harness light" posture**, I want **the leanness tripwire to ratchet downward on every surface instead of tolerating silent growth up to +10%**, so that **any weight increase is a deliberate, recorded act with a one-line justification and reductions are free and automatic.**

## Acceptance Criteria

- [x] **Given** a per-surface baseline from Story 1 and a measured surface whose current `lines` (or `chars`) is **≤** the recorded baseline, **when** `python3 scripts/eval-leanness.py` runs, **then** that surface produces no warning and `--update-baseline` rewrites the baseline entry down to the current value for that metric.
- [x] **Given** a measured surface whose current value is **>** the baseline and the baseline entry contains a non-empty `justification` string for that surface, **when** the check runs, **then** the increase is silent (zero warnings for that surface) and the helper still exits 0.
- [x] **Given** a measured surface whose current value is **>** the baseline with no `justification` (missing, empty, or whitespace-only), **when** the check runs, **then** `warnings` contains an entry naming the surface, baseline value, current value, and delta — and `structural` remains empty for that condition.
- [x] **Given** a missing or malformed baseline file, **when** the check runs, **then** existing structural-finding behavior is preserved (baseline error in `structural`, not silently passed) and count-ceiling warnings (`MAX_COMMANDS` / `MAX_AGENTS` / `MAX_SKILLS`) still emit as warn-only when exceeded.
- [x] **Given** `GROWTH_TOLERANCE` and the legacy aggregate-only comparison are removed, **when** I inspect `scripts/eval-leanness.py`, **then** `check_baseline()` compares every gated registry surface against its per-surface baseline entry — not `command_lines`/`command_chars` alone via a percentage tolerance.

## Implementation Tasks

- [x] Extend `scripts/tests/test_eval_leanness.sh` first with temp-dir ratchet fixtures: (a) decrease branch — current ≤ baseline → zero warnings; (b) justified increase — non-empty `justification` → zero warnings; (c) unjustified increase → warning naming surface, baseline, current, and delta with zero structural findings; (d) `--update-baseline` on a decreased surface rewrites baseline down; replace Scenario 4's `+10%` tolerance test with the unjustified-increase case.
- [x] Delete `GROWTH_TOLERANCE` from `scripts/eval-leanness.py` and remove the `base * (1 + GROWTH_TOLERANCE)` comparison path from `check_baseline()`.
- [x] Extend the baseline schema in `.writ/leanness-baseline.json` (and the `--update-baseline` writer) so each gated surface records `lines`, `chars`, and an optional `justification` string; retain top-level legacy keys (`recorded`, `commands`, `agents`, `skills`, `command_lines`, `command_chars`, `note`) for Tier B compatibility.
- [x] Rewrite `check_baseline()` to iterate gated registry surfaces from Story 1's `metrics.per_surface`, comparing current `lines` and `chars` against the matching baseline entry and applying the three ratchet branches (decrease silent / justified increase silent / unjustified increase warns).
- [x] Update `--update-baseline` so decreases auto-ratchet the stored baseline down, justified increases persist the new values (and retain or clear `justification` per the chosen write contract documented in-code), and the writer never promotes growth warnings to structural findings.
- [x] Preserve `check_ceilings()` and missing/malformed baseline structural handling unchanged; confirm growth warnings flow only through `warnings` and never increment `eval.sh`'s findings counter.
- [x] Verify acceptance criteria: run `bash scripts/tests/test_eval_leanness.sh`, `python3 scripts/eval-leanness.py` against this repo (zero unjustified-increase warnings on a clean tree), and `bash scripts/eval.sh --check=leanness` with `Findings: 0`.

## Notes

- **The design reversal.** Today's `GROWTH_TOLERANCE = 0.10` can only ever *fail to complain* — it permits silent drift up to a threshold and has no mechanism to drive weight down. The ratchet inverts that posture: down is free, up costs a sentence (Business Rule 3). ADR-015 already accepted this friction class for baseline bumps ("intentional and rare").
- **Do not reopen ADR-015 Alternative B.** Hard-FAILING on weight growth was rejected; only Story 2's coverage guard adds structural teeth. Growth stays warn-only via `add_note`; unjustified increases must never appear in `structural`.
- **Alternative C stays settled.** The trend line resets with Story 1's full-surface baseline — do not derive history from git tags. ADR-019 (later story) records the discontinuity explicitly.
- **Metric choice for comparison.** Compare both `lines` and `chars` per surface; either exceeding its baseline triggers the ratchet branch for that metric. Warnings should name which metric (`lines` or `chars`) exceeded.
- **Test harness seam.** Story 1's `build_repo()` and per-surface baseline seeding supply the fixture skeleton; this story adds surface-specific baseline entries with controlled deltas and justification fields. Scenario 4 in the existing harness explicitly tests tolerance — replace it, do not accumulate a dead code path.
- **Integration point.** `check_baseline()` receives `metrics` from the registry-driven `compute_metrics()` introduced in Story 1; it does not re-walk the filesystem. Coverage guard (Story 2) and `story_context_bytes` (Story 3) are orthogonal — do not gate or ratchet the context metric unless spec scope expands later.

## Definition of Done

- [x] `GROWTH_TOLERANCE` deleted; per-surface ratchet logic replaces tolerance comparison in `check_baseline()`.
- [x] All acceptance criteria pass via `scripts/tests/test_eval_leanness.sh`.
- [x] `.writ/leanness-baseline.json` migrated to per-surface schema with justifications ready for legitimate bumps.
- [x] JSON envelope contract preserved (`structural` / `warnings` / `metrics`); helper always exits 0.
- [x] Real-repo eval Tier 1 stays green (`Findings: 0`); growth remains warn-only only.

## Context for Agents

- **Files in scope:** `scripts/eval-leanness.py`, `.writ/leanness-baseline.json`, `scripts/tests/test_eval_leanness.sh`.
- **Format reference:** `spec.md → ## Detailed Requirements → ### Reduction ratchet`.
- **Business rules:** `spec.md → ## 📋 Business Rules` → [Rule 3 (down is free; up costs a sentence), Rule 4 (only unmeasured surface hard-fails — growth stays warn-only; do not reopen ADR-015 Alternative B)].
- **Experience:** `spec.md → ## 🎯 Experience Design (CLI / CI — no user-facing UI) → ### Error Experience` → [Measured surface grew without a baseline justification (warning), Baseline missing or malformed (structural, preserved)]; `spec.md → ## 🎯 Experience Design (CLI / CI — no user-facing UI) → ### Feedback Model` (warnings via `add_note` never touch findings counter).
- **Error map rows:** `spec.md → ## 🎯 Experience Design (CLI / CI — no user-facing UI) → ### Error Experience` → [Measured surface grew without a baseline justification, Baseline missing or malformed].
- **Shadow paths:** `spec.md → ## Scope Boundaries → **Excluded, deliberately:**` → [Reopening ADR-015's warn-only decision for growth]; ADR-015 → **Considered Alternatives** → [B (hard-FAIL on growth — rejected), C (git-tag trend — rejected)].

---

## What Was Built

**Per-surface reduction ratchet, replacing `GROWTH_TOLERANCE` entirely.**

- `scripts/eval-leanness.py` — deleted `GROWTH_TOLERANCE = 0.10` and the
  `base * (1 + GROWTH_TOLERANCE)` aggregate comparison. Rewrote
  `check_baseline()`:
  - Missing/malformed baseline → structural finding (unchanged behavior).
  - Baseline present but `schema != 2` or no `surfaces` dict (legacy
    pre-full-surface format) → a distinct structural finding pointing at
    `--update-baseline` (the one-time migration path from
    `technical-spec.md → Error & Rescue Map`).
  - Otherwise: for each `SURFACE_REGISTRY` entry with a matching
    `surfaces[name]` baseline record, compares **both** `lines` and `chars`
    independently. `current <= baseline` → silent. `current > baseline` with
    a non-empty (stripped) `justification` → silent. `current > baseline`
    with no justification → a warning naming the surface, metric
    (`lines`/`chars`), baseline value, current value, and delta. A surface
    with no prior baseline record (newly added) is skipped — no history to
    ratchet yet, not an error.
  - `--update-baseline` extended: every gated surface's `justification`
    field resets to `""` on every reseed (documented in-code: a
    justification describes a specific delta, and that delta stops existing
    once absorbed into a fresh baseline).
  - `check_ceilings()` untouched — count-ceiling warnings remain warn-only,
    orthogonal to the ratchet.
- `scripts/tests/test_eval_leanness.sh` — `build_repo()`'s baseline seeding
  now calls the helper's own `--update-baseline` (schema 2) instead of a
  hand-rolled legacy JSON block, so every existing scenario continues to
  exercise the current schema. **Replaced** the old `+10%`-tolerance
  scenario with 5 ratchet scenarios: decrease → silent + `--update-baseline`
  ratchets down; unjustified increase → warning naming surface + delta, zero
  structural; justified increase (non-empty `justification`) → silent;
  legacy (schema-1) baseline → structural finding pointing at
  `--update-baseline`; count-ceiling warnings still fire alongside the
  ratchet (40 extra commands + matching README rows, past `MAX_COMMANDS`).
- **Real baseline reseeded twice**: once at this story's completion
  (`python3 scripts/eval-leanness.py --update-baseline`, capturing the
  trend-line reset the spec calls for), and once more after Story 5's
  `eval.sh` wiring edit grew `scripts/` further (see spec-level integration
  note). Both reseeds are silent, `Findings: 0` runs.

### Implementation Decisions

1. **`--update-baseline` always clears `justification` to `""`** rather than
   preserving old text — documented in-code as the chosen write contract per
   the story's explicit "retain or clear... documented in-code" instruction.
   Rationale: a justification is scoped to a specific past delta; once a
   reseed absorbs that delta into the new baseline, the old justification
   text no longer describes anything measurable, and a genuinely new future
   increase deserves its own fresh justification rather than inheriting one.
2. **Both `lines` and `chars` are compared per surface**, each independently
   eligible to warn, per the story's Notes ("either exceeding its baseline
   triggers the ratchet branch... name which metric exceeded").

### Test Results

**Verification:** `bash scripts/tests/test_eval_leanness.sh` — 29/29
assertions pass (cumulative through Story 4). Real-repo
`python3 scripts/eval-leanness.py` and `bash scripts/eval.sh --check=leanness`
both verified clean (`Findings: 0`) immediately after each real-baseline
reseed.

### Review Outcome

**Result:** PASS (self-reviewed against every acceptance criterion; see
Story 1's note on subagent scoping for this spec).

- **Drift:** None. `GROWTH_TOLERANCE` fully removed (grep-verified — only
  explanatory code comments reference the old name).
- **Security:** Clean.

### Deviations from Spec

None.
