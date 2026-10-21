# Story 1: Strip Internal References and Add `shipped-refs`

> **Status:** Completed ✅
> **Commit:** bba00cb3c96be08983d752db1aaf81200bf0dc97
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer who installs Writ into a project
**I want to** read shipped commands whose paths all exist in my project or are placeholders for my own files
**So that** no command sends me or my agent to an ADR, archived spec, research document, or calibration record that only exists in Writ's source repo, and an eval check keeps it that way

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given a temp root whose `commands/x.md` holds one line of each internal-reference kind (a `../.writ/decision-records/adr-013-….md` link, a `../../decision-records/adr-009-….md` link, a dated `.writ/specs/archive/<date>-<name>/` path, an old `.writ/specs/<date>-<name>/` path whose folder exists under `.writ/specs/archive/`, a dated `.writ/research/<date>-….md` path, and a `calibrated_against:` value naming `.writ/state/phase-execution-20260719-121255.json`), when `python3 scripts/eval-shipped-refs.py --root <tmp>` runs, then it prints one FAIL line per hit naming `commands/x.md:<line>`, the kind, and the token `[AC-1.1]`
- [x] Given the same root holding only runtime paths (`.writ/state/` in prose, `.writ/state/phase-execution-*.json` on a `calibrated_against:` line, `.writ/specs/<name>/`, `.writ/specs/archive/<name>/`, `.writ/specs/archive/LEDGER.md`, `.writ/research/[DATE]-[topic-name]-research.md`, `.writ/decision-records/adr-*.md`, `.writ/docs/spec-lifecycle.md`, an example ID such as `.writ/specs/2026-03-15-auth-system/spec.md` with no archive folder), when the helper runs, then it prints no FAIL line, and every rule's self-test scenario prints PASS `[AC-1.2]`
- [x] Given a temp copy of `scripts/eval.sh`, `scripts/eval-shipped-refs.py`, and a clean `commands/` tree, when `bash scripts/eval.sh --check=shipped-refs` runs before and after one ADR link is appended to a command, then it exits 0 before, exits 1 after with a FAIL finding naming that file and line, and exits 0 again once the link is removed; with the helper deleted it exits 2 `[AC-1.3]`
- [x] Given the real tree after this story, when `bash scripts/eval.sh --check=shipped-refs` runs, then it passes with 0 findings; the contract grep over `commands/*.md` returns only runtime paths and `calibrated_against` values that cite shipped files; and every removed link left no bare `ADR-NNN` label behind `[AC-1.4]`
- [x] Given the rewritten `calibrated_against` values in `implement-phase.md`, `implement-spec.md`, `implement-story.md` (two units), and `refactor.md`, when `bash scripts/eval.sh --check=loop-bounds` runs, then it passes; each value keeps a shipped path token or `no recorded run`; `refactor.md`'s value still contains `no recorded run`; and no value names `.writ/state/` or `.writ/specs/archive/` except as a glob `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing tests in a new `scripts/tests/test_eval_shipped_refs.py`: per-kind positive fixtures and runtime-path negatives against `eval-shipped-refs.py --root <tmp>`, and the eval-level mutation (clean → link added → link removed → helper missing), copying `eval.sh` into a temp `scripts/` the way `scripts/tests/test_product_check_direction.py` does `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.2 Implement `scripts/eval-shipped-refs.py`: the four rules from technical-spec.md → Rules, the scanned-directory constant (`commands` only), `--root`, one self-test scenario per rule, PASS/FAIL TSV; Python 3.9 standard library `[AC-1.1, AC-1.2]`
- [x] 1.3 Add `check_shipped_refs` to `scripts/eval.sh` (missing-helper run error, FAIL → `add_finding`, PASS → scenario counts) and register `shipped-refs` in `CHECKS` after `referenced-paths` `[AC-1.3]`
- [x] 1.4 Re-inventory: run the helper and the contract grep on the current tree (expect about 19 lines in about 12 files; `2026-10-20-harness-cuts` may already have removed `retro.md`'s ADR-025 row). Remove each ADR, archived-spec, and research reference with its label, adding the replacement sentences from technical-spec.md → Replacement sentences only where listed `[AC-1.4]`
- [x] 1.5 Rewrite the five `calibrated_against` values from technical-spec.md → Calibration value rewrites, reading each unit name from the file first `[AC-1.5]`
- [x] 1.6 Verify the checks: `bash scripts/eval.sh --check=shipped-refs`, `--check=loop-bounds`, `--check=broken-refs`, `--check=referenced-paths` all pass; run the AC-1.3 mutation by hand on a temp copy and see it fail `[AC-1.3, AC-1.4, AC-1.5]`
- [x] 1.7 Verify the suites: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox) with 0 findings `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Only links.** Bare `ADR-NNN` labels that were never links stay (spec.md → Grounding Notes). Do not widen the edit.
- **Pinned text nearby.** `check_refresh_evidence` pins "structural only — not an LLM-as-judge" in `refresh-command.md`, next to the research link. Keep that phrase. Run `--check=refresh-evidence` after the edit.
- **`calibrated_against` checks.** `scripts/eval-loop-bounds.py` reads only assertion 4 (path token or `no recorded run`) and the refactor literal from the value. Assertion 8 cross-reads the bound numbers from command prose and agent files, not from the citation.
- **Old-path rule.** The `archived-spec` rule's second form checks `<root>/.writ/specs/archive/<name>/` on disk. Tests must create that folder in the temp root. Example IDs in command docs never match because no such folder exists.
- **`.lean.md`.** The helper skips `*.lean.md` because those never ship. After `2026-10-20-harness-cuts` there are none.
- **Technical spec:** `sub-specs/technical-spec.md` → Current State → Internal references in shipped commands (the per-line table), and → Story 1: Shipped-Refs Check (rules, output, replacement sentences, calibration value rewrites).
- **Product files.** Every `commands/` edit ships to users. Change only the reference lines and their replacement sentences. Check `git diff` before each commit.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Run `shipped-refs`, Strip a link, Rewrite `calibrated_against`, Rewrite refactor's value]
- **Shadow paths:** []
- **Business rules:** [Shipped commands, Internal reference kinds, Runtime paths stay, Removal, `calibrated_against` stays, Runtime]
- **Experience:** [Journey, State Catalog]

---

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

1. **`scripts/eval-shipped-refs.py`** (203 lines)
   - Dev-only emitter for the four rules in technical-spec.md → Rules (`adr`, `archived-spec` in archive and old form, `research`, `calibration-state`). Scanned directories live in one constant, `SCANNED_DIRS = ("commands",)`. Takes `--root`. Prints one self-test scenario per rule first, then `FAIL\tshipped-refs:<file>:<line>\t<kind>: <token>` per hit or `PASS\tshipped-refs-tree`. Exit 0 clean, 1 on any FAIL, 2 when no `commands/*.md` exists. Python 3.9 standard library.
2. **`scripts/tests/test_eval_shipped_refs.py`** (272 lines)
   - 13 tests: per-kind positives, runtime-path negatives, a dead regex per rule, `_preamble.md` scanned, `agents/` not scanned, the single scan constant, missing `commands/`, the eval-level mutation (exit 0 → 1 → 0 → 2), `CHECKS` order, and the real tree.

### Files Modified

- **`scripts/eval.sh`** (`check_shipped_refs`, `CHECKS`)
  - New check after `referenced-paths`. Missing helper → run error + finding. Helper exit above 1 or no tree verdict → run error. Tree FAIL → `add_finding` with the spec's remediation. Rule self-test FAIL → "Fix the rule's pattern" remediation. PASS → scenario counts.
- **12 command files** (reference lines only)
  - ADR links removed with their labels: `create-spec.md`, `implement-phase.md`, `new-command.md` (model-tiers link kept), `new-skill.md` (4), `refresh-command.md`, `release.md`, `retro.md` (ADR-025 row), `ship.md`.
  - Archived spec: `implement-phase.md` § `/goal` Stop hook replaced with the technical spec's two sentences; `revert.md` "Technical spec: …" clause dropped.
  - Research: `refresh-command.md` uses the technical spec's replacement sentence; "Tier 2 is structural only — not an LLM-as-judge." unchanged.
  - `calibrated_against` rewrites: `implement-phase.md` (`spec`), `implement-spec.md` (`story`), `implement-story.md` (`review_cycle`, `testing_cycle`), `refactor.md` (`change`, keeps `no recorded run`). Each cites only shipped paths or globs.
- **`scripts/tests/test_governor_enforcement.py`** (`KNOWN_OVER_BUDGET`)
  - Downward repins to the exact new overage: create-spec 28738 → 28652, implement-phase 10361 → 9921, release 7655 → 7571, ship 4023 → 3947, implement-story 11533 → 11266.

### Implementation Decisions

1. **The helper scans every `commands/*.md`** — install.sh ships every command file after `2026-10-20-harness-cuts`, and that spec's guard forbids `.lean.md` text under `scripts/` (DEV-001).
2. **No command files under `--root` is a run error** — a vacuous PASS on a wrong root would hide a broken checkout (DEV-002).
3. **Governor ledger repinned in this story** — the exact-sum assertion forces it whenever an over-budget command shrinks (DEV-003).

### Test Results

**Verification:** Automated, test-first (12 of 12 new tests red before the helper existed).
**Coverage:** 98% (92 statements, 2 missed) on `scripts/eval-shipped-refs.py`, measured by the orchestrator with `coverage run` and `patch = subprocess` over `test_eval_shipped_refs.py`.

- ✅ Orchestrator targeted run: `test_eval_shipped_refs.py`, `test_governor_enforcement.py`, `test_harness_cuts.py` → 104 passed.
- ✅ Full pytest (3.9): 2728 passed, 2 skipped (baseline 2715 + 13).
- ✅ Bash tests: 45 run, 0 failed.
- ✅ `bash scripts/eval.sh`: Findings 0, run errors 0. `--check=shipped-refs` 5/5, `--check=loop-bounds` 38/38, `--check=refresh-evidence` 22/22.
- ✅ Manual AC-1.3 mutation (coder and reviewer, temp copy): exit 0 clean, exit 1 with `shipped-refs:commands/ship.md:645` after an ADR link, exit 0 restored, exit 2 without the helper.
- ✅ On the base tree the helper flags exactly the 19 lines in 12 files from the technical spec, and none of the lines that stay.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-001, DEV-002, DEV-003)
- **Security:** Clean
- **Boundary Compliance:** 11 command files outside the map are named in technical-spec.md → Files in Scope for Story 1 and touched only on reference lines; justified.
- gate3-route: review-agent (outside_boundary commands/create-spec.md commands/implement-phase.md commands/implement-spec.md commands/implement-story.md commands/new-command.md commands/new-skill.md commands/refactor.md commands/refresh-command.md commands/release.md commands/retro.md commands/revert.md commands/ship.md scripts/eval-shipped-refs.py scripts/eval.sh scripts/tests/test_eval_shipped_refs.py scripts/tests/test_governor_enforcement.py). review-panel: skipped — platform cannot spawn other vendors. arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; build-smoke unverifiable (unsupported_stack). Gate 3 review-override: unverifiable (no coverage report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable by the script (no report); measured 98% by hand. Gate 4 authenticity: pass. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Reviewer residual (Minor): intermediate commit `6434d9c` carries a `.lean.md` skip that `ccfa77c` removes, so that one commit fails the harness-cuts guard; two `check_shipped_refs` branches (helper exit >1 or no tree verdict, rule self-test FAIL) have no eval-level test and were exercised by hand.

### Deviations from Spec

- **[DEV-001] `shipped-refs` scans every `commands/*.md`, including any `*.lean.md`** — Severity: Small
  - Spec said: skip `*.lean.md`.
  - Reality: no name is skipped; install.sh ships every command file and the harness-cuts guard forbids `.lean.md` text under `scripts/`.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md business rule updated.
- **[DEV-002] No `commands/*.md` under `--root` is a run error, not a PASS** — Severity: Small
  - Spec said: empty `commands/` → PASS.
  - Reality: self-tests print, then exit 2 and an eval run error.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md Shadow Paths updated.
- **[DEV-003] Story 1 repins `KNOWN_OVER_BUDGET` for five commands** — Severity: Small
  - Spec said: the ledger file belongs to Story 3.
  - Reality: five downward repins, forced by the exact-sum assertion.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md Files in Scope updated.

---

### Post-Completion Repair (2026-10-21)

- After this story was marked Completed, `scripts/ac-trace.py` reported AC-1.2 to AC-1.5 as `untested_criterion` and full eval had 5 `review-override` findings. ac-trace credits a test token to the spec folder named most recently above it, and the AC-1.1 fixtures named archived spec folders; AC-1.5 had no test.
- `499dbc5`: the class docstrings in `scripts/tests/test_eval_shipped_refs.py` name this spec before each AC tag, and `CalibrationValueTests` covers AC-1.5 (shipped path or `no recorded run`, refactor literal, no record path outside a glob, loop-bounds rows PASS).
- `b129c34`: `.writ/context.md` named the retired lean-file suffix in DEV-001's headline and tripped the harness-cuts guard; the line was reworded.
- A fresh evaluator passed the repair: each AC now cites a test that exercises it, five value mutations fail the AC-1.5 tests, and ac-trace over all 81 spec folders changed only for this spec and the archived `2026-07-18-logical-unit-revert` (3 false findings gone).
