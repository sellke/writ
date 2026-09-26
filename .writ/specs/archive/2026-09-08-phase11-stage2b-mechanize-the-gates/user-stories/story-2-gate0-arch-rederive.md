# Story 2: Gate 0 Architecture Re-derivation — arch-check.py Re-derives PROCEED/CAUTION, Never ABORT

> **Status:** Completed ✅
> **Commit:** dda5623edcac6b435be25d005e3f4c4239cc5c17
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who needs Gate 0's PROCEED/CAUTION re-derived from the story graph and planned file set so an architecture agent cannot invent a clean PROCEED on an invalid deps graph or an empty plan
**I want** `scripts/arch-check.py` with `--planned` (pre-implementation, Gate 0's real moment) and `--changed` (replay), calling `story-deps.py` plus an optional boundary map, wired into `implement-story.md` after the architecture-check agent returns PROCEED or CAUTION
**so that** proceed/caution are measurements, ABORT stays LLM-judged, and omitting both mode flags is `unverifiable` rather than an invented empty-tree PROCEED

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `scripts/arch-check.py check --story PATH --repo .` with exactly one of `--planned FILE …` or `--changed FILE …` and optional `--boundary PATH`, when `story-deps.py validate --spec-dir` (called, not copied; spec dir derived from `--story`) exits 0 and the file set is non-empty and ⊆ owned∪readable (or no boundary was supplied), then the script prints `pass` with `rederived: proceed`; when the set is empty, a path is in out-of-scope, or story-deps reports a warning-class result, then `pass` with `rederived: caution`; when story-deps reports an invalid graph, then `fail`; when neither mode flag is passed, then `unverifiable` with `reason: no_file_mode` (not an invented empty-tree proceed); when both mode flags are passed, then exit 2. `[AC-2.1]`
- [x] Given a caller asking `arch-check.py` to classify an ABORT-shaped case, when the script runs, then it prints `unverifiable` with `reason: abort_is_llm_residual` and never prints `abort`; when the caller does not ask for that classification, then the script does not mention ABORT. `[AC-2.2]`
- [x] Given Gate 0 in `commands/implement-story.md` after the architecture-check agent returns PROCEED or CAUTION, when the orchestrator runs `arch-check.py` with `--planned`, then `caution` injects the script `reason` into the coding-agent warnings the way the agent's CAUTION already does, `fail` applies the existing BLOCKED escalation, `proceed` continues, and `unverifiable` continues with the reason verbatim and does not mark the story `DEGRADED`; the ABORT path and the ADR-024 floor→anchor re-run stay untouched. `[AC-2.3]`
- [x] Given this story lands, when `commands/implement-story.md` frontmatter is read, then `gate0_arch` is `script: scripts/arch-check.py` and the other nine `gates:` entries are unchanged; `pipeline-baseline.py` `GATE_NAMES` still includes `gate0_arch` with the same join id; `--prose-only-blocking` is not passed; background-subagent spawning is not changed. `[AC-2.4]`
- [x] Given pytest fixtures for planned-inside-boundary → proceed, planned-empty → caution, out-of-scope path → caution, invalid story-deps → fail, and no mode flag → unverifiable (covering `pass` / `fail` / `unverifiable`), when `uv run --python 3.9 pytest` on the new tests and `bash scripts/eval.sh --check=arch-check` run, then they exit 0 and `eval.sh` registers `arch-check` (findings via `add_finding`, not count-blocking). `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write `scripts/tests/test_arch_check.py` (pytest, Python 3.9) with fixtures matching spec.md Story 2 tests: planned-inside-boundary → proceed, planned-empty → caution, out-of-scope path → caution, invalid story-deps → fail, no mode flag → unverifiable; plus both-flags → exit 2 and ABORT-shaped → `abort_is_llm_residual`; add `scripts/tests/test_eval_arch_check.sh` following `scripts/tests/test_eval_verdict_provenance.sh` `[AC-2.1, AC-2.2, AC-2.5]`
- [x] 2.2 Implement `scripts/arch-check.py` (`check --story PATH --repo . [--planned FILE … | --changed FILE …] [--boundary PATH]`, stdlib, argparse, exit 0/1/2): call `story-deps.py validate --spec-dir` as a helper; `--planned` is Gate 0's pre-implementation set, `--changed` is replay; neither → `unverifiable` (`reason: no_file_mode`); both → exit 2 `[AC-2.1]`
- [x] 2.3 Map helper + file-set + optional boundary to printed verdicts: `proceed`/`caution` as `pass` with `rederived: proceed|caution`; `fail` on an invalid story-deps graph; never print `abort`; ABORT-shaped classification → `unverifiable` (`reason: abort_is_llm_residual`) `[AC-2.1, AC-2.2]`
- [x] 2.4 After the architecture-check agent returns PROCEED or CAUTION, add a Gate 4-shaped “Verify the claim, don't trust it.” block to `#### Gate 0` that runs `arch-check.py` with `--planned`; inject `caution` reasons into coding-agent warnings; `fail` → existing BLOCKED; `unverifiable` → continue; do not rewrite the ABORT path or the ADR-024 floor→anchor re-run; set frontmatter `gate0_arch: script: scripts/arch-check.py` without flipping other gates `[AC-2.3, AC-2.4]`
- [x] 2.5 Register `check_arch_check()` in `scripts/eval.sh` `CHECKS=(...)` as `arch-check` (not count-blocking; do not pass `--prose-only-blocking`); leave `pipeline-baseline.py` `GATE_NAMES` join ids unchanged; do not change how `/implement-story` spawns background subagents `[AC-2.4, AC-2.5]`
- [x] 2.6 Verify all acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_arch_check.py` green, `bash scripts/tests/test_eval_arch_check.sh` green, `bash scripts/eval.sh --check=arch-check` and full `bash scripts/eval.sh` exit 0; append `{date} stage-2b: arch-check.py re-derives Gate 0 proceed/caution (never abort); --planned is the live mode` to the story's completion commit `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **`--planned` is the live Gate 0 input.** Coding has not happened yet; `--changed` exists so Story 5's replay can invoke the same script post-hoc. Inventing proceed from an empty tree when neither flag is set is the defect this story exists to prevent.
- **Call `story-deps.py`, do not copy it.** Derive `--spec-dir` from `--story` (the spec folder that contains `user-stories/`). Graph invalid → `fail` / BLOCKED. Warning-class results the helper already emits → `caution`.
- **Optional `--boundary`.** Story 4 lands `boundary-map.py`; Gate 0 may run with no map. No `--boundary` means “do not apply out-of-scope,” not “treat the tree as empty.”
- **ABORT is residual.** Gate 0's ABORT path and ADR-024 floor→anchor re-run stay as written. The script never re-derives `abort`. How the test suite asks for an ABORT-shaped classification is an implementation detail inside this story; the command body must not invoke the script on ABORT.
- **Printed vocabulary is `GATE_SCRIPT_VERDICTS`.** `proceed`/`caution` are `rederived:` annotations on a printed `pass`. `unverifiable` continues the pipeline and does not mark `DEGRADED`.
- **Out of scope here:** flipping `--prose-only-blocking` (Story 5), rewriting `GATE_NAMES`, fixing background-subagent spawning, new gate numbers, eight-run keep-or-revert, ADR-013 merge/PR/release.
- **Python 3.9 stdlib.** Same shape as `build-smoke.py` / `test-integrity.py` / `verdict-provenance.py`. `install.sh` already copies `scripts/*.py`.
- **Decision log.** Closing commit appends `{date} stage-2b: …` per Business Rule 10.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [spec.md → Experience Design → Error experience (FAIL → existing BLOCKED; `unverifiable` continues, no `DEGRADED`); technical-spec.md §2 verdict table (`proceed`/`caution` printed as `pass`, `fail`, `unverifiable` / `no_file_mode` / `abort_is_llm_residual`, never `abort`)]
- **Shadow paths:** [spec.md → Experience Design → Happy path step 2 (Gate 0 script lands; ABORT still goes to the human)]
- **Business rules:** [Checker wins, `unverifiable` is not a failed gate, No new gate numbers, ABORT and Large-drift stay human, Python 3.9 stdlib, ADR-013 holds, Decision log]
- **Experience:** [Feedback model (agent claim + measurement on the story report), Error experience (FAIL → BLOCKED; `unverifiable` continues), State catalog (scripts landing / all six new scripts exist)]

---

## What Was Built

**Implementation Date:** 2026-09-08

### Files Created

1. **`scripts/arch-check.py`** (309 lines) — `check --story --repo [--planned | --changed] [--boundary] [--classify-abort]`. Calls `story-deps.py validate`. `proceed`/`caution` print as `pass` + `rederived:`. Never prints `abort`; `--classify-abort` → `unverifiable` / `abort_is_llm_residual`. Neither mode → `no_file_mode`. Both → exit 2.
2. **`scripts/tests/test_arch_check.py`** (368 lines) — proceed / empty-caution / out-of-scope-caution / invalid-graph-fail / no-mode / both-flags / abort residual. [AC-2.1–AC-2.5]
3. **`scripts/tests/test_eval_arch_check.sh`** (243 lines)

### Files Modified

- **`commands/implement-story.md`** — `gate0_arch: script: scripts/arch-check.py`; Gate 0 verify block after PROCEED/CAUTION only; ABORT + ADR-024 untouched.
- **`scripts/eval.sh`** — `arch-check` / `check_arch_check()`.

### Implementation Decisions

1. **`--classify-abort` is the test/explicit hook.** The command body never passes it.
2. **No `--boundary` does not treat the tree as empty.**

### Test Results

Story-module pytest + bash eval harness green. Full suite 1135 passed, 1 skipped. `eval.sh` Findings 0. Coverage unverifiable (no coverage tool).

### Review Outcome

**Result:** PASS — 1 iteration. Drift: Medium (DEV-001).
