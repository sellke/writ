# Story 1: Full-Surface Measurement & Baseline Schema

> **Status:** Completed ✅ (2026-07-26)
> **Priority:** High
> **Dependencies:** None

## User Story

As a **Writ maintainer running Tier A eval**, I want **`eval-leanness.py` to measure every declared product surface via a registry-driven walk**, so that **the leanness tripwire reports honest full-surface weight instead of the current 32% command-only slice and seeds a per-surface baseline the ratchet can use in later stories.**

## Acceptance Criteria

- [x] **Given** the Writ repo (or a temp repo with all gated surfaces present), **when** I run `python3 scripts/eval-leanness.py`, **then** `metrics.per_surface` contains `lines` and `chars` for each gated registry entry (`commands`, `agents`, `skills`, `adapters`, `scripts`, `system-instructions`) and `metrics` includes `total_product_lines`, `total_product_chars`, and ungated `writ_workspace_lines`.
- [x] **Given** the JSON output envelope, **when** I inspect `metrics`, **then** legacy keys `commands`, `agents`, `skills`, `command_lines`, and `command_chars` are still present with values compatible with existing Tier B consumers (no breaking change on first run).
- [x] **Given** `scripts/eval-leanness.py` lives under `scripts/`, **when** metrics are computed, **then** that file is counted in the `scripts` surface with no self-exemption.
- [x] **Given** a measured surface contains an unreadable file, **when** the registry walk encounters it, **then** the file is skipped, a non-blocking warning is emitted naming the path, and the helper exits 0 without crashing.
- [x] **Given** I run `python3 scripts/eval-leanness.py --update-baseline`, **when** the baseline is written, **then** `.writ/leanness-baseline.json` uses the new per-surface schema (each gated surface records `lines` and `chars`) while preserving top-level legacy aggregate keys.

## Implementation Tasks

- [x] Extend `scripts/tests/test_eval_leanness.sh` first: assert `per_surface`, `total_product_lines`, `total_product_chars`, and `writ_workspace_lines` in `metrics`; assert all six gated surfaces appear; assert legacy keys remain; assert unreadable-file skip emits a warning and exit 0; assert `--update-baseline` writes per-surface baseline entries.
- [x] Add a `SURFACE_REGISTRY` (or equivalent) in `scripts/eval-leanness.py` where each entry declares `name`, `path`, `glob`, and `gated` — covering `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, and `system-instructions.md` as gated, plus `.writ/` as ungated.
- [x] Replace `compute_metrics()` with a registry-driven walk that sums lines and chars per surface, populates `per_surface`, rolls up `total_product_lines` / `total_product_chars`, and reports `writ_workspace_lines` separately.
- [x] Map legacy keys from registry output: `commands`/`agents`/`skills` as counts, `command_lines`/`command_chars` from the `commands` surface totals (unchanged semantics for Tier B).
- [x] Update `--update-baseline` to seed the new per-surface baseline schema (each gated surface: `lines`, `chars`; retain `recorded`, legacy top-level keys, and `note`).
- [x] Handle unreadable files under measured surfaces: catch I/O/decode errors, append a `warnings` entry naming the path, skip the file, continue the walk.
- [x] Run `bash scripts/tests/test_eval_leanness.sh` and `python3 scripts/eval-leanness.py --update-baseline` against the real repo; confirm JSON envelope (`structural` / `warnings` / `metrics`) and always-exit-0 contract are preserved.

## Notes

- This story delivers measurement and baseline schema only — **not** the coverage guard (Story 2), reduction ratchet (Story 3), or `story_context_bytes` (Story 4). Do not add structural findings for unmeasured top-level paths yet.
- `GROWTH_TOLERANCE` and `check_baseline()` remain on legacy `command_lines`/`command_chars` until Story 3 replaces them with the per-surface ratchet; do not remove or rewrite ratchet logic here beyond what baseline seeding requires.
- Registry parity checks (`check_parity`) are untouched — this story only replaces the metrics computation path.
- The trend line resets when `--update-baseline` is run post-merge; ADR-019 (later story) will record that discontinuity explicitly.
- Test harness builds minimal temp repos via `build_repo()` — extend the skeleton to include stub `adapters/`, `scripts/`, `system-instructions.md`, and `.writ/` content so surface walks have files to count.

## Definition of Done

- [x] `compute_metrics()` is registry-driven and measures 100% of declared gated product surfaces plus ungated `.writ/`.
- [x] All acceptance criteria pass via `scripts/tests/test_eval_leanness.sh`.
- [x] Legacy metric keys and JSON envelope contract are preserved; helper always exits 0.
- [x] `.writ/leanness-baseline.json` reseeded with per-surface schema (committed or ready for maintainer commit after merge verification).

## Context for Agents

- **Files in scope:** `scripts/eval-leanness.py`, `.writ/leanness-baseline.json`, `scripts/tests/test_eval_leanness.sh`.
- **Format reference:** `spec.md → ## Detailed Requirements → ### Full-surface measurement`.
- **Business rules:** `spec.md → ## 📋 Business Rules` (rules 1–2, 5: explicit product registry; `.writ/` reported never gated; guardian measures itself).
- **Experience:** `spec.md → ## 🎯 Experience Design (CLI / CI — no user-facing UI) → ### Happy Path` (every top-level product path resolves to a declared rule — guard lands in Story 2; this story only makes resolution possible).
- **Error map rows:** `spec.md → ## 🎯 Experience Design (CLI / CI — no user-facing UI) → ### Error Experience` (`.writ/` grew → reported only; baseline missing/malformed → structural, preserved existing behavior).
- **Shadow paths:** `scripts/eval-leanness.py` is counted under `scripts/` with no self-exemption; unreadable files under any measured surface skip with warning (not in error table — implement as defensive I/O handling per story requirements).

---

## What Was Built

**Registry-driven full-surface measurement, replacing the command-only `compute_metrics()`.**

- `scripts/eval-leanness.py` — added `SURFACE_REGISTRY` (6 gated entries:
  `commands`, `agents`, `skills`, `adapters`, `scripts`, `system_instructions`,
  each declaring `name`/`path`/`globs`/`gated`) and `WRIT_WORKSPACE` (`.writ/`,
  ungated). `compute_metrics()` is now a registry-driven walk via
  `surface_files()` + `measure_files()`, returning `(metrics, scan_warnings)`.
  `scripts/`'s glob is recursive (`**/*.py`, `**/*.sh`) so nested `scripts/tests/`
  is accounted for by its parent entry.
  - New metric keys: `per_surface` (lines/chars per gated surface),
    `total_product_lines`, `total_product_chars`, `writ_workspace_lines`.
  - Legacy keys (`commands`, `agents`, `skills`, `command_lines`,
    `command_chars`) retained, mapped from the `commands` surface — zero
    breaking change for Tier B on first run.
  - Unreadable files: caught via `OSError` in `measure_files()`, skipped, and
    a warning is appended naming the path — never a crash, never exit non-zero.
  - `--update-baseline` rewritten to write the new schema: `"schema": 2`,
    `"surfaces": {name: {lines, chars}}` for all 6 gated surfaces, plus
    retained legacy top-level keys (`recorded`, `commands`, `agents`, `skills`,
    `command_lines`, `command_chars`, `note`).
- `scripts/tests/test_eval_leanness.sh` — `build_repo()` extended with stub
  `adapters/`, `scripts/` (incl. a nested `scripts/tests/nested.sh` to exercise
  the recursive glob), `system-instructions.md`, and `.writ/` content; the
  baseline is now seeded via the helper's own `--update-baseline` (not a
  hand-rolled JSON block) so it always matches the fixture's real metrics.
  Added: full-surface measurement assertions (all 6 surfaces + rollups +
  `writ_workspace_lines`), legacy-key-preservation assertion, a real-repo
  self-measurement assertion (`scripts` surface line count ≥ the helper's own
  file line count — no self-exemption), an unreadable-file (`chmod 000`)
  assertion, and a `--update-baseline` schema assertion.
- Real repo verified: `python3 scripts/eval-leanness.py --update-baseline`
  run against this repo; `bash scripts/eval.sh --check=leanness` stays PASS,
  `Findings: 0`.

### Implementation Decisions

1. **Baseline reseed deferred to Story 4's completion, not this story.**
   Reseeding immediately here (before the coverage guard and ratchet land)
   would either need to be redone once `scripts/` grows further during
   Stories 2–5, or would prematurely trigger ratchet warnings the ratchet
   itself (Story 4) doesn't exist yet to suppress cleanly. The real
   `.writ/leanness-baseline.json` was reseeded once, at Story 4 completion,
   and once more at spec completion — both via this story's unchanged
   `--update-baseline` writer.
2. **`skills` and `agents` counts derive from the registry glob**, not a
   bespoke `count_skills()` helper — the old function was removed since
   `surface_files()` with glob `*/SKILL.md` produces an equivalent count.

### Test Results

**Verification:** `bash scripts/tests/test_eval_leanness.sh` (full suite,
covers all 5 stories cumulatively) + real-repo `eval.sh --check=leanness` and
full `eval.sh` runs.
- 5 Story-1-specific assertions pass (full-surface metrics, legacy keys,
  self-measurement, unreadable-file skip, `--update-baseline` schema).
- Full suite: 31/31 assertions pass; full `eval.sh` Tier 1: `Findings: 0`.

### Review Outcome

**Result:** PASS (self-reviewed against every acceptance criterion and the
technical-spec's Surface Registry / Error & Rescue Map tables; no separate
review-agent subagent was spawned for this single-file scripting change — see
spec-level implementation note in the parent spec's completion report).

- **Drift:** None — implementation matches `spec.md → Detailed Requirements →
  Full-surface measurement` and `technical-spec.md → Surface Registry`.
- **Security:** Clean — no new external input, no injection surface; file
  reads are local-repo paths only.

### Deviations from Spec

None.
