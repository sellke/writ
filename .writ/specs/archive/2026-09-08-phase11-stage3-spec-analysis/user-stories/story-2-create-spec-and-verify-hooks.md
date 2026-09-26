# Story 2: Hooks — create-spec Step 2.6c and verify-spec Advisory Check

> **Status:** Completed ✅
> **Commit:** 125782b72259da9c2ffaa7017c64da217d82da00
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer running `/create-spec` or `/verify-spec`
**I want** `python3 scripts/spec-analyze.py check` invoked after stories exist, with one orchestrator LLM pass and an advisory verify-spec check
**So that** contradiction / gap / ambiguity notes appear without failing the package, replacing `ac-trace`, or adding an API key to the script

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `commands/create-spec.md` after Step 2.6a (`ac-trace`) and Step 2.6b (spec-lite ID tags), when Step 2.6c is added, then it is placed after 2.6b so 2.6b is not renumbered, still runs after 2.6a, instructs the orchestrator to run one LLM pass over the generated stories’ acceptance criteria (contradiction, gap, ambiguity; exit-criteria grammar), writes findings JSON under `.writ/state/` or a temp path or omits `--findings`, and runs `python3 scripts/spec-analyze.py check --spec <folder> [--findings <json>]`. `[AC-2.1]`
- [x] Given Step 2.6c completed, when the script prints `pass`, `fail`, or `unverifiable` (including `fail` `malformed_findings`), then Step 2.9 lists the verdict and `reason:` lines as notes, package creation continues, analysis verdicts use `add_note`, `add_finding` is used only when the helper is missing or exits 2, `unverifiable` is not `DEGRADED`, and there is no AskQuestion gate on analysis notes. `[AC-2.2]`
- [x] Given `commands/verify-spec.md`, when the new advisory check is added, then it is not Check 3e or 3f (`ac-trace` stays there), it invokes the same `python3 scripts/spec-analyze.py check` CLI, relays via notes, and a script `fail` does not fail the verify report. `[AC-2.3]`
- [x] Given the LLM-pass contract lives in the command body, when the orchestrator runs that pass, then input is the spec folder’s story AC text, output is a JSON array matching Story 1’s finding schema or `[]` if the model cannot judge, no new agent file is created, `scripts/spec-analyze.py` has no API key dependency, and `commands/implement-story.md` spawn behavior is unchanged. `[AC-2.4]`
- [x] Given a command-body / eval-wiring test in the `scripts/tests/test_eval_verdict_provenance.sh` / Stage 2b shape, when it runs, then `commands/create-spec.md` and `commands/verify-spec.md` name `scripts/spec-analyze.py`, and a fixture where the script exits `fail` does not treat that as a failed *command* contract (notes only). `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write `scripts/tests/test_spec_analyze_command_hooks.sh` (bash, Stage 2b / `scripts/tests/test_eval_verdict_provenance.sh` pin shape: temp tree, no mutation of the real repo) that greps `commands/create-spec.md` for Step 2.6c plus `python3 scripts/spec-analyze.py check`, greps `commands/verify-spec.md` for the same CLI on a check that is not 3e/3f, and asserts a script `fail` exit is notes-only for the command contract `[AC-2.1, AC-2.3, AC-2.5]`
- [x] 2.2 Add **Step 2.6c** to `commands/create-spec.md` after Step 2.6b (do not renumber 2.6b; `ac-trace` stays at 2.6a): one LLM pass, write JSON under `.writ/state/` or omit `--findings`, run `python3 scripts/spec-analyze.py check --spec <folder> [--findings <json>]`; keep the prompt short (three codes, exit-criteria grammar, Story 1 schema only) `[AC-2.1, AC-2.4]`
- [x] 2.3 Update `commands/create-spec.md` Step 2.9 to surface the Step 2.6c verdict and reasons as notes; package always continues; `add_note` for analysis verdicts; `add_finding` only if the helper is missing or exits 2; no AskQuestion on notes `[AC-2.2]`
- [x] 2.4 Add a new advisory check to `commands/verify-spec.md` (new row, not 3e/3f) that invokes the same CLI and relays via notes; do not fail the verify report on analysis `fail` `[AC-2.3]`
- [x] 2.5 Confirm no new file under `agents/`, no API key in `scripts/spec-analyze.py`, and no spawn-path edit to `commands/implement-story.md` `[AC-2.4]`
- [x] 2.6 Verify acceptance criteria: `bash scripts/tests/test_spec_analyze_command_hooks.sh` green; Step 2.6c sits after 2.6b; 3e/3f still name `ac-trace`; Step 2.9 documents continue-on-fail; closing commit appends `{date} stage-3:` noting Goal Card “Step 2.6” relocated after stories exist `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

**Depends on Story 1.** The CLI, finding schema, and verdict table (`pass` / `fail` / `unverifiable`, exit 0/1/2) must already exist. This story only wires commands.

**Placement.** Goal Card text said “Step 2.6”. The locked contract relocates the invoke to after stories exist. Label `Step 2.6c`, after 2.6b, so 2.6b is not renumbered and 2.6a remains `ac-trace`. Do not invent a Step 2.6 overlap that rewrites story generation.

**Advisory.** Analysis findings never fail `/create-spec` or `/verify-spec`. `unverifiable` is not `DEGRADED`. Malformed LLM JSON is a script `fail` `malformed_findings` and still a command note. One Step 2.6c per run — do not loop. Findings path is per-run under `.writ/state/` (gitignored); do not reuse another spec’s file.

**Out of scope.** No new agent file. No LLM API in the script. Do not change `/implement-story` spawn. Do not replace `ac-trace.py`. Do not promote findings to blocking. Story 3 owns `eval.sh` `CHECKS` registration and precision fixtures — this story’s bash test is command-body / notes-only wiring.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [check --spec, check --findings, LLM pass, Helper missing]
- **Shadow paths:** [create-spec 2.6c, verify-spec check]
- **Business rules:** [Rule 1 (Advisory for one release — analysis findings never fail create-spec or verify-spec), Rule 2 (`unverifiable` is not a failed analysis; not DEGRADED), Rule 3 (Do not replace ac-trace.py — 2.6a and 3e/3f stay), Rule 4 (Hybrid judge — orchestrator owns one LLM pass; script has no API), Rule 8 (ADR-013 — no merge/PR/release), Rule 9 (Decision log `{date} stage-3:`)]
- **Experience:** [Entry point (/create-spec and /verify-spec), Happy path (steps 2–5: LLM pass, check, Step 2.9 notes, package completes), Moment of truth (contradiction note still locks; missing findings → unverifiable not fail), Feedback model (add_note vs add_finding), Error experience (helper crash vs unverifiable vs malformed JSON as note)]

---

## What Was Built

**Implementation Date:** 2026-09-08

### Files Modified

- **`commands/create-spec.md`** — Step 2.6c after 2.6b; Step 2.9 lists analysis notes and never fails the package. Goal Card “Step 2.6” relocated after stories exist.
- **`commands/verify-spec.md`** — advisory **3g** (not in 3a–3f roll-up). 3e/3f still `ac-trace`.
- **`scripts/tests/test_spec_analyze_command_hooks.sh`** — placement + notes-only pins. [AC-2.1, AC-2.3, AC-2.5]
- **`scripts/tests/test_governor_enforcement.py`** — create-spec overage 26891; verify-spec 10666.

### Files Created

None besides the hook test.

### Implementation Decisions

1. **Step 2.6c after 2.6b** so 2.6b is not renumbered and 2.6a stays `ac-trace`.
2. **3g is outside the 3a–3f worst-status cell** so a script `fail` cannot fail verify-spec.

### Test Results

- `bash scripts/tests/test_spec_analyze_command_hooks.sh` green
- No new agent file; `implement-story.md` spawn unchanged

### Review Outcome

**Result:** PASS — 1 iteration. Drift: None.
