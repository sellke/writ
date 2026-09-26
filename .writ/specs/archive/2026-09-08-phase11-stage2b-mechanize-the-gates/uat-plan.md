# UAT Plan: Phase 11 Stage 2b: Mechanize the Gates

> **Generated:** 2026-09-25
> **Spec:** `.writ/specs/2026-09-08-phase11-stage2b-mechanize-the-gates/`
> **Stories Covered:** 5 of 5 completed
> **Total Scenarios:** 37
> **Updated:** 2026-09-25 after defect fixes

## How to Use This Plan

1. Work through scenarios in order (grouped by story, ordered by priority).
2. Run every command from the repository root. Scenarios marked "scratch" build throwaway files under a temp directory; they never touch tracked files.
3. Mark Pass or Fail. Add notes for any output that differs from the Expected Result.
4. File a Fail as an issue or feed it back to the spec. Do not fix it inline.
5. The feature passes UAT when every scenario passes, or when a failure is accepted as a known limitation.

> **Note on this methodology repo:** the deliverables are six Python scripts, wiring in `commands/implement-story.md`, seven `eval.sh` checks, a watch field in `scripts/pipeline-baseline.py`, and fixtures. There is no UI. Most scenarios run a script and compare its printed lines.
>
> **Scratch setup used by several scenarios.** Run once before starting:
> ```
> export UAT=$(mktemp -d)
> export SPEC=.writ/specs/2026-09-08-phase11-stage2b-mechanize-the-gates
> ```
> Every scratch file lives under `$UAT`. Delete it with `rm -rf "$UAT"` when done.
>
> **`eval.sh` scenarios** create temp git repos. Run them outside any sandbox. Each run writes one report under `.writ/state/` (gitignored).

## What This Spec Delivered

Six scripts re-derive a verdict for six `/implement-story` gates: `review-override.py` (Gate 3), `arch-check.py` (Gate 0), `docs-check.py` (Gate 5), `boundary-map.py` (Gate 0.5), `change-surface.py` (Gate 2.5), and `drift-format.py` (Gate 3.5). Together with the existing `build-smoke.py` (Gate 2) and `test-integrity.py` (Gate 4), eight of ten gates name a script in the `gates:` frontmatter. Gate 1 and Gate 4.5 stay `prose-only`, and `eval.sh` now runs `verdict-provenance.py` with `--prose-only-blocking`, so a third honor-system gate is a finding. `pipeline-baseline.py` gained a `background_tasks_outstanding` field. `scripts/tests/test_gate_replay.py` replays Gate 2.5 on each of the 16 committed baseline records and marks the other five new gates `not_replayable`, because the records do not carry their inputs.

This spec is marked **Superseded by** `2026-09-09-phase11-stage4b-pipeline-demote`. That later spec changed the default path: Gate 0 and Gate 5 now run the script only, and Gate 3's default agent is `evaluator-agent`. Scenarios below check the current `commands/implement-story.md`, not the 2026-09-08 text.

## Honest Notes (read before signing off)

1. **The replay compares no agent verdicts.** `test_gate_replay.py` replays only Gate 2.5 (`change-surface.py` on the record's test files). The records come from another repository and carry no story file, spec, drift log, review output, or changed source, so the other five gates are `not_replayable` with a reason. Totals: `replayed=16 not_replayable=80 compared=0`. The earlier totals (54 agree / 42 note / 48 unverifiable) came from constant inputs and are marked corrected in the decision log and Story 5. AC-5.5 asks for an agent-verdict vs re-derived table; the table exists but holds no comparison. This is a limit of the committed data, not of the scripts. Scenario 35 tests this.
2. **`boundary-map.py` keeps names it cannot resolve.** `path::symbol` is cut to the path, and a bare filename resolves when exactly one tracked file has that name. A bare filename with no match or several matches is kept as named (`objective.md` in `2026-09-05-phase11-repair-and-baseline` Story 1), since it may be a file the story creates. Scenario 26 records this.
3. **Some live `eval.sh` checks use fixed inputs.** `review-override` and `arch-check` now run once per active story, and `docs-check` runs on every shipped Python/JS/TS file. `drift-format` still checks this spec's Story 5 with no drift log (always `unverifiable`), `change-surface` classifies `commands/implement-story.md` (always `cross-component`), and `boundary-map` maps the first active story. On this repo `docs-check` prints `unverifiable` because no shipped file declares `__all__` or a JS/TS `export`; it fails only if one appears undocumented. By design: these are wiring checks, and the decision log records Writ-the-product as `unverifiable` for Gate 5.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Gate 3 Review Override | ✅ Covered | 8 | AC: 6, Errors: 0, Shadow: 1, Edge: 0, Experience: 1 |
| Story 2: Gate 0 Architecture Re-derivation | ✅ Covered | 7 | AC: 6, Errors: 1, Shadow: 0, Edge: 0 |
| Story 3: Gate 5 Docs Check | ✅ Covered | 5 | AC: 5, Errors: 0, Shadow: 0, Edge: 0 (Scenario 18 also covers the "Gate 5 on this repo" edge case) |
| Story 4: Boundary and Surface Classifiers | ✅ Covered | 6 | AC: 5, Errors: 0, Shadow: 0, Edge: 0, Experience: 1 |
| Story 5: Drift Format, Flip, and Watch | ✅ Covered | 11 | AC: 6, Errors: 0, Shadow: 0, Edge: 3, Experience: 2 |

`sub-specs/technical-spec.md` has no Error & Rescue Map, Shadow Paths, or Interaction Edge Cases tables. Shadow paths and edge cases come from `spec-lite.md` ("Shadow Paths to Verify", "Edge Cases"). Error scenarios come from `spec.md` Experience Design ("Error experience") and the verdict tables in `technical-spec.md`. Shadow path "nil input" is Scenario 2, "empty input" is Scenario 9, "upstream error" is Scenario 7, and "mechanical fail overrides agent PASS" is Scenario 1.

---

## Story 1: Gate 3 Review Override

### Scenario 1: ac-trace findings drive the verdict; `untested_criterion` blocks only on a completed story

**Source:** Acceptance Criteria (AC-1.1) — Story 1

**Preconditions:**
- `$UAT` and `$SPEC` set (scratch setup).

**Steps:**
1. Build a scratch spec whose only criterion has no citing task:
   ```
   mkdir -p "$UAT/rv/.writ/specs/demo/user-stories"
   cat > "$UAT/rv/.writ/specs/demo/user-stories/story-3-fixture.md" <<'EOF'
   # Story 3: Fixture

   > **Status:** In Progress
   > **Priority:** High
   > **Dependencies:** None

   ## Acceptance Criteria

   > **AC IDs assigned through:** AC-3.1

   - [ ] Given a criterion no task cites, when checked, then `x` exists. `[AC-3.1]`

   ## Implementation Tasks

   - [ ] 3.1 Unrelated task with no citation.
   EOF
   R="$UAT/rv/.writ/specs/demo"; ST="$R/user-stories/story-3-fixture.md"
   python3 scripts/review-override.py check --spec "$R" --repo "$UAT/rv" --story "$ST"; echo "exit=$?"
   ```
2. Make the task cite the criterion and run again:
   ```
   sed -i '' 's/^- \[ \] 3.1 Unrelated task with no citation./- [ ] 3.1 Build it `[AC-3.1]`/' "$ST"
   python3 scripts/review-override.py check --spec "$R" --repo "$UAT/rv" --story "$ST"; echo "exit=$?"
   ```
   (On Linux use `sed -i` without `''`.)
3. Mark the story complete without checking the criterion or adding a test:
   ```
   sed -i '' 's/In Progress/Completed ✅/' "$ST"
   python3 scripts/review-override.py check --spec "$R" --repo "$UAT/rv" --story "$ST"; echo "exit=$?"
   ```
4. Run against a real completed story of this spec:
   `python3 scripts/review-override.py check --spec $SPEC --repo . --story $SPEC/user-stories/story-1-gate3-review-override.md; echo "exit=$?"`

**Expected Result:**
- Step 1: `fail`, `reason: untasked_criterion`, `review-override: fail (ac-trace blocking finding on story 3)`; `exit=1`.
- Step 2: `pass`, `review-override: pass (no blocking helper finding)`; `exit=0`. An untested criterion on an In Progress story does not fail.
- Step 3: `fail`, `reason: untested_criterion`, same summary as step 1; `exit=1`.
- Step 4: `pass`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/review-override.py` (calls `ac-trace.py` and `test-integrity.py` as subprocesses); commit `dda5623`

**Notes:**

---

### Scenario 2: Missing `--spec` or `--story` is `unverifiable`; a bad subcommand is exit 2

**Source:** Acceptance Criteria (AC-1.1) and Shadow Path (nil input: missing spec/story → unverifiable) — Story 1

**Preconditions:**
- `$SPEC` set.

**Steps:**
1. `python3 scripts/review-override.py check --repo .; echo "exit=$?"`
2. `python3 scripts/review-override.py check --spec $SPEC --repo .; echo "exit=$?"`
3. `python3 scripts/review-override.py check --spec /nonexistent --repo . --story x.md; echo "exit=$?"`
4. `python3 scripts/review-override.py frob; echo "exit=$?"`

**Expected Result:**
- Step 1: `unverifiable`, `reason: missing_spec`, `review-override: unverifiable (missing --spec)`; `exit=0`.
- Step 2: `unverifiable`, `reason: missing_story`, `review-override: unverifiable (missing --story)`; `exit=0`.
- Step 3: `unverifiable`, `reason: unparseable_story`, `review-override: unverifiable (story filename has no number)`; `exit=0`.
- Step 4: usage error on stderr naming `invalid choice: 'frob'`; `exit=2`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 3: Gate 3's verify block is FAIL-only

**Source:** Acceptance Criteria (AC-1.2) — Story 1

**Preconditions:**
- None. Reading exercise plus grep.

**Steps:**
1. `grep -n "review-override" commands/implement-story.md`
2. Open `commands/implement-story.md` at `#### Gate 3: Review Agent` and read the "Verify the claim, don't trust it." block.
3. `git show --stat dda5623 5fd325f | grep "agents/review-agent.md"; echo "grep-exit=$?"`

**Expected Result:**
- Step 1: the frontmatter line `script: scripts/review-override.py` and a command line `python3 scripts/review-override.py check --spec <spec-folder> --repo . --story <story-file> [--new-files …] [--tests …]` inside Gate 3.
- Step 2: the block says the override is **FAIL-only**. A script `fail` (it lists `untested_criterion`, `untasked_criterion`, `dangling_reference`, `duplicate_id`, `coverage_below_threshold`, `coverage_regression`, `test_imports_no_source`) takes the review-loop recode path. A script `pass` or `unverifiable` leaves the agent's FAIL or PAUSE standing, and `unverifiable` does not mark the story `⚠️ DEGRADED`. Architecture, security, and taste stay with the agent (`evaluator-agent` on default, `review-agent` on `--full-pipeline` since Stage 4b).
- Step 3: no match; `grep-exit=1`. Neither Stage 2b commit edited `agents/review-agent.md`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Implementation Decision 1 records the FAIL-only asymmetry.

**Notes:**

---

### Scenario 4: `gate3_review` names the script

**Source:** Acceptance Criteria (AC-1.3) — Story 1

**Preconditions:**
- None.

**Steps:**
1. `grep -n -A1 "id: gate3_review" commands/implement-story.md`

**Expected Result:**
- `- id: gate3_review` followed by `script: scripts/review-override.py`.
- (The AC-1.3 clause "`--prose-only-blocking` still not passed" was true only until Story 5; Scenario 32 checks the final state.)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: The Story 1 pytest module passes on Python 3.9

**Source:** Acceptance Criteria (AC-1.4) — Story 1

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q -p no:cacheprovider scripts/tests/test_review_override.py`
2. `grep -n "def test_" scripts/tests/test_review_override.py`

**Expected Result:**
- Step 1: `11 passed`.
- Step 2: tests for missing spec, missing story, usage exit 2, pass invoking ac-trace, fail from ac-trace (stub and real), untested-on-incomplete not fail, fail from integrity coverage, unverifiable helper, and two command-wiring tests.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — Files: `scripts/tests/test_review_override.py` (stub helpers record their argv to prove the script calls them)

**Notes:**

---

### Scenario 6: `review-override` eval check is registered, its test passes, and the decision log has the line

**Source:** Acceptance Criteria (AC-1.5) — Story 1

**Preconditions:**
- Run outside any sandbox.

**Steps:**
1. `grep -nE "^  review-override$|^check_review_override\(\)" scripts/eval.sh`
2. `bash scripts/tests/test_eval_review_override.sh; echo "exit=$?"`
3. `bash scripts/eval.sh --check=review-override; echo "exit=$?"` and open the report path it prints.
4. `grep -n "stage-2b: Story 1" .writ/decision-log.md`

**Expected Result:**
- Step 1: two hits, the `CHECKS` entry and the function.
- Step 2: ends with `All 6 review-override check assertions passed.`; `exit=0`.
- Step 3: `exit=0`. The `## review-override` section reads `PASS` with one note per active story (24 on 2026-09-25), each of the form `NOTE [review-override] <story path>: pass | review-override: pass (no blocking helper finding)`. The check passes `--spec` and `--story` for every story of every active spec; a story that fails ac-trace would be a finding. Summary `Findings: 0`, `Run errors: 0`.
- Step 4: one line starting `2026-09-08 stage-2b: Story 1 — review-override.py, Gate 3 verify block…` that names the FAIL-only rule.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: An `unverifiable` helper makes the override `unverifiable`; `--tests` on Writ tests passes

**Source:** Shadow Path (upstream error: helper unverifiable → override unverifiable) — Story 1

**Preconditions:**
- `$SPEC` set. No coverage report exists in the repo (the normal state).

**Steps:**
1. `python3 scripts/review-override.py check --spec $SPEC --repo . --story $SPEC/user-stories/story-1-gate3-review-override.md --new-files scripts/review-override.py; echo "exit=$?"`
2. `python3 scripts/review-override.py check --spec $SPEC --repo . --story $SPEC/user-stories/story-1-gate3-review-override.md --tests scripts/tests/test_review_override.py; echo "exit=$?"`
3. `python3 scripts/test-integrity.py authenticity --project . --tests scripts/tests/test_review_override.py scripts/tests/test_arch_check.py scripts/tests/test_docs_check.py scripts/tests/test_drift_format.py scripts/tests/test_ac_trace.py; echo "exit=$?"`

**Expected Result:**
- Step 1: `unverifiable`, `reason: no_coverage_report`, `reason: nothing_inspected`, `review-override: unverifiable (test-integrity coverage)`; `exit=0`. Omitting a coverage tool does not invent a fail.
- Step 2: `pass`, `review-override: pass (no blocking helper finding)`; `exit=0`. `test-integrity.py` now counts a Python test that runs a project script by path (subprocess, importlib, runpy) as exercising source.
- Step 3: JSON with `"findings": []`, `"files": 5`, `"verdict": "pass"`; `exit=0`. None of Writ's subprocess-style tests is flagged `test_imports_no_source`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 8: The story report shows the agent's claim beside the measurement

**Source:** Experience Design (Feedback model; Error experience) — Story 1

**Preconditions:**
- None. Reading exercise.

**Steps:**
1. Read the Gate 3 verify block in `commands/implement-story.md` again.
2. Read the "Review Outcome" section of `$SPEC/user-stories/story-5-drift-format-flip-and-watch.md`.

**Expected Result:**
- Step 1: the block says to "show both the claim and the measurement in the story report", and names no new control flow: `fail` reuses the recode path, `unverifiable` continues.
- Step 2: the outcome lists the agent result (`PASS — 1 iteration`) and a "Mechanical:" line with each script's verdict (`arch-check pass (proceed); review-override pass; drift-format pass; docs-check unverifiable (no_public_exports); change-surface cross-component`).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 2: Gate 0 Architecture Re-derivation

### Scenario 9: `proceed` and `caution` print as `pass`; no file mode is `unverifiable`; both modes is exit 2

**Source:** Acceptance Criteria (AC-2.1) and Shadow Path (empty input: no `--planned`/`--changed` → unverifiable) — Story 2

**Preconditions:**
- `$UAT` and `$SPEC` set.

**Steps:**
1. `ST=$SPEC/user-stories/story-2-gate0-arch-rederive.md`
2. `python3 scripts/arch-check.py check --story $ST --repo . --planned scripts/arch-check.py; echo "exit=$?"`
3. `python3 scripts/arch-check.py check --story $ST --repo . --planned; echo "exit=$?"`
4. `printf '{"owned":["src/app.py"],"readable":["src/lib.py"],"out_of_scope":["secrets/key"]}' > "$UAT/map.json"`
5. `python3 scripts/arch-check.py check --story $ST --repo . --planned src/app.py src/lib.py --boundary "$UAT/map.json"; echo "exit=$?"`
6. `python3 scripts/arch-check.py check --story $ST --repo . --planned src/app.py secrets/key --boundary "$UAT/map.json"; echo "exit=$?"`
7. `python3 scripts/arch-check.py check --story $ST --repo . --planned README.md --boundary "$UAT/map.json"; echo "exit=$?"`
8. `python3 scripts/arch-check.py check --story $ST --repo .; echo "exit=$?"`
9. `python3 scripts/arch-check.py check --story $ST --repo . --planned a --changed b; echo "exit=$?"`

**Expected Result:**
- Step 2: `pass`, `rederived: proceed`, `arch-check: pass (rederived proceed)`; `exit=0`.
- Step 3: `pass`, `rederived: caution`, `reason: empty_file_set`, `arch-check: pass (rederived caution)`; `exit=0`.
- Step 5: `pass`, `rederived: proceed`; `exit=0` (owned plus readable is inside the map).
- Step 6: `pass`, `rederived: caution`, `reason: out_of_scope`; `exit=0`.
- Step 7: `pass`, `rederived: caution`, `reason: outside_boundary`; `exit=0`.
- Step 8: `unverifiable`, `reason: no_file_mode`, `arch-check: unverifiable (no --planned or --changed)`; `exit=0`. No invented proceed.
- Step 9: `error: pass exactly one of --planned or --changed`; `exit=2`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Files: `scripts/arch-check.py`; commit `dda5623`

**Notes:**

---

### Scenario 10: An invalid story graph is `fail`

**Source:** Acceptance Criteria (AC-2.1) — Story 2

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Build two stories that depend on each other:
   ```
   mkdir -p "$UAT/cyc/user-stories"
   printf '# Story 1: A\n\n> **Status:** Not Started\n> **Dependencies:** Story 2\n' > "$UAT/cyc/user-stories/story-1-a.md"
   printf '# Story 2: B\n\n> **Status:** Not Started\n> **Dependencies:** Story 1\n' > "$UAT/cyc/user-stories/story-2-b.md"
   ```
2. `python3 scripts/story-deps.py validate --spec-dir "$UAT/cyc"; echo "exit=$?"`
3. `python3 scripts/arch-check.py check --story "$UAT/cyc/user-stories/story-1-a.md" --repo . --changed src/app.py; echo "exit=$?"`

**Expected Result:**
- Step 2: JSON with `"code": "dependency_cycle"` and `story cycle: story-1 -> story-2 -> story-1`; `exit=1`.
- Step 3: `fail`, `reason: dependency_cycle`, `arch-check: fail (invalid story graph)`; `exit=1`. The reason comes from `story-deps.py`, which the script calls.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: The script never prints `abort`

**Source:** Acceptance Criteria (AC-2.2) — Story 2

**Preconditions:**
- `ST` set as in Scenario 9.

**Steps:**
1. `python3 scripts/arch-check.py check --story $ST --repo . --planned scripts/arch-check.py --classify-abort; echo "exit=$?"`
2. `python3 scripts/arch-check.py check --story $ST --repo . --changed scripts/arch-check.py | grep -ci abort`
3. `grep -n "classify-abort" commands/implement-story.md; echo "grep-exit=$?"`

**Expected Result:**
- Step 1: `unverifiable`, `reason: abort_is_llm_residual`, `arch-check: unverifiable (llm residual)`; `exit=0`.
- Step 2: `0`. Output without `--classify-abort` does not mention ABORT.
- Step 3: no match; `grep-exit=1`. The command never asks the script to classify ABORT.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — Implementation Decision 1: `--classify-abort` is the test and explicit-caller hook.

**Notes:**

---

### Scenario 12: Gate 0 runs the script after PROCEED/CAUTION and leaves ABORT alone

**Source:** Acceptance Criteria (AC-2.3) — Story 2

**Preconditions:**
- None. Reading exercise.

**Steps:**
1. Open `commands/implement-story.md` at `#### Gate 0: Architecture Check` and read the "Verify the claim, don't trust it." block and the `--full-pipeline` section below it.

**Expected Result:**
- The block runs `python3 scripts/arch-check.py check --story <story-file> --repo . --planned <planned files> [--boundary <map.json>]` after the agent returns PROCEED or CAUTION, "never on ABORT", and always on default.
- `rederived: caution` → inject the script's `reason` into coding-agent warnings. Script `fail` → shared BLOCKED escalation. `rederived: proceed` → continue. `unverifiable` → continue, reason verbatim, not `⚠️ DEGRADED`.
- The ABORT handling and the "Anchor confirmation (ADR-024)" floor→anchor re-run are present under `--full-pipeline`, unchanged in substance.
- Note: since Stage 4b the default path does not spawn `architecture-check-agent`; the script is the only Gate 0 check on default.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 13: `gate0_arch` names the script; the baseline join id is unchanged

**Source:** Acceptance Criteria (AC-2.4) — Story 2

**Preconditions:**
- None.

**Steps:**
1. `grep -n -A1 "id: gate0_arch" commands/implement-story.md`
2. `grep -n '"gate0_arch"' scripts/pipeline-baseline.py`

**Expected Result:**
- Step 1: `- id: gate0_arch` then `script: scripts/arch-check.py`.
- Step 2: `gate0_arch` appears in `GATE_NAMES` (line ~714) and in the `VERDICT_GATE` map (`"ARCH_CHECK": "gate0_arch"`).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 14: Story 2 tests and the `arch-check` eval check pass

**Source:** Acceptance Criteria (AC-2.5) — Story 2

**Preconditions:**
- `uv` installed. Run outside any sandbox.

**Steps:**
1. `uv run --python 3.9 pytest -q -p no:cacheprovider scripts/tests/test_arch_check.py`
2. `bash scripts/tests/test_eval_arch_check.sh; echo "exit=$?"`
3. `bash scripts/eval.sh --check=arch-check; echo "exit=$?"` and open the report.

**Expected Result:**
- Step 1: `15 passed`.
- Step 2: ends with `All 7 arch-check check assertions passed.`; `exit=0`.
- Step 3: `exit=0`. The `## arch-check` section reads `PASS` with one note per active story (24 on 2026-09-25). The check computes each story's boundary map, passes its `owned` paths as `--planned`, and passes the map as `--boundary`. 23 notes read `pass | rederived: proceed | arch-check: pass (rederived proceed)`; `2026-09-07-phase11-stage2-prune-the-base` Story 5 reads `pass | rederived: caution | reason: empty_file_set | arch-check: pass (rederived caution)` (boundary-map finds no paths in its tasks). `Findings: 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 15: An unreadable boundary map or a story outside a spec is `unverifiable`

**Source:** Error Map (technical-spec §2 verdict table, `unverifiable` row) — Story 2

**Preconditions:**
- `ST` and `$UAT` set.

**Steps:**
1. `python3 scripts/arch-check.py check --story $ST --repo . --planned src/app.py --boundary "$UAT/nomap.json"; echo "exit=$?"`
2. `python3 scripts/arch-check.py check --story /nonexistent/story-1-x.md --repo . --planned a; echo "exit=$?"`

**Expected Result:**
- Step 1: `unverifiable`, `reason: boundary_unreadable`, `arch-check: unverifiable (boundary map unreadable)`; `exit=0`.
- Step 2: `unverifiable`, `reason: spec_dir_unresolved`, `arch-check: unverifiable (no user-stories ancestor for --story)`; `exit=0`.
- Neither case is `fail`. "Could not tell" does not block.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Gate 5 Docs Check

### Scenario 16: A documented export passes (README and docstring)

**Source:** Acceptance Criteria (AC-3.1) — Story 3

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Build a tiny JS app with a README that names its export:
   ```
   mkdir -p "$UAT/app/src"
   printf 'export function greet() { return "hi"; }\n' > "$UAT/app/src/greet.js"
   printf '# App\n\nCall `greet()` to say hi.\n' > "$UAT/app/README.md"
   python3 scripts/docs-check.py check --repo "$UAT/app" --changed src/greet.js; echo "exit=$?"
   ```
2. Build a tiny Python module whose `__all__` export has a docstring:
   ```
   mkdir -p "$UAT/py"; printf '# Py\n' > "$UAT/py/README.md"
   printf '__all__ = ["make_widget"]\n\ndef make_widget():\n    """Build a widget."""\n' > "$UAT/py/widgets.py"
   python3 scripts/docs-check.py check --repo "$UAT/py" --changed widgets.py; echo "exit=$?"
   ```

**Expected Result:**
- Both steps: `pass`, `docs-check: pass (1 export(s) documented)`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — Files: `scripts/docs-check.py` (exports are `__all__` and JS/TS `export` only; bare `def`/`class` are not exports); commit `dda5623`

**Notes:**

---

### Scenario 17: An undocumented export fails; `__all__` inside a string is not an export

**Source:** Acceptance Criteria (AC-3.2) — Story 3

**Preconditions:**
- Scenario 16 run (the scratch app exists).

**Steps:**
1. Add a second export the README does not mention:
   ```
   printf 'export function greet() { return "hi"; }\nexport const farewell = () => "bye";\n' > "$UAT/app/src/greet.js"
   python3 scripts/docs-check.py check --repo "$UAT/app" --changed src/greet.js; echo "exit=$?"
   ```
2. Remove the docstring from the Python module:
   ```
   printf '__all__ = ["make_widget"]\n\ndef make_widget():\n    pass\n' > "$UAT/py/widgets.py"
   python3 scripts/docs-check.py check --repo "$UAT/py" --changed widgets.py; echo "exit=$?"
   ```
3. Add a module whose only `__all__` sits inside a string literal (a test fixture, say):
   ```
   printf 'FIXTURE = """\n__all__ = ["ghost"]\n"""\n' > "$UAT/py/fixture_holder.py"
   python3 scripts/docs-check.py check --repo "$UAT/py" --changed fixture_holder.py; echo "exit=$?"
   ```

**Expected Result:**
- Step 1: `fail`, `reason: undocumented_export`, `symbol: farewell`, `docs-check: fail (farewell has no matching documented symbol)`; `exit=1`.
- Step 2: `fail`, `reason: undocumented_export`, `symbol: make_widget`, `docs-check: fail (make_widget has no matching documented symbol)`; `exit=1`.
- Step 3: `unverifiable`, `reason: no_public_exports`, `docs-check: unverifiable (no public exports in the changed set)`; `exit=0`. Only a module-level `__all__` counts.
- `reason:` lines carry codes only. Symbol names print on `symbol:` lines.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: A markdown-only tree, and this repo, are `unverifiable`

**Source:** Acceptance Criteria (AC-3.3) and Edge Case (Gate 5 on this markdown repo → unverifiable) — Story 3

**Preconditions:**
- `$UAT` set.

**Steps:**
1. ```
   mkdir -p "$UAT/md"; printf '# Notes\n\nJust prose.\n' > "$UAT/md/guide.md"
   python3 scripts/docs-check.py check --repo "$UAT/md" --changed guide.md; echo "exit=$?"
   ```
2. `python3 scripts/docs-check.py check --repo . --changed README.md; echo "exit=$?"`
3. `python3 scripts/docs-check.py check --repo .; echo "exit=$?"`

**Expected Result:**
- Step 1: `unverifiable`, `reason: no_public_exports`, `docs-check: unverifiable (no docs framework and no public exports)`; `exit=0`.
- Steps 2 and 3: `unverifiable`, `reason: no_public_exports`, `docs-check: unverifiable (no public exports in the changed set)`; `exit=0`.
- None of the three prints `pass` or `fail`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: An unresolvable changed set is `unverifiable`

**Source:** Acceptance Criteria (AC-3.4) — Story 3

**Preconditions:**
- Scenarios 16–17 run (`$UAT/app` and `$UAT/md` exist).

**Steps:**
1. `python3 scripts/docs-check.py check --repo "$UAT/md"; echo "exit=$?"` (not a git repo).
2. Make the app a git repo with one commit, so `HEAD^` does not exist:
   ```
   (cd "$UAT/app" && git init -q && git add -A && git -c user.email=u@x -c user.name=u commit -qm one)
   python3 scripts/docs-check.py check --repo "$UAT/app"; echo "exit=$?"
   ```

**Expected Result:**
- Both steps: `unverifiable`, `reason: changed_set_unresolved`, `docs-check: unverifiable (changed set could not be resolved)`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 20: Gate 5 wiring, frontmatter, tests, and eval check

**Source:** Acceptance Criteria (AC-3.5) — Story 3

**Preconditions:**
- `uv` installed. Run outside any sandbox.

**Steps:**
1. `grep -n -A1 "id: gate5_docs" commands/implement-story.md`
2. Read `#### Gate 5: Documentation Agent` in `commands/implement-story.md`.
3. `uv run --python 3.9 pytest -q -p no:cacheprovider scripts/tests/test_docs_check.py`
4. `bash scripts/tests/test_eval_docs_check.sh; echo "exit=$?"`
5. `bash scripts/eval.sh --check=docs-check; echo "exit=$?"` and open the report.

**Expected Result:**
- Step 1: `script: scripts/docs-check.py`.
- Step 2: the verify block runs `python3 scripts/docs-check.py check --repo . [--changed <story's changed files>]` after the documentation agent (or immediately on default). `fail` → BLOCKED escalation with agent `documentation-agent`, restarting Gate 5. `unverifiable` → continue, reason verbatim, not DEGRADED.
- Step 3: `15 passed`.
- Step 4: ends with `All 6 docs-check check assertions passed.`; `exit=0`.
- Step 5: `exit=0`; `## docs-check` reads `PASS` with notes `unverifiable`, `reason: no_public_exports`, `docs-check: unverifiable (no public exports in the changed set)`. `Findings: 0`. The live check passes every shipped Python/JS/TS file (tests and `.writ/` excluded) as `--changed`; none declares an export, so the verdict is `unverifiable` (Honest Note 3).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Boundary and Surface Classifiers

### Scenario 21: Boundary map with and without overlap; nothing is written

**Source:** Acceptance Criteria (AC-4.1) — Story 4

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Build a story and a Check 5 overlap table:
   ```
   mkdir -p "$UAT/bm"
   cat > "$UAT/bm/story-1-login.md" <<'EOF'
   # Story 1: Login

   > **Status:** Not Started

   ## Acceptance Criteria

   - [ ] Given a user, when they log in, then `session` exists

   ## Implementation Tasks

   - [ ] 1.1 Create `src/auth/login.ts`
   - [ ] 1.2 Modify `src/auth/session.ts`
   - [ ] 1.3 Add to `src/lib/utils.ts`

   ## Notes

   Ignore `src/other/out-of-scope.ts` here.
   EOF
   cat > "$UAT/bm/overlap.md" <<'EOF'
   ## Check 5 — File overlap

   | File / area | Stories sharing | Severity (note / warn) |
   |-------------|-----------------|-------------------------|
   | `src/lib/utils.ts` | 1, 2, 3 | warn |
   | `src/shared/types.ts` | 1, 2 | note |
   EOF
   (cd "$UAT/bm" && ls -A > "$UAT/bm-before.txt")
   ```
2. `python3 scripts/boundary-map.py compute --story "$UAT/bm/story-1-login.md" --repo "$UAT/bm"; echo "exit=$?"`
3. `python3 scripts/boundary-map.py compute --story "$UAT/bm/story-1-login.md" --repo "$UAT/bm" --overlap "$UAT/bm/overlap.md"; echo "exit=$?"`
4. `(cd "$UAT/bm" && ls -A | diff "$UAT/bm-before.txt" -); echo "diff-exit=$?"`

**Expected Result:**
- Step 2: `{"owned": ["src/auth/login.ts", "src/auth/session.ts", "src/lib/utils.ts"], "readable": [], "out_of_scope": []}`; `exit=0`. The path in Notes is not owned.
- Step 3: same `owned`, `"readable": ["src/shared/types.ts"]`, `"out_of_scope": []`; `exit=0`. The shared path the story already owns stays owned.
- Step 4: no difference; `diff-exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `scripts/boundary-map.py`; Implementation Decision 2: `out_of_scope` stays `[]` unless overlap data names it; commit `dda5623`

**Notes:**

---

### Scenario 22: Malformed story exits 1; usage exits 2 with a message

**Source:** Acceptance Criteria (AC-4.2) — Story 4

**Preconditions:**
- Scenario 21 run.

**Steps:**
1. `printf '# Story\n\nNo tasks.\n' > "$UAT/bm/bad.md"` then `python3 scripts/boundary-map.py compute --story "$UAT/bm/bad.md" --repo "$UAT/bm"; echo "exit=$?"`
2. `python3 scripts/boundary-map.py compute --story "$UAT/bm/missing.md" --repo "$UAT/bm"; echo "exit=$?"`
3. `python3 scripts/boundary-map.py compute; echo "exit=$?"`
4. `python3 scripts/boundary-map.py compute --story "$UAT/bm/story-1-login.md" --repo "$UAT/bm" --overlap "$UAT/bm/nope.md"; echo "exit=$?"`

**Expected Result:**
- Steps 1 and 2: no output; `exit=1`.
- Step 3: usage error naming `--story, --repo`; `exit=2`.
- Step 4: stderr `error: overlap file is not readable: <path>/bm/nope.md`; `exit=2`. A supplied overlap path that does not exist is a usage error; only omitting `--overlap` takes the degrade path.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: Four surface classes, classify up when ambiguous, no files is exit 2

**Source:** Acceptance Criteria (AC-4.3) — Story 4

**Preconditions:**
- None.

**Steps:**
1. `python3 scripts/change-surface.py classify --changed src/styles/theme.css src/app.module.css`
2. `python3 scripts/change-surface.py classify --changed src/components/Form.tsx src/components/Form.test.tsx`
3. `python3 scripts/change-surface.py classify --changed src/hooks/useAuth.ts`
4. `python3 scripts/change-surface.py classify --changed prisma/schema.prisma`
5. `python3 scripts/change-surface.py classify --changed src/styles/theme.css prisma/migrations/001.sql`
6. `python3 scripts/change-surface.py classify --changed src/components/A.tsx src/components/B.tsx`
7. `python3 scripts/change-surface.py classify --changed; echo "exit=$?"`
8. `python3 scripts/change-surface.py classify; echo "exit=$?"`

**Expected Result:**
- Steps 1–6 print, in order: `style-only`, `single-component`, `cross-component`, `full-stack`, `full-stack`, `cross-component`. Each prints one token and nothing else.
- Steps 7 and 8: no output; `exit=2`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — Files: `scripts/change-surface.py` (six-step path heuristic from `skills/change-surface-classification/SKILL.md`)

**Notes:** Any unrecognized path classifies up. `README.md` alone and `commands/implement-story.md scripts/eval.sh` both print `cross-component`, which is why every replay row reads `cross-component`.

---

### Scenario 24: Gates 0.5 and 2.5 run the scripts and stay advisory

**Source:** Acceptance Criteria (AC-4.4) — Story 4

**Preconditions:**
- None. Reading exercise.

**Steps:**
1. Read `#### Gate 0.5: Boundary Computation` and `#### Gate 2.5: Change Surface Classification` in `commands/implement-story.md`.
2. `grep -n "^#### Gate" commands/implement-story.md`

**Expected Result:**
- Step 1: Gate 0.5 runs `python3 scripts/boundary-map.py compute --story <story-file> --repo . [--overlap <check-5-overlap>]` and passes stdout on as `boundary_map`; the text says the map is advisory with no hard file locking. Gate 2.5 runs `python3 scripts/change-surface.py classify --changed <files>` and passes stdout to Gate 3 as `change_surface`.
- Step 2: ten headings, Gate 0, 0.5, 1, 2, 2.5, 3, 3.5, 4, 4.5, 5. No new gate numbers.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 25: Frontmatter, tests, and the two eval checks

**Source:** Acceptance Criteria (AC-4.5) — Story 4

**Preconditions:**
- `uv` installed. Run outside any sandbox.

**Steps:**
1. `grep -n -A1 "id: gate0_5_boundary\|id: gate2_5_surface" commands/implement-story.md`
2. `uv run --python 3.9 pytest -q -p no:cacheprovider scripts/tests/test_boundary_map.py scripts/tests/test_change_surface.py`
3. `bash scripts/tests/test_eval_boundary_map.sh; echo "exit=$?"`
4. `bash scripts/eval.sh --check=change-surface; echo "exit=$?"` and open the report. Then the same with `--check=boundary-map`.

**Expected Result:**
- Step 1: `script: scripts/boundary-map.py` and `script: scripts/change-surface.py`.
- Step 2: `30 passed` (18 + 12).
- Step 3: ends with `All 8 boundary-map / change-surface check assertions passed.`; `exit=0`.
- Step 4: both `exit=0`. `## change-surface` reads `PASS` with note `cross-component` (it classifies `commands/implement-story.md`). `## boundary-map` reads `PASS` with one note holding the JSON map of the first active story (`2026-09-05-phase11-repair-and-baseline` Story 1). `Findings: 0`. Both checks use fixed inputs (Honest Note 3).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 26: The boundary map names real paths

**Source:** Experience Design (Happy path step 4: "Advisory maps become checkable artifacts") — Story 4

**Preconditions:**
- Scenario 21 run.

**Steps:**
1. ```
   printf '# Story 1: Dots\n\n> **Status:** Not Started\n\n## Implementation Tasks\n\n- [ ] 1.1 Append to `.writ/decision-log.md`\n- [ ] 1.2 Edit `scripts/eval.sh` lines 70/219/231\n- [ ] 1.3 Update `.github/workflows/ci.yml`\n' > "$UAT/bm/story-1-dots.md"
   python3 scripts/boundary-map.py compute --story "$UAT/bm/story-1-dots.md" --repo "$UAT/bm"
   ```
2. `python3 scripts/boundary-map.py compute --story $SPEC/user-stories/story-5-drift-format-flip-and-watch.md --repo .`
3. `python3 scripts/boundary-map.py compute --story .writ/specs/2026-09-05-phase11-repair-and-baseline/user-stories/story-1-repair-dead-ends.md --repo .`

**Expected Result:**
- Step 1: `{"owned": [".writ/decision-log.md", "scripts/eval.sh", ".github/workflows/ci.yml"], "readable": [], "out_of_scope": []}`. Leading dots are kept; `70/219/231` is not a path.
- Step 2: 11 owned entries: `scripts/tests/test_drift_format.py`, `scripts/tests/test_gate_replay.py`, `scripts/tests/test_eval_drift_format.sh`, `test_eval_verdict_provenance.sh`, `scripts/drift-format.py`, `.writ/docs/drift-report-format.md`, `.writ/specs/2026-09-08-phase11-stage2b-mechanize-the-gates/sub-specs/technical-spec.md`, `commands/implement-story.md`, `scripts/eval.sh`, `agents/visual-qa-agent.md`, `scripts/pipeline-baseline.py`. No `/implement-story` or `/revert`. The spec-relative `sub-specs/technical-spec.md` is rewritten to its repo path.
- Step 3: 25 owned entries. Bare filenames resolve to their tracked paths (`scripts/tests/test_phase_state.py`, `commands/create-spec.md`, `commands/ship.md`); `scripts/phase-state.py::knowledge_writeback` becomes `scripts/phase-state.py`. Two entries do not name a single file: the directory `commands/` and the unmatched `objective.md`.
- Step 2's `test_eval_verdict_provenance.sh` and step 3's bare names and `::` token do not exist at the repo root. Mark **Fail** if Gates 1 and 3 must receive only resolvable paths. See Honest Note 2.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 5: Drift Format, Flip, and Watch

### Scenario 27: drift-format pass, fail, and `unverifiable`

**Source:** Acceptance Criteria (AC-5.1) — Story 5

**Preconditions:**
- `$UAT` and `$SPEC` set.

**Steps:**
1. Build fixtures:
   ```
   mkdir -p "$UAT/drift"
   printf '# Story 1\n\n> **Status:** In Progress\n' > "$UAT/drift/story-nopause.md"
   printf '# Story 1\n\n> **Status:** In Progress\n\nREVIEW_RESULT: PAUSE\n' > "$UAT/drift/story-pause.md"
   printf '# Drift Log\n\n#### [DEV-001] Missing fields\n- **Severity:** Small\n- **Spec said:** X\n' > "$UAT/drift/malformed.md"
   cat > "$UAT/drift/large-titled.md" <<'EOF'
   # Drift Log

   ## Story 1: Fixture — Drift Report

   > Run: 2026-09-08
   > Overall Drift: Large

   ### Deviations

   #### [DEV-001] Large: replaced the payment provider
   - **Severity:** Large
   - **Spec said:** Use Stripe
   - **Implementation did:** Used a different provider
   - **Reason:** Test fixture
   - **Resolution:** Pipeline paused — accepted by user
   - **Spec amendment:** N/A — deviation accepted as-is
   EOF
   ```
2. `python3 scripts/drift-format.py check --story "$UAT/drift/story-nopause.md"; echo "exit=$?"`
3. `python3 scripts/drift-format.py check --story "$UAT/drift/story-nopause.md" --drift-log $SPEC/drift-log.md; echo "exit=$?"`
4. `python3 scripts/drift-format.py check --story "$UAT/drift/story-nopause.md" --drift-log "$UAT/drift/malformed.md"; echo "exit=$?"`
5. `python3 scripts/drift-format.py check --story "$UAT/drift/story-nopause.md" --drift-log "$UAT/drift/large-titled.md"; echo "exit=$?"`
6. `python3 scripts/drift-format.py check --story "$UAT/drift/story-pause.md" --drift-log "$UAT/drift/large-titled.md"; echo "exit=$?"`
7. `python3 scripts/drift-format.py check; echo "exit=$?"`
8. `grep -niE "^(accept|reject|modify)" scripts/drift-format.py; echo "grep-exit=$?"`

**Expected Result:**
- Step 2: `unverifiable`, `reason: no_drift_signal`, `drift-format: unverifiable (no drift log and no Large-drift heading)`; `exit=0`.
- Step 3: `pass`, `drift-format: pass (entries well-formed)`; `exit=0` (this spec's real DEV-001 entry).
- Step 4: `fail`, `reason: malformed_entry`, `drift-format: fail (format or PAUSE)`; `exit=1`.
- Step 5: `fail`, `reason: large_drift_without_pause`, same summary; `exit=1`.
- Step 6: `pass`; `exit=0`.
- Step 7: usage error naming `--story`; `exit=2`.
- Step 8: no match; the script prints no accept / reject / modify-spec verdict.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/drift-format.py`; commit `5fd325f`

**Notes:**

---

### Scenario 28: A Large drift in the documented format without PAUSE fails

**Source:** Edge Case (Large-drift without PAUSE → drift-format fail) — Story 5

**Preconditions:**
- Scenario 27 run.

**Steps:**
1. Give the Large entry a title that does not contain the word "large":
   ```
   sed 's/Large: replaced the payment provider/Replaced the payment provider/' "$UAT/drift/large-titled.md" > "$UAT/drift/large.md"
   grep -n "Overall Drift\|Severity" "$UAT/drift/large.md"
   grep -n "^> Overall Drift\|^- \*\*Severity" .writ/docs/drift-report-format.md | head -3
   ```
2. `python3 scripts/drift-format.py check --story "$UAT/drift/story-nopause.md" --drift-log "$UAT/drift/large.md"; echo "exit=$?"`
3. `python3 scripts/drift-format.py check --story "$UAT/drift/story-pause.md" --drift-log "$UAT/drift/large.md"; echo "exit=$?"`

**Expected Result:**
- Step 1: the fixture shows `6:> Overall Drift: Large` and `11:- **Severity:** Large`. The format doc shows `> Overall Drift: Small | Medium | Large`, `- **Severity:** Small | Medium | Large`, and an example `> Overall Drift: Small`: the same shape.
- Step 2: `fail`, `reason: large_drift_without_pause`, `drift-format: fail (format or PAUSE)`; `exit=1`. Large is detected from `Overall Drift:` and `- **Severity:** Large`, not from the entry title.
- Step 3: `pass`, `drift-format: pass (entries well-formed)`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: The PAUSE check needs a PAUSE verdict, not the word anywhere

**Source:** Edge Case (Large-drift without PAUSE → drift-format fail) — Story 5

**Preconditions:**
- Scenario 27 run.

**Steps:**
1. `grep -c PAUSE $SPEC/user-stories/story-1-gate3-review-override.md`
2. `python3 scripts/drift-format.py check --story $SPEC/user-stories/story-1-gate3-review-override.md --drift-log "$UAT/drift/large-titled.md"; echo "exit=$?"`
3. Supply the verdict as review output:
   ```
   printf 'EVALUATION_RESULT: PAUSE\n' > "$UAT/drift/eval-out.txt"
   python3 scripts/drift-format.py check --story $SPEC/user-stories/story-1-gate3-review-override.md --drift-log "$UAT/drift/large-titled.md" --review-output "$UAT/drift/eval-out.txt"; echo "exit=$?"
   ```
4. Put the verdict in the story as a heading:
   ```
   printf '# Story 1\n\n> **Status:** In Progress\n\n### REVIEW_RESULT: PAUSE\n' > "$UAT/drift/story-pause-h.md"
   python3 scripts/drift-format.py check --story "$UAT/drift/story-pause-h.md" --drift-log "$UAT/drift/large.md"; echo "exit=$?"
   ```

**Expected Result:**
- Step 1: `5`. The story's criteria mention PAUSE in prose.
- Step 2: `fail`, `reason: large_drift_without_pause`, `drift-format: fail (format or PAUSE)`; `exit=1`. Prose mentions do not count.
- Step 3: `pass`, `drift-format: pass (entries well-formed)`; `exit=0`.
- Step 4: `pass`; `exit=0`. A `REVIEW_RESULT:` or `EVALUATION_RESULT: PAUSE` line, plain, bold, or as a heading, is the verdict.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 30: Eight gates name scripts, two stay `prose-only`, provenance passes with blocking on

**Source:** Acceptance Criteria (AC-5.2) and Experience Design (Moment of truth) — Story 5

**Preconditions:**
- None.

**Steps:**
1. `sed -n '/^gates:/,/^---/p' commands/implement-story.md`
2. `for s in $(sed -n '/^gates:/,/^---/p' commands/implement-story.md | grep -o 'script: scripts/[a-z-]*\.py' | cut -d' ' -f2); do test -f "$s" && echo "ok $s" || echo "MISSING $s"; done`
3. `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --prose-only-blocking; echo "exit=$?"`

**Expected Result:**
- Step 1: a two-line comment naming `scripts/verdict-provenance.py`, then ten entries. `gate1_coding` and `gate4_5_visual` read `verification: prose-only`. The other eight read `script:` with `arch-check.py`, `boundary-map.py`, `build-smoke.py`, `change-surface.py`, `review-override.py`, `drift-format.py`, `test-integrity.py`, `docs-check.py`, matching technical-spec §6.
- Step 2: eight lines, every one starts `ok`.
- Step 3: `note: prose_only_count: 2 (cap 2)` and `gates: 10 entries, headings: 10, script: 8, prose-only: 2, findings: 0`; `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 31: A third `prose-only` gate, or a missing script, is a finding

**Source:** Experience Design (Moment of truth: "Adding a third `prose-only` is a finding") — Story 5

**Preconditions:**
- `$UAT` set.

**Steps:**
1. Write two altered copies of the command file to scratch:
   ```
   python3 - "$UAT" <<'EOF'
   import sys
   t = open('commands/implement-story.md').read()
   old = "  - id: gate5_docs\n    script: scripts/docs-check.py"
   open(sys.argv[1] + '/is-3prose.md', 'w').write(t.replace(old, "  - id: gate5_docs\n    verification: prose-only", 1))
   open(sys.argv[1] + '/is-badpath.md', 'w').write(t.replace(old, "  - id: gate5_docs\n    script: scripts/does-not-exist.py", 1))
   EOF
   ```
2. `python3 scripts/verdict-provenance.py check --command "$UAT/is-3prose.md" --repo . --prose-only-blocking; echo "exit=$?"`
3. `python3 scripts/verdict-provenance.py check --command "$UAT/is-3prose.md" --repo .; echo "exit=$?"`
4. `python3 scripts/verdict-provenance.py check --command "$UAT/is-badpath.md" --repo . --prose-only-blocking; echo "exit=$?"`

**Expected Result:**
- Step 2: `prose_only_count: 3 (cap 2)` (no `note:` prefix), `… prose-only: 3, findings: 1`; `exit=1`.
- Step 3: the same count as a `note:`, `findings: 0`; `exit=0`. The flag is what makes it blocking.
- Step 4: `script_missing: … gate5_docs (scripts/does-not-exist.py not found under .)`, `findings: 1`; `exit=1`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: Gate 3.5 runs the format check; eval passes `--prose-only-blocking`

**Source:** Acceptance Criteria (AC-5.2) — Story 5

**Preconditions:**
- `uv` installed. Run outside any sandbox.

**Steps:**
1. Read `#### Gate 3.5` § A in `commands/implement-story.md`.
2. `grep -n "prose-only-blocking" scripts/eval.sh`
3. `bash scripts/tests/test_eval_drift_format.sh; echo "exit=$?"` and `bash scripts/tests/test_eval_verdict_provenance.sh; echo "exit=$?"`
4. `bash scripts/eval.sh --check=verdict-provenance; echo "exit=$?"` and open the report. Then the same with `--check=drift-format`.

**Expected Result:**
- Step 1: after the drift step, "format-check only — this script never decides accept / reject / modify-spec", then `python3 scripts/drift-format.py check --story <story-file> [--drift-log <spec>/drift-log.md] [--review-output <review-agent stdout>]`. `fail` → BLOCKED escalation. `unverifiable` → continue, not DEGRADED. Large drift still presents accept / reject / modify-spec to the user.
- Step 2: three hits. The `check_verdict_provenance` call line (~3989) passes `--prose-only-blocking`; the other two are comments (~3969 in `check_verdict_provenance`, ~4073 in `check_review_override`).
- Step 3: `All 3 drift-format check assertions passed.` and `All 7 verdict-provenance check assertions passed.`; both `exit=0`.
- Step 4: both `exit=0`. `## verdict-provenance` reads `PASS` with note `prose_only_count: 2 (cap 2)`. `## drift-format` reads `PASS` with notes `unverifiable`, `reason: no_drift_signal`, `drift-format: unverifiable (no drift log and no Large-drift heading)`. `Findings: 0`. The live drift-format check runs on this spec's Story 5 with no drift log (Honest Note 3).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 33: Visual QA has no match percentages

**Source:** Acceptance Criteria (AC-5.3) — Story 5

**Preconditions:**
- None.

**Steps:**
1. `grep -nE "85|70|%" agents/visual-qa-agent.md; echo "grep-exit=$?"`
2. `grep -n "SOFT PASS" agents/visual-qa-agent.md`
3. `git show 5fd325f -- agents/visual-qa-agent.md | grep '^-' | grep -v '^---'`

**Expected Result:**
- Step 1: no match; `grep-exit=1`.
- Step 2: lines naming PASS / SOFT PASS / FAIL, including `**Overall:** {PASS / SOFT PASS / FAIL}` and the SOFT PASS rule "only cosmetic, medium-or-low mismatches".
- Step 3: the removed lines carry the old thresholds (`≥85% match`, `≥70% match`, `<70% match`, `**Overall match:** {percentage}%`).

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 34: New run records carry the watch field; committed baselines are unchanged

**Source:** Acceptance Criteria (AC-5.4) — Story 5

**Preconditions:**
- `uv` installed.

**Steps:**
1. `grep -n "background_tasks_outstanding\|Background tasks still running after 600s" scripts/pipeline-baseline.py`
2. `sed -n '/^REDERIVATION_KEYS/,/)/p' scripts/pipeline-baseline.py`
3. `uv run --python 3.9 pytest -q -p no:cacheprovider scripts/tests/test_gate_replay.py -k "watch_field or background_drop"`
4. `grep -c background_tasks_outstanding .writ/eval/baselines/2026-09-06-claude-fable-5-1.json .writ/eval/baselines/2026-09-07-claude-fable-5-1.json`
5. `git log --oneline 5fd325f^.. -- .writ/eval/baselines/2026-09-06-claude-fable-5-1.json .writ/eval/baselines/2026-09-07-claude-fable-5-1.json`
6. `python3 scripts/pipeline-baseline.py validate .writ/eval/baselines/2026-09-06-claude-fable-5-1.json; echo "exit=$?"` and the same for `2026-09-07`.

**Expected Result:**
- Step 1: the `BACKGROUND_DROP` constant, the record field set from metadata, and two ingest/run sites that fill it from stderr.
- Step 2: `build_smoke`, `test_integrity`, `arch_check`, `review_override`, `docs_check`, `boundary_map`, `change_surface`, `drift_format`.
- Step 3: `2 passed, 2 deselected` (a new record carries the value; two drop lines count as 2, empty text as 0).
- Step 4: both files `0`.
- Step 5: no output. No commit from Story 5 on touched either file.
- Step 6: both `exit=0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 5 — Files: `scripts/pipeline-baseline.py` (`count_background_drops`); Implementation Decision 3: the field sits after the stable `RUN_KEYS` prefix

**Notes:**

---

### Scenario 35: The replay covers 16 records and the decision log names the totals

**Source:** Acceptance Criteria (AC-5.5) — Story 5

**Preconditions:**
- `uv` installed.

**Steps:**
1. `uv run --python 3.9 pytest -q -s -p no:cacheprovider scripts/tests/test_gate_replay.py`
2. `grep -n "stage-2b: Story 5" .writ/decision-log.md`
3. Read "Replay table" under What Was Built in `$SPEC/user-stories/story-5-drift-format-flip-and-watch.md`.
4. `sed -n '/^NOT_REPLAYABLE/,/^}/p' scripts/tests/test_gate_replay.py`

**Expected Result:**
- Step 1: `4 passed`. Sixteen `REPLAY_ROW` lines; on each, `gate2_5_surface=-->cross-component` and the other five gates `…->n/r`. Last line: `REPLAY_TABLE rows=16 cells=96 replayed=16 not_replayable=80 compared=0 agree=0 disagree=0 expected_integrity_notes=16`.
- Step 2: the original line `… Story 5 — drift-format.py; gates flipped to 8 script / 2 prose-only; --prose-only-blocking on; watch field; replay totals {54 agree / 42 note / 48 unverifiable}`, followed on the same line by `(corrected 2026-09-25: those totals double-counted constant inputs; only Gate 2.5 replays from baseline records — 16 replayed / 80 not_replayable of 96 cells)`.
- Step 3: a "Correction (2026-09-25)" block explaining why the first totals were constants, then the same `REPLAY_TABLE` totals as step 1, a per-gate reason list, and a 16-row table. Disagreement is a note; no revert.
- Step 4: five entries: `gate0_arch` and `gate3_review` → `record_spec_absent`, `gate5_docs` → `record_checkout_absent`, `gate0_5_boundary` and `gate3_5_drift` → `record_story_absent`.
- `compared=0`: no recorded agent verdict is checked against a re-derived one. Mark **Fail** if AC-5.5 requires at least one agent-vs-re-derived comparison. See Honest Note 1.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 36: Historical `nothing_inspected` shows as expected `unverifiable`, not a defect

**Source:** Edge Case (historical `test_integrity: nothing_inspected` → unverifiable on replay) — Story 5

**Preconditions:**
- None.

**Steps:**
1. `python3 -c "import json; [print(f, sorted({(r.get('rederivation') or {}).get('test_integrity', {}).get('reason') for r in json.load(open(f))['runs']})) for f in ['.writ/eval/baselines/2026-09-06-claude-fable-5-1.json', '.writ/eval/baselines/2026-09-07-claude-fable-5-1.json']]"`
2. `grep -n "nothing_inspected" scripts/tests/test_gate_replay.py`

**Expected Result:**
- Step 1: each file prints `['nothing_inspected']`. Every one of the 16 records has that reason.
- Step 2: the replay appends `test_integrity nothing_inspected -> unverifiable expected` as a note, counts it as `expected_integrity_notes`, and asserts at least 8. It does not fail on them. Scenario 35 step 1 shows `expected_integrity_notes=16`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 37: Full suite and full eval pass at spec close

**Source:** Experience Design (State catalog: "replay recorded"; Success criteria: `eval.sh` exits 0) — Story 5

**Preconditions:**
- `uv` installed. Run outside any sandbox. Allow several minutes.

**Steps:**
1. `uv run --python 3.9 pytest -q -p no:cacheprovider scripts/tests/test_review_override.py scripts/tests/test_arch_check.py scripts/tests/test_docs_check.py scripts/tests/test_boundary_map.py scripts/tests/test_change_surface.py scripts/tests/test_drift_format.py scripts/tests/test_gate_replay.py`
2. `bash scripts/eval.sh; echo "exit=$?"` and open the report path it prints.

**Expected Result:**
- Step 1: `93 passed`.
- Step 2: `exit=0`. The report ends with `Findings: 0` and `Run errors: 0`.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Pending Stories

None. All five stories are Completed ✅.
