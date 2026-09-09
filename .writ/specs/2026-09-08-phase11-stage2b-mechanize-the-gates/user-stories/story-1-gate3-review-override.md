# Story 1: Gate 3 Review Override — review-override.py Re-derives PASS/FAIL from ac-trace + test-integrity

> **Status:** Completed ✅
> **Commit:** dda5623edcac6b435be25d005e3f4c4239cc5c17
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who needs Gate 3's honor-system PASS/FAIL re-derived from acceptance-criteria coverage and test integrity so a same-family reviewer cannot rubber-stamp untested ACs
**I want to** land `scripts/review-override.py` that calls `ac-trace.py` and `test-integrity.py` (without reimplementing them), wire a Gate 4-style "Verify the claim, don't trust it" block into `commands/implement-story.md` Gate 3, and declare `gate3_review` as that script
**So that** a mechanical fail blocks an untested or untraced story while architecture, security, and taste stay with `review-agent`, and a mechanical pass never washes out the agent's FAIL or PAUSE

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `scripts/review-override.py check --spec <folder> --repo .` with optional `--story`, `--new-files`, and `--tests`, when the script runs on Python 3.9 stdlib, then it invokes `ac-trace.py check` and (when those path flags are present) `test-integrity.py coverage` / `authenticity` as read-only helpers and does not copy their parsers; it prints `fail` when ac-trace reports a blocking finding on the story (`untested_criterion` after the story would be complete, `untasked_criterion`, `dangling_reference`, `duplicate_id`) or test-integrity reports `coverage_below_threshold` / `coverage_regression` / `test_imports_no_source`; it prints `unverifiable` when either helper is `unverifiable` or `--spec` / `--story` is missing; it prints `pass` otherwise; and it exits 0 / 1 / 2 in the same shape as `build-smoke.py` / `test-integrity.py` `[AC-1.1]`
- [x] Given Gate 3 after the review agent returns, when the new "Verify the claim, don't trust it" block runs `review-override.py` the way Gate 4 runs `test-integrity.py`, then a script `fail` takes the existing review-loop recode path; a script `pass` or `unverifiable` leaves the review-agent FAIL or PAUSE standing (FAIL-only override — a mechanical pass does not force PASS); `unverifiable` continues the pipeline with the reason verbatim and does not mark the story `⚠️ DEGRADED`; residual architecture, security, and taste stay with `review-agent`; spawn behavior is unchanged; and `agents/review-agent.md` is left alone except for an optional one-line pointer `[AC-1.2]`
- [x] Given `commands/implement-story.md` `gates:` frontmatter, when this story lands, then `gate3_review` is `script: scripts/review-override.py`; `eval.sh` `check_verdict_provenance()` still does not pass `--prose-only-blocking` (Story 5 owns that flip); and `verdict-provenance.py` already listing `gate3_review` is not rewritten beyond what the frontmatter change requires `[AC-1.3]`
- [x] Given pytest fixtures for pass, fail-from-ac-trace, fail-from-integrity, unverifiable-helper, and missing spec, when `uv run --python 3.9 pytest scripts/tests/test_review_override.py` runs, then each fixture asserts the matching verdict line and that the script called the helpers rather than re-deriving their findings itself `[AC-1.4]`
- [x] Given `bash scripts/eval.sh`, when `check_review_override` is registered next to `check_verdict_provenance`, then helper findings surface via `add_finding` and the summary via `add_note`, the check is not count-blocking, `scripts/tests/test_eval_review_override.sh` mirrors `scripts/tests/test_eval_verdict_provenance.sh`, and a closing commit appends `{date} stage-2b: {what changed and why}` to `.writ/decision-log.md` `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_review_override.py` (pytest, Python 3.9) with fixtures for pass, fail-from-ac-trace (blocking finding on the story), fail-from-integrity (`coverage_below_threshold` / `coverage_regression` / `test_imports_no_source`), unverifiable-helper, and missing `--spec` / `--story`; assert CLI `check --spec --repo` plus optional `--story` / `--new-files` / `--tests`, exit 0/1/2, and that helpers are invoked rather than reimplemented `[AC-1.1, AC-1.4]`
- [x] 1.2 Write `scripts/tests/test_eval_review_override.sh` mirroring `scripts/tests/test_eval_verdict_provenance.sh` (temp `scripts/` + fixture tree, no mutation of the real repo) for `check_review_override` registration, finding/note relay, and non-count-blocking behavior `[AC-1.5]`
- [x] 1.3 Implement `scripts/review-override.py` (stdlib, Python 3.9, argparse subcommands, `--repo` / `--project` house shape): `check` calls `ac-trace.py check` and, when path flags are present, `test-integrity.py coverage` / `authenticity`; map helper output to `pass` / `fail` / `unverifiable` per technical-spec §1; do not judge architecture, security, or taste `[AC-1.1]`
- [x] 1.4 Add a "Verify the claim, don't trust it" block to `commands/implement-story.md` Gate 3 after the review agent returns, mirroring Gate 4 lines ~280–290: invoke `python3 scripts/review-override.py check …`; script `fail` → existing review-loop recode path; script `pass` / `unverifiable` leave agent FAIL/PAUSE standing; `unverifiable` continues, reason verbatim, no `DEGRADED`; do not change how Gate 3 spawns `review-agent`; do not rewrite `agents/review-agent.md` except an optional one-line pointer `[AC-1.2]`
- [x] 1.5 Set `gates:` `gate3_review` to `script: scripts/review-override.py` in `commands/implement-story.md`; leave `check_verdict_provenance()` without `--prose-only-blocking` `[AC-1.3]`
- [x] 1.6 Register `check_review_override()` in `scripts/eval.sh` next to `check_verdict_provenance()`, add `review-override` to `CHECKS=(...)`, relay findings via `add_finding` and the summary via `add_note` `[AC-1.5]`
- [x] 1.7 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_review_override.py` green, `bash scripts/tests/test_eval_review_override.sh` green, `bash scripts/eval.sh` Findings 0, frontmatter names the script, Gate 3 body contains the verify block with FAIL-only semantics, and the closing commit appends `{date} stage-2b: Story 1 — review-override.py, Gate 3 verify block, gate3_review script source, eval.sh review-override check landed` plus records the FAIL-only asymmetry in What Was Built `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

**Technical considerations.** Call the helpers; do not import their parsers or duplicate finding vocabularies. CLI shape matches `build-smoke.py` / `test-integrity.py` / `verdict-provenance.py`: subcommands, exit 0 (ran, no blocking verdict), 1 (`fail`), 2 (usage). One verdict line, then optional `reason:` lines, then a summary line last (technical-spec shared contract). `test-integrity.py` coverage / authenticity run only when `--new-files` / `--tests` are given; omitting those flags must not invent a fail.

**FAIL-only override.** This is the one deliberate departure from Gate 4's bidirectional override. A mechanical pass must not wash out a review-agent FAIL on architecture or security. Record the asymmetry in What Was Built so Stage 4's fresh-context evaluator does not rediscover it. Fresh-context evaluator itself is out of scope.

**Risks.** Stage 2a baselines already show `test_integrity: unverifiable` on the eight runs; many historical Gate 3 PASSes will re-derive `unverifiable`, not `fail`. That is inherited helper honesty, not a script defect — Story 5's replay table must not treat it as one. `untested_criterion` is blocking only after the story would be complete; do not fail a Not Started story on that code. `install.sh` already copies `scripts/*.py` — no install work.

**Integration.** No story dependencies. Story 5's final `gates:` block must still name this script; setting `script:` here keeps provenance truthful mid-spec. Story 5 flips `--prose-only-blocking` — do not pass that flag from `check_verdict_provenance()` here. Do not change spawn behavior (Business Rule 7). ADR-013: nothing merges, opens a PR, or releases.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [spec.md → ## 🎯 Experience Design → Error experience (script FAIL → existing BLOCKED escalation; `unverifiable` → continue, reason verbatim, no `DEGRADED`)]
- **Shadow paths:** [spec.md → ## 🎯 Experience Design → Happy path, step (1) Gate 3 script lands and overrides a PASS that ac-trace would fail]
- **Business rules:** [Rule 1 (Checker wins — Gate 3 FAIL-only: mechanical fail blocks, mechanical pass leaves agent FAIL/PAUSE), Rule 2 (`unverifiable` is not a failed gate; no `DEGRADED`), Rule 3 (No new gate numbers), Rule 7 (Do not change how `/implement-story` spawns agents), Rule 8 (Python 3.9 stdlib; subcommands; exit 0/1/2; `--repo`), Rule 9 (ADR-013 — no merge/PR/release), Rule 10 (Decision log `{date} stage-2b:`)]
- **Experience:** [Feedback model (verdict line + reason; story report shows agent claim and measurement), Error experience (FAIL vs unverifiable), Happy path step 1, State catalog → Scripts landing]
- **Detailed requirements:** [spec.md → ## Detailed Requirements → ### Story 1 — Gate 3 review override]
- **Technical contract:** [technical-spec.md → ## 1. `scripts/review-override.py` (Story 1) — CLI, verdict table, FAIL-only override, frontmatter]
- **Shared script contract:** [technical-spec.md opening paragraph + ## 8. Tests (pass/fail/unverifiable fixtures; bash eval-wiring like `test_eval_verdict_provenance.sh`; `--prose-only-blocking` not until Story 5)]
- **Scope boundaries:** [spec.md → ## Specification Contract → Scope Boundaries (Excluded: eight-run re-run; fresh-context evaluator / Stage 4)]
- **Implementation approach:** [spec.md → ## Implementation Approach (call helpers, do not copy parsers; Gate 3 FAIL-only recorded in What Was Built)]

---

## What Was Built

**Implementation Date:** 2026-09-08

### Files Created

1. **`scripts/review-override.py`** (233 lines)
   - `check --spec PATH --repo . [--story] [--new-files] [--tests]`. Calls `ac-trace.py` and (when path flags are present) `test-integrity.py` as subprocesses. FAIL-only measurement: `fail` on listed blocking helper codes; `unverifiable` when `--spec`/`--story` is missing or a helper cannot answer; `pass` otherwise. `untested_criterion` is ignored unless the story reads Completed.
2. **`scripts/tests/test_review_override.py`** (375 lines) — pass / fail-from-ac-trace / fail-from-integrity / unverifiable-helper / missing spec; stub helpers record argv. [AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]
3. **`scripts/tests/test_eval_review_override.sh`** (153 lines) — relay + registration; `--prose-only-blocking` still off.

### Files Modified

- **`commands/implement-story.md`** — `gate3_review: script: scripts/review-override.py`; Gate 3 “Verify the claim, don't trust it.” block with FAIL-only semantics (mechanical pass does not force PASS).
- **`scripts/eval.sh`** — `review-override` in `CHECKS`; `check_review_override()` relays findings / notes.
- **`scripts/tests/test_verdict_provenance.py`** — real-command tests accept the mid-spec script count.

### Implementation Decisions

1. **FAIL-only asymmetry (required record).** A script `fail` takes the Gate 3 recode path. A script `pass` or `unverifiable` leaves review-agent FAIL/PAUSE standing. Stage 4's fresh-context evaluator must not rediscover this as a bug.
2. **Helpers are subprocesses.** The override does not import `ac-trace` or `test-integrity` parsers.
3. **Batch-1 shared-file landing.** Stories 1–4 share `implement-story.md` and `eval.sh`. Exclusive scripts were authored in parallel; shared wiring is one checkout (DEV-001).

### Test Results

- `uv run --python 3.9 pytest scripts/tests/test_review_override.py` green
- `bash scripts/tests/test_eval_review_override.sh` green
- Full suite `1135 passed, 1 skipped`; `bash scripts/eval.sh` Findings 0
- `test-integrity.py` coverage → `unverifiable` (`no_coverage_report`). Not DEGRADED.

### Review Outcome

**Result:** PASS — 1 iteration. Drift: Medium (DEV-001 shared-file batch). Residual architecture/security/taste stay with `review-agent`. Spawn unchanged.
