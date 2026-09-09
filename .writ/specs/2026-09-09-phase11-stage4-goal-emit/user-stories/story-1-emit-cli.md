# Story 1: CLI + Schema — goal-emit.py Emit and Check

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who needs a Goal Card to become paste-ready `/goal` files without registering a hook
**I want to** land `scripts/goal-emit.py` with `emit --card PATH [--out DIR]` and `check --card PATH [--out DIR]` that writes `GOAL.md` / `VERIFY.md`, prints the invoke line, and schema-checks an emit dir
**So that** a `loop: yes` card becomes files plus a copy-paste Claude Code `/goal` line, with `pass` / `fail` / `unverifiable` verdicts and no LLM API, no `/goal` hook registration, and no accept / reject / modify-spec on stdout

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given a `loop: yes` Goal Card with header `> **loop:**`, `## OBJECTIVE`, `## DONE WHEN`, and `## STOP-CAPS`, when `python3 scripts/goal-emit.py emit --card PATH [--out DIR]` runs on Python 3.9 stdlib, then it writes `GOAL.md` (title, OBJECTIVE, DONE WHEN, STOP-CAPS, ADR-013 sentence, invoke fenced block equal to the adapter `/goal` template) and `VERIFY.md` (QUALITY if present, how to check DONE WHEN, ADR-013 sentence) under `--out` or the default `.writ/goals/<card-stem>/`; a second emit overwrites those files in place and does not append; `install.sh` is not edited; and the script does not import an LLM library. `[AC-1.1]`
- [x] Given an emit directory already written, when `python3 scripts/goal-emit.py check --card PATH [--out DIR]` runs, then it validates the card plus `GOAL.md` / `VERIFY.md` without rewriting the card; a written file missing the ADR-013 sentence prints `fail` with `reason: missing_boundary` and exits 1. `[AC-1.2]`
- [x] Given `emit` or `check`, when the card is `loop: yes` with required sections and both files carry the ADR sentence, then the only verdict line is `pass` and the process exits 0; when a required section is missing, the verdict is `fail` `malformed_card` (exit 1); when `--card` is missing or unreadable, the verdict is `unverifiable` `missing_card` (exit 0) and no emit dir is created; when the card is `loop: no`, the verdict is `unverifiable` `loop_no` (exit 0) and no emit dir is created; unknown subcommand or bad argv exits 2 on stderr; stdout never prints accept, reject, or modify-spec; and the script never registers a `/goal` hook. `[AC-1.3]`
- [x] Given pytest fixtures for pass (`loop: yes` + required sections), fail `malformed_card`, fail `missing_boundary`, unverifiable `missing_card`, unverifiable `loop_no`, and usage (exit 2), when `uv run --python 3.9 pytest scripts/tests/test_goal_emit.py` runs, then each fixture asserts the matching verdict line, `reason:` lines when present, a summary line last, invoke printed after the summary on a successful emit, and exit 0 / 1 / 2. `[AC-1.4]`
- [x] Given the landed CLI, when stdout and the module graph are inspected, then output matches the Stage 2b/3 helper family (one verdict line, optional `reason:` lines, summary last); `--repo` / `--project` alias to repo root defaulting to `.`; and this story does not edit `commands/create-goal.md`, `commands/implement-phase.md`, `commands/implement-story.md`, `adapters/claude-code.md`, or `scripts/eval.sh`. `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `scripts/tests/test_goal_emit.py` (pytest, Python 3.9) with fixtures for pass (`loop: yes` emit + check), fail `malformed_card`, fail `missing_boundary` (check of mutated files), unverifiable `missing_card`, unverifiable `loop_no` (no dir), and usage exit 2; assert `emit` / `check --card PATH [--out DIR]`, default `--out` stem, overwrite-not-append, ADR sentence in both files, invoke after summary, exit 0/1/2, and that accept / reject / modify-spec never appear `[AC-1.3, AC-1.4]`
- [x] 1.2 Implement `scripts/goal-emit.py` (stdlib, Python 3.9, argparse subcommands, `--repo` / `--project` house shape): `emit --card PATH [--out DIR]` and `check --card PATH [--out DIR]`; do not call an LLM API; unknown subcommand / bad argv → exit 2 `[AC-1.5]`
- [x] 1.3 Implement `emit`: parse required card fields; write `GOAL.md` / `VERIFY.md` per technical-spec §1; default `--out` to `.writ/goals/<card-stem>/`; overwrite idempotently; copy the adapter `/goal` template into the invoke block and print that line after the summary `[AC-1.1]`
- [x] 1.4 Implement `check`: schema-validate card + written files without rewriting the card; absent ADR sentence → `missing_boundary` `[AC-1.2]`
- [x] 1.5 Map the verdict table: `pass` exit 0; `fail` `malformed_card` / `missing_boundary` exit 1; `unverifiable` `missing_card` / `loop_no` exit 0 with no emit dir; one verdict line, optional `reason:` lines, summary last; never print accept / reject / modify-spec; never register a `/goal` hook `[AC-1.3]`
- [x] 1.6 Leave `commands/create-goal.md`, `commands/implement-phase.md`, `commands/implement-story.md`, `adapters/claude-code.md`, `scripts/eval.sh`, and `scripts/install.sh` unchanged in this story `[AC-1.5]`
- [x] 1.7 Verify acceptance criteria: `uv run --python 3.9 pytest scripts/tests/test_goal_emit.py` green; confirm emit/check surfaces, verdict vocabulary, no LLM import, no hook registration, and no edits to Story 2/3 files `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

**Technical considerations.** Mirror `scripts/spec-analyze.py` for argparse, one verdict line, `reason:` lines, summary last, and `--repo` / `--project`. Pin the invoke text as a copy of `adapters/claude-code.md` § The /goal Stop Hook (literal in the script or read from the adapter file). ADR-013 may backtick `--recommend`; other words and punctuation must match. `check` is read-only on the card.

**Risks.** Story 3 owns gold fixtures under `scripts/tests/fixtures/goal-emit/` and `eval.sh`. This story’s pytest fixtures may be temporary dirs; do not land eval gold or rewrite the three-way disjunction. `loop: no` must not create an empty `--out` dir.

**Integration.** No story dependencies. Story 2 owns `/create-goal` and `/implement-phase` hooks. Story 3 owns adapter paste wording, `eval.sh` `goal-emit`, and committed gold. Do not edit `implement-story.md`. ADR-013: nothing merges, opens a PR, or releases.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [emit --card, emit on loop: no, Parse card, check written files]
- **Shadow paths:** [Happy, Nil, Empty]
- **Business rules:** [Emit is not register, `loop: no` does not emit, ADR-013 verbatim, Invoke is copy-paste, Overwrite is idempotent, Default `--out`]
- **Experience:** [Happy path (files + printed line), Moment of truth (invoke + ADR-013), Error experience (`missing_card` / `loop_no` / `malformed_card` / `missing_boundary`), Feedback model (verdict / `reason:` / summary)]

---

## What Was Built

**Implementation Date:** 2026-09-09

### Files Created

1. **`scripts/goal-emit.py`** (266 lines)
   - `emit --card PATH [--out DIR]` writes `GOAL.md` / `VERIFY.md` (ADR-013 in both; invoke fence in GOAL) and prints the pinned adapter `/goal` template after the summary. `check` is read-only on the card. [AC-1.1, AC-1.2, AC-1.3]
2. **`scripts/tests/test_goal_emit.py`** (755 lines)
   - 41 tests: usage exit 2, `missing_card` / `loop_no` / `malformed_card` / `missing_boundary`, pass emit+check, default `--out` stem, overwrite-not-append, `--repo`/`--project`, no LLM import, no accept/reject/modify-spec, plus in-process coverage for `spec_ref` and empty sections. [AC-1.4, AC-1.5]

### Files Modified

- **`.writ/specs/2026-09-09-phase11-stage4-goal-emit/spec-lite.md`** — Small-drift auto-amend: `spec_ref` → `exit-criteria.py` rule; missing written files on `check` → `missing_boundary`.
- **`.writ/specs/2026-09-09-phase11-stage4-goal-emit/drift-log.md`** — created with DEV-001..003.

`commands/create-goal.md`, `commands/implement-phase.md`, `commands/implement-story.md`, `adapters/claude-code.md`, `scripts/eval.sh`, and `scripts/install.sh` left unchanged.

### Implementation Decisions

1. **`--card` is optional** so a missing or unreadable path is `unverifiable` `missing_card` (exit 0), not argparse exit 2.
2. **Invoke is a pinned literal** copied from `adapters/claude-code.md` § The /goal Stop Hook (768 bytes, equal). Printed only after the summary on successful `emit`.
3. **Default `--out` is `--repo/.writ/goals/<card-stem>/`.** Tests always use a temp `--repo` or `--out`.
4. **`spec_ref` token cleanup keeps a leading `.`** so `.writ/.../spec.md` resolves; only a trailing period is stripped.

### Test Results

**Verification:** Automated
- ✅ `uv run --python 3.9 pytest scripts/tests/test_goal_emit.py` — 41 passed
- ✅ Regression `scripts/tests/test_spec_analyze.py` — 14 passed
- ✅ `test-integrity.py coverage` — 99.4% (165/166) on `scripts/goal-emit.py` vs 80% threshold
- ⚠️ `test-integrity.py authenticity` — `fail` / `test_imports_no_source` (known checker gap: Python importlib-by-path / subprocess CLI tests; third occurrence appended to `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`)
- Mechanical: arch-check `pass` (rederived proceed; agent CAUTION injected); review-override `unverifiable` (`no_coverage_report` at Gate 3); drift-format `pass`; docs-check `unverifiable` (`no_public_exports`); build-smoke `unverifiable` (`unsupported_stack`)

**Coverage:** 99.4% line coverage on `scripts/goal-emit.py`

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** Story 1 stayed inside the two owned files and did not land gold fixtures or hook/eval edits.

### Deviations from Spec

- **[DEV-001] VERIFY.md names exit-criteria.py when spec_ref exists** — Severity: Small
  - Spec said: name `exit-criteria.py` when a promoted spec exists; otherwise count DONE WHEN lines
  - Reality: detects existing `spec.md` from card `spec_ref` under `--repo`
  - Resolution: Auto-amended
  - Spec amendment: spec-lite Implementation Approach states the rule
- **[DEV-002] check maps missing emit files to missing_boundary** — Severity: Small
  - Spec said: written files lacking ADR → `missing_boundary`
  - Reality: absent `GOAL.md` / `VERIFY.md` on `check` of a valid `loop: yes` card uses the same code
  - Resolution: Auto-amended
  - Spec amendment: spec-lite Error Handling lists the case
- **[DEV-003] Banned-token matcher uses word boundaries** — Severity: Small
  - Spec said: stdout never prints accept / reject / modify-spec
  - Reality: word-boundary match so invoke text `acceptable` does not false-fail `accept`
  - Resolution: Auto-amended
  - Spec amendment: N/A — test assertion detail

### Next Story

**Story 2:** Hooks — `/create-goal` after save and `/implement-phase` origin emit.
