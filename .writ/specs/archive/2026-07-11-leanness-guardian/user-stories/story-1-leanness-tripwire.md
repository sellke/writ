# Story 1: Leanness Tripwire (Tier A eval check)

> **Status:** Complete
> **Priority:** High
> **Dependencies:** None

## User Story

As the **Writ maintainer**, I want an automated CI check that measures the
framework's aggregate surface and cross-registry consistency, so that bloat and
dead surface are caught on every PR instead of only when I happen to notice.

## Acceptance Criteria

1. **Given** the current clean repo, **when** I run
   `bash scripts/eval.sh --check=leanness`, **then** the check reports PASS with
   zero structural findings.
2. **Given** a command file absent from the README command table or the
   `/status` allowlist, **when** the check runs, **then** it FAILS with a
   structural finding naming the orphan and the missing registry.
3. **Given** a name in the README table or `/status` allowlist with no matching
   file, **when** the check runs, **then** it FAILS with a phantom finding.
4. **Given** aggregate command weight grows >10% over `.writ/leanness-baseline.json`,
   **when** the check runs, **then** it emits a non-blocking WARNING (exit 0) that
   names the baseline file and how to bump it.
5. **Given** the check exists, **then** it does **not** re-validate manifest
   parity (owned by `check_manifest`) or per-file length (owned by `check_length`).

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_eval_leanness.sh` first — assert clean PASS,
      injected orphan FAIL, injected phantom FAIL (tests before implementation).
- [x] 1.2 Create `scripts/eval-leanness.py` — parse `commands/*.md` (excl.
      `_preamble.md`), README command table, `/status` allowlist; compute
      registry parity + counts + aggregate weight; emit JSON (`structural`,
      `warnings`, `metrics`); always exit 0.
- [x] 1.3 Create `.writ/leanness-baseline.json` seeded with real current numbers.
- [x] 1.4 Register `leanness` in `CHECKS=()` and add `check_leanness()` in
      `scripts/eval.sh` — structural → `add_finding` (FAIL); warnings → report
      body only (no `add_finding`, stays exit 0).
- [x] 1.5 Update any eval self-test/assertion that enumerates the check list to
      include `leanness`; run full `bash scripts/eval.sh` and confirm green.
- [x] 1.6 Author `.writ/decision-records/adr-015-leanness-self-governance.md`.

## Technical Notes

- Runner maps `leanness` → `check_leanness` via `check_${check//-/_}`.
- Warn-only outcomes must keep `CURRENT_FINDINGS` at 0 (see technical-spec note
  on `add_finding` semantics).
- Count ceilings: commands >35, agents >10, skills >12 (headroom over 31/7/6).

## Definition of Done

- [x] All acceptance criteria pass.
- [x] `scripts/eval.sh --check=leanness` PASS on current repo; fixture test green.
- [x] Full `scripts/eval.sh` suite still green with `leanness` registered.
- [x] ADR-015 committed.
- [x] No new `commands/*.md`; `/status` allowlist and manifest lists unchanged.

## What Was Built

**Tier A leanness tripwire — dogfooding CI check.**

- `scripts/eval-leanness.py` — stdlib-only helper. Emits
  `{structural, warnings, metrics}` JSON, always exit 0. Flags:
  `--root`, `--baseline`, `--update-baseline` (deliberate-bump path).
  - **Metrics** (`--check=leanness` surfaces these via a non-blocking Notes
    block; Story 2's ritual consumes them): `commands`, `agents`, `skills`,
    `command_lines`, `command_chars`. `commands` counts **all** `commands/*.md`
    including `_preamble` (matches the baseline convention). Live values:
    `commands=31 agents=7 skills=6 command_lines=10659 command_chars=484616`.
  - **Structural (hard-FAIL):** directional registry parity + missing/malformed
    baseline. README `## Commands` table ↔ files is bidirectional; `/status`
    "Maintainer Note" allowlist → files is phantom-only (see DEV-001). README
    parsing is scoped to the `## Commands` section and ignores fenced code so
    stray `/agent`-style tokens in other tables can't create false phantoms.
  - **Warnings (non-blocking):** count ceilings (commands>35, agents>10,
    skills>12) and aggregate weight growth >+10% vs baseline.
- `scripts/eval.sh` — appended `leanness` to `CHECKS`, added `check_leanness()`,
  and introduced a **reusable `add_note` primitive** (+ `CURRENT_NOTES`/`NOTE_TMP`
  and a "Notes (non-blocking)" report block in `run_check`) so warnings/metrics
  render even on PASS without touching the findings counter (stays exit 0).
- `scripts/tests/test_eval_leanness.sh` — 8 assertions covering clean PASS,
  directional non-orphan, metrics, orphan FAIL, phantom FAIL (both registries),
  growth WARNING, and missing-baseline hard error.
- `.writ/leanness-baseline.json` — committed, seeded from the helper's own
  metrics (real numbers).
- `.writ/decision-records/adr-015-leanness-self-governance.md` — durable stance.

**How Story 2 consumes this:** run `python3 scripts/eval-leanness.py` for the
raw metrics JSON, or `bash scripts/eval.sh --check=leanness` and read the
"Notes (non-blocking)" block for the metrics summary line.

**Contract deviation:** registry parity is directional, not "both registries"
(user-approved; recorded as DEV-001 in `../drift-log.md`).
