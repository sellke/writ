# Lean Implement Phase (Lite)

> Source: .writ/specs/2026-11-06-lean-implement-phase/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `/implement-phase` generates UAT plans only with `--uat` or a later `/create-uat-plan`, and `commands/implement-phase.md` drops to at most 240 lines with no behavior change beyond that.

**Implementation Approach:**
- Story 1: `phase-state.py init --uat` → `uatRequested`; c2 skips plan checks only on an explicit `false` (a missing key or any other value checks plans); resume uses phase state and story statuses, not `uat-plan.md`.
- Story 2: `health` marks omitted sources `not_requested`; `--drift` repeats (any material log → `material`, else any missing → `missing`); Step 4.1c passes only produced sources; Step 1.4 Goal emit removed.
- Story 3: lanes write `phase-spec-result-v1` to `<repo>/.writ/state/lane-result-<phase>-<spec>.json`; brief template `commands/_lane-brief.md`; `gen-platform-trees.py` treats every underscore file in `commands/` as a partial (shipped, linked from the plugin root, never a plugin command); `validate-result` returns `result_missing` / `invalid_result` for a missing or non-object file. The supervisor gets the result file's contents (verbatim), not its path; the adapters' lane-result wording describes the result file.
- Story 4: cut prose to ≤ 240 lines; rationale moves to `phase-execution-state-format.md`; every `eval.sh` literal stays.
- Scripts are Python 3.9 stdlib. Refresh generated trees with `python3 scripts/gen-platform-trees.py`.

**Files in Scope:**
- `commands/implement-phase.md`: all four stories
- `scripts/phase-state.py`, `scripts/exit-criteria.py` + tests: `--uat`, c2, `health`, `resultPath`
- `commands/implement-spec.md` § Phase-Orchestrated Lane Mode; `commands/_lane-brief.md` (new)
- `commands/status.md`, `README.md`, `SKILL.md`, `.writ/docs/{exit-criteria-classification,phase-execution-state-format,agent-cli-contract}.md`
- `scripts/eval.sh` c2 literal; `scripts/tests/test_goal_emit_command_hooks.sh`; `test_governor_enforcement.py` ledger

**Error Handling:**
- State file without `uatRequested` → treated as requested
- Lane result file missing → resume the lane once, then `transient`
- A pinned literal cut in Story 4 → `eval.sh` fails; restore it

**Integration Points:**
- `/create-uat-plan` unchanged; `check-uat` unchanged
- `/status` calls `health` with its own sources

**Line Budget Constraints:** `implement-phase.md` ≤ 240 lines after Story 4; disclose byte changes in `KNOWN_OVER_BUDGET`.

---

## For Review Agents

**Acceptance Criteria:**
1. A phase without `--uat` runs no `/create-uat-plan` and c2 returns `met` with `UAT not requested` `[AC-1.1, AC-1.2]`
2. With `--uat`, a missing or stub plan leaves c2 `unmet`; a state file with no `uatRequested` behaves as requested `[AC-1.2, AC-1.3]`
3. Resume skips by phase state and story status, never by `uat-plan.md` alone `[AC-1.4]`
4. `health` with only produced, clean sources returns `Healthy`; a passed path that is missing is a Warning `[AC-2.1, AC-2.2]`
5. Step 1.4 is gone and the goal-emit tests assert only `/create-goal` `[AC-2.3, AC-2.4]`
6. The lane writes its result file and `validate-result` reads it; a missing file gets one resume, then `transient` `[AC-3.1, AC-3.2, AC-3.3]`
7. `implement-phase.md` ≤ 240 lines; every `eval.sh` literal and phase test passes unchanged `[AC-4.1, AC-4.2, AC-4.3]`

**Business Rules:**
- Rules 1–8 in `spec.md` → Specification Contract; expanded in `spec.md` → Business Rules (Expanded)
- Unchanged: verified-only merge, checker governs, no self-certified human criteria, lane supervisor, quarantine and closure (Rule 8)

**Experience Design:**
- Entry: `/implement-phase N` or `/implement-phase N --uat`
- Happy path: lanes merge; report lists human criteria with one `/create-uat-plan {spec}` line per merged spec
- Moment of truth: `UAT: not requested` and checker `met`
- Feedback: report lines plus `uatRequested` in state
- Error: under `--uat`, c2 `unmet` names the spec

---

## For Testing Agents

**Success Criteria:**
1. Both pytest runs (3.9, 3.14), bash tests, and `eval.sh` pass at spec end
2. Fixture: no `--uat` → c2 `met`; `--uat` without plan → c2 `unmet`
3. `wc -l commands/implement-phase.md` ≤ 240

**Shadow Paths to Verify:**
- **Happy path:** no `--uat`, all merged → c2 `met`
- **Nil input:** state without `uatRequested` → c2 checks plans
- **Empty input:** no merged specs → c2 `met`
- **Upstream error:** `/create-uat-plan` fails under `--uat` → c2 `unmet`

**Edge Cases:**
- `--resume --uat` on a run started without it → `uatRequested` flips to true; plans generated for integrated specs
- `health` with no flags → `Healthy` when state reconciles

**Test Strategy:**
- Unit tests in `test_exit_criteria.py`, `test_phase_state.py`; existing eval literals guard Story 4
- Targeted tests per story; full suites once at spec end
