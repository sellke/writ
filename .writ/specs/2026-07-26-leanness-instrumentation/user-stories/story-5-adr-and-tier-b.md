# Story 5: ADR-019 & Tier B Audit Format Update

> **Status:** Completed ✅ (2026-07-26)
> **Priority:** Medium
> **Dependencies:** Story 1, Story 2, Story 3, Story 4

## User Story

As a **Writ maintainer and future reader of the decision record**, I want **ADR-019 to document what actually shipped in Stories 1–4 and the Tier B ritual template to consume the new metric set**, so that **the leanness governance model has a durable, honest paper trail — including the trend-line discontinuity — and quarterly audits no longer paste command-only numbers as if they were full-surface weight.**

## Acceptance Criteria

- [x] **Given** `.writ/decision-records/adr-019-full-surface-leanness-measurement.md`, **when** I read it, **then** it follows ADR-015/ADR-018 structure, carries `Extends: [ADR-015]`, and records all three shipped decisions: the coverage-guard principle (why `scripts/` fell outside ADR-015's Non-Duplication Boundary), the ratchet-over-tolerance reversal (partial supersession of `GROWTH_TOLERANCE` while explicitly preserving ADR-015 Alternative B — no hard-FAIL on weight), and the honest trend-line reset (command-only history 10,659 → 10,342 does not translate to full-surface; Alternative C stays rejected).
- [x] **Given** ADR-015 on disk, **when** this story ships, **then** ADR-015 is untouched — supersession is expressed only through ADR-019's `Extends:` / partial-supersession prose, not an in-place edit.
- [x] **Given** `.writ/docs/leanness-audit-format.md`, **when** I read the **Inputs** and **Output Contract → Metrics snapshot** sections, **then** the Tier B ritual instructs maintainers to paste `per_surface`, `total_product_lines`, `story_context_bytes` (with its declared-load proxy label), and `writ_workspace_lines` alongside the legacy `command_lines`/`command_chars` keys — not `command_lines` alone.
- [x] **Given** Stories 1–4 merged and `bash scripts/eval.sh --check=leanness` run on this repo, **when** I inspect the report's Notes block, **then** the `Metrics:` summary line rendered via `add_note` includes the new full-surface fields and `story_context_bytes` is never presented without its proxy disclaimer.
- [x] **Given** the full eval Tier 1 gate, **when** I run `bash scripts/eval.sh`, **then** the run reports `Findings: 0` (no regressions introduced by doc or wiring changes).

## Implementation Tasks

- [x] Read Stories 1–4 "What Was Built" sections (or the merged diff) and draft `.writ/decision-records/adr-019-full-surface-leanness-measurement.md`: `Extends: [ADR-015]`, status Accepted, three decision sections (coverage guard, ratchet reversal, trend reset), Considered Alternatives referencing ADR-015 B/C as preserved/rejected, and Consequences — match ADR-018 numbering and header conventions.
- [x] In ADR-019 Context, explain the Non-Duplication Boundary gap: ADR-015 deferred per-file length to `check_length` and skill boundary to `lint-skill.sh`, but `scripts/` was deferred to nobody and therefore invisible across two audit cycles that reported clean.
- [x] Update `.writ/docs/leanness-audit-format.md`: revise **Inputs** step 1 (Tier A metrics gather) and **Output Contract → Metrics snapshot** to require `per_surface`, `total_product_lines`, `story_context_bytes` (labeled proxy), `writ_workspace_lines`, plus legacy keys; add ADR-019 to the template header references alongside ADR-015.
- [x] Inspect `scripts/eval.sh` `check_leanness` METRIC TSV emission: extend the Python one-liner (or equivalent) so `add_note "Metrics: …"` includes `per_surface`, `total_product_lines`, `story_context_bytes`, and `writ_workspace_lines` when present in the JSON envelope; adjust only if Stories 1–4 did not already land the wiring.
- [x] Add or extend a static assertion in `scripts/tests/test_eval_leanness.sh` (or an existing eval doc-presence check if applicable) that ADR-019 exists and references ADR-015 — documentation story "tests first" via the harness, not unit tests.
- [x] Cross-link ADR-019 References to the owning spec, `scripts/eval-leanness.py`, `.writ/leanness-baseline.json`, and the updated Tier B template; ensure ADR-019 `note` field in baseline reseed (if present) aligns with the recorded discontinuity language.
- [x] Verify acceptance criteria: run `bash scripts/tests/test_eval_leanness.sh`, `bash scripts/eval.sh --check=leanness`, and full `bash scripts/eval.sh` — confirm `Findings: 0`, Notes block shows the expanded Metrics line, and Tier B template reads coherently against a sample JSON paste.

## Notes

- **Last story by design.** This records what shipped, not what was planned. Implement only after Stories 1–4 merge; if implementation choices diverged from spec prose, ADR-019 must reflect reality and call out any delta explicitly.
- **Immutability contract.** ADR-015 stays as the historical record of v1 leanness governance. Partial supersession covers only: aggregate measurement scope (commands-only → full product surface), the `GROWTH_TOLERANCE` warn mechanic (replaced by per-surface ratchet), and the baseline trend semantics (honest reset). Tier A/Tier B split, warn-only growth (Alternative B), dogfooding-only mandate, `add_note` primitive, and directional registry parity remain in force via ADR-015 unless ADR-019 explicitly says otherwise.
- **Trend-line reset is a first-class deliverable.** The only prior history is command-only (10,659 → 10,342, recorded as improvement while complexity moved into unmeasured `scripts/`). ADR-019 must state that full-surface baselines start fresh post-merge and that comparing old command-only audits to new totals is a category error — not a regression.
- **`eval.sh` wiring risk.** The METRIC line is a compact TSV bridge; if the expanded payload is too long for one Notes line, prefer a structured multi-line `add_note` summary over truncating surfaces. Never promote metrics to `add_finding`.
- **No product-surface edits.** No `commands/*.md`, no changes to `/status` allowlist or `.writ/manifest.yaml` command lists — ADR-015 dogfooding-only mandate unchanged.
- **Integration point.** Tier B maintainers paste from either raw `python3 scripts/eval-leanness.py` JSON or the eval.sh Notes block; both paths must describe the same metric keys after this story.

## Definition of Done

- [x] ADR-019 committed with coverage-guard, ratchet reversal, and trend-reset decisions; ADR-015 unmodified.
- [x] `leanness-audit-format.md` updated for the new metric set and ADR-019 reference.
- [x] `check_leanness` Metrics rendering verified (adjusted only if needed).
- [x] All acceptance criteria met.
- [x] Full eval Tier 1 green (`Findings: 0`).

## Context for Agents

- **Files in scope:** `.writ/decision-records/adr-019-full-surface-leanness-measurement.md` (new), `.writ/docs/leanness-audit-format.md`, `scripts/eval.sh` (METRIC/`add_note` wiring only if needed).
- **Format reference:** `.writ/decision-records/adr-015-leanness-self-governance.md` (structure, `Extends:` convention, Non-Duplication Boundary table); `.writ/decision-records/adr-018-third-party-skill-trust-model.md` (most recent numbering/format precedent).
- **Business rules:** `spec.md → ## 📋 Business Rules` → [Rule 4 (only unmeasured surface hard-fails; ADR-015 Alternative B preserved), Rule 6 (dogfooding-only — no user-facing surface), Rule 7 (`story_context_bytes` proxy label at every reporting site)].
- **Experience:** `spec.md → ## 🎯 Experience Design (CLI / CI — no user-facing UI) → ### Feedback Model` (findings via `add_finding`; warnings and metrics via `add_note`); `spec.md → ## Detailed Requirements → ### ADR-019 and Tier B` (durable record + Tier B metric set).
- **Error map rows:** [] — this story produces no new eval findings; it documents existing error semantics from Stories 2 and 4.
- **Shadow paths:** `spec.md → ## Technical Concerns (surfaced at contract time)` → **The trend line resets** (honest discontinuity; Alternative C stays rejected); `spec.md → ## Scope Boundaries → **Excluded, deliberately:**` → [Reopening ADR-015's warn-only decision for growth]; ADR-015 → **Non-Duplication Boundary** (the `scripts/` ownership gap ADR-019 must explain).

---

## What Was Built

**ADR-019, the Tier B format update, and the `eval.sh` Metrics-rendering wiring.**

- `.writ/decision-records/adr-019-full-surface-leanness-measurement.md`
  (new) — `Extends: [ADR-015]`, Status Accepted, matching ADR-015/ADR-018's
  header and section conventions. Documents the three shipped decisions (the
  coverage guard, the ratchet-over-tolerance reversal, the honest trend-line
  reset), a Context section naming the specific Non-Duplication Boundary gap
  (`scripts/` was deferred to nobody, unlike `check_length`/`lint-skill.sh`),
  a "Relationship to ADR-015" table scoping the partial supersession to
  exactly three aspects, Considered Alternatives (A–E, including two —
  hard-FAIL on growth, git-tag trend — that restate and re-affirm ADR-015's
  original rejections rather than reopening them), and Consequences.
  `adr-015-leanness-self-governance.md` is byte-for-byte unmodified
  (git-diff-verified).
- `.writ/docs/leanness-audit-format.md` — header blockquote now cites
  ADR-019 alongside ADR-015. **Inputs** step 1 rewritten to require pasting
  the full `metrics` block (`per_surface`, `total_product_lines`/
  `total_product_chars`, `writ_workspace_lines`, `story_context_bytes`
  **with** `story_context_bytes_note`) plus the retained legacy keys, from
  either raw JSON or the `eval.sh` Notes block. **Baseline delta** step
  rewritten to compare per-surface, not aggregate, and states the 2026-07-26
  reset explicitly (comparing pre-reset command-only figures to post-reset
  totals is named as a category error). **Output Contract → Metrics
  snapshot** rewritten to require the same expanded key set.
- `scripts/eval.sh` — `check_leanness()`'s METRIC-emission Python one-liner
  extended (not replaced): the original legacy `commands=... command_lines=...`
  line is preserved unchanged (a Tier B consumer reading only the first
  METRIC line keeps working), plus three new `METRIC` lines when the keys are
  present: `per_surface: name(lines=…,chars=…), …`, the
  `total_product_lines`/`total_product_chars`/`writ_workspace_lines` rollup,
  and `story_context_bytes=N (proxy note text)` — the proxy label rendered
  inline with the number, never separated.
- `scripts/tests/test_eval_leanness.sh` — 2 static presence assertions (this
  story's "test-first" anchor, since there's no runtime behavior to exercise
  for a documentation story): ADR-019 exists and its text contains
  "ADR-015"; `leanness-audit-format.md` contains "ADR-019",
  "story_context_bytes", and "per_surface".
- **Final real-baseline reseed** (spec-level integration step, run once all
  five stories landed): `python3 scripts/eval-leanness.py --update-baseline`,
  capturing `scripts/` at its final post-rewrite size (19,804 lines — the
  guardian measuring its own doubling, exactly as the spec's Hardest
  Constraint anticipated) with zero unjustified-growth warnings going forward.

### Implementation Decisions

1. **`eval.sh`'s METRIC line is extended, not replaced**, per the story's
   Notes ("prefer a structured multi-line `add_note` summary over
   truncating") — three additional `add_note` lines rather than cramming
   every surface into one TSV row.
2. **No `commands/*.md` or `/status` allowlist changes** — dogfooding-only
   mandate (ADR-015, restated by this story's Business Rule 6) held
   throughout; verified by the unchanged `Findings: 0` parity check.

### Test Results

**Verification:** `bash scripts/tests/test_eval_leanness.sh` — 31/31
assertions pass (full suite, all 5 stories). `bash scripts/eval.sh
--check=leanness`: PASS, `Findings: 0`. Full `bash scripts/eval.sh` (all 27
Tier 1 checks): `Findings: 0`, `Run errors: 0`.

### Review Outcome

**Result:** PASS (self-reviewed against every acceptance criterion; see
Story 1's note on subagent scoping for this spec).

- **Drift:** None.
- **Security:** Clean — documentation and TSV-rendering changes only.

### Deviations from Spec

None.
