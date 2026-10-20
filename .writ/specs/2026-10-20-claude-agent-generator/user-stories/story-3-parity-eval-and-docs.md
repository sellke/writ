# Story 3: Parity Check, Eval Check, and Docs

> **Status:** Completed ✅ (2026-10-20)
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** Writ maintainer
**I want to** have `check-agent-parity.sh` and `eval.sh` fail on drift between canonical agents and generated Claude agents, and have the Claude adapter and refresh-command docs cover the agent path mapping and `writ-visual-qa`
**So that** a stale, hand-edited, missing, orphan, or unmapped `writ-*.md` fails the same gates that already catch missing files, and a Claude install resolves `> **Agent:** agents/<stem>.md` references to the right `writ-*.md` file

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given `check-agent-parity.sh` maps `visual-qa-agent` to `writ-visual-qa.md` and the visual-qa exemption is removed, when the parity fixture runs with `writ-visual-qa.md` absent, then the presence check reports it as missing the same way it reports any other counterpart, and `scripts/tests/test_shell_check_shape.sh` contains no visual-qa exemption case `[AC-3.1]`
- [x] Given both generators sit beside `check-agent-parity.sh` and one canonical line was edited without regeneration, when the script runs, then it runs `gen-claude-agents.py --check` and `gen-codex-agent-tomls.py --check`, prints `fail` on line 1, folds each `reason: <kind> <stem>` line into a drift reason `<gen>: <kind> <stem>`, prints the summary last, and exits 1 `[AC-3.2]`
- [x] Given a generator exits with rc 2 or higher, when the parity script runs, then it records the drift reason `<gen> --check exited <rc>` and exits 1; given a generator file is absent, when the script runs, then the presence check still runs, the summary appends `; content not checked: <gens>`, and the verdict depends only on presence reasons `[AC-3.3]`
- [x] Given a Claude agent file is stale, missing, orphan, or unmapped, when `bash scripts/eval.sh` runs, then `check_claude_agents` adds one finding per `reason:` line, each with a kind-specific remedy that names `python3 scripts/gen-claude-agents.py`; given the generator is missing, the finding says so and gives the restore remedy; the check is registered next to the codex check `[AC-3.4]`
- [x] Given `adapters/claude-code.md` and `commands/refresh-command.md`, when a maintainer reads them, then the adapter maps `agents/<stem>.md` to `.claude/agents/writ-<x>.md` for all eight stems, its agent tables list `writ-evaluator` and `writ-visual-qa`, and the refresh-command parity section drops the visual-qa exclusion and names `python3 scripts/gen-claude-agents.py` as the regenerate command `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Update the parity fixture in `scripts/tests/test_shell_check_shape.sh`: drop the visual-qa exemption case and add a content-drift case that copies `gen-claude-agents.py` into the temp tree, stales one file, and expects `fail` with a `gen-claude-agents.py: stale <stem>` reason. Run it and confirm the new case fails before the script change `[AC-3.1, AC-3.2]`
- [x] 3.2 Update `scripts/check-agent-parity.sh`: remove the visual-qa exemption, add `visual-qa-agent → writ-visual-qa.md` to the counterpart map, run both generators' `--check` after the presence loop, fold `reason:` lines into drift reasons, record rc ≥ 2 as `<gen> --check exited <rc>`, and append the content-not-checked note to the summary when a generator is absent `[AC-3.1, AC-3.2, AC-3.3]`
- [x] 3.3 Add `check_claude_agents` to `scripts/eval.sh`, structured like `check_codex_tomls`: one `add_finding` per `reason:` line with a kind-specific remedy (`stale` and `missing` regenerate, `orphan` removes the file or adds an overlay, `unmapped` adds an overlay entry, then regenerate), plus a missing-generator finding with the restore remedy. Register it next to the codex check `[AC-3.4]`
- [x] 3.4 Update `adapters/claude-code.md`: add the agent-path mapping for the eight stems (`agents/<stem>.md` → `.claude/agents/writ-<x>.md`), and add `writ-evaluator` and `writ-visual-qa` to the agent tables. Keep the agent-path row in this file only `[AC-3.5]`
- [x] 3.5 Update the parity section of `commands/refresh-command.md`: remove the visual-qa exclusion and document `python3 scripts/gen-claude-agents.py` as the regenerate command `[AC-3.5]`
- [x] 3.6 Run every script in `scripts/tests/test_*.sh` and the new `check_claude_agents` check. Confirm that verdict line 1, reason lines, and summary last are unchanged, and that exit codes are 0, 1, and 2 as specified `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
- [x] 3.7 Verify on the committed tree: `bash scripts/eval.sh` and `bash scripts/check-agent-parity.sh` pass. In a temp copy, edit one canonical line, confirm `eval.sh` reports `stale coding-agent` with the `python3 scripts/gen-claude-agents.py` remedy, and confirm the parity script's summary notes the skipped content check when a generator is removed from the copy `[AC-3.2, AC-3.4]`

## Notes

- **Dependencies:** The generator (Story 1) must exist. The committed tree passes only after Story 2 regenerates `claude-code/agents/` and adds `writ-visual-qa.md`.
- **Verdict contract:** `check-agent-parity.sh` stays a warning for `/refresh-command --check-parity`. Its verdict depends only on reasons, and its exit codes 0, 1, and 2 do not change. Content drift adds reasons; it does not add a new exit path.
- **Shape consistency:** The generator's `--check` output matches `gen-codex-agent-tomls.py`, so folding its reasons needs no special cases.
- **Cross-spec overlap:** The planned `2026-10-20-claude-code-parity` spec also edits `adapters/claude-code.md`. The agent-path row lives in one place. Coordinate with that spec or sequence the two.
- **Risk: silent pass.** A generator that crashes (rc ≥ 2) must not produce `pass`. Task 3.2 and AC-3.3 cover this.
- **Fixture resolution.** `gen-codex-agent-tomls.py` sets `ROOT = pathlib.Path(__file__).resolve().parents[1]`. If `gen-claude-agents.py` does the same, a copy at `<tmp>/scripts/` checks `<tmp>/agents/` and `<tmp>/claude-code/agents/`, so the fixture must copy the script into `<tmp>/scripts/`, not elsewhere.
- **Summary wording.** The pass summary in `check-agent-parity.sh` ends with "subject to documented exclusions". Drop that phrase when the visual-qa exemption goes, since no exclusion remains.
- **Scope:** No change to generated content, overlay values, or command spawn behavior. Excluded: Cursor-shaped `Task(...)` rewrites and plugin distribution (Phase 14).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** Parity script / generator absent → skip content check, summary notes the skip, verdict from presence only. Parity script / generator crashes (rc ≥ 2) → record as drift `reason: <gen> --check exited <rc>`. `eval.sh` / generator missing → finding "Claude agent generator is missing" with restore remedy. From technical-spec.md → Error & Rescue Map.
- **Shadow paths:** Nil: `agents/` absent → `check-agent-parity.sh` prints `unverifiable` before reaching content checks. From technical-spec.md → Shadow Paths.
- **Business rules:** Rule 4 (stem → filename map, including `visual-qa-agent → writ-visual-qa`) for the adapter mapping. Rule 6 (parity check never blocks callers; stays a warning; exit codes unchanged). From spec.md → ## Business Rules.
- **Experience:** Canonical edited, not regenerated → `fail`, `reason: stale coding-agent`, eval finding names `python3 scripts/gen-claude-agents.py`. Generator absent beside the parity script → summary says content was not checked; verdict unaffected. Check-shape output: verdict on line 1, one `reason:` line per problem, summary last. From spec.md → Experience Design and State catalog.

---

## What Was Built

**Implementation Date:** 2026-10-20

### Files Created

1. **`scripts/tests/test_eval_claude_agents.sh`** (114 lines)
   - 7 assertions for `check_claude_agents`: fresh pass, stale, stale plus missing, unmapped plus orphan, missing generator, generator exit 2, registration order. Not named in the story tasks; permitted by the orchestrator.

### Files Modified

- **`scripts/check-agent-parity.sh`** (presence loop, content check, summary)
  - Visual-qa exemption removed and `visual-qa-agent → writ-visual-qa.md` mapped. Runs both generators' `--check` and folds each reason as `reason: <gen>: <kind> <x>`; rc ≥ 2 and rc 1 without a reason line are drift; an absent generator adds `; content not checked: <gens>` to the summary. Shape and exit codes unchanged.
- **`scripts/eval.sh`** (`check_claude_agents`, `CHECKS`)
  - New `claude-agents` check after `codex-tomls`; one finding per reason with a kind-specific remedy naming `python3 scripts/gen-claude-agents.py`.
- **`scripts/tests/test_shell_check_shape.sh`** (parity fixture)
  - Exemption case removed; cases for missing `writ-visual-qa.md`, content-not-checked, aligned, stale `coding-agent`, generator exit 2, one generator absent.
- **`adapters/claude-code.md`** (Agent Paths, agent tables)
  - New Agent Paths table for all eight stems; `writ-evaluator` and `writ-visual-qa` in the tree, tier, permission, and memory listings; generated/do-not-hand-edit note.
- **`commands/refresh-command.md`** (Phase 6 parity)
  - Exclusions removed; both regenerate commands and the content-drift reason formats documented.

### Implementation Decisions

1. **eval findings keyed on the canonical file for stale/missing** — avoids a third copy of the stem map (DEV-005).
2. **Orchestrator fix after review** — orphan remedy now says to restore the canonical source and OVERLAY entry; adding an OVERLAY entry alone leaves the file an orphan under DEV-001.

### Test Results

**Verification:** `test_shell_check_shape.sh` 29 assertions passed; `test_eval_claude_agents.sh` 7 passed; `check-agent-parity.sh` pass on the committed tree. Reviewer re-ran: all bash suites, `uv run pytest` 2672 passed / 2 skipped, contract tests 318 passed, `eval.sh` rc 0.
- ✅ Manual drift in a temp worktree: parity `fail` with `reason: gen-claude-agents.py: stale coding-agent`; eval finding names the regenerate command
- ⚠️ `test-integrity.py authenticity` → `test_imports_no_source` on both bash tests. Known checker false positive for shell tests (same verdict on the existing `test_eval_codex_tomls.sh`). Carried on mutation evidence: disabling the reason fold, the crash branch, or the eval remedy text each makes its test fail.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** One permitted crossing (`scripts/tests/test_eval_claude_agents.sh`)

### Deviations from Spec

- **[DEV-004] Fail summary splits presence and content counts** — Severity: Small
  - Spec said: shape and exit codes unchanged; old summary counted only missing counterparts
  - Reality: `fail (<m> missing counterpart(s), <c> content drift reason(s) across <a> agents[; content not checked: ...])`
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md "For Review Agents" criterion 5
- **[DEV-005] eval stale and missing findings point at the canonical file** — Severity: Small
  - Spec said: structured like `check_codex_tomls`
  - Reality: stale/missing on `agents/<stem>.md`; orphan on `claude-code/agents/writ-<x>.md`
  - Resolution: Auto-amended (no change needed)
- **[DEV-006] Generator exits 1 with no `reason:` line** — Severity: Small
  - Spec said: rc 1 folds reasons; rc ≥ 2 is drift
  - Reality: rc 1 with no reason line is also drift
  - Resolution: Auto-amended (no change needed)
